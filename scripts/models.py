from sqlalchemy.orm.decl_api import declarative_base
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Integer, String

BaseModel = declarative_base()


class Paragraphs(BaseModel):
    __tablename__ = "paragraphs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_name = Column(String)
    page_id = Column(Integer)
    paragraph_id = Column(Integer)
    content = Column(String)
    word_count = Column(Integer)
    token_count = Column(Integer)


class Explanation(BaseModel):
    __tablename__ = "explanation"
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_name = Column(String)
    page_id = Column(Integer)
    start_paragraph_id = Column(Integer)
    end_paragraph_id = Column(Integer)
    explanation_content = Column(String)
    llm_model = Column(String)
    input_token_count = Column(Integer)
    output_token_count = Column(Integer)
