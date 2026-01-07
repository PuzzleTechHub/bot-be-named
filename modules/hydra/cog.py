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

    ###################
    # HYDRA COMMANDS  #
    ###################

    @command_predicates.is_solver()
    @commands.command(name="roundhydra")
    async def roundhydra(self, ctx: commands.Context, *, round_name: str = None):
        """Sets or updates the round information on the Overview sheet. Passing no argument retrieves the current round.

        If you wrap the round name in quotes, it will appear that way in the sheet. Quotes are not required.

        Permission Category : Solver Roles only
        Usage: `~roundhydra` (retrieves current round)
        Usage: `~roundhydra Round Name` (sets round)
        """
        await logging_utils.log_command(
            "roundhydra", ctx.guild, ctx.channel, ctx.author
        )
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
        overview_sheet = await hydra_utils.get_overview(
            self.gspread_client, ctx, curr_sheet_link
        )
        if overview_sheet is None:
            return

        row_to_find, err_embed = overview_sheet.find_row_of_channel(ctx)
        if err_embed is not None:
            await discord_utils.send_message(ctx, err_embed)
            return

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
    async def noteshydra(self, ctx: commands.Context, *, notes: str = None):
        """Sets or updates the notes information on the Overview sheet. Passing no argument retrieves the current notes.

        If you wrap your note in quotes, it will appear that way in the sheet. Quotes are not required.

        Permission Category : Solver Roles only
        Usage: `~noteshydra` (retrieves current notes)
        Usage: `~noteshydra This puzzle has unclued anagrams.` (sets notes)
        """

        await logging_utils.log_command(
            "noteshydra", ctx.guild, ctx.channel, ctx.author
        )
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
        overview_sheet = await hydra_utils.get_overview(
            self.gspread_client, ctx, curr_sheet_link
        )
        if overview_sheet is None:
            return

        row_to_find, err_embed = overview_sheet.find_row_of_channel(ctx)
        if err_embed is not None:
            await discord_utils.send_message(ctx, err_embed)
            return

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
                overview_sheet.worksheet.update_acell(
                    notes_col + str(row_to_find), notes
                )

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

                list_chan_cells_overview = await hydra_utils.findchanidcell(
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
                        messages.append(
                            f"- {currchan.mention} - {overview_desc[:100] + '...' if len(overview_desc) > 100 else overview_desc}"
                        )
                    else:
                        messages.append(f"- {currchan.mention} - *(empty description)*")
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
        await logging_utils.log_command("chanhydra", ctx.guild, ctx.channel, ctx.author)

        arg_list = shlex.split(args)
        if len(arg_list) < 2 or len(arg_list) > 3:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value="Invalid arguments. Usage: `~chanhydra [puzzle name] [template name] [puzzle url (optional)]`",
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

    @command_predicates.is_solver()
    @commands.command(name="mtahydra", aliases=["movetoarchivehydra"])
    async def mtahydra(self, ctx, *, category_name: str = None):
        """Finds a category with `<category_name> Archive`, and moves the channel to that category.
        Fails if there is no such category. If the category is full (50 channels), I will make a new one.
        If called from thread (instead of channel), closes the thread instead of moving channel.

        Also moves the tab to the end of the list of tabs on the Google Sheet.

        Attempts to search smart, for example `~mtalion "MH21 Students"` will search for "MH21 Students Archive" and "MH21 Archive" categories.
        Some other common variants for "Archive" will also be attempted.

        Permission Category : Solver Roles only.
        Usage: `~mtalion`
        Usage: `~mtalion archive_category_name`
        """
        await logging_utils.log_command("mtahydra", ctx.guild, ctx.channel, ctx.author)
        await hydra_utils.sheet_move_to_archive(self.gspread_client, ctx)
        await hydra_utils.category_move_to_archive(ctx, category_name)


def setup(bot):
    bot.add_cog(HydraCog(bot))
