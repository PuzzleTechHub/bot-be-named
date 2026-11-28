import asyncio
import re

import gspread
import nextcord
from nextcord.ext import commands

import database
from modules.hydra import constants as hydra_constants
from utils import discord_utils, sheet_utils, sheets_constants

"""Helper utilities for `~catsummaryhydra` and `~watchcategoryhydra`"""


def get_allowed_roles(guild, channel_id) -> list[nextcord.Role]:
    """Roles granted summaries in this channel, skips deleted roles."""
    role_ids = database.get_summary_role_ids(channel_id)
    return [role for role in map(guild.get_role, role_ids) if role is not None]


async def get_matched_roles(ctx: commands.Context) -> list[nextcord.Role]:
    """Gets the roles for the channel called from the context. Sends an error reply if summaries aren't set up or
    caller does not have the required perms."""
    allowed = get_allowed_roles(ctx.guild, ctx.channel.id)
    if not allowed:
        embed = discord_utils.create_failure_embed(
            "Summaries aren't set up in this channel. "
            "Ask an admin to run `~summaryallowhydra @role #channel`."
        )
        await discord_utils.send_message(ctx, embed)
        return []

    matched = [role for role in allowed if role in ctx.author.roles]
    if not matched:
        embed = discord_utils.create_failure_embed("You need a role allowed here.")
        await discord_utils.send_message(ctx, embed)
    return matched


def get_role_categories(guild, role) -> list[nextcord.CategoryChannel]:
    """Find categories whose permissions explicitly allow the role passed in to view and is not an archived category."""
    return [
        category
        for category in guild.categories
        if category.overwrites_for(role).view_channel is True
        and not re.search(hydra_constants.ARCHIVE_REGEX_PATTERN, category.name)
    ]


def _role_can_view(channel, role) -> bool:
    """Threads don't have permissions, so it uses that of its parents."""
    target = getattr(channel, "parent", None) or channel
    return target.overwrites_for(role).view_channel is not False


def _is_solved(overview_values, rownum: int) -> bool:
    """Whether the puzzle on this Overview row has a solve status."""
    try:
        status_col = sheet_utils.get_cell_value(
            overview_values, sheets_constants.STATUS_COLUMN_LOCATION
        )
        status = sheet_utils.get_cell_value(overview_values, f"{status_col}{rownum}")
    except gspread.exceptions.IncorrectCellLabel:
        return False
    return sheet_utils.normalize_status(status) in sheets_constants.solve_statuses


async def get_roles_channels(gspread_client, ctx: commands.Context, role, categories):
    """Finds the puzzle channels, threads and forum posts in the tethered sheets. Returns found and failed list.

    Automatically archived threads (inactivity) are kept, but archived threads of solved puzzles
    (~mtahydra) aren't."""
    channels = []
    for category in categories:
        for channel in await discord_utils.get_category_channels(
            category, include_archived=True
        ):
            if _role_can_view(channel, role):
                channels.append(channel)
    found, failed, _ = await find_channel_rows(gspread_client, ctx, channels)
    found = [
        (channel, rownum, overview_values)
        for channel, rownum, overview_values in found
        if not (
            getattr(channel, "archived", False) and _is_solved(overview_values, rownum)
        )
    ]
    return found, failed


async def find_channel_rows(gspread_client, ctx: commands.Context, channels):
    """Finds each channel's row in the tethered Overview sheet. Returns found, failed and missing lists.
    The missing channels either have no sheet tethered or are not on the overview."""
    # One query for every tether, in a worker thread, so the bot keeps answering other
    # commands meanwhile. A channel's own tether wins over its category's, like findsheettether.
    tethers = await asyncio.to_thread(
        database.get_tethers,
        [
            place_id
            for channel in channels
            for place_id in (channel.id, channel.category_id)
        ],
    )
    sheet_channels = {}
    missing = []
    for channel in channels:
        result = tethers.get(channel.id) or tethers.get(channel.category_id)
        if result is None:
            missing.append(channel)
            continue
        sheet_channels.setdefault(result.sheet_link, []).append(channel)

    found = []
    failed = []
    for sheet_link, sheet_channel in sheet_channels.items():
        cells = await sheet_utils.findchanidcell(
            gspread_client, ctx, sheet_link, [channel.id for channel in sheet_channel]
        )
        if cells is None:
            failed.extend(sheet_channel)
            continue
        for channel, (rownum, _, overview_values) in zip(
            sheet_channel, cells, strict=True
        ):
            if rownum is None:
                missing.append(channel)
            else:
                found.append((channel, rownum, overview_values))
    return found, failed, missing
