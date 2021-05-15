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

    @commands.command(name="addsheettether", aliases=['editsheettether','tether','edittether','addtether'])
    async def addsheettether(self, ctx, sheet_key_or_link: str = None):
        """Add a sheet to the current channel's category"""
        print("Received addsheettether")
        # Ensure the user has supplied a new sheet key to tether
        if not sheet_key_or_link:
            embed = discord_utils.create_no_argument_embed('Sheet Link')
            await ctx.send(embed=embed)
            return

        # We accept both sheet keys or full links
        proposed_sheet = self.get_sheet_from_key_or_link(sheet_key_or_link)
        # If we can't open the sheet, send an error and return
        if not proposed_sheet:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"Error",
                            value=f"Sorry, we can't find a sheet there. "
                                  f"Did you forget to set your sheet as 'Anyone with the link can edit'?",
                            inline=False)
            await ctx.send(embed=embed)
            return
        # Get category information
        curr_cat = str(ctx.message.channel.category)
        curr_cat_id = str(ctx.message.channel.category_id)
        curr_guild = str(ctx.guild)

        # If the category already has a sheet, then we update it.
        # Otherwise, we add the category to our master sheet to establish the tether
        try:
            # Search first column for the category
            curr_cat_cell = self.category_tether_tab.find(curr_cat_id, in_column=1)
            #TODO: Lock sheet?
            # Prepare Row and update values
            row_vals = [[curr_cat_id, curr_guild + " - " + curr_cat, proposed_sheet.url]]
            rownum = "A" + str(curr_cat_cell.row) + ":C" + str(curr_cat_cell.row)
            self.category_tether_tab.update(rownum, row_vals)
        except gspread.exceptions.CellNotFound:
            # Cell isn't found, so we add a new row to the sheet to establish the tether
            values = [curr_cat_id, curr_guild + " - " + curr_cat, proposed_sheet.url]
            self.category_tether_tab.append_row(values)

        embed = discord_utils.create_embed()
        embed.add_field(name=f"Successful",
                         value=f"The category **{curr_cat}** is now tethered to the [Google sheet at link]({proposed_sheet.url})",
                         inline=False)
        await ctx.send(embed=embed)


    @commands.command(name="removesheettether")
    async def removesheettether(self, ctx):
        """Remove the sheet-category tethering"""
        print("Received removesheettether")
        # Get category information
        curr_cat = str(ctx.message.channel.category)
        curr_cat_id = str(ctx.message.channel.category_id)

        try:
            # Search first column for the category
            curr_cat_cell = self.category_tether_tab.find(curr_cat_id, in_column=1)
        except gspread.exceptions.CellNotFound:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"Error",
                            value=f"The category **{curr_cat}** is not tethered to any Google sheet.",
                            inline=False)
            await ctx.send(embed=embed)
            return
        # If the tethering exists, remove it from the sheet.
        curr_sheet_link = self.category_tether_tab.cell(curr_cat_cell.row, curr_cat_cell.col + 2).value
        self.category_tether_tab.delete_row(curr_cat_cell.row)
        embed = discord_utils.create_embed()
        embed.add_field(name=f"Successful",
                        value=f"The category **{curr_cat}** is no longer tethered to [sheet]({curr_sheet_link})",
                        inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="displaysheettether", aliases=['showsheettether','showtether','displaytether'])
    async def displaysheettether(self, ctx):
        """Find the sheet the category is current tethered too"""
        print("Received displaysheettether")
        # Get category information
        curr_cat = str(ctx.message.channel.category)
        curr_cat_id = str(ctx.message.channel.category_id)

        try:
            # Search first column for the category
            curr_cat_cell = self.category_tether_tab.find(curr_cat_id, in_column=1)
        except gspread.exceptions.CellNotFound:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"Error",
                            value=f"The category **{curr_cat}** is not tethered to any Google sheet.",
                            inline=False)
            await ctx.send(embed=embed)
            return

        curr_sheet_link = self.category_tether_tab.cell(curr_cat_cell.row, curr_cat_cell.col + 2).value
        embed = discord_utils.create_embed()
        embed.add_field(name=f"Result",
                        value=f"The category **{curr_cat}** is currently tethered to the [Google sheet at link]({curr_sheet_link})",
                        inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="sheetcreatetab", aliases=['SheetCrab','sheettab'])
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

        try:
            # Search first column for the category
            curr_cat_cell = self.category_tether_tab.find(curr_cat_id, in_column=1)
        except gspread.exceptions.CellNotFound:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"Error",
                            value=f"The category **{curr_cat}** is not tethered to any Google sheet.",
                            inline=False)
            await ctx.send(embed=embed)
            return

        curr_sheet_link = self.category_tether_tab.cell(curr_cat_cell.row, curr_cat_cell.col + 2).value

        # Make sure the template tab exists on the sheet.
        try:
            curr_sheet = self.gspread_client.open_by_url(curr_sheet_link)
            template_id = curr_sheet.worksheet("Template").id
        # Error when we can't open the curr sheet link
        except gspread.exceptions.APIError:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"Error",
                            value=f"I'm unable to open the tethered [sheet]({curr_sheet_link}). Did the permissions change?",
                            inline=False)
            await ctx.send(embed=embed)
            return
        # Error when the sheet has no template tab
        except gspread.exceptions.WorksheetNotFound:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"Error",
                             value=f"The [sheet]({curr_sheet_link}) has no tab named 'Template'. Did you forget to add one?",
                             inline=False)
            await ctx.send(embed=embed)
            return
        # Make sure tab_name does not exist
        try:
            curr_sheet.worksheet(tab_name)
            # If there is a tab with the given name, that's an error!
            embed = discord_utils.create_embed()
            embed.add_field(name=f"Error",
                            value=f"The [Google sheet at link]({curr_sheet_link}) already has a tab named **{tab_name}**. Cannot create a tab with same name.",
                            inline=False)
            await ctx.send(embed=embed)
            return
        except gspread.exceptions.WorksheetNotFound:
            # If the tab isn't found, that's good! We will create one.
            pass

        # Try to duplicate the template tab and rename it to the given name
        try:
            # Index of 4 is hardcoded for Team Arithmancy server
            newsheet = curr_sheet.duplicate_sheet(source_sheet_id=template_id,
                                                  new_sheet_name=tab_name,
                                                  insert_sheet_index=4)
        except gspread.exceptions.APIError:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"Error",
                             value=f"Could not duplicate 'Template' tab in the [Google sheet at link]({curr_sheet_link}). Is the permission set up with 'Anyone with link can edit'?",
                             inline=False)
            await ctx.send(embed=embed)
            return

        # This link is customized for the newly made tab
        final_sheet_link = curr_sheet_link + '/edit#gid=' + str(newsheet.id)

        embed = discord_utils.create_embed()
        embed.add_field(name=f"Success!",
                         value=f"Tab **{tab_name}** has been created at [Tab link]({final_sheet_link}).",
                         inline=False)
        msg = await ctx.send(embed=embed)
        await msg.pin()

    def get_sheet_from_key_or_link(self, sheet_key_or_link: str) -> gspread.Spreadsheet:
        """Takes in a string, which could be a google sheet key or URL"""
        # Assume the str is a URL
        try:
            sheet = self.gspread_client.open_by_url(sheet_key_or_link)
            return sheet
        except gspread.exceptions.APIError:
            return None
        # Given str was not a link
        except gspread.exceptions.NoValidUrlKeyFound:
            pass
        # Assume the str is a sheet key
        try:
            sheet = self.gspread_client.open_by_key(sheet_key_or_link)
            return sheet
        # Entity Not Found
        except gspread.exceptions.APIError:
            return None


def setup(bot):
    bot.add_cog(SheetsCog(bot))