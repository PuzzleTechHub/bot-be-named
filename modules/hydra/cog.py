import nextcord
import constants
import gspread
import asyncio
import heapq
import shlex
import re
import emoji
from collections import Counter
from nextcord.ext import commands
from utils import (
    discord_utils,
    google_utils,
    logging_utils,
    command_predicates,
    sheets_constants,
    sheet_utils,
)
from modules.hydra.hydra_utils import hydra_helpers
from modules.hydra.hydra_utils import discord_utils as hydra_discord_utils
from modules.hydra.hydra_utils import sheet_utils as hydra_sheet_utils
from modules.hydra.hydra_utils.sheet_command_base import SheetCommandBase
from modules.hydra import constants as hydra_constants

"""
Hydra module. Module with more advanced GSheet-Discord interfacing. See module's README.md for more.
"""


class HydraCog(commands.Cog, name="Hydra"):
    """
    More powerful useful GSheet-Discord commands.
    """

    def __init__(self, bot):
        self.bot = bot
        self.lock = asyncio.Lock()
        self.gdrive_credentials = google_utils.get_gdrive_credentials()
        self.gspread_client = google_utils.create_gspread_client()

    ###################
    # HYDRA COMMANDS  #
    ###################

    @command_predicates.is_solver()
    @commands.command(name="roundhydra")
    async def roundhydra(self, ctx: commands.Context, round_name: str = None):
        """Sets or updates the round information on the Overview sheet. Passing no argument retrieves the current round.

        Permission Category : Solver Roles only
        Usage: `~roundhydra` (retrieves current round)
        Usage: `~roundhydra "Round Name"` (sets round)
        """
        await logging_utils.log_command(
            "roundhydra", ctx.guild, ctx.channel, ctx.author
        )

        base = SheetCommandBase(ctx, self.gspread_client)
        curr_sheet_link, overview_sheet, row_to_find = await base.get_sheet_context()

        if overview_sheet is None:
            return

        embed = discord_utils.create_embed()

        round_col = sheets_constants.ROUND_COLUMN

        try:
            if round_name is None:
                # If no arg passed, retrieve current round and tell user
                current_round = overview_sheet.worksheet.acell(
                    round_col + str(row_to_find)
                ).value
                if current_round is None:
                    embed.add_field(
                        name="Current Round",
                        value=f"The current round for {ctx.channel.mention} is not set.",
                        inline=False,
                    )
                else:
                    embed.add_field(
                        name="Current Round",
                        value=f"The current round for {ctx.channel.mention} is `{current_round}`.",
                        inline=False,
                    )
                await discord_utils.send_message(ctx, embed)
            else:
                # Update round instead
                current_round = overview_sheet.worksheet.acell(
                    round_col + str(row_to_find)
                ).value

                overview_sheet.worksheet.update_acell(
                    round_col + str(row_to_find), round_name
                )

                if current_round:
                    embed.add_field(
                        name="Success",
                        value=f"Successfully updated round for {ctx.channel.mention} from `{current_round}` to `{round_name}`",
                        inline=False,
                    )
                else:
                    embed.add_field(
                        name="Success",
                        value=f"Successfully updated round for {ctx.channel.mention} to `{round_name}`",
                        inline=False,
                    )

                await ctx.message.add_reaction(emoji.emojize(":check_mark_button:"))
                await discord_utils.send_message(ctx, embed)

        except gspread.exceptions.APIError as e:
            error_json = e.response.json()
            error_status = error_json.get("error", {}).get("status")
            if error_status == "PERMISSION_DENIED":
                embed.add_field(
                    name="Failed",
                    value="Could not update the sheet. Permission denied.",
                    inline=False,
                )
            else:
                embed.add_field(
                    name="Failed",
                    value=f"Unknown GSheets API Error - `{error_json.get('error', {}).get('message')}`",
                    inline=False,
                )
            await discord_utils.send_message(ctx, embed)

    @command_predicates.is_solver()
    @commands.command(name="noteshydra")
    async def noteshydra(self, ctx: commands.Context, notes: str = None):
        """Sets or updates the notes information on the Overview sheet. Passing no argument retrieves the current notes.

        Permission Category : Solver Roles only
        Usage: `~noteshydra` (retrieves current notes)
        Usage: `~noteshydra "This puzzle has unclued anagrams."` (sets notes)
        """

        await logging_utils.log_command(
            "noteshydra", ctx.guild, ctx.channel, ctx.author
        )

        base = SheetCommandBase(ctx, self.gspread_client)
        curr_sheet_link, overview_sheet, row_to_find = await base.get_sheet_context()

        if overview_sheet is None:
            return

        embed = discord_utils.create_embed()

        notes_col = sheets_constants.NOTES_COLUMN

        try:
            if notes is None:
                # If no arg passed, retrieve current notes and tell user
                current_notes = overview_sheet.worksheet.acell(
                    notes_col + str(row_to_find)
                ).value
                if current_notes is None:
                    embed.add_field(
                        name="Current Notes",
                        value=f"The current notes for {ctx.channel.mention} are not set.",
                        inline=False,
                    )
                else:
                    embed.add_field(
                        name="Current Notes",
                        value=f"The current notes for {ctx.channel.mention} are `{current_notes}`.",
                        inline=False,
                    )
                await discord_utils.send_message(ctx, embed)
            else:
                # Update notes instead
                current_notes = overview_sheet.worksheet.acell(
                    notes_col + str(row_to_find)
                ).value

                overview_sheet.worksheet.update_acell(
                    notes_col + str(row_to_find), notes
                )

                if current_notes:
                    embed.add_field(
                        name="Success",
                        value=f"Successfully updated notes for {ctx.channel.mention} from `{current_notes}` to `{notes}`",
                        inline=False,
                    )
                else:
                    embed.add_field(
                        name="Success",
                        value=f"Successfully updated notes for {ctx.channel.mention} to `{notes}`",
                        inline=False,
                    )

                await ctx.message.add_reaction(emoji.emojize(":check_mark_button:"))
                await discord_utils.send_message(ctx, embed)

        except gspread.exceptions.APIError as e:
            error_json = e.response.json()
            error_status = error_json.get("error", {}).get("status")
            if error_status == "PERMISSION_DENIED":
                embed.add_field(
                    name="Failed",
                    value="Could not update the sheet. Permission denied.",
                    inline=False,
                )
            else:
                embed.add_field(
                    name="Failed",
                    value=f"Unknown GSheets API Error - `{error_json.get('error', {}).get('message')}`",
                    inline=False,
                )
            await discord_utils.send_message(ctx, embed)

    @command_predicates.is_solver()
    @commands.command(name="catsummaryhydra", aliases=["categorysummaryhydra"])
    async def catsummaryhydra(self, ctx) -> None:
        """Collates all the notes on the overview sheet for each text channel in the category the command was
        called in. Silently skips channels not on the overview. The sheet will need to follow the Hydra
        requirements for this to work as expected.

        Permission Category : Solver Roles only.

        Usage: `~catsummaryhydra`
        """
        await logging_utils.log_command(
            "catsummaryhydra", ctx.guild, ctx.channel, ctx.author
        )
        embed = discord_utils.create_embed()

        currcat = ctx.message.channel.category

        start_embed = discord_utils.create_embed()
        start_embed.add_field(
            name="Summary Started",
            value=f"Your summarizing of category `{currcat.name}`"
            f" has begun! This may take a while. If I run into "
            f"any errors, I'll let you know.",
            inline=False,
        )

        # Set initial message to be variable to delete after success/failure
        initial_message = (await discord_utils.send_message(ctx, start_embed))[0]

        try:
            allchans = currcat.text_channels
            messages = []
            allsheets = []

            # Group all channels sharing the same tethered sheet. Now find the right cell
            for currchan in allchans:
                result, _ = sheet_utils.findsheettether(
                    str(currchan.category_id), str(currchan.id)
                )
                if result is None:
                    continue  # Silently skip channels with no tether
                curr_sheet_link = result.sheet_link
                allsheets.append((curr_sheet_link, currchan))

            all_unique_sheets = list(set([x[0] for x in allsheets]))

            for curr_sheet_link in all_unique_sheets:
                list_curr_sheet_chans = [
                    x[1] for x in allsheets if x[0] == curr_sheet_link
                ]

                list_chan_cells_overview = await hydra_sheet_utils.findchanidcell(
                    self.gspread_client,
                    ctx,
                    curr_sheet_link,
                    [x.id for x in list_curr_sheet_chans],
                )

                if list_chan_cells_overview is None:
                    for currchan in list_curr_sheet_chans:
                        messages.append(
                            f"- {currchan.mention} - **Failed to load sheet!**"
                        )
                    continue

                overview_col = sheets_constants.NOTES_COLUMN
                _, sample_overview, sample_values = next(
                    (t for t in list_chan_cells_overview if t[1] is not None),
                    (None, None, None),
                )

                if sample_overview is None or sample_values is None:
                    continue  # Silently skip if no valid overview found

                _, col_idx = gspread.utils.a1_to_rowcol(overview_col + "1")
                for i in range(len(list_curr_sheet_chans)):
                    currchan = list_curr_sheet_chans[i]
                    rownum, overview, overview_values = list_chan_cells_overview[i]
                    if rownum is None or overview is None:
                        continue  # Silently skip again

                    # Safe get overview values
                    try:
                        overview_desc = overview_values[rownum - 1][col_idx - 1]
                    except Exception:
                        overview_desc = None
                    if overview_desc:
                        preview = (
                            overview_desc[: hydra_constants.OVERVIEW_DESC_PREVIEW]
                            + "..."
                            if len(overview_desc)
                            > hydra_constants.OVERVIEW_DESC_PREVIEW
                            else overview_desc
                        )
                        messages.append(f"- {currchan.mention} - {preview}")
                    else:
                        messages.append(f"- {currchan.mention} - *(empty description)*")
        except Exception as e:
            embed = discord_utils.create_embed()
            embed.add_field(
                name="Failed",
                value=f"An error occurred while summarizing category `{currcat.name}`. "
                f"Error: {str(e)}",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            await initial_message.delete()
            return

        if not messages:
            embed = discord_utils.create_embed()
            embed.add_field(
                name="Failed",
                value=f"No text channels found in category `{currcat.name}`.",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            await initial_message.delete()
            return

        # Split into multiple messages
        chunk_size = hydra_constants.SUMMARY_CHUNK_SIZE
        for i in range(0, len(messages), chunk_size):
            final_embed = discord_utils.create_embed()
            chunk = messages[i : i + chunk_size]

            for j, msg in enumerate(chunk):
                parts = msg.split(" - ", 1)
                channel_part = parts[0].replace("- ", "").strip()
                desc_part = parts[1].strip() if len(parts) > 1 else "\u200b"

                final_embed.add_field(name=channel_part, value=desc_part, inline=True)

                if (j + 1) % 2 == 0:
                    final_embed.add_field(name="\u200b", value="\u200b", inline=True)

            await discord_utils.send_message(ctx, final_embed)

        await initial_message.delete()

    @command_predicates.is_solver()
    @commands.command(name="anychanhydra", aliases=["anyhydra"])
    async def anychanhydra(
        self,
        ctx,
        *,
        args,
    ):
        """Creates a new tab from a template, and a new channel for a puzzle. Then updates the info in the sheet accordingly.

        Creates a new puzzle channel based on a template in the tethered GSheet. Template must be passed in.

        Requires that the sheet has Overview following Hydra rules (FIXME).
        Requires that there is a template tab on the sheet with that name, for example passing "Acrostics" uses "Acrostics Template".
        Requires that Template tab follows Hydra rules (Cell B4 must be used for answer).

        Permission Category : Solver Roles only.

        Usage: ~anychanhydra "Puzzle Name" "TemplateName" (uses "TemplateName Template" from the sheet)
        Usage: ~anychanhydra PuzzleName "Square" "http://www.linktopuzzle.com" (uses "Square Template" from the sheet)
        """
        await logging_utils.log_command(
            "anychanhydra", ctx.guild, ctx.channel, ctx.author
        )

        arg_list = shlex.split(args)
        if len(arg_list) < 2 or len(arg_list) > 3:
            embed = discord_utils.create_embed()
            embed.add_field(
                name="Failed",
                value="Invalid arguments. Usage: `~anychanhydra [puzzle name] [template name] [puzzle url (optional)]`",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return

        puzzle_name = arg_list[0]
        template_name = arg_list[1]
        puzzle_url = arg_list[2] if len(arg_list) > 2 else None

        await hydra_sheet_utils.create_puzzle_channel_from_template(
            self.bot,
            ctx,
            puzzle_name,
            template_name,
            puzzle_url,
            self.gspread_client,
        )

    @command_predicates.is_solver()
    @commands.command(name="mtahydra", aliases=["movetoarchivehydra"])
    async def mtahydra(self, ctx, *, category_name: str = None):
        """Finds a category with `<category_name> Archive`, and moves the channel to that category.
        Fails if there is no such category. If the category is full (50 channels), I will make a new one.
        If called from thread (instead of channel), closes the thread instead of moving channel.

        In the hydra implementation of ~mta, the archive category name is stardardized.

        It must be in the form of `<category_name> Archive`, e.g. `MH21 Students Archive`.
        Your solving category should not end with Archive.

        Also moves the tab to the end of the list of tabs on the Google Sheet.

        Attempts to search smart, for example `~mtahydra "MH21 Students"` will search for "MH21 Students Archive" and "MH21 Archive" categories.
        Some other common variants for "Archive" will also be attempted.

        Permission Category : Solver Roles only.
        Usage: `~mtahydra`
        Usage: `~mtahydra archive_category_name`
        """
        await logging_utils.log_command("mtahydra", ctx.guild, ctx.channel, ctx.author)
        await hydra_sheet_utils.sheet_move_to_archive(self.gspread_client, ctx)
        await hydra_discord_utils.category_move_to_archive(ctx, category_name)

    @commands.command(name="chanhydra")
    async def chanhydra(self, ctx: commands.Context, *, content: str = ""):
        """Creates a new tab and a new channel for a new feeder puzzle and then updates the info in the sheet accordingly.

        Requires that the sheet has Overview and Template tabs.
        Supports creating multiple channels in parallel delimited by new lines (CTRL + Enter).

        Permission Category : Solver Roles only.
        Usage: ~chanhydra "Puzzle Name"
        Usage: ~chanhydra PuzzleName "http://www.linktopuzzle.com"
        Usage:
        ~chanhydra
        APuzzle "http://linktoapuzzle.com"
        "B Puzzle" "http://linktobpuzzle.com"
        3rdPuzzle
        """

        await logging_utils.log_command("chanhydra", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        content = content.strip()

        if not content:
            embed.add_field(
                name="Failed",
                value="You need to provide at least a puzzle name.",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return

        # Parse all puzzle configurations
        puzzle_configs = []
        lines = [line.strip() for line in content.split("\n") if line.strip()]

        for line in lines:
            try:
                parts = shlex.split(line)
            except ValueError as e:
                embed.add_field(
                    name="Failed",
                    value=f"Error parsing line `{line}`... continuing parsing the rest.\nError: {str(e)}",
                    inline=False,
                )
                await discord_utils.send_message(ctx, embed)
                continue

            if not parts:
                continue

            puzzle_name = parts[0]
            puzzle_url = parts[1] if len(parts) > 1 else ""
            puzzle_configs.append((puzzle_name, puzzle_url))

        if not puzzle_configs:
            embed.add_field(
                name="Failed",
                value="No data passed into the command!",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return

        # Batch create all channels and sheets
        results = await hydra_sheet_utils.batch_create_puzzle_channels(
            self.bot,
            ctx,
            self.gspread_client,
            puzzle_configs,
        )

        # Report results
        success_count = sum(1 for r in results if r[0] is not None)
        success_messages = []
        failed_messages = []

        for result in results:
            if result[0] is not None:  # Success
                channel = result[2]
                puzzle_name = result[3]
                success_messages.append(
                    f"- Channel `{puzzle_name}` created as {channel.mention}, posts pinned!"
                )
            else:  # Failed
                puzzle_name = result[3]
                failed_messages.append(f"- `{puzzle_name}`")

        if success_count > 0:
            embed = discord_utils.create_embed()
            embed.add_field(
                name="Success",
                value=(
                    f"Successfully created {success_count} puzzle channel(s):\n\n"
                    "\n".join(success_messages)
                    if success_messages
                    else f"Successfully created {success_count} puzzle channel(s)!"
                ),
                inline=False,
            )
            await ctx.message.add_reaction(emoji.emojize(":check_mark_button:"))
            await discord_utils.send_message(ctx, embed)

        if success_count < len(puzzle_configs):
            failed_count = len(puzzle_configs) - success_count
            embed = discord_utils.create_embed()
            embed.add_field(
                name="Failed",
                value=f"Failed to create {failed_count} puzzle channel(s). Check earlier messages for details.\n\n"
                + "\n".join(failed_messages),
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)

    @command_predicates.is_trusted()
    @commands.command(name="deletehydra")
    async def deletehydra(self, ctx: commands.Context, channel_mention: str = ""):
        """Deletes a puzzle channel, its corresponding tab, triggers archiving and cleans
        up the overview.

        Must be called from a different channel from the one being deleted.

        You'll need to confirm the deletion by reacting to the confirmation message within 15 seconds.

        Permission Category : Trusted Roles only.

        Usage: `~deletehydra #puzzle-channel` (deletes #puzzle-channel)
        """
        await logging_utils.log_command(
            "deletehydra", ctx.guild, ctx.channel, ctx.author
        )
        embed = discord_utils.create_embed()

        # Check if channel mention is provided
        if channel_mention == "":
            embed.add_field(
                name="Failed",
                value="Please provide a channel to delete. Usage: `~deletehydra #puzzle-channel`",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return

        # Parse the channel from the mention
        target_channel = None
        if ctx.message.channel_mentions:
            target_channel = ctx.message.channel_mentions[0]

        if target_channel is None:
            embed.add_field(
                name="Failed",
                value="Please mention the channel, not just type its name!",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return

        # Check that the target channel is not the same as the command channel
        if target_channel.id == ctx.channel.id:
            embed.add_field(
                name="Failed",
                value="You cannot delete the channel you are currently in. Please run this command from a different channel.",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return

        # Check that the target channel has a valid sheet tether
        result, _ = sheet_utils.findsheettether(
            str(target_channel.category_id), str(target_channel.id)
        )

        if result is None:
            embed.add_field(
                name="Failed",
                value=f"The channel {target_channel.mention} is not tethered to any Google sheet.",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return

        curr_sheet_link = str(result.sheet_link)

        # Confirmation prompt
        confirm_embed = discord_utils.create_embed()
        confirm_embed.add_field(
            name="Confirm deletion?",
            value=f"You are about to delete the channel {target_channel.mention} and its corresponding tab in the sheet.\n\n"
            f"This will:\n"
            f"- Archive the channel contents\n"
            f"- Delete the Discord channel\n"
            f"- Delete the tab from the Google Sheet\n"
            f"- Remove the entry from the Overview sheet\n\n"
            f"React with ✅ to confirm or ❌ to cancel.",
        )

        confirm_emoji = hydra_constants.CONFIRM_EMOJI
        cancel_emoji = hydra_constants.CANCEL_EMOJI

        confirm_message = (await discord_utils.send_message(ctx, confirm_embed))[0]
        await confirm_message.add_reaction(confirm_emoji)
        await confirm_message.add_reaction(cancel_emoji)

        def check_correct_react(reaction, user):
            return (
                user == ctx.author
                and reaction.message.id == confirm_message.id
                and str(reaction.emoji)
                in (
                    hydra_constants.CONFIRM_EMOJI,
                    hydra_constants.CANCEL_EMOJI,
                )
            )

        try:
            reaction, _ = await self.bot.wait_for(
                "reaction_add",
                timeout=hydra_constants.DELETE_CONFIRM_TIMEOUT,
                check=check_correct_react,
            )
        except asyncio.TimeoutError:
            timeout_embed = discord_utils.create_embed()
            timeout_embed.add_field(
                name="Cancelled!",
                value="No confirmation received in time. "
                f"{target_channel.mention} will not deleted.",
                inline=False,
            )
            await discord_utils.send_message(ctx, timeout_embed)
            return

        # If the user reacted with the cancel emoji, abort immediately.
        if str(reaction.emoji) == hydra_constants.CANCEL_EMOJI:
            cancel_embed = discord_utils.create_embed()
            cancel_embed.add_field(
                name="Aborted!",
                value=f"Deletion aborted. {target_channel.mention} will not be deleted.",
                inline=False,
            )
            await discord_utils.send_message(ctx, cancel_embed)
            return

        # Proceed with deletehydra

        async with self.lock:
            progress_embed = discord_utils.create_embed()
            progress_embed.add_field(
                name="Deletion in Progress",
                value=f"Deleting channel {target_channel.mention} and its corresponding tab. Please wait...",
                inline=False,
            )
            progress_msg = (await discord_utils.send_message(ctx, progress_embed))[0]

            try:
                # 1. Archive channel first
                archive_cmd = self.bot.get_command("archivechannel")
                if archive_cmd:
                    await ctx.invoke(archive_cmd, target_channel.mention)
                else:
                    # Fallback
                    fallback_embed = discord_utils.create_embed()
                    fallback_embed.add_field(
                        name="Failed",
                        value="Could not find archivechannel command. Continuing without archiving.",
                        inline=False,
                    )
                    await discord_utils.send_message(ctx, fallback_embed)

                # 2. Get overview and find the row for this channel
                overview_sheet = await hydra_sheet_utils.get_overview(
                    self.gspread_client, ctx, curr_sheet_link
                )

                tab_name = None
                row_to_find = None
                overview_ws = None
                tab_name_found = False

                if overview_sheet is not None:
                    # We need to find the row by channel ID
                    list_chan_cells = await hydra_sheet_utils.findchanidcell(
                        self.gspread_client,
                        ctx,
                        curr_sheet_link,
                        [target_channel.id],
                    )

                    if list_chan_cells and list_chan_cells[0][0] is not None:
                        row_to_find = list_chan_cells[0][0]
                        overview_ws = overview_sheet.worksheet

                        # Get tab name from the appropriate column
                        # Get the cell formula from column D
                        try:
                            tab_name = overview_ws.acell(
                                f"D{row_to_find}"
                            ).value  # FIXME - hardcoded
                            tab_name_found = True
                        except gspread.exceptions.APIError:
                            tab_name_found = False

                # 3. Delete discord channel
                channel_name = target_channel.name
                await target_channel.delete(
                    reason=f"Deleted by {ctx.author} via `~deletehydra` command."
                )

                # 4. Delete tab from sheet (skip if tab name wasn't found anyway)
                if tab_name_found and tab_name:
                    tab_deleted = False
                    try:
                        sh = self.gspread_client.open_by_url(curr_sheet_link)

                        # Try to find and delete worksheet
                        ws_to_delete = None
                        if tab_name:
                            ws_to_delete = next(
                                (ws for ws in sh.worksheets() if ws.title == tab_name),
                                None,
                            )

                        if ws_to_delete:
                            sh.del_worksheet(ws_to_delete)
                            tab_deleted = True
                    except gspread.exceptions.APIError:  # Report in final message
                        pass
                    except Exception:
                        pass

                # 5. Delete overview row
                row_moved = False
                if overview_sheet is not None and row_to_find is not None:
                    try:
                        overview_ws = overview_sheet.worksheet

                        # Get the row values
                        row_values = overview_ws.row_values(row_to_find)

                        if row_values:
                            overview_ws.delete_rows(row_to_find)
                            # A new row probably should be created here, but
                            # the filter on the overview sheet doesnt apply
                            # properly, so we'll just trust the users good
                            # judgement to add more rows manually

                            row_moved = True

                    except gspread.exceptions.APIError:  # Report in final message
                        pass
                    except Exception:
                        pass

                # Delete progress message
                await progress_msg.delete()

                # 6. Send success message
                success_embed = discord_utils.create_embed()

                status_lines = []
                status_lines.append(
                    f"- ✅ Channel {channel_name} deleted successfully."
                )
                status_lines.append("- ✅ Archiving completed.")
                if tab_deleted:
                    status_lines.append(f"- ✅ Tab '{tab_name}' deleted from sheet.")
                else:
                    status_lines.append(
                        f"- ❌ Failed to delete tab '{tab_name}' from sheet."
                    )

                if row_moved:
                    status_lines.append("- ✅ Overview row deleted.")
                else:
                    status_lines.append("- ❌ Failed to delete overview row.")

                success_embed.add_field(
                    name="Report of deletion",
                    value="\n".join(status_lines),
                    inline=False,
                )

                await ctx.message.add_reaction(emoji.emojize(":check_mark_button:"))
                await discord_utils.send_message(ctx, success_embed)

            except gspread.exceptions.APIError as e:
                await hydra_helpers.handle_gspread_error(ctx, e, embed)
            except nextcord.Forbidden:
                embed.add_field(
                    name="Failed",
                    value="I do not have permission to delete the channel.",
                    inline=False,
                )
                await discord_utils.send_message(ctx, embed)
            except Exception as e:
                embed.add_field(
                    name="Failed",
                    value=f"An unknown error occurred: {str(e)}",
                    inline=False,
                )
                await discord_utils.send_message(ctx, embed)

    @command_predicates.is_solver()
    @commands.command(
        name="watchcategoryhydra",
        aliases=["watchcathydra", "watchcat", "watchcategory"],
    )
    async def watchcategoryhydra(self, ctx, *args):
        """Summarise the last `limit` messages across one or more categories:
        `limit` caps off at 250.
        Note: Will pick up messages to which the command user does not have access to.
        Only counts messages from humans (not bots).

        Permission Category : Solver Roles only.
        Usage: `~watchcategoryhydra [category names] [limit]`
        Usage: `~watchcategoryhydra` (current category, limit 100)
        Usage: `~watchcategoryhydra 50` (current category, limit 50)
        Usage: `~watchcategoryhydra "Cat 1" "Cat 2"` (multiple categories, limit 100)
        Usage: `~watchcategoryhydra "Cat 1" "Cat 2" 50` (multiple categories, limit 50)
        """

        await logging_utils.log_command(
            "watchcategoryhydra", ctx.guild, ctx.channel, ctx.author
        )
        embed = discord_utils.create_embed()

        # Parse arguments
        limit = hydra_constants.WATCH_DEFAULT_LIMIT
        category_names = []

        if args:
            # Check if last arg is an integer (limit)
            try:
                limit = int(args[-1])
                category_names = list(args[:-1])
            except ValueError:
                # Last arg is not an integer, all args are category names
                category_names = list(args)

        if limit > hydra_constants.WATCH_MAX_LIMIT:
            limit = hydra_constants.WATCH_MAX_LIMIT

        # Determine which categories to watch
        categories = []
        if not category_names:
            # No categories specified, use current channel's category
            currcat = ctx.message.channel.category
            if currcat is None:
                embed.add_field(
                    name="Failed",
                    value="You must call this command from a channel in a category, or specify category names.",
                )
                await discord_utils.send_message(ctx, embed)
                return
            categories = [currcat]
        else:
            # Find each specified category
            for cat_name in category_names:
                cat = await discord_utils.find_category(ctx, cat_name)
                if cat is None:
                    embed.add_field(
                        name="Failed",
                        value=f"I cannot find category `{cat_name}`. Perhaps check your spelling and try again.",
                    )
                    await discord_utils.send_message(ctx, embed)
                    return
                categories.append(cat)

        start_embed = discord_utils.create_embed()
        cat_names = ", ".join([f"`{cat.name}`" for cat in categories])
        start_embed.add_field(
            name="Summary Started",
            value=f"Your summarizing of {len(categories)} categor{'ies' if len(categories) > 1 else 'y'} ({cat_names})"
            f" has begun! This may take a while. If I run into "
            f"any errors, I'll let you know.",
            inline=False,
        )

        start_msg = (await discord_utils.send_message(ctx, start_embed))[0]

        embed = discord_utils.create_embed()

        try:
            # 1. Fetch initial messages from each channel across categories given
            channel_histories = []
            for cat in categories:
                for ch in cat.text_channels:
                    try:
                        history = []
                        async for m in ch.history(
                            limit=hydra_constants.HISTORY_FETCH_LIMIT
                        ):
                            history.append(m)
                        if history:
                            channel_histories.append(
                                (ch, history, 0)
                            )  # (channel, messages, current_index)
                    except Exception:
                        # Skip channels we can't read
                        continue

            # 2. Initialize Min-Heap with the first message from each channel
            min_heap = []
            for ch, history, idx in channel_histories:
                if history:
                    msg = history[idx]
                    # Push (timestamp, channel_index, message) - using negative timestamp for max-heap behavior
                    heapq.heappush(
                        min_heap,
                        (-msg.created_at.timestamp(), len(min_heap), ch, history, idx),
                    )

            # 3. Extract human messages and non bot calls until we have enough
            msgs = []
            channel_indices = {ch: i for i, (ch, _, _) in enumerate(channel_histories)}

            while min_heap and len(msgs) < limit:
                # Get the most recent message
                _, _, ch, history, idx = heapq.heappop(min_heap)
                current_msg = history[idx]

                # Check if it's from a human (not a bot)
                if not current_msg.author.bot and not current_msg.content.startswith(
                    constants.DEFAULT_BOT_PREFIX
                ):
                    msgs.append(
                        (
                            current_msg.created_at,
                            ch,
                            current_msg.author,
                            current_msg.content,
                        )
                    )

                # Refill the heap from the same channel
                next_idx = idx + 1
                if next_idx < len(history):
                    next_msg = history[next_idx]
                    heapq.heappush(
                        min_heap,
                        (
                            -next_msg.created_at.timestamp(),
                            channel_indices.get(ch, 0),
                            ch,
                            history,
                            next_idx,
                        ),
                    )

        except Exception as e:
            embed.add_field(
                name="Failed",
                value=f"An error occurred while fetching messages. Error: {str(e)}",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return

        # Delete start message
        if start_msg:
            await start_msg.delete()

        # aggregate
        channel_counts = Counter()
        author_counts = Counter()
        for _, ch, author, _ in msgs:
            channel_counts[ch.mention] += 1
            author_counts[author.mention] += 1

        total = len(msgs)
        total_channels = sum(len(cat.text_channels) for cat in categories)
        embed.add_field(
            name="Summary",
            value=f"Analyzed {total} human messages across {total_channels} channels in {len(categories)} categor{'ies' if len(categories) > 1 else 'y'} ({cat_names}).",
            inline=False,
        )
        await discord_utils.send_message(ctx, embed)
        embed = discord_utils.create_embed()

        if channel_counts:
            ch_lines = [
                f"- {ch_mention}: {count} message{'s' if count != 1 else ''}"
                for ch_mention, count in channel_counts.most_common()
            ]
            embed.add_field(
                name="By channel",
                value="\n".join(ch_lines),
                inline=False,
            )
        await discord_utils.send_message(ctx, embed)
        embed = discord_utils.create_embed()

        if author_counts:
            author_lines = [
                f"- {author_mention}: {count} message{'s' if count != 1 else ''}"
                for author_mention, count in author_counts.most_common()
            ]
            embed.add_field(
                name="By author",
                value="\n".join(author_lines),
                inline=False,
            )

        await discord_utils.send_message(ctx, embed)

    @command_predicates.is_solver()
    @commands.command(name="slainhydra", aliases=["donehydra"])
    async def slainhydra(self, ctx, answer: str = None):
        """Runs `~solvedhydra` "ANSWER" then `~mtahydra`.

        Permission Category : Solver Roles only.
        Usage: `~slainhydra`
        Usage: `~slainhydra ANSWER`
        Usage: `~slainhydra "A MULTIWORD ANSWER"`
        """
        await logging_utils.log_command(
            "slainhydra", ctx.guild, ctx.channel, ctx.author
        )

        solvedhydra = self.bot.get_command("solvedhydra")
        mtahydra = self.bot.get_command("mtahydra")

        await ctx.invoke(solvedhydra, answer=answer)
        await ctx.invoke(mtahydra)

    @command_predicates.is_solver()
    @commands.command(name="backslainhydra")
    async def backslainhydra(self, ctx, answer: str = None):
        """Runs `~backsolvedhydra` "ANSWER" then `~mtahydra`.

        Permission Category : Solver Roles only.
        Usage: `~backslainhydra`
        Usage: `~backslainhydra ANSWER`
        Usage: `~backslainhydra "A MULTIWORD ANSWER"`
        """
        await logging_utils.log_command(
            "backslainhydra", ctx.guild, ctx.channel, ctx.author
        )

        backsolvedhydra = self.bot.get_command("backsolvedhydra")
        mtahydra = self.bot.get_command("mtahydra")

        await ctx.invoke(backsolvedhydra, answer=answer)
        await ctx.invoke(mtahydra)

    @command_predicates.is_solver()
    @commands.command(name="unmtahydra")
    async def unmtahydra(self, ctx: commands.Context, category_name: str = ""):
        """Does the rough opposite of ~mtahydra. Moves the channel into the main hunt category and moves the sheet into the active section.
        If I cannot find the main hunt category, I will ask the user to specify it.

        Permission Category : Solver Roles only.
        Usage: `~unmtahydra`
        Usage: `~unmtahydra "Main Hunt Category Name"` (If I cannot find the main hunt category automatically)
        """
        await logging_utils.log_command(
            "unmtahydra", ctx.guild, ctx.channel, ctx.author
        )

        base = SheetCommandBase(ctx, self.gspread_client)
        curr_sheet_link, overview_sheet, row_to_find = await base.get_sheet_context()

        if overview_sheet is None:
            return

        embed = discord_utils.create_embed()

        sheet_tab_id_col = sheets_constants.SHEET_TAB_ID_COLUMN
        try:
            overview_values = overview_sheet.overview_data
            _, col_idx = gspread.utils.a1_to_rowcol(sheet_tab_id_col + "1")
            sheet_tab_id = overview_values[row_to_find - 1][col_idx - 1]
        except Exception:
            embed.add_field(
                name="Failed",
                value=f"Could not find the Sheet Tab ID for channel {ctx.message.channel.mention} in the Overview sheet.",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return

        if ctx.channel.category is None:
            embed.add_field(
                name="Failed",
                value=f"The channel {ctx.message.channel.mention} is not in a category.",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return

        # Find the main hunt category. We will first check if an argument was passed. Then, look for a category tethered to the
        # same sheet. If that fails, we get the current category's name, and remove "Archive" and look for that. Else, we will
        # just ask the user for the category name.

        main_category = None

        if category_name != "":
            main_category = await discord_utils.find_category(ctx, category_name)
            if main_category is None:
                embed.add_field(
                    name="Failed",
                    value=f"I cannot find category `{category_name}`. Perhaps check your spelling and try again.",
                )
                await discord_utils.send_message(ctx, embed)
                return

        if main_category is None:
            for category in ctx.guild.categories:
                if category.id == ctx.channel.category.id:
                    continue  # Skip current category
                cat_result, _ = sheet_utils.findsheettether(str(category.id), None)
                if (
                    cat_result is not None
                    and str(cat_result.sheet_link) == curr_sheet_link
                ):
                    main_category = category
                    break

        if main_category is None:
            curr_cat_name = ctx.channel.category.name
            base_name = re.sub(r"\s*Archive\s*\d*$", "", curr_cat_name).strip()
            split_base_names = base_name.split()
            possible_category_prefixes = [
                " ".join(split_base_names[: len(split_base_names) - i])
                for i, _ in enumerate(split_base_names)
            ]

            possible_solving_categories = []
            # Look for categories that begin with the exact base name, then the bas name minus last word, etc.
            for possible_base_name in possible_category_prefixes:
                to_add_candidates = [
                    category
                    for category in ctx.guild.categories
                    if category.name.startswith(possible_base_name)
                    and not re.match(r".*Archive\s*\d*$", category.name)
                ]

                for candidate in to_add_candidates:
                    if candidate not in possible_solving_categories:
                        possible_solving_categories.append(candidate)

            if len(possible_solving_categories) == 1:
                main_category = possible_solving_categories[0]
            elif len(possible_solving_categories) > 1:
                # Collate list into embed so user can pick
                selection_embed = discord_utils.create_embed()
                selection_embed.add_field(
                    name="Multiple possible main hunt categories found",
                    value='Please specify which category to move the channel to by using `~unmtahydra "Category Name"`.\n\n'
                    + "\n".join(
                        [f"- {cat.name}" for cat in possible_solving_categories]
                    ),
                )
                await discord_utils.send_message(ctx, selection_embed)
                return

        if main_category is None:
            embed.add_field(
                name="Failed",
                value="I could not automatically find the main hunt category. \n"
                "Please specify the main hunt category name as an argument.",
            )
            await discord_utils.send_message(ctx, embed)
            return

        # Try to move the channel
        channel_embed = discord_utils.create_embed()
        try:
            await ctx.channel.edit(category=main_category)
            channel_embed.add_field(
                name="Success",
                value=f"Successfully moved channel {ctx.channel.mention} to category `{main_category.name}`.",
                inline=False,
            )
            await discord_utils.send_message(ctx, channel_embed)
        except nextcord.Forbidden:
            channel_embed.add_field(
                name="Failed",
                value=f"I do not have permission to move the channel {ctx.channel.mention} to category `{main_category.name}`.",
                inline=False,
            )
            await discord_utils.send_message(ctx, channel_embed)
            return
        except Exception as e:
            channel_embed.add_field(
                name="Failed",
                value=f"Could not move channel {ctx.channel.mention} to category `{main_category.name}`. Error: {str(e)}",
                inline=False,
            )
            await discord_utils.send_message(ctx, channel_embed)
            return

        # Move the sheet tab into the active section
        tab_embed = discord_utils.create_embed()
        try:
            curr_sheet = self.gspread_client.open_by_url(curr_sheet_link)

            # Find index by looking for last occurrence of a sheet ending with "Template".

            template_index = 0
            found_template = False
            for sheet in curr_sheet.worksheets():
                if sheet.title.endswith("Template"):
                    template_index = sheet.index
                    found_template = True
                else:
                    if found_template:
                        break  # We found the last template already

            if not found_template:
                template_index = 0  # Move to start if no templates found

            tab_to_move = curr_sheet.get_worksheet_by_id(int(sheet_tab_id))
            tab_to_move.update_index(template_index + 1)  # Move to after last template
            tab_embed.add_field(
                name="Success",
                value=f"Successfully moved the sheet tab for {ctx.channel.mention} to the active section.",
                inline=False,
            )
            await discord_utils.send_message(ctx, tab_embed)
        except gspread.exceptions.APIError as e:
            await hydra_helpers.handle_gspread_error(ctx, e, tab_embed)
            return
        except Exception as e:
            tab_embed.add_field(
                name="Failed",
                value=f"Unknown error when moving tab: `{str(e)}`",
                inline=False,
            )
            await discord_utils.send_message(ctx, tab_embed)
            return


def setup(bot):
    bot.add_cog(HydraCog(bot))
