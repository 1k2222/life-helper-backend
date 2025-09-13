import json
import re

import spacy
from sqlalchemy.engine.create import create_engine
from sqlalchemy.orm.session import sessionmaker

from scripts.models import BaseModel, Explanation, Paragraphs

import pandas as pd
from loguru import logger

real_word_cache_file_path = './assets/the_economist/real_word.json'
word_lemma_cache_file_path = './assets/the_economist/word_lemma.json'


def get_easy_word_set():
    easy_words = []
    file_list = ['1 初中-乱序.txt', '2 高中-乱序.txt']
    for file in file_list:
        lines = open(f"./assets/word_list/{file}", "r").read().split("\n")
        for line in lines:
            line = line.strip()
            if re.match(r'[A-Z]', line):
                continue
            result = re.search(r'^[A-Za-z]+', line)
            if not result:
                continue
            word = result.group(0)
            easy_words.append(word)
    return set(easy_words)


def count_real_words(session_cls, nlp, easy_words):
    paragraph_records = session_cls().query(Paragraphs).order_by(Paragraphs.id.asc()).all()
    re_word = re.compile(r'\b[a-zA-Z]+(?:-[a-zA-Z]+)*\b')
    # paragraphs_already_counted_real_words = set()
    # for record in real_word_count_records:
    #     paragraphs_already_counted_real_words.add(record.paragraph_id)

    last_para_id, all_word_count = 0, {}
    try:
        with open(real_word_cache_file_path, 'r') as f:
            obj = json.loads(f.read())
            last_para_id, all_word_count = obj['last_para_id'], obj['all_word_count']
    except Exception:
        pass

    for i, record in enumerate(paragraph_records):
        if record.id < last_para_id:
            continue
        nlp_result = nlp(record.content)
        for token in nlp_result:
            word = token.lemma_.lower()
            if not re_word.match(word) or word in easy_words:
                continue
            all_word_count[word] = all_word_count.get(word, 0) + 1
        last_para_id = record.id
        if (i + 1) % 1000 == 0:
            with open(real_word_cache_file_path, 'w') as f:
                f.write(json.dumps({"last_para_id": last_para_id, "all_word_count": all_word_count}))
            logger.info(
                f"real word count {len(all_word_count)}, progress: {i + 1}/{len(paragraph_records)} ({(i + 1) * 100.0 / len(paragraph_records):.4f}%)")


def count_word_from_explanation(nlp):
    real_word_count = {}
    with open(real_word_cache_file_path, 'r') as f:
        obj = json.loads(f.read())
        real_word_count = obj["all_word_count"]
    explanation_records = Session().query(Explanation).order_by(Explanation.id.asc()).all()
    re_letter = re.compile(r'[a-zA-Z]')
    re_non_word_characters = re.compile(r'[-*.0-9]')
    word_count = {}

    for record in explanation_records:
        explanation_content = record.explanation_content
        word_list_lines, word_list_start_pos = explanation_content.split('\n'), -1
        for i, line in enumerate(word_list_lines):
            if 'Word List' in line:
                word_list_start_pos = i
                break
        if word_list_start_pos < 0:
            continue
        word_list_lines = word_list_lines[word_list_start_pos + 1:]
        for line in word_list_lines:
            if not re_letter.search(line):
                continue
            line = line.strip().strip('|')
            parts = [x.strip() for x in line.split('|')]
            if len(parts) != 2 or not parts[0] or not parts[1]:
                break
            parts[0] = re_non_word_characters.sub('', parts[0])
            word_count[parts[0]] = word_count.get(parts[0], 0) + 1
    lemma_map, lemma_word_count, real_word_count_column = {}, {}, []
    lemma_map = {}
    try:
        with open(word_lemma_cache_file_path, 'r') as f:
            lemma_map = json.loads(f.read())
    except Exception:
        pass
    for i, (k, v) in enumerate(word_count.items()):
        if (i + 1) % 1000 == 0:
            with open(word_lemma_cache_file_path, 'w') as f:
                f.write(json.dumps(lemma_map))
            logger.info(f"Word Count: {i + 1}/{len(word_count)} finished")
        words = k.split()
        for word in words:
            if word not in lemma_map:
                nlp_result = nlp(word)
                lemma_map[word] = nlp_result[0].lemma_
            word = lemma_map[word]
            if word in easy_words:
                continue
            lemma_word_count[word] = lemma_word_count.get(word, 0) + v
    for word in lemma_word_count.keys():
        real_word_count_column.append(real_word_count.get(word, 0))

    df = pd.DataFrame(
        {"word": lemma_word_count.keys(), "count": lemma_word_count.values(), "real_count": real_word_count_column})
    df.to_csv('./assets/the_economist/word_count_2023_07.csv', index=False)


if __name__ == '__main__':
    engine = create_engine('sqlite:///assets/the_economist/sqlite_database.db')
    nlp = spacy.load("en_core_web_trf")
    nlp.max_length = 10000000
    easy_words = get_easy_word_set()
    BaseModel.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    # count_real_words(Session, nlp, easy_words)
    count_word_from_explanation(nlp)
