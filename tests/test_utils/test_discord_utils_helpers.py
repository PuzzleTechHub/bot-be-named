import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

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
    """edit() raises each of errors in turn, then renames."""

    def __init__(self, name, *errors, channel_id=20):
        super().__init__(channel_id, name, FakeCategory(10, "Puzzles"))
        self.guild = FakeGuild()
        self.errors = list(errors)
        self.renames = []

    async def edit(self, name):
        await asyncio.sleep(0)
        if self.errors:
            raise self.errors.pop(0)
        self.name = name
        self.renames.append(name)


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


# numbered_categories and category_move_to_archive


def _archive_guild(*names, full=()):
    categories = [FakeCategory(100 + i, name) for i, name in enumerate(names)]
    for category in categories:
        if category.name in full:
            category.channels = [object()] * 50
    return FakeGuild(categories=categories)


def _category(guild, name):
    return next(category for category in guild.categories if category.name == name)


def test_numbered_categories_sorted_by_number():
    guild = _archive_guild(
        "Puzzles Archive 3", "Puzzles Archive", "Puzzles archive 2", "Puzzles Archived"
    )
    base = _category(guild, "Puzzles Archive")
    assert [(n, c.name) for n, c in discord_utils.numbered_categories(guild, base)] == [
        (1, "Puzzles Archive"),
        (2, "Puzzles archive 2"),
        (3, "Puzzles Archive 3"),
    ]


def test_numbered_categories_ignores_other_names():
    guild = _archive_guild(
        "Puzzles Archive", "Puzzles Archived", "Puzzles Archive old", "Other Archive 2"
    )
    base = _category(guild, "Puzzles Archive")
    assert discord_utils.numbered_categories(guild, base) == [(1, base)]


def _mta_ctx(guild, monkeypatch):
    """A channel in Puzzles, plus a clonecat that adds the new category to the guild."""

    async def find(ctx, name):
        return next((c for c in guild.categories if c.name == name), None)

    monkeypatch.setattr(discord_utils, "find_category", find)
    channel = MagicMock(spec=nextcord.TextChannel)
    channel.type = nextcord.ChannelType.text
    channel.category = FakeCategory(1, "Puzzles")
    channel.mention = "<#20>"
    channel.edit = AsyncMock()
    ctx = FakeContext(guild, channel)
    ctx.bot = SimpleNamespace(get_command=lambda name: name)
    ctx.cloned = []

    async def invoke(command, origCatName, targetCatName):
        ctx.cloned.append((command, origCatName, targetCatName))
        guild.categories.append(FakeCategory(999, targetCatName))

    ctx.invoke = invoke
    return ctx, channel


async def test_mta_uses_the_highest_numbered_archive_even_with_room_lower(
    monkeypatch,
):
    guild = _archive_guild("Puzzles Archive", "Puzzles Archive 3", "Puzzles Archive 2")
    ctx, channel = _mta_ctx(guild, monkeypatch)

    await discord_utils.category_move_to_archive(ctx, None)

    channel.edit.assert_any_await(category=_category(guild, "Puzzles Archive 3"))
    assert ctx.cloned == []


async def test_mta_makes_the_next_archive_when_the_highest_is_full(monkeypatch):
    guild = _archive_guild(
        "Puzzles Archive", "Puzzles Archive 2", full=("Puzzles Archive 2",)
    )
    ctx, channel = _mta_ctx(guild, monkeypatch)

    await discord_utils.category_move_to_archive(ctx, None)

    assert ctx.cloned == [("clonecat", "Puzzles Archive 2", "Puzzles Archive 3")]
    channel.edit.assert_any_await(category=_category(guild, "Puzzles Archive 3"))


async def test_mta_uses_a_named_archive_as_given(monkeypatch):
    guild = _archive_guild("Puzzles Archive", "Puzzles Archive 2")
    ctx, channel = _mta_ctx(guild, monkeypatch)

    await discord_utils.category_move_to_archive(ctx, "Puzzles Archive")

    channel.edit.assert_any_await(category=_category(guild, "Puzzles Archive"))


