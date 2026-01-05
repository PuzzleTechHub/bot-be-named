import asyncio
from typing import Union

import emoji
import gspread
import nextcord
from nextcord.ext import commands

import constants
from utils import (
    batch_update_utils,
    command_predicates,
    discord_utils,
    google_utils,
    logging_utils,
    sheet_utils,
    sheets_constants,
    solved_utils,
)

"""
Lion module. Module with GSheet-Discord interfacing. See module's README.md for more.
"""


class LionCog(commands.Cog, name="Lion"):
    """
    Useful GSheet-Discord commands.
    """

    def __init__(self, bot):
        self.bot = bot
        self.lock = asyncio.Lock()
        self.gdrive_credentials = google_utils.get_gdrive_credentials()
        self.gspread_client = google_utils.create_gspread_client()

    ################################
    # SOLVED COMMANDS WITHOUT LION #
    ################################

    @command_predicates.is_solver()
    @commands.command(name="solved", aliases=["solvedcrab"])
    async def solved(self, ctx: commands.Context):
        """Changes channel name to solved-<channel-name>

        Permission Category : Solver Roles only.
        Usage: `~solved`

        Note that if you use more than 2 channel renaming commands quickly, Discord automatically stops any more channel-name changes for 10 more minutes. Those channels will have to be renamed manually, or wait for the full 10 mins.
        """
        status = "Solved"
        status_prefix = sheets_constants.status_dict.get(status).get("prefix_name")
        embed = await solved_utils.status_channel(ctx, status_prefix)
        await discord_utils.send_message(ctx, embed)

    @command_predicates.is_solver()
    @commands.command(name="solvedish", aliases=["solvedishcrab"])
    async def solvedish(self, ctx: commands.Context):
        """Changes channel name to solvedish-<channel-name>

        Permission Category : Solver Roles only.
        Usage: `~solvedish`

        Note that if you use more than 2 channel renaming commands quickly, Discord automatically stops any more channel-name changes for 10 more minutes. Those channels will have to be renamed manually, or wait for the full 10 mins.
        """
        status = "Solvedish"
        status_prefix = sheets_constants.status_dict.get(status).get("prefix_name")
        embed = await solved_utils.status_channel(ctx, status_prefix)
        await discord_utils.send_message(ctx, embed)

    @command_predicates.is_solver()
    @commands.command(name="backsolved", aliases=["backsolvedcrab"])
    async def backsolved(self, ctx: commands.Context):
        """Changes channel name to backsolved-<channel-name>

        Permission Category : Solver Roles only.
        Usage: `~backsolved`

        Note that if you use more than 2 channel renaming commands quickly, Discord automatically stops any more channel-name changes for 10 more minutes. Those channels will have to be renamed manually, or wait for the full 10 mins.
        """
        status = "Backsolved"
        status_prefix = sheets_constants.status_dict.get(status).get("prefix_name")
        embed = await solved_utils.status_channel(ctx, status_prefix)
        await discord_utils.send_message(ctx, embed)

    @command_predicates.is_solver()
    @commands.command(name="unsolved", aliases=["unsolvedcrab"])
    async def unsolved(self, ctx: commands.context):
        """removes one of the solved prefixes from channel name

        Permission Category : Solver Roles only.
        Usage: `~unsolved`

        Note that if you use more than 2 channel renaming commands quickly, Discord automatically stops any more channel-name changes for 10 more minutes. Those channels will have to be renamed manually, or wait for the full 10 mins.
        """
        # log command in console
        await logging_utils.log_command("unsolved", ctx.guild, ctx.channel, ctx.author)
        embed = await solved_utils.status_remove(ctx)
        await discord_utils.send_message(ctx, embed)

    async def movetoarchive_generic(self, ctx: commands.Context, archive_name: str):
        embed = discord_utils.create_embed()
        # Handling if mta is called from a thread
        if await discord_utils.is_thread(ctx, ctx.channel):
            # Checking if thread can be archived by the bot
            try:
                await ctx.channel.edit(archived=True)
            except nextcord.Forbidden:
                embed.add_field(
                    name=f"{constants.FAILED}!",
                    value="Forbidden! Have you checked if the bot has the required permisisons?",
                )
                await discord_utils.send_message(ctx, embed)
                return
            embed.add_field(
                name=f"{constants.SUCCESS}!",
                value=f"Archived {ctx.channel.mention} thread",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            await ctx.channel.edit(archived=True)
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
                archive_category = await discord_utils.find_category(ctx, cand)
                if archive_category:
                    break

        else:
            archive_category = await discord_utils.find_category(ctx, archive_name)

        if archive_category is None:
            if archive_name is None:
                embed.add_field(
                    name=f"{constants.FAILED}!",
                    value=f"I can't find the archive, so I cannot move {ctx.channel.mention}. "
                    "I checked for the following categories: "
                    + ", ".join(f"`{c}`" for c in candidates),
                    inline=False,
                )
                await discord_utils.send_message(ctx, embed)
                return
            else:
                embed.add_field(
                    name=f"{constants.FAILED}!",
                    value=f"There is no category named `{archive_name}`, so I cannot move {ctx.channel.mention}.",
                    inline=False,
                )
                await discord_utils.send_message(ctx, embed)
                return

        if discord_utils.category_is_full(archive_category):
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"`{archive_category.name}` is already full, max limit is 50 channels. Consider renaming"
                f" `{archive_category.name}` and creating a new `{archive_category.name}`.",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return

        try:
            # move channel
            await ctx.channel.edit(category=archive_category)
            await ctx.channel.edit(position=1)
        except nextcord.Forbidden:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Can you check my permissions? I can't seem to be able to move "
                f"{ctx.channel.mention} to `{archive_category.name}`",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return

        embed.add_field(
            name=f"{constants.SUCCESS}!",
            value=f"Moved channel {ctx.channel.mention} to `{archive_category.name}`",
            inline=False,
        )
        await discord_utils.send_message(ctx, embed)

    @command_predicates.is_solver()
    @commands.command(name="mta", aliases=["movetoarchive", "mtacrab"])
    async def movetoarchive(self, ctx: commands.Context, archive_name: str = None):
        """Finds a category with `<category_name> Archive`, and moves the channel to that category.
        Fails if there is no such category, or is the category is full (i.e. 50 Channels).
        If called from thread (instead of channel), closes the thread instead of moving channel.

        Permission Category : Solver Roles only.
        Usage: `~mta`
        Usage: `~movetoarchive archive_category_name`
        """
        await logging_utils.log_command(
            "movetoarchive", ctx.guild, ctx.channel, ctx.author
        )
        await self.movetoarchive_generic(ctx, archive_name)

    #################
    # LION COMMANDS #
    #################

    ########################
    # LION STATUS COMMANDS #
    ########################

    async def get_overview(
        self, ctx: commands.Context, sheet_link: str
    ) -> sheet_utils.OverviewSheet | None:
        try:
            overview_sheet = sheet_utils.OverviewSheet(self.gspread_client, sheet_link)

        # Error when we can't open the curr sheet link
        except gspread.exceptions.APIError as e:
            error_json = e.response.json()
            error_status = error_json.get("error", {}).get("status")
            if error_status == "PERMISSION_DENIED":
                embed = discord_utils.create_embed()
                embed.add_field(
                    name=f"{constants.FAILED}",
                    value=f"I'm unable to open the tethered [sheet]({sheet_link}). "
                    f"Did the permissions change?",
                    inline=False,
                )
                await discord_utils.send_message(ctx, embed)
                return None
            else:
                raise e
        # Error when the sheet has no template tab
        except gspread.exceptions.WorksheetNotFound:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"The [sheet]({sheet_link}) has no tab named 'Overview'. "
                f"Did you forget to add one?",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return None

        return overview_sheet

    async def findchanidcell(self, ctx: commands.Context, sheet_link):
        """Find the cell with the discord channel id based on lion overview"""
        curr_chan_id = ctx.channel.id
        curr_sheet = None
        overview = None
        try:
            curr_sheet = self.gspread_client.open_by_url(sheet_link)
            overview = curr_sheet.worksheet("Overview")
        # Error when we can't open the curr sheet link
        except gspread.exceptions.APIError as e:
            error_json = e.response.json()
            error_status = error_json.get("error", {}).get("status")
            if error_status == "PERMISSION_DENIED":
                embed = discord_utils.create_embed()
                embed.add_field(
                    name=f"{constants.FAILED}",
                    value=f"I'm unable to open the tethered [sheet]({sheet_link}). "
                    f"Did the permissions change?",
                    inline=False,
                )
                await discord_utils.send_message(ctx, embed)
                return
            else:
                raise e
        # Error when the sheet has no template tab
        except gspread.exceptions.WorksheetNotFound:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"The [sheet]({sheet_link}) has no tab named 'Overview'. "
                f"Did you forget to add one?",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return

        curr_chan_or_cat_cell = None
        # Search first column for the channel
        curr_chan_or_cat_cell = overview.find(str(curr_chan_id), in_column=1)
        if curr_chan_or_cat_cell is None:
            # If there is no tether for the specific channel, check if there is one for the category.
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"I couldn't find the channel {ctx.channel.mention} in the sheet."
                f" Are you sure this channel is linked to a puzzle?",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)

        return curr_chan_or_cat_cell, overview

    @command_predicates.is_solver()
    @commands.command(name="gettablion", aliases=["tablion", "gettab"])
    async def gettablion(self, ctx: commands.Context):
        """Gets the tab linked to the current channel. Returns an error if there is not one.

        Also see ~sheetlion and ~displaytether.

        Permission Category : Solver Roles only.

        Usage: ~gettablion
        """
        await logging_utils.log_command(
            "gettablion", ctx.guild, ctx.channel, ctx.author
        )
        result, _ = sheet_utils.findsheettether(
            ctx.message.channel.category_id, ctx.message.channel.id
        )

        if result is None:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"Neither the category **{ctx.message.channel.category.name}** nor the channel {ctx.message.channel.mention} "
                f"are tethered to any Google sheet.",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return

        curr_sheet_link = str(result.sheet_link)
        overview_sheet = await self.get_overview(ctx, curr_sheet_link)
        if overview_sheet is None:
            return

        row_to_find, err_embed = overview_sheet.find_row_of_channel(ctx)
        if err_embed is not None:
            await discord_utils.send_message(ctx, err_embed)
            return

        tab_cell_label = sheets_constants.SHEET_TAB_ID_COLUMN + str(row_to_find)
        tab_id = overview_sheet.get_cell_value(tab_cell_label)

        final_link = curr_sheet_link + "/edit#gid=" + str(tab_id)

        embed = discord_utils.create_embed()

        embed.add_field(
            name=f"{constants.SUCCESS}",
            value=f"The tab linked to {ctx.message.channel.mention} is at [tab link]({final_link})",
            inline=False,
        )
        await discord_utils.send_message(ctx, embed)

    @command_predicates.is_solver()
    @commands.command(name="solvedlion")
    async def solvedlion(self, ctx: commands.Context, answer: str = None):
        """Sets the puzzle to solved and updates the sheet and channel name accordingly

        Permission Category : Solver Roles only.
        Usage: ~solvedlion
        Usage: ~solvedlion "answer"
        """
        await logging_utils.log_command(
            "solvedlion", ctx.guild, ctx.channel, str(ctx.author)
        )
        await self.statuslion(ctx, "solved", answer)

    @command_predicates.is_solver()
    @commands.command(name="backsolvedlion", aliases=["backlion"])
    async def backsolvedlion(self, ctx: commands.Context, answer: str = None):
        """Sets the puzzle to backsolved and updates the sheet and channel name accordingly

        Permission Category : Solver Roles only.
        Usage: ~backsolvedlion
        Usage: ~backsolvedlion "answer"
        """
        await logging_utils.log_command(
            "backsolvedlion", ctx.guild, ctx.channel, str(ctx.author)
        )
        await self.statuslion(ctx, "backsolved", answer)

    @command_predicates.is_solver()
    @commands.command(name="solvedishlion")
    async def solvedishlion(self, ctx: commands.Context, answer: str = None):
        """Sets the puzzle to solvedish and updates the sheet and channel name accordingly

        Permission Category : Solver Roles only.
        Usage: ~solvedishlion
        Usage: ~solvedishlion "answer"
        """
        await logging_utils.log_command(
            "solvedishlion", ctx.guild, ctx.channel, str(ctx.author)
        )
        await self.statuslion(ctx, "solvedish", answer)

    @command_predicates.is_solver()
    @commands.command(name="unsolvedlion", aliases=["unlion"])
    async def unsolvedlion(self, ctx: commands.Context, answer: str = ""):
        """Sets the puzzle to in progress and updates the sheet and channel name accordingly

        Permission Category : Solver Roles only.

        Usage: ~unsolvedlion (Removes the answer from the sheet)
        Usage: ~unsolvedlion "answer" (Updates the answer from the sheet to "answer")

        """
        await logging_utils.log_command(
            "unsolvedlion", ctx.guild, ctx.channel, str(ctx.author)
        )
        await self.statuslion(ctx, "In Progress", answer)

    @command_predicates.is_solver()
    @commands.command(name="statuslion", aliases=["statlion", "stat", "puzzstatus"])
    async def statuslion(self, ctx: commands.Context, status: str, answer: str = None):
        """Adds a status to the puzzle and updates the sheet and channel name accordingly

        You may pick one of [solved, solvedish, backsolved, postsolved, unstarted, unsolvable, stuck, abandoned, "In Progress"] as statuses.
        Alternatively, you can give a custom status.

        For statuses [solved, solvedish, postsolved, backsolved, "In Progress", custom] users have the option to add an answer
        For statuses  [solved, solvedish, backsolved, postsolved, "In Progress"] the channel name gets updated

        Permission Category : Solver Roles only.
        Usage: ~statuslion status
        Usage: ~statuslion solved "answer"
        Usage: ~statuslion "custom-update-string" "answer"
        """
        status = status.capitalize()
        if status == "In progress":
            status = "In Progress"
        embed = discord_utils.create_embed()

        try:
            status_info = sheets_constants.status_dict.get(status)

            # If something other than known strings (Custom status)
            if status_info is None:
                status_info = sheets_constants.status_dict.get("None")

            # Find tethered sheet
            result, _ = sheet_utils.findsheettether(
                str(ctx.message.channel.category_id), str(ctx.message.channel.id)
            )

            if result is None:
                embed.add_field(
                    name=f"{constants.FAILED}",
                    value=f"Neither the category **{ctx.message.channel.category.name}** nor the channel {ctx.message.channel.mention} "
                    f"are tethered to any Google sheet.",
                    inline=False,
                )
                await discord_utils.send_message(ctx, embed)
                return

            curr_sheet_link = str(result.sheet_link)
            overview_sheet = await self.get_overview(ctx, curr_sheet_link)
            if overview_sheet is None:
                return

            row_to_find, err_embed = overview_sheet.find_row_of_channel(ctx)
            if err_embed is not None:
                await discord_utils.send_message(ctx, err_embed)
                return

            status_col = overview_sheet.get_cell_value(
                sheets_constants.STATUS_COLUMN_LOCATION
            )

            tab_ans_loc = sheets_constants.TAB_ANSWER_LOCATION
            tab_cell_label = sheets_constants.SHEET_TAB_ID_COLUMN + str(row_to_find)
            tab_id = overview_sheet.get_cell_value(tab_cell_label)
            puzzle_tab = overview_sheet.spreadsheet.get_worksheet_by_id(int(tab_id))

            batch_update_builder = batch_update_utils.BatchUpdateBuilder()

            if answer is not None and status_info.get("update_ans"):
                batch_update_builder.update_cell_by_label(
                    puzzle_tab.id, tab_ans_loc, answer.upper()
                )
            elif not status_info.get("update_ans"):
                batch_update_builder.update_cell_by_label(
                    puzzle_tab.id, tab_ans_loc, ""
                )

            curr_status = overview_sheet.get_cell_value(status_col + str(row_to_find))
            curr_stat_info = sheets_constants.status_dict.get(curr_status)

            if curr_stat_info is None:
                curr_stat_info = sheets_constants.status_dict.get("None")

            batch_update_builder.update_cell_by_label(
                overview_sheet.worksheet.id, status_col + str(row_to_find), status
            )

            color = status_info.get("color")
            batch_update_builder.color_update(tab_id, color)

            try:
                overview_sheet.worksheet.spreadsheet.batch_update(
                    batch_update_builder.build()
                )
            except gspread.exceptions.APIError as e:
                error_json = e.response.json()
                error_status = error_json.get("error", {}).get("status")
                if error_status == "PERMISSION_DENIED":
                    embed.add_field(
                        name=f"{constants.FAILED}",
                        value="Could not update the sheet.",
                        inline=False,
                    )
                else:
                    raise e

            embed.add_field(
                name=f"{constants.SUCCESS}",
                value="The sheet was successfully updated.",
                inline=False,
            )

            add_prefix = status_info.get("prefix")
            past_prefix = curr_stat_info.get("prefix")

            if status == curr_status:
                await ctx.message.add_reaction(emoji.emojize(":check_mark_button:"))
                return

            if add_prefix:
                prefix_name = status_info.get("prefix_name")

            if past_prefix and not add_prefix:
                new_embed = await solved_utils.status_remove(ctx)
                embed = discord_utils.merge_embed(embed, new_embed)
            if add_prefix:
                new_embed = await solved_utils.status_channel(ctx, prefix_name)
                embed = discord_utils.merge_embed(embed, new_embed)

            await ctx.message.add_reaction(emoji.emojize(":check_mark_button:"))
            await discord_utils.send_message(ctx, embed)

        except gspread.exceptions.APIError as e:
            if hasattr(e, "response"):
                error_json = e.response.json()
                error_message = error_json.get("error", {}).get("message")
                embed.add_field(
                    name=f"{constants.FAILED}",
                    value=f"Unknown GSheets API Error - `{error_message}`",
                    inline=False,
                )
                await discord_utils.send_message(ctx, embed)
                return

    @command_predicates.is_solver()
    @commands.command(name="mtalion", aliases=["movetoarchivelion", "archivelion"])
    async def mtalion(self, ctx: commands.Context, archive_name: str = None):
        """Finds a category with `<category_name> Archive`, and moves the channel to that category.
        Fails if there is no such category, or is the category is full (i.e. 50 Channels).
        If called from thread (instead of channel), closes the thread instead of moving channel.

        Also moves the tab to the end of the list of tabs on the Google Sheet.

        Permission Category : Solver Roles only.
        Usage: `~mtalion`
        Usage: `~mtalion archive_category_name`
        """
        embed = discord_utils.create_embed()

        await logging_utils.log_command(
            "mtalion", ctx.guild, ctx.channel, str(ctx.author)
        )

        result, _ = sheet_utils.findsheettether(
            ctx.message.channel.category_id, ctx.message.channel.id
        )

        if result is None:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"Neither the category **{ctx.message.channel.category.name}** nor the channel {ctx.message.channel.mention} "
                f"are tethered to any Google sheet.",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return

        curr_sheet_link = str(result.sheet_link)
        overview_sheet = await self.get_overview(ctx, curr_sheet_link)
        if overview_sheet is None:
            return

        row_to_find, err_embed = overview_sheet.find_row_of_channel(ctx)
        if err_embed is not None:
            await discord_utils.send_message(ctx, err_embed)
            return

        sheet_tab_id_col = sheets_constants.SHEET_TAB_ID_COLUMN
        tab_id = overview_sheet.get_cell_value(sheet_tab_id_col + str(row_to_find))

        # Track sheet move success
        sheet_move_success = False
        sheet_move_error = None

        try:
            worksheets = overview_sheet.spreadsheet.worksheets()
            puzzle_tab = next((w for w in worksheets if w.id == int(tab_id)), None)

            if puzzle_tab is None:
                sheet_move_error = "Could not find puzzle tab in spreadsheet."
            else:
                puzzle_tab.update_index(len(worksheets))
                sheet_move_success = True
        except gspread.exceptions.APIError as e:
            error_json = e.response.json()
            error_message = error_json.get("error", {}).get("message")
            sheet_move_error = f"Google Sheets API Error: {error_message}"
        except StopIteration:
            sheet_move_error = "Could not find puzzle tab in spreadsheet."
        except Exception as e:
            sheet_move_error = f"Unknown error: {str(e)}"

        await self.movetoarchive_generic(ctx, archive_name) # Attempt to move channel regardless 

        if sheet_move_success:
            embed.add_field(
                name=f"{constants.SUCCESS}!",
                value="Moved sheet to the end of the spreadsheet!",
                inline=False,
            )
        else:
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"Failed to move sheet tab: {sheet_move_error}",
                inline=False,
            )

        await discord_utils.send_message(ctx, embed)

    ###############################
    # LION CHANNEL/SHEET CREATION #
    ###############################

    async def puzzlelion(
        self, ctx: commands.Context, chan_name, url, curr_sheet_link, newsheet, new_chan
    ):
        """Does the final touches on the sheet after creating a puzzle"""
        try:
            embed = discord_utils.create_embed()

            tab_name = chan_name.replace("#", "").replace("-", " ")

            sheet = self.gspread_client.open_by_url(curr_sheet_link)
            try:
                overview_sheet = await self.get_overview(ctx, curr_sheet_link)
            # Error when the sheet has no Overview tab
            except gspread.exceptions.WorksheetNotFound:
                embed.add_field(
                    name=f"{constants.FAILED}",
                    value=f"The [sheet]({curr_sheet_link}) has no tab named 'Overview'. "
                    f"Did you forget to add one?",
                    inline=False,
                )
                await discord_utils.send_message(ctx, embed)
                return

            if not overview_sheet:
                return

            overview_id = overview_sheet.worksheet.id
            first_empty = len(overview_sheet.overview_data) + 1

            discord_channel_id_col = sheets_constants.DISCORD_CHANNEL_ID_COLUMN
            sheet_tab_id_col = sheets_constants.SHEET_TAB_ID_COLUMN
            puzz_name_col = overview_sheet.get_cell_value(
                sheets_constants.PUZZLE_NAME_COLUMN_LOCATION
            )
            status_col = overview_sheet.get_cell_value(
                sheets_constants.STATUS_COLUMN_LOCATION
            )
            answer_col = overview_sheet.get_cell_value(
                sheets_constants.ANSWER_COLUMN_LOCATION
            )

            final_sheet_link = curr_sheet_link + "/edit#gid=" + str(newsheet.id)

            chan_name_for_sheet_ref = chan_name.replace("'", "''")
            batch_update_builder = batch_update_utils.BatchUpdateBuilder()

            batch_update_builder.update_cell_by_label(
                sheet_id=overview_id,
                label=puzz_name_col + str(first_empty),
                value=f'=HYPERLINK("{final_sheet_link}", "{chan_name}")',
                is_formula=True,
            )

            batch_update_builder.update_cell_by_label(
                sheet_id=overview_id,
                label=discord_channel_id_col + str(first_empty),
                value=str(new_chan.id),
            )

            batch_update_builder.update_cell_by_label(
                sheet_id=overview_id,
                label=sheet_tab_id_col + str(first_empty),
                value=str(newsheet.id),
            )

            unstarted = sheets_constants.UNSTARTED_NAME
            batch_update_builder.update_cell_by_label(
                sheet_id=overview_id,
                label=status_col + str(first_empty),
                value=unstarted,
            )

            batch_update_builder.unhide_sheet(sheet_id=newsheet.id)

            chan_name_for_sheet_ref = tab_name.replace("'", "''")
            tab_ans_loc = sheets_constants.TAB_ANSWER_LOCATION
            chan_name_loc = sheets_constants.TAB_CHAN_NAME_LOCATION
            url_loc = sheets_constants.TAB_URL_LOCATION

            batch_update_builder.update_cell_by_label(
                sheet_id=overview_id,
                label=answer_col + str(first_empty),
                value=f"='{chan_name_for_sheet_ref}'!{tab_ans_loc}",
                is_formula=True,
            )

            batch_update_builder.update_cell_by_label(
                sheet_id=newsheet.id, label=chan_name_loc, value=chan_name
            )
            if url:
                batch_update_builder.update_cell_by_label(
                    sheet_id=newsheet.id, label=url_loc, value=url
                )

            sheet.batch_update(batch_update_builder.build())

            await ctx.message.add_reaction(emoji.emojize(":check_mark_button:"))
        except gspread.exceptions.APIError as e:
            if hasattr(e, "response"):
                error_json = e.response.json()
                error_message = error_json.get("error", {}).get("message")
                embed.add_field(
                    name=f"{constants.FAILED}",
                    value=f"Unknown GSheets API Error - `{error_message}`",
                    inline=False,
                )
                await discord_utils.send_message(ctx, embed)
                return

    @command_predicates.is_solver()
    @commands.command(name="chanlion")
    async def chanlion(self, ctx: commands.Context, chan_name: str, *args):
        """Creates a new tab and a new channel for a new feeder puzzle and then updates the info in the sheet accordingly.

        Requires that the sheet has Overview and Template tabs

        Permission Category : Solver Roles only.
        Usage: ~chanlion "Puzzle Name"
        Usage: ~chanlion PuzzleName "http://www.linktopuzzle.com"
        """
        await logging_utils.log_command("chanlion", ctx.guild, ctx.channel, ctx.author)

        curr_sheet_link, newsheet, new_chan = None, None, None
        text_to_pin = " ".join(args)

        curr_sheet_link, newsheet, new_chan = await sheet_utils.chancrabgeneric(
            self.gspread_client,
            ctx,
            chan_name,
            chan_type="chan",
            is_meta=False,
            text_to_pin=text_to_pin,
        )

        if curr_sheet_link is None or newsheet is None or new_chan is None:
            return

        await self.puzzlelion(
            ctx, chan_name, text_to_pin, curr_sheet_link, newsheet, new_chan
        )

    @command_predicates.is_solver()
    @commands.command(name="metalion", aliases=["metachanlion"])
    async def metalion(self, ctx: commands.Context, chan_name: str, *args):
        """Creates a new tab and a new channel for a new metapuzzle and then updates the info in the sheet accordingly.

        Requires that the sheet has Overview and Meta Template tabs

        Permission Category : Solver Roles only.
        Usage: ~metalion PuzzleName
        Usage: ~metalion PuzzleName linktopuzzle
        """
        await logging_utils.log_command("metalion", ctx.guild, ctx.channel, ctx.author)

        curr_sheet_link, newsheet, new_chan = None, None, None
        text_to_pin = " ".join(args)

        curr_sheet_link, newsheet, new_chan = await sheet_utils.chancrabgeneric(
            self.gspread_client,
            ctx,
            chan_name,
            chan_type="chan",
            is_meta=True,
            text_to_pin=text_to_pin,
        )

        if curr_sheet_link is None or newsheet is None or new_chan is None:
            return

        await self.puzzlelion(
            ctx, chan_name, text_to_pin, curr_sheet_link, newsheet, new_chan
        )

    @command_predicates.is_solver()
    @commands.command(name="threadlion")
    async def threadlion(self, ctx: commands.Context, chan_name: str, *args):
        """Creates a new tab and a new thread for a new feeder puzzle and then updates the info in the sheet accordingly.

        Requires that the sheet has Overview and Template tabs

        Permission Category : Solver Roles only.
        Usage: ~threadlion PuzzleName
        Usage: ~threadlion PuzzleName linktopuzzle
        """
        await logging_utils.log_command(
            "threadlion", ctx.guild, ctx.channel, ctx.author
        )

        curr_sheet_link, newsheet, new_chan = None, None, None
        text_to_pin = " ".join(args)

        curr_sheet_link, newsheet, new_chan = await sheet_utils.chancrabgeneric(
            self.gspread_client,
            ctx,
            chan_name,
            chan_type="thread",
            is_meta=False,
            text_to_pin=text_to_pin,
        )

        if curr_sheet_link is None or newsheet is None or new_chan is None:
            return

        await self.puzzlelion(
            ctx, chan_name, text_to_pin, curr_sheet_link, newsheet, new_chan
        )

    @command_predicates.is_solver()
    @commands.command(name="metathreadlion")
    async def metathreadlion(self, ctx: commands.Context, chan_name: str, *args):
        """Creates a new tab and a new thread for a new metapuzzle and then updates the info in the sheet accordingly.

        Requires that the sheet has Overview and Meta Template tabs

        Permission Category : Solver Roles only.
        Usage: ~metathreadlion PuzzleName
        Usage: ~metathreadlion PuzzleName linktopuzzle
        """
        await logging_utils.log_command(
            "metathreadlion", ctx.guild, ctx.channel, ctx.author
        )

        curr_sheet_link, newsheet, new_chan = None, None, None
        text_to_pin = " ".join(args)

        curr_sheet_link, newsheet, new_chan = await sheet_utils.chancrabgeneric(
            self.gspread_client,
            ctx,
            chan_name,
            chan_type="thread",
            is_meta=True,
            text_to_pin=text_to_pin,
        )

        if curr_sheet_link is None or newsheet is None or new_chan is None:
            return

        await self.puzzlelion(
            ctx, chan_name, text_to_pin, curr_sheet_link, newsheet, new_chan
        )

    @command_predicates.is_solver()
    @commands.command(name="forumlion")
    async def forumlion(self, ctx: commands.Context, chan_name: str, *args):
        """Creates a new tab and a new forum post for a new feeder puzzle and then updates the info in the sheet accordingly.

        Requires that the sheet has Overview and Template tabs. Works only from within a forum post.

        Permission Category : Solver Roles only.
        Usage: ~forumlion PuzzleName
        Usage: ~forumlion PuzzleName linktopuzzle
        """
        await logging_utils.log_command("forumlion", ctx.guild, ctx.channel, ctx.author)

        curr_sheet_link, newsheet, new_chan = None, None, None
        text_to_pin = " ".join(args)

        curr_sheet_link, newsheet, new_chan = await sheet_utils.chancrabgeneric(
            self.gspread_client,
            ctx,
            chan_name,
            chan_type="forum",
            is_meta=False,
            text_to_pin=text_to_pin,
        )

        if curr_sheet_link is None or newsheet is None or new_chan is None:
            return

        await self.puzzlelion(
            ctx, chan_name, text_to_pin, curr_sheet_link, newsheet, new_chan
        )

    @command_predicates.is_solver()
    @commands.command(name="metaforumlion")
    async def metaforumlion(self, ctx: commands.Context, chan_name: str, *args):
        """Creates a new tab and a new forum post for a new metapuzzle and then updates the info in the sheet accordingly.

        Requires that the sheet has Overview and Meta Template tabs. Works only from within a forum post.

        Permission Category : Solver Roles only.
        Usage: ~metaforumlion PuzzleName
        Usage: ~metaforumlion PuzzleName linktopuzzle
        """
        await logging_utils.log_command(
            "metaforumlion", ctx.guild, ctx.channel, ctx.author
        )

        curr_sheet_link, newsheet, new_chan = None, None, None
        text_to_pin = " ".join(args)

        curr_sheet_link, newsheet, new_chan = await sheet_utils.chancrabgeneric(
            self.gspread_client,
            ctx,
            chan_name,
            chan_type="forum",
            is_meta=True,
            text_to_pin=text_to_pin,
        )

        if curr_sheet_link is None or newsheet is None or new_chan is None:
            return

        await self.puzzlelion(
            ctx, chan_name, text_to_pin, curr_sheet_link, newsheet, new_chan
        )

    @command_predicates.is_solver()
    @commands.command(name="sheetlion")
    async def sheetlion(self, ctx: commands.Context, tab_name: str, url: str = None):
        """Creates a new tab for a new feeder puzzle and then updates the info in the sheet accordingly.

        Requires that the sheet has Overview and Template tabs

        Permission Category : Solver Roles only.
        Usage: ~sheetlion PuzzleName
        Usage: ~sheetlion PuzzleName linktopuzzle
        """
        await logging_utils.log_command("sheetlion", ctx.guild, ctx.channel, ctx.author)

        curr_sheet_link, newsheet = await sheet_utils.sheetcrabgeneric(
            self.gspread_client, ctx, tab_name, False
        )

        # Error, already being handled at the generic function
        if not curr_sheet_link or newsheet is None:
            return

        await self.puzzlelion(
            ctx, tab_name, url, curr_sheet_link, newsheet, ctx.channel
        )

    @command_predicates.is_solver()
    @commands.command(name="metasheetlion")
    async def metasheetlion(
        self, ctx: commands.Context, tab_name: str, url: str = None
    ):
        """Creates a new tab for a new metapuzzle and then updates the info in the sheet accordingly.

        Requires that the sheet has Overview and Meta Template tabs

        Permission Category : Solver Roles only.
        Usage: ~metasheetlion PuzzleName
        Usage: ~metasheetlion PuzzleName linktopuzzle
        """
        await logging_utils.log_command(
            "metasheetlion", ctx.guild, ctx.channel, ctx.author
        )

        curr_sheet_link, newsheet = None, None

        curr_sheet_link, newsheet = await sheet_utils.sheetcrabgeneric(
            self.gspread_client, ctx, tab_name, True
        )

        # Error, already being handled at the generic function
        if curr_sheet_link is None or newsheet is None:
            return

        await self.puzzlelion(
            ctx, tab_name, url, curr_sheet_link, newsheet, ctx.channel
        )

    ##########################
    # LION TEMPLATE COMMANDS #
    ##########################

    async def validate_template(self, ctx: commands.Context, proposed_sheet):
        embed = discord_utils.create_embed()

        proposed_template = sheet_utils.get_sheet_from_key_or_link(
            self.gspread_client, proposed_sheet
        )

        if not proposed_template:
            embed.add_field(
                name=f"{constants.FAILED}",
                value="Sorry, we can't find a sheet there. "
                "Did you forget to set your sheet as 'Anyone with the link can edit'?",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return None

        curr_link = proposed_template.url

        # Make sure the template tab exists on the sheet.
        try:
            curr_sheet = self.gspread_client.open_by_url(curr_link)
            _template_id = curr_sheet.worksheet("Template").id
        # Error when we can't open the curr sheet link
        except gspread.exceptions.APIError as e:
            error_json = e.response.json()
            error_status = error_json.get("error", {}).get("status")
            if error_status == "PERMISSION_DENIED":
                embed = discord_utils.create_embed()
                embed.add_field(
                    name=f"{constants.FAILED}",
                    value=f"I'm unable to open the tethered [sheet]({curr_link}). "
                    f"Did the permissions change?",
                    inline=False,
                )
                await discord_utils.send_message(ctx, embed)
                return None
            else:
                raise e
        # Error when the sheet has no template tab
        except gspread.exceptions.WorksheetNotFound:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"The [sheet]({curr_link}) has no tab named 'Template'. "
                f"Did you forget to add one?",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return None

        # Make sure the Meta Template tab exists on the sheet.
        try:
            curr_sheet = self.gspread_client.open_by_url(curr_link)
            _overview_id = curr_sheet.worksheet("Meta Template").id
        # Error when the sheet has no Meta Template tab
        except gspread.exceptions.WorksheetNotFound:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"The [sheet]({curr_link}) has no tab named 'Meta Template'. "
                f"Did you forget to add one?",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return None

        # Make sure the Overview tab exists on the sheet.
        try:
            curr_sheet = self.gspread_client.open_by_url(curr_link)
            _overview_id = curr_sheet.worksheet("Overview").id
        # Error when the sheet has no Overview tab
        except gspread.exceptions.WorksheetNotFound:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"The [sheet]({curr_link}) has no tab named 'Overview'. "
                f"Did you forget to add one?",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return None

        return proposed_template

    ######################
    # LION HUNT COMMANDS #
    ######################

    # @command_predicates.is_verified()
    # @commands.command(
    #    name="huntlion",
    # )
    async def huntlion(
        self,
        ctx: commands.Context,
        hunt_team_name: str,
        hunturl: str,
        rolename_or_folderurl: Union[nextcord.Role, str] = None,
        folderurl: str = None,
    ):
        """Clone the template and names the new sheet into a new category named huntteamname.

        This new category will have 3 premade channels: #huntteamname-main and #huntteamname-bot-spam and #huntteamname-vc

        The category will only be visible to those with the role rolename.

        Also tethers the new sheet to the category.

        Useful when we want to make a new hunt team.

        For any lion commands, a tether using either ~clonelion or ~huntlion is necessary.

        Requires that role does not have "folder/" inside the role name

        Permission Category : Verified Roles only.
        Usage: ~huntlion SheetName hunturl
        Usage: ~huntlion SheetName hunturl role
        Usage: ~huntlion SheetName hunturl role folderurl
        Usage: ~huntlion SheetName hunturl folderurl
        """
        await logging_utils.log_command(
            "huntlion", ctx.guild, ctx.channel, str(ctx.author)
        )

        f_url = folderurl
        roleName = None
        if folderurl is None:
            if (
                isinstance(rolename_or_folderurl, str)
                and len(rolename_or_folderurl.split("folders/")) == 2
            ):
                f_url = rolename_or_folderurl
            else:
                roleName = rolename_or_folderurl
        else:
            roleName = rolename_or_folderurl

        try:
            await ctx.guild.create_category(hunt_team_name)
            cat = await discord_utils.find_category(ctx, hunt_team_name)
            if cat is None:
                embed = discord_utils.create_embed()
                embed.add_field(
                    name=f"{constants.FAILED}!",
                    value="Error! The hunt category was not correctly created.",
                )
                # reply to user
                await discord_utils.send_message(ctx, embed)
                return

            if roleName:
                role_to_allow = await discord_utils.find_role(ctx, roleName)

                if role_to_allow is None:
                    role_to_allow = await ctx.guild.create_role(name=roleName)
                    embed = discord_utils.create_embed()
                    embed.add_field(
                        name=f"Created role {roleName}",
                        value=f"Could not find role `{roleName}`, so I created it.",
                        inline=False,
                    )
                    await discord_utils.send_message(ctx, embed)

                await cat.set_permissions(
                    role_to_allow,
                    read_messages=True,
                    send_messages=True,
                    connect=True,
                    speak=True,
                )
                await cat.set_permissions(
                    ctx.guild.default_role, read_messages=False, connect=False
                )

            await discord_utils.createchannelgeneric(
                ctx.guild, cat, hunt_team_name + " main"
            )
            await discord_utils.createchannelgeneric(
                ctx.guild, cat, hunt_team_name + " bot spam"
            )
            await discord_utils.createvoicechannelgeneric(
                ctx.guild, cat, hunt_team_name + " VC"
            )
        except nextcord.Forbidden:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value="Forbidden! Have you checked if the bot has the required permisisons?",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return

        channel_list = cat.channels
        channels = [f"{chan.mention}" for chan in channel_list]
        embed = discord_utils.create_embed()
        embed.add_field(
            name=f"{constants.SUCCESS}!",
            value="The hunt category was created.",
            inline=False,
        )
        embed.add_field(name=f"Channels in {cat}", value=f"{chr(10).join(channels)}")
        await discord_utils.send_message(ctx, embed)

        new_sheet = await self.clonetemplatelion(ctx, hunt_team_name, f_url)
        if new_sheet is None:
            return

        if await self.validate_template(ctx, new_sheet.url) is None:
            return

        proposed_sheet = sheet_utils.addsheettethergeneric(
            self.gspread_client, new_sheet.url, ctx.guild, cat
        )

        if proposed_sheet:
            new_embed = discord_utils.create_embed()
            new_embed.add_field(
                name=f"{constants.SUCCESS}!",
                value=f"The category **{cat.name}** is now tethered to the "
                f"[Google sheet at link]({proposed_sheet.url})",
                inline=False,
            )
            await discord_utils.send_message(ctx, new_embed)
        # If we can't open the sheet, send an error and return
        else:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}!",
                value="Sorry, we can't find a sheet there. "
                "Did you forget to set your sheet as 'Anyone with the link can edit'?",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return

        if await self.initoverview(ctx, hunturl, new_sheet):
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.SUCCESS}!",
                value="The sheet is now set up for use",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)

    # @command_predicates.is_verified()
    # @commands.command(name="clonelion")
    async def clonelion(
        self,
        ctx: commands.Context,
        huntroundname: str,
        hunturl: str,
        folderurl: str = None,
    ):
        """Clone the template and names the new sheet. Also tethers the new sheet to the category.

        Useful when we want to make a new sheet for a new set of rounds.

        For any lion commands, a tether using either ~clonelion or ~huntlion is necessary.

        Permission Category : Verified Roles only.
        Usage: ~clonelion SheetName hunturl
        Usage: ~clonelion SheetName hunturl folderurl
        """
        await logging_utils.log_command(
            "clonelion", ctx.guild, ctx.channel, str(ctx.author)
        )

        new_sheet = await self.clonetemplatelion(ctx, huntroundname, folderurl)
        if new_sheet is None:
            return

        await self.tetherlion(ctx, new_sheet.url)
        if await self.initoverview(ctx, hunturl, new_sheet):
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.SUCCESS}!",
                value="The sheet is now set up for use",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)

    async def initoverview(self, ctx, hunturl, sheet):
        """Initializes the overview sheet for the hunt."""
        overview = None

        try:
            overview = sheet.worksheet("Overview")
        # Error when the sheet has no Overview tab
        except gspread.exceptions.WorksheetNotFound:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"The [sheet]({overview.url}) has no tab named 'Overview'. "
                f"Did you forget to add one?",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return None

        overview_hunturl_loc = sheets_constants.OVERVIEW_HUNTURL_LOCATION
        overview.update_acell(label=overview_hunturl_loc, value=hunturl)
        return True

    # @command_predicates.is_verified()
    # @commands.command(
    #    name="clonetemplatelion",
    #    aliases=["clonetemplate", "clonetemp", "clonetemplion"],
    # )
    async def clonetemplatelion(
        self, ctx: commands.Context, newname, folderurl: str | None = None
    ):
        """Clones the template and names the new sheet

        For developers: also returns the cloned sheet

        Permission Category : Verified Roles only.
        Usage: ~clonetemplatelion SheetName
        """
        await logging_utils.log_command(
            "clonetemplatelion", ctx.guild, ctx.channel, ctx.author
        )
        embed = discord_utils.create_embed()

        result = self.findtemplate(ctx)

        if result is None:
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"This server **{ctx.guild.name}** does not have a template Google Sheet.",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return None

        f_id = ""

        if folderurl:
            try:
                f_id = folderurl.split("folders/")[1]
            except IndexError:
                f_id = ""

        sheet = result.sheet_link
        curr_sheet = self.gspread_client.open_by_url(sheet)

        new_sheet = ""

        try:
            new_sheet = self.gspread_client.copy(
                file_id=curr_sheet.id,
                title=newname,
                copy_permissions=True,
                folder_id=(f_id or None),
            )
        except gspread.exceptions.APIError:
            embed.add_field(
                name=f"{constants.FAILED}",
                value="Invalid folder. Please check to see that you have the correct link and permissions.",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return None

        if f_id:
            embed.add_field(
                name=f"{constants.SUCCESS}!",
                value=f"Cloned sheet located at [sheet link]({new_sheet.url}) "
                f"in folder [GDrive folder link]({folderurl})",
                inline=False,
            )
        else:
            embed.add_field(
                name=f"{constants.SUCCESS}!",
                value=f"Cloned sheet located at [sheet link]({new_sheet.url})",
                inline=False,
            )

        await discord_utils.send_message(ctx, embed)
        return new_sheet

    @command_predicates.is_solver()
    @commands.command(name="tetherlion")
    async def tetherlion(self, ctx, sheet_key_or_link: str):
        """Tethers a sheet to the category and also checks that it is the correct format to be used by the lion commands

        Sheet must have the following tabs: Overview, Template, Meta Template

        Usage: ~tetherlion sheeturl
        """
        await logging_utils.log_command(
            "tetherlion", ctx.guild, ctx.channel, ctx.author
        )
        embed = discord_utils.create_embed()

        if await self.validate_template(ctx, sheet_key_or_link) is None:
            return

        proposed_sheet = sheet_utils.addsheettethergeneric(
            self.gspread_client, sheet_key_or_link, ctx.guild, ctx.channel.category
        )

        if proposed_sheet:
            embed.add_field(
                name=f"{constants.SUCCESS}!",
                value=f"The category **{ctx.channel.category.name}** is now tethered to the "
                f"[Google sheet at link]({proposed_sheet.url})",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
        # If we can't open the sheet, send an error and return
        else:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value="Sorry, we can't find a sheet there. "
                "Did you forget to set your sheet as 'Anyone with the link can edit'?",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return


def setup(bot):
    bot.add_cog(LionCog(bot))
