
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
        self.category_tether_tab = self.gspread_client.open_by_key(os.getenv('MASTER_SHEET_KEY')).worksheet(sheets_constants.CATEGORY_TAB)

    def findsheettether(self, curr_cat_id):
        """Finds the tethered sheet for a category, or 0 and an empty string if not found"""
        allvals = self.category_tether_tab.get_all_values()
        i=1
        idx=0
        curr_sheet = ""
        for row in allvals:
            if row[0] == curr_cat_id:
                idx = i
                curr_sheet=row[2]
                break
            i=i+1
        if idx == 0:
            return 0, ""
        else:
            return idx, curr_sheet

    @commands.command(name="addsheettether", aliases=['editsheettether'])
    async def addsheettether(self, ctx, *args):
        print("Received addsheettether")
        if len(args) < 1:
            embed = discord_utils.create_no_argument_embed('Sheet Link')
            await ctx.send(embed=embed)
            return

        curr_cat = str(ctx.message.channel.category)
        curr_cat_id = str(ctx.message.channel.category_id)
        curr_guild = str(ctx.message.channel.guild)
        curr_sheet = str(args[0])
        curr_sheet_link = f"https://docs.google.com/spreadsheets/d/{curr_sheet}/"

        idx,prev_sheet = self.findsheettether(curr_cat_id)
        prev_sheet_link = f"https://docs.google.com/spreadsheets/d/{prev_sheet}/"

        allvals = self.category_tether_tab.get_all_values()

        try:
            test_category_tether_tab = self.gspread_client.open_by_key(curr_sheet).sheet1
            pass
        except Exception as e:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"Error",
                             value=f"There is no sheet currently existing at [Google sheet at link]({curr_sheet_link}). Did you forget to set your sheet as 'Anyone with the link can edit'?",
                             inline=False)
            await ctx.send(embed=embed)
            return

        if idx == 0:
            values = [curr_cat_id, curr_guild + " - " + curr_cat, curr_sheet]
            self.category_tether_tab.append_row(values)
        else:
            values = [[curr_cat_id, curr_guild + " - " + curr_cat, curr_sheet]]
            rownum = "A"+str(idx)+":C"+str(idx)
            self.category_tether_tab.update(rownum, values)
        embed = discord_utils.create_embed()
        embed.add_field(name=f"Successful",
                         value=f"The category **{curr_cat}** is now tethered to the [Google sheet at link]({curr_sheet_link})",
                         inline=False)
        msg = await ctx.send(embed=embed)



    @commands.command(name="removesheettether")
    async def removesheettether(self, ctx, *args):
        print("Received removesheettether")
        curr_cat = str(ctx.message.channel.category)
        curr_cat_id = str(ctx.message.channel.category_id)

        idx,curr_sheet = self.findsheettether(curr_cat_id)
        curr_sheet_link = f"https://docs.google.com/spreadsheets/d/{curr_sheet}/"

        if idx == 0:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"Error",
                value=f"The category **{curr_cat}** is not tethered to any Google sheet.",
                inline=False)
            await ctx.send(embed=embed)
        else:
            self.category_tether_tab.delete_row(idx)
            embed = discord_utils.create_embed()
            embed.add_field(name=f"Successful",
                             value=f"The category **{curr_cat}** is no longer tethered to the [Google sheet at link]({curr_sheet_link})",
                             inline=False)
            await ctx.send(embed=embed)


    @commands.command(name="displaysheettether")
    async def displaysheettether(self, ctx, *args):
        print("Received displaysheettether")
        curr_cat = str(ctx.message.channel.category)
        curr_cat_id = str(ctx.message.channel.category_id)

        idx,curr_sheet = self.findsheettether(curr_cat_id)
        curr_sheet_link = f"https://docs.google.com/spreadsheets/d/{curr_sheet}/"

        if idx == 0:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"Error",
                value=f"The category **{curr_cat}** is not tethered to any Google sheet.",
                inline=False)
            await ctx.send(embed=embed)
        else:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"Result",
                             value=f"The category **{curr_cat}** is currently tethered to the [Google sheet at link]({curr_sheet_link})",
                             inline=False)
            await ctx.send(embed=embed)


    @commands.command(name="sheetcreatetab")
    async def sheetcreatetab(self, ctx, *args):
        print("Received sheetcreatetab")
        if len(args) < 1:
            embed = discord_utils.create_no_argument_embed('Tab Name')
            await ctx.send(embed=embed)
            return
        tab_name = str(args[0])

        curr_cat = str(ctx.message.channel.category)        
        curr_cat_id = str(ctx.message.channel.category_id)

        idx,curr_sheet = self.findsheettether(curr_cat_id)
        curr_sheet_link = f"https://docs.google.com/spreadsheets/d/{curr_sheet}/"

        if idx == 0:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"Error",
                value=f"The category **{curr_cat}** is not tethered to any Google sheet.",
                inline=False)
            await ctx.send(embed=embed)
            return

        try:
            test_gspread_client = google_utils.create_gspread_client()
            test_category_tether_tab = test_gspread_client.open_by_key(curr_sheet).worksheet("Template")
            template_id = test_category_tether_tab.id
        except Exception as e:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"Error",
                             value=f"The [Google sheet at link]({curr_sheet_link}) has no tab named 'Template'. Did you forget to add one?",
                             inline=False)
            await ctx.send(embed=embed)
            return

        try:
            test2_gspread_client = google_utils.create_gspread_client()
            test2_category_tether_tab = test2_gspread_client.open_by_key(curr_sheet).worksheet(tab_name)
            template2_id = test2_category_tether_tab.id
        except Exception as e:
            pass
        else:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"Error",
                             value=f"The [Google sheet at link]({curr_sheet_link}) already has a tab named **{tab_name}**. Cannot create a tab with same name.",
                             inline=False)
            await ctx.send(embed=embed)
            return

        try:
            test_gspread_client = google_utils.create_gspread_client()
            test_category_tether = test_gspread_client.open_by_key(curr_sheet) 
            newsheet = test_category_tether.duplicate_sheet(source_sheet_id=template_id,new_sheet_name=tab_name, insert_sheet_index=4)
        except Exception as e:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"Error",
                             value=f"Could not duplicate 'Template' tab in the [Google sheet at link]({curr_sheet_link}). Is the permission set up with 'Anyone with link can edit'?",
                             inline=False)
            await ctx.send(embed=embed)
            return

        final_sheet_link = f"https://docs.google.com/spreadsheets/d/{curr_sheet}/edit#gid={newsheet.id}"

        embed = discord_utils.create_embed()
        embed.add_field(name=f"Successful",
                         value=f"Tab **{tab_name}** has been created at [Tab link]({final_sheet_link}).",
                         inline=False)
        msg = await ctx.send(embed=embed)
        await msg.pin()
        print("Received sheetcreatetab")

def setup(bot):
    bot.add_cog(SheetsCog(bot))