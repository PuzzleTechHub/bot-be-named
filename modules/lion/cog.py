import constants
import nextcord
import gspread
import asyncio
import emoji
from nextcord.ext import commands
from typing import Union
from utils import (
    batch_update_utils,
    discord_utils,
    google_utils,
    logging_utils,
    command_predicates,
    sheets_constants,
)
from utils import sheet_utils
from utils import solved_utils

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

    async def movetoarchive_generic(self, ctx, archive_name: str):
        embed = discord_utils.create_embed()
        # Handling if mta is called from a thread
        if await discord_utils.is_thread(ctx, ctx.channel):
            # Checking if thread can be archived by the bot
            try:
                await ctx.channel.edit(archived=True)
            except nextcord.Forbidden:
                embed.add_field(
                    name=f"{constants.FAILED}!",
                    value=f"Forbidden! Have you checked if the bot has the required permisisons?",
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
        if archive_name is None:
            # Find category with same name + Archive (or select combinations)
            archive_category = (
                await discord_utils.find_category(
                    ctx, f"{ctx.channel.category.name} Archive"
                )
                or await discord_utils.find_category(
                    ctx, f"Archive: {ctx.channel.category.name}"
                )
                or await discord_utils.find_category(
                    ctx, f"{ctx.channel.category.name} archive"
                )
            )
        else:
            archive_category = await discord_utils.find_category(ctx, archive_name)

        if archive_category is None:
            if archive_name is None:
                embed.add_field(
                    name=f"{constants.FAILED}!",
                    value=f"There is no category named `{ctx.channel.category.name} Archive` or "
                    f"`Archive: {ctx.channel.category.name}`, so I cannot move {ctx.channel.mention}.",
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
    async def movetoarchive(self, ctx, archive_name: str = None):
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

    async def findchanidcell(self, ctx, sheet_link):
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
    async def gettablion(self, ctx):
        """Gets the tab linked to the current channel. Returns an error if there is not one.

        Also see ~sheetlion and ~displaytether.

        Permission Category : Solver Roles only.

        Usage: ~gettablion
        """
        await logging_utils.log_command(
            "gettablion", ctx.guild, ctx.channel, ctx.author
        )
        result, _ = sheet_utils.findsheettether(
            str(ctx.message.channel.category_id), str(ctx.message.channel.id)
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

        curr_sheet_link = result.sheet_link
        chan_cell, overview = None, None
        chan_cell, overview = await self.findchanidcell(ctx, curr_sheet_link)
        if chan_cell is None or overview is None:
            return

        row_to_find = chan_cell.row

        sheet_tab_id_col = sheets_constants.SHEET_TAB_ID_COLUMN
        tab_id = overview.acell(sheet_tab_id_col + str(row_to_find)).value

        final_link = curr_sheet_link + "/edit#gid=" + str(tab_id)

        embed = discord_utils.create_embed()

        embed.add_field(
            name=f"{constants.SUCCESS}",
            value=f"The tab linked to {ctx.message.channel.mention} is at [tab link]({final_link})",
            inline=False,
        )
        await discord_utils.send_message(ctx, embed)

    def firstemptyrow(self, worksheet):
        """Finds the first empty row in a worksheet"""
        return len(worksheet.get_values()) + 1

    @command_predicates.is_solver()
    @commands.command(name="solvedlion")
    async def solvedlion(self, ctx, answer: str = None):
        """Sets the puzzle to solved and updates the sheet and channel name accordingly

        Permission Category : Solver Roles only.
        Usage: ~solvedlion
        Usage: ~solvedlion "answer"
        """
        await logging_utils.log_command(
            "solvedlion", ctx.guild, ctx.channel, ctx.author
        )
        await self.statuslion(ctx, "solved", answer)

    @command_predicates.is_solver()
    @commands.command(name="backsolvedlion", aliases=["backlion"])
    async def backsolvedlion(self, ctx, answer: str = None):
        """Sets the puzzle to backsolved and updates the sheet and channel name accordingly

        Permission Category : Solver Roles only.
        Usage: ~backsolvedlion
        Usage: ~backsolvedlion "answer"
        """
        await logging_utils.log_command(
            "backsolvedlion", ctx.guild, ctx.channel, ctx.author
        )
        await self.statuslion(ctx, "backsolved", answer)

    @command_predicates.is_solver()
    @commands.command(name="solvedishlion")
    async def solvedishlion(self, ctx, answer: str = None):
        """Sets the puzzle to solvedish and updates the sheet and channel name accordingly

        Permission Category : Solver Roles only.
        Usage: ~solvedishlion
        Usage: ~solvedishlion "answer"
        """
        await logging_utils.log_command(
            "solvedishlion", ctx.guild, ctx.channel, ctx.author
        )
        await self.statuslion(ctx, "solvedish", answer)

    @command_predicates.is_solver()
    @commands.command(name="unsolvedlion", aliases=["unlion"])
    async def unsolvedlion(self, ctx, answer: str = None):
        """Sets the puzzle to in progress and updates the sheet and channel name accordingly

        Permission Category : Solver Roles only.
        Usage: ~unsolvedlion
        """
        await logging_utils.log_command(
            "unsolvedlion", ctx.guild, ctx.channel, ctx.author
        )
        await self.statuslion(ctx, "in progress", answer)

    @command_predicates.is_solver()
    @commands.command(name="statuslion", aliases=["statlion", "stat", "puzzstatus"])
    async def statuslion(self, ctx, status: str, answer: str = None):
        """Adds a status to the puzzle and updates the sheet and channel name accordingly

        You may pick one of [solved, solvedish, backsolved, postsolved, unstarted, unsolvable, stuck, abandoned, in progress] as statuses.
        Alternatively, you can give a custom status.

        For statuses [solved, solvedish, postsolved, backsolved, custom] users have the option to add an answer
        For statuses  [solved, solvedish, backsolved, postsolved] the channel name gets updated

        Permission Category : Solver Roles only.
        Usage: ~statuslion status
        Usage: ~statuslion solved "answer"
        Usage: ~statuslion "custom-update-string" "answer"
        """
        status = status.capitalize()
        if status == "Inprogress":
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

            curr_sheet_link = result.sheet_link
            chan_cell, overview = None, None
            chan_cell, overview = await self.findchanidcell(ctx, curr_sheet_link)
            curr_sheet = self.gspread_client.open_by_url(curr_sheet_link)

            if chan_cell is None or overview is None:
                return

            row_to_find = chan_cell.row

            # discord_channel_id_col = sheets_constants.DISCORD_CHANNEL_ID_COLUMN
            sheet_tab_id_col = sheets_constants.SHEET_TAB_ID_COLUMN
            # puzz_name_col = overview.acell(sheets_constants.PUZZLE_NAME_COLUMN_LOCATION).value
            status_col = overview.acell(sheets_constants.STATUS_COLUMN_LOCATION).value
            # answer_col = overview.acell(sheets_constants.ANSWER_COLUMN_LOCATION).value

            tab_ans_loc = sheets_constants.TAB_ANSWER_LOCATION
            # chan_name_loc = sheets_constants.TAB_CHAN_NAME_LOCATION
            # url_loc = sheets_constants.TAB_URL_LOCATION

            tab_id = overview.acell(sheet_tab_id_col + str(row_to_find)).value
            puzzle_tab = curr_sheet.get_worksheet_by_id(int(tab_id))

            if answer and status_info.get("update_ans"):
                puzzle_tab.update_acell(label=tab_ans_loc, value=answer.upper())
            elif not status_info.get("update_ans"):
                puzzle_tab.update_acell(label=tab_ans_loc, value="")

            curr_status = overview.acell(status_col + str(row_to_find)).value
            curr_stat_info = sheets_constants.status_dict.get(curr_status)

            if curr_stat_info is None:
                curr_stat_info = sheets_constants.status_dict.get("None")

            overview.update_acell(label=status_col + str(row_to_find), value=status)

            color = status_info.get("color")

            body = {
                "requests": [
                    {
                        "updateSheetProperties": {
                            "properties": {
                                "sheetId": tab_id,
                                "tabColor": {
                                    "red": color[0] / 255,
                                    "green": color[1] / 255,
                                    "blue": color[2] / 255,
                                },
                            },
                            "fields": "tabColor",
                        }
                    }
                ]
            }

            try:
                curr_sheet.batch_update(body)
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
    async def mtalion(self, ctx, archive_name: str = None):
        """Finds a category with `<category_name> Archive`, and moves the channel to that category.
        Fails if there is no such category, or is the category is full (i.e. 50 Channels).
        If called from thread (instead of channel), closes the thread instead of moving channel.

        Also moves the tab to the end of the list of tabs on the Google Sheet.

        Permission Category : Solver Roles only.
        Usage: `~mtalion`
        Usage: `~mtalion archive_category_name`
        """
        await logging_utils.log_command("mtalion", ctx.guild, ctx.channel, ctx.author)

        result, _ = sheet_utils.findsheettether(
            str(ctx.message.channel.category_id), str(ctx.message.channel.id)
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

        curr_sheet_link = result.sheet_link
        chan_cell, overview = None, None
        chan_cell, overview = await self.findchanidcell(ctx, curr_sheet_link)
        curr_sheet = self.gspread_client.open_by_url(curr_sheet_link)
        if chan_cell is None or overview is None:
            return

        row_to_find = chan_cell.row

        sheet_tab_id_col = sheets_constants.SHEET_TAB_ID_COLUMN

        tab_id = overview.acell(sheet_tab_id_col + str(row_to_find)).value
        puzzle_tab = curr_sheet.get_worksheet_by_id(int(tab_id))

        tab_id = overview.acell(sheet_tab_id_col + str(row_to_find)).value
        puzzle_tab = curr_sheet.get_worksheet_by_id(int(tab_id))
        puzzle_tab.update_index(len(curr_sheet.worksheets()))
        embed = discord_utils.create_embed()
        embed.add_field(
            name=f"{constants.SUCCESS}!",
            value=f"Moved sheet to the end of the spreadsheet!",
            inline=False,
        )

        await self.movetoarchive_generic(ctx, archive_name)

    ###############################
    # LION CHANNEL/SHEET CREATION #
    ###############################

    async def puzzlelion(
        self, ctx, chan_name, url, curr_sheet_link, newsheet, new_chan
    ):
        """Does the final touches on the sheet after creating a puzzle"""
        try:
            embed = discord_utils.create_embed()
            tab_name = chan_name.replace("#", "").replace("-", " ")

            sheet = self.gspread_client.open_by_url(curr_sheet_link)
            overview = None
            try:
                overview = sheet.worksheet("Overview")
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

            first_empty = self.firstemptyrow(overview)

            discord_channel_id_col = sheets_constants.DISCORD_CHANNEL_ID_COLUMN
            sheet_tab_id_col = sheets_constants.SHEET_TAB_ID_COLUMN
            puzz_name_col = overview.acell(
                sheets_constants.PUZZLE_NAME_COLUMN_LOCATION
            ).value
            status_col = overview.acell(sheets_constants.STATUS_COLUMN_LOCATION).value
            answer_col = overview.acell(sheets_constants.ANSWER_COLUMN_LOCATION).value

            final_sheet_link = curr_sheet_link + "/edit#gid=" + str(newsheet.id)

            chan_name_for_sheet_ref = chan_name.replace("'", "''")
            batch_update_builder = batch_update_utils.BatchUpdateBuilder()

            batch_update_builder.update_cell_by_label(
                sheet_id=overview.id,
                label=puzz_name_col + str(first_empty),
                value=f'=HYPERLINK("{final_sheet_link}", "{chan_name}")',
                is_formula=True,
            )

            batch_update_builder.update_cell_by_label(
                sheet_id=overview.id,
                label=discord_channel_id_col + str(first_empty),
                value=str(new_chan.id),
            )

            batch_update_builder.update_cell_by_label(
                sheet_id=overview.id,
                label=sheet_tab_id_col + str(first_empty),
                value=str(newsheet.id),
            )

            unstarted = sheets_constants.UNSTARTED_NAME
            batch_update_builder.update_cell_by_label(
                sheet_id=overview.id,
                label=status_col + str(first_empty),
                value=unstarted,
            )

            chan_name_for_sheet_ref = tab_name.replace("'", "''")
            tab_ans_loc = sheets_constants.TAB_ANSWER_LOCATION
            chan_name_loc = sheets_constants.TAB_CHAN_NAME_LOCATION
            url_loc = sheets_constants.TAB_URL_LOCATION

            batch_update_builder.update_cell_by_label(
                sheet_id=overview.id,
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
    async def chanlion(self, ctx, chan_name: str, *args):
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
            chan_or_thread="chan",
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
    async def metalion(self, ctx, chan_name: str, *args):
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
            chan_or_thread="chan",
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
    async def threadlion(self, ctx, chan_name: str, *args):
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
            chan_or_thread="thread",
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
    async def metathreadlion(self, ctx, chan_name: str, *args):
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
            chan_or_thread="thread",
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
    async def sheetlion(self, ctx, tab_name: str, url: str = None):
        """Creates a new tab for a new feeder puzzle and then updates the info in the sheet accordingly.

        Requires that the sheet has Overview and Template tabs

        Permission Category : Solver Roles only.
        Usage: ~sheetlion PuzzleName
        Usage: ~sheetlion PuzzleName linktopuzzle
        """
        await logging_utils.log_command("sheetlion", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

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
    async def metasheetlion(self, ctx, tab_name: str, url: str = None):
        """Creates a new tab for a new metapuzzle and then updates the info in the sheet accordingly.

        Requires that the sheet has Overview and Meta Template tabs

        Permission Category : Solver Roles only.
        Usage: ~metasheetlion PuzzleName
        Usage: ~metasheetlion PuzzleName linktopuzzle
        """
        await logging_utils.log_command(
            "metasheetlion", ctx.guild, ctx.channel, ctx.author
        )
        embed = discord_utils.create_embed()

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

    async def validate_template(self, ctx, proposed_sheet):
        embed = discord_utils.create_embed()

        proposed_template = sheet_utils.get_sheet_from_key_or_link(
            self.gspread_client, proposed_sheet
        )

        if not proposed_template:
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"Sorry, we can't find a sheet there. "
                f"Did you forget to set your sheet as 'Anyone with the link can edit'?",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return None

        curr_link = proposed_template.url

        # Make sure the template tab exists on the sheet.
        try:
            curr_sheet = self.gspread_client.open_by_url(curr_link)
            template_id = curr_sheet.worksheet("Template").id
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
            overview_id = curr_sheet.worksheet("Meta Template").id
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
            overview_id = curr_sheet.worksheet("Overview").id
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
        ctx,
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
        await logging_utils.log_command("huntlion", ctx.guild, ctx.channel, ctx.author)

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
                    value=f"Error! The hunt category was not correctly created.",
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
                value=f"Forbidden! Have you checked if the bot has the required permisisons?",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return

        channel_list = cat.channels
        channels = [f"{chan.mention}" for chan in channel_list]
        embed = discord_utils.create_embed()
        embed.add_field(
            name=f"{constants.SUCCESS}!",
            value=f"The hunt category was created.",
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
                value=f"Sorry, we can't find a sheet there. "
                f"Did you forget to set your sheet as 'Anyone with the link can edit'?",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return

        if await self.initoverview(ctx, hunturl, new_sheet):
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.SUCCESS}!",
                value=f"The sheet is now set up for use",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)

    # @command_predicates.is_verified()
    # @commands.command(name="clonelion")
    async def clonelion(
        self, ctx, huntroundname: str, hunturl: str, folderurl: str = None
    ):
        """Clone the template and names the new sheet. Also tethers the new sheet to the category.

        Useful when we want to make a new sheet for a new set of rounds.

        For any lion commands, a tether using either ~clonelion or ~huntlion is necessary.

        Permission Category : Verified Roles only.
        Usage: ~clonelion SheetName hunturl
        Usage: ~clonelion SheetName hunturl folderurl
        """
        await logging_utils.log_command("clonelion", ctx.guild, ctx.channel, ctx.author)

        new_sheet = await self.clonetemplatelion(ctx, huntroundname, folderurl)
        if new_sheet is None:
            return

        await self.tetherlion(ctx, new_sheet.url)
        if await self.initoverview(ctx, hunturl, new_sheet):
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.SUCCESS}!",
                value=f"The sheet is now set up for use",
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
    async def clonetemplatelion(self, ctx, newname, folderurl: str = None):
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
                value=f"Sorry, we can't find a sheet there. "
                f"Did you forget to set your sheet as 'Anyone with the link can edit'?",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return


def setup(bot):
    bot.add_cog(LionCog(bot))
