from utils import discord_utils, google_utils
from modules.sheets import sheets_constants
import discord
from discord.ext import commands
import os
import gspread

class SheetsCog(commands.Cog, name="Sheets"):
    """A collection of commands for Google Sheests management"""
    def __init__(self, bot):
        self.bot = bot
        self.gspread_client = google_utils.create_gspread_client()
        self.category_tether_tab = self.gspread_client.open_by_key(os.getenv('MASTER_SHEET_KEY')).worksheet(sheets_constants.CATEGORY_TAB)

    def findsheettether(self, curr_cat_id):
        """Finds the tethered sheet for a category, or 0 and None if not found"""
        allvals = self.category_tether_tab.get_all_values()
        i=1
        idx=0
        curr_sheet = None
        for row in allvals:
            if row[0] == curr_cat_id:
                idx = i
                # The 3rd column is where the sheet keys are stored
                curr_sheet=row[2]
                break
            i=i+1
        return idx, curr_sheet

    @commands.command(name="addsheettether", aliases=['editsheettether'])
    async def addsheettether(self, ctx, sheet_key: str = None):
        """Add a sheet to the current channel's category"""
        print("Received addsheettether")
        if not sheet_key:
            embed = discord_utils.create_no_argument_embed('Sheet Link')
            await ctx.send(embed=embed)
            return

        curr_cat = str(ctx.message.channel.category)
        curr_cat_id = str(ctx.message.channel.category_id)
        curr_guild = str(ctx.guild)
        curr_sheet_link = f"https://docs.google.com/spreadsheets/d/{sheet_key}/"

        idx, prev_sheet = self.findsheettether(curr_cat_id)

        try:
            self.gspread_client.open_by_key(sheet_key).sheet1
        except gspread.exceptions.APIError:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"Error",
                            value=f"There is no sheet currently existing at [Google sheet at link]({curr_sheet_link}). "
                                  f"Did you forget to set your sheet as 'Anyone with the link can edit'?",
                            inline=False)
            await ctx.send(embed=embed)
            return

        # If the category already has a sheet, then we update it.
        # Otherwise, we add the category to our master sheet to establish the tether
        if idx:
            values = [[curr_cat_id, curr_guild + " - " + curr_cat, sheet_key]]
            rownum = "A" + str(idx) + ":C" + str(idx)
            self.category_tether_tab.update(rownum, values)
        else:
            values = [curr_cat_id, curr_guild + " - " + curr_cat, sheet_key]
            self.category_tether_tab.append_row(values)
        embed = discord_utils.create_embed()
        embed.add_field(name=f"Successful",
                         value=f"The category **{curr_cat}** is now tethered to the [Google sheet at link]({curr_sheet_link})",
                         inline=False)
        await ctx.send(embed=embed)


    @commands.command(name="removesheettether")
    async def removesheettether(self, ctx):
        """Remove the sheet-category tethering"""
        print("Received removesheettether")
        curr_cat = str(ctx.message.channel.category)
        curr_cat_id = str(ctx.message.channel.category_id)

        idx, curr_sheet = self.findsheettether(curr_cat_id)
        curr_sheet_link = f"https://docs.google.com/spreadsheets/d/{curr_sheet}/"

        # If there is a tether established, remove it, otherwise error
        if idx:
            self.category_tether_tab.delete_row(idx)
            embed = discord_utils.create_embed()
            embed.add_field(name=f"Successful",
                            value=f"The category **{curr_cat}** is no longer tethered to the [Google sheet at link]({curr_sheet_link})",
                            inline=False)
            await ctx.send(embed=embed)
        else:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"Error",
                value=f"The category **{curr_cat}** is not tethered to any Google sheet.",
                inline=False)
            await ctx.send(embed=embed)


    @commands.command(name="displaysheettether")
    async def displaysheettether(self, ctx):
        """Find the sheet the category is current tethered too"""
        print("Received displaysheettether")
        curr_cat = str(ctx.message.channel.category)
        curr_cat_id = str(ctx.message.channel.category_id)

        idx, curr_sheet = self.findsheettether(curr_cat_id)
        curr_sheet_link = f"https://docs.google.com/spreadsheets/d/{curr_sheet}/"

        if idx:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"Result",
                            value=f"The category **{curr_cat}** is currently tethered to the [Google sheet at link]({curr_sheet_link})",
                            inline=False)
            await ctx.send(embed=embed)
        else:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"Error",
                value=f"The category **{curr_cat}** is not tethered to any Google sheet.",
                inline=False)
            await ctx.send(embed=embed)


    @commands.command(name="sheetcreatetab")
    async def sheetcreatetab(self, ctx, *args):
        """Create a New tab on the sheet that is currently tethered to this category"""
        print("Received sheetcreatetab")
        if len(args) < 1:
            embed = discord_utils.create_no_argument_embed('Tab Name')
            await ctx.send(embed=embed)
            return

        curr_cat = str(ctx.message.channel.category)        
        curr_cat_id = str(ctx.message.channel.category_id)
        tab_name = ' '.join(args)

        idx, curr_sheet = self.findsheettether(curr_cat_id)
        if idx == 0:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"Error",
                value=f"The category **{curr_cat}** is not tethered to any Google sheet.",
                inline=False)
            await ctx.send(embed=embed)
            return

        curr_sheet_link = f"https://docs.google.com/spreadsheets/d/{curr_sheet}/"
        # Make sure the template tab exists on the sheet.
        try:
            template_id = self.gspread_client.open_by_key(curr_sheet).worksheet("Template").id
        except gspread.exceptions.WorksheetNotFound:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"Error",
                             value=f"The [Google sheet at link]({curr_sheet_link}) has no tab named 'Template'. Did you forget to add one?",
                             inline=False)
            await ctx.send(embed=embed)
            return
        # Make sure no tab exists
        try:
            self.gspread_client.open_by_key(curr_sheet).worksheet(tab_name)
            # If there is a tab with the given name, that's an error!
            embed = discord_utils.create_embed()
            embed.add_field(name=f"Error",
                            value=f"The [Google sheet at link]({curr_sheet_link}) already has a tab named **{tab_name}**. Cannot create a tab with same name.",
                            inline=False)
            await ctx.send(embed=embed)
            return
        except gspread.exceptions.WorksheetNotFound:
            # If the sheet isn't found, that's good! We will create one.
            pass

        # Try to duplicate the template tab and rename it to the given name
        try:
            test_category_tether = self.gspread_client.open_by_key(curr_sheet)
            # Index of 4 is hardcoded for Team Arithmancy server
            newsheet = test_category_tether.duplicate_sheet(source_sheet_id=template_id,new_sheet_name=tab_name, insert_sheet_index=4)
        except gspread.exceptions.APIError:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"Error",
                             value=f"Could not duplicate 'Template' tab in the [Google sheet at link]({curr_sheet_link}). Is the permission set up with 'Anyone with link can edit'?",
                             inline=False)
            await ctx.send(embed=embed)
            return

        # This link is customized for the newly made tab
        final_sheet_link = f"https://docs.google.com/spreadsheets/d/{curr_sheet}/edit#gid={newsheet.id}"

        embed = discord_utils.create_embed()
        embed.add_field(name=f"Successful",
                         value=f"Tab **{tab_name}** has been created at [Tab link]({final_sheet_link}).",
                         inline=False)
        msg = await ctx.send(embed=embed)
        await msg.pin()

def setup(bot):
    bot.add_cog(SheetsCog(bot))