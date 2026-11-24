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
