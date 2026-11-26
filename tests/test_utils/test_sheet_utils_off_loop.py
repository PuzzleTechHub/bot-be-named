"""The Hydra sheet helpers make their Google Sheets calls and database queries in worker
threads, so one slow sheet doesn't freeze every other command."""

import gspread
import pytest

import database

from tests.fakes import (
    FakeCategory,
    FakeChannel,
    FakeContext,
    FakeGuild,
    FakeMessage,
    add_tether,
    watch_threads,
)
from utils import discord_utils, sheet_utils

SHEET = "https://docs.google.com/spreadsheets/d/hunt/edit"
TAB_ID = 7


class FakeTab:
    def __init__(self, title, tab_id, index, spreadsheet=None):
        self.title = title
        self.id = tab_id
        self.index = index
        self.spreadsheet = spreadsheet
        self.moved_to = None

    def update_index(self, index):
        self.moved_to = index


class FakeSpreadsheet:
    title = "Hunt"
    url = SHEET

    def __init__(self):
        self.tabs = [
            FakeTab("Overview", 0, 0, self),
            FakeTab("Template", 1, 1, self),
            FakeTab("Meta Template", 2, 2, self),
        ]
        self.batches = []

    def worksheet(self, title):
        for tab in self.tabs:
            if tab.title == title:
                return tab
        raise gspread.exceptions.WorksheetNotFound(title)

    def duplicate_sheet(self, source_sheet_id, new_sheet_name, insert_sheet_index):
        tab = FakeTab(new_sheet_name, 100 + len(self.tabs), insert_sheet_index, self)
        self.tabs.append(tab)
        return tab

    def worksheets(self):
        return list(self.tabs)

    def batch_update(self, body):
        self.batches.append(body)
        for request in body["requests"]:
            if "duplicateSheet" in request:
                new = request["duplicateSheet"]
                self.tabs.append(
                    FakeTab(
                        new["newSheetName"],
                        100 + len(self.tabs),
                        new["insertSheetIndex"],
                        self,
                    )
                )


class FakeClient:
    def __init__(self, spreadsheet):
        self.spreadsheet = spreadsheet

    def open_by_url(self, sheet_link):
        return self.spreadsheet


class PuzzleChannel(FakeChannel):
    """A new puzzle channel that takes a topic and messages."""

    async def edit(self, topic):
        self.topic = topic

    async def send(self, embed=None):
        return FakeMessage("", channel=self, embed=embed)


@pytest.fixture
def category():
    return FakeCategory(100, "GPH 1 Puzzles")


@pytest.fixture
def ctx(category):
    add_tether(category.id, SHEET)
    channel = FakeChannel(201, "puzzle-1", category)
    return FakeContext(FakeGuild(categories=[category]), channel)


class FakeOverview:
    """Stands in for OverviewSheet, has an empty Overview whose column cells all say C."""

    overview_data = [[""], [""], [""]]

    def __init__(self, gspread_client, sheet_link):
        self.worksheet = FakeTab("Overview", 0, 0)

    def get_cell_value(self, label):
        return "C"


def _not_on_loop(calls):
    assert calls
    assert [name for name, on_loop in calls if on_loop] == []


async def test_sheet_move_to_archive_off_the_event_loop(ctx, monkeypatch):
    spreadsheet = FakeSpreadsheet()
    spreadsheet.tabs.append(FakeTab("Puzzle 1", TAB_ID, 2, spreadsheet))

    class Overview:
        def find_row_of_channel(self, ctx):
            return 4, None

        def get_cell_value(self, label):
            return str(TAB_ID)

    overview = Overview()
    overview.spreadsheet = spreadsheet

    async def get_overview(gspread_client, ctx, sheet_link):
        return overview

    monkeypatch.setattr(sheet_utils, "get_overview", get_overview)
    calls = watch_threads(monkeypatch, spreadsheet, "worksheets")
    watch_threads(monkeypatch, sheet_utils, "findsheettether", calls=calls)
    watch_threads(monkeypatch, spreadsheet.tabs[-1], "update_index", calls=calls)

    await sheet_utils.sheet_move_to_archive(None, ctx)

    assert spreadsheet.tabs[-1].moved_to == len(spreadsheet.tabs)
    assert ctx.sent_embeds[-1].fields[0].name == "Success"
    assert {name for name, _ in calls} == {
        "findsheettether",
        "worksheets",
        "update_index",
    }
    _not_on_loop(calls)