async def test_mta_named_archive_when_full_moves_to_the_highest(monkeypatch):
    guild = _archive_guild(
        "Puzzles Archive", "Puzzles Archive 2", full=("Puzzles Archive",)
    )
    ctx, channel = _mta_ctx(guild, monkeypatch)

    await discord_utils.category_move_to_archive(ctx, "Puzzles Archive")

    channel.edit.assert_any_await(category=_category(guild, "Puzzles Archive 2"))
    assert ctx.cloned == []


def _rename_ctx(channel):
    return FakeContext(channel.guild, channel)


async def test_quick_rename_sends_no_notice():
    channel = RenamableChannel("puzzle-1")
    ctx = _rename_ctx(channel)

    await discord_utils.rename_channel(channel, "solved-puzzle-1", notify=ctx)

    assert channel.name == "solved-puzzle-1"
    assert ctx.sent == []


class _RateLimited:
    """A 429 response like the one Discord sends after 2 renames in 10 minutes."""

    status = 429
    reason = "Too Many Requests"

    def __init__(self, retry_after="0.01"):
        self.headers = {} if retry_after is None else {"Retry-After": retry_after}


def rate_limited(retry_after="0.01"):
    return nextcord.HTTPException(
        _RateLimited(retry_after), "The resource is being rate limited."
    )


@pytest.fixture
def no_wait_margin(monkeypatch):
    monkeypatch.setattr(discord_utils, "RENAME_WAIT_MARGIN", 0)


@pytest.fixture(autouse=True)
def fresh_rename_locks(monkeypatch):
    # Each test has its own event loop, and an asyncio.Lock belongs to one loop
    monkeypatch.setattr(discord_utils, "_rename_queues", {})


async def test_rate_limited_rename_waits_says_so_and_retries(no_wait_margin):
    channel = RenamableChannel("puzzle-1", rate_limited())
    ctx = _rename_ctx(channel)

    await discord_utils.rename_channel(
        channel, "solved-puzzle-1", notify=ctx, note="The sheet is done."
    )

    assert channel.name == "solved-puzzle-1"
    [notice] = ctx.sent
    [field] = notice.embed.fields
    assert field.name == "Rename in progress"
    assert "2 renames per channel every 10 minutes" in field.value
    assert "`solved-puzzle-1` in about 1 second." in field.value
    assert field.value.endswith("The sheet is done.")
    assert notice.deleted


async def test_rate_limited_twice_sends_one_notice(no_wait_margin):
    channel = RenamableChannel("puzzle-1", rate_limited(), rate_limited())
    ctx = _rename_ctx(channel)

    await discord_utils.rename_channel(channel, "solved-puzzle-1", notify=ctx)

    assert channel.name == "solved-puzzle-1"
    [notice] = ctx.sent
    assert notice.deleted


async def test_gives_up_after_waiting_too_many_times(no_wait_margin, monkeypatch):
    monkeypatch.setattr(discord_utils, "RENAME_MAX_WAITS", 2)
    channel = RenamableChannel("puzzle-1", *[rate_limited() for _ in range(3)])
    ctx = _rename_ctx(channel)

    with pytest.raises(nextcord.HTTPException):
        await discord_utils.rename_channel(channel, "solved-puzzle-1", notify=ctx)

    assert channel.name == "puzzle-1"
    [notice] = ctx.sent
    assert notice.deleted


async def test_does_not_wait_longer_than_the_maximum(monkeypatch):
    lines = []
    monkeypatch.setattr(logging_utils, "print_with_timestamp", lines.append)
    channel = RenamableChannel("puzzle-1", rate_limited(retry_after="3600"))
    ctx = _rename_ctx(channel)

    with pytest.raises(nextcord.HTTPException):
        await discord_utils.rename_channel(channel, "solved-puzzle-1", notify=ctx)

    assert ctx.sent == []
    assert lines[-1].endswith(": HTTPException")


async def test_other_errors_are_not_retried():
    channel = RenamableChannel(
        "puzzle-1", nextcord.Forbidden(_Response(403), "Missing Permissions")
    )
    ctx = _rename_ctx(channel)

    with pytest.raises(nextcord.Forbidden):
        await discord_utils.rename_channel(channel, "solved-puzzle-1", notify=ctx)

    assert ctx.sent == []


