import asyncio
import os
import re
import time

import nextcord
from nextcord.ext import commands
from typing import Callable, List, NamedTuple, Optional, Union
import constants
from utils import logging_utils

"""
Discord utils. Lots of little functions required for making smoother discord operations,
or deduplicating important code that applies broadly to any Discord facing commands.
Used throughout the bot.
"""

#################
# SENDS MESSAGE #
#################


async def send_message(
    ctx: commands.Context, message: nextcord.Embed
) -> list[nextcord.Message]:
    embeds = split_embed(message)
    return_code = []
    for e in embeds:
        r = await ctx.send(embed=e)
        return_code = return_code + [r]
    return return_code


##########
# CHECKS #
##########


def category_is_full(category: nextcord.CategoryChannel) -> bool:
    """Determines whether a category is full (has 50 channels)
    Arguments:
        - category (nextcord.CategoryChannel)
    Returns:
        - bool
    """
    return len(category.channels) >= 50


def numbered_categories(
    guild: nextcord.Guild, base: nextcord.CategoryChannel
) -> list[tuple[int, nextcord.CategoryChannel]]:
    """The base category and its numbered copies (`Archive`, `Archive 2`, `Archive 3`...),
    as (number, category) sorted by number. The base counts as 1. Names match ignoring case.
    """
    pattern = re.compile(rf"{re.escape(base.name)}\s+(\d+)", re.IGNORECASE)
    numbered = [(1, base)]
    for category in guild.categories:
        match = pattern.fullmatch(category.name)
        if match and category != base:
            numbered.append((int(match.group(1)), category))
    return sorted(numbered, key=lambda pair: pair[0])


def server_is_full(guild: nextcord.Guild) -> bool:
    """Determines whether a guild is full (has 500 channels + Voice chats + categories)
    Arguments:
        - category (nextcord.CategoryChannel)
    Returns:
        - bool
    """
    return len(guild.channels) >= 500


async def is_thread(
    ctx: commands.Context, channel: Union[nextcord.Thread, nextcord.TextChannel, str]
) -> bool:
    """Checks if a given channel is a Thread or not.

    Arguments -
        - channel (nextcord.TextChannel or nextcord.Thread): The channel or thread which we are checking.
        - ctx (nextcord.ext.commands.Context): The command's context

    Returns -
        - True if channel is a Public thread (Thread in a channel that follows regular channel settings)
        - True if channel is a Private thread (Thread in a channel that's restricted to some people)
        - True if channel is a News thread (???? Maybe it's every thread in a ForumChannel)
        - False otherwise
    """
    if isinstance(channel, str):
        channel = await find_chan_or_thread(ctx, channel)

    if channel is None:
        return False

    if channel.type in {
        nextcord.ChannelType.news_thread,
        nextcord.ChannelType.public_thread,
        nextcord.ChannelType.private_thread,
    }:
        return True

    return False


###########
# CREATES #
###########


async def createchannelgeneric(
    guild: nextcord.Guild, category: nextcord.CategoryChannel, name: str
) -> nextcord.TextChannel:
    """Command to create channel in same category with given name
    Arguments:
        - guild (nextcord.Guild): the guild the channel is being created in
        - category (nextcord.TextChannel): the category the channel is being created in
        - name (str): the name for the channel
    Returns:
        - channel (nextcord.TextChannel): The created channel, or none if the bot does not have sufficient perms.
    """
    try:
        # create channel
        channel = await guild.create_text_channel(name, category=category)
    except nextcord.Forbidden:
        # not allowed
        return None
    except nextcord.errors.HTTPException:
        # channel limit
        return None

    return channel


async def createthreadgeneric(
    ctx: commands.Context,
    message: nextcord.Message,
    chan_or_forum: Union[nextcord.TextChannel, nextcord.ForumChannel],
    name: str,
) -> nextcord.Thread:
    """Command to create thread in same channel with given name
    Arguments:
        - guild (nextcord.Guild): the guild the channel is being created in
        - category_or_forum (nextcord.CategoryChannel or nextcord.ForumChannel): the category or forum the channel is being created in
        - name (str): the name for the channel
    Returns:
        - thread (nextcord.Thread): The created thread, or none if the bot does not have sufficient perms.
    """
    if await is_thread(ctx, chan_or_forum):
        return None
    try:
        # create channel
        thread = await chan_or_forum.create_thread(name=name, message=message)
    except nextcord.Forbidden:
        return None

    return thread


async def createforumthreadgeneric(
    ctx: commands.Context,
    thread: nextcord.Thread,
    name: str,
    content: str,
) -> nextcord.Thread | None:
    """Command to create a forum thread in the parent channel
    Arguments:
        - guild (nextcord.Guild): the guild the channel is being created in
        - thread (nextcord.Thread): the forum post to create a sibling of
        - name (str): the name for the thread
    Returns:
        - thread (nextcord.Thread): The created thread, or none if the bot does not have sufficient perms.
    """
    if not await is_thread(ctx, thread):
        print(f"not thread: {thread}")
        return None
    if not isinstance(thread.parent, nextcord.ForumChannel):
        return None

    try:
        # create channel
        new_thread = await thread.parent.create_thread(name=name, content=content)
    except nextcord.Forbidden as e:
        print(e)
        return None

    return new_thread


