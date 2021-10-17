import os
from sqlalchemy import Column, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.sqltypes import BIGINT, Boolean, String


def create_database_engine():
    return create_engine(os.getenv("POSTGRES_DB_URL"), echo=True, future=True)


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


class CustomCommmands(Base):
    __tablename__ = 'custom_commands'
    server_id = Column(BIGINT)
    server_name = Column(String)
    server_id_command = Column(String, primary_key=True) # server id + command name
    command_name = Column(String)
    command_return = Column(String)
    image = Column(Boolean) # Flag for whether or not we need to send an embed 
