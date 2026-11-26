import gspread
import nextcord
import pytest

from tests.fakes import (
    FakeCategory,
    FakeChannel,
    FakeContext,
    FakeGuild,
    watch_threads,
)
from utils import sheet_utils, sheets_constants, solved_utils

CHANNEL_ID = 20
TAB_ID = 123
ROW = 4


class FakeResponse:
    def __init__(self, status, message=""):
        self.text = message
        self._json = {"error": {"code": 400, "status": status, "message": message}}

    def json(self):
        return self._json


def api_error(status, message=""):
    return gspread.exceptions.APIError(FakeResponse(status, message))


class _Forbidden:
    status = 403
    reason = "Forbidden"


class EditableChannel(FakeChannel):
    def __init__(self, name, forbidden=False):
        super().__init__(CHANNEL_ID, name, FakeCategory(10, "GPH 1 Puzzles"))
        self.forbidden = forbidden
        self.edits = []

    async def edit(self, name):
        if self.forbidden:
            raise nextcord.Forbidden(_Forbidden(), "Missing Permissions")
        self.edits.append(name)
        self.name = name


class FakeTab:
    def __init__(self, tab_id):
        self.id = tab_id


class FakeSpreadsheet:
    def __init__(self, batch_error=None):
        self.batch_error = batch_error
        self.batches = []

    def get_worksheet_by_id(self, tab_id):
        return FakeTab(tab_id)

    def batch_update(self, body):
        if self.batch_error is not None:
            raise self.batch_error
        self.batches.append(body)


class FakeOverviewWorksheet:
    id = 0

    def __init__(self, spreadsheet):
        self.spreadsheet = spreadsheet


class StatusSheet:
    """Overview with the status column in E (B1 says so) and one puzzle on row 4."""

    def __init__(self, status="In Progress", batch_error=None):
        self.overview_data = [
            ["", "E"],
            [],
            [],
            [str(CHANNEL_ID), str(TAB_ID), "", "", status],
        ]
        self.spreadsheet = FakeSpreadsheet(batch_error)
        self.worksheet = FakeOverviewWorksheet(self.spreadsheet)

    def get_cell_value(self, label):
        return sheet_utils.get_cell_value(self.overview_data, label)


def _ctx(channel):
    ctx = FakeContext(FakeGuild(categories=[channel.category]), channel)
    ctx.message.reactions = []

    async def add_reaction(reaction):
        ctx.message.reactions.append(reaction)

    ctx.message.add_reaction = add_reaction
    return ctx


def _written(sheet):
    """Every (sheetId, row, col, value) the batch updates wrote are 0-indexed"""
    cells = []
    for batch in sheet.spreadsheet.batches:
        for request in batch["requests"]:
            if "updateCells" in request:
                update = request["updateCells"]
                value = update["rows"][0]["values"][0]["userEnteredValue"]
                start = update["start"]
                cells.append(
                    (
                        start["sheetId"],
                        start["rowIndex"],
                        start["columnIndex"],
                        value["stringValue"],
                    )
                )
    return cells


def _field_names(ctx):
    return [field.name for embed in ctx.sent_embeds for field in embed.fields]


# get_status_info


def test_get_status_info_known():
    assert (
        solved_utils.get_status_info("Solved") is sheets_constants.status_dict["Solved"]
    )


def test_get_status_info_custom_uses_none_entry():
    assert (
        solved_utils.get_status_info("waiting on runaround")
        is sheets_constants.status_dict["None"]
    )


# is_solve_status


@pytest.mark.parametrize(
    "status", ["Solved", "solved", "BACKSOLVED", "Postsolved", "postsolved"]
)
def test_is_solve_status_true(status):
    assert solved_utils.is_solve_status(status)


@pytest.mark.parametrize(
    "status", ["Solvedish", "In Progress", "Stuck", "", "my custom status"]
)
def test_is_solve_status_false(status):
    assert not solved_utils.is_solve_status(status)


# answer_cell_value


def test_answer_cell_value_uppercases_answer():
    info = solved_utils.get_status_info("Solved")
    assert solved_utils.answer_cell_value(info, "Hello World") == "HELLO WORLD"


def test_answer_cell_value_keeps_answer_when_none_given():
    info = solved_utils.get_status_info("Solved")
    assert solved_utils.answer_cell_value(info, None) is None


def test_answer_cell_value_clears_for_status_without_answer():
    info = solved_utils.get_status_info("Stuck")
    assert solved_utils.answer_cell_value(info, "IGNORED") == ""


def test_answer_cell_value_empty_string_clears():
    # ~unsolvedlion passes "" by default, which empties the answer
    info = solved_utils.get_status_info("In Progress")
    assert solved_utils.answer_cell_value(info, "") == ""