async def createvoicechannelgeneric(
    guild: nextcord.Guild, category: nextcord.CategoryChannel, name: str
) -> nextcord.TextChannel:
    """Command to create channel in same category with given name
    Arguments:
        - guild (nextcord.Guild): the guild the channel is being created in
        - category (nextcord.CategoryChannel): the category the channel is being created in
        - name (str): the name for the channel
    Returns:
        - channel (nextcord.TextChannel): The created channel, or none if the bot does not have sufficient perms.
    """
    try:
        # create channel
        channel = await guild.create_voice_channel(name, category=category)
    except nextcord.Forbidden:
        return None

    return channel


##########
# EMBEDS #
##########


def bot_owner_ids() -> list[int]:
    """The bot owners' Discord IDs from the .env file, in the order they're listed."""
    raw_ids = os.getenv("BOT_OWNER_DISCORD_ID", "")
    return [int(raw_id) for raw_id in raw_ids.replace(",", " ").split()]


def bot_owner_mention() -> str:
    """Mentions the bot owner from the .env file. With several owners, only the first one is mentioned."""
    owner_ids = bot_owner_ids()
    return f"<@{owner_ids[0]}>" if owner_ids else "the bot owner"


# Discord allows 2 renames per channel every 10 minutes. nextcord retries the 429 only a few
# times, within about 2 seconds, and then raises it, so rename_channel waits out the limit itself.
# A longer wait than RENAME_MAX_WAIT seconds is treated as an error.
RENAME_MAX_WAIT = 15 * 60
# How many times one rename waits for the limit before giving up.
RENAME_MAX_WAITS = 3
# Used when Discord's 429 doesn't say how long to wait.
RENAME_DEFAULT_WAIT = 10 * 60
# Seconds to spare after Discord's wait, so the retry doesn't land just before it allows it.
RENAME_WAIT_MARGIN = 1
# One _ChannelRenames per channel, so renames of the same channel happen one after another.
# The waits are asyncio sleeps in the command's own task while other commands keep running.
_rename_queues: dict[int, "_ChannelRenames"] = {}


class Renamed(NamedTuple):
    """What rename_channel did."""

    old: str
    new: str
    # True if a rename asked for later replaced this one, so new isn't the name asked for.
    # The later command reports the rename; the replaced one should stay quiet.
    replaced: bool = False


class _WaitingRename:
    """A rename held back by Discord's limit. A rename asked for during the wait replaces its
    target, so the channel goes straight to the newest name in one request."""

    def __init__(self, target: str, wait: float):
        self.target = target
        self.wake_at = time.monotonic() + wait
        # (old name, final name), or the error, once the rename is done
        self.done = asyncio.get_running_loop().create_future()


class _ChannelRenames:
    """Renames of one channel: a lock that runs them in order, and the rename (if any) that is
    waiting out Discord's limit."""

    def __init__(self):
        self.lock = asyncio.Lock()
        self.waiting: Optional[_WaitingRename] = None


async def rename_channel(
    channel,
    new_name: Union[str, Callable[[str], Optional[str]]],
    notify=None,
    note: str = "",
) -> Optional[Renamed]:
    """Rename a channel or thread, logging the attempt and how long it took.

    new_name is the new name, or a function that gets the channel's current name and returns
    the new one (None to leave it as it is). The function gets the name the channel will have
    once earlier renames of it are done, so a command that has to wait sees that name.
    If Discord's rename limit holds the rename back, waits until Discord allows it and tries again.
    A rename asked for during that wait replaces the waiting one. The channel goes straight to
    the newest name, and the replaced call's result says replaced=True.
    If notify was given, a temporary note about the channel's rename status will be sent.

    Returns Renamed(old name, the name the channel got, replaced), or None if there was
    nothing to rename.
    """
    queue = _rename_queues.setdefault(channel.id, _ChannelRenames())
    notices = []
    try:
        if queue.waiting is not None:
            return await _replace_waiting_rename(
                queue.waiting, new_name, notify, note, notices
            )
        if queue.lock.locked():
            await _send_rename_notice(
                notices,
                notify,
                "I'll rename this channel as soon as the rename before it is done.",
                note,
            )
        async with queue.lock:
            # The rename before this one may have started waiting for Discord meanwhile
            if queue.waiting is not None:
                return await _replace_waiting_rename(
                    queue.waiting, new_name, notify, note, notices
                )
            old_name = channel.name
            wanted = new_name(old_name) if callable(new_name) else new_name
            if not wanted or wanted == old_name:
                return None
            return await _rename_waiting_out_the_limit(
                channel, queue, old_name, wanted, notify, note, notices
            )
    finally:
        for notice in notices:
            try:
                await notice.delete()
            except nextcord.HTTPException:
                pass  # Already deleted, nothing to clean up.


