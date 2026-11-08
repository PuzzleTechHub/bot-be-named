import os
from sqlalchemy import Column, create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.sqltypes import BIGINT, Boolean, String

# Your link may use postgres:// everywhere but it's deprecated by SQLAlchemy.
uri = os.getenv("DATABASE_URL")
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

print(uri)
DATABASE_ENGINE = create_engine(uri, echo=False, future=True)
Base = declarative_base()


class Verifieds(Base):
    __tablename__ = "verifieds"
    server_id = Column(BIGINT)
    server_name = Column(String)
    role_id = Column(BIGINT)
    role_name = Column(String)
    permissions = Column(String)
    role_id_permissions = Column(String, primary_key=True)


# enum for the different permissions in Verifieds
VERIFIED = "Verified"
SOLVER = "Solver"
TRUSTED = "Trusted"
TESTER = "Tester"
VERIFIED_CATEGORIES = [VERIFIED, TRUSTED, TESTER, SOLVER]


class CustomCommands(Base):
    __tablename__ = "custom_commands"
    server_id = Column(BIGINT)
    server_name = Column(String)
    server_id_command = Column(String, primary_key=True)  # server id + command name
    command_name = Column(String)
    command_return = Column(String)
    image = Column(Boolean)  # Flag for whether or not we need to send an embed
    responses = Column(JSONB(none_as_null=True))


class SheetTethers(Base):
    __tablename__ = "sheet_tethers"
    server_id = Column(BIGINT)
    server_name = Column(String)
    channel_or_cat_id = Column(BIGINT, primary_key=True)
    channel_or_cat_name = Column(String)
    sheet_link = Column(String)


class Prefixes(Base):
    __tablename__ = "prefixes"
    server_id = Column(BIGINT, primary_key=True)
    server_name = Column(String)
    prefix = Column(String)


class SummaryGrants(Base):
    __tablename__ = "summary_grants"
    server_id = Column(BIGINT)
    server_name = Column(String)
    channel_id = Column(BIGINT)
    channel_name = Column(String)
    role_id = Column(BIGINT)
    role_name = Column(String)
    channel_id_role_id = Column(String, primary_key=True)


class SolveStreams(Base):
    __tablename__ = "solve_streams"
    server_id = Column(BIGINT)
    server_name = Column(String)
    # A sheet can post to several channels, so (sheet_key, channel_id) is the key
    channel_id = Column(BIGINT, primary_key=True)
    channel_name = Column(String)
    sheet_key = Column(String, primary_key=True)  # spreadsheet id from sheet link


class ChannelMirrors(Base):
    __tablename__ = "channel_mirrors"
    server_id = Column(BIGINT)
    server_name = Column(String)
    # A channel can be mirrored into several channels, so (source, target) is the key
    source_channel_id = Column(BIGINT, primary_key=True)
    source_channel_name = Column(String)
    target_channel_id = Column(BIGINT, primary_key=True)
    target_channel_name = Column(String)


Base.metadata.create_all(DATABASE_ENGINE)
