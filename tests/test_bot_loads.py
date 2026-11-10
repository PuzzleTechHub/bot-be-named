import importlib
from collections import Counter
from pathlib import Path
from unittest.mock import MagicMock

import nextcord
import pytest
from nextcord.ext import commands

from utils import google_utils

COG_MODULES = sorted(
    f"modules.{path.parent.name}.cog"
    for path in (Path(__file__).parent.parent / "modules").glob("*/cog.py")
)


@pytest.fixture
def bot(monkeypatch):
    monkeypatch.setattr(google_utils, "create_gspread_client", MagicMock())
    monkeypatch.setattr(google_utils, "get_gdrive_credentials", MagicMock())
    intents = nextcord.Intents.default()
    intents.message_content = True
    intents.members = True
    return commands.Bot(command_prefix="~", intents=intents)


def test_every_cog_loads(bot):
    assert len(COG_MODULES) >= 15
    for name in COG_MODULES:
        importlib.import_module(name).setup(bot)
    assert len(bot.cogs) == len(COG_MODULES)


def test_no_command_name_or_alias_used_twice(bot):
    for name in COG_MODULES:
        importlib.import_module(name).setup(bot)
    names = Counter()
    for command in bot.walk_commands():
        names.update([command.qualified_name, *command.aliases])
    assert [name for name, count in names.items() if count > 1] == []


@pytest.mark.parametrize(
    "command",
    [
        "statushydra",
        "catsummaryhydra",
        "watchcat",
        "addcc",
        "reloaddatabasecache",
        "help",
    ],
)
def test_key_commands_exist(bot, command):
    for name in COG_MODULES:
        importlib.import_module(name).setup(bot)
    assert bot.get_command(command) is not None