async def _replace_waiting_rename(waiting, new_name, notify, note, notices):
    """Points a rename that is waiting for Discord at new_name instead, and waits for it."""
    previous = waiting.target
    wanted = new_name(previous) if callable(new_name) else new_name
    if not wanted or wanted == previous:
        return None
    waiting.target = wanted
    await _send_rename_notice(
        notices,
        notify,
        f"I'll rename this channel to `{wanted}` instead of `{previous}` in about "
        f"{_wait_text(waiting.wake_at - time.monotonic())}.",
        note,
    )
    # shield: if this command is cancelled, the rename itself carries on
    old_name, final_name = await asyncio.shield(waiting.done)
    # waiting.target is the last name asked for; a later rename may have replaced this one too
    return Renamed(old_name, final_name, replaced=waiting.target != wanted)


async def _rename_waiting_out_the_limit(
    channel, queue, old_name, new_name, notify, note, notices
) -> Renamed:
    """Renames the channel, waiting out Discord's rename limit.

    While it waits, queue.waiting lets later renames change the target."""
    asked_for = new_name
    where = getattr(getattr(channel, "guild", None), "name", "unknown server")
    logging_utils.print_with_timestamp(
        f"Renaming #{old_name} to #{new_name} in {where} ({channel.id})"
    )
    start = time.monotonic()
    waits = 0
    waiting = None
    try:
        while True:
            try:
                edited = await channel.edit(name=new_name)
                # Discord may tidy the name up (e.g. "My Puzzle" -> "my-puzzle"). Store what it
                # returned, so the next rename doesn't have to wait for the gateway update.
                new_name = getattr(edited, "name", None) or new_name
                channel.name = new_name
                break
            except nextcord.HTTPException as e:
                wait = _retry_after(e)
                if (
                    e.status != 429
                    or waits >= RENAME_MAX_WAITS
                    or wait > RENAME_MAX_WAIT
                ):
                    raise
                waits += 1
                logging_utils.print_with_timestamp(
                    f"Discord is holding back the rename of #{old_name} to #{new_name}, "
                    f"trying again in {wait:.0f} s"
                )
                if waiting is None:
                    waiting = _WaitingRename(new_name, wait)
                else:
                    waiting.wake_at = time.monotonic() + wait
                queue.waiting = waiting
                if not notices:
                    await _send_rename_notice(
                        notices,
                        notify,
                        "Discord allows 2 renames per channel every 10 minutes, so I'll rename "
                        f"this channel to `{new_name}` in about {_wait_text(wait)}.",
                        note,
                    )
                await asyncio.sleep(wait + RENAME_WAIT_MARGIN)
                # The target is settled now. A rename asked for from here on can't change the
                # request about to be sent, so it queues behind this one instead.
                queue.waiting = None
                if waiting.target != new_name:
                    logging_utils.print_with_timestamp(
                        f"Rename of #{old_name} to #{new_name} replaced by #{waiting.target}"
                    )
                    new_name = waiting.target
                    if new_name == channel.name:
                        break  # e.g. ~solved, then ~unsolved during the wait: nothing to do
    except Exception as e:
        _log_rename_failure(old_name, new_name, start, e)
        if waiting is not None:
            queue.waiting = None
            waiting.done.set_exception(e)
            waiting.done.exception()  # Mark it seen, in case no later rename waits on it
        raise
    except asyncio.CancelledError:
        if waiting is not None:
            queue.waiting = None
            waiting.done.cancel()
        raise
    if waiting is not None:
        waiting.done.set_result((old_name, new_name))
    logging_utils.print_with_timestamp(
        f"Renamed #{old_name} to #{new_name} after {time.monotonic() - start:.1f} s"
    )
    return Renamed(
        old_name, new_name, replaced=waiting is not None and waiting.target != asked_for
    )


def _retry_after(error: nextcord.HTTPException) -> float:
    """Seconds Discord asked to wait, from the 429's Retry-After header."""
    try:
        return float(error.response.headers["Retry-After"])
    except (AttributeError, KeyError, TypeError, ValueError):
        return RENAME_DEFAULT_WAIT


def _wait_text(seconds: float) -> str:
    if seconds < 90:
        count, unit = max(1, round(seconds)), "second"
    else:
        count, unit = round(seconds / 60), "minute"
    return f"{count} {unit}{'' if count == 1 else 's'}"


def _log_rename_failure(old_name, new_name, start, error):
    logging_utils.print_with_timestamp(
        f"Rename of #{old_name} to #{new_name} failed after "
        f"{time.monotonic() - start:.1f} s: {type(error).__name__}"
    )


async def _send_rename_notice(notices: list, notify, text: str, note: str) -> None:
    """Sends a "Rename in progress" message to notify, if given, and adds it to notices.
    Does nothing if it can't be sent."""
    if notify is None:
        return
    embed = create_embed()
    embed.add_field(
        name="Rename in progress",
        value=text + (f" {note}" if note else ""),
        inline=False,
    )
    try:
        notices.append(await notify.send(embed=embed))
    except nextcord.HTTPException:
        pass


