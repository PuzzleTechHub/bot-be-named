import nextcord
import pytest

from tests.fakes import FakeCategory, FakeChannel, FakeContext, FakeGuild
from utils import solved_utils


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


# Prefix


def test_prefix_class():
    p = solved_utils.Prefix("solved-puzzle", "solved-")
    assert p.has_prefix()
    assert p.remove_prefix() == "puzzle"
    assert solved_utils.Prefix("puzzle", "solved-").add_prefix() == "solved-puzzle"
    assert not solved_utils.Prefix("puzzle", "solved-").has_prefix()
