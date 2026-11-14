import re

import gspread
import pytest

from tests.fakes import FakeCategory, FakeChannel, FakeContext, FakeGuild, add_tether
from utils import sheet_utils, sheets_constants

SHEET = "https://docs.google.com/spreadsheets/d/gph1/edit"


class FakeResponse:
    def __init__(self, status, message=""):
        self.text = message
        self._json = {"error": {"code": 400, "status": status, "message": message}}

    def json(self):
        return self._json


def api_error(status, message=""):
    return gspread.exceptions.APIError(FakeResponse(status, message))


class FakeWorksheet:
    def __init__(self, rows):
        self.rows = rows

    def get(self):
        return self.rows


class FakeSpreadsheet:
    def __init__(self, tabs):
        self.tabs = tabs

    def worksheet(self, name):
        if name not in self.tabs:
            raise gspread.exceptions.WorksheetNotFound(name)
        return self.tabs[name]


class FakeClient:
    """sheets maps a link or key to tabs {name: rows}, or to an exception to raise.
    Anything that isn't a docs.google.com link can only be opened by key."""

    def __init__(self, sheets):
        self.sheets = sheets
        self.opened = []

    def _open(self, how, key):
        self.opened.append((how, key))
        sheet = self.sheets.get(key, gspread.exceptions.SpreadsheetNotFound())
        if isinstance(sheet, Exception):
            raise sheet
        return FakeSpreadsheet(
            {name: FakeWorksheet(rows) for name, rows in sheet.items()}
        )

    def open_by_url(self, url):
        if "docs.google.com" not in url:
            raise gspread.exceptions.NoValidUrlKeyFound
        return self._open("url", url)

    def open_by_key(self, key):
        return self._open("key", key)


@pytest.fixture
def channel():
    category = FakeCategory(100, "GPH 1 Puzzles")
    return FakeChannel(201, "puzzle-1", category)


@pytest.fixture
def ctx(channel):
    return FakeContext(FakeGuild(categories=[channel.category]), channel)


OVERVIEW = [
    ["Channel ID", "Name", "Status"],
    ["", ""],
    ["999", "other"],
    ["201", "puzzle-1", "Solved"],
]


# OverviewSheet


def test_overview_sheet_caches_rows():
    sheet = sheet_utils.OverviewSheet(
        FakeClient({SHEET: {"Overview": OVERVIEW}}), SHEET
    )
    assert sheet.overview_data == OVERVIEW
    assert sheet.sheet_url == SHEET


def test_overview_sheet_missing_tab():
    with pytest.raises(gspread.exceptions.WorksheetNotFound):
        sheet_utils.OverviewSheet(FakeClient({SHEET: {"Puzzle": []}}), SHEET)


@pytest.mark.parametrize(
    "label, value",
    [("A1", "Channel ID"), ("C4", "Solved"), ("C3", ""), ("A99", ""), ("Z1", "")],
)
def test_get_cell_value(label, value):
    sheet = sheet_utils.OverviewSheet(
        FakeClient({SHEET: {"Overview": OVERVIEW}}), SHEET
    )
    assert sheet.get_cell_value(label) == value


def test_find_row_of_channel(ctx):
    sheet = sheet_utils.OverviewSheet(
        FakeClient({SHEET: {"Overview": OVERVIEW}}), SHEET
    )
    assert sheet.find_row_of_channel(ctx) == (4, None)


def test_find_row_of_channel_missing(ctx, channel):
    rows = [["Channel ID"], ["999"]]
    sheet = sheet_utils.OverviewSheet(FakeClient({SHEET: {"Overview": rows}}), SHEET)
    row, embed = sheet.find_row_of_channel(ctx)
    assert row is None
    assert embed.fields[0].name == "Failed"
    assert channel.mention in embed.fields[0].value


# get_overview


async def test_get_overview(ctx):
    sheet = await sheet_utils.get_overview(
        FakeClient({SHEET: {"Overview": OVERVIEW}}), ctx, SHEET
    )
    assert sheet.overview_data == OVERVIEW
    assert ctx.sent == []


async def test_get_overview_no_overview_tab(ctx):
    client = FakeClient({SHEET: {"Puzzle": []}})
    assert await sheet_utils.get_overview(client, ctx, SHEET) is None
    [embed] = ctx.sent_embeds
    assert "no tab named 'Overview'" in embed.fields[0].value


async def test_get_overview_permission_denied(ctx):
    client = FakeClient({SHEET: api_error("PERMISSION_DENIED")})
    assert await sheet_utils.get_overview(client, ctx, SHEET) is None
    [embed] = ctx.sent_embeds
    assert "Did the permissions change?" in embed.fields[0].value


