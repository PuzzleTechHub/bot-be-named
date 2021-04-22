
from utils import discord_utils, google_utils
from modules.sheets import sheets_constants
import discord
from discord.ext import commands
import os

class SheetsCog(commands.Cog, name="Sheets"):
    """A collection of commands for Google Sheests management"""
    def __init__(self, bot):
        self.bot = bot

        # self.gspread_client = google_utils.create_gspread_client()
        # self.tether_sheet = self.gspread_client.open_by_key(os.getenv("GSHEETS_TETHER_KEY")).sheet1
        # self.tether_df = google_utils.get_dataframe_from_gsheet(self.tether_sheet, sheets_constants.COLUMNS)


    @commands.command(name="sheetcreatetab")
    async def sheetcreatetab(self, ctx, *args):
        """Clones Template Tab in category's sheet, renames to tabname, posts link in channel, pins link"""
        print("Received sheetcreatetab")
        # if len(args) < 1:
        #   discord_utils.create_no_argument_embed("Tab Name")
        # Get sheet in ctx's category
        # if ctx.message.channel.category in self.tether_df[sheet_constants.CATEGORY]:
        #   category_sheet_id = self.tether_df[self.tether_df[sheet_constants.CATEGORY] == ctx.message.channel.category][sheet_constants.SHEET_ID]
        #   category_sheet = self.gspread_client.open_by_key(category_sheet_id)

        # Clone template tab of sheet
        # TODO: can we assume template tab is always index 0?
        # new_sheet = category_sheet.duplicate_sheet(0, new_sheet_name = ' '.join(args))

        # post link to sheet in channel
        # embed = discord_utils.create_embed()
        # embed.add_field(name=f"Sheet for {ctx.message.channel}",
        #                 value=new_sheet.url,
        #                 inline=False)
        # msg = await ctx.send(embed=embed)
        # pin message
        # await msg.pin()


def setup(bot):
    bot.add_cog(SheetsCog(bot))