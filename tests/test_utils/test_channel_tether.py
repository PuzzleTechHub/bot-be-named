from unittest.mock import MagicMock

import gspread
import pytest
from sqlalchemy.orm import Session

import database
from tests.fakes import (
    FakeCategory,
    FakeChannel,
    FakeContext,
    FakeForum,
    FakeGuild,
    FakeThread,
    add_tether,
)
from utils import sheet_utils, sheets_constants

CATEGORY_SHEET = "https://docs.google.com/spreadsheets/d/category/edit"
CHANNEL_SHEET = "https://docs.google.com/spreadsheets/d/channel/edit"
THREAD_SHEET = "https://docs.google.com/spreadsheets/d/thread/edit"
NEW_SHEET = "https://docs.google.com/spreadsheets/d/new/edit"


@pytest.fixture
def category():
    return FakeCategory(100, "GPH 1 Puzzles")


@pytest.fixture
def channel(category):
    return FakeChannel(201, "puzzle-1", category)


# find_channel_tether


def test_channel_tether_beats_category(channel):
    add_tether(100, CATEGORY_SHEET)
    add_tether(201, CHANNEL_SHEET)
    result, kind = sheet_utils.find_channel_tether(channel)
    assert (result.sheet_link, kind) == (CHANNEL_SHEET, sheets_constants.CHANNEL)


def test_channel_falls_back_to_category(channel):
    add_tether(100, CATEGORY_SHEET)
    result, kind = sheet_utils.find_channel_tether(channel)
    assert (result.sheet_link, kind) == (CATEGORY_SHEET, sheets_constants.CATEGORY)


def test_thread_tether_beats_parent(channel):
    thread = FakeThread(300, "thread", channel)
    add_tether(201, CHANNEL_SHEET)
    add_tether(300, THREAD_SHEET)
    result, kind = sheet_utils.find_channel_tether(thread)
    assert (result.sheet_link, kind) == (THREAD_SHEET, sheets_constants.THREAD)


def test_thread_falls_back_to_parent_then_category(channel):
    thread = FakeThread(300, "thread", channel)
    add_tether(100, CATEGORY_SHEET)
    result, kind = sheet_utils.find_channel_tether(thread)
    assert (result.sheet_link, kind) == (CATEGORY_SHEET, sheets_constants.CATEGORY)
    add_tether(201, CHANNEL_SHEET)
    result, kind = sheet_utils.find_channel_tether(thread)
    assert (result.sheet_link, kind) == (CHANNEL_SHEET, sheets_constants.CHANNEL)


def test_forum_post_uses_forum_tether(category):
    post = FakeThread(300, "post", FakeForum(202, "forum", category))
    add_tether(202, CHANNEL_SHEET)
    result, kind = sheet_utils.find_channel_tether(post)
    assert (result.sheet_link, kind) == (CHANNEL_SHEET, sheets_constants.CHANNEL)


def test_channel_without_category():
    lone = FakeChannel(201, "lone")
    assert sheet_utils.find_channel_tether(lone)[0] is None
    add_tether(201, CHANNEL_SHEET)
    assert sheet_utils.find_channel_tether(lone)[0].sheet_link == CHANNEL_SHEET


# tether_template_sheet


def _sheet(missing=()):
    sheet = MagicMock(url=NEW_SHEET)

    def worksheet(name):
        if name in missing:
            raise gspread.exceptions.WorksheetNotFound(name)
        return MagicMock()

    sheet.worksheet.side_effect = worksheet
    return sheet


@pytest.fixture
def opens(monkeypatch):
    """Makes get_sheet_from_key_or_link (also used by addsheettethergeneric) return a sheet."""

    def set_sheet(sheet):
        monkeypatch.setattr(
            sheet_utils, "get_sheet_from_key_or_link", lambda client, link: sheet
        )

    return set_sheet


def _tethered(channel_or_cat_id):
    with Session(database.DATABASE_ENGINE) as session:
        row = (
            session.query(database.SheetTethers)
            .filter_by(channel_or_cat_id=channel_or_cat_id)
            .first()
        )
        return row.sheet_link if row else None


async def test_tether_template_sheet_tethers_category(channel, opens):
    opens(_sheet())
    ctx = FakeContext(FakeGuild(categories=[channel.category]), channel)
    await sheet_utils.tether_template_sheet(MagicMock(), ctx, NEW_SHEET)
    assert _tethered(100) == NEW_SHEET
    [embed] = ctx.sent_embeds
    assert embed.fields[0].name == "Success"
    assert "**GPH 1 Puzzles**" in embed.fields[0].value


@pytest.mark.parametrize("tab", ["Template", "Meta Template", "Overview"])
async def test_tether_template_sheet_missing_tab(channel, opens, tab):
    opens(_sheet(missing=[tab]))
    ctx = FakeContext(FakeGuild(categories=[channel.category]), channel)
    await sheet_utils.tether_template_sheet(MagicMock(), ctx, NEW_SHEET)
    assert _tethered(100) is None
    [embed] = ctx.sent_embeds
    assert embed.fields[0].name == "Failed"
    assert f"no tab named '{tab}'" in embed.fields[0].value


async def test_tether_template_sheet_no_category(opens):
    opens(_sheet())
    lone = FakeChannel(201, "lone")
    ctx = FakeContext(FakeGuild(), lone)
    ctx.prefix = "~"
    await sheet_utils.tether_template_sheet(MagicMock(), ctx, NEW_SHEET)
    assert _tethered(201) is None
    [embed] = ctx.sent_embeds
    assert "there is no category for this channel" in embed.fields[0].value


async def test_tether_template_sheet_no_sheet(channel, opens):
    opens(None)
    ctx = FakeContext(FakeGuild(categories=[channel.category]), channel)
    await sheet_utils.tether_template_sheet(MagicMock(), ctx, NEW_SHEET)
    assert _tethered(100) is None
    [embed] = ctx.sent_embeds
    assert "can't find a sheet there" in embed.fields[0].value
