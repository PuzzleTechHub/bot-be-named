import pytest

from tests.fakes import (
    FakeCategory,
    FakeChannel,
    FakeContext,
    FakeGuild,
    add_tether,
    patch_overview_sheets,
)
from utils import sheet_utils
from utils.sheet_command_base import SheetCommandBase

CATEGORY_SHEET = "https://docs.google.com/spreadsheets/d/category/edit"
CHANNEL_SHEET = "https://docs.google.com/spreadsheets/d/channel/edit"


@pytest.fixture
def channel():
    return FakeChannel(201, "puzzle-1", FakeCategory(100, "GPH 1 Puzzles"))


@pytest.fixture
def ctx(channel):
    return FakeContext(FakeGuild(categories=[channel.category]), channel)


def _overview(*channel_ids):
    return [["Channel ID"], [""]] + [[str(cid)] for cid in channel_ids]


@pytest.fixture
def real_overview_lookup(monkeypatch):
    """patch_overview_sheets swaps OverviewSheet for a stand-in without find_row_of_channel,
    so give it the real method."""
    from tests import fakes

    monkeypatch.setattr(
        fakes.FakeOverviewSheet,
        "find_row_of_channel",
        sheet_utils.OverviewSheet.find_row_of_channel,
        raising=False,
    )


def test_starts_with_empty_embed(ctx):
    command = SheetCommandBase(ctx, "client")
    assert command.ctx is ctx
    assert command.gspread_client == "client"
    assert command.embed.fields == []


async def test_get_sheet_context(ctx, monkeypatch, real_overview_lookup):
    add_tether(100, CATEGORY_SHEET)
    opened = patch_overview_sheets(monkeypatch, {CATEGORY_SHEET: _overview(999, 201)})
    link, sheet, row = await SheetCommandBase(ctx, None).get_sheet_context()
    assert link == CATEGORY_SHEET
    assert sheet.sheet_url == CATEGORY_SHEET
    assert row == 4
    assert opened == [CATEGORY_SHEET]
    assert ctx.sent == []


async def test_channel_tether_beats_category(ctx, monkeypatch, real_overview_lookup):
    add_tether(100, CATEGORY_SHEET)
    add_tether(201, CHANNEL_SHEET)
    opened = patch_overview_sheets(monkeypatch, {CHANNEL_SHEET: _overview(201)})
    link, _, row = await SheetCommandBase(ctx, None).get_sheet_context()
    assert (link, row) == (CHANNEL_SHEET, 3)
    assert opened == [CHANNEL_SHEET]


async def test_not_tethered(ctx, channel, monkeypatch):
    opened = patch_overview_sheets(monkeypatch, {})
    command = SheetCommandBase(ctx, None)
    assert await command.get_sheet_context() == (None, None, None)
    assert opened == []
    [embed] = ctx.sent_embeds
    assert embed.fields[0].name == "Failed"
    assert "**GPH 1 Puzzles**" in embed.fields[0].value
    assert channel.mention in embed.fields[0].value


async def test_overview_fails_to_open(ctx, monkeypatch):
    add_tether(100, CATEGORY_SHEET)

    async def no_overview(gspread_client, ctx, sheet_link):
        return None

    monkeypatch.setattr(sheet_utils, "get_overview", no_overview)
    assert await SheetCommandBase(ctx, None).get_sheet_context() == (None, None, None)


async def test_channel_not_on_overview(ctx, channel, monkeypatch, real_overview_lookup):
    add_tether(100, CATEGORY_SHEET)
    patch_overview_sheets(monkeypatch, {CATEGORY_SHEET: _overview(999)})
    assert await SheetCommandBase(ctx, None).get_sheet_context() == (None, None, None)
    [embed] = ctx.sent_embeds
    assert f"I couldn't find the channel {channel.mention}" in embed.fields[0].value
