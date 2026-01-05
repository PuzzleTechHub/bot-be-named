from utils import batch_update_utils, sheets_constants
from utils import discord_utils
import constants
import nextcord
import gspread
from utils.sheet_utils import OverviewSheet, findsheettether, addsheettethergeneric
import emoji

from nextcord.ext.commands import Context

########################
# RESERVED HYDRA UTILS #
########################

async def create_puzzle_channel_from_template(
    bot,
    ctx,
    puzzle_name: str,
    template_name: str,
    puzzle_url: str | None,
    gspread_client,
):
    """Create a puzzle channel and a new tab from `template_name` template, and update in overview. Based off chancrabgeneric."""
    embed = discord_utils.create_embed()
    tab_name = puzzle_name.replace("#", "").replace("-", " ")

    # Find tether for this category/channel
    if ctx.channel.category is None:
        embed.add_field(
            name=f"{constants.FAILED}!",
            value="This command must be used in a channel inside a category!",
        )
        await discord_utils.send_message(ctx, embed)
        return None, None, None

    tether_db_result, tether_type = findsheettether(
        str(ctx.channel.category.id), str(ctx.channel.id)
    )
    if tether_db_result is None:
        embed.add_field(
            name=f"{constants.FAILED}!",
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
                name=f"{constants.FAILED}",
                value=f"I'm unable to open the tethered [sheet]({curr_sheet_link}). "
                f"Did the permissions change?",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return None, None, None
        else:
            raise e
    desired_template_tab = f"{template_name.title()} Template"

    template_ws = None
    template_id = None
    template_index = None
    used_fallback = False

    try:
        template_ws = curr_sheet.worksheet(desired_template_tab)
    except gspread.exceptions.WorksheetNotFound:
        try:
            template_ws = curr_sheet.worksheet("Template")
            used_fallback = True
        except gspread.exceptions.WorksheetNotFound:
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"Neither the tab `{desired_template_tab}` nor `Template` exist on the tethered sheet",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return None, None, None

    template_id = template_ws.id
    template_index = template_ws.index

    # Tell user if fallback was used
    if used_fallback:
        embed = discord_utils.create_embed()
        embed.add_field(
            name=f"{constants.FAILED}",
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
            name=f"{constants.FAILED}",
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
            insert_sheet_index=template_index + 2,
        )

    except gspread.exceptions.APIError as e:
        error_json = e.response.json()
        error_status = error_json.get("error", {}).get("status")
        if error_status == "PERMISSION_DENIED":
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
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
            name=f"{constants.FAILED}!",
            value="Forbidden! Have you checked if the bot has the required permisisons?",
        )
        await discord_utils.send_message(ctx, embed)
        return None, None, None

    embed = discord_utils.create_embed()
    embed.add_field(
        name=f"{constants.SUCCESS}!",
        value=f"Tab **{tab_name}** has been created at [{newsheet.spreadsheet.title}]({final_sheet_link}) spreadsheet.",
        inline=False,
    )
    try:
        msg = await new_chan.send(embed=embed)
    except nextcord.Forbidden:
        embed.add_field(
            name=f"{constants.FAILED}!",
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

    await new_chan.edit(topic=f"Tab Link - {final_sheet_link}")

    # tether channel
    addsheettethergeneric(gspread_client, curr_sheet_link, ctx.message.guild, new_chan)

    # update overview and new sheet(similar to lion)
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
                sheet_id=newsheet.id, 
                label=url_loc, 
                value=puzzle_url
            )

        gspread_client.open_by_url(curr_sheet_link).batch_update(batch.build())

    except gspread.exceptions.APIError as e:
        # surface a concise error back to user
        if hasattr(e, "response"):
            error_json = e.response.json()
            error_message = error_json.get("error", {}).get("message")
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"Unknown GSheets API Error - `{error_message}`",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return curr_sheet_link, newsheet, new_chan

    await ctx.message.add_reaction(emoji.emojize(":check_mark_button:"))