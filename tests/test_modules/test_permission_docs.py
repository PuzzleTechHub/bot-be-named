"""Check the "Permission Category : ..." docstring line shown by ~help actually matches the command"""

import importlib
import re
from pathlib import Path
from unittest.mock import MagicMock

import nextcord
import pytest
from nextcord.ext import commands

from utils import command_predicates, google_utils

COG_MODULES = sorted(
    f"modules.{path.parent.name}.cog"
    for path in (Path(__file__).parents[2] / "modules").glob("*/cog.py")
)
LINE_RE = re.compile(r"Permission Category ?: ?(.*?)\s*$", re.M)


@pytest.fixture
async def bot(monkeypatch):
    monkeypatch.setattr(google_utils, "create_gspread_client", MagicMock())
    monkeypatch.setattr(google_utils, "get_gdrive_credentials", MagicMock())
    intents = nextcord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix="~", intents=intents, help_command=None)
    for name in COG_MODULES:
        importlib.import_module(name).setup(bot)
    return bot


async def test_permission_lines_match_the_checks(bot):
    wrong = []
    for command in bot.walk_commands():
        expected = command_predicates.permission_category(command)
        lines = LINE_RE.findall(command.help or "")
        if expected is None:
            if lines:
                wrong.append(f"{command}: says {lines} but anyone can use it")
        elif lines != [expected]:
            wrong.append(f"{command}: says {lines}, should say {expected!r}")
    assert wrong == []


async def test_every_check_has_a_category(bot):
    checks = {
        check.__qualname__.split(".")[0]
        for command in bot.walk_commands()
        for check in command.checks
    }
    assert checks <= set(command_predicates.PERMISSION_CATEGORIES)


def test_permission_category_of_a_public_command():
    @commands.command()
    async def hello(ctx):
        pass

    assert command_predicates.permission_category(hello) is None


def test_permission_category_with_an_unknown_check():
    @commands.check(lambda ctx: True)
    @commands.command()
    async def hello(ctx):
        pass

    with pytest.raises(ValueError):
        command_predicates.permission_category(hello)
