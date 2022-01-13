from xmlrpc import server
from sqlalchemy import Column, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.sqltypes import BIGINT, Boolean, String
import os

print(os.getenv("POSTGRES_DB_URL"))
DATABASE_ENGINE = create_engine(os.getenv("POSTGRES_DB_URL"), echo=False, future=True)
Base = declarative_base()

# TODO: Right now, each of our databases is being treated as a key-value store.
# It would be great to take advantage of using postgres as a relational db


class Verifieds(Base):
    __tablename__ = "verifieds"
    server_id = Column(BIGINT)
    server_name = Column(String)
    role_id = Column(BIGINT, primary_key=True)
    role_name = Column(String)
    permissions = Column(String)


# enum for the different permissions in Verifieds
VERIFIED = "Verified"
TRUSTED = "Trusted"
TESTER = "Tester"
VERIFIED_CATEGORIES = [VERIFIED, TRUSTED, TESTER]


class CustomCommands(Base):
    __tablename__ = "custom_commands"
    server_id = Column(BIGINT)
    server_name = Column(String)
    server_id_command = Column(String, primary_key=True)  # server id + command name
    command_name = Column(String)
    command_return = Column(String)
    image = Column(Boolean)  # Flag for whether or not we need to send an embed


class SheetTethers(Base):
    __tablename__ = "sheet_tethers"
    server_id = Column(BIGINT)
    server_name = Column(String)
    channel_or_cat_id = Column(BIGINT, primary_key=True)
    channel_or_cat_name = Column(String)
    sheet_link = Column(String)


class SheetTemplates(Base):
    __tablename__ = "sheet_templates"
    server_id = Column(BIGINT, primary_key=True)
    server_name = Column(String)
    sheet_link = Column(String)


class Prefixes(Base):
    __tablename__ = "prefixes"
    server_id = Column(BIGINT, primary_key=True)
    server_name = Column(String)
    prefix = Column(String)


Base.metadata.create_all(DATABASE_ENGINE)