async def test_notice_that_cannot_be_sent_does_not_stop_the_rename(no_wait_margin):
    channel = RenamableChannel("puzzle-1", rate_limited())

    class Muted:
        async def send(self, embed):
            raise nextcord.Forbidden(_Response(403), "Missing Permissions")

    await discord_utils.rename_channel(channel, "solved-puzzle-1", notify=Muted())

    assert channel.name == "solved-puzzle-1"


async def test_rate_limited_rename_without_notify_just_waits(no_wait_margin):
    channel = RenamableChannel("puzzle-1", rate_limited())

    await discord_utils.rename_channel(channel, "solved-puzzle-1")

    assert channel.name == "solved-puzzle-1"


async def test_rename_during_a_wait_replaces_the_waiting_one(no_wait_margin):
    channel = RenamableChannel("b", rate_limited("0.05"))
    first_ctx, second_ctx = _rename_ctx(channel), _rename_ctx(channel)

    first = asyncio.create_task(
        discord_utils.rename_channel(channel, "c", notify=first_ctx)
    )
    await asyncio.sleep(0.01)
    second = await discord_utils.rename_channel(channel, "d", notify=second_ctx)

    assert channel.renames == ["d"]  # one request, straight to the newest name
    assert second == discord_utils.Renamed("b", "d", replaced=False)
    assert await first == discord_utils.Renamed("b", "d", replaced=True)
    [notice] = second_ctx.sent
    assert "to `d` instead of `c` in about 1 second." in notice.embed.fields[0].value
    assert all(m.deleted for m in first_ctx.sent + second_ctx.sent)


async def test_each_rename_during_a_wait_replaces_the_one_before(no_wait_margin):
    channel = RenamableChannel("b", rate_limited("0.05"))
    ctx = _rename_ctx(channel)

    first = asyncio.create_task(discord_utils.rename_channel(channel, "c"))
    await asyncio.sleep(0.01)
    second = asyncio.create_task(discord_utils.rename_channel(channel, "d"))
    await asyncio.sleep(0.01)
    third = await discord_utils.rename_channel(channel, "e", notify=ctx)

    assert channel.renames == ["e"]
    assert third.replaced is False
    assert (await first).replaced and (await second).replaced
    assert "to `e` instead of `d`" in ctx.sent[0].embed.fields[0].value


async def test_renaming_back_during_a_wait_sends_no_request(no_wait_margin):
    # e.g. ~solved, then ~unsolved while the first rename waits for Discord
    channel = RenamableChannel("puzzle-1", rate_limited("0.05"))

    first = asyncio.create_task(
        discord_utils.rename_channel(channel, "solved-puzzle-1")
    )
    await asyncio.sleep(0.01)
    second = await discord_utils.rename_channel(channel, "puzzle-1")

    assert channel.renames == []
    assert second == discord_utils.Renamed("puzzle-1", "puzzle-1", replaced=False)
    assert (await first).replaced


async def test_same_name_as_the_waiting_rename_returns_none(no_wait_margin):
    channel = RenamableChannel("b", rate_limited("0.05"))

    first = asyncio.create_task(discord_utils.rename_channel(channel, "c"))
    await asyncio.sleep(0.01)
    assert await discord_utils.rename_channel(channel, "c") is None
    assert await discord_utils.rename_channel(channel, lambda name: name) is None

    assert await first == discord_utils.Renamed("b", "c", replaced=False)
    assert channel.renames == ["c"]


async def test_name_function_during_a_wait_gets_the_waiting_name(no_wait_margin):
    channel = RenamableChannel("puzzle-1", rate_limited("0.05"))
    seen = []

    def add_x(name):
        seen.append(name)
        return name + "-x"

    first = asyncio.create_task(
        discord_utils.rename_channel(channel, "solved-puzzle-1")
    )
    await asyncio.sleep(0.01)
    await discord_utils.rename_channel(channel, add_x)
    await first

    assert seen == ["solved-puzzle-1"]
    assert channel.renames == ["solved-puzzle-1-x"]


async def test_a_failure_after_the_wait_reaches_the_replacing_rename(no_wait_margin):
    forbidden = nextcord.Forbidden(_Response(403), "Missing Permissions")
    channel = RenamableChannel("b", rate_limited("0.05"), forbidden)

    first = asyncio.create_task(discord_utils.rename_channel(channel, "c"))
    await asyncio.sleep(0.01)
    with pytest.raises(nextcord.Forbidden):
        await discord_utils.rename_channel(channel, "d")
    with pytest.raises(nextcord.Forbidden):
        await first

    # The next rename starts afresh
    assert await discord_utils.rename_channel(channel, "e") == ("b", "e", False)