def create_embed() -> nextcord.Embed:
    """
    Create an empty discord embed with color.
    :return: (nextcord.Embed)
    """
    return nextcord.Embed(description="", color=constants.EMBED_COLOR)


def merge_embed(orig: nextcord.Embed, to_merge: nextcord.Embed) -> nextcord.Embed:
    """
    Takes two discord embeds, and adds all fields in latter to former
    :return: (nextcord.Embed)
    """
    for field in to_merge.fields:
        orig.add_field(
            name=field.name,
            value=field.value,
            inline=field.inline,
        )
    return orig


def create_no_argument_embed(arg_name: str = "argument") -> nextcord.Embed:
    """
    Create an embed which alerts the user they need to supply an argument
    :param arg_name: (str) The type of argument needed (e.g. channel)
    """
    embed = create_embed()
    embed.add_field(name="Failed", value=f"You need to supply a {arg_name}!")
    return embed


def populate_embed(names: list, values: list, inline: bool = False) -> nextcord.Embed:
    """Populate an embed with a list of names and values"""
    assert len(names) == len(values), (
        "Tried to populate an embed with uneven numbers of names and values"
    )
    embed = nextcord.Embed(color=constants.EMBED_COLOR)
    for idx in range(len(names)):
        embed.add_field(name=names[idx], value=values[idx], inline=inline)
    return embed


def create_success_embed(message: str) -> nextcord.Embed:
    """Create a standardized success embed."""
    embed = create_embed()
    embed.add_field(
        name="Success",
        value=message,
        inline=False,
    )
    return embed


def create_failure_embed(message: str) -> nextcord.Embed:
    """Create a standardized failure embed."""
    embed = create_embed()
    embed.add_field(
        name="Failed",
        value=message,
        inline=False,
    )
    return embed


async def send_failure(ctx: commands.Context, message: str) -> list[nextcord.Message]:
    """Send a one-field "Failed" embed."""
    return await send_message(ctx, create_failure_embed(message))


def get_ordinal_suffix(n: int) -> str:
    """Return the ordinal suffix for a number (1st, 2nd, 3rd, 4th, etc.)"""
    if 11 <= (n % 100) <= 13:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


def split_embed(embed: nextcord.Embed) -> List[nextcord.Embed]:
    """Splits embeds that are too long (discord character limit)
    Arguments:
        - embed (nextcord.Embed)
    Returns
        - embed_list (List[nextcord.Embed]):
    """
    embed_title = embed.title or ""
    embed_description = embed.description or ""

    EMBED_CHARACTER_LIMIT = 2000  # Actual limit is 2000.
    FIELD_CHARACTER_LIMIT = 1000  # Actual limit is 1000.
    DISCORD_EMBED_LIMIT = 6000  # Total characters in one embed
    DISCORD_FIELD_COUNT_LIMIT = 25
    embed_list = []

    character_count = len(embed_title) + len(embed_description)
    # If the title + description exceeds the character limit, we must break up the description into smaller parts.
    if character_count > EMBED_CHARACTER_LIMIT:
        print(f"Title and description are too long with {character_count} characters")
        description = embed_description
        while description != "":
            embed_list.append(
                nextcord.Embed(
                    title=(
                        embed_title + " (continued)"
                        if len(embed_title) > 0
                        else embed_title
                    ),
                    color=embed.color,
                )
            )
            # Find the point that is closest to the cutoff but with a space.
            cutoff_point = description[
                : (EMBED_CHARACTER_LIMIT - len(embed_title))
            ].rfind(" ")
            if cutoff_point == -1:
                cutoff_point = EMBED_CHARACTER_LIMIT - len(embed_title) - 1
            embed_list[-1].description = description[: cutoff_point + 1]
            description = description[cutoff_point + 1 :]
    # If the title + description are small, we can just copy them over
    else:
        embed_list.append(
            nextcord.Embed(
                title=embed_title, description=embed_description, color=embed.color
            )
        )

    # Split each field into pieces of at most FIELD_CHARACTER_LIMIT, cutting at spaces,
    # then add them to embeds while each embed stays within Discord's limits.
    for field in embed.fields:
        pieces = []
        value = field.value
        while len(value) > FIELD_CHARACTER_LIMIT:
            cutoff_point = value[:FIELD_CHARACTER_LIMIT].rfind(" ")
            if cutoff_point == -1:
                cutoff_point = FIELD_CHARACTER_LIMIT - 1
            pieces.append(value[: cutoff_point + 1])
            value = value[cutoff_point + 1 :]
        # A field cut exactly at its end leaves nothing, and Discord rejects empty fields
        if value or not pieces:
            pieces.append(value)
        inline = field.inline if len(pieces) == 1 else False

        for piece in pieces:
            current = embed_list[-1]
            if (
                len(current) + len(field.name) + len(piece) > DISCORD_EMBED_LIMIT
                or len(current.fields) >= DISCORD_FIELD_COUNT_LIMIT
            ):
                current = nextcord.Embed(
                    title=embed_title + " (continued)", color=embed.color
                )
                embed_list.append(current)
            current.add_field(name=field.name, value=piece, inline=inline)

    return embed_list


