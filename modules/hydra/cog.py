import constants
import gspread
import asyncio
import emoji
import shlex
from nextcord.ext import commands
from utils import (
    discord_utils,
    google_utils,
    logging_utils,
    command_predicates,
    sheets_constants,
    sheet_utils,
)
from gspread.worksheet import Worksheet
from modules.hydra import hydra_utils

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

    ############################
    # REFACTORED LION COMMANDS #
    ############################

    async def findchanidcell(
        self, ctx, sheet_link, list_channel_id
    ) -> list[tuple[int, Worksheet, list]] | None:
        """Find the cell with the discord channel id based on lion overview"""
        try:
            overview_wrapper = sheet_utils.OverviewSheet(
                self.gspread_client, sheet_link
            )

        except gspread.exceptions.APIError as e:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"I'm unable to open the tethered sheet. Error: {str(e)}",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return None

        except gspread.exceptions.SpreadsheetNotFound as e:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"The [sheet]({sheet_link}) has no tab named 'Overview'. "
                f"Did you forget to add one?",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return None

        except Exception as e:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
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

    def firstemptyrow(self, worksheet):
        """Finds the first empty row in a worksheet"""
        return len(worksheet.get_values()) + 1

    ###################
    # HYDRA COMMANDS  #
    ###################

    @command_predicates.is_solver()
    @commands.command(name="roundhydra")
    async def roundlion(self, ctx: commands.Context, round_name: str):
        """Sets or updates the round information on the Overview sheet.

        Permission Category : Solver Roles only
        Usage: ~roundhydra "Round Name"
        Usage: ~roundhydra RoundName
        """
        await logging_utils.log_command("roundlion", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

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

        round_col = sheets_constants.ROUND_COLUMN

        try:
            overview_sheet.worksheet.update_acell(
                round_col + str(row_to_find), round_name
            )

            embed.add_field(
                name=f"{constants.SUCCESS}",
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
                    name=f"{constants.FAILED}",
                    value="Could not update the sheet. Permission denied.",
                    inline=False,
                )
            else:
                embed.add_field(
                    name=f"{constants.FAILED}",
                    value=f"Unknown GSheets API Error - `{error_json.get('error', {}).get('message')}`",
                    inline=False,
                )
            await discord_utils.send_message(ctx, embed)

    @command_predicates.is_solver()
    @commands.command(name="noteshydra")
    async def noteshydra(self, ctx: commands.Context, *, notes: str):
        """Sets or updates the notes information on the Overview sheet.

        If you wrap your note in quotes, it will appear that way in the sheet. Quotes are not required.

        Permission Category : Solver Roles only
        Usage: ~noteshydra "Notes about the puzzle"
        """

        await logging_utils.log_command("noteshydra", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

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

        notes_col = sheets_constants.NOTES_COLUMN

        try:
            overview_sheet.worksheet.update_acell(notes_col + str(row_to_find), notes)

            embed.add_field(
                name=f"{constants.SUCCESS}",
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
                    name=f"{constants.FAILED}",
                    value="Could not update the sheet. Permission denied.",
                    inline=False,
                )
            else:
                embed.add_field(
                    name=f"{constants.FAILED}",
                    value=f"Unknown GSheets API Error - `{error_json.get('error', {}).get('message')}`",
                    inline=False,
                )
            await discord_utils.send_message(ctx, embed)

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

    @command_predicates.is_solver()
    @commands.command(name="catsummaryhydra", aliases=["categorysummaryhydra"])
    async def catsummaryhydra(self, ctx, cat_name: str = "") -> None:
        """For all channels in the current category, gets a summary of the channels via the Ovewview column. Pastes the summary already in there.

        Permission Category : Solver Roles only.

        Usage: `~catsummaryhydra`
        Usage: `~catsummaryhydra "Cat Name"` (Named category)
        """
        await logging_utils.log_command(
            "catsummaryhydra", ctx.guild, ctx.channel, ctx.author
        )
        embed = discord_utils.create_embed()

        # Make sure it's a valid category to summarise
        if cat_name == "":
            currcat = ctx.message.channel.category
        else:
            currcat = await discord_utils.find_category(ctx, cat_name)
        if currcat is None:
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"I cannot find category `{cat_name}`. Perhaps check your spelling and try again.",
            )
            await discord_utils.send_message(ctx, embed)
            return

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
                    messages.append(f"- {currchan.mention} - **No sheet tethered!**")
                    continue
                curr_sheet_link = result.sheet_link
                allsheets.append((curr_sheet_link, currchan))

            all_unique_sheets = list(set([x[0] for x in allsheets]))

            for curr_sheet_link in all_unique_sheets:
                list_curr_sheet_chans = [
                    x[1] for x in allsheets if x[0] == curr_sheet_link
                ]

                list_chan_cells_overview = await self.findchanidcell(
                    ctx, curr_sheet_link, [x.id for x in list_curr_sheet_chans]
                )

                if list_chan_cells_overview is None:
                    for currchan in list_curr_sheet_chans:
                        messages.append(
                            f"- {currchan.mention} - **Failed to load sheet!**"
                        )
                    continue

                overview_col = sheets_constants.OVERVIEW_COLUMN
                _, sample_overview, sample_values = next(
                    (t for t in list_chan_cells_overview if t[1] is not None),
                    (None, None, None),
                )

                if sample_overview is None or sample_values is None:
                    for currchan in list_curr_sheet_chans:
                        messages.append(
                            f"- {currchan.mention} - **Sheet ID unavailable!**"
                        )
                    continue

                _, col_idx = gspread.utils.a1_to_rowcol(overview_col + "1")
                for i in range(len(list_curr_sheet_chans)):
                    currchan = list_curr_sheet_chans[i]
                    rownum, overview, overview_values = list_chan_cells_overview[i]
                    if rownum is None or overview is None:
                        messages.append(
                            f"- {currchan.mention} - **Channel not found in sheet!**"
                        )
                        continue

                    row_to_find = chan_cell.row
                    overview_col = sheets_constants.NOTES_COLUMN
                    overview_desc = overview.acell(
                        overview_col + str(row_to_find)
                    ).value
                    if overview_desc is not None:
                        messages.append(f"- {currchan.mention} - {overview_desc[:100]}")
                    else:
                        messages.append(
                            f"- {currchan.mention} - *(empty description)*"
                        )
        except Exception as e:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
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
                name=f"{constants.FAILED}",
                value=f"No text channels found in category `{currcat.name}`.",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            await initial_message.delete()
            return

        # Split into multiple messages
        chunk_size = 12
        for i in range(0, len(messages), chunk_size):

            final_embed = discord_utils.create_embed()
            chunk = messages[i : i + chunk_size]

            for j, msg in enumerate(chunk):
                parts = msg.split(" - ", 1)
                channel_part = parts[0].replace('- ', '').strip()
                desc_part = parts[1].strip() if len(parts) > 1 else "\u200b"

                final_embed.add_field(name=channel_part, value=desc_part, inline=True)

                if (j + 1) % 2 == 0:
                    final_embed.add_field(name="\u200b", value="\u200b", inline=True)

            await discord_utils.send_message(ctx, final_embed)

        await initial_message.delete()


    @command_predicates.is_solver()
    @commands.command(name="anychanhydra")
    async def anychanhydra(
        self,
        ctx,
        *,
        args,
    ):
        """Creates a new puzzle channel based on a template in the tethered GSheet. Template must be passed in.

        Permission Category : Solver Roles only.

        Usage: `~chanhydra [puzzle name] [template name] [puzzle url]`
        """
        await logging_utils.log_command(
            "chanhydra", ctx.guild, ctx.channel, ctx.author
        )

        arg_list = shlex.split(args)
        if len(arg_list) < 2 or len(arg_list) > 3:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"Invalid arguments. Usage: `~chanhydra [puzzle name] [template name] [puzzle url (optional)]`",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return

        puzzle_name = arg_list[0]
        template_name = arg_list[1]
        puzzle_url = arg_list[2] if len(arg_list) > 2 else None

        await hydra_utils.create_puzzle_channel_from_template(
            self.bot,
            ctx,
            puzzle_name,
            template_name,
            puzzle_url,
            self.gspread_client,
        )

def setup(bot):
    bot.add_cog(HydraCog(bot))
