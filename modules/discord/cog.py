import geopy
import os
from discord.ext import commands
from utils import discord_utils
from datetime import datetime

class DiscordCog(commands.Cog, name="Discord"):
    """Discord Utility Commands"""

    def __init__(self, bot):
        self.bot = bot


    @commands.command(name="stats")
    async def stats(self, ctx, *args):
        print("Received stats")
        return 0

def setup(bot):
    bot.add_cog(DiscordCog(bot))