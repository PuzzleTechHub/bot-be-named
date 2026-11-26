"""Finding the category to move an archived channel back to, for ~unmta and ~unmtahydra."""

import nextcord
import pytest

from modules.discord_channel_management.cog import DiscordChannelManagementCog
from tests.fakes import FakeCategory, FakeChannel, FakeContext, FakeGuild, add_tether
from utils import discord_utils, sheet_utils

SHEET = "https://docs.google.com/spreadsheets/d/hunt"


class MovableChannel(FakeChannel):
    async def edit(self, category):
        self.category.text_channels.remove(self)
        self.category = category
        self.category_id = category.id
        category.text_channels.append(self)


def guild_with(*names):
    categories = [FakeCategory(10 + n, name) for n, name in enumerate(names)]
    return FakeGuild(categories=categories), categories


def archived_ctx(guild, archive):
    channel = MovableChannel(500, "solved-puzzle", archive)
    ctx = FakeContext(guild, channel)
    ctx.prefix = "~"
    return ctx


def fill(category):
    category.channels = [object()] * 50


async def test_archive_name_without_archive_and_number():
    guild, (main, archive) = guild_with("MH21", "MH21 Archive 2")
    assert (
        await sheet_utils.find_unarchive_category(archived_ctx(guild, archive)) is main
    )


@pytest.mark.parametrize(
    "archive_name",
    [
        "MH21 Archive",
        "MH21 Archive 2",
        "MH21 archive",
        "Archive: MH21",
        "archive 2: MH21",
    ],
)
async def test_every_archive_name_mta_uses(archive_name):
    guild, (main, archive) = guild_with("MH21", archive_name)
    assert (
        await sheet_utils.find_unarchive_category(archived_ctx(guild, archive)) is main
    )


@pytest.mark.parametrize(
    "name, base",
    [
        ("MH21 Archive", "MH21"),
        ("MH21 archive 3", "MH21"),
        ("Archive: MH21 Students", "MH21 Students"),
        ("MH21", None),
        ("Archived Puzzles", None),
    ],
)
def test_archive_base_name(name, base):
    assert sheet_utils.archive_base_name(name) == base


async def test_channel_not_in_an_archive_is_not_moved_to_its_own_category():
    guild, (main,) = guild_with("MH21")
    ctx = archived_ctx(guild, main)
    assert await sheet_utils.find_unarchive_category(ctx, command_name="unmta") is None
    message = ctx.sent_embeds[0].fields[0].value
    assert "doesn't look like an archive category" in message
    assert '`~unmta "Category Name"`' in message


async def test_other_archives_are_not_offered():
    guild, (main, _, archive) = guild_with("MH21", "Archive: MH21", "MH21 archive 2")
    assert (
        await sheet_utils.find_unarchive_category(archived_ctx(guild, archive)) is main
    )


async def test_drops_last_words_when_needed():
    guild, (main, archive) = guild_with("MH21", "MH21 Students Archive")
    assert (
        await sheet_utils.find_unarchive_category(archived_ctx(guild, archive)) is main
    )


async def test_tethered_category_wins_over_names():
    guild, (_, archive, tethered) = guild_with("MH21", "MH21 Archive", "Hunt Puzzles")
    add_tether(tethered.id, SHEET)
    ctx = archived_ctx(guild, archive)
    assert await sheet_utils.find_unarchive_category(ctx, "", SHEET) is tethered


async def test_full_categories_are_skipped():
    guild, (main, archive, overflow) = guild_with("MH21", "MH21 Archive", "MH21 Two")
    fill(main)
    assert (
        await sheet_utils.find_unarchive_category(archived_ctx(guild, archive))
        is overflow
    )


async def test_several_matches_lists_them_and_asks():
    guild, (_, _, archive) = guild_with("MH21 A", "MH21 B", "MH21 Archive")
    ctx = archived_ctx(guild, archive)

    assert await sheet_utils.find_unarchive_category(ctx, command_name="unmta") is None

    [embed] = ctx.sent_embeds
    assert '`~unmta "Category Name"`' in embed.fields[0].value
    assert "- MH21 A\n- MH21 B" in embed.fields[0].value


async def test_no_match_says_so():
    guild, (archive,) = guild_with("Old Archive")
    ctx = archived_ctx(guild, archive)
    assert await sheet_utils.find_unarchive_category(ctx) is None
    assert "could not automatically find" in ctx.sent_embeds[0].fields[0].value


@pytest.mark.parametrize("full", [False, True])
async def test_named_category(monkeypatch, full):
    guild, (main, archive) = guild_with("Puzzles", "MH21 Archive")
    if full:
        fill(main)

    async def find_category(ctx, name):
        return main if name == "Puzzles" else None

    monkeypatch.setattr(discord_utils, "find_category", find_category)
    ctx = archived_ctx(guild, archive)

    found = await sheet_utils.find_unarchive_category(ctx, "Puzzles")

    assert found is (None if full else main)
    if full:
        assert "is full" in ctx.sent_embeds[0].fields[0].value


async def test_unknown_named_category(monkeypatch):
    guild, (_, archive) = guild_with("MH21", "MH21 Archive")

    async def find_category(ctx, name):
        return None

    monkeypatch.setattr(discord_utils, "find_category", find_category)
    ctx = archived_ctx(guild, archive)
    assert await sheet_utils.find_unarchive_category(ctx, "Nope") is None
    assert "I cannot find category `Nope`" in ctx.sent_embeds[0].fields[0].value


# ~unmta


async def test_unmta_moves_only_the_channel(monkeypatch):
    monkeypatch.setattr(nextcord, "TextChannel", MovableChannel)
    guild, (main, archive) = guild_with("MH21", "MH21 Archive")
    ctx = archived_ctx(guild, archive)
    cog = DiscordChannelManagementCog(bot=None)

    await cog.unmovetoarchive.callback(cog, ctx)

    assert ctx.channel.category is main
    [embed] = ctx.sent_embeds
    assert embed.fields[0].name == "Success"


async def test_unmta_uses_the_channels_tether(monkeypatch):
    monkeypatch.setattr(nextcord, "TextChannel", MovableChannel)
    guild, (_, archive, tethered) = guild_with("MH21", "MH21 Archive", "Hunt")
    add_tether(tethered.id, SHEET)
    add_tether(archive.id, SHEET)
    ctx = archived_ctx(guild, archive)
    cog = DiscordChannelManagementCog(bot=None)

    await cog.unmovetoarchive.callback(cog, ctx)

    assert ctx.channel.category is tethered
