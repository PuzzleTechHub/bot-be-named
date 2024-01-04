from http.client import FORBIDDEN
import googleapiclient
from modules.sheets import sheets_constants
from utils import discord_utils
import constants
import nextcord
import gspread
import database
from sqlalchemy.sql.expression import insert
from sqlalchemy.orm import Session
from typing import Union
import emoji
import itertools

#########################
# SHEET UTILS FUNCTIONS #
#########################

def open_by_url_or_key(
    gspread_client, sheet_key_or_link: str
) -> gspread.Spreadsheet:
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
    #something else happened:
    return None

def set_sheet_generic(
    sheet_url: str,
    guild: nextcord.Guild,
    what: Union[nextcord.CategoryChannel, nextcord.TextChannel, nextcord.Guild],
):
    """Add a sheet url to the given object (what). The url is not validated"""
    
    # If the channel already has a sheet, then we update it.
    # Otherwise, we add the channel to our master sheet to establish the tether

    with Session(database.DATABASE_ENGINE) as session:
        result = (
            session.query(database.SheetTethers)
            .filter_by(channel_or_cat_id=what.id)
            .first()
        )
        # If there is already an entry, we just need to update it.
        if result is not None:
            result.sheet_link = sheet_url
        # Otherwise, we need to create an entry
        else:
            stmt = insert(database.SheetTethers).values(
                server_id=guild.id,
                server_name=guild.name,
                channel_or_cat_name=what.name,
                channel_or_cat_id=what.id,
                sheet_link=sheet_url,
            )
            session.execute(stmt)
        # Commits change
        session.commit()

def get_sheet(search_ids : list[int]):
    """For finding the appropriate sheet tethering for a given category or channel
        The ids are given in search order
    returns (sheet, id_index) if an id was in the database
    otherwise returns (None,None)
    """
    
    #TODO: a better way would be to use an address scheme and prefix searches
    #      e.g. store <guild_id>/<category_id>/<channel_id>/... as the key in the database
    # then do a longest-prefix search e.g. https://www.richard-towers.com/2023/01/29/finding-the-longest-matching-prefix-in-sql.html

    # Search DB for the sheet tether, if there is one
    with Session(database.DATABASE_ENGINE) as session:
        for curr_id, curr_index in enumerate(search_ids):
            #TODO: does the id need to be converted to str?
            result = session.query(database.SheetTethers).filter_by(channel_or_cat_id=str(curr_id)).first()
            if result is not None:
                return result, curr_index

    return None,None

def unset_sheet(category_id : int, channel_id : int, thread_id : int = None):
    """Remove the sheet tethered to a given channel or category"""
    #search order: thread, channel, category
    ids = [thread_id, channel_id, category_id]
    types = [sheets_constants.THREAD, sheets_constants.CHANNEL, sheets_constants.CATEGORY]
    tether_type = None
    sheet_url = None
    with Session(database.DATABASE_ENGINE) as session:
        for curr_id, curr_type in zip(ids, types):
            result = session.query(database.SheetTethers).filter_by(channel_or_cat_id=str(curr_id)).first()
            if result is not None:
                tether_type = curr_type
                sheet_url = result.sheet_link
                result.delete()
                session.commit()
                break
    return sheet_url, tether_type

def prune_sheets(guilds):
    """remove unused tether database rows """
        guilds_by_id = {guild.id:guild for guild in guilds}
        active_ids_by_guild_id = {}

        pruned = []
        unknown_guilds = set()
        with Session(database.DATABASE_ENGINE) as session:
            
            for row in session.query(database.SheetTethers):
                #skip sheets associated with the server directly
                if row.server_id == row.channel_or_cat_id:
                    continue

                #get the ids of categories, channels, and threads in the given guilds
                active_ids = active_ids_by_guild_id.get(row.server_id, default=None)
                if active_ids is None:
                    guild = guilds_by_id.get(row.server_id, default=None)
                    if guild is None:
                        #skip rows with unknown server_id
                        unknown_guilds.add((row.server_id, row.server_name))
                        continue
                    active_ids = set(x.id for x in itertools.chain(guild.categories, guild.channels, guild.threads))
                    active_ids_by_guild_id[row.server_id] = active_ids

                #check if the server still has the associated channel
                if row.channel_or_cat_id not in active_ids:
                    #TODO: where does this print?!
                    pruned.append((row.server_id, row.server_name, row.channel_or_cat_id, row.channel_or_cat_name, row.sheet_link))
                    print(f'Deleting tether: {pruned[-1]}')                    
                    row.delete()
            session.commit()
        if unknown_guilds:
            #TODO: where does this print?!
            print(f'Unknown guilds in database: {unknown_guilds}')
        return pruned

