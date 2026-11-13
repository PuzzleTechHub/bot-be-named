import emoji
import gspread
from nextcord.ext import commands

from utils import (
    batch_update_utils,
    command_predicates,
    discord_utils,
    google_utils,
    sheet_utils,
    sheets_constants,
    solved_utils,
)
from utils.sheet_command_base import SheetCommandBase

"""
Lion module. Module with GSheet-Discord interfacing. See module's README.md for more.
"""


class LionCog(commands.Cog, name="Lion"):
    """
    Useful GSheet-Discord commands.
    """

    def __init__(self, bot):
        self.bot = bot
        self.gspread_client = google_utils.create_gspread_client()

    ########################
    # LION STATUS COMMANDS #
    ########################

    @command_predicates.is_solver()
    @commands.command(name="gettablion", aliases=["tablion", "gettab"])
    async def gettablion(self, ctx: commands.Context):
        """Gets the tab linked to the current channel. Returns an error if there is not one.

        Also see ~sheetlion and ~displaytether.

        Permission Category : Solver Roles only.

        Usage: ~gettablion
        """
        base = SheetCommandBase(ctx, self.gspread_client)
        curr_sheet_link, overview_sheet, row_to_find = await base.get_sheet_context()
        if overview_sheet is None:
            return

        tab_cell_label = sheets_constants.SHEET_TAB_ID_COLUMN + str(row_to_find)
        tab_id = overview_sheet.get_cell_value(tab_cell_label)

        final_link = curr_sheet_link + "/edit#gid=" + str(tab_id)

        embed = discord_utils.create_embed()

        embed.add_field(
            name="Success",
            value=f"The tab linked to {ctx.message.channel.mention} is at [tab link]({final_link})",
            inline=False,
        )
        await discord_utils.send_message(ctx, embed)

    @command_predicates.is_solver()
    @commands.command(name="solvedlion")
    async def solvedlion(self, ctx: commands.Context, answer: str = None):
        """Sets the puzzle to solved and updates the sheet and channel name accordingly.

        Permission Category : Solver Roles only.
        Usage: ~solvedlion
        Usage: ~solvedlion "answer"
        """
        await self.statuslion(ctx, "solved", answer)

    @command_predicates.is_solver()
    @commands.command(name="backsolvedlion", aliases=["backlion"])
    async def backsolvedlion(self, ctx: commands.Context, answer: str = None):
        """Sets the puzzle to backsolved and updates the sheet and channel name accordingly.

        Permission Category : Solver Roles only.

        Usage: ~backsolvedlion
        Usage: ~backsolvedlion "answer"
        """
        await self.statuslion(ctx, "backsolved", answer)

    @command_predicates.is_solver()
    @commands.command(name="solvedishlion")
    async def solvedishlion(self, ctx: commands.Context, answer: str = None):
        """Sets the puzzle to solvedish and updates the sheet and channel name accordingly

        Permission Category : Solver Roles only.

        Usage: ~solvedishlion
        Usage: ~solvedishlion "answer"
        """
        await self.statuslion(ctx, "solvedish", answer)

    @command_predicates.is_solver()
    @commands.command(name="unsolvedlion", aliases=["unlion"])
    async def unsolvedlion(self, ctx: commands.Context, answer: str = ""):
        """Sets the puzzle to in progress and updates the sheet and channel name accordingly

        Permission Category : Solver Roles only.

        Usage: ~unsolvedlion (Removes the answer from the sheet)
        Usage: ~unsolvedlion "answer" (Updates the answer from the sheet to "answer")

        """
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
        status = sheet_utils.normalize_status(status)
        embed = discord_utils.create_embed()

        try:
            status_info = sheets_constants.status_dict.get(status)

            # If something other than known strings (Custom status)
            if status_info is None:
                status_info = sheets_constants.status_dict.get("None")

            # Find tethered sheet
            base = SheetCommandBase(ctx, self.gspread_client)
            _, overview_sheet, row_to_find = await base.get_sheet_context()

            if overview_sheet is None:
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
                        name="Failed",
                        value="Could not update the sheet.",
                        inline=False,
                    )
                else:
                    raise e

            embed.add_field(
                name="Success",
                value="The sheet was successfully updated.",
                inline=False,
            )

            add_prefix = status_info.get("prefix")
            past_prefix = curr_stat_info.get("prefix")

            if status == curr_status:
                embed.add_field(
                    name="Note",
                    value=f"The puzzle status was already set to `{status}`. No changes were made.",
                    inline=False,
                )
                await ctx.message.add_reaction(emoji.emojize(":check_mark_button:"))
                await discord_utils.send_message(ctx, embed)
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
                    name="Failed",
                    value=f"Unknown GSheets API Error - `{error_message}`",
                    inline=False,
                )
                await discord_utils.send_message(ctx, embed)
                return

    async def sheetmta_generic(self, ctx: commands.Context):
        """Just handles the sheet aspect of mtalion, moving the tab associated with ctx.channel to the end of the sheet"""
        embed = discord_utils.create_embed()
        base = SheetCommandBase(ctx, self.gspread_client)
        _, overview_sheet, row_to_find = await base.get_sheet_context()

        if overview_sheet is None:
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

    @command_predicates.is_solver()
    @commands.command(name="mtalion", aliases=["movetoarchivelion", "archivelion"])
    async def mtalion(self, ctx: commands.Context, archive_name: str = None):
        """Finds a category with `<category_name> Archive`, and moves the channel to that category.
        Fails if there is no such category, or is the category is full (i.e. 50 Channels).
        If called from thread (instead of channel), closes the thread instead of moving channel.

        Also moves the tab to the end of the list of tabs on the Google Sheet.

        Attempts to search smart, for example `~mtalion "MH21 Students"` will search for "MH21 Students Archive" and "MH21 Archive" categories.
        Some other common variants for "Archive" will also be attempted.

        Permission Category : Solver Roles only.
        Usage: `~mtalion`
        Usage: `~mtalion archive_category_name`
        """
        await self.sheetmta_generic(ctx)  # Attempt to move sheet stuff
        await discord_utils.movetoarchive_generic(
            ctx, archive_name
        )  # Attempt to move channel stuff

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
            overview_sheet = await sheet_utils.get_overview(
                self.gspread_client, ctx, curr_sheet_link
            )

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
                    name="Failed",
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
                name="Failed",
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
                    name="Failed",
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
                name="Failed",
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
                name="Failed",
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
                name="Failed",
                value=f"The [sheet]({curr_link}) has no tab named 'Overview'. "
                f"Did you forget to add one?",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return None

        return proposed_template

    @command_predicates.is_solver()
    @commands.command(name="tetherlion", aliases=["tetherhydra"])
    async def tetherlion(self, ctx: commands.Context, sheet_key_or_link: str):
        """Tethers a sheet to the category and also checks that it is the correct format to be used by the lion commands

        Sheet must have the following tabs: Overview, Template, Meta Template

        Usage: ~tetherlion sheeturl
        """
        embed = discord_utils.create_embed()

        if await self.validate_template(ctx, sheet_key_or_link) is None:
            return

        proposed_sheet = sheet_utils.addsheettethergeneric(
            self.gspread_client, sheet_key_or_link, ctx.guild, ctx.channel.category
        )

        if proposed_sheet:
            embed.add_field(
                name="Success",
                value=f"The category **{ctx.channel.category.name}** is now tethered to the "
                f"[Google sheet at link]({proposed_sheet.url})",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
        # If we can't open the sheet, send an error and return
        else:
            embed.add_field(
                name="Failed",
                value="Sorry, we can't find a sheet there. "
                "Did you forget to set your sheet as 'Anyone with the link can edit'?",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return


def setup(bot):
    bot.add_cog(LionCog(bot))
