import os
from sqlalchemy import Column, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.sqltypes import BIGINT, Integer, String

# text, Table, Column, Integer, String, insert, MetaData
# from sqlalchemy.orm import Session

# with Session(engine) as session:
#     result = session.execute(text("SELECT * FROM verifieds where server_id='820327073213186079'"))
#     for row in result:
#         print(f"Verified role ids: {','.join(row['verified_role_ids'])}")

def create_database_engine():
    return create_engine(os.getenv("DATABASE_URL"), echo=True, future=True)


Base = declarative_base()


class Verifieds(Base):
    __tablename__ = 'verifieds'
    role_id = Column(BIGINT, primary_key=True)
    role_name = Column(String)
    server_id = Column(BIGINT)
    server_name = Column(String)
    category = Column(String)

# enum
VERIFIED_CATEGORIES = ["Verified", "Tester"]


class Prefixes(Base):
    __tablename__ = 'prefixes'
    server_id = Column(BIGINT, primary_key=True)
    server_name = Column(String)
    prefix = Column(String)
