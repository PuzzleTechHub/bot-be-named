"""Hydra commands that read or write single Overview cells do it in worker threads, so the
bot keeps answering other commands while Google responds."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from modules.hydra.cog import HydraCog
from tests.fakes import FakeCategory, FakeChannel, FakeContext, FakeGuild, watch_threads
from utils import google_utils, sheets_constants
from utils.sheet_command_base import SheetCommandBase

ROW = 4


class FakeOverviewWorksheet:
    id = 0

    def __init__(self, cells):
        self.cells = cells

    def acell(self, label):
        return SimpleNamespace(value=self.cells.get(label))

    def update_acell(self, label, value):
        self.cells[label] = value


@pytest.fixture
def cog(monkeypatch):
    monkeypatch.setattr(google_utils, "create_gspread_client", MagicMock())
    return HydraCog(MagicMock())


@pytest.fixture
def worksheet(monkeypatch):
    worksheet = FakeOverviewWorksheet({})
    overview = SimpleNamespace(worksheet=worksheet)

    async def get_sheet_context(self):
        return "sheet link", overview, ROW

    monkeypatch.setattr(SheetCommandBase, "get_sheet_context", get_sheet_context)
    return worksheet


@pytest.fixture
def ctx():
    category = FakeCategory(100, "GPH 1 Puzzles")
    ctx = FakeContext(
        FakeGuild(categories=[category]), FakeChannel(201, "puzzle-1", category)
    )

    async def add_reaction(reaction):
        pass

    ctx.message.add_reaction = add_reaction
    return ctx


@pytest.mark.parametrize(
    "command, column, args",
    [
        ("roundhydra", sheets_constants.ROUND_COLUMN, ("Round 2",)),
        ("noteshydra", sheets_constants.NOTES_COLUMN, ("needs eyes",)),
    ],
)
async def test_set_cell_off_the_event_loop(
    cog, ctx, worksheet, monkeypatch, command, column, args
):
    calls = watch_threads(monkeypatch, worksheet, "acell", "update_acell")

    await getattr(cog, command).callback(cog, ctx, *args)

    assert worksheet.cells[f"{column}{ROW}"] == args[0]
    assert [name for name, _ in calls] == ["acell", "update_acell"]
    assert [name for name, on_loop in calls if on_loop] == []
    assert ctx.sent_embeds[-1].fields[0].name == "Success"


@pytest.mark.parametrize("command", ["roundhydra", "noteshydra"])
async def test_read_cell_off_the_event_loop(cog, ctx, worksheet, monkeypatch, command):
    calls = watch_threads(monkeypatch, worksheet, "acell")

    await getattr(cog, command).callback(cog, ctx)

    assert calls == [("acell", False)]
