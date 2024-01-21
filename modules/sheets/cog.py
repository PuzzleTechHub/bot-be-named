import googleapiclient
from modules.lion import sheets_constants
from utils import discord_utils, google_utils, logging_utils, command_predicates
from modules.sheets import sheet_utils
import constants
from nextcord.ext import commands
from nextcord.ext.tasks import loop
import nextcord
import os
import httplib2
from googleapiclient import discovery
import database
from sqlalchemy.orm import Session
import asyncio
import shutil


class SheetsCog(commands.Cog, name="Sheets"):
    """Google Sheets management commands"""

    def __init__(self, bot):
        self.bot = bot
        self.lock = asyncio.Lock()
        self.gdrive_credentials = google_utils.get_gdrive_credentials()
        self.gspread_client = google_utils.create_gspread_client()

    # Reload the google sheet every hour
    @commands.Cog.listener()
    async def on_ready(self):
        """When discord is connected"""
        if not self.prune_tethers.is_running():
            self.prune_tethers.start()

    @command_predicates.is_solver()
    @commands.command(
        name="addtether",
        aliases=["editsheettether", "tether", "edittether", "addsheettether"],
    )
    async def addsheettether(self, ctx, sheet_key_or_link: str):
        """Tethers a sheet to the current category.

        For any Google sheets commands, a tether to either category or channel (See `~chantether`) is necessary.

        See also `~sheetcrab` and `~sheetlion`.

        Permission Category : Solver Roles only.
        Usage : `~tether SheetLink`
        """
        await logging_utils.log_command(
            "addsheettether", ctx.guild, ctx.channel, ctx.author
        )
        embed = discord_utils.create_embed()

        proposed_sheet = sheet_utils.addsheettethergeneric(
            self.gspread_client, sheet_key_or_link, ctx.guild, ctx.channel.category
        )

        if proposed_sheet:
            embed.add_field(
                name=f"{constants.SUCCESS}!",
                value=f"The category **{ctx.channel.category.name}** is now tethered to the "
                f"[Google sheet at link]({proposed_sheet.url})",
                inline=False,
            )
            await ctx.send(embed=embed)
        # If we can't open the sheet, send an error and return
        else:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Sorry, we can't find a sheet there. "
                f"Did you forget to set your sheet as 'Anyone with the link can edit'?",
                inline=False,
            )
            await ctx.send(embed=embed)
            return

    @command_predicates.is_solver()
    @commands.command(
        name="chantether",
        aliases=[
            "channeltether",
            "editchantether",
            "addchantether",
            "addchannelsheettether",
            "editthreadtether",
            "addthreadtether",
            "threadtether",
        ],
    )
    async def addchannelsheettether(self, ctx, sheet_key_or_link: str):
        """Tethers a sheet to the current channel/thread

        For any Google sheets commands, a tether to either category (See `~tether`) or channel is necessary.

        See also `~sheetcrab` and `~sheetlion`.

        Permission Category : Solver Roles only.
        Usage : `~chantether SheetLink`
        """
        await logging_utils.log_command(
            "addchannelsheettether", ctx.guild, ctx.channel, ctx.author
        )
        embed = discord_utils.create_embed()

        proposed_sheet = sheet_utils.addsheettethergeneric(
            self.gspread_client, sheet_key_or_link, ctx.guild, ctx.channel
        )

        if proposed_sheet:
            embed.add_field(
                name=f"{constants.SUCCESS}",
                value=f"The channel {ctx.channel.mention} is now tethered to the "
                f"[Google sheet at link]({proposed_sheet.url})",
                inline=False,
            )
            await ctx.send(embed=embed)
        # If we can't open the sheet, send an error and return
        else:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Sorry, we can't find a sheet there. "
                f"Did you forget to set your sheet as 'Anyone with the link can edit'?",
                inline=False,
            )
            await ctx.send(embed=embed)
            return

    @command_predicates.is_solver()
    @commands.command(
        name="removetether",
        aliases=[
            "deletetether",
            "untether",
            "deltether",
            "removetetherlion",
            "deltetherlion",
        ],
    )
    async def removesheettether(self, ctx):
        """Remove the Category or Channel tethering to the sheet.

        If a channel tether and a category tether both exist, the channel tether will always be removed first.
        See also `~tether` and `~sheetcrab` and `~sheetlion`.

        Permission Category : Solver Roles only.
        Usage : `~removetether`
        """
        await logging_utils.log_command(
            "removesheettether", ctx.guild, ctx.channel, ctx.author
        )
        embed = discord_utils.create_embed()

        # Get category and channel information
        curr_cat = ctx.message.channel.category.name
        curr_cat_id = str(ctx.message.channel.category_id)
        curr_chan = ctx.message.channel
        curr_chan_id = str(ctx.message.channel.id)

        curr_thread_id = None
        if await discord_utils.is_thread(ctx, curr_chan):
            curr_thread_id = ctx.message.channel.id
            curr_chan_id = ctx.message.channel.parent.id

        curr_chan_or_cat_row, tether_type = sheet_utils.findsheettether(
            curr_cat_id, curr_chan_id, curr_thread_id
        )

        # If the tethering exists, remove it from the sheet.
        if curr_chan_or_cat_row is not None:
            sheet_link = curr_chan_or_cat_row.sheet_link
            with Session(database.DATABASE_ENGINE) as session:
                session.query(database.SheetTethers).filter_by(
                    channel_or_cat_id=curr_chan_or_cat_row.channel_or_cat_id
                ).delete()
                session.commit()
            if tether_type == sheets_constants.THREAD and curr_thread_id is not None:
                embed.add_field(
                    name=f"{constants.SUCCESS}",
                    value=f"{ctx.channel.mention}'s tether to [sheet]({sheet_link}) has been removed!",
                    inline=False,
                )
            elif tether_type == sheets_constants.CHANNEL and curr_thread_id is not None:
                embed.add_field(
                    name=f"{constants.SUCCESS}",
                    value=f"{ctx.channel.parent.mention}'s tether to [sheet]({sheet_link}) has been removed!",
                    inline=False,
                )
            elif tether_type == sheets_constants.CHANNEL:
                embed.add_field(
                    name=f"{constants.SUCCESS}",
                    value=f"{ctx.channel.mention}'s tether to [sheet]({sheet_link}) has been removed!",
                    inline=False,
                )
            elif tether_type == sheets_constants.CATEGORY:
                embed.add_field(
                    name=f"{constants.SUCCESS}",
                    value=f"The category **{ctx.channel.category}**'s tether to [sheet]({sheet_link}) has been removed!",
                    inline=False,
                )
            # Else: Generic catch
            else:
                embed.add_field(
                    name=f"{constants.SUCCESS}",
                    value=f"The tether to [sheet]({sheet_link}) has been removed!",
                    inline=False,
                )
            await ctx.send(embed=embed)
        else:
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"The category **{curr_cat}** or the channel {curr_chan.mention} "
                f"are not tethered to any Google sheet.",
                inline=False,
            )
            await ctx.send(embed=embed)
            return

    @command_predicates.is_bot_owner_or_admin()
    @commands.command(
        name="prunetethers",
    )
    async def prunetethers(self, ctx):
        """Remove all tethers from channels that no longer exist

        See also : ~addtether

        Permission Category : Owner or Admin only
        Usage : `~prunetethers`
        """
        await logging_utils.log_command(
            "prunetethers", ctx.guild, ctx.channel, ctx.author
        )
        embed = discord_utils.create_embed()

        to_delete = await self.prune_tethers()

        embed.add_field(
            name=f"{constants.SUCCESS}!",
            value=f"**{len(to_delete)}** tethers deleted.",
            inline=False,
        )
        await ctx.send(embed=embed)

    @command_predicates.is_solver()
    @commands.command(
        name="showtether",
        aliases=["showsheettether", "displaysheettether", "displaytether"],
    )
    async def displaysheettether(self, ctx):
        """Find the sheet the category is current tethered too

        Permission Category : Solver Roles only.
        Usage : `~showtether`
        """
        await logging_utils.log_command(
            "displaysheettether", ctx.guild, ctx.channel, ctx.author
        )
        embed = discord_utils.create_embed()

        curr_cat = ctx.message.channel.category.name
        curr_cat_id = str(ctx.message.channel.category_id)
        curr_chan = ctx.message.channel
        curr_chan_id = str(ctx.message.channel.id)

        curr_thread_id = None
        if await discord_utils.is_thread(ctx, curr_chan):
            curr_thread_id = ctx.message.channel.id
            curr_chan_id = ctx.message.channel.parent.id

        curr_chan_or_cat_row, tether_type = sheet_utils.findsheettether(
            curr_cat_id, curr_chan_id, curr_thread_id
        )

        if curr_chan_or_cat_row is not None:
            curr_sheet_link = curr_chan_or_cat_row.sheet_link
            if tether_type == sheets_constants.THREAD and curr_thread_id is not None:
                embed.add_field(
                    name=f"Result",
                    value=f"The channel {curr_chan.mention} is currently tethered to the "
                    f"[Google sheet at link]({curr_sheet_link})",
                    inline=False,
                )
            elif tether_type == sheets_constants.CHANNEL and curr_thread_id is not None:
                embed.add_field(
                    name=f"Result",
                    value=f"The channel {curr_chan.parent.mention} is currently tethered to the "
                    f"[Google sheet at link]({curr_sheet_link})",
                    inline=False,
                )
            elif tether_type == sheets_constants.CHANNEL:
                embed.add_field(
                    name=f"Result",
                    value=f"The channel {curr_chan.mention} is currently tethered to the "
                    f"[Google sheet at link]({curr_sheet_link})",
                    inline=False,
                )
            elif tether_type == sheets_constants.CATEGORY:
                embed.add_field(
                    name=f"Result",
                    value=f"The category **{curr_cat}** is currently tethered to the "
                    f"[Google sheet at link]({curr_sheet_link})",
                    inline=False,
                )
            # Generic catch
            else:
                embed.add_field(
                    name=f"Result",
                    value=f"There is a tether to [Google sheet at link]({curr_sheet_link})",
                    inline=False,
                )
            await ctx.send(embed=embed)
        else:
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"Neither the category **{curr_cat}** nor the channel {curr_chan.mention} "
                f"are tethered to any Google sheet.",
                inline=False,
            )
            await ctx.send(embed=embed)
            return

    @command_predicates.is_solver()
    @commands.command(name="downloadsheet", aliases=["savesheet"])
    async def downloadsheet(self, ctx, sheet_url=None):
        """Download the channel/category's currently tethered sheet. You can supply a URL or it will
        use the currently tethered sheet.

        Permission Category : Solver Roles only.
        Usage: `~savesheet`
        """
        await logging_utils.log_command(
            "downloadsheet", ctx.guild, ctx.channel, ctx.author
        )
        embed = discord_utils.create_embed()

        http = self.gdrive_credentials.authorize(httplib2.Http())
        service = discovery.build("drive", "v3", http=http)

        if sheet_url is None:
            tether_db_result, _ = sheet_utils.findsheettether(
                ctx.channel.id, ctx.channel.category.id
            )
            if tether_db_result is None:
                embed.add_field(
                    name=f"{constants.FAILED}",
                    value=f"There is no sheet tethered to {ctx.channel.mention} or the "
                    f"**{ctx.channel.category.name}** category. You'll need to supply a sheet link "
                    f"for me to download.",
                )
                await ctx.send(embed=embed)
                return
            sheet_url = tether_db_result.sheet_link

        
        sheet = sheet_utils.get_sheet_from_key_or_link(
            self.gspread_client, sheet_url
        )
        if sheet is None:
            embed.add_field(
                name=f"{constants.FAILED}",
                value="I can't find that sheet. Are you sure the link is a valid sheet with permissions set to "
                "'Anyone with the link can edit'?",
                inline=False,
            )
            await ctx.send(embed=embed)
            return

        try:
            request = service.files().export_media(
                fileId=sheet.id, mimeType=sheets_constants.MIMETYPE
            )
            response = request.execute()
        except googleapiclient.errors.HttpError:
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"Sorry, your sheet is too large and cannot be downloaded.",
                inline=False,
            )
            await ctx.send(embed=embed)
            return

        download_dir = "saved_sheets"
        download_path = os.path.join(download_dir, sheet.title + ".xlsx")
        async with self.lock:
            if os.path.exists(download_dir):
                shutil.rmtree(download_dir)
            os.mkdir(download_dir)
            with open(download_path, "wb") as sheet_file:
                sheet_file.write(response)
                file_size = sheet_file.tell()
                if file_size > ctx.guild.filesize_limit:
                    embed = discord_utils.create_embed()
                    embed.add_field(
                        name=f"{constants.FAILED}",
                        value=f"Sorry, your sheet is {(file_size/constants.BYTES_TO_MEGABYTES):.2f}MB big, "
                        "but I can only send files of up to "
                        "{(ctx.guild.filesize_limit/constants.BYTES_TO_MEGABYTES):.2f}MB.",
                        inline=False,
                    )
                    await ctx.send(embed=embed)
                    return

            await ctx.send(file=nextcord.File(download_path))

    @loop(hours=12)
    async def prune_tethers(self):
        """Function which runs periodically to remove all tethers to channels which have been deleted"""
        with Session(database.DATABASE_ENGINE) as session:
            result = session.query(database.SheetTethers)

        listresults = list(result)
        to_delete = []
        not_in_server = set()
        for x in listresults:
            serv = x.server_id
            chan = x.channel_or_cat_id
            botguilds = list(map(lambda x: x.id, self.bot.guilds))
            if serv == 0:
                pass
            elif serv not in botguilds and serv != 0:
                not_in_server.add(serv)
            else:
                serverguild = list(filter(lambda x: x.id == serv, self.bot.guilds))[0]
                # Don't delete server tethers
                if chan != serv:
                    chan_cat_threads = serverguild.channels + serverguild.threads
                    chan_cat_threads_id = list(map(lambda x: x.id, chan_cat_threads))
                    # All channels and threads currently active in the server, aka the bot can find it
                    if chan not in chan_cat_threads_id:
                        to_delete.append((serv, chan))

        print(
            "Server not in bot for these channels... Probably running the test version of the bot"
        )
        print(list(not_in_server))

        print()
        for x in to_delete:
            session.query(database.SheetTethers).filter_by(
                server_id=x[0], channel_or_cat_id=x[1]
            ).delete()
            session.commit()
            print(f"Deleting tether at {x[0]} - {x[1]}")
        return to_delete


def setup(bot):
    bot.add_cog(SheetsCog(bot))
