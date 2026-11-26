from types import SimpleNamespace

import nextcord
import pytest

from modules.discord_channel_management.cog import DiscordChannelManagementCog
from tests.fakes import FakeCategory, FakeChannel, FakeContext, FakeGuild
from utils import discord_utils


class _Forbidden:
    status = 403
    reason = "Forbidden"


class FakeHTTP:
    def __init__(self, forbidden=False):
        self.forbidden = forbidden
        self.updates = []

    async def bulk_channel_update(self, guild_id, data, reason=None):
        if self.forbidden:
            raise nextcord.Forbidden(_Forbidden(), "Missing Permissions")
        self.updates.append(data)


def make_category(names, first_position=10):
    """A category whose channels sit at first_position, first_position + 1, ... in order."""
    category = FakeCategory(1, "GPH Puzzles")
    for offset, name in enumerate(names):
        channel = FakeChannel(100 + offset, name, category)
        channel.position = first_position + offset
    guild = FakeGuild(categories=[category])
    guild._state = SimpleNamespace(http=FakeHTTP())
    category.guild = guild
    return category


@pytest.fixture
def cog():
    return DiscordChannelManagementCog(bot=None)


async def run_sortcat(cog, category, monkeypatch):
    async def find_category(ctx, name):
        return category

    monkeypatch.setattr(discord_utils, "find_category", find_category)
    ctx = FakeContext(category.guild, category.text_channels[0])
    await cog.categorysort.callback(cog, ctx)
    return ctx


def names(channels):
    return [channel.name for channel in channels]


def test_backsolved_comes_before_solved(cog):
    category = make_category(
        [
            "solved-a",
            "postsolved-b",
            "backsolved-c",
            "zebra",
            "solvedish-d",
            "apple",
            "solved-e",
        ]
    )
    assert names(cog.sort_channels(category.text_channels)) == [
        "apple",
        "zebra",
        "solvedish-d",
        "backsolved-c",
        "solved-a",
        "solved-e",
        "postsolved-b",
    ]


def test_solvedish_is_not_mistaken_for_solved(cog):
    category = make_category(["solved-b", "solvedish-a"])
    assert names(cog.sort_channels(category.text_channels)) == [
        "solvedish-a",
        "solved-b",
    ]


async def test_sortcat_sends_one_request_moving_only_misplaced_channels(
    cog, monkeypatch
):
    category = make_category(["apple", "solved-x", "banana", "cherry"])

    ctx = await run_sortcat(cog, category, monkeypatch)

    [update] = category.guild._state.http.updates
    by_id = {channel.id: channel.name for channel in category.text_channels}
    # apple stays at 10; banana, cherry, solved-x take 11, 12, 13
    assert [(by_id[d["id"]], d["position"]) for d in update] == [
        ("banana", 11),
        ("cherry", 12),
        ("solved-x", 13),
    ]
    assert ctx.sent_embeds[-1].fields[0].name == "Success"


async def test_sortcat_on_a_sorted_category_sends_nothing(cog, monkeypatch):
    category = make_category(["apple", "banana", "solved-x"])

    ctx = await run_sortcat(cog, category, monkeypatch)

    assert category.guild._state.http.updates == []
    assert "already sorted" in ctx.sent_embeds[-1].fields[0].value


async def test_sortcat_with_clashing_positions_numbers_from_the_lowest(
    cog, monkeypatch
):
    category = make_category(["banana", "apple"])
    for channel in category.text_channels:
        channel.position = 5

    await run_sortcat(cog, category, monkeypatch)

    [update] = category.guild._state.http.updates
    by_id = {channel.id: channel.name for channel in category.text_channels}
    assert {by_id[d["id"]]: d["position"] for d in update} == {"banana": 6}


async def test_sortcat_without_permission_says_so(cog, monkeypatch):
    category = make_category(["banana", "apple"])
    category.guild._state.http.forbidden = True

    ctx = await run_sortcat(cog, category, monkeypatch)

    [embed] = ctx.sent_embeds
    assert embed.fields[0].name == "Failed"
    assert "manage_channels" in embed.fields[0].value
