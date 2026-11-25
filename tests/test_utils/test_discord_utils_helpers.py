import asyncio
from types import SimpleNamespace

import nextcord
import pytest

import constants
from tests.fakes import (
    FakeCategory,
    FakeChannel,
    FakeContext,
    FakeForum,
    FakeGuild,
    FakeMember,
    FakeRole,
    FakeThread,
)
from utils import discord_utils, logging_utils


def _ctx(**guild_attrs):
    guild = FakeGuild()
    for name, value in guild_attrs.items():
        setattr(guild, name, value)
    return FakeContext(guild, FakeChannel(20, "bot-commands"))


# send_message


async def test_send_message_short_embed():
    ctx = _ctx()
    embed = discord_utils.create_success_embed("Done")
    sent = await discord_utils.send_message(ctx, embed)
    assert sent == ctx.sent
    # split_embed always sends a copy
    [copy] = ctx.sent_embeds
    assert copy.to_dict() == embed.to_dict()


async def test_send_message_splits_long_field():
    ctx = _ctx()
    embed = discord_utils.create_embed()
    long_text = ("word " * 1000).strip()
    embed.add_field(name="Puzzles", value=long_text, inline=False)
    await discord_utils.send_message(ctx, embed)
    fields = [f for e in ctx.sent_embeds for f in e.fields]
    assert len(fields) > 1
    assert "".join(f.value for f in fields) == long_text


async def test_send_message_long_field_ending_on_split():
    ctx = _ctx()
    embed = discord_utils.create_embed()
    embed.add_field(name="Puzzles", value="word " * 1000, inline=False)
    await discord_utils.send_message(ctx, embed)


async def test_send_message_splits_many_fields():
    ctx = _ctx()
    embed = discord_utils.create_embed()
    for n in range(10):
        embed.add_field(name=f"Field {n}", value="x" * 1000, inline=False)
    sent = await discord_utils.send_message(ctx, embed)
    # FakeContext.send would have refused anything Discord rejects
    assert len(sent) > 1
    assert sum(len(e.fields) for e in ctx.sent_embeds) == 10


# Checks


@pytest.mark.parametrize(
    "count, full", [(0, False), (49, False), (50, True), (51, True)]
)
def test_category_is_full(count, full):
    category = SimpleNamespace(channels=[object()] * count)
    assert discord_utils.category_is_full(category) is full


@pytest.mark.parametrize("count, full", [(499, False), (500, True)])
def test_server_is_full(count, full):
    guild = SimpleNamespace(channels=[object()] * count)
    assert discord_utils.server_is_full(guild) is full


# Embeds


@pytest.mark.parametrize(
    "value, ids, mention",
    [
        ("1234", [1234], "<@1234>"),
        ("", [], "the bot owner"),
        ("1234, 5678,9", [1234, 5678, 9], "<@1234>"),
        (" 1234 , 5678 , 9 ", [1234, 5678, 9], "<@1234>"),
        (" 1234 ", [1234], "<@1234>"),
        (" 1234 ,4321", [1234, 4321], "<@1234>"),
    ],
)
def test_bot_owners_from_env(monkeypatch, value, ids, mention):
    monkeypatch.setenv("BOT_OWNER_DISCORD_ID", value)
    assert discord_utils.bot_owner_ids() == ids
    assert discord_utils.bot_owner_mention() == mention


def test_bot_owners_env_not_set(monkeypatch):
    monkeypatch.delenv("BOT_OWNER_DISCORD_ID", raising=False)
    assert discord_utils.bot_owner_ids() == []
    assert discord_utils.bot_owner_mention() == "the bot owner"


def test_create_embed():
    embed = discord_utils.create_embed()
    assert embed.description == ""
    assert embed.color.value == constants.EMBED_COLOR
    assert embed.fields == []


@pytest.mark.parametrize(
    "args, value",
    [
        ((), "You need to supply a argument!"),
        (("channel",), "You need to supply a channel!"),
    ],
)
def test_create_no_argument_embed(args, value):
    [field] = discord_utils.create_no_argument_embed(*args).fields
    assert (field.name, field.value) == ("Failed", value)


@pytest.mark.parametrize("inline", [False, True])
def test_populate_embed(inline):
    embed = discord_utils.populate_embed(["a", "b"], ["1", "2"], inline=inline)
    assert [(f.name, f.value, f.inline) for f in embed.fields] == [
        ("a", "1", inline),
        ("b", "2", inline),
    ]
    assert embed.color.value == constants.EMBED_COLOR


def test_populate_embed_uneven():
    with pytest.raises(AssertionError):
        discord_utils.populate_embed(["a", "b"], ["1"])


# Finds


async def test_find_role_ignores_case():
    gph1 = FakeRole(11, "GPH1")
    ctx = _ctx(roles=[FakeRole(1, "@everyone"), gph1])
    assert await discord_utils.find_role(ctx, "gph1") is gph1
    assert await discord_utils.find_role(ctx, "GPH2") is None
    assert await discord_utils.find_role(ctx, None) is None


