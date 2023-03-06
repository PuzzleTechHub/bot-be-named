from utils import discord_utils, google_utils, logging_utils, command_predicates
from modules.sheets import sheets_constants, sheet_utils
from modules.sheets import cog
from modules import sheets
import constants
from nextcord.ext import commands
import nextcord
import gspread
from sqlalchemy.sql.expression import insert
from sqlalchemy.orm import Session
import asyncio
from typing import Union
from emoji import EMOJI_ALIAS_UNICODE_ENGLISH as EMOJIS


class LionCog(commands.Cog, name="Lion"):
    """Google Sheets - Lion management commands"""

    def __init__(self, bot):
        self.bot = bot
        self.lock = asyncio.Lock()
        self.gdrive_credentials = google_utils.get_gdrive_credentials()
        self.gspread_client = google_utils.create_gspread_client()

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
        except gspread.exceptions.APIError:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"I'm unable to open the tethered [sheet]({sheet_link}). "
                f"Did the permissions change?",
                inline=False,
            )
            await ctx.send(embed=embed)
            return
        # Error when the sheet has no template tab
        except gspread.exceptions.WorksheetNotFound:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"The [sheet]({sheet_link}) has no tab named 'Overview'. "
                f"Did you forget to add one?",
                inline=False,
            )
            await ctx.send(embed=embed)
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
            await ctx.send(embed=embed)

        return curr_chan_or_cat_cell, overview

    @command_predicates.is_solver()
    @commands.command(name="gettablion", aliases=["tablion", "gettab"])
    async def gettablion(self, ctx):
        """Gets the tab linked to the current channel. Returns an error if there is not one.

        Also see ~sheetlion and ~displaytether.

        Permission Category : Solver Roles only.

        Usage: ~gettablion
        """
        logging_utils.log_command("gettablion", ctx.guild, ctx.channel, ctx.author)
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
            await ctx.send(embed=embed)
            return

        curr_sheet_link = result.sheet_link

        chan_cell, overview = None, None

        chan_cell, overview = await self.findchanidcell(ctx, curr_sheet_link)

        if chan_cell is None or overview is None:
            return

        row_to_find = chan_cell.row

        tab_id = overview.acell("B" + str(row_to_find)).value

        final_link = curr_sheet_link + "/edit#gid=" + str(tab_id)

        embed = discord_utils.create_embed()

        embed.add_field(
            name=f"{constants.SUCCESS}",
            value=f"The tab linked to {ctx.message.channel.mention} is at [tab link]({final_link})",
            inline=False,
        )
        await ctx.send(embed=embed)

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
        await self.statuslion(ctx, "solved", answer)

    @command_predicates.is_solver()
    @commands.command(name="backsolvedlion", aliases=["backlion"])
    async def backsolvedlion(self, ctx, answer: str = None):
        """Sets the puzzle to backsolved and updates the sheet and channel name accordingly

        Permission Category : Solver Roles only.
        Usage: ~backsolvedlion
        Usage: ~backsolvedlion "answer"
        """
        await self.statuslion(ctx, "backsolved", answer)

    @command_predicates.is_solver()
    @commands.command(name="solvedishlion")
    async def solvedishlion(self, ctx):
        """Sets the puzzle to solvedish and updates the sheet and channel name accordingly

        Permission Category : Solver Roles only.
        Usage: ~solvedishlion
        """
        await self.statuslion(ctx, "solvedish")

    @command_predicates.is_solver()
    @commands.command(name="unsolvedlion", aliases=["unlion"])
    async def unsolvedlion(self, ctx):
        """Sets the puzzle to in progress and updates the sheet and channel name accordingly

        Permission Category : Solver Roles only.
        Usage: ~unsolvedlion
        """
        await self.statuslion(ctx, "inprogress")

    @command_predicates.is_solver()
    @commands.command(name="statuslion", aliases=["statlion", "stat", "puzzstatus"])
    async def statuslion(self, ctx, status: str, answer: str = None):
        """Adds a status to the puzzle and updates the sheet and channel name accordingly

        For statuses solved, postsolved, and backsolved, users have the option to add an answer

        Permission Category : Solver Roles only.
        Usage: ~statuslion status
        Usage: ~statuslion solved "answer"
        """
        logging_utils.log_command("statuslion", ctx.guild, ctx.channel, ctx.author)
        channel = ctx.message.channel
        status = status.capitalize()
        if status == "Inprogress":
            status = "In Progress"

        status_info = sheets_constants.status_dict.get(status)

        if status_info is None:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value="Invalid status. Please double check the spelling of the status.",
                inline=False,
            )
            await ctx.send(embed=embed)
            return

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
            await ctx.send(embed=embed)
            return

        curr_sheet_link = result.sheet_link

        chan_cell, overview = None, None

        chan_cell, overview = await self.findchanidcell(ctx, curr_sheet_link)

        curr_sheet = self.gspread_client.open_by_url(curr_sheet_link)

        if chan_cell is None or overview is None:
            return

        row_to_find = chan_cell.row

        tab_id = overview.acell("B" + str(row_to_find)).value

        puzzle_tab = curr_sheet.get_worksheet_by_id(int(tab_id))

        if answer and status_info.get("update_ans"):
            puzzle_tab.update("B3", answer.upper())
        elif not status_info.get("update_ans"):
            puzzle_tab.update("B3", "")

        status_col = overview.acell("B1").value
        puzz_name_col = overview.acell("A1").value

        curr_status = overview.acell(status_col + str(row_to_find)).value
        curr_stat_info = sheets_constants.status_dict.get(curr_status)

        overview.update_acell(status_col + str(row_to_find), status)

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

        embed = discord_utils.create_embed()
        try:
            curr_sheet.batch_update(body)
        except gspread.exceptions.APIError:
            embed.add_field(
                name=f"{constants.FAILED}",
                value="Could not update the sheet.",
                inline=False,
            )
            return

        embed.add_field(
            name=f"{constants.SUCCESS}",
            value="The sheet was successfully updated.",
            inline=False,
        )

        if status == curr_status:
            await ctx.message.add_reaction(EMOJIS[":white_check_mark:"])
            return

        add_prefix = status_info.get("prefix")
        past_prefix = curr_stat_info.get("prefix")
        tab_name = overview.acell(puzz_name_col + str(row_to_find)).value

        if not add_prefix and not past_prefix:
            await ctx.message.add_reaction(EMOJIS[":white_check_mark:"])
        elif past_prefix and not add_prefix:
            await channel.edit(name=tab_name)
            embed.add_field(
                name=f"{constants.SUCCESS}",
                value=f"Channel renamed to {channel.mention}",
                inline=False,
            )
            await ctx.message.add_reaction(EMOJIS[":white_check_mark:"])
        else:
            await channel.edit(name=status + " " + tab_name)
            embed.add_field(
                name=f"{constants.SUCCESS}",
                value=f"Channel renamed to {channel.mention}",
                inline=False,
            )
            await ctx.message.add_reaction(EMOJIS[":white_check_mark:"])

        await ctx.send(embed=embed)

    @command_predicates.is_solver()
    @commands.command(name="mtalion", aliases=["movetoarchivelion", "archivelion"])
    async def mtalion(self, ctx, archive_name: str = None):
        """Finds a category with `<category_name> Archive`, and moves the channel to that category.
        Fails if there is no such category, or is the category is full (i.e. 50 Channels).

        Also moves the tab to the end of the list of tabs on the Google Sheet.

        Permission Category : Solver Roles only.
        Usage: `~mtalion`
        Usage: `~mtalion archive_category_name`
        """
        logging_utils.log_command("mtalion", ctx.guild, ctx.channel, ctx.author)

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
            await ctx.send(embed=embed)
            return

        curr_sheet_link = result.sheet_link

        chan_cell, overview = None, None

        chan_cell, overview = await self.findchanidcell(ctx, curr_sheet_link)

        curr_sheet = self.gspread_client.open_by_url(curr_sheet_link)

        if chan_cell is None or overview is None:
            return

        row_to_find = chan_cell.row

        tab_id = overview.acell("B" + str(row_to_find)).value

        puzzle_tab = curr_sheet.get_worksheet_by_id(int(tab_id))

        puzzle_tab.update_index(len(curr_sheet.worksheets()))

        embed = discord_utils.create_embed()
        embed.add_field(
            name=f"{constants.SUCCESS}!",
            value=f"Moved sheet to the end of the spreadsheet!",
            inline=False,
        )

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
                await ctx.send(embed=embed)
                return
            else:
                embed.add_field(
                    name=f"{constants.FAILED}!",
                    value=f"There is no category named `{archive_name}`, so I cannot move {ctx.channel.mention}.",
                    inline=False,
                )
                await ctx.send(embed=embed)
                return

        if discord_utils.category_is_full(archive_category):
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"`{archive_category.name}` is already full, max limit is 50 channels. Consider renaming"
                f" `{archive_category.name}` and creating a new `{archive_category.name}`.",
                inline=False,
            )
            await ctx.send(embed=embed)
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
            await ctx.send(embed=embed)
            return

        embed.add_field(
            name=f"{constants.SUCCESS}!",
            value=f"Moved channel {ctx.channel.mention} to `{archive_category.name}`",
            inline=False,
        )
        await ctx.send(embed=embed)

    ###############################
    # LION CHANNEL/SHEET CREATION #
    ###############################

    async def puzzlelion(
        self, ctx, chan_name, url, curr_sheet_link, newsheet, new_chan
    ):
        """Does the final touches on the sheet after creating a puzzle"""
        sheet = self.gspread_client.open_by_url(curr_sheet_link)
        overview = None
        try:
            overview = sheet.worksheet("Overview")
        # Error when the sheet has no Overview tab
        except gspread.exceptions.WorksheetNotFound:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"The [sheet]({curr_sheet_link}) has no tab named 'Overview'. "
                f"Did you forget to add one?",
                inline=False,
            )
            await ctx.send(embed=embed)
            return

        first_empty = self.firstemptyrow(overview)

        puzz_name_col = overview.acell("A1").value
        answer_col = overview.acell("A2").value
        status_col = overview.acell("B1").value
        final_sheet_link = curr_sheet_link + "/edit#gid=" + str(newsheet.id)

        overview.update_acell(
            puzz_name_col + str(first_empty),
            f'=HYPERLINK("{final_sheet_link}", "{chan_name}")',
        )

        overview.update_acell("A" + str(first_empty), str(new_chan.id))
        overview.update_acell("B" + str(first_empty), str(newsheet.id))
        overview.update_acell(status_col + str(first_empty), "Unstarted")
        chan_name_for_sheet_ref = chan_name.replace("'", "''")
        overview.update_acell(
            answer_col + str(first_empty), f"='{chan_name_for_sheet_ref}'!B3"
        )

        newsheet.update_acell("A1", chan_name)

        if url:
            newsheet.update_acell("B1", url)

        await ctx.message.add_reaction(EMOJIS[":white_check_mark:"])

    @command_predicates.is_solver()
    @commands.command(name="chanlion")
    async def chanlion(self, ctx, chan_name: str, url=None):
        """Creates a new tab and a new channel for a new feeder puzzle and then updates the info in the sheet accordingly.

        Requires that the sheet has Overview and Template tabs

        Permission Category : Solver Roles only.
        Usage: ~chanlion PuzzleName
        Usage: ~chanlion PuzzleName linktopuzzle
        """
        logging_utils.log_command("chanlion", ctx.guild, ctx.channel, ctx.author)

        curr_sheet_link, newsheet, new_chan = None, None, None

        if url is not None:
            curr_sheet_link, newsheet, new_chan = await sheet_utils.chancrabgeneric(
                self.gspread_client, ctx, chan_name, "chan", url
            )
        else:
            curr_sheet_link, newsheet, new_chan = await sheet_utils.chancrabgeneric(
                self.gspread_client, ctx, chan_name, "chan"
            )

        if curr_sheet_link is None or newsheet is None or new_chan is None:
            return

        await self.puzzlelion(ctx, chan_name, url, curr_sheet_link, newsheet, new_chan)

    @command_predicates.is_solver()
    @commands.command(name="metalion", aliases=["metachanlion"])
    async def metalion(self, ctx, chan_name: str, url: str = None):
        """Creates a new tab and a new channel for a new metapuzzle and then updates the info in the sheet accordingly.

        Requires that the sheet has Overview and Meta Template tabs

        Permission Category : Solver Roles only.
        Usage: ~chanlion PuzzleName
        Usage: ~chanlion PuzzleName linktopuzzle
        """
        logging_utils.log_command("metalion", ctx.guild, ctx.channel, ctx.author)

        curr_sheet_link, newsheet, new_chan = None, None, None

        if url is not None:
            curr_sheet_link, newsheet, new_chan = await sheet_utils.metacrabgeneric(
                self.gspread_client, ctx, chan_name, "chan", url
            )
        else:
            curr_sheet_link, newsheet, new_chan = await sheet_utils.metacrabgeneric(
                self.gspread_client, ctx, chan_name, "chan"
            )

        if curr_sheet_link is None or newsheet is None or new_chan is None:
            return

        await self.puzzlelion(ctx, chan_name, url, curr_sheet_link, newsheet, new_chan)

    @command_predicates.is_solver()
    @commands.command(name="threadlion")
    async def threadlion(self, ctx, chan_name: str, url=None):
        """Creates a new tab and a new thread for a new feeder puzzle and then updates the info in the sheet accordingly.

        Requires that the sheet has Overview and Template tabs

        Permission Category : Solver Roles only.
        Usage: ~threadlion PuzzleName
        Usage: ~threadlion PuzzleName linktopuzzle
        """
        logging_utils.log_command("threadlion", ctx.guild, ctx.channel, ctx.author)

        curr_sheet_link, newsheet, new_chan = None, None, None

        if url is not None:
            curr_sheet_link, newsheet, new_chan = await sheet_utils.chancrabgeneric(
                self.gspread_client, ctx, chan_name, "thread", url
            )
        else:
            curr_sheet_link, newsheet, new_chan = await sheet_utils.chancrabgeneric(
                self.gspread_client, ctx, chan_name, "thread"
            )

        if curr_sheet_link is None or newsheet is None or new_chan is None:
            return

        await self.puzzlelion(ctx, chan_name, url, curr_sheet_link, newsheet, new_chan)

    @command_predicates.is_solver()
    @commands.command(name="metathreadlion")
    async def metathreadlion(self, ctx, chan_name: str, url: str = None):
        """Creates a new tab and a new thread for a new metapuzzle and then updates the info in the sheet accordingly.

        Requires that the sheet has Overview and Meta Template tabs

        Permission Category : Solver Roles only.
        Usage: ~chanlion PuzzleName
        Usage: ~chanlion PuzzleName linktopuzzle
        """
        logging_utils.log_command("metathreadlion", ctx.guild, ctx.channel, ctx.author)

        curr_sheet_link, newsheet, new_chan = None, None, None

        if url is not None:
            curr_sheet_link, newsheet, new_chan = await sheet_utils.metacrabgeneric(
                self.gspread_client, ctx, chan_name, "thread", url
            )
        else:
            curr_sheet_link, newsheet, new_chan = await sheet_utils.metacrabgeneric(
                self.gspread_client, ctx, chan_name, "thread"
            )

        if curr_sheet_link is None or newsheet is None or new_chan is None:
            return

        await self.puzzlelion(ctx, chan_name, url, curr_sheet_link, newsheet, new_chan)

    @command_predicates.is_solver()
    @commands.command(name="sheetlion")
    async def sheetlion(self, ctx, tab_name: str, url: str = None):
        """Creates a new tab for a new feeder puzzle and then updates the info in the sheet accordingly.

        Requires that the sheet has Overview and Template tabs

        Permission Category : Solver Roles only.
        Usage: ~chanlion PuzzleName
        Usage: ~chanlion PuzzleName linktopuzzle
        """
        logging_utils.log_command("sheetlion", ctx.guild, ctx.channel, ctx.author)

        curr_sheet_link, newsheet = await sheet_utils.sheetcrabgeneric(
            self.gspread_client, ctx, tab_name
        )

        if curr_sheet_link is None or newsheet is None:
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
        Usage: ~chanlion PuzzleName
        Usage: ~chanlion PuzzleName linktopuzzle
        """
        logging_utils.log_command("metasheetlion", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        curr_sheet_link, newsheet = None, None

        curr_chan = ctx.message.channel
        curr_cat = ctx.message.channel.category
        curr_sheet_link, newsheet = await sheet_utils.sheetcreatetabmeta(
            self.gspread_client, ctx, curr_chan, curr_cat, tab_name
        )

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
        embed_or_none = await discord_utils.pin_message(msg)
        await msg.add_reaction(EMOJIS[":pushpin:"])

        if embed_or_none is not None:
            await ctx.send(embed=embed_or_none)

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
            await ctx.send(embed=embed)
            return None

        curr_link = proposed_template.url

        # Make sure the template tab exists on the sheet.
        try:
            curr_sheet = self.gspread_client.open_by_url(curr_link)
            template_id = curr_sheet.worksheet("Template").id
        # Error when we can't open the curr sheet link
        except gspread.exceptions.APIError:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"I'm unable to open the tethered [sheet]({curr_link}). "
                f"Did the permissions change?",
                inline=False,
            )
            await ctx.send(embed=embed)
            return None
        # Error when the sheet has no template tab
        except gspread.exceptions.WorksheetNotFound:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"The [sheet]({curr_link}) has no tab named 'Template'. "
                f"Did you forget to add one?",
                inline=False,
            )
            await ctx.send(embed=embed)
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
            await ctx.send(embed=embed)
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
            await ctx.send(embed=embed)
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
        logging_utils.log_command("huntlion", ctx.guild, ctx.channel, ctx.author)

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
                await ctx.send(embed=embed)
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
                    await ctx.send(embed=embed)

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
            await ctx.send(embed=embed)
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
        await ctx.send(embed=embed)

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
            await ctx.send(embed=new_embed)
        # If we can't open the sheet, send an error and return
        else:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Sorry, we can't find a sheet there. "
                f"Did you forget to set your sheet as 'Anyone with the link can edit'?",
                inline=False,
            )
            await ctx.send(embed=embed)
            return

        if await self.initoverview(ctx, hunturl, new_sheet):
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.SUCCESS}!",
                value=f"The sheet is now set up for use",
                inline=False,
            )
            await ctx.send(embed=embed)

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
        logging_utils.log_command("clonelion", ctx.guild, ctx.channel, ctx.author)

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
            await ctx.send(embed=embed)

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
            await ctx.send(embed=embed)
            return None

        overview.update("C1", hunturl)
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
        logging_utils.log_command(
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
            await ctx.send(embed=embed)
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
            await ctx.send(embed=embed)
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

        await ctx.send(embed=embed)
        return new_sheet

    @command_predicates.is_solver()
    @commands.command(name="tetherlion")
    async def tetherlion(self, ctx, sheet_key_or_link: str):
        """Tethers a sheet to the category and also checks that it is the correct format to be used by the lion commands

        Sheet must have the following tabs: Overview, Template, Meta Template

        Usage: ~tetherlion sheeturl
        """
        logging_utils.log_command("tetherlion", ctx.guild, ctx.channel, ctx.author)
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
            await ctx.send(embed=embed)
        # If we can't open the sheet, send an error and return
        else:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Sorry, we can't find a sheet there. "
                f"Did you forget to set your sheet as 'Anyone with the link can edit'?",
                inline=False,
            )
            await ctx.send(embed=embed)
            return


def setup(bot):
    bot.add_cog(LionCog(bot))
