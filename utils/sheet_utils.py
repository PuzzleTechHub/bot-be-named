from utils import sheets_constants
from utils import discord_utils
from utils import batch_update_utils
import nextcord
import gspread
from gspread.worksheet import Worksheet
import database
from sqlalchemy.sql.expression import insert
from sqlalchemy.orm import Session
from typing import Optional, Union
import emoji

from datetime import datetime, timezone
from nextcord.ext import commands

"""
Sheets utils. Useful for any commands that require Google Sheets.
Contains deduplicated code and logic from multiple commands/modules then generic helper functions.
Used in any modules that uses sheets (sheets, lion, hydra...)
"""

#########################
# SHEET UTILS FUNCTIONS #
#########################


async def handle_gspread_error(
    ctx: commands.Context, e: gspread.exceptions.APIError, embed=None
):
    """Centralized handler for gspread API errors."""
    if embed is None:
        embed = discord_utils.create_embed()

    error_json = e.response.json()
    error_status = error_json.get("error", {}).get("status")
    error_message = error_json.get("error", {}).get("message", "")

    if (
        error_status == "BAD_REQUEST"
        and "columnIndex" in error_message
        and "is after last column" in error_message
    ):
        embed.add_field(
            name="Failed",
            value="Invalid Template!\n\n"
            f"The worksheet provided is missing required columns. \n"
            f"Visit the [BBN Server](discord.gg/x8f2ywHUky) to get the correct template. \n\n"
            f"Error: `{error_message}`",
            inline=False,
        )
    elif error_status == "PERMISSION_DENIED":
        embed.add_field(
            name="Failed",
            value="Could not update the Google Sheet because permission was denied.",
            inline=False,
        )
    else:
        embed.add_field(
            name="Failed",
            value=f"Unknown GSheets API Error - `{error_message}`",
            inline=False,
        )
    await discord_utils.send_message(ctx, embed)
    return embed


def addsheettethergeneric(
    gspread_client,
    sheet_key_or_link: str,
    curr_guild: nextcord.Guild,
    curr_catorchan: Union[nextcord.CategoryChannel, nextcord.TextChannel],
) -> gspread.Spreadsheet:
    """Add a sheet to the current channel"""
    # We accept both sheet keys or full links
    proposed_sheet = get_sheet_from_key_or_link(gspread_client, sheet_key_or_link)

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


async def sheetcrabgeneric(
    gspread_client,
    ctx: commands.Context,
    tab_name: str,
    is_meta: bool,
    to_pin: str = "",
):
    embed = discord_utils.create_embed()

    curr_chan = ctx.message.channel
    curr_cat = ctx.message.channel.category

    if is_meta:
        tab_type = "Meta Template"
    else:
        tab_type = "Template"

    curr_sheet_link, newsheet = await sheetcreatetabgeneric(
        gspread_client, ctx, curr_chan, curr_cat, tab_name, tab_type
    )

    pin_flag = False
    if to_pin.lower()[0:3] == "pin":
        pin_flag = True

    # Error, already being handled at the generic function
    if not curr_sheet_link or newsheet is None:
        return

    # This link is customized for the newly made tab
    final_sheet_link = curr_sheet_link + "/edit#gid=" + str(newsheet.id)

    # get spreadsheet title for nicer embed

    embed.add_field(
        name="Success",
        value=f"Tab **{tab_name}** has been created at [{newsheet.spreadsheet.title}]({final_sheet_link}) spreadsheet.",
        inline=False,
    )
    msgs = await discord_utils.send_message(ctx, embed)
    msg = msgs[0]

    # Pin message to the new channel
    if pin_flag:
        embed_or_none = await discord_utils.pin_message(msg)
        if embed_or_none is not None:
            await discord_utils.send_message(ctx, embed_or_none)
        else:
            await msg.add_reaction(emoji.emojize(":pushpin:"))

    return curr_sheet_link, newsheet


