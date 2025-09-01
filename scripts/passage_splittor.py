import datetime
import glob
import os.path
import re

import spacy
import tiktoken
from sqlalchemy.engine.create import create_engine
from sqlalchemy.orm.session import sessionmaker

from scripts.defines import MONTH_ENGLISH
from scripts.models import BaseModel, Paragraphs
from scripts.utils import get_ordinal_suffix
from loguru import logger


def remove_economist_date(file_name, raw_text):
    date_str = file_name.lstrip("The_Economist_").rstrip(".md")
    date_val = datetime.datetime.strptime(date_str, '%Y_%m_%d').date()
    target_str = f'The Economist {MONTH_ENGLISH[date_val.month - 1]}'
    lines = raw_text.split('\n')
    new_lines = []
    for line in lines:
        if target_str in line:
            continue
        new_lines.append(line)
    return '\n'.join(new_lines)


def remove_singular_symbols(text):
    text = re.sub(r'[\u4e00-\u9fff\uFF00-\uFFEF。？！，：；]', '', text)
    lines = text.split('\n')
    re_letters = re.compile(r'[a-zA-Z]')
    new_lines = []
    for line in lines:
        if line.strip() and line.strip() != '---' and not re_letters.search(line):
            continue
        new_lines.append(line)
    return '\n'.join(new_lines)


def remove_figures(raw_text):
    lines = raw_text.split('\n')
    new_lines = []
    for line in lines:
        if re.match(r'!\[Figure]\(figures/.+', line):
            continue
        new_lines.append(line)
    return '\n'.join(new_lines)


def remove_contents(raw_text):
    pages = raw_text.split('\n---\n')
    content_page_id = -1
    for i, page in enumerate(pages):
        res = re.search(r'\d*\s*Contents', page.strip())
        if res:
            content_page_id = i
    return content_page_id + 1, '\n---\n' + '\n---\n'.join(pages[content_page_id + 1:])


def remove_tables(raw_text):
    return re.sub(r'<table>.+?</table>', '', raw_text)


def cleanup_markdown(input_file_path, output_file_path):
    text = open(input_file_path, 'r').read()
    text = remove_economist_date(os.path.basename(input_file_path), text)
    text = remove_figures(text)
    content_page_count, text = remove_contents(text)
    text = remove_tables(text)
    text = remove_singular_symbols(text)
    with open(output_file_path, 'w') as f:
        f.write(text)
    return content_page_count, text


if __name__ == '__main__':
    engine = create_engine('sqlite:///assets/the_economist/sqlite_database.db')
    BaseModel.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    files = glob.glob('./assets/the_economist/ocr_results/markdown/*.md')
    files.sort()

    encoder = tiktoken.encoding_for_model('gpt-4o')

    re_incomplete_paragraph = re.compile(r'[a-zA-Z\-]\s*$')

    for file_ind, filepath in enumerate(files):
        filename = os.path.basename(filepath)
        logger.info(f"Processing '{filename} ({file_ind + 1}/{len(files)})...'")
        content_page_count, text = cleanup_markdown(filepath,
                                f'./assets/the_economist/cleaned_md_articles/{filename}')
        pages = text.split('\n---\n')
        for i, page in enumerate(pages):
            raw_paragraphs = [x for x in page.split('\n') if x.split()]
            paragraphs, buf = [], ''
            for item in raw_paragraphs:
                buf += item
                if not re_incomplete_paragraph.search(item):
                    if buf:
                        paragraphs.append(buf)
                    buf = ''
            if buf:
                paragraphs.append(buf)

            paragraphs = [x for x in paragraphs if x]
            records = []

            for j, para in enumerate(paragraphs):
                record = Paragraphs(
                    file_name=filename,
                    page_id=content_page_count + i + 1,
                    paragraph_id=j,
                    content=para,
                    word_count=len(para.split()),
                    token_count=len(encoder.encode(para))
                )
                records.append(record)
            if records:
                session = Session()
                session.add_all(records)
                session.commit()
