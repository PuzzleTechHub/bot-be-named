from discord.ext import commands
from modules.admin import admin_utils
from utils import discord_utils, google_utils
import constants
import os
#import json

class AdminCog(commands.Cog, name="Admin"):
    """Administrative Commands"""
    def __init__(self, bot):
        self.bot = bot
        self.gspread_client = google_utils.create_gspread_client()
        self.prefix_sheet = self.gspread_client.open_by_key(os.getenv("PREFIX_SHEET_KEY")).sheet1

    @admin_utils.is_owner_or_admin()
    @commands.command(name="setprefix")
    async def setprefix(self, ctx, prefix: str):
        print("Received setprefix")
        find_cell = self.prefix_sheet.find(str(ctx.message.guild.id))
        self.prefix_sheet.update_cell(find_cell.row, find_cell.col+1, prefix)

        embed = discord_utils.create_embed()
        embed.add_field(name=constants.SUCCESS,
                        value=f"Prefix for this server set to {prefix}",
                        inline=False)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(AdminCog(bot))