from discord.ext import commands
from modules.admin import admin_utils
from utils import discord_utils
import constants
import json

class AdminCog(commands.Cog, name="Admin"):
    """Administrative Commands"""
    def __init(self, bot):
        self.bot = bot

    @admin_utils.is_owner_or_admin()
    @commands.command(name="setprefix")
    async def setprefix(self, ctx, prefix: str):
        print("Received setprefix")
        with open(constants.PREFIX_JSON_FILE, 'r') as f:
            prefixes = json.load(f)

        prefixes[str(ctx.guild.id)] = prefix

        with open(constants.PREFIX_JSON_FILE, 'w') as f:
            json.dump(prefixes, f)

        embed = discord_utils.create_embed()
        embed.add_field(name=constants.SUCCESS,
                        value=f"Prefix for this server set to {prefix}",
                        inline=False)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(AdminCog(bot))