def _member(name, display_name=None, global_name=None):
    member = FakeMember(name=name)
    member.display_name = display_name
    member.global_name = global_name
    return member


@pytest.mark.parametrize("query", ["solver", "SOLVER", "Nick", "Global Name"])
async def test_find_user_by_any_name(query):
    member = _member("solver", "Nick", "Global Name")
    ctx = _ctx(members=[_member("other", "Other"), member])
    assert await discord_utils.find_user(ctx, query) is member


async def test_find_user_missing_names_and_not_found():
    ctx = _ctx(members=[_member("solver")])
    assert await discord_utils.find_user(ctx, "nobody") is None
    assert await discord_utils.find_user(ctx, None) is None


async def test_find_user_fetches_member_list_first():
    ctx = _ctx(members=[_member("solver")], chunked=False)
    assert await discord_utils.find_user(ctx, "solver") is not None
    assert ctx.guild.chunk_calls == 1


# ensure_members_cached / chunk_all_guilds


async def test_ensure_members_cached_skips_dms_and_cached_guilds():
    guild = FakeGuild()
    assert await discord_utils.ensure_members_cached(None) is True
    assert await discord_utils.ensure_members_cached(guild) is True
    assert guild.chunk_calls == 0


async def test_ensure_members_cached_fetches_uncached_guild():
    guild = FakeGuild()
    guild.chunked = False
    assert await discord_utils.ensure_members_cached(guild) is True
    assert guild.chunk_calls == 1
    # Now cached, so no second fetch
    assert await discord_utils.ensure_members_cached(guild) is True
    assert guild.chunk_calls == 1


async def test_ensure_members_cached_timeout(monkeypatch):
    async def never_answers():
        await asyncio.sleep(10)

    monkeypatch.setattr(discord_utils, "MEMBER_FETCH_TIMEOUT", 0.01)
    guild = FakeGuild()
    guild.chunked = False
    guild.chunk = never_answers
    assert await discord_utils.ensure_members_cached(guild) is False


async def test_ensure_members_cached_without_members_intent():
    async def no_intent():
        raise nextcord.ClientException("Intents.members must be enabled to use this.")

    guild = FakeGuild()
    guild.chunked = False
    guild.chunk = no_intent
    assert await discord_utils.ensure_members_cached(guild) is False


async def test_chunk_all_guilds_carries_on_after_a_failure():
    async def broken():
        raise RuntimeError("gateway closed")

    guilds = [FakeGuild(i, f"Guild {i}") for i in range(3)]
    for guild in guilds:
        guild.chunked = False
    guilds[1].chunk = broken
    assert await discord_utils.chunk_all_guilds(guilds) == [guilds[1]]
    assert guilds[0].chunk_calls == 1
    assert guilds[2].chunk_calls == 1


async def test_find_guild():
    first = FakeGuild(1, "First")
    second = FakeGuild(2, "Second")
    ctx = _ctx()
    ctx.bot = SimpleNamespace(guilds=[first, second])
    assert await discord_utils.find_guild(ctx, "Second") is second
    assert await discord_utils.find_guild(ctx, "second") is None
    assert await discord_utils.find_guild(ctx, None) is None


async def test_find_guild_without_bot():
    assert await discord_utils.find_guild(_ctx(), "Second") is None


# pin_message


class _Response:
    def __init__(self, status):
        self.status = status
        self.reason = "error"


class PinChannel(FakeChannel):
    def __init__(self, pins=0, history=()):
        super().__init__(20, "puzzle")
        self._pins = [object()] * pins
        self._history = list(history)

    async def pins(self):
        return self._pins

    async def history(self, limit):
        for message in self._history[:limit]:
            yield message


class PinMessage:
    def __init__(self, channel, error=None):
        self.channel = channel
        self.error = error
        self.calls = []

    async def unpin(self):
        self.calls.append("unpin")

    async def pin(self):
        if self.error:
            raise self.error
        self.calls.append("pin")


class SystemMessage:
    def __init__(self, message_type):
        self.type = message_type
        self.deleted = False

    async def delete(self):
        self.deleted = True


async def test_pin_message_deletes_pin_notice():
    notice = SystemMessage(nextcord.MessageType.pins_add)
    other = SystemMessage(nextcord.MessageType.default)
    message = PinMessage(PinChannel(history=[other, notice]))
    assert await discord_utils.pin_message(message) is None
    assert message.calls == ["unpin", "pin"]
    assert notice.deleted and not other.deleted


async def test_pin_message_channel_full():
    message = PinMessage(PinChannel(pins=50))
    [field] = (await discord_utils.pin_message(message)).fields
    assert "max. number of pins (50)" in field.value
    assert message.calls == []


