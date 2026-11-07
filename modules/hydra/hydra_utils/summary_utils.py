import re
import nextcord
from nextcord.ext import commands
from sqlalchemy.orm import Session
import database
from utils import discord_utils, sheet_utils
from modules.hydra import constants as hydra_constants
from modules.hydra.hydra_utils import hydra_helpers
from modules.hydra.hydra_utils import sheet_utils as hydra_sheet_utils

"""Helper utilities for `~catsummaryhydra` and `~watchcategoryhydra`"""


def get_allowed_roles(guild, channel_id) -> list[nextcord.Role]:
    """Roles granted summaries in this channel, skips deleted roles."""
    with Session(database.DATABASE_ENGINE) as session:
        rows = (
            session.query(database.SummaryGrants).filter_by(channel_id=channel_id).all()
        )
        role_ids = [row.role_id for row in rows]
    return [role for role in map(guild.get_role, role_ids) if role is not None]


async def get_matched_roles(ctx: commands.Context) -> list[nextcord.Role]:
    """Gets the roles for the channel called from the context. Sends an error reply if summaries aren't set up or
    caller does not have the required perms."""
    allowed = get_allowed_roles(ctx.guild, ctx.channel.id)
    if not allowed:
        embed = hydra_helpers.create_failure_embed(
            "Summaries aren't set up in this channel. "
            "Ask an admin to run `~summaryallowhydra @role #channel`."
        )
        await discord_utils.send_message(ctx, embed)
        return []

    matched = [role for role in allowed if role in ctx.author.roles]
    if not matched:
        embed = hydra_helpers.create_failure_embed("You need a role allowed here.")
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


async def get_roles_channels(gspread_client, ctx: commands.Context, role, categories):
    """Finds the puzzle channels in the tethered sheets. Returns found and failed list."""
    channels = [
        channel
        for category in categories
        for channel in category.text_channels
        if channel.overwrites_for(role).view_channel is not False
    ]
    found, failed, _ = await find_channel_rows(gspread_client, ctx, channels)
    return found, failed


async def find_channel_rows(gspread_client, ctx: commands.Context, channels):
    """Finds each channel's row in the tethered Overview sheet. Returns found, failed and missing lists.
    The missing channels either have no sheet tethered or are not on the overview."""
    sheet_channels = {}
    missing = []
    for channel in channels:
        result, _ = sheet_utils.findsheettether(channel.category_id, channel.id)
        if result is None:
            missing.append(channel)
            continue
        sheet_channels.setdefault(result.sheet_link, []).append(channel)

    found = []
    failed = []
    for sheet_link, sheet_channel in sheet_channels.items():
        cells = await hydra_sheet_utils.findchanidcell(
            gspread_client, ctx, sheet_link, [channel.id for channel in sheet_channel]
        )
        if cells is None:
            failed.extend(sheet_channel)
            continue
        for channel, (rownum, _, overview_values) in zip(sheet_channel, cells):
            if rownum is None:
                missing.append(channel)
            else:
                found.append((channel, rownum, overview_values))
    return found, failed, missing
