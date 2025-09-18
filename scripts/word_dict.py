from sqlalchemy.engine.create import create_engine
from sqlalchemy.orm.session import sessionmaker

from scripts.gpt_client import chat_completion
import pandas as pd

from scripts.models import Dictionary, BaseModel
from loguru import logger

raw_word_file_path = './assets/the_economist/word_count_2023_07.csv'
high_freq_word_file_path = './assets/the_economist/word_count_2023_07_high_freq.csv'


def filter_high_freq_words():
    df = pd.read_csv(raw_word_file_path)
    df = df[df['count'] >= 20]
    df.to_csv(high_freq_word_file_path, index=False)


def generate_word_dictionary():
    system_prompt = '''
    你是一位经验丰富的英语老师，我是正在学习英语的学生，在后面的对话中，我会给你一个单词，请你给出这个单词的中文含义，以及至少三个例句。
    
    你的输出格式应当如下：
    
    # 单词
    word
    
    # 含义
    abbr of wordclass(n/v/adj/adv/...). 中文含义
    
    
    # 例句
    
    1. Sample sentence 1...
    中文翻译 1
    
    2. Sample sentence 2...
    中文翻译 2
    
    以下是一个输入/输出的示例：
    
    示例输入：
    
    sun
    
    示例输出：
    
    # 单词
    sun
    
    # 含义
    n. 太阳
    
    # 例句
    
    1. The sun rises in the east and sets in the west.
    太阳从东方升起，在西方落下。
    
    2. She likes to sit outside and enjoy the warm sun.
    她喜欢坐在户外享受温暖的阳光。
    
    3. Without the sun, life on Earth would not be possible.
    没有太阳，地球上的生命将无法存在。
    '''

    df = pd.read_csv(high_freq_word_file_path)
    engine = create_engine('sqlite:///assets/the_economist/sqlite_database.db')
    BaseModel.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    total_input_tokens, total_output_tokens = 0, 0
    session = Session()
    all_records = session.query(Dictionary).all()
    generated_words = set([x.word for x in all_records])
    for i, (_, row) in enumerate(df.iterrows()):
        word, count, real_count = row['word'], row['count'], row['real_count']
        if word in generated_words:
            continue
        explanation, input_tokens, output_tokens = chat_completion(word, system_prompt)
        record = Dictionary(
            word=word,
            llm_explanation=explanation,
            llm_mentioned_times=count,
            times_in_ocr=real_count
        )
        total_input_tokens += input_tokens
        total_output_tokens += output_tokens
        session = Session()
        session.add(record)
        session.commit()
        logger.info(
            f"Word explanation generated, word: {word}, "
            f"progress: {i + 1}/{len(df)} ({(i + 1) * 100.0 / len(df):.4f}%), "
            f"total_input_tokens: {total_input_tokens:,}, "
            f"total_output_tokens: {total_output_tokens:,}"
        )


if __name__ == '__main__':
    generate_word_dictionary()