async def test_pin_message_forbidden():
    channel = PinChannel()
    message = PinMessage(channel, nextcord.Forbidden(_Response(403), "no"))
    [field] = (await discord_utils.pin_message(message)).fields
    assert field.name == "Failed to pin!"
    assert f"permissions to pin a message in {channel.mention}" in field.value


async def test_pin_message_system_message():
    message = PinMessage(PinChannel(), nextcord.HTTPException(_Response(400), "no"))
    [field] = (await discord_utils.pin_message(message)).fields
    assert "Cannot pin system messages" in field.value


# get_category_channels


def _fake_voice():
    return SimpleNamespace(type=nextcord.ChannelType.voice)


async def test_get_category_channels_threads_follow_their_channel():
    category = FakeCategory(100, "Puzzles")
    hub = FakeChannel(1, "hub", category)
    thread = FakeThread(2, "thread-puzzle", hub)
    p1 = FakeChannel(3, "puzzle-1", category)
    forum = FakeForum(4, "forum", category)
    post = FakeThread(5, "forum-post", forum)
    # The forum itself has no messages, so it isn't listed
    result = await discord_utils.get_category_channels(category)
    assert result == [hub, thread, p1, post]


async def test_get_category_channels_default_skips_archived_without_api_calls():
    category = FakeCategory(100, "Puzzles")
    hub = FakeChannel(1, "hub", category)
    FakeThread(2, "solved", hub, archived=True)
    FakeThread(3, "private", hub, private=True)
    forum = FakeForum(4, "forum", category)
    FakeThread(5, "solved-post", forum, archived=True, cached=False)
    assert await discord_utils.get_category_channels(category) == [hub]
    assert hub.archived_calls == forum.archived_calls == 0


async def test_get_category_channels_include_archived():
    category = FakeCategory(100, "Puzzles")
    hub = FakeChannel(1, "hub", category)
    active = FakeThread(2, "active", hub)
    cached = FakeThread(3, "archived-cached", hub, archived=True)
    uncached = FakeThread(4, "archived-uncached", hub, archived=True, cached=False)
    FakeThread(5, "private", hub, archived=True, private=True)
    forum = FakeForum(6, "forum", category)
    post = FakeThread(7, "old-post", forum, archived=True, cached=False)

    result = await discord_utils.get_category_channels(category, include_archived=True)

    # Active threads first, each thread once, private threads never
    assert result == [hub, active, cached, uncached, post]


async def test_get_category_channels_archived_forbidden_keeps_active():
    category = FakeCategory(100, "Puzzles")
    hub = FakeChannel(1, "hub", category)
    active = FakeThread(2, "active", hub)
    FakeThread(3, "archived", hub, archived=True, cached=False)
    hub.archived_error = nextcord.Forbidden(
        SimpleNamespace(status=403, reason="Forbidden"), "Missing Access"
    )
    p1 = FakeChannel(4, "puzzle-1", category)
    old = FakeThread(5, "old", p1, archived=True, cached=False)

    result = await discord_utils.get_category_channels(category, include_archived=True)

    assert result == [hub, active, p1, old]


async def test_get_category_channels_skips_voice_and_keeps_news():
    category = FakeCategory(100, "Puzzles")
    news = SimpleNamespace(type=nextcord.ChannelType.news, threads=[])
    category.channels += [_fake_voice(), news]
    assert await discord_utils.get_category_channels(category) == [news]


async def test_get_category_channels_empty():
    category = FakeCategory(100, "Empty")
    assert await discord_utils.get_category_channels(category) == []


# rename_channel


class RenamableChannel(FakeChannel):
    def __init__(self, name, error=None):
        super().__init__(20, name, FakeCategory(10, "Puzzles"))
        self.guild = FakeGuild()
        self.error = error

    async def edit(self, name):
        if self.error:
            raise self.error
        self.name = name


async def test_rename_channel_logs_the_attempt_and_the_result(monkeypatch):
    lines = []
    monkeypatch.setattr(logging_utils, "print_with_timestamp", lines.append)
    channel = RenamableChannel("puzzle-1")

    await discord_utils.rename_channel(channel, "solved-puzzle-1")

    assert channel.name == "solved-puzzle-1"
    assert lines[0] == "Renaming #puzzle-1 to #solved-puzzle-1 in Test server (20)"
    assert lines[1].startswith("Renamed #puzzle-1 to #solved-puzzle-1 after ")


async def test_rename_channel_logs_and_reraises_a_failure(monkeypatch):
    lines = []
    monkeypatch.setattr(logging_utils, "print_with_timestamp", lines.append)
    channel = RenamableChannel(
        "puzzle-1", nextcord.Forbidden(_Response(403), "Missing Permissions")
    )

    with pytest.raises(nextcord.Forbidden):
        await discord_utils.rename_channel(channel, "solved-puzzle-1")

    assert channel.name == "puzzle-1"
    assert lines[1].startswith("Rename of #puzzle-1 to #solved-puzzle-1 failed after ")
    assert lines[1].endswith(": Forbidden")
