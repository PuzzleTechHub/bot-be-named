import asyncio

import nextcord
import pytest

from tests.fakes import FakeCategory, FakeChannel, FakeContext, FakeGuild
from utils import discord_utils, solved_utils


class EditableChannel(FakeChannel):
    """A channel that can be renamed, or refuses to be like a missing manage_channels."""

    def __init__(self, name, forbidden=False):
        super().__init__(20, name, FakeCategory(10, "GPH 1 Puzzles"))
        self.forbidden = forbidden
        self.edits = []

    async def edit(self, name):
        if self.forbidden:
            raise nextcord.Forbidden(_Response(), "Missing Permissions")
        self.edits.append(name)
        self.name = name


class _Response:
    status = 403
    reason = "Forbidden"


def _ctx(channel):
    return FakeContext(FakeGuild(categories=[channel.category]), channel)


# status_channel


async def test_status_channel_adds_prefix():
    channel = EditableChannel("puzzle-1")
    embed = await solved_utils.status_channel(_ctx(channel), "solved")
    assert channel.name == "solved-puzzle-1"
    [field] = embed.fields
    assert field.name == "Success"
    assert field.value == f"Marking {channel.mention} as solved!"


async def test_status_channel_swaps_prefix():
    channel = EditableChannel("solved-puzzle-1")
    await solved_utils.status_channel(_ctx(channel), "backsolved")
    assert channel.edits == ["backsolved-puzzle-1"]


async def test_status_channel_already_marked():
    channel = EditableChannel("solved-puzzle-1")
    embed = await solved_utils.status_channel(_ctx(channel), "solved")
    assert channel.edits == []
    [field] = embed.fields
    assert field.name == "Failed"
    assert field.value == "Channel already marked as solved!"


async def test_status_channel_forbidden_sends_and_returns_none():
    channel = EditableChannel("puzzle-1", forbidden=True)
    ctx = _ctx(channel)
    assert await solved_utils.status_channel(ctx, "solved") is None
    [embed] = ctx.sent_embeds
    assert embed.fields[0].name == "Failed"
    assert "manage_channels" in embed.fields[0].value


# status_remove


@pytest.mark.parametrize(
    "name, prefix",
    [
        ("solved-puzzle-1", "solved"),
        ("solvedish-puzzle-1", "solvedish"),
        ("backsolved-puzzle-1", "backsolved"),
        ("postsolved-puzzle-1", "postsolved"),
    ],
)
async def test_status_remove(name, prefix):
    channel = EditableChannel(name)
    embed = await solved_utils.status_remove(_ctx(channel))
    assert channel.edits == ["puzzle-1"]
    [field] = embed.fields
    assert field.name == "Success"
    assert field.value == f"Marking {channel.mention} as un-{prefix}!"


async def test_status_remove_not_marked():
    channel = EditableChannel("puzzle-1")
    embed = await solved_utils.status_remove(_ctx(channel))
    assert channel.edits == []
    [field] = embed.fields
    assert field.name == "Failed"
    assert field.value == (
        "Channel is not marked as `solved / solvedish / backsolved / postsolved`!"
    )


# Status changes queued behind a rename that Discord holds back


class _RateLimited:
    status = 429
    reason = "Too Many Requests"
    headers = {"Retry-After": "0.05"}


class HeldBackChannel(EditableChannel):
    """The first rename is refused with a 429, like a 3rd rename within 10 minutes."""

    def __init__(self, name):
        super().__init__(name)
        self.held_back = False

    async def edit(self, name):
        if not self.held_back:
            self.held_back = True
            raise nextcord.HTTPException(_RateLimited(), "rate limited")
        await super().edit(name)


@pytest.fixture
def queued_renames(monkeypatch):
    monkeypatch.setattr(discord_utils, "RENAME_WAIT_MARGIN", 0)
    monkeypatch.setattr(discord_utils, "_rename_queues", {})


async def test_unsolved_while_solved_waits_undoes_it(queued_renames):
    channel = HeldBackChannel("puzzle-1")
    solved = asyncio.create_task(solved_utils.status_channel(_ctx(channel), "solved"))
    await asyncio.sleep(0.01)

    # The channel is still called puzzle-1 here, but ~unsolved sees the waiting ~solved
    embed = await solved_utils.status_remove(_ctx(channel))
    solved_embed = await solved

    assert channel.edits == []  # back where it started, no rename needed
    assert channel.name == "puzzle-1"
    assert embed.fields[0].name == "Success"
    assert embed.fields[0].value == f"Marking {channel.mention} as un-solved!"
    assert solved_embed is None  # only ~unsolved reports


async def test_backsolved_while_solved_waits_replaces_it(queued_renames):
    channel = HeldBackChannel("puzzle-1")
    solved = asyncio.create_task(solved_utils.status_channel(_ctx(channel), "solved"))
    await asyncio.sleep(0.01)

    # ~unsolved then ~backsolved should mean the channel goes straight to backsolved
    await solved_utils.status_remove(_ctx(channel))
    backsolved = await solved_utils.status_channel(_ctx(channel), "backsolved")
    solved_embed = await solved

    assert channel.edits == ["backsolved-puzzle-1"]
    assert backsolved.fields[0].value == f"Marking {channel.mention} as backsolved!"
    assert solved_embed is None


async def test_second_solved_while_the_first_waits_is_already_marked(queued_renames):
    channel = HeldBackChannel("puzzle-1")
    first = asyncio.create_task(solved_utils.status_channel(_ctx(channel), "solved"))
    await asyncio.sleep(0.01)

    second = await solved_utils.status_channel(_ctx(channel), "solved")
    await first

    assert channel.edits == ["solved-puzzle-1"]  # no rename wasted
    assert second.fields[0].value == "Channel already marked as solved!"


# Prefix


def test_prefix_class():
    p = solved_utils.Prefix("solved-puzzle", "solved-")
    assert p.has_prefix()
    assert p.remove_prefix() == "puzzle"
    assert solved_utils.Prefix("puzzle", "solved-").add_prefix() == "solved-puzzle"
    assert not solved_utils.Prefix("puzzle", "solved-").has_prefix()
