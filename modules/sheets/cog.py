
from utils import discord_utils, google_utils
from modules.sheets import sheets_constants
import discord
from discord.ext import commands
import os

class SheetsCog(commands.Cog, name="Sheets"):
    """A collection of commands for Google Sheests management"""
    def __init__(self, bot):
        self.bot = bot
        self.gspread_client = google_utils.create_gspread_client()
        self.category_tether_tab = self.gspread_client.open_by_key(sheets_constants.SHEET_ID).worksheet(sheets_constants.CATEGORY_TAB)
        #self.tether_df = google_utils.get_dataframe_from_gsheet(self.tether_sheet, sheets_constants.COLUMNS)
        print(self.category_tether_tab.get_all_values())

    @commands.command(name="addsheettether")
    async def addsheettether(self, ctx, *args):
        if len(args) < 1:
            embed = discord_utils.create_no_argument_embed('Sheet Link')
            await ctx.send(embed=embed)
            return 0
        curr_cat = str(ctx.message.channel.category)
        curr_cat_id = str(ctx.message.channel.category_id)
        curr_guild = str(ctx.message.channel.guild)
        curr_sheet = args[0]
        #if ctx.message.channel.category in self.tether_df[sheet_constants.CATEGORY]:
        allvals = self.category_tether_tab.get_all_values()
        i=1
        idx=0
        for row in allvals:
            if(row[0] == curr_cat_id):
                idx = i
                break
            i=i+1

        if(idx==0):
            values = [curr_cat_id, curr_guild + " - " + curr_cat, str(curr_sheet)]
            self.category_tether_tab.append_row(values)
        else:
            values = [[curr_cat_id, curr_guild + " - " + curr_cat, str(curr_sheet)]]
            rownum = "A"+str(idx)+":C"+str(idx)
            self.category_tether_tab.update(rownum, values)
        print("Received sheettether")
        print(curr_cat+"\n"+curr_cat_id+"\n"+curr_guild+"\n"+curr_sheet+"\n")

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