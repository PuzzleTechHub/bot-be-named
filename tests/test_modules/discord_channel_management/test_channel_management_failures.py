import asyncio

import nextcord

from modules.discord_channel_management.cog import DiscordChannelManagementCog
from tests.fakes import FakeCategory, FakeChannel, FakeContext, FakeGuild
from utils import discord_utils


class _Forbidden:
    status = 403
    reason = "Forbidden"


class RefusingChannel(FakeChannel):
    async def edit(self, **kwargs):
        raise nextcord.Forbidden(_Forbidden(), "Missing Permissions")


def _ctx(channel):
    return FakeContext(FakeGuild(categories=[channel.category]), channel)


def _only_field(ctx):
    [embed] = ctx.sent_embeds
    [field] = embed.fields
    return field


async def test_renamechan_missing_channel_sends_one_failure(monkeypatch):
    async def not_found(ctx, name):
        return None

    monkeypatch.setattr(discord_utils, "find_chan_or_thread", not_found)
    channel = FakeChannel(20, "puzzle-1", FakeCategory(10, "Puzzles"))
    ctx = _ctx(channel)
    cog = DiscordChannelManagementCog(bot=None)

    await cog.renamechannel.callback(cog, ctx, "old-name", "new-name")

    field = _only_field(ctx)
    assert field.name == "Failed"
    assert field.value == "Channel `old-name` was not found."


async def test_renamechan_forbidden_sends_one_failure(monkeypatch):
    channel = RefusingChannel(20, "puzzle-1", FakeCategory(10, "Puzzles"))

    async def found(ctx, name):
        return channel

    monkeypatch.setattr(discord_utils, "find_chan_or_thread", found)
    ctx = _ctx(channel)
    cog = DiscordChannelManagementCog(bot=None)

    await cog.renamechannel.callback(cog, ctx, "new-name")

    field = _only_field(ctx)
    assert field.name == "Failed"
    assert field.value.startswith("Forbidden!")


class _RateLimited:
    status = 429
    reason = "Too Many Requests"
    headers = {"Retry-After": "0.05"}


class HeldBackChannel(FakeChannel):
    """The first rename gets a 429, the rest go through."""

    def __init__(self, name):
        super().__init__(20, name, FakeCategory(10, "Puzzles"))
        self.held_back = False

    async def edit(self, name):
        if not self.held_back:
            self.held_back = True
            raise nextcord.HTTPException(_RateLimited(), "rate limited")
        self.name = name


async def test_queued_renamechan_reports_the_name_it_really_renamed(monkeypatch):
    monkeypatch.setattr(discord_utils, "RENAME_WAIT_MARGIN", 0)
    monkeypatch.setattr(discord_utils, "_rename_queues", {})
    channel = HeldBackChannel("b")

    async def found(ctx, name):
        return channel

    monkeypatch.setattr(discord_utils, "find_chan_or_thread", found)
    cog = DiscordChannelManagementCog(bot=None)
    first_ctx, second_ctx = _ctx(channel), _ctx(channel)

    first = asyncio.create_task(cog.renamechannel.callback(cog, first_ctx, "c"))
    await asyncio.sleep(0.01)
    await cog.renamechannel.callback(cog, second_ctx, "d")
    await first

    assert channel.name == "d"
    # One message for both, the replaced ~renamechan only had its wait notice
    assert all(message.deleted for message in first_ctx.sent)
    assert [e.fields[0].name for e in first_ctx.sent_embeds] == ["Rename in progress"]
    assert second_ctx.sent_embeds[-1].fields[0].value.startswith("Renamed `b` to `d`")


async def test_renamechan_to_the_same_name_says_so(monkeypatch):
    monkeypatch.setattr(discord_utils, "_rename_queues", {})
    channel = FakeChannel(20, "puzzle-1", FakeCategory(10, "Puzzles"))

    async def found(ctx, name):
        return channel

    monkeypatch.setattr(discord_utils, "find_chan_or_thread", found)
    ctx = _ctx(channel)
    cog = DiscordChannelManagementCog(bot=None)

    await cog.renamechannel.callback(cog, ctx, "puzzle-1")

    field = _only_field(ctx)
    assert field.name == "Failed"
    assert "already called `puzzle-1`" in field.value
