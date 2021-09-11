import geopy
import os
from discord.ext import commands
from utils import discord_utils, logging_utils
from modules.time import time_utils
from datetime import datetime


class TimeCog(commands.Cog, name="Time"):
    """Get time and timezone of any location"""

    def __init__(self, bot):
        self.bot = bot

        self.geopy_client = geopy.geocoders.GeoNames(os.getenv("GEOPY_USERNAME"))

    @commands.command(name="unixtime")
    async def unixtime(self, ctx, *args):
        """Return the time given (or current time if no argument) in Unix format (1626206635)

        Usage: `~unixtime Tuesday, September 27, 2021 9pm EDT"""
        logging_utils.log_command("time", ctx.channel, ctx.author)
        embed = discord_utils.create_embed()
        if len(args) < 1:
            curr_time = int(datetime.timestamp(datetime.now()))
            embed.add_field(name="Success!", value=f"Current time is `{curr_time}`", inline=False)
        else:
            user_time = time_utils.parse_date(" ".join(args))
            if user_time is None:
                embed.add_field(name="Failed!",
                                value=f"Is {' '.join(args)} a valid time?",
                                inline=False)
                await ctx.send(embed=embed)
                return
            unix_time = int(datetime.timestamp(user_time))
            embed.add_field(name="Success!",
                            value=f"The Unix Time at {' '.join(args)} is `{unix_time}`",
                            inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="time")
    async def time(self, ctx, *args):
        """Return the time in the specified location

        Usage: `~time location`"""
        logging_utils.log_command("time", ctx.channel, ctx.author)
        # No location provided
        if len(args) < 1:
            embed = discord_utils.create_no_argument_embed("location")
            await ctx.send(embed=embed)
            return
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
                  format_gmt_offset(timezone_dict),
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
    date = datetime.strptime(time, "%Y-%m-%d %H:%M")
    return date.strftime('%B %d, %H:%M')


def format_gmt_offset(timezone_dict):
    """Find GMT offset (include dst if applicable)"""
    raw_offset = timezone_dict['gmtOffset']
    dst_offset = timezone_dict['dstOffset']
    if raw_offset == dst_offset:
        return f"{timezone_dict['timezoneId']} (" + (
            "+" if timezone_dict['gmtOffset'] > 0 else "") + f"{timezone_dict['gmtOffset']})"
    else:
        return f"{timezone_dict['timezoneId']} (" + (
            "+" if timezone_dict['gmtOffset'] > 0 else "") + f"{timezone_dict['gmtOffset']}/" + \
                ("+" if timezone_dict['dstOffset'] > 0 else "") + f"{timezone_dict['dstOffset']})"


def setup(bot):
    bot.add_cog(TimeCog(bot))