async def test_rename_after_the_wait_ended_queues_instead_of_replacing(
    no_wait_margin,
):
    # The waiting rename has woken up and sent its request, which is still in flight
    class SlowRetry(RenamableChannel):
        def __init__(self):
            super().__init__("b", rate_limited("0.01"))
            self.in_flight = asyncio.Event()
            self.release = asyncio.Event()

        async def edit(self, name):
            if not self.errors and not self.renames:
                self.in_flight.set()
                await self.release.wait()
            await super().edit(name)

    channel = SlowRetry()
    first = asyncio.create_task(discord_utils.rename_channel(channel, "c"))
    await channel.in_flight.wait()
    second = asyncio.create_task(discord_utils.rename_channel(channel, "d"))
    await asyncio.sleep(0.01)
    channel.release.set()

    assert await first == ("b", "c", False)
    assert await second == ("c", "d", False)
    assert channel.renames == ["c", "d"]


async def test_rename_queued_behind_one_in_flight_waits_for_it():
    # The rename before it hasn't hit Discord's limit, it's just not done yet
    channel = RenamableChannel("puzzle-1")
    ctx = _rename_ctx(channel)

    first = asyncio.create_task(
        discord_utils.rename_channel(channel, "solved-puzzle-1")
    )
    await asyncio.sleep(0)
    await discord_utils.rename_channel(channel, "puzzle-1", notify=ctx)
    await first

    assert channel.renames == ["solved-puzzle-1", "puzzle-1"]
    [notice] = ctx.sent
    assert "as soon as the rename before it is done" in notice.embed.fields[0].value
    assert notice.deleted


async def test_a_waiting_rename_does_not_stall_other_channels(no_wait_margin):
    waiting = RenamableChannel("puzzle-1", rate_limited("0.2"), channel_id=21)
    other = RenamableChannel("puzzle-2", channel_id=22)

    slow = asyncio.create_task(discord_utils.rename_channel(waiting, "solved-puzzle-1"))
    await asyncio.sleep(0.01)
    await asyncio.wait_for(
        discord_utils.rename_channel(other, "solved-puzzle-2"), timeout=0.1
    )

    assert other.name == "solved-puzzle-2"
    assert waiting.name == "puzzle-1"  # still waiting for Discord
    await slow
    assert waiting.name == "solved-puzzle-1"


async def test_uses_the_name_discord_returns_without_waiting_for_the_gateway():
    class LaggingChannel(RenamableChannel):
        # Like nextcord: edit() returns the updated channel, the cached one only
        # changes when the gateway update arrives (never, here)
        async def edit(self, name):
            self.renames.append(name)
            return SimpleNamespace(name=name.lower().replace(" ", "-"))

    channel = LaggingChannel("puzzle-1")

    first = await discord_utils.rename_channel(channel, "Solved Puzzle 1")
    second = await discord_utils.rename_channel(channel, lambda name: name + "-x")

    assert first == ("puzzle-1", "solved-puzzle-1", False)
    assert second == ("solved-puzzle-1", "solved-puzzle-1-x", False)
    assert channel.renames == ["Solved Puzzle 1", "solved-puzzle-1-x"]


async def test_nothing_to_rename_returns_none_without_a_request():
    channel = RenamableChannel("puzzle-1")

    assert await discord_utils.rename_channel(channel, "puzzle-1") is None
    assert await discord_utils.rename_channel(channel, lambda name: None) is None
    assert channel.renames == []


def test_retry_after_defaults_when_discord_does_not_say():
    assert (
        discord_utils._retry_after(rate_limited(retry_after=None))
        == discord_utils.RENAME_DEFAULT_WAIT
    )


@pytest.mark.parametrize(
    "seconds, text",
    [
        (0.2, "1 second"),
        (30, "30 seconds"),
        (60, "60 seconds"),
        (90, "2 minutes"),
        (420, "7 minutes"),
    ],
)
def test_wait_text(seconds, text):
    assert discord_utils._wait_text(seconds) == text
