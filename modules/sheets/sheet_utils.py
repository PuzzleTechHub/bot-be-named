from http.client import FORBIDDEN
from discord import Forbidden
import googleapiclient
from modules.sheets import sheets_constants, sheet_utils
from utils import discord_utils
import constants
from nextcord.ext import commands
import nextcord
import gspread
from googleapiclient import discovery
import database
from sqlalchemy.sql.expression import insert
from sqlalchemy.orm import Session
from typing import Union
from emoji import EMOJI_ALIAS_UNICODE_ENGLISH as EMOJIS

    #########################
    # SHEET UTILS FUNCTIONS #
    #########################

def addsheettethergeneric(
    gspread_client,
    sheet_key_or_link: str,
    curr_guild: nextcord.Guild,
    curr_catorchan: Union[nextcord.CategoryChannel, nextcord.TextChannel],
) -> gspread.Spreadsheet:
    """Add a sheet to the current channel"""
    # We accept both sheet keys or full links
    proposed_sheet = get_sheet_from_key_or_link(gspread_client,sheet_key_or_link)

    # If we can't open the sheet, send an error and return
    if not proposed_sheet:
        return None

    # If the channel already has a sheet, then we update it.
    # Otherwise, we add the channel to our master sheet to establish the tether

    with Session(database.DATABASE_ENGINE) as session:
        result = (
            session.query(database.SheetTethers)
            .filter_by(channel_or_cat_id=curr_catorchan.id)
            .first()
        )
        # If there is already an entry, we just need to update it.
        if result is not None:
            result.sheet_link = proposed_sheet.url
        # Otherwise, we need to create an entry
        else:
            stmt = insert(database.SheetTethers).values(
                server_id=curr_guild.id,
                server_name=curr_guild.name,
                channel_or_cat_name=curr_catorchan.name,
                channel_or_cat_id=curr_catorchan.id,
                sheet_link=proposed_sheet.url,
            )
            session.execute(stmt)
        # Commits change
        session.commit()
    return proposed_sheet

async def sheetcrabgeneric(gspread_client,ctx, tab_name: str, to_pin: str = ""):
    embed = discord_utils.create_embed()

    curr_chan = ctx.message.channel
    curr_cat = ctx.message.channel.category
    curr_sheet_link, newsheet = await sheet_utils.sheetcreatetabgeneric(
        gspread_client, ctx, curr_chan, curr_cat, tab_name
    )

    pin_flag = False
    if to_pin.lower()[0:3] == "pin":
        pin_flag = True

    # Error, already being handled at the generic function
    if not curr_sheet_link or newsheet is None:
        return

    # This link is customized for the newly made tab
    final_sheet_link = curr_sheet_link + "/edit#gid=" + str(newsheet.id)

    embed.add_field(
        name=f"{constants.SUCCESS}!",
        value=f"Tab **{tab_name}** has been created at [Tab link]({final_sheet_link}).",
        inline=False,
    )
    msg = await ctx.send(embed=embed)

    # Pin message to the new channel
    if pin_flag:
        embed_or_none = await discord_utils.pin_message(msg)
        if embed_or_none is not None:
            await ctx.send(embed=embed_or_none)
        else:
            await msg.add_reaction(EMOJIS[":pushpin:"])

    return curr_sheet_link, newsheet


async def chancrabgeneric(gspread_client,ctx,chan_name: str, *args):
    embed = discord_utils.create_embed()
    # Cannot make a new channel if the category is full
    if discord_utils.category_is_full(ctx.channel.category):
        embed.add_field(
            name=f"{constants.FAILED}!",
            value=f"Category `{ctx.channel.category.name}` is already full, max limit is 50 channels.",
        )
        # reply to user
        await ctx.send(embed=embed)
        return None,None,None

    text_to_pin = " ".join(args)
    tab_name = chan_name.replace("#", "").replace("-", " ")

    curr_sheet_link, newsheet = await sheet_utils.sheetcreatetabgeneric(
        gspread_client, ctx, ctx.channel, ctx.channel.category, tab_name
    )

    # Error, already being handled at the generic function
    if not curr_sheet_link or not newsheet or not newsheet.id:
        return None,None,None

    # This link is customized for the newly made tab
    final_sheet_link = curr_sheet_link + "/edit#gid=" + str(newsheet.id)

    # new channel created (or None)
    new_chan = await discord_utils.createchannelgeneric(
        ctx.guild, ctx.channel.category, chan_name
    )
    # Error creating channel
    if not new_chan:
        embed = discord_utils.create_embed()
        embed.add_field(
            name=f"{constants.FAILED}!",
            value=f"Forbidden! Have you checked if the bot has the required permisisons?",
        )
        await ctx.send(embed=embed)
        return None,None,None

    embed = discord_utils.create_embed()
    embed.add_field(
        name=f"{constants.SUCCESS}!",
        value=f"Tab **{tab_name}** has been created at [Tab link]({final_sheet_link}).",
        inline=False,
    )

    msg = None
    try:
        msg = await new_chan.send(embed=embed)
    except nextcord.Forbidden:
        embed.add_field(
        name=f"{constants.FAILED}!",
        value=f"Cannot send messages in `{chan_name}`!",
        inline=False,
        )
        await ctx.send(embed=embed)
        return None, None, new_chan

    
    # Try to pin the message in new channel
    embed_or_none = await discord_utils.pin_message(msg)
    # Error pinning message
    if embed_or_none is not None:
        await new_chan.send(embed=embed_or_none)

    if text_to_pin:
        embed = discord_utils.create_embed()
        embed.description = text_to_pin
        msg = await new_chan.send(embed=embed)
        # Pin message in the new channel
        embed_or_none = await discord_utils.pin_message(msg)

        # Error pinning message
        if embed_or_none is not None:
            await ctx.send(embed=embed_or_none)
        else:
            await msg.add_reaction(EMOJIS[":pushpin:"])

    embed = discord_utils.create_embed()
    embed.add_field(
        name=f"{constants.SUCCESS}!",
        value=f"Channel `{chan_name}` created as {new_chan.mention}, posts pinned!",
        inline=False,
    )
    await ctx.send(embed=embed)
    return curr_sheet_link, newsheet, new_chan