async def test_batch_create_puzzle_channels_off_the_event_loop(
    ctx, category, monkeypatch
):
    spreadsheet = FakeSpreadsheet()
    client = FakeClient(spreadsheet)

    async def create_channel(guild, category, name):
        return PuzzleChannel(300, name, category)

    async def pin_message(message):
        return message.embed

    tethered = []
    monkeypatch.setattr(sheet_utils, "OverviewSheet", FakeOverview)
    monkeypatch.setattr(
        database,
        "set_tether",
        lambda guild_id, guild_name, chan_id, chan_name, link: tethered.append(
            (chan_name, link)
        ),
    )
    monkeypatch.setattr(discord_utils, "createchannelgeneric", create_channel)
    monkeypatch.setattr(discord_utils, "pin_message", pin_message)
    calls = watch_threads(monkeypatch, client, "open_by_url")
    watch_threads(
        monkeypatch, spreadsheet, "worksheet", "worksheets", "batch_update", calls=calls
    )
    watch_threads(
        monkeypatch, sheet_utils, "findsheettether", "OverviewSheet", calls=calls
    )
    watch_threads(monkeypatch, database, "set_tether", calls=calls)

    results = await sheet_utils.batch_create_puzzle_channels(
        None, ctx, client, [("puzzle-a", "", None), ("puzzle-b", "", None)]
    )

    assert [name for _, _, _, name in results] == ["puzzle-a", "puzzle-b"]
    assert all(link is not None for link, _, _, _ in results)
    # Each channel is tethered to the link already opened, without reopening the sheet
    assert tethered == [("puzzle-a", SHEET), ("puzzle-b", SHEET)]
    assert [name for name, _ in calls].count("open_by_url") == 1
    assert {name for name, _ in calls} == {
        "findsheettether",
        "open_by_url",
        "worksheet",
        "worksheets",
        "batch_update",
        "OverviewSheet",
        "set_tether",
    }
    _not_on_loop(calls)


async def test_create_puzzle_channel_from_template_off_the_event_loop(ctx, monkeypatch):
    """The path behind ~anychanhydra, ~metachanhydra, ~forumhydra and friends."""
    spreadsheet = FakeSpreadsheet()
    client = FakeClient(spreadsheet)

    async def add_reaction(reaction):
        pass

    ctx.message.add_reaction = add_reaction
    monkeypatch.setattr(sheet_utils, "OverviewSheet", FakeOverview)
    calls = watch_threads(monkeypatch, client, "open_by_url")
    watch_threads(
        monkeypatch,
        spreadsheet,
        "worksheet",
        "worksheets",
        "duplicate_sheet",
        "batch_update",
        calls=calls,
    )
    watch_threads(
        monkeypatch, sheet_utils, "findsheettether", "OverviewSheet", calls=calls
    )

    link, newsheet, channel = await sheet_utils.create_puzzle_channel_from_template(
        None, ctx, "puzzle-a", "Template", "", client, chan_type="none"
    )

    assert (link, newsheet.title, channel) == (SHEET, "puzzle a", None)
    assert len(spreadsheet.batches) == 1
    # The open sheet is reused for the final update, so it is opened once
    assert [name for name, _ in calls].count("open_by_url") == 1
    assert ctx.sent_embeds[-1].fields[0].name == "Success"
    _not_on_loop(calls)


async def test_sheetcreatetabgeneric_off_the_event_loop(ctx, category, monkeypatch):
    spreadsheet = FakeSpreadsheet()
    client = FakeClient(spreadsheet)
    calls = watch_threads(monkeypatch, client, "open_by_url")
    watch_threads(
        monkeypatch,
        spreadsheet,
        "worksheet",
        "worksheets",
        "duplicate_sheet",
        calls=calls,
    )
    watch_threads(monkeypatch, sheet_utils, "findsheettether", calls=calls)

    link, newsheet = await sheet_utils.sheetcreatetabgeneric(
        client, ctx, ctx.channel, category, "Puzzle A", "Meta Template"
    )

    assert (link, newsheet.title) == (SHEET, "Puzzle A")
    assert {name for name, _ in calls} == {
        "findsheettether",
        "open_by_url",
        "worksheet",
        "worksheets",
        "duplicate_sheet",
    }
    _not_on_loop(calls)


async def test_tether_template_sheet_off_the_event_loop(ctx, monkeypatch):
    spreadsheet = FakeSpreadsheet()
    client = FakeClient(spreadsheet)
    tethered = []
    monkeypatch.setattr(
        sheet_utils,
        "addsheettethergeneric",
        lambda gspread_client, link, guild, category: (
            tethered.append(link) or spreadsheet
        ),
    )
    calls = watch_threads(monkeypatch, client, "open_by_url")
    watch_threads(monkeypatch, spreadsheet, "worksheet", calls=calls)
    watch_threads(monkeypatch, sheet_utils, "addsheettethergeneric", calls=calls)

    await sheet_utils.tether_template_sheet(client, ctx, SHEET)

    assert tethered == [SHEET]
    assert [name for name, _ in calls].count("worksheet") == 3
    _not_on_loop(calls)
