import nextcord
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

    # ============================
    # REFACTORED LION COMMANDS
    # ============================

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

        except gspread.exceptions.SpreadsheetNotFound:
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

    # ============================
    # HYDRA COMMANDS
    # ============================

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

                overview_col = sheets_constants.NOTES_COLUMN
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
    @commands.command(name="anychanhydra")
    async def anychanhydra(
        self,
        ctx,
        *,
        args,
    ):
        """Creates a new puzzle channel based on a template in the tethered GSheet. Template must be passed in.

        Permission Category : Solver Roles only.

        Usage: `~anychanhydra [puzzle name] [template name] [puzzle url]`
        """
        await logging_utils.log_command(
            "anychanhydra", ctx.guild, ctx.channel, ctx.author
        )

        arg_list = shlex.split(args)
        if len(arg_list) < 2 or len(arg_list) > 3:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value="Invalid arguments. Usage: `~anychanhydra [puzzle name] [template name] [puzzle url (optional)]`",
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
    @commands.command(name="unmtahydra")
    async def unmtahydra(self, ctx: commands.Context, category_name: str = ""):
        """Does the rough opposite of ~mtahydra (~mtalion). Moves the channel into the main hunt category and moves the sheet into the active section.
        If I cannot find the main hunt category, I will ask the user to specify it.

        Permission Category : Solver Roles only.
        Usage: `~unmtahydra`
        Usage: `~unmtahydra "Main Hunt Category Name"` (If I cannot find the main hunt category automatically)
        """
        await logging_utils.log_command(
            "unmtahydra", ctx.guild, ctx.channel, ctx.author
        )
        embed = discord_utils.create_embed()


        result, _ = sheet_utils.findsheettether(
            str(ctx.message.channel.category_id), str(ctx.message.channel.id)
        )

        if result is None:
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"The channel {ctx.message.channel.mention} is not tethered to any Google sheet.",
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
        try:
            overview_values = overview_sheet.overview_data
            _, col_idx = gspread.utils.a1_to_rowcol(sheet_tab_id_col + "1")
            sheet_tab_id = overview_values[row_to_find - 1][col_idx - 1]
        except Exception:
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"Could not find the Sheet Tab ID for channel {ctx.message.channel.mention} in the Overview sheet.",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return


        if ctx.channel.category is None:
            embed.add_field(
                name=f"{constants.FAILED}",
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
                    name=f"{constants.FAILED}",
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
            possible_name_candidates = [  # These are the category names this command *should* get called from, where [x] is anything.
                "[x] Archive",
                "Archive: [x]",
                "[x] archive",
            ]
            curr_cat_name = ctx.channel.category.name
            for candidate in possible_name_candidates:
                if candidate.replace("[x]", "").strip() in curr_cat_name:
                    possible_main_cat_name = curr_cat_name.replace(
                        candidate.replace("[x]", "").strip(), ""
                    ).strip()
                    main_category = await discord_utils.find_category(
                        ctx, possible_main_cat_name
                    )
                    if main_category is not None:
                        break

        if main_category is None:
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"I could not automatically find the main hunt category. "
                f"Please specify the main hunt category name as an argument.",
            )
            await discord_utils.send_message(ctx, embed)
            return

        # Try to move the channel
        channel_embed = discord_utils.create_embed()
        try:
            await ctx.channel.edit(category=main_category)
            channel_embed.add_field(
                name=f"{constants.SUCCESS}",
                value=f"Successfully moved channel {ctx.channel.mention} to category `{main_category.name}`.",
                inline=False,
            )
            await discord_utils.send_message(ctx, channel_embed)
        except nextcord.Forbidden:
            channel_embed.add_field(
                name=f"{constants.FAILED}",
                value=f"I do not have permission to move the channel {ctx.channel.mention} to category `{main_category.name}`.",
                inline=False,
            )
            await discord_utils.send_message(ctx, channel_embed)
            return
        except Exception as e:
            channel_embed.add_field(
                name=f"{constants.FAILED}",
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
                name=f"{constants.SUCCESS}",
                value=f"Successfully moved the sheet tab for {ctx.channel.mention} to the active section.",
                inline=False,
            )
            await discord_utils.send_message(ctx, tab_embed)
        except gspread.exceptions.APIError as e:
            error_json = e.response.json()
            error_message = error_json.get("error", {}).get("message")
            tab_embed.add_field(
                name=f"{constants.FAILED}",
                value=f"Google Sheets API Error when moving tab: `{error_message}`",
                inline=False,
            )
            await discord_utils.send_message(ctx, tab_embed)
            return
        except Exception as e:
            tab_embed.add_field(
                name=f"{constants.FAILED}",
                value=f"Unknown error when moving tab: `{str(e)}`",
                inline=False,
            )
            await discord_utils.send_message(ctx, tab_embed)
            return


def setup(bot):
    bot.add_cog(HydraCog(bot))
