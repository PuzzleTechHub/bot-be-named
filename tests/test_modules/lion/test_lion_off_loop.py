"""Lion's sheet commands make their Google calls in worker threads, so the bot keeps
answering other commands while Google responds."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from modules.lion.cog import LionCog
from tests.fakes import FakeCategory, FakeChannel, FakeContext, FakeGuild, watch_threads
from utils import google_utils, sheet_utils
from utils.sheet_command_base import SheetCommandBase

SHEET = "https://docs.google.com/spreadsheets/d/hunt"
TAB_ID = 7
ROW = 4


class FakeTab:
    def __init__(self, tab_id):
        self.id = tab_id
        self.moved_to = None

    def update_index(self, index):
        self.moved_to = index


class FakeSpreadsheet:
    def __init__(self):
        self.tabs = [FakeTab(0), FakeTab(TAB_ID), FakeTab(9)]
        self.batches = []

    def worksheets(self):
        return list(self.tabs)

    def batch_update(self, body):
        self.batches.append(body)


class FakeOverview:
    def __init__(self, spreadsheet):
        self.spreadsheet = spreadsheet
        self.worksheet = SimpleNamespace(id=0)
        self.overview_data = [["", "E"], [], []]

    def get_cell_value(self, label):
        return str(TAB_ID) if label.endswith(str(ROW)) else "E"


@pytest.fixture
def cog(monkeypatch):
    monkeypatch.setattr(google_utils, "create_gspread_client", MagicMock())
    return LionCog(MagicMock())


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


def _not_on_loop(calls):
    assert calls
    assert [name for name, on_loop in calls if on_loop] == []


async def test_sheetmta_generic_off_the_event_loop(cog, ctx, monkeypatch):
    spreadsheet = FakeSpreadsheet()
    overview = FakeOverview(spreadsheet)

    async def get_sheet_context(self):
        return SHEET, overview, ROW

    monkeypatch.setattr(SheetCommandBase, "get_sheet_context", get_sheet_context)
    calls = watch_threads(monkeypatch, spreadsheet, "worksheets")
    watch_threads(monkeypatch, spreadsheet.tabs[1], "update_index", calls=calls)

    await cog.sheetmta_generic(ctx)

    assert spreadsheet.tabs[1].moved_to == 3
    assert ctx.sent_embeds[-1].fields[0].name == "Success"
    assert [name for name, _ in calls] == ["worksheets", "update_index"]
    _not_on_loop(calls)


async def test_puzzlelion_off_the_event_loop_and_opens_sheet_once(
    cog, ctx, monkeypatch
):
    spreadsheet = FakeSpreadsheet()

    async def get_overview(gspread_client, ctx, sheet_link):
        return FakeOverview(spreadsheet)

    monkeypatch.setattr(sheet_utils, "get_overview", get_overview)
    calls = watch_threads(monkeypatch, spreadsheet, "batch_update")

    await cog.puzzlelion(
        ctx, "puzzle-1", "", SHEET, FakeTab(TAB_ID), FakeChannel(201, "puzzle-1")
    )

    assert len(spreadsheet.batches) == 1
    # The Overview's spreadsheet is reused instead of opening the sheet again
    cog.gspread_client.open_by_url.assert_not_called()
    _not_on_loop(calls)
