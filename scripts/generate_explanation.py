import tiktoken
from sqlalchemy.engine.create import create_engine
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.functions import func

from scripts.gpt_client import chat_completion
from scripts.models import BaseModel, Paragraphs, Explanation

from loguru import logger

system_prompt = '''
你是一位专业的英语老师，而我是一名有想学习英语的学生，我的英语水平勉强达到中国的大学英语四级（CET-4）水准。

我正在尝试阅读英文杂志，我会在后续的绘画中，列出我正在阅读到的段落。请你详细地给我，按顺序讲解一下这段台词中出现的所有生词、短语和语法点。
讲解完毕后，附上一个生词表，列出你觉得我需要掌握的单词和短语。生词表以单独的一行‘### Word List ###‘开头，之后每行一个单词/短语，每一行的格式如下：

word/phrase | wordclass. 中文含义

注意，由于我的英语水平勉强达到中国的大学英语四级（CET-4）水准，所以请不要再生词表中列出非常简单的单词/短语。
如果一个生词在段落中出现多次，在生词表中只能出现一次，不应重复出现。

注意，我给你列出的段落，是使用OCR工具转换成文字呈现给你的，所以其中可能会出现缺失的字符、错误的拼写，多余的空格，或者其他格式不正确的地方。
你需要利用你自己的丰富经验，去修正这些错误，并给出正确的解释。

以下是一组示例输入/输出

示例输入：

Distance to resources is typically very low, with loot being about double of that.


示例输出：

1. Distance to resources is typically very low:
主语：Distance to resources
谓语：is
表语：typically very low
这是一个简单的主系表结构，谓语动词是be动词。


2. with loot being about double of that:
With引导的介词短语，修饰前面的句子，表示附加信息。
Being在这里是动名词形式，作为介词with的宾语。
About double of that是补语，说明loot的情况。

### Word List ###
typically | adv. 通常，典型地
loot | n. 战利品，掠夺物

'''


def cost_estimation(engine, chunk_limit=512):
    encoder = tiktoken.encoding_for_model('gpt-4o')
    system_prompt_tokens = len(encoder.encode(system_prompt))
    total_input_tokens, total_output_tokens = 0, 0
    records = sessionmaker(bind=engine)().query(Paragraphs).order_by(Paragraphs.file_name.asc(),
                                                                     Paragraphs.page_id.asc(),
                                                                     Paragraphs.paragraph_id.asc()).all()
    buf, buf_tokens = "", 0
    for record in records:
        token_count = len(encoder.encode(record.content))
        if record.paragraph_id == 0 or buf_tokens + token_count > chunk_limit:
            total_input_tokens += system_prompt_tokens + buf_tokens
            total_output_tokens += round(buf_tokens * 7)
            buf, buf_tokens = record.content, token_count
        else:
            buf += record.content
            buf_tokens += token_count
    if buf:
        total_input_tokens += system_prompt_tokens + buf_tokens
        total_output_tokens += round(buf_tokens * 4)

    estimated_cost = (0.15 * total_input_tokens + 0.6 * total_output_tokens) / 1000000.0 * 5.0
    print(f"total input tokens: {total_input_tokens}, total output tokens: {total_output_tokens}")
    print(f"total cost: {estimated_cost}")


def generate(session, llm_model, file_name, page_id, content, buf_para_range):
    try:
        result, input_tokens, output_tokens = chat_completion(content, system_prompt, model=llm_model)
        new_record = Explanation(
            file_name=file_name,
            page_id=page_id,
            start_paragraph_id=buf_para_range[0],
            end_paragraph_id=buf_para_range[1],
            explanation_content=result,
            llm_model=llm_model,
            input_token_count=input_tokens,
            output_token_count=output_tokens
        )
        session.add(new_record)
        session.commit()
    except Exception:
        logger.exception("generate explanation failed.")


if __name__ == '__main__':
    chunk_limit, llm_model = 512, 'gpt-4o-mini'
    encoder = tiktoken.encoding_for_model(llm_model)
    system_prompt_tokens = len(encoder.encode(system_prompt))
    engine = create_engine('sqlite:///assets/the_economist/sqlite_database.db')
    cost_estimation(engine)
    BaseModel.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    valid_page_records = Session().query(Paragraphs.file_name, Paragraphs.page_id,
                                         func.max(Paragraphs.token_count).label('max_token_count')).filter(
        Paragraphs.file_name >= 'The_Economist_2025_06_07.md').group_by(Paragraphs.file_name,
                                                                        Paragraphs.page_id).having(
        text("max_token_count <= 512")).order_by(
        Paragraphs.file_name.asc(), Paragraphs.page_id.asc(), Paragraphs.paragraph_id.asc()).all()
    valid_pages = set([(x.file_name, x.page_id) for x in valid_page_records])
    explanation_records = Session().query(Explanation).all()
    already_explained = set()
    for record in explanation_records:
        for para_id in range(record.start_paragraph_id, record.end_paragraph_id + 1):
            already_explained.add((record.file_name, record.page_id, para_id))
    paragraph_records = Session().query(Paragraphs).filter(
        Paragraphs.file_name >= 'The_Economist_2025_06_07.md').order_by(
        Paragraphs.file_name.asc(), Paragraphs.page_id.asc(), Paragraphs.paragraph_id.asc()).all()

    records_by_page = {}
    session = Session()
    for record in paragraph_records:
        key = (record.file_name, record.page_id)
        if key not in records_by_page:
            records_by_page[key] = []
        records_by_page[key].append(record)
    progress = 0
    for k, v in records_by_page.items():
        file_name, page_id = k
        buf, buf_tokens, buf_para_range = "", 0, [0, 0]
        for i, record in enumerate(v):
            progress += 1
            if (file_name, page_id, record.paragraph_id) in already_explained:
                continue
            token_count = len(encoder.encode(record.content))
            if buf_tokens + token_count > chunk_limit:
                generate(session, llm_model, file_name, page_id, buf, buf_para_range)
                buf, buf_tokens = record.content, token_count
                buf_para_range = [record.paragraph_id, record.paragraph_id]
                logger.info(
                    f"Paragraph explanation generated, filename: {record.file_name}, page_id: {record.page_id}, paragraph_id: {record.paragraph_id}, progress: {progress}/{len(paragraph_records)} ({progress * 100.0 / len(paragraph_records)}%)")
            else:
                buf += record.content
                buf_tokens += token_count
                buf_para_range[1] = record.paragraph_id
        if buf:
            generate(session, llm_model, file_name, page_id, buf, buf_para_range)