#########
# FINDS #
#########


async def find_guild(
    ctx: commands.Context, guild_name: Union[nextcord.Guild, str]
) -> nextcord.Guild:
    """Uses nextcord.py's GuildConverter to convert the name to a discord Guild
    Arguments:
        - ctx (nextcord.ext.commands.Context): The command's context
        - guild_name (str): The name of the guild
    Returns:
        - guild (nextcord.Guild): the guild or None if not found"""
    if (isinstance(guild_name, nextcord.Guild)) or guild_name is None:
        return guild_name
    guild = None
    try:
        guilds = ctx.bot.guilds
        for currguild in guilds:
            if guild_name == currguild.name:
                guild = currguild
                break
    except Exception:
        pass
    return guild


async def find_category(
    ctx: commands.Context,
    category_name: nextcord.CategoryChannel | str,
) -> nextcord.CategoryChannel | None:
    """Uses nextcord.py's CategoryChannelConverter to convert the name to a discord CategoryChannel
    Arguments:
        - ctx (nextcord.ext.commands.Context): The command's context
        - category_name (str): The name of the category
    Returns:
        - category (nextcord.CategoryChannel): the category or None if not found"""
    if isinstance(category_name, nextcord.CategoryChannel) or category_name is None:
        return category_name

    # Since we have a lot of lookups, collect categories first
    # We do want to find the most specific category first, so we search unnormalized
    cat_names = set(cat.name for cat in ctx.guild.categories)
    candidates = (
        category_name,
        category_name.upper(),
        category_name.title(),
        category_name.capitalize(),
        category_name.lower(),
    )
    for cand in candidates:
        if cand in cat_names:
            return await commands.CategoryChannelConverter().convert(ctx, cand)

    return None


_TEXT_CHANNEL_TYPES = {nextcord.ChannelType.text, nextcord.ChannelType.news}


async def get_category_channels(
    category: nextcord.CategoryChannel, include_archived: bool = False
) -> list[nextcord.TextChannel | nextcord.Thread]:
    """Every place puzzles can be discussed in a category: its text channels, their threads,
    and the posts in its forum channels. Each channel's threads come right after it, active ones first.
    Private threads are always left out.

    Archived threads are left out unless include_archived is True. Active threads come from the bot's
    cache, but archived ones need at least one API call per text or forum channel, so only ask for them
    when needed. A channel whose archived threads the bot can't read just lists its active ones.
    Arguments:
        - category (nextcord.CategoryChannel)
        - include_archived (bool): also list archived threads and forum posts
    Returns:
        - list of text channels and threads"""
    found = []
    for channel in category.channels:
        if channel.type in _TEXT_CHANNEL_TYPES:
            found.append(channel)
        elif channel.type != nextcord.ChannelType.forum:
            continue
        threads = {
            thread.id: thread
            for thread in channel.threads
            if not thread.archived and not thread.is_private()
        }
        if include_archived:
            try:
                async for thread in channel.archived_threads(limit=None):
                    if not thread.is_private():
                        threads.setdefault(thread.id, thread)
            except nextcord.HTTPException:
                pass
        found.extend(threads.values())
    return found


_CHANNEL_NAME_EDGE_JUNK = "\u2060\u200b\u200c\u200d\ufeff \t\n\r"


def _normalize_channel_query(chan_name: Optional[str]) -> Optional[str]:
    """Strip leading # and edge paste artifacts from a channel name query.

    Returns None if chan_name is None or empty after cleaning.
    """
    if chan_name is None:
        return None
    cleaned = chan_name.strip(_CHANNEL_NAME_EDGE_JUNK)
    cleaned = cleaned.lstrip("#").strip(_CHANNEL_NAME_EDGE_JUNK)
    return cleaned or None


async def _lookup_chan_or_thread(
    ctx: commands.Context, query: str, *, normalize_names: bool
) -> Union[
    nextcord.TextChannel,
    nextcord.Thread,
    nextcord.ForumChannel,
    nextcord.VoiceChannel,
    None,
]:
    """Try converters, then case-insensitive name match for one query string."""
    for converter in (
        commands.TextChannelConverter,
        commands.ThreadConverter,
        commands.GuildChannelConverter,
    ):
        try:
            chan_or_thread = await converter().convert(ctx, query)

            if not isinstance(
                chan_or_thread,
                nextcord.TextChannel
                | nextcord.Thread
                | nextcord.ForumChannel
                | nextcord.VoiceChannel,
            ):
                continue

            return chan_or_thread
        except commands.BadArgument:
            continue

    # Fallback: case-insensitive name match (same idea as find_role).
    query_lower = query.lower()
    for channel in ctx.guild.channels:
        if not isinstance(
            channel,
            nextcord.TextChannel | nextcord.VoiceChannel | nextcord.ForumChannel,
        ):
            continue
        name = (
            _normalize_channel_query(channel.name) if normalize_names else channel.name
        )
        if name is not None and name.lower() == query_lower:
            return channel
    for thread in getattr(ctx.guild, "threads", []):
        name = _normalize_channel_query(thread.name) if normalize_names else thread.name
        if name is not None and name.lower() == query_lower:
            return thread
    return None


