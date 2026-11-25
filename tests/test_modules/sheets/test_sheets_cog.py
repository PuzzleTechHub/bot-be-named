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
import database
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


async def test_prune_tethers_removes_only_missing_channels(cog):
    category = FakeCategory(100, "GPH 1 Puzzles")
    channel = FakeChannel(201, "puzzle-1", category)
    thread = FakeThread(300, "thread", channel)
    guild = FakeGuild(categories=[category])
    guild.channels = [category, channel]
    guild.threads = [thread]
    cog.bot.guilds = [guild]
    for place_id in (100, 201, 300, 999, guild.id):
        add_tether(place_id, CHANNEL_SHEET)
    add_tether(555, CHANNEL_SHEET, server_id=42)  # a server the bot isn't in

    to_delete = await cog.prune_tethers.coro(cog)

    assert to_delete == [(guild.id, 999)]
    kept = {row.channel_or_cat_id for row in database.get_all_tethers()}
    assert kept == {100, 201, 300, 555, guild.id}
