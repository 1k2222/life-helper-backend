import re

import spacy
from sqlalchemy.engine.create import create_engine
from sqlalchemy.orm.session import sessionmaker

from scripts.models import BaseModel, Explanation

import pandas as pd

if __name__ == '__main__':
    engine = create_engine('sqlite:///assets/the_economist/sqlite_database.db')
    BaseModel.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    explanation_records = Session().query(Explanation).order_by(Explanation.id.asc()).all()
    bad_records = 0
    re_words = re.compile(r'[a-zA-Z]')
    re_non_word_characters = re.compile(r'[-*.0-9]')
    word_count = {}
    nlp = spacy.load("en_core_web_trf")
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
            if not re_words.search(line):
                continue
            line = line.strip().strip('|')
            parts = [x.strip() for x in line.split('|')]
            if len(parts) != 2 or not parts[0] or not parts[1]:
                break
            parts[0] = re_non_word_characters.sub('', parts[0])
            word_count[parts[0]] = word_count.get(parts[0], 0) + 1
    words_str = ' '.join(word_count.keys())
    nlp_result = nlp(words_str)
    lemma_map, lemma_word_count = {}, {}
    for token in nlp_result:
        lemma_map[token.text] = token.lemma_
    for k, v in word_count.items():
        word = lemma_map.get(k, k)
        lemma_word_count[word] = lemma_word_count.get(word, 0) + v

    df = pd.DataFrame({"word": lemma_word_count.keys(), "count": lemma_word_count.values()})
    df.to_csv('./assets/the_economist/word_count.csv', index=False)
