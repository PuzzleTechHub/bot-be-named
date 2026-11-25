from unittest.mock import MagicMock

import pytest

from modules.sheets.cog import SheetsCog
from tests.fakes import (
    FakeCategory,
    FakeChannel,
    FakeContext,
    FakeGuild,
    FakeThread,
    add_tether,
)
from utils import google_utils

CHANNEL_SHEET = "https://docs.google.com/spreadsheets/d/channel/edit"


@pytest.fixture
def cog(monkeypatch):
    monkeypatch.setattr(google_utils, "create_gspread_client", MagicMock())
    monkeypatch.setattr(google_utils, "get_gdrive_credentials", MagicMock())
    return SheetsCog(MagicMock())


async def test_showtether_in_thread_names_parent_channel(cog):
    channel = FakeChannel(201, "puzzle-1", FakeCategory(100, "GPH 1 Puzzles"))
    thread = FakeThread(300, "thread", channel)
    add_tether(201, CHANNEL_SHEET)
    ctx = FakeContext(FakeGuild(categories=[channel.category]), thread)
    await cog.displaysheettether.callback(cog, ctx)
    [embed] = ctx.sent_embeds
    assert embed.fields[0].name == "Result"
    assert f"The channel {channel.mention} is currently tethered" in (
        embed.fields[0].value
    )


async def test_removetether_without_category(cog):
    lone = FakeChannel(201, "lone")
    add_tether(201, CHANNEL_SHEET)
    ctx = FakeContext(FakeGuild(), lone)
    await cog.removesheettether.callback(cog, ctx)
    [embed] = ctx.sent_embeds
    assert embed.fields[0].name == "Success"


async def test_downloadsheet_without_category_or_tether(cog):
    """Used to crash on ctx.channel.category.id."""
    lone = FakeChannel(201, "lone")
    ctx = FakeContext(FakeGuild(), lone)
    await cog.downloadsheet.callback(cog, ctx)
    [embed] = ctx.sent_embeds
    assert embed.fields[0].value.startswith(
        f"There is no sheet tethered to {lone.mention}. You'll need"
    )
