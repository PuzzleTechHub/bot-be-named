import nextcord
import geopy
import datetime
import os
import pytz
import constants

from modules.time import time_utils
from nextcord.ext import commands
from nextcord.ext.tasks import loop
from utils import logging_utils, time_utils, google_utils, discord_utils

# Code partially taken from Ravenclaw-Discord-Bot, also a bot by Kevslinger
# https://github.com/kevslinger/ravenclaw-discord-bot


class TimeCog(commands.Cog, name="Time"):
    """Get time and timezone of any location"""

    def __init__(self, bot):
        self.bot = bot
        self.geopy_client = geopy.geocoders.GeoNames(os.getenv("GEOPY_USERNAME"))

        self.gspread_client = google_utils.create_gspread_client()
        self.main_data_sheet = self.gspread_client.open_by_key(
            os.getenv("MASTER_SHEET_KEY")
        )
        self.reminder_tab = self.main_data_sheet.worksheet("Reminders")

    @commands.Cog.listener()
    async def on_ready(self):
        """When discord is connected"""
        if not self.check_reminders.is_running():
            self.check_reminders.start()

    @commands.command(name="countdown")
    async def countdown(self, ctx, *args):
        """Uses discord message time formatting to provide a countdown

        Usage: `~countdown September 22, 2021 9:00pm EDT`
        """
        logging_utils.log_command("countdown", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        if len(args) < 1:
            await ctx.send(embed=embed)
            return

        user_time = time_utils.parse_date(" ".join(args))

        if user_time is None:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Is {' '.join(args)} a valid time?",
                inline=False,
            )
            await ctx.send(embed=embed)
            return

        unix_time = int(datetime.datetime.timestamp(user_time))
        embed.add_field(
            name=f"{' '.join(args)}",
            value=f"<t:{unix_time}:f>\n"
            f"`<t:{unix_time}:R>` - <t:{unix_time}:R>\n\n"
            f"[Guide to format](https://discord.com/developers/docs/reference#message-formatting-formats)",
        )
        await ctx.send(embed=embed)

    @commands.command(name="time")
    async def time(self, ctx, *args):
        """Return the time in the specified location

        Usage: `~time Mumbai`
        """
        logging_utils.log_command("time", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

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
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"Cannot find {location}!",
                inline=False,
            )
            await ctx.send(embed=embed)
            return

        names = ["Location", "Timezone", "Current Time"]
        # The DB provides a - (GMT) for west timezones but not a + for the east
        values = [
            f"{location.title()}",
            format_gmt_offset(timezone_dict),
            format_time(timezone_dict["time"]),
        ]
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

    @loop(minutes=1)
    async def check_reminders(self):
        """Check the Remindme sheet for all reminders"""
        utctime = datetime.datetime.now(tz=pytz.UTC)

        rows_to_remind = []
        idxs_to_delete = []

        # Server Channel Time Username ID Event
        reminders = self.reminder_tab.get_all_values()
        # Skip header row
        for i, row in enumerate(reminders[1:]):
            deadline_time = time_utils.parse_date(
                row[3], from_tz=row[3].split()[-1], to_tz=constants.UTC
            )
            # Check if it's time to remind the person
            if (
                deadline_time.year != utctime.year
                or deadline_time.month != utctime.month
                or deadline_time.day != utctime.day
                or deadline_time.minute != utctime.minute
            ):
                continue

            # If we're here, that means it's time to announce
            rows_to_remind.append(row)
            idxs_to_delete.append(i)

        for row in rows_to_remind:
            author = self.bot.get_user(int(row[5]))
            channel = self.bot.get_channel(int(row[2]))

            await channel.send(f"{author.mention}, please don't forget to `{row[6]}`")

        idxs_to_delete = sorted(idxs_to_delete, reverse=True)
        # enumerate is 0-index, but google is 1-index plus we skip header row so we need +2
        for idx in idxs_to_delete:
            self.reminder_tab.delete_row(idx + 2)

    @commands.command(name="remindme", aliases=["remind", "reminder"])
    async def remindme(self, ctx, *args):
        """
        Reminds you to do something later. Pick one of days (d), hours (h), minutes (m)

        Usage: `~remindme 24h Take out the trash`
        """
        logging_utils.log_command("remindme", ctx.guild, ctx.channel, ctx.author)

        utctime = datetime.datetime.now(tz=pytz.UTC)

        # Note: I'm being REALLY loose on the arguments here
        if "d" in args[0] and args[0][0] != "-":
            remind_time = utctime + datetime.timedelta(days=int(args[0][:-1]))
        elif "h" in args[0] and args[0][0] != "-":
            remind_time = utctime + datetime.timedelta(hours=int(args[0][:-1]))
        elif "m" in args[0] and args[0][0] != "-":
            remind_time = utctime + datetime.timedelta(minutes=int(args[0][:-1]))
        else:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}!",
                value="Must supply a positive unit of time! (e.g. 5d, 24h, 30m)",
                inline=False,
            )
            await ctx.send(embed=embed)
            return

        self.reminder_tab.append_row(
            [
                ctx.guild.name,
                ctx.channel.name,
                str(ctx.channel.id),
                remind_time.strftime(constants.SHEET_DATETIME_FORMAT),
                ctx.author.name,
                str(ctx.author.id),
                " ".join(args[1:]),
            ]
        )

        embed = discord_utils.create_embed()
        embed.add_field(
            name=f"{constants.SUCCESS}!",
            value=f"I will remind you to `{' '.join(args[1:])}` <t:{int(datetime.datetime.timestamp(remind_time))}:R>",
            inline=False,
        )
        await ctx.send(embed=embed)


def format_time(time):
    """Rearrange time str. Comes in as YYYY-MM-DD HH:MM, change to MM-DD-YYYY HH:MM"""
    date = datetime.datetime.strptime(time, "%Y-%m-%d %H:%M")
    return date.strftime("%B %d, %H:%M")


def format_gmt_offset(timezone_dict):
    """Find GMT offset (include dst if applicable)"""
    raw_offset = timezone_dict["gmtOffset"]
    dst_offset = timezone_dict["dstOffset"]
    if raw_offset == dst_offset:
        return (
            f"{timezone_dict['timezoneId']} ("
            + ("+" if timezone_dict["gmtOffset"] > 0 else "")
            + f"{timezone_dict['gmtOffset']})"
        )
    else:
        return (
            f"{timezone_dict['timezoneId']} ("
            + ("+" if timezone_dict["gmtOffset"] > 0 else "")
            + f"{timezone_dict['gmtOffset']}/"
            + ("+" if timezone_dict["dstOffset"] > 0 else "")
            + f"{timezone_dict['dstOffset']})"
        )


def setup(bot):
    bot.add_cog(TimeCog(bot))