async def chancrabgeneric(
    gspread_client,
    ctx: commands.Context,
    chan_name: str,
    chan_type: str,
    is_meta: bool,
    text_to_pin: str = "",
):
    embed = discord_utils.create_embed()
    tab_name = chan_name.replace("#", "").replace("-", " ")

    # Cannot make a new channel if the category is full``
    if chan_type == "chan":
        if discord_utils.category_is_full(ctx.channel.category):
            embed.add_field(
                name="Failed",
                value=f"Category `{ctx.channel.category.name}` is already full, max limit is 50 channels.",
            )
            # reply to user
            await discord_utils.send_message(ctx, embed)
            return None, None, None
        if discord_utils.server_is_full(ctx.channel.guild):
            embed.add_field(
                name="Failed",
                value=f"Guild `{ctx.channel.guild.name}` is completely full! Max limit is 500 channels/categories/... Please contact a mod for help.",
            )
            # reply to user
            await discord_utils.send_message(ctx, embed)
            return None, None, None

    if is_meta:
        tab_type = "Meta Template"
    else:
        tab_type = "Template"

    if chan_type == "thread" and await discord_utils.is_thread(ctx, ctx.channel):
        embed.add_field(
            name="Failed",
            value="Invalid! You cannot make a thread from inside another thread!",
        )
        await discord_utils.send_message(ctx, embed)
        return None, None, None

    # Creates the new sheet
    curr_sheet_link, newsheet = await sheetcreatetabgeneric(
        gspread_client, ctx, ctx.channel, ctx.channel.category, tab_name, tab_type
    )

    # Error, already being handled at the generic function
    if not curr_sheet_link or not newsheet or not newsheet.id:
        return None, None, None

    # This link is customized for the newly made tab
    final_sheet_link = curr_sheet_link + "/edit#gid=" + str(newsheet.id)

    # new channel created (or None)
    if chan_type == "chan":
        new_chan = await discord_utils.createchannelgeneric(
            ctx.guild, ctx.channel.category, chan_name
        )
    elif chan_type == "thread":
        new_chan = await discord_utils.createthreadgeneric(
            ctx, ctx.message, ctx.channel, chan_name
        )
    elif chan_type == "forum":
        new_chan = await discord_utils.createforumthreadgeneric(
            ctx, ctx.channel, chan_name, f"Tab Link - {final_sheet_link}"
        )

    # Error creating channel
    if not new_chan:
        embed.add_field(
            name="Failed",
            value="Forbidden! Have you checked if the bot has the required permissions?",
        )
        await discord_utils.send_message(ctx, embed)
        return None, None, None

    embed = discord_utils.create_embed()

    # get spreadsheet title for nicer embed

    embed.add_field(
        name="Success",
        value=f"Tab **{tab_name}** has been created at [{newsheet.spreadsheet.title}]({final_sheet_link}) spreadsheet.",
        inline=False,
    )

    msg = None
    try:
        msg = await new_chan.send(embed=embed)
    except nextcord.Forbidden:
        embed.add_field(
            name="Failed",
            value=f"Cannot send messages in `{chan_name}`!",
            inline=False,
        )
        await discord_utils.send_message(ctx, embed)
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
            await discord_utils.send_message(ctx, embed_or_none)
        else:
            await msg.add_reaction(emoji.emojize(":pushpin:"))

    if chan_type == "chan":
        await new_chan.edit(topic=f"Tab Link - {final_sheet_link}")

    embed = discord_utils.create_embed()
    embed.add_field(
        name="Success",
        value=f"Channel `{chan_name}` created as {new_chan.mention}, posts pinned!",
        inline=False,
    )
    await discord_utils.send_message(ctx, embed)

    addsheettethergeneric(gspread_client, curr_sheet_link, ctx.message.guild, new_chan)
    return curr_sheet_link, newsheet, new_chan


def normalize_status(status: str) -> str:
    """Matches the input to a known status, regardless of case. e.g., "in progress" -> "In Progress"
    Custom statuses return unchanged"""
    for recognized_status in sheets_constants.status_dict:
        if status.lower() == recognized_status.lower():
            return recognized_status
    return status