async def test_get_overview_other_api_error_raised(ctx):
    client = FakeClient({SHEET: api_error("INTERNAL")})
    with pytest.raises(gspread.exceptions.APIError):
        await sheet_utils.get_overview(client, ctx, SHEET)
    assert ctx.sent == []


# findchanidcell


async def test_findchanidcell_rows(ctx):
    client = FakeClient({SHEET: {"Overview": OVERVIEW}})
    result = await sheet_utils.findchanidcell(client, ctx, SHEET, [201, 999, 555])
    assert [row for row, _, _ in result] == [4, 3, None]
    assert all(values == OVERVIEW for _, _, values in result)


async def test_findchanidcell_skips_blank_rows(ctx):
    rows = [[], [""], ["201"]]
    client = FakeClient({SHEET: {"Overview": rows}})
    [(row, _, _)] = await sheet_utils.findchanidcell(client, ctx, SHEET, ["201"])
    assert row == 3


@pytest.mark.parametrize(
    "error, text",
    [
        (api_error("PERMISSION_DENIED", "denied"), "unable to open the tethered sheet"),
        (gspread.exceptions.SpreadsheetNotFound(), "no tab named 'Overview'"),
        (RuntimeError("boom"), "unknown error occurred"),
    ],
)
async def test_findchanidcell_errors(ctx, error, text):
    client = FakeClient({SHEET: error})
    assert await sheet_utils.findchanidcell(client, ctx, SHEET, [201]) is None
    [embed] = ctx.sent_embeds
    assert text in embed.fields[0].value


# handle_gspread_error


@pytest.mark.parametrize(
    "status, message, text",
    [
        (
            "BAD_REQUEST",
            "Invalid requests[0]: columnIndex[12] is after last column",
            "Invalid Template!",
        ),
        ("PERMISSION_DENIED", "", "permission was denied"),
        (
            "BAD_REQUEST",
            "Something else",
            "Unknown GSheets API Error - `Something else`",
        ),
    ],
)
async def test_handle_gspread_error(ctx, status, message, text):
    embed = await sheet_utils.handle_gspread_error(ctx, api_error(status, message))
    assert text in embed.fields[0].value
    assert ctx.sent_embeds[0].fields[0].value == embed.fields[0].value


async def test_handle_gspread_error_adds_to_given_embed(ctx):
    embed = sheet_utils.discord_utils.create_success_embed("Made the tab")
    result = await sheet_utils.handle_gspread_error(
        ctx, api_error("PERMISSION_DENIED"), embed
    )
    assert result is embed
    assert [f.name for f in embed.fields] == ["Success", "Failed"]


# get_sheet_from_key_or_link


def test_get_sheet_by_link():
    client = FakeClient({SHEET: {"Overview": []}})
    assert sheet_utils.get_sheet_from_key_or_link(client, SHEET) is not None
    assert client.opened == [("url", SHEET)]


def test_get_sheet_by_key():
    client = FakeClient({"gph1": {"Overview": []}})
    assert sheet_utils.get_sheet_from_key_or_link(client, "gph1") is not None
    assert client.opened == [("key", "gph1")]


@pytest.mark.parametrize(
    "error",
    [
        api_error("PERMISSION_DENIED"),
        gspread.exceptions.SpreadsheetNotFound(),
        PermissionError(),
    ],
)
def test_get_sheet_link_errors_return_none(error):
    client = FakeClient({SHEET: error})
    assert sheet_utils.get_sheet_from_key_or_link(client, SHEET) is None
    assert client.opened == [("url", SHEET)]


def test_get_sheet_unknown_key_returns_none():
    assert sheet_utils.get_sheet_from_key_or_link(FakeClient({}), "nope") is None


# findsheettether / get_timestamp


def test_findsheettether_thread_beats_channel():
    add_tether(300, "thread-sheet")
    add_tether(201, "channel-sheet")
    result, kind = sheet_utils.findsheettether(100, 201, 300)
    assert (result.sheet_link, kind) == ("thread-sheet", sheets_constants.THREAD)


def test_findsheettether_thread_falls_back_to_channel():
    add_tether(201, "channel-sheet")
    result, kind = sheet_utils.findsheettether(100, 201, 300)
    assert (result.sheet_link, kind) == ("channel-sheet", sheets_constants.CHANNEL)


def test_get_timestamp_format():
    assert re.fullmatch(r"\d{4}-\d\d-\d\d \d\d:\d\d:\d\d", sheet_utils.get_timestamp())
