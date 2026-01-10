from datetime import datetime, timezone

import emoji
import gspread
import nextcord
from gspread.worksheet import Worksheet
from nextcord.ext.commands import Context

from utils import batch_update_utils, discord_utils, sheets_constants
from utils.sheet_utils import OverviewSheet, addsheettethergeneric, findsheettether

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
            name="Failed",
            value="This command must be used in a channel inside a category!",
        )
        await discord_utils.send_message(ctx, embed)
        return None, None, None

    tether_db_result, tether_type = findsheettether(
        str(ctx.channel.category.id), str(ctx.channel.id)
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
                name="Failed",
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
            name="Failed",
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
    # Find the last template sheet to insert after it (in the active section)
    insert_index = template_index + 1  # Default: right after current template
    found_template = False
    for sheet in curr_sheet.worksheets():
        if sheet.title.endswith("Template"):
            insert_index = sheet.index + 1
            found_template = True
        else:
            if found_template:
                break  # We found the last template already

    try:
        newsheet = curr_sheet.duplicate_sheet(
            source_sheet_id=template_id,
            new_sheet_name=tab_name,
            insert_sheet_index=insert_index,
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
            value="Forbidden! Have you checked if the bot has the required permisisons?",
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
        unlocked_timestamp_col = sheets_constants.PUZZLE_UNLOCKED_TIMESTAMP_COLUMN

        # Get current timestamp in DD/MM/YY HH:MM:SS format
        current_timestamp = datetime.now(timezone.utc).strftime("%d/%m/%y %H:%M:%S")

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
            label=unlocked_timestamp_col + str(first_empty),
            value=current_timestamp,
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

        gspread_client.open_by_url(curr_sheet_link).batch_update(batch.build())

    except gspread.exceptions.APIError as e:
        # surface a concise error back to user
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
            return curr_sheet_link, newsheet, new_chan

    await ctx.message.add_reaction(emoji.emojize(":check_mark_button:"))

    # Send success message to the calling channel
    success_embed = discord_utils.create_embed()
    success_embed.add_field(
        name="Success",
        value=f"Channel `{puzzle_name}` created as {new_chan.mention} from template `{template_name}`, posts pinned!",
        inline=False,
    )
    await discord_utils.send_message(ctx, success_embed)


async def findchanidcell(
    gspread_client, ctx, sheet_link, list_channel_id
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


def firstemptyrow(worksheet):
    """Finds the first empty row in a worksheet (moved from HydraCog)."""
    return len(worksheet.get_values()) + 1


async def get_overview(
    gspread_client, ctx: Context, sheet_link: str
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


async def sheet_move_to_archive(gspread_client, ctx: Context):
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
        embed.add_field(
            name="Failed",
            value="Error! Overview tab not found in the sheet! Did you accidentally delete it?",
            inline=False,
        )
        await discord_utils.send_message(ctx, embed)
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
    ctx,
    gspread_client,
    puzzle_configs: list[tuple[str, str | None]],
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
        existing_sheet_names = {ws.title for ws in spreadsheet.worksheets()}
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

    for puzzle_name, puzzle_url in puzzle_configs:
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

            channels.append((puzzle_name, tab_name, puzzle_url, new_channel))

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
    for puzzle_name, tab_name, _, _ in channels:
        requests.append(
            {
                "duplicateSheet": {
                    "sourceSheetId": template_sheet.id,
                    "insertSheetIndex": template_sheet.index + 1,
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
    worksheets = []

    for _, tab_name, _, _ in channels:
        try:
            ws = spreadsheet.worksheet(tab_name)
            worksheets.append(ws)
        except Exception:
            worksheets.append(None)

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

    # Get current timestamp for all puzzles in DD/MM/YY HH:MM:SS format
    current_timestamp = datetime.now(timezone.utc).strftime("%d/%m/%y %H:%M:%S")
    unlocked_timestamp_col = sheets_constants.PUZZLE_UNLOCKED_TIMESTAMP_COLUMN

    # Build batch update for overview and new sheets
    batch = batch_update_utils.BatchUpdateBuilder()

    for idx, (puzzle_name, tab_name, puzzle_url, channel) in enumerate(channels):
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
                unlocked_timestamp_col + str(row_num): (current_timestamp, False),
            }

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
    for idx, (puzzle_name, tab_name, puzzle_url, channel) in enumerate(channels):
        if worksheets[idx] is not None:
            final_link = curr_sheet_link + "/edit#gid=" + str(worksheets[idx].id)
            results.append((final_link, worksheets[idx], channel, puzzle_name))
        else:
            results.append((None, None, None, puzzle_name))

    # Add skipped puzzles to results
    for puzzle_name in skipped_puzzles:
        results.append((None, None, None, puzzle_name))

    return results