async def sheetcrabgeneric(gspread_client, ctx, tab_name: str, to_pin: str = ""):
    embed = discord_utils.create_embed()

    curr_chan = ctx.message.channel
    curr_cat = ctx.message.channel.category
    curr_sheet_link, newsheet = await sheetcreatetabgeneric(
        gspread_client, ctx, curr_chan, curr_cat, tab_name, "Template"
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
            await msg.add_reaction(emoji.emojize(":pushpin:"))

    return curr_sheet_link, newsheet


async def chancrabgeneric(
    gspread_client, ctx, chan_name: str, chan_or_thread: str, is_meta: bool, text_to_pin
):
    embed = discord_utils.create_embed()
    # Cannot make a new channel if the category is full``
    if chan_or_thread == "chan":
        if discord_utils.category_is_full(ctx.channel.category):
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Category `{ctx.channel.category.name}` is already full, max limit is 50 channels.",
            )
            # reply to user
            await ctx.send(embed=embed)
            return None, None, None
        if discord_utils.server_is_full(ctx.channel.guild):
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Guild `{ctx.channel.guild.name}` is completely full! Max limit is 500 channels/categories/... Please contact a mod for help.",
            )
            # reply to user
            await ctx.send(embed=embed)
            return None, None, None

    if is_meta:
        tab_type = "Meta Template"
    else:
        tab_type = "Template"

    tab_name = chan_name.replace("#", "").replace("-", " ")

    if chan_or_thread == "thread" and await discord_utils.is_thread(ctx, ctx.channel):
        embed.add_field(
            name=f"{constants.FAILED}!",
            value=f"Invalid! You cannot make a thread from inside another thread!",
        )
        await ctx.send(embed=embed)
        return None, None, None

    curr_sheet_link, newsheet = await sheetcreatetabgeneric(
        gspread_client, ctx, ctx.channel, ctx.channel.category, tab_name, tab_type
    )

    # Error, already being handled at the generic function
    if not curr_sheet_link or not newsheet or not newsheet.id:
        return None, None, None

    # This link is customized for the newly made tab
    final_sheet_link = curr_sheet_link + "/edit#gid=" + str(newsheet.id)

    # new channel created (or None)
    if chan_or_thread == "chan":
        new_chan = await discord_utils.createchannelgeneric(
            ctx.guild, ctx.channel.category, chan_name
        )
    elif chan_or_thread == "thread":
        new_chan = await discord_utils.createthreadgeneric(
            ctx, ctx.message, ctx.channel, chan_name
        )

    # Error creating channel
    if not new_chan:
        embed.add_field(
            name=f"{constants.FAILED}!",
            value=f"Forbidden! Have you checked if the bot has the required permisisons?",
        )
        await ctx.send(embed=embed)
        return None, None, None

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

    if text_to_pin != "":
        embed = discord_utils.create_embed()
        embed.description = text_to_pin
        msg = await new_chan.send(embed=embed)
        # Pin message in the new channel
        embed_or_none = await discord_utils.pin_message(msg)

        # Error pinning message
        if embed_or_none is not None:
            await ctx.send(embed=embed_or_none)
        else:
            await msg.add_reaction(emoji.emojize(":pushpin:"))

    if chan_or_thread == "chan":
        await new_chan.edit(topic=f"Tab Link - {final_sheet_link}")

    embed = discord_utils.create_embed()
    embed.add_field(
        name=f"{constants.SUCCESS}!",
        value=f"Channel `{chan_name}` created as {new_chan.mention}, posts pinned!",
        inline=False,
    )
    await ctx.send(embed=embed)

    set_sheet_generic(gspread_client, curr_sheet_link, ctx.message.guild, new_chan)
    return curr_sheet_link, newsheet, new_chan


async def sheetcreatetabgeneric(
    gspread_client, ctx, curr_chan, curr_cat, tab_name, template_or_meta
):
    """Actually creates the sheet and handles errors"""
    embed = discord_utils.create_embed()
    curr_sheet_link = None
    newsheet = None

    tether_db_result, id_index = get_sheet((curr_chan.id, curr_cat.id))
    
    try:
        if tether_db_result is not None:
            tether_type = (sheets_constants.CHANNEL, sheets_constants.CATEGORY)[id_index]
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

        # Make sure the template/metatemplate tab exists on the sheet.
        template_index = 0
        try:
            curr_sheet = gspread_client.open_by_url(curr_sheet_link)
            template_id = curr_sheet.worksheet(template_or_meta).id
            template_index = curr_sheet.worksheet(template_or_meta).index
        # Error when we can't open the curr sheet link
        except gspread.exceptions.APIError as e:
            error_json = e.response.json()
            error_status = error_json.get("error", {}).get("status")
            if error_status == "PERMISSION_DENIED":
                embed = discord_utils.create_embed()
                embed.add_field(
                    name=f"{constants.FAILED}",
                    value=f"I'm unable to open the tethered [sheet]({curr_sheet_link}). "
                    f"Did the permissions change?",
                    inline=False,
                )
                await ctx.send(embed=embed)
                return curr_sheet_link, newsheet
            else:
                raise e
        # Error when the sheet has no template tab
        except gspread.exceptions.WorksheetNotFound:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"The [sheet]({curr_sheet_link}) has no tab named '{template_or_meta}'. "
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

        # Try to duplicate the template/meta tab and rename it to the given name
        try:
            # Index of template+2 (for template) and template+1 (for meta) is hardcoded for The Mathemagicians server
            if template_or_meta == "Template":
                i = 2
            else:
                i = 1

            newsheet = curr_sheet.duplicate_sheet(
                source_sheet_id=template_id,
                new_sheet_name=tab_name,
                insert_sheet_index=template_index + i,
            )
        except gspread.exceptions.APIError as e:
            error_json = e.response.json()
            error_status = error_json.get("error", {}).get("status")
            if error_status == "PERMISSION_DENIED":
                embed = discord_utils.create_embed()
                embed.add_field(
                    name=f"{constants.FAILED}",
                    value=f"Could not duplicate '{template_or_meta}' tab in the "
                    f"[Google sheet at link]({curr_sheet_link}). "
                    f"Is the permission set up with 'Anyone with link can edit'?",
                    inline=False,
                )
                await ctx.send(embed=embed)
                return curr_sheet_link, None
            else:
                raise e
        return curr_sheet_link, newsheet

    except gspread.exceptions.APIError as e:
        if hasattr(e, "response"):
            error_json = e.response.json()
            error_message = error_json.get("error", {}).get("message")
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"Unknown GSheets API Error - `{error_message}`",
                inline=False,
            )
            await ctx.send(embed=embed)
            return
