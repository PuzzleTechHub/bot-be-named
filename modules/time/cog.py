import geopy
import os

from modules.time import time_utils
from nextcord.ext import commands
from utils import discord_utils

"""
Time module. Code to get time and timezone from different locations, convert timezones and similar.
Code copied/adapted from Kevslinger's Ravenclaw-Discord-Bot repo - https://github.com/kevslinger/ravenclaw-discord-bot
"""


class TimeCog(commands.Cog, name="Time"):
    """
    For timezone conversions and similar.
    """

    def __init__(self, bot):
        self.bot = bot
        self.geopy_client = geopy.geocoders.GeoNames(os.getenv("GEOPY_USERNAME"))

    @commands.command(name="time")
    async def time(self, ctx: commands.Context, *args):
        """Return the time in the specified location

        Usage: `~time Mumbai`
        Usage: `~time New York`
        Usage: `~time Perth, Australia`
        Usage: `~time Boston, Massachusetts, USA`
        Usage: `~time Tokyo, Japan`
        """
        embed = discord_utils.create_embed()

        # No location provided
        if len(args) < 1:
            embed = discord_utils.create_no_argument_embed("location")
            await discord_utils.send_message(ctx, embed)
            return
        # Allow long input (e.g. St. Louis, Missouri, USA)
        location = " ".join(args)

        timezone_dict = self.get_tz(location)
        # Unable to find the location in the geonames database
        if timezone_dict is None:
            embed.add_field(
                name="Failed",
                value=f"Cannot find location `{location}`!",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return

        names = ["Location", "Timezone", "Current Time"]
        # The DB provides a - (UTC) for west timezones but not a + for the east
        values = [
            f"{location.title()}",
            time_utils.format_utc_offset(timezone_dict),
            time_utils.format_time(timezone_dict["time"]),
        ]
        embed = discord_utils.populate_embed(names, values, inline=False)

        await discord_utils.send_message(ctx, embed)

    def get_tz(self, location: str) -> dict:
        """Get timezone from a given string"""
        tz = None
        try:
            geocode = self.geopy_client.geocode(location)
            tz = self.geopy_client.reverse_timezone(geocode.point).raw
        # Attribute Error is triggered when geocode is none (none has no attribute point)
        except AttributeError:
            pass
        return tz


def setup(bot):
    bot.add_cog(TimeCog(bot))
