from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.sqltypes import BIGINT, Boolean, String


Base = declarative_base()

# One server has:
#   - Many verifieds
#   - Many Custom Commands
#   - Many Sheet Tethers
#   - One prefix (I can keep this on its own table for now if it makes it easier)


class Servers(Base):
    __tablename__ = 'test_servers'
    server_id = Column(BIGINT, primary_key=True)
    server_name = Column(String)
    verifieds = relationship("Verifieds", cascade="all, delete", passive_deletes=True)
    custom_commands = relationship("CustomCommands", cascade="all, delete")
    sheet_tethers = relationship("SheetTethers", cascade="all, delete")


class Verifieds(Base):
    __tablename__ = 'test_verifieds'
    role_id = Column(BIGINT, primary_key=True)
    role_name = Column(String)
    server_id = Column(BIGINT, ForeignKey('test_servers.server_id', ondelete="CASCADE"))
    permissions = Column(String)

# enum for the different permissions in Verifieds
VERIFIED_CATEGORIES = ["Verified", "Tester"]


class CustomCommands(Base):
    __tablename__ = 'test_custom_commands'
    server_id = Column(BIGINT, ForeignKey('test_servers.server_id', ondelete="CASCADE"))
    server_id_command = Column(String, primary_key=True) # server id + command name
    command_name = Column(String)
    command_return = Column(String)
    image = Column(Boolean) # Flag for whether or not we need to send an embed 


class SheetTethers(Base):
    __tablename__ = 'sheet_tethers'
    channel_id = Column(BIGINT, primary_key=True)
    channel_name = Column(String)
    sheet_link = Column(String)
    server_id = Column(BIGINT, ForeignKey('test_servers.server_id', ondelete="CASCADE"))


# TODO: Should I link this to the servers table?
class Prefixes(Base):
    __tablename__ = 'prefixes'
    server_id = Column(BIGINT, primary_key=True)
    server_name = Column(String)
    prefix = Column(String)
