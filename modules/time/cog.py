import geopy
import os
from discord.ext import commands
from utils import discord_utils
import datetime

class TimeCog(commands.Cog, name="Time"):
    """Opens up the Casino"""

    def __init__(self, bot):
        self.bot = bot

        self.geopy_client = geopy.geocoders.GeoNames(os.getenv("GEOPY_USERNAME"))

    @commands.command(name="time")
    async def time(self, ctx, *args):
        """Return the time in the specified location"""
        print("Received time")
        # Allow long input (e.g. St. Louis, Missouri, USA)
        location = " ".join(args)

        timezone_dict = self.get_tz(location)
        # Unable to find the location in the geonames database
        if timezone_dict is None:
            embed = discord_utils.create_embed()
            embed.add_field(name="Error!", value=f"Cannot find {location}!", inline=False)
            await ctx.send(embed=embed)
            return

        names = ["Location",
                 "Timezone",
                 "Current Time"]
        # The DB provides a - (GMT) for west timezones but not a + for the east
        values = [f"{location.title()}",
                  f"{timezone_dict['timezoneId']} (" + ("+" if timezone_dict['gmtOffset'] > 0 else "") + f"{timezone_dict['gmtOffset']})",
                  format_time(timezone_dict['time'])]
        embed = discord_utils.populate_embed(names, values, inline=False)

        await ctx.send(embed=embed)


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


def format_time(time):
    """Rearrange time str. Comes in as YYYY-MM-DD HH:MM, change to MM-DD-YYYY HH:MM"""
    date = datetime.datetime.strptime(time, "%Y-%m-%d %H:%M")
    return f"{date.month}-{date.day}-{date.year} {date.hour}:{date.minute}"


def setup(bot):
    bot.add_cog(TimeCog(bot))