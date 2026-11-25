from unittest.mock import MagicMock

import nextcord
import pytest

from modules.hydra.cog import HydraCog
from tests.fakes import FakeChannel, FakeContext, FakeGuild, FakeRole
from utils import google_utils


@pytest.fixture
def cog(monkeypatch):
    monkeypatch.setattr(google_utils, "create_gspread_client", MagicMock())
    return HydraCog(MagicMock())


@pytest.fixture
def role():
    return FakeRole(7, "Solvers")


@pytest.fixture
def channel():
    """The commands need a real TextChannel type."""
    channel = MagicMock(spec=nextcord.TextChannel)
    channel.id = 200
    channel.name = "summaries"
    channel.mention = "<#200>"
    return channel


@pytest.fixture
def ctx(role, channel):
    guild = FakeGuild(roles=[role])
    guild.get_channel = lambda channel_id: channel if channel_id == 200 else None
    return FakeContext(guild, FakeChannel(201, "bot-spam"))


def _last(ctx):
    field = ctx.sent_embeds[-1].fields[0]
    return field.name, field.value


async def test_allow_then_allow_again(cog, ctx, role, channel):
    await cog.summaryallowhydra.callback(cog, ctx, "Solvers", channel)
    assert _last(ctx) == (
        "Success",
        f"{role.mention} can now run summaries in {channel.mention}.",
    )
    await cog.summaryallowhydra.callback(cog, ctx, "Solvers", channel)
    assert _last(ctx) == (
        "Failed",
        f"{role.mention} is already allowed in {channel.mention}",
    )


async def test_list_shows_grants(cog, ctx, role, channel):
    await cog.summaryallowhydra.callback(cog, ctx, "Solvers", channel)
    await cog.summarylisthydra.callback(cog, ctx)
    assert _last(ctx)[1] == "- @Solvers in #summaries"


async def test_list_empty(cog, ctx):
    await cog.summarylisthydra.callback(cog, ctx)
    assert _last(ctx)[1] == "No summary grants found."


async def test_disallow_then_disallow_again(cog, ctx, role, channel):
    await cog.summaryallowhydra.callback(cog, ctx, "Solvers", channel)
    await cog.summarydisallowhydra.callback(cog, ctx, "Solvers", channel)
    assert _last(ctx) == (
        "Success",
        f"{role.mention} can no longer run summaries in {channel.mention}",
    )
    await cog.summarydisallowhydra.callback(cog, ctx, "Solvers", channel)
    assert _last(ctx)[0] == "Failed"