async def find_chan_or_thread(
    ctx: commands.Context,
    chan_name: Union[
        nextcord.TextChannel,
        nextcord.Thread,
        nextcord.ForumChannel,
        nextcord.VoiceChannel,
        str,
        None,
    ],
) -> Union[
    nextcord.TextChannel,
    nextcord.Thread,
    nextcord.ForumChannel,
    nextcord.VoiceChannel,
    None,
]:
    """Convert a name or object to a nextcord channel/thread.

    Arguments:
        - ctx (nextcord.ext.commands.Context): The command's context
        - chan_name: Channel/thread object, name string, or None
    Returns:
        - TextChannel, Thread, ForumChannel, VoiceChannel, or None if not found
    """

    if (
        isinstance(
            chan_name,
            nextcord.TextChannel
            | nextcord.Thread
            | nextcord.ForumChannel
            | nextcord.VoiceChannel,
        )
        or chan_name is None
    ):
        return chan_name

    raw = str(chan_name)
    # Prefer exact input first so a VC named "#1" stays findable.
    found = await _lookup_chan_or_thread(ctx, raw, normalize_names=False)
    if found is not None:
        return found

    # Then strip paste junk / leading # (e.g. "⁠test-channel", "#general").
    query = _normalize_channel_query(raw)
    if not query or query == raw:
        return None
    return await _lookup_chan_or_thread(ctx, query, normalize_names=True)


async def find_role(
    ctx: commands.Context, role_name: Union[nextcord.Role, str]
) -> nextcord.Role:
    """Convert the name to a nextcord Role
    Arguments:
        - ctx (nextcord.ext.commands.Context): The command's context
        - role_name (str): The name of the role
    Returns:
        - role (nextcord.Role): the role or None if not found"""

    if (isinstance(role_name, nextcord.Role)) or role_name is None:
        return role_name
    for role in ctx.guild.roles:
        if role.name.lower() == role_name.lower():
            return role
    return None


# The bot starts with chunk_guilds_at_startup=False, so a guild's member list can be incomplete
# until it's fetched. chunk_all_guilds() fetches them in the background after on_ready, and
# commands that read guild/role/channel .members call ensure_members_cached() first in case
# that hasn't reached their guild yet.
MEMBER_FETCH_TIMEOUT = 60


async def ensure_members_cached(guild: Optional[nextcord.Guild]) -> bool:
    """Make sure the guild's full member list is cached, fetching it from Discord if needed.

    Arguments:
        - guild (nextcord.Guild): The guild, or None (in DMs)
    Returns:
        - bool: True if the member list is complete, False if fetching failed or timed out
        (the command then carries on with whatever members are cached)."""
    if guild is None or guild.chunked:
        return True
    try:
        await asyncio.wait_for(guild.chunk(), timeout=MEMBER_FETCH_TIMEOUT)
    except (asyncio.TimeoutError, nextcord.ClientException):
        return False
    return True


async def chunk_all_guilds(guilds: List[nextcord.Guild]) -> List[nextcord.Guild]:
    """Fetch the member list of every guild that isn't fully cached yet, one guild at a time.

    Arguments:
        - guilds (List[nextcord.Guild]): The guilds to fetch
    Returns:
        - List[nextcord.Guild]: The guilds whose member list couldn't be fetched"""
    failed = []
    for guild in guilds:
        try:
            if not await ensure_members_cached(guild):
                failed.append(guild)
        except Exception:  # Don't let one guild stop the rest
            failed.append(guild)
    return failed


async def find_user(
    ctx: commands.Context, user_name: Union[nextcord.Member, str]
) -> nextcord.Role:
    """Convert the name to a nextcord Member
    Arguments:
        - ctx (nextcord.ext.commands.Context): The command's context
        - user_name (str): The name of the user
    Returns:
        - user (nextcord.Member): the user or None if not found"""

    if (isinstance(user_name, nextcord.Member)) or user_name is None:
        return user_name
    await ensure_members_cached(ctx.guild)
    guild_users = ctx.guild.members
    for user in guild_users:
        # Not quite sure the difference between user.name and user.display_name, probably waiting on nextcord 3.0 to hash this
        if user.name is not None and user.name.lower() == user_name.lower():
            return user
        if (
            user.display_name is not None
            and user.display_name.lower() == user_name.lower()
        ):
            return user
        if (
            user.global_name is not None
            and user.global_name.lower() == user_name.lower()
        ):
            return user
    return None


########
# PINS #
########