def findsheettether(
    curr_cat_id: int, curr_chan_id: int, curr_thread_id: int = None
):
    """For finding the appropriate sheet tethering for a given category or channel"""
    result = None
    tether_type = None
    # Search DB for the sheet tether, if there is one
    with Session(database.DATABASE_ENGINE) as session:
        # Search for channel's tether
        result = (
            session.query(database.SheetTethers)
            .filter_by(channel_or_cat_id=curr_thread_id)
            .first()
        )
        if result is not None:
            tether_type = sheets_constants.THREAD
        else:
            result = (
                session.query(database.SheetTethers)
                .filter_by(channel_or_cat_id=curr_chan_id)
                .first()
            )
            # If we miss on the channel ID, try the category ID
            if result is not None:
                tether_type = sheets_constants.CHANNEL
            else:
                result = (
                    session.query(database.SheetTethers)
                    .filter_by(channel_or_cat_id=curr_cat_id)
                    .first()
                )
                tether_type = sheets_constants.CATEGORY
    return result, tether_type

def get_sheet_from_key_or_link(gspread_client,sheet_key_or_link: str) -> gspread.Spreadsheet:
    """Takes in a string, which could be a google sheet key or URL"""
    # Assume the str is a URL
    try:
        sheet = gspread_client.open_by_url(sheet_key_or_link)
        return sheet
    except gspread.exceptions.APIError:
        return None
    # Given str was not a link
    except gspread.exceptions.NoValidUrlKeyFound:
        pass
    # Assume the str is a sheet key
    try:
        sheet = gspread_client.open_by_key(sheet_key_or_link)
        return sheet
    # Entity Not Found
    except gspread.exceptions.APIError:
        return None

async def sheetcreatetabgeneric(gspread_client, ctx, curr_chan, curr_cat, tab_name):
    """Actually creates the sheet and handles errors"""
    embed = discord_utils.create_embed()
    curr_sheet_link = None
    newsheet = None

    tether_db_result, tether_type = findsheettether(
        str(curr_cat.id), str(curr_chan.id)
    )

    if tether_db_result is not None:
        curr_sheet_link = tether_db_result.sheet_link
    else:
        embed = discord_utils.create_embed()
        embed.add_field(
            name=f"{constants.FAILED}",
            value=f"The category **{curr_cat.name}** nor the channel **{curr_chan.name}** are not "
            f"tethered to any Google sheet.",
            inline=False,
        )
        await ctx.send(embed=embed)
        return curr_sheet_link, newsheet

    # Make sure the template tab exists on the sheet.
    template_index = 0
    try:
        curr_sheet = gspread_client.open_by_url(curr_sheet_link)
        template_id = curr_sheet.worksheet("Template").id
        template_index = curr_sheet.worksheet("Template").index
    # Error when we can't open the curr sheet link
    except gspread.exceptions.APIError:
        embed = discord_utils.create_embed()
        embed.add_field(
            name=f"{constants.FAILED}",
            value=f"I'm unable to open the tethered [sheet]({curr_sheet_link}). "
            f"Did the permissions change?",
            inline=False,
        )
        await ctx.send(embed=embed)
        return curr_sheet_link, newsheet
    # Error when the sheet has no template tab
    except gspread.exceptions.WorksheetNotFound:
        embed = discord_utils.create_embed()
        embed.add_field(
            name=f"{constants.FAILED}",
            value=f"The [sheet]({curr_sheet_link}) has no tab named 'Template'. "
            f"Did you forget to add one?",
            inline=False,
        )
        await ctx.send(embed=embed)
        return curr_sheet_link, newsheet
    # Make sure tab_name does not exist
    try:
        curr_sheet.worksheet(tab_name)
        # If there is a tab with the given name, that's an error!
        embed = discord_utils.create_embed()
        embed.add_field(
            name=f"{constants.FAILED}",
            value=f"The [Google sheet at link]({curr_sheet_link}) already has a tab named "
            f"**{tab_name}**. Cannot create a tab with same name.",
            inline=False,
        )
        await ctx.send(embed=embed)
        return curr_sheet_link, newsheet
    except gspread.exceptions.WorksheetNotFound:
        # If the tab isn't found, that's good! We will create one.
        pass

    # Try to duplicate the template tab and rename it to the given name
    try:
        # Index of template+2 is hardcoded for Team Arithmancy server
        newsheet = curr_sheet.duplicate_sheet(
            source_sheet_id=template_id,
            new_sheet_name=tab_name,
            insert_sheet_index=template_index + 2,
        )
    except gspread.exceptions.APIError:
        embed = discord_utils.create_embed()
        embed.add_field(
            name=f"{constants.FAILED}",
            value=f"Could not duplicate 'Template' tab in the "
            f"[Google sheet at link]({curr_sheet_link}). "
            f"Is the permission set up with 'Anyone with link can edit'?",
            inline=False,
        )
        await ctx.send(embed=embed)
        return curr_sheet_link, None

    return curr_sheet_link, newsheet

