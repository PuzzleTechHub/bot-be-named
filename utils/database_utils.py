import os
from sqlalchemy import Column, create_engine
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.sqltypes import BIGINT, Boolean, String



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


def create_database_engine():
    return create_engine(os.getenv("POSTGRES_DB_URL"), echo=False, future=True)


DATABASE_ENGINE = create_database_engine()


def get_prefixes():
    prefixes = {}
    with Session(DATABASE_ENGINE) as session:
        result = session.query(Prefixes).all()
        for row in result:
            prefixes[row.server_id] = row.prefix
    return prefixes


def get_verifieds():
    verifieds = {}
    with Session(DATABASE_ENGINE) as session:
        result = session.query(Verifieds).filter_by(category="Verified").all()
        for row in result:
            if row.server_id in verifieds:
                verifieds[row.server_id].append(row.role_id)
            else:
                verifieds[row.server_id] = [row.role_id] 
    return verifieds


def get_custom_commands():
    custom_commands = {}
    with Session(DATABASE_ENGINE) as session:
        result = session.query(CustomCommmands).all()
        for row in result:
            if row.server_id not in custom_commands:
                custom_commands[row.server_id] = {}
            custom_commands[row.server_id][row.command_name.lower()] = (row.command_return, row.image)
    return custom_commands 


PREFIXES = get_prefixes()
VERIFIEDS = get_verifieds()
CUSTOM_COMMANDS = get_custom_commands()