async def pin_message(message: nextcord.Message) -> nextcord.Embed:
    """Pin a message. Catches Forbidden, HTTPSError (too many pins in channel)
    Arguments:
        - message (nextcord.Message): The message to pin
    Return:
        - embed (nextcord.Embed): We create an embed if any issue occurs in pinning.
    """
    # Channels can't have more than 50 pinned messages
    pins = await message.channel.pins()
    if len(pins) >= 50:
        embed = create_embed()
        embed.add_field(
            name="Failed to pin!",
            value="This channel already has max. number of pins (50)!",
        )
        return embed

    try:
        await message.unpin()
        await message.pin()
        async for pinmsg in message.channel.history(limit=5):
            if pinmsg.type == nextcord.MessageType.pins_add:
                await pinmsg.delete()
    except nextcord.Forbidden:
        embed = create_embed()
        embed.add_field(
            name="Failed to pin!",
            value=f"I don't have permissions to pin a message in {message.channel.mention}. Please check "
            "my permissions and try again.",
        )
        return embed
    except nextcord.HTTPException:
        embed = create_embed()
        embed.add_field(
            name="Failed to pin!",
            value="Cannot pin system messages (e.g. **Bot-Be-Named** pinned **a message** to this channel.)",
        )
        return embed

    return None


async def movetoarchive_generic(ctx: commands.Context, archive_name: str):
    embed = create_embed()
    # Handling if mta is called from a thread
    if await is_thread(ctx, ctx.channel):
        embed.add_field(
            name="Success",
            value=f"Archived {ctx.channel.mention} thread",
            inline=False,
        )
        # Send before archiving, as a new message unarchives the thread
        await send_message(ctx, embed)
        # Checking if thread can be archived by the bot
        try:
            await ctx.channel.edit(archived=True)
        except nextcord.Forbidden:
            embed = create_embed()
            embed.add_field(
                name="Failed",
                value="Forbidden! Have you checked if the bot has the required permissions?",
            )
            await send_message(ctx, embed)
        return

    # Otherwise mta is called from a regular channel
    archive_category = None
    candidates = []
    if archive_name is None:
        # Find category with same name + Archive (or select combinations)
        cat_name = ctx.channel.category.name
        while cat_name:
            candidates.append(f"{cat_name} Archive")
            candidates.append(f"Archive: {cat_name}")
            candidates.append(f"{cat_name} archive")
            cat_name, _, _ = cat_name.rpartition(" ")

        for cand in candidates:
            archive_category = await find_category(ctx, cand)
            if archive_category:
                break

    else:
        archive_category = await find_category(ctx, archive_name)

    if archive_category is None:
        if archive_name is None:
            embed.add_field(
                name="Failed",
                value=f"I can't find the archive, so I cannot move {ctx.channel.mention}. "
                "I checked for the following categories: "
                + ", ".join(f"`{c}`" for c in candidates),
                inline=False,
            )
            await send_message(ctx, embed)
            return
        else:
            embed.add_field(
                name="Failed",
                value=f"There is no category named `{archive_name}`, so I cannot move {ctx.channel.mention}.",
                inline=False,
            )
            await send_message(ctx, embed)
            return

    if category_is_full(archive_category):
        embed.add_field(
            name="Failed",
            value=f"`{archive_category.name}` is already full, max limit is 50 channels. Consider renaming"
            f" `{archive_category.name}` and creating a new `{archive_category.name}`.",
            inline=False,
        )
        await send_message(ctx, embed)
        return

    if archive_category == ctx.channel.category:
        embed.add_field(
            name="Failed",
            value=f"Archive category `{archive_category.name}` is the same as current category `{ctx.channel.category.name}`. No need to move channel!",
            inline=False,
        )
        await send_message(ctx, embed)
        return

    try:
        # move channel
        await ctx.channel.edit(category=archive_category)
        await ctx.channel.edit(position=1)
    except nextcord.Forbidden:
        embed.add_field(
            name="Failed",
            value=f"Can you check my permissions? I can't seem to be able to move "
            f"{ctx.channel.mention} to `{archive_category.name}`",
            inline=False,
        )
        await send_message(ctx, embed)
        return

    embed.add_field(
        name="Success",
        value=f"Moved channel {ctx.channel.mention} to `{archive_category.name}`",
        inline=False,
    )
    await send_message(ctx, embed)


