"""Every command's docstring follows the layout ~help reads:

    One or more sentences on what the command does.

    Any notes, in their own paragraphs.

    Permission Category : Solver Roles only.      (left out when anyone can use it)
    Usage: `~command example`
    Usage: `~command other example` (an optional note in brackets)

A "Usage:" line on its own, followed by lines up to the end, is one example spread over several
lines (shown as a code block).
"""

import importlib
import re
from pathlib import Path
from unittest.mock import MagicMock

import nextcord
import pytest
from nextcord.ext import commands

from modules.help import help_command
from utils import google_utils

COG_MODULES = sorted(
    f"modules.{path.parent.name}.cog"
    for path in (Path(__file__).parents[3] / "modules").glob("*/cog.py")
)
USAGE_RE = re.compile(r"^Usage: `~(?P<name>[^\s`]+)[^`]*`( \(.+\))?$")


@pytest.fixture
def all_commands(monkeypatch):
    monkeypatch.setattr(google_utils, "create_gspread_client", MagicMock())
    monkeypatch.setattr(google_utils, "get_gdrive_credentials", MagicMock())
    intents = nextcord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix="~", intents=intents, help_command=None)
    for name in COG_MODULES:
        importlib.import_module(name).setup(bot)
    return list(bot.walk_commands())


def problems(command: commands.Command) -> list:
    """What is wrong with the command's docstring layout, empty when nothing is."""
    lines = [
        line.strip() for line in help_command.unwrap(command.help or "").splitlines()
    ]
    names = {command.name, *command.aliases}
    usage_at = [i for i, line in enumerate(lines) if line.startswith("Usage")]
    if not lines or lines[0].startswith(("Usage", "Permission Category")):
        return ["no summary first"]
    if not usage_at:
        return ["no Usage line"]
    found = []
    first = usage_at[0]
    above = lines[first - 1] if first else ""
    has_permission = any(line.startswith("Permission Category") for line in lines)
    if has_permission and not above.startswith("Permission Category"):
        found.append("Permission Category line is not right above the Usage lines")
    for index, line in enumerate(lines[first:], start=first):
        if not line:
            found.append("blank line or text after the Usage lines")
            break
        if line == "Usage:":
            block = lines[index + 1 :]
            if not block or block[0].split()[0].lstrip("~") not in names:
                found.append("multi-line Usage example doesn't start with the command")
            if any(not row for row in block):
                found.append("blank line in or after a multi-line Usage example")
            break
        match = USAGE_RE.match(line)
        if match is None:
            found.append(f"badly formatted: {line}")
        elif match["name"] not in names:
            found.append(f"example isn't for this command: {line}")
    return found


def test_every_docstring_follows_the_layout(all_commands):
    wrong = {
        command.qualified_name: problems(command)
        for command in all_commands
        if problems(command)
    }
    assert wrong == {}


@pytest.mark.parametrize(
    ("doc", "expected"),
    [
        ("Does a thing.\n\nUsage: `~thing`", []),
        ("Does a thing.\n\nUsage: `~alias x` (a note)", []),
        ("Does a thing.\n\nUsage:\n~thing\nA\nB", []),
        ("Usage: `~thing`", ["no summary first"]),
        ("Does a thing.", ["no Usage line"]),
        ("Does a thing.\n\nUsage : `~thing`", ["badly formatted: Usage : `~thing`"]),
        ("Does a thing.\n\nUsage: ~thing x", ["badly formatted: Usage: ~thing x"]),
        (
            "Does a thing.\n\nUsage: `~other`",
            ["example isn't for this command: Usage: `~other`"],
        ),
        (
            "Does a thing.\n\nUsage: `~thing`\n\nA note.",
            ["blank line or text after the Usage lines"],
        ),
        (
            "Does a thing.\n\nPermission Category : Admin only.\n\nA note.\n\nUsage: `~thing`",
            ["Permission Category line is not right above the Usage lines"],
        ),
    ],
)
def test_layout_rules(doc, expected):
    @commands.command(name="thing", aliases=["alias"], help=doc)
    async def thing(ctx):
        pass

    assert problems(thing) == expected