def get_timestamp() -> str:
    """Finds the current UTC timestamp."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def findsheettether(
    curr_cat_id: int, curr_chan_id: int, curr_thread_id: Optional[int] = None
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


def get_sheet_from_key_or_link(
    gspread_client, sheet_key_or_link: str
) -> gspread.Spreadsheet:
    """Takes in a string, which could be a google sheet key or URL"""
    # Assume the str is a URL
    try:
        sheet = gspread_client.open_by_url(sheet_key_or_link)
        return sheet
    except (
        gspread.exceptions.APIError,
        gspread.exceptions.SpreadsheetNotFound,
        PermissionError,
    ):
        return None
    # Given str was not a link
    except gspread.exceptions.NoValidUrlKeyFound:
        pass
    # Assume the str is a sheet key
    try:
        sheet = gspread_client.open_by_key(sheet_key_or_link)
        return sheet
    # Entity Not Found
    except (
        gspread.exceptions.APIError,
        gspread.exceptions.SpreadsheetNotFound,
        PermissionError,
    ):
        return None


def get_new_puzzle_tab_index(worksheets: list[gspread.Worksheet]) -> int:
    """Searches for the first run of tabs ending with Template, then returns the index of
    the tab right after. If no template, returns the last tab."""
    insert_index = len(worksheets)
    found_template = False
    for ws in worksheets:
        if ws.title.endswith("Template"):
            insert_index = ws.index + 1
            found_template = True
        elif found_template:
            break
    return insert_index


async def sheetcreatetabgeneric(
    gspread_client,
    ctx: commands.Context,
    curr_chan,
    curr_cat,
    tab_name,
    template_or_meta,
):
    """Actually creates the sheet and handles errors"""
    embed = discord_utils.create_embed()
    curr_sheet_link = None
    newsheet = None

    tether_db_result, tether_type = findsheettether(curr_cat.id, curr_chan.id)

    try:
        if tether_db_result is not None:
            curr_sheet_link = tether_db_result.sheet_link
        else:
            embed = discord_utils.create_embed()
            embed.add_field(
                name="Failed",
                value=f"The category **{curr_cat.name}** nor the channel **{curr_chan.name}** are not "
                f"tethered to any Google sheet.",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return curr_sheet_link, newsheet

        # Make sure the template/metatemplate tab exists on the sheet.
        try:
            curr_sheet = gspread_client.open_by_url(curr_sheet_link)
            template_id = curr_sheet.worksheet(template_or_meta).id
        # Error when we can't open the curr sheet link
        except gspread.exceptions.APIError as e:
            error_json = e.response.json()
            error_status = error_json.get("error", {}).get("status")
            if error_status == "PERMISSION_DENIED":
                embed = discord_utils.create_embed()
                embed.add_field(
                    name="Failed",
                    value=f"I'm unable to open the tethered [sheet]({curr_sheet_link}). "
                    f"Did the permissions change?",
                    inline=False,
                )
                await discord_utils.send_message(ctx, embed)
                return curr_sheet_link, newsheet
            else:
                raise e
        # Error when the sheet has no template tab
        except gspread.exceptions.WorksheetNotFound:
            embed = discord_utils.create_embed()
            embed.add_field(
                name="Failed",
                value=f"The [sheet]({curr_sheet_link}) has no tab named '{template_or_meta}'. "
                f"Did you forget to add one?",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return curr_sheet_link, newsheet
        # Make sure tab_name does not exist
        try:
            curr_sheet.worksheet(tab_name)
            # If there is a tab with the given name, that's an error!
            embed = discord_utils.create_embed()
            embed.add_field(
                name="Failed",
                value=f"The [Google sheet at link]({curr_sheet_link}) already has a tab named "
                f"**{tab_name}**. Cannot create a tab with same name.",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return curr_sheet_link, newsheet
        except gspread.exceptions.WorksheetNotFound:
            # If the tab isn't found, that's good! We will create one.
            pass

        # Try to duplicate the template/meta tab and rename it to the given name
        try:
            newsheet = curr_sheet.duplicate_sheet(
                source_sheet_id=template_id,
                new_sheet_name=tab_name,
                insert_sheet_index=get_new_puzzle_tab_index(curr_sheet.worksheets()),
            )
        except gspread.exceptions.APIError as e:
            error_json = e.response.json()
            error_status = error_json.get("error", {}).get("status")
            if error_status == "PERMISSION_DENIED":
                embed = discord_utils.create_embed()
                embed.add_field(
                    name="Failed",
                    value=f"Could not duplicate '{template_or_meta}' tab in the "
                    f"[Google sheet at link]({curr_sheet_link}). "
                    f"Is the permission set up with 'Anyone with link can edit'?",
                    inline=False,
                )
                await discord_utils.send_message(ctx, embed)
                return curr_sheet_link, None
            else:
                raise e
        return curr_sheet_link, newsheet

    except gspread.exceptions.APIError as e:
        if hasattr(e, "response"):
            error_json = e.response.json()
            error_message = error_json.get("error", {}).get("message")
            embed.add_field(
                name="Failed",
                value=f"Unknown GSheets API Error - `{error_message}`",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return


class OverviewSheet:
    def __init__(self, gspread_client: gspread.Client, sheet_url: str):
        self.gspread_client = gspread_client
        self.sheet_url = sheet_url
        self.exception = None

        self.spreadsheet = self.gspread_client.open_by_url(sheet_url)
        self.worksheet = self.spreadsheet.worksheet("Overview")

        # Cache all data on the overview sheet
        self.overview_data = self.worksheet.get()

    def get_cell_value(self, label: str) -> str:
        row, col = gspread.utils.a1_to_rowcol(label)
        try:
            return self.overview_data[row - 1][col - 1]
        except IndexError:
            return ""

    def find_row_of_channel(
        self, ctx: commands.Context
    ) -> tuple[int, None] | tuple[None, nextcord.Embed]:
        chan_id = str(ctx.channel.id)
        for i, row in enumerate(self.overview_data):
            if chan_id == row[0]:
                # Users expect 1-indexed rows
                return i + 1, None

        # I don't like Go-style errors, but I also don't want to make this async...
        embed = discord_utils.create_embed()
        embed.add_field(
            name="Failed",
            value=f"I couldn't find the channel {ctx.channel.mention} in the sheet."
            f" Are you sure this channel is linked to a puzzle?",
            inline=False,
        )
        return None, embed


########################
# RESERVED HYDRA UTILS #
########################


async def create_puzzle_channel_from_template(
    bot,
    ctx: commands.Context,
    puzzle_name: str,
    template_name: str,
    puzzle_url: str | None,
    gspread_client,
    notes: str | None = None,
):
    """Create a puzzle channel and a new tab from `template_name` template, and update in overview. Based off chancrabgeneric."""
    embed = discord_utils.create_embed()
    tab_name = puzzle_name.replace("#", "").replace("-", " ")

    # Find tether for this category/channel
    if ctx.channel.category is None:
        embed.add_field(
            name="Failed",
            value="This command must be used in a channel inside a category!",
        )
        await discord_utils.send_message(ctx, embed)
        return None, None, None

    tether_db_result, tether_type = findsheettether(
        ctx.channel.category.id, ctx.channel.id
    )
    if tether_db_result is None:
        embed.add_field(
            name="Failed",
            value=f"The category **{ctx.channel.category.name}** nor the channel **{ctx.channel.name}** are tethered to a sheet.",
            inline=False,
        )
        await discord_utils.send_message(ctx, embed)
        return None, None, None

    curr_sheet_link = tether_db_result.sheet_link

    # Open the spreadsheet and choose template tab
    try:
        curr_sheet = gspread_client.open_by_url(curr_sheet_link)
    except gspread.exceptions.APIError as e:
        error_json = e.response.json()
        error_status = error_json.get("error", {}).get("status")
        if error_status == "PERMISSION_DENIED":
            embed = discord_utils.create_embed()
            embed.add_field(
                name="Failed",
                value=f"I'm unable to open the tethered [sheet]({curr_sheet_link}). "
                f"Did the permissions change?",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return None, None, None
        else:
            raise e

    desired_template_tab = (
        f"{template_name.title()} Template"
        if template_name.title() != "Template"
        else "Template"
    )

    template_ws = None
    template_id = None
    used_fallback = False

    try:
        template_ws = curr_sheet.worksheet(desired_template_tab)
    except gspread.exceptions.WorksheetNotFound:
        try:
            template_ws = curr_sheet.worksheet("Template")
            used_fallback = True
        except gspread.exceptions.WorksheetNotFound:
            embed.add_field(
                name="Failed",
                value=f"Neither the tab `{desired_template_tab}` nor `Template` exist on the tethered sheet",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return None, None, None

    template_id = template_ws.id

    # Tell user if fallback was used
    if used_fallback:
        embed = discord_utils.create_embed()
        embed.add_field(
            name="Note",
            value=f"The tab `{desired_template_tab}` does not exist on the tethered sheet. Using `Template` tab instead.",
            inline=False,
        )
        await discord_utils.send_message(ctx, embed)

    # Make sure tab_name does not exist
    try:
        curr_sheet.worksheet(tab_name)
        # If there is a tab with the given name, that's an error!
        embed = discord_utils.create_embed()
        embed.add_field(
            name="Failed",
            value=f"The [Google sheet at link]({curr_sheet_link}) already has a tab named "
            f"**{tab_name}**. Cannot create a tab with same name.",
            inline=False,
        )
        await discord_utils.send_message(ctx, embed)
        return None, None, None

    except gspread.exceptions.WorksheetNotFound:
        # If the tab isn't found, that's good! We will create one.
        pass

    # Try to duplicate the template tab and rename it to the given name
    try:
        newsheet = curr_sheet.duplicate_sheet(
            source_sheet_id=template_id,
            new_sheet_name=tab_name,
            insert_sheet_index=get_new_puzzle_tab_index(curr_sheet.worksheets()),
        )

    except gspread.exceptions.APIError as e:
        error_json = e.response.json()
        error_status = error_json.get("error", {}).get("status")
        if error_status == "PERMISSION_DENIED":
            embed = discord_utils.create_embed()
            embed.add_field(
                name="Failed",
                value=f"Could not duplicate '{desired_template_tab}' tab in the "
                f"[Google sheet at link]({curr_sheet_link}). "
                f"Is the permission set up with 'Anyone with link can edit'?",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return None, None, None
        else:
            raise e

    final_sheet_link = curr_sheet_link + "/edit#gid=" + str(newsheet.id)

    # create new channel
    new_chan = await discord_utils.createchannelgeneric(
        ctx.guild, ctx.channel.category, puzzle_name
    )

    if not new_chan:
        embed.add_field(
            name="Failed",
            value="Forbidden! Have you checked if the bot has the required permissions?",
        )
        await discord_utils.send_message(ctx, embed)
        return None, None, None

    embed = discord_utils.create_embed()
    embed.add_field(
        name="Success",
        value=f"Tab **{tab_name}** has been created at [{newsheet.spreadsheet.title}]({final_sheet_link}) spreadsheet.",
        inline=False,
    )
    try:
        msg = await new_chan.send(embed=embed)
    except nextcord.Forbidden:
        embed.add_field(
            name="Failed",
            value=f"Cannot send messages in `{puzzle_name}`!",
            inline=False,
        )
        await discord_utils.send_message(ctx, embed)
        return None, None, new_chan

    embed_or_none = await discord_utils.pin_message(msg)
    if embed_or_none is not None:
        await new_chan.send(embed=embed_or_none)

    if puzzle_url:
        embed = discord_utils.create_embed()
        embed.description = puzzle_url
        msg2 = await new_chan.send(embed=embed)
        embed_or_none = await discord_utils.pin_message(msg2)
        if embed_or_none is not None:
            await discord_utils.send_message(ctx, embed_or_none)
        else:
            await msg2.add_reaction(emoji.emojize(":pushpin:"))

    if notes:
        embed = discord_utils.create_embed()
        embed.description = f"`{notes}`"
        msg3 = await new_chan.send(embed=embed)

        embed_or_none = await discord_utils.pin_message(msg3)

        if embed_or_none is not None:
            await discord_utils.send_message(ctx, embed_or_none)
        else:
            await msg3.add_reaction(emoji.emojize(":pushpin:"))

    await new_chan.edit(topic=f"Tab Link - {final_sheet_link}")

    # tether channel
    addsheettethergeneric(gspread_client, curr_sheet_link, ctx.message.guild, new_chan)

    # update overview and new sheet
    try:
        overview = OverviewSheet(gspread_client, curr_sheet_link)
        overview_id = overview.worksheet.id
        first_empty = len(overview.overview_data) + 1

        discord_channel_id_col = sheets_constants.DISCORD_CHANNEL_ID_COLUMN
        sheet_tab_id_col = sheets_constants.SHEET_TAB_ID_COLUMN
        puzzle_name_col = overview.get_cell_value(
            sheets_constants.PUZZLE_NAME_COLUMN_LOCATION
        )
        status_col = overview.get_cell_value(sheets_constants.STATUS_COLUMN_LOCATION)
        answer_col = overview.get_cell_value(sheets_constants.ANSWER_COLUMN_LOCATION)

        batch = batch_update_utils.BatchUpdateBuilder()
        batch.update_cell_by_label(
            sheet_id=overview_id,
            label=puzzle_name_col + str(first_empty),
            value=f'=HYPERLINK("{final_sheet_link}", "{puzzle_name}")',
            is_formula=True,
        )

        batch.update_cell_by_label(
            sheet_id=overview_id,
            label=discord_channel_id_col + str(first_empty),
            value=str(new_chan.id),
        )
        batch.update_cell_by_label(
            sheet_id=overview_id,
            label=sheet_tab_id_col + str(first_empty),
            value=str(newsheet.id),
        )

        unstarted = sheets_constants.UNSTARTED_NAME
        batch.update_cell_by_label(
            sheet_id=overview_id,
            label=status_col + str(first_empty),
            value=unstarted,
        )

        batch.update_cell_by_label(
            sheet_id=overview_id,
            label=sheets_constants.PUZZLE_UNLOCKED_TIMESTAMP_COLUMN + str(first_empty),
            value=get_timestamp(),
        )

        tab_ans_loc = sheets_constants.TAB_ANSWER_LOCATION
        chan_name_loc = sheets_constants.TAB_CHAN_NAME_LOCATION
        url_loc = sheets_constants.TAB_URL_LOCATION

        batch.update_cell_by_label(
            sheet_id=overview_id,
            label=answer_col + str(first_empty),
            value="='{}'!{}".format(tab_name.replace("'", "''"), tab_ans_loc),
            is_formula=True,
        )

        batch.update_cell_by_label(
            sheet_id=newsheet.id,
            label=chan_name_loc,
            value=puzzle_name,
        )
        if puzzle_url:
            batch.update_cell_by_label(
                sheet_id=newsheet.id, label=url_loc, value=puzzle_url
            )

        batch.unhide_sheet(newsheet.id)

        if notes:
            batch.update_cell_by_label(
                sheet_id=overview_id,
                label=sheets_constants.NOTES_COLUMN + str(first_empty),
                value=notes,
            )

        gspread_client.open_by_url(curr_sheet_link).batch_update(batch.build())

    except gspread.exceptions.APIError as e:
        await handle_gspread_error(ctx, e)
        return curr_sheet_link, newsheet, new_chan

    await ctx.message.add_reaction(emoji.emojize(":check_mark_button:"))
    success_embed = discord_utils.create_embed()
    success_embed.add_field(
        name="Success",
        value=f"Channel `{puzzle_name}` created as {new_chan.mention} from template `{template_ws.title}`, posts pinned!",
        inline=False,
    )
    await discord_utils.send_message(ctx, success_embed)


async def findchanidcell(
    gspread_client, ctx: commands.Context, sheet_link, list_channel_id
) -> list[tuple[int, Worksheet, list]] | None:
    """Find the cell with the discord channel id based on overview (moved from HydraCog)."""
    try:
        overview_wrapper = OverviewSheet(gspread_client, sheet_link)
    except gspread.exceptions.APIError as e:
        embed = discord_utils.create_embed()
        embed.add_field(
            name="Failed",
            value=f"I'm unable to open the tethered sheet. Error: {str(e)}",
            inline=False,
        )
        await discord_utils.send_message(ctx, embed)
        return None
    except gspread.exceptions.SpreadsheetNotFound:
        embed = discord_utils.create_embed()
        embed.add_field(
            name="Failed",
            value=f"The [sheet]({sheet_link}) has no tab named 'Overview'. "
            f"Did you forget to add one?",
            inline=False,
        )
        await discord_utils.send_message(ctx, embed)
        return None
    except Exception as e:
        embed = discord_utils.create_embed()
        embed.add_field(
            name="Failed",
            value=f"An unknown error occurred when trying to open the tethered sheet. Error: {str(e)}",
            inline=False,
        )
        await discord_utils.send_message(ctx, embed)
        return None

    overview_values = overview_wrapper.overview_data
    id_to_row = {
        str(row[0]): idx + 1
        for idx, row in enumerate(overview_values)
        if row and row[0]
    }

    all_chan_ids = []
    for channel_id in list_channel_id:
        rownum = id_to_row.get(str(channel_id))
        all_chan_ids.append((rownum, overview_wrapper.worksheet, overview_values))
    return all_chan_ids


async def get_overview(
    gspread_client, ctx: commands.Context, sheet_link: str
) -> OverviewSheet | None:
    """Open an OverviewSheet with improved error messages (moved from HydraCog)."""
    try:
        overview_sheet = OverviewSheet(gspread_client, sheet_link)
    except gspread.exceptions.APIError as e:
        error_json = e.response.json()
        error_status = error_json.get("error", {}).get("status")
        if error_status == "PERMISSION_DENIED":
            embed = discord_utils.create_embed()
            embed.add_field(
                name="Failed",
                value=f"I'm unable to open the tethered [sheet]({sheet_link}). "
                f"Did the permissions change?",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return None
        else:
            raise e
    except gspread.exceptions.WorksheetNotFound:
        embed = discord_utils.create_embed()
        embed.add_field(
            name="Failed",
            value=f"The [sheet]({sheet_link}) has no tab named 'Overview'. "
            f"Did you forget to add one?",
            inline=False,
        )
        await discord_utils.send_message(ctx, embed)
        return None

    return overview_sheet


async def sheet_move_to_archive(gspread_client, ctx: commands.Context):
    """Handles the sheet aspect of mtahydra."""
    embed = discord_utils.create_embed()
    result, _ = findsheettether(ctx.message.channel.category_id, ctx.message.channel.id)

    if result is None:
        embed.add_field(
            name="Failed",
            value=f"Neither the category **{ctx.message.channel.category.name}** nor the channel {ctx.message.channel.mention} "
            f"are tethered to any Google sheet.",
            inline=False,
        )
        await discord_utils.send_message(ctx, embed)
        return

    curr_sheet_link = str(result.sheet_link)
    overview_sheet = await get_overview(gspread_client, ctx, curr_sheet_link)
    if overview_sheet is None:
        return

    row_to_find, err_embed = overview_sheet.find_row_of_channel(ctx)
    if err_embed is not None:
        await discord_utils.send_message(ctx, err_embed)
        return

    sheet_tab_id_col = sheets_constants.SHEET_TAB_ID_COLUMN
    tab_id = overview_sheet.get_cell_value(sheet_tab_id_col + str(row_to_find))

    try:
        worksheets = overview_sheet.spreadsheet.worksheets()
        puzzle_tab = next((w for w in worksheets if w.id == int(tab_id)), None)
        if puzzle_tab is None:
            embed.add_field(
                name="Failed",
                value="Could not find associated tab for puzzle in the tethered sheet.",
                inline=False,
            )
        else:
            puzzle_tab.update_index(len(worksheets))
            embed.add_field(
                name="Success",
                value="Moved tab to the end of the sheet!",
                inline=False,
            )
    except gspread.exceptions.APIError as e:
        error_json = e.response.json()
        error_message = error_json.get("error", {}).get("message")
        embed.add_field(
            name="Failed",
            value=f"Google Sheets API Error: `{error_message}`",
            inline=False,
        )
    except StopIteration:
        embed.add_field(
            name="Failed",
            value="Could not find associated tab for puzzle in the tethered sheet.",
            inline=False,
        )
    except Exception as e:
        embed.add_field(
            name="Failed",
            value=f"Unknown error: `{str(e)}`",
            inline=False,
        )
    await discord_utils.send_message(ctx, embed)


async def batch_create_puzzle_channels(
    bot,
    ctx: commands.Context,
    gspread_client,
    puzzle_configs: list[tuple[str, str | None, str | None]],
):
    """Batch creates multiple puzzle channels and tabs from template. Reserved for `chanhydra`."""
    result, _ = findsheettether(ctx.channel.category.id, ctx.channel.id)

    if result is None:
        embed = discord_utils.create_embed()
        embed.add_field(
            name="Failed",
            value=f"Neither the category **{ctx.channel.category.name}** nor the channel **{ctx.channel.name}** "
            "are tethered to a sheet.",
        )
        await discord_utils.send_message(ctx, embed)
        return []

    curr_sheet_link = str(result.sheet_link)

    try:
        spreadsheet = gspread_client.open_by_url(curr_sheet_link)
        template_sheet = spreadsheet.worksheet("Template")

        # Fetch all existing worksheet names once (single API call)
        all_worksheets = spreadsheet.worksheets()
        existing_sheet_names = {ws.title for ws in all_worksheets}
        insert_index = get_new_puzzle_tab_index(all_worksheets)

    except gspread.exceptions.WorksheetNotFound:
        embed = discord_utils.create_embed()
        embed.add_field(
            name="Failed",
            value="The sheet is missing either the 'Template' or 'Overview' tab.",
        )
        await discord_utils.send_message(ctx, embed)
        return []
    except gspread.exceptions.APIError as e:
        error_json = e.response.json()
        error_status = error_json.get("error", {}).get("status")
        if error_status == "PERMISSION_DENIED":
            embed = discord_utils.create_embed()
            embed.add_field(
                name="Failed",
                value=f"I'm unable to open the tethered [sheet]({curr_sheet_link}). "
                f"Did the permissions change?",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return []
        else:
            raise e
    except Exception as e:
        embed = discord_utils.create_embed()
        embed.add_field(
            name="Failed",
            value=f"Could not open the sheet. Error: {str(e)}",
        )
        await discord_utils.send_message(ctx, embed)
        return []

    # Create discord channels
    channels = []
    skipped_puzzles = []  # Track puzzles that were skipped

    for puzzle_name, puzzle_url, notes in puzzle_configs:
        tab_name = puzzle_name.replace("#", "").replace("-", " ")

        # Check if a sheet with this name already exists (using cached list)
        if tab_name in existing_sheet_names:
            embed = discord_utils.create_embed()
            embed.add_field(
                name="Failed",
                value=f"A sheet with the name `{tab_name}` already exists. Skipping `{puzzle_name}`.",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            skipped_puzzles.append(puzzle_name)
            continue

        try:
            new_channel = await discord_utils.createchannelgeneric(
                ctx.guild, ctx.channel.category, puzzle_name
            )

            if new_channel is None:
                raise Exception("Channel creation returned None")

            channels.append((puzzle_name, tab_name, puzzle_url, notes, new_channel))

        except Exception as e:
            embed = discord_utils.create_embed()
            embed.add_field(
                name="Failed",
                value=f"Could not create channel for `{puzzle_name}`. Error: {str(e)}",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            skipped_puzzles.append(puzzle_name)
            continue

    if not channels:
        # Return results for all skipped puzzles
        return [(None, None, None, name) for name in skipped_puzzles]

    # Batch create all worksheets
    requests = []
    # Each channel is (puzzle_name, tab_name, puzzle_url, notes, new_channel)
    for i, (_, tab_name, _, _, _) in enumerate(channels):
        requests.append(
            {
                "duplicateSheet": {
                    "sourceSheetId": template_sheet.id,
                    "insertSheetIndex": insert_index + i,
                    "newSheetName": tab_name,
                }
            }
        )

    try:
        batch_response = spreadsheet.batch_update({"requests": requests})  # noqa: F841
    except gspread.exceptions.APIError as e:
        error_json = e.response.json()
        error_status = error_json.get("error", {}).get("status")
        error_message = error_json.get("error", {}).get("message", "")

        # Check for duplicate sheet name error
        if "already exists" in error_message:
            embed = discord_utils.create_embed()
            embed.add_field(
                name="Failed",
                value=f"One or more sheets already exist with the given names. Error: {error_message}",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return []
        elif error_status == "PERMISSION_DENIED":
            embed = discord_utils.create_embed()
            embed.add_field(
                name="Failed",
                value="Could not duplicate tabs. Is the permission set to 'Anyone with link can edit'?",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return []
        else:
            raise e
    except Exception as e:
        embed = discord_utils.create_embed()
        embed.add_field(
            name="Failed",
            value=f"Could not create sheets. Error: {str(e)}",
            inline=False,
        )
        await discord_utils.send_message(ctx, embed)
        return []

    # Refresh and get the newly created sheets
    spreadsheet = gspread_client.open_by_url(curr_sheet_link)
    worksheets_by_title = {ws.title: ws for ws in spreadsheet.worksheets()}
    # Each channel is (puzzle_name, tab_name, puzzle_url, notes, new_channel)
    worksheets = [
        worksheets_by_title.get(tab_name) for _, tab_name, _, _, _ in channels
    ]

    # Get overview wrapper and constants
    overview_wrapper = OverviewSheet(gspread_client, curr_sheet_link)
    overview_values = overview_wrapper.overview_data
    first_empty_row = len(overview_values) + 1
    overview_id = overview_wrapper.worksheet.id

    # Get column labels
    puzzle_name_col = overview_wrapper.get_cell_value(
        sheets_constants.PUZZLE_NAME_COLUMN_LOCATION
    )
    status_col = overview_wrapper.get_cell_value(
        sheets_constants.STATUS_COLUMN_LOCATION
    )
    answer_col = overview_wrapper.get_cell_value(
        sheets_constants.ANSWER_COLUMN_LOCATION
    )
    discord_channel_id_col = sheets_constants.DISCORD_CHANNEL_ID_COLUMN
    sheet_tab_id_col = sheets_constants.SHEET_TAB_ID_COLUMN

    unlocked_timestamp = get_timestamp()

    # Build batch update for overview and new sheets
    batch = batch_update_utils.BatchUpdateBuilder()

    for idx, (puzzle_name, tab_name, puzzle_url, notes, channel) in enumerate(channels):
        if worksheets[idx] is None:
            continue
        try:
            row_num = first_empty_row + idx
            newsheet = worksheets[idx]
            final_sheet_link = curr_sheet_link + "/edit#gid=" + str(newsheet.id)

            # Batch update overview row
            overview_updates = {
                puzzle_name_col + str(row_num): (
                    f'=HYPERLINK("{final_sheet_link}", "{puzzle_name}")',
                    True,  # is_formula
                ),
                discord_channel_id_col + str(row_num): (str(channel.id), False),
                sheet_tab_id_col + str(row_num): (str(newsheet.id), False),
                status_col + str(row_num): (sheets_constants.UNSTARTED_NAME, False),
                answer_col + str(row_num): (
                    "='{}'!{}".format(
                        tab_name.replace("'", "''"),
                        sheets_constants.TAB_ANSWER_LOCATION,
                    ),
                    True,  # is_formula
                ),
                sheets_constants.PUZZLE_UNLOCKED_TIMESTAMP_COLUMN + str(row_num): (
                    unlocked_timestamp,
                    False,
                ),
            }
            if notes:
                overview_updates[sheets_constants.NOTES_COLUMN + str(row_num)] = (
                    notes,
                    False,
                )

            for label, (value, is_formula) in overview_updates.items():
                batch.update_cell_by_label(
                    sheet_id=overview_id,
                    label=label,
                    value=value,
                    is_formula=is_formula,
                )

            # Batch update new sheet
            new_sheet_updates = {
                sheets_constants.TAB_CHAN_NAME_LOCATION: puzzle_name,
            }
            if puzzle_url:
                new_sheet_updates[sheets_constants.TAB_URL_LOCATION] = puzzle_url

            for label, value in new_sheet_updates.items():
                batch.update_cell_by_label(
                    sheet_id=newsheet.id,
                    label=label,
                    value=value,
                )

            # Templates are often hidden, and the copies inherit that
            batch.unhide_sheet(newsheet.id)

            # Tether channel
            addsheettethergeneric(gspread_client, curr_sheet_link, ctx.guild, channel)

            # Update channel topic
            await channel.edit(topic=f"Tab Link - {final_sheet_link}")

            # Send messages to channel
            try:
                embed = discord_utils.create_embed()
                embed.add_field(
                    name="Success",
                    value=f"Tab **{tab_name}** has been created at [{newsheet.spreadsheet.title}]({final_sheet_link}) spreadsheet.",
                    inline=False,
                )
                msg = await channel.send(embed=embed)
                await discord_utils.pin_message(msg)

                if puzzle_url:
                    embed = discord_utils.create_embed()
                    embed.description = puzzle_url
                    msg2 = await channel.send(embed=embed)
                    embed_or_none = await discord_utils.pin_message(msg2)
                    if embed_or_none is None:
                        await msg2.add_reaction(emoji.emojize(":pushpin:"))

                if notes:
                    embed = discord_utils.create_embed()
                    embed.description = f"`{notes}`"
                    msg3 = await channel.send(embed=embed)
                    embed_or_none = await discord_utils.pin_message(msg3)
                    if embed_or_none is None:
                        await msg3.add_reaction(emoji.emojize(":pushpin:"))
            except Exception:
                pass
        except Exception as e:
            embed = discord_utils.create_embed()
            embed.add_field(
                name="Failed",
                value=f"Error processing `{puzzle_name}`. Error: {str(e)}",
                inline=False,
            )

            await discord_utils.send_message(ctx, embed)
            worksheets[idx] = None
            continue

    # Execute single batch update for ALL changes
    try:
        spreadsheet.batch_update(batch.build())
    except gspread.exceptions.APIError as e:
        if hasattr(e, "response"):
            error_json = e.response.json()
            error_message = error_json.get("error", {}).get("message")
            embed = discord_utils.create_embed()
            embed.add_field(
                name="Failed",
                value=f"Unknown GSheets API Error - `{error_message}`",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return []
    except Exception as e:
        embed = discord_utils.create_embed()
        embed.add_field(
            name="Failed",
            value=f"Could not update sheets. Error: {str(e)}",
            inline=False,
        )
        await discord_utils.send_message(ctx, embed)
        return []

    # Return results
    results = []
    for idx, (puzzle_name, tab_name, puzzle_url, notes, channel) in enumerate(channels):
        if worksheets[idx] is not None:
            final_link = curr_sheet_link + "/edit#gid=" + str(worksheets[idx].id)
            results.append((final_link, worksheets[idx], channel, puzzle_name))
        else:
            results.append((None, None, None, puzzle_name))

    # Add skipped puzzles to results
    for puzzle_name in skipped_puzzles:
        results.append((None, None, None, puzzle_name))

    return results