async def category_move_to_archive(ctx: commands.Context, archive_name: Optional[str]):
    """Moves the current channel to an archive category, or archives the thread if called from a thread.
    1. Takes the current channel's category name, and splits it into words. Looks for (all words) Archive, then (all but last word) Archive,
    then (all but last two words) Archive etc.

    2. If numbered copies of that category exist (`X Archive 2`, `X Archive 3`...), uses the highest-numbered
    one, even if a lower one has room. An archive named in the command is used as given unless it is full.

    3. Moves the channel there. If that category is full, makes the next one (`X Archive 4` after `X Archive 3`)
    by cloning it, and moves the channel there instead.
    """
    embed = create_embed()

    # Type guard: Ensure we're working with a thread or text channel
    if not isinstance(ctx.channel, (nextcord.Thread, nextcord.TextChannel)):
        embed.add_field(
            name="Failed",
            value="This command can only be used in a guild (server) text channel or thread.",
            inline=False,
        )
        await send_message(ctx, embed)
        return

    # Handling if mta is called from a thread
    if await is_thread(ctx, ctx.channel):
        # Checking if thread can be archived by the bot
        if isinstance(ctx.channel, nextcord.Thread):
            embed.add_field(
                name="Success",
                value=f"Archived {ctx.channel.mention} thread",
                inline=False,
            )
            # Sending a new message unarchives the thread, so we send the success message before archiving it.
            await send_message(ctx, embed)
            try:
                await ctx.channel.edit(archived=True)
            except nextcord.Forbidden:
                embed.add_field(
                    name="Failed",
                    value="Forbidden! Have you checked if the bot has the required permissions?",
                )
                await send_message(ctx, embed)
        return

    # Otherwise mta is called from a regular channel
    archive_category = None
    candidates = []

    # Type guard: must have guild for category operations
    if ctx.guild is None:
        embed.add_field(
            name="Failed",
            value="This command must be used in a guild (server).",
            inline=False,
        )
        await send_message(ctx, embed)
        return

    if archive_name is None:
        # Find category with same name + Archive (or select combinations)
        if ctx.channel.category is None:
            embed.add_field(
                name="Failed",
                value="Channel must be in a category to automatically find archive.",
                inline=False,
            )
            await send_message(ctx, embed)
            return

        cat_name = ctx.channel.category.name
        cat_name_words = cat_name.split(" ")

        for i in range(len(cat_name_words), 0, -1):
            candidate = " ".join(cat_name_words[:i]) + " Archive"
            candidates.append(candidate)

        for cand in candidates:
            archive_category = await find_category(ctx, cand)
            if archive_category:
                break

    else:
        archive_category = await find_category(ctx, archive_name)

    if archive_category is None:
        if archive_name is None:
            embed.add_field(
                name="Failed",
                value=f"I can't find the archive, so I cannot move {ctx.channel.mention}. "
                "I checked for the following categories: "
                + ", ".join(f"`{c}`" for c in candidates),
                inline=False,
            )
            await send_message(ctx, embed)
            return
        else:
            embed.add_field(
                name="Failed",
                value=f"There is no category named `{archive_name}`, so I cannot move {ctx.channel.mention}.",
                inline=False,
            )
            await send_message(ctx, embed)
            return

    # Use the highest-numbered archive (`X Archive 3` over `X Archive 2` over `X Archive`),
    # even if a lower one has room, so a hunt can start a new archive per round.
    # An archive named in the command is used as given unless it is full.
    base_category = archive_category
    numbered = numbered_categories(ctx.guild, base_category)
    if archive_name is None or category_is_full(archive_category):
        archive_category = numbered[-1][1]

    if category_is_full(archive_category):
        # Check if we've hit the maximum category limit (50)
        if len(ctx.guild.categories) >= 50:
            embed.add_field(
                name="Failed",
                value=f"Cannot create new archive category. Server has reached the maximum limit of 50 categories. "
                f"Archive category `{archive_category.name}` is full.",
                inline=False,
            )
            await send_message(ctx, embed)
            return

        clonecat = ctx.bot.get_command("clonecat")
        category_to_make = f"{base_category.name} {numbered[-1][0] + 1}"

        await ctx.invoke(
            clonecat,
            origCatName=archive_category.name,
            targetCatName=category_to_make,
        )
        embed.add_field(
            name="Created new archive category!",
            value=f"Archive category `{archive_category.name}` is full, so created new category `{category_to_make}`!",
            inline=False,
        )
        await send_message(ctx, embed)

        embed = create_embed()  # Reset embed
        archive_category = await find_category(
            ctx, category_to_make
        )  # Change it to the new one!

    # Check if channel is already in the archive category
    if (
        archive_category
        and ctx.channel.category
        and archive_category == ctx.channel.category
    ):
        embed.add_field(
            name="Failed",
            value=f"Archive category `{archive_category.name}` is the same as current category `{ctx.channel.category.name}`. No need to move channel!",
            inline=False,
        )
        await send_message(ctx, embed)
        return

    # Ensure we have a valid archive category
    if archive_category is None:
        embed.add_field(
            name="Failed",
            value="Could not find or create an archive category.",
            inline=False,
        )
        await send_message(ctx, embed)
        return

    try:
        # move channel - ctx.channel is guaranteed to be TextChannel here
        if isinstance(ctx.channel, nextcord.TextChannel):
            await ctx.channel.edit(category=archive_category)
            await ctx.channel.edit(position=1)
    except nextcord.Forbidden:
        embed.add_field(
            name="Failed",
            value=f"Can you check my permissions? I can't seem to be able to move "
            f"{ctx.channel.mention} to `{archive_category.name}`",
            inline=False,
        )
        await send_message(ctx, embed)
        return

    embed.add_field(
        name="Success",
        value=f"Moved channel {ctx.channel.mention} to `{archive_category.name}`",
        inline=False,
    )
    await send_message(ctx, embed)
