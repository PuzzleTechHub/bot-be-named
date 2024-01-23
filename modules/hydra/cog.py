import constants
import gspread
import asyncio
from nextcord.ext import commands
from utils import (
    discord_utils,
    google_utils,
    logging_utils,
    command_predicates,
    sheets_constants,
)
from utils import sheet_utils

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
    # LION DUPLICATED COMMANDS #
    ############################

    async def findchanidcell(self, ctx, sheet_link, list_channel_id):
        """Find the cell with the discord channel id based on lion overview"""
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
                await ctx.send(embed=embed)
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
            await ctx.send(embed=embed)
            return

        all_chan_ids = []
        for channel_id in list_channel_id:
            curr_chan_or_cat_cell = None
            # Search first column for the channel
            curr_chan_or_cat_cell = overview.find(str(channel_id), in_column=1)
            all_chan_ids.append((curr_chan_or_cat_cell, overview))
        return all_chan_ids

    def firstemptyrow(self, worksheet):
        """Finds the first empty row in a worksheet"""
        return len(worksheet.get_values()) + 1

    ###################
    # HYDRA COMMANDS  #
    ###################

    @command_predicates.is_solver()
    @commands.command(name="catsummaryhydra", aliases=["categorysummaryhydra"])
    async def catsummaryhydra(self, ctx, cat_name: str = ""):
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
            await ctx.send(embed=embed)
            return

        start_embed = discord_utils.create_embed()
        start_embed.add_field(
            name="Summary Started",
            value=f"Your summarizing of category `{currcat.name}`"
            f" has begun! This may take a while. If I run into "
            f"any errors, I'll let you know.",
            inline=False,
        )

        start_msg = await ctx.send(embed=start_embed)
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
                    messages.append(f"- {currchan.mention} - N/A")
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

                for i in range(len(list_curr_sheet_chans)):
                    currchan = list_curr_sheet_chans[i]
                    chan_cell, overview = list_chan_cells_overview[i]
                    if chan_cell is None or overview is None:
                        messages.append(f"- {currchan.mention} - N/A")
                        continue

                    row_to_find = chan_cell.row
                    overview_col = sheets_constants.OVERVIEW_COLUMN
                    overview_desc = overview.acell(
                        overview_col + str(row_to_find)
                    ).value
                    if(overview_desc is not None):
                        messages.append(f"- {currchan.mention} - {overview_desc[:100]}")
                    else:
                        messages.append(f"- {currchan.mention} - N/A")
        # Error when we can't open the curr sheet link
        except gspread.exceptions.APIError as e:
            error_json = e.response.json()
            error_status = error_json.get("error", {}).get("status")
            if error_status == "PERMISSION_DENIED":
                embed = discord_utils.create_embed()
                embed.add_field(
                    name=f"{constants.FAILED}",
                    value=f"I'm unable to open the tethered sheet. "
                    f"Did the permissions change?",
                    inline=False,
                )
                await ctx.send(embed=embed)
                return
            else:
                raise e

        message = "\n".join(messages)
        embed.add_field(
            name=f"{constants.SUCCESS}",
            value=f"Summary of Category `{currcat.name}` ({len(allchans)} text channels) - \n"
            f"{message}",
            inline=False,
        )

        if start_msg:
            await start_msg.delete()
        embeds = discord_utils.split_embed(embed)
        for embed in embeds:
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(HydraCog(bot))
