import os

from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql.sqltypes import BIGINT, Boolean, String

# Your link may use postgres:// everywhere but it's deprecated by SQLAlchemy.
# Name the driver too: SQLAlchemy 2.1 picks psycopg (v3) for a plain postgresql://,
# but we install psycopg2 (psycopg2-binary), which 2.0 picked by default.
uri = os.getenv("DATABASE_URL")
if uri and uri.startswith(("postgres://", "postgresql://")):
    uri = "postgresql+psycopg2://" + uri.split("://", 1)[1]

# Connecting is held off. SQLAlchemy only connects on first use. Tables are created in database.load_all().
DATABASE_ENGINE = create_engine(uri, echo=False, future=True)


class Base(DeclarativeBase):
    pass


# Columns are Optional (nullable) unless they are part of the primary key, as before the
# move to `Mapped`: a plain Mapped[int] would make the column NOT NULL on new installs.


class Verifieds(Base):
    __tablename__ = "verifieds"
    server_id: Mapped[int | None] = mapped_column(BIGINT)
    server_name: Mapped[str | None] = mapped_column(String)
    role_id: Mapped[int | None] = mapped_column(BIGINT)
    role_name: Mapped[str | None] = mapped_column(String)
    permissions: Mapped[str | None] = mapped_column(String)
    role_id_permissions: Mapped[str] = mapped_column(String, primary_key=True)


# enum for the different permissions in Verifieds
VERIFIED = "Verified"
SOLVER = "Solver"
TRUSTED = "Trusted"
TESTER = "Tester"
VERIFIED_CATEGORIES = [VERIFIED, TRUSTED, TESTER, SOLVER]


class CustomCommands(Base):
    __tablename__ = "custom_commands"
    server_id: Mapped[int | None] = mapped_column(BIGINT)
    server_name: Mapped[str | None] = mapped_column(String)
    # server id + command name
    server_id_command: Mapped[str] = mapped_column(String, primary_key=True)
    command_name: Mapped[str | None] = mapped_column(String)
    command_return: Mapped[str | None] = mapped_column(String)
    # Flag for whether or not we need to send an embed
    image: Mapped[bool | None] = mapped_column(Boolean)
    responses: Mapped[list[str] | None] = mapped_column(JSONB(none_as_null=True))


class SheetTethers(Base):
    __tablename__ = "sheet_tethers"
    server_id: Mapped[int | None] = mapped_column(BIGINT)
    server_name: Mapped[str | None] = mapped_column(String)
    channel_or_cat_id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    channel_or_cat_name: Mapped[str | None] = mapped_column(String)
    sheet_link: Mapped[str | None] = mapped_column(String)


class Prefixes(Base):
    __tablename__ = "prefixes"
    server_id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    server_name: Mapped[str | None] = mapped_column(String)
    prefix: Mapped[str | None] = mapped_column(String)


class SummaryGrants(Base):
    __tablename__ = "summary_grants"
    server_id: Mapped[int | None] = mapped_column(BIGINT)
    server_name: Mapped[str | None] = mapped_column(String)
    channel_id: Mapped[int | None] = mapped_column(BIGINT)
    channel_name: Mapped[str | None] = mapped_column(String)
    role_id: Mapped[int | None] = mapped_column(BIGINT)
    role_name: Mapped[str | None] = mapped_column(String)
    channel_id_role_id: Mapped[str] = mapped_column(String, primary_key=True)


class SolveStreams(Base):
    __tablename__ = "solve_streams"
    server_id: Mapped[int | None] = mapped_column(BIGINT)
    server_name: Mapped[str | None] = mapped_column(String)
    # A sheet can post to several channels, so (sheet_key, channel_id) is the key
    channel_id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    channel_name: Mapped[str | None] = mapped_column(String)
    # spreadsheet id from sheet link
    sheet_key: Mapped[str] = mapped_column(String, primary_key=True)


class ChannelMirrors(Base):
    __tablename__ = "channel_mirrors"
    server_id: Mapped[int | None] = mapped_column(BIGINT)
    server_name: Mapped[str | None] = mapped_column(String)
    # A channel can be mirrored into several channels, so (source, target) is the key
    source_channel_id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    source_channel_name: Mapped[str | None] = mapped_column(String)
    target_channel_id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    target_channel_name: Mapped[str | None] = mapped_column(String)