async def sheetcreatetabmeta(gspread_client, ctx, curr_chan, curr_cat, tab_name):
    """Actually creates the meta sheet and handles errors"""
    embed = discord_utils.create_embed()
    curr_sheet_link = None
    newsheet = None

    tether_db_result, tether_type = findsheettether(
        str(curr_cat.id), str(curr_chan.id)
    )

    if tether_db_result is not None:
        curr_sheet_link = tether_db_result.sheet_link
    else:
        embed = discord_utils.create_embed()
        embed.add_field(
            name=f"{constants.FAILED}",
            value=f"The category **{curr_cat.name}** nor the channel **{curr_chan.name}** are not "
            f"tethered to any Google sheet.",
            inline=False,
        )
        await ctx.send(embed=embed)
        return curr_sheet_link, newsheet

    # Make sure the template tab exists on the sheet.
    try:
        curr_sheet = gspread_client.open_by_url(curr_sheet_link)
        template_id = curr_sheet.worksheet("Meta Template").id
        template_index = curr_sheet.worksheet("Meta Template").index
    # Error when we can't open the curr sheet link
    except gspread.exceptions.APIError:
        embed = discord_utils.create_embed()
        embed.add_field(
            name=f"{constants.FAILED}",
            value=f"I'm unable to open the tethered [sheet]({curr_sheet_link}). "
            f"Did the permissions change?",
            inline=False,
        )
        await ctx.send(embed=embed)
        return curr_sheet_link, newsheet
    # Error when the sheet has no template tab
    except gspread.exceptions.WorksheetNotFound:
        embed = discord_utils.create_embed()
        embed.add_field(
            name=f"{constants.FAILED}",
            value=f"The [sheet]({curr_sheet_link}) has no tab named 'Meta Template'. "
            f"Did you forget to add one?",
            inline=False,
        )
        await ctx.send(embed=embed)
        return curr_sheet_link, newsheet
    # Make sure tab_name does not exist
    try:
        curr_sheet.worksheet(tab_name)
        # If there is a tab with the given name, that's an error!
        embed = discord_utils.create_embed()
        embed.add_field(
            name=f"{constants.FAILED}",
            value=f"The [Google sheet at link]({curr_sheet_link}) already has a tab named "
            f"**{tab_name}**. Cannot create a tab with same name.",
            inline=False,
        )
        await ctx.send(embed=embed)
        return curr_sheet_link, newsheet
    except gspread.exceptions.WorksheetNotFound:
        # If the tab isn't found, that's good! We will create one.
        pass

    # Try to duplicate the template tab and rename it to the given name
    try:
        # Index of 4 is hardcoded for Team Arithmancy server
        newsheet = curr_sheet.duplicate_sheet(
            source_sheet_id=template_id,
            new_sheet_name=tab_name,
            insert_sheet_index=template_index + 1,
        )
    except gspread.exceptions.APIError:
        embed = discord_utils.create_embed()
        embed.add_field(
            name=f"{constants.FAILED}",
            value=f"Could not duplicate 'Meta Template' tab in the "
            f"[Google sheet at link]({curr_sheet_link}). "
            f"Is the permission set up with 'Anyone with link can edit'?",
            inline=False,
        )
        await ctx.send(embed=embed)
        return curr_sheet_link, None

    return curr_sheet_link, newsheet