# solved_time_value


NOW = "2026-11-24 12:00:00"


@pytest.mark.parametrize(
    "prev, new, has_time, expected",
    [
        ("In Progress", "Solved", False, NOW),
        ("In Progress", "solved", True, NOW),
        ("Solvedish", "Backsolved", False, NOW),
        ("Solved", "Backsolved", True, None),
        ("Solved", "Postsolved", False, None),
        ("Solved", "In Progress", True, ""),
        ("Solved", "Solvedish", True, ""),
        ("Stuck", "In Progress", True, ""),
        ("Stuck", "In Progress", False, None),
    ],
)
def test_solved_time_value(prev, new, has_time, expected):
    assert solved_utils.solved_time_value(prev, new, has_time, NOW) == expected


# update_puzzle_status


async def test_update_puzzle_status_solved():
    channel = EditableChannel("puzzle-1")
    ctx = _ctx(channel)
    sheet = StatusSheet("In Progress")

    ok = await solved_utils.update_puzzle_status(ctx, sheet, ROW, "solved", "abc")

    assert ok is True
    # Answer on the tab (B3), then the status on the Overview (E4)
    assert _written(sheet) == [(TAB_ID, 2, 1, "ABC"), (0, 3, 4, "Solved")]
    assert channel.edits == ["solved-puzzle-1"]
    assert _field_names(ctx) == ["Success", "Success"]
    assert len(ctx.message.reactions) == 1


async def test_update_puzzle_status_unsolved_removes_prefix():
    channel = EditableChannel("solved-puzzle-1")
    ctx = _ctx(channel)
    sheet = StatusSheet("Solved")

    ok = await solved_utils.update_puzzle_status(ctx, sheet, ROW, "In Progress", "")

    assert ok is True
    assert _written(sheet) == [(TAB_ID, 2, 1, ""), (0, 3, 4, "In Progress")]
    assert channel.edits == ["puzzle-1"]


async def test_update_puzzle_status_same_status_notes_it():
    channel = EditableChannel("solved-puzzle-1")
    ctx = _ctx(channel)
    sheet = StatusSheet("Solved")

    ok = await solved_utils.update_puzzle_status(ctx, sheet, ROW, "Solved")

    assert ok is True
    assert channel.edits == []
    assert _field_names(ctx) == ["Success", "Note"]
    assert sheet.spreadsheet.batches
    note = ctx.sent_embeds[0].fields[1].value
    assert note.endswith("No changes were made to the channel name.")


async def test_update_puzzle_status_permission_denied_returns_false():
    channel = EditableChannel("puzzle-1")
    ctx = _ctx(channel)
    sheet = StatusSheet(batch_error=api_error("PERMISSION_DENIED"))

    ok = await solved_utils.update_puzzle_status(ctx, sheet, ROW, "Solved")

    assert ok is False
    assert channel.edits == []
    assert ctx.message.reactions == []
    [embed] = ctx.sent_embeds
    [field] = embed.fields
    assert field.name == "Failed"
    assert "permission was denied" in field.value


async def test_update_puzzle_status_other_api_error_reports_and_returns_false():
    channel = EditableChannel("puzzle-1")
    ctx = _ctx(channel)
    sheet = StatusSheet(batch_error=api_error("INTERNAL", "backend broke"))

    ok = await solved_utils.update_puzzle_status(ctx, sheet, ROW, "Solved")

    assert ok is False
    assert channel.edits == []
    [embed] = ctx.sent_embeds
    [field] = embed.fields
    assert field.name == "Failed"
    assert "backend broke" in field.value


async def test_update_puzzle_status_rename_forbidden_does_not_crash():
    channel = EditableChannel("puzzle-1", forbidden=True)
    ctx = _ctx(channel)
    sheet = StatusSheet("In Progress")

    ok = await solved_utils.update_puzzle_status(ctx, sheet, ROW, "Solved")

    assert ok is True
    # status_channel sends its own Failed, then the sheet Success follows
    assert _field_names(ctx) == ["Failed", "Success"]


async def test_update_puzzle_status_calls_sheets_off_the_event_loop(monkeypatch):
    ctx = _ctx(EditableChannel("puzzle-1"))
    sheet = StatusSheet("In Progress")
    calls = watch_threads(
        monkeypatch, sheet.spreadsheet, "get_worksheet_by_id", "batch_update"
    )

    assert await solved_utils.update_puzzle_status(ctx, sheet, ROW, "solved", "abc")

    assert calls == [("get_worksheet_by_id", False), ("batch_update", False)]
