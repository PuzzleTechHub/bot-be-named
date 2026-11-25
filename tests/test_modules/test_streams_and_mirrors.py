from unittest.mock import MagicMock

import nextcord
import pytest

import database
from modules.hydra.cog import HydraCog
from modules.mirror.cog import ChannelMirrorCog
from tests.fakes import FakeChannel, FakeContext, FakeGuild
from utils import google_utils, sheet_utils

SHEET = "https://docs.google.com/spreadsheets/d/sheetkey/edit"


def _text_channel(channel_id, name):
    """The commands need a real TextChannel type."""
    channel = MagicMock(spec=nextcord.TextChannel)
    channel.id = channel_id
    channel.name = name
    channel.mention = f"<#{channel_id}>"
    return channel


@pytest.fixture
def ctx():
    ctx = FakeContext(FakeGuild(), FakeChannel(201, "bot-spam"))
    ctx.prefix = "~"
    return ctx


def _last(ctx):
    field = ctx.sent_embeds[-1].fields[0]
    return field.name, field.value


# solve streams: ~addupdateshydra / ~rmupdatehydra


@pytest.fixture
def hydra(monkeypatch):
    monkeypatch.setattr(google_utils, "create_gspread_client", MagicMock())
    monkeypatch.setattr(
        sheet_utils, "get_sheet_from_key_or_link", lambda client, key: object()
    )
    return HydraCog(MagicMock())


async def test_add_solve_stream_then_again(hydra, ctx):
    stream = _text_channel(300, "solves")
    await hydra.addupdateshydra.callback(hydra, ctx, stream, SHEET)
    assert "solves will now be posted to <#300>" in _last(ctx)[1]
    await hydra.addupdateshydra.callback(hydra, ctx, stream, SHEET)
    assert "solves were already being posted to <#300>" in _last(ctx)[1]
    [row] = database.get_solve_streams("sheetkey", ctx.guild.id)
    assert (row.channel_id, row.channel_name) == (300, "solves")


async def test_remove_solve_stream_then_again(hydra, ctx):
    stream = _text_channel(300, "solves")
    await hydra.addupdateshydra.callback(hydra, ctx, stream, SHEET)
    await hydra.rmupdateshydra.callback(hydra, ctx, stream, SHEET)
    assert "solves will no longer be posted to <#300>" in _last(ctx)[1]
    await hydra.rmupdateshydra.callback(hydra, ctx, stream, SHEET)
    assert "**Failed** - solves on this sheet aren't being posted" in _last(ctx)[1]
    assert database.get_solve_streams("sheetkey", ctx.guild.id) == []


# channel mirrors: ~mirrorchan / ~unmirrorchan / ~listmirrorchan


@pytest.fixture
def mirror():
    return ChannelMirrorCog(MagicMock())


async def test_mirror_then_again(mirror, ctx):
    source, target = _text_channel(10, "mod-mail"), _text_channel(20, "vets")
    await mirror.mirrorchan.callback(mirror, ctx, source, target)
    assert _last(ctx) == (
        "Success",
        "New messages in <#10> will be mirrored to <#20>.",
    )
    await mirror.mirrorchan.callback(mirror, ctx, source, target)
    assert _last(ctx) == (
        "Success",
        "Messages in <#10> are already being mirrored to <#20>.",
    )
    assert database.CHANNEL_MIRRORS == {10: {20}}


async def test_list_mirrors(mirror, ctx):
    await mirror.listmirrorchan.callback(mirror, ctx)
    assert _last(ctx)[1].startswith("No channels are being mirrored on this server.")
    source, target = _text_channel(10, "mod-mail"), _text_channel(20, "vets")
    await mirror.mirrorchan.callback(mirror, ctx, source, target)
    await mirror.listmirrorchan.callback(mirror, ctx)
    assert _last(ctx)[1] == "<#10> -> <#20>"


async def test_unmirror_then_again(mirror, ctx):
    source, target = _text_channel(10, "mod-mail"), _text_channel(20, "vets")
    await mirror.mirrorchan.callback(mirror, ctx, source, target)
    await mirror.unmirrorchan.callback(mirror, ctx, source, target)
    assert _last(ctx) == (
        "Success",
        "Messages in <#10> will no longer be mirrored to <#20>.",
    )
    await mirror.unmirrorchan.callback(mirror, ctx, source, target)
    assert _last(ctx) == ("Failed", "No mirroring exists from <#10> to <#20>.")
    assert database.CHANNEL_MIRRORS == {10: set()}
