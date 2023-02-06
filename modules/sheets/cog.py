import googleapiclient
from utils import discord_utils, google_utils, logging_utils, command_predicates
from modules.sheets import sheets_constants, sheet_utils
import constants
from nextcord.ext import commands
from nextcord.ext.tasks import loop
import nextcord
import os
import gspread
import httplib2
from googleapiclient import discovery
import database
from sqlalchemy.sql.expression import insert
from sqlalchemy.orm import Session
import asyncio
import shutil
from typing import Union
from emoji import EMOJI_ALIAS_UNICODE_ENGLISH as EMOJIS


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

        See also `~sheettab`.

        Permission Category : Solver Roles only.
        Usage : `~tether SheetLink`
        """
        logging_utils.log_command("addsheettether", ctx.guild, ctx.channel, ctx.author)
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

        See also `~sheettab`.

        Permission Category : Solver Roles only.
        Usage : `~chantether SheetLink`
        """
        logging_utils.log_command(
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
            "removesheettether",
            "deltether",
            "removetetherlion",
            "deltetherlion",
            "unhunt",
            "huntnt",
            "unhuntlion",
            "huntntlion",
        ],
    )
    async def removesheettether(self, ctx):
        """Remove the Category or Channel tethering to the sheet.

        If a channel tether and a category tether both exist, the channel tether will always be removed first.
        See also `~addtether` and `~sheettab`.

        Permission Category : Solver Roles only.
        Usage : `~removetether`
        """
        logging_utils.log_command(
            "removesheettether", ctx.guild, ctx.channel, ctx.author
        )
        embed = discord_utils.create_embed()

        # Get category and channel information
        curr_cat = ctx.message.channel.category.name
        curr_cat_id = str(ctx.message.channel.category_id)
        curr_chan = ctx.message.channel
        curr_chan_id = str(ctx.message.channel.id)

        curr_thread_id = None
        if curr_chan.type in {
            nextcord.ChannelType.news_thread,
            nextcord.ChannelType.public_thread,
            nextcord.ChannelType.private_thread,
        }:
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

    @command_predicates.is_owner_or_admin()
    @commands.command(
        name="prunetethers",
    )
    async def prunetethers(self, ctx):
        """Remove all tethers from channels that no longer exist

        See also : ~addtether

        Permission Category : Owner or Admin only
        Usage : `~prunetethers`
        """
        logging_utils.log_command("prunetethers", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        to_delete = await self.prune_tethers()

        embed.add_field(
            name=f"{constants.SUCCESS}!",
            value=f"**{len(to_delete)}** tethers deleted.",
            inline=False,
        )
        await ctx.send(embed=embed)

    @command_predicates.is_solver()
    @commands.command(name="chancrab", aliases=["channelcrab", "channelcreatetab"])
    async def channelcreatetab(self, ctx, chan_name: str, *args):
        """Create new channel, then a New tab on the sheet that is currently tethered to this category, then pins links to the channel, if any.

        This requires a tethered sheet (See `~addtether`) and a tab named "Template" on the sheet.
        Also the sheet must be 'Anyone with the link can edit' or the bot email get edit access.

        Permission Category : Solver Roles only.
        Usage : `~chancrab PuzzleName`
        Usage : `~chancrab PuzzleName linktopuzzle`
        """
        logging_utils.log_command(
            "channelcreatetab", ctx.guild, ctx.channel, ctx.author
        )
        embed = discord_utils.create_embed()

        return await sheet_utils.chancrabgeneric(
            self.gspread_client, ctx, chan_name, "chan", *args
        )

    @command_predicates.is_solver()
    @commands.command(name="metacrab", aliases=["channelcreatemetatab"])
    async def channelcreatemetatab(self, ctx, chan_name: str, *args):
        """Create new channel, then a New tab on the sheet that is currently tethered to this category, then pins links to the channel, if any.

        FOR METAPUZZLES ONLY

        This requires a tethered sheet (See `~addtether`) and a tab named "Template" on the sheet.
        Also the sheet must be 'Anyone with the link can edit' or the bot email get edit access.

        Permission Category : Solver Roles only.
        Usage : `~metacrab PuzzleName`
        Usage : `~metacrab PuzzleName linktopuzzle`
        """
        logging_utils.log_command(
            "channelcreatetab", ctx.guild, ctx.channel, ctx.author
        )
        embed = discord_utils.create_embed()

        return await sheet_utils.metacrabgeneric(
            self.gspread_client, ctx, chan_name, "chan", *args
        )

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
        logging_utils.log_command(
            "displaysheettether", ctx.guild, ctx.channel, ctx.author
        )
        embed = discord_utils.create_embed()

        curr_cat = ctx.message.channel.category.name
        curr_cat_id = str(ctx.message.channel.category_id)
        curr_chan = ctx.message.channel
        curr_chan_id = str(ctx.message.channel.id)

        curr_thread_id = None
        if curr_chan.type in {
            nextcord.ChannelType.news_thread,
            nextcord.ChannelType.public_thread,
            nextcord.ChannelType.private_thread,
        }:
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
    @commands.command(name="sheetcrab", aliases=["sheettab", "sheetcreatetab"])
    async def sheetcreatetab(self, ctx, tab_name: str, to_pin: str = ""):
        """Create a New tab on the sheet that is currently tethered to this category

        This requires a tethered sheet (See `~addtether`) and a tab named "Template" on the sheet.
        Also the sheet must be 'Anyone with the link can edit' or the bot email get edit access.

        Permission Category : Solver Roles only.
        Usage : `~sheetcrab TabName`
        Usage : `~sheetcrab TabName pin` (Pins the new tab on creation)
        """
        logging_utils.log_command("sheetcreatetab", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        await sheet_utils.sheetcrabgeneric(self.gspread_client, ctx, tab_name, to_pin)

    @command_predicates.is_solver()
    @commands.command(
        name="sheetmetacrab", aliases=["sheetmetatab", "sheetcreatemetatab"]
    )
    async def sheetcreatemetatab(self, ctx, tab_name: str):
        """Create a New tab on the sheet that is currently tethered to this category

        This requires a tethered sheet (See `~addtether`) and a tab named "Template" on the sheet.
        Also the sheet must be 'Anyone with the link can edit' or the bot email get edit access.

        Permission Category : Solver Roles only.
        Usage : `~sheettab TabName`
        """
        logging_utils.log_command("sheetcreatetab", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        curr_chan = ctx.message.channel
        curr_cat = ctx.message.channel.category
        curr_sheet_link, newsheet = await sheet_utils.sheetcreatetabmeta(
            self.gspread_client, ctx, curr_chan, curr_cat, tab_name
        )

        # Error, already being handled at the generic function
        if not curr_sheet_link or newsheet is None:
            return

        # This link is customized for the newly made tab
        final_sheet_link = curr_sheet_link + "/edit#gid=" + str(newsheet.id)

        embed.add_field(
            name=f"{constants.SUCCESS}!",
            value=f"Tab **{tab_name}** has been created at [Tab link]({final_sheet_link}).",
            inline=False,
        )
        msg = await ctx.send(embed=embed)
        # Pin message to the new channel
        embed_or_none = await discord_utils.pin_message(msg)
        if embed_or_none is not None:
            await ctx.send(embed=embed_or_none)

        return curr_sheet_link, newsheet

    @command_predicates.is_solver()
    @commands.command(name="downloadsheet", aliases=["savesheet"])
    async def downloadsheet(self, ctx, sheet_url=None):
        """Download the channel/category's currently tethered sheet. You can supply a URL or it will
        use the currently tethered sheet.

        Permission Category : Solver Roles only.
        Usage: `~savesheet`
        """
        logging_utils.log_command("downloadsheet", ctx.guild, ctx.channel, ctx.author)
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

        sheet = sheet_utils.get_sheet_from_key_or_link(
            self.gspread_client, tether_db_result.sheet_link
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
            if serv not in botguilds:
                not_in_server.add(serv)
            else:
                serverguild = list(filter(lambda x: x.id == serv, self.bot.guilds))[0]
                # Don't delete server tethers
                if chan != serv:
                    chan_cat_threads = serverguild.channels + serverguild.threads
                    chan_cat_threads_id = list(map(lambda x: x.id, chan_cat_threads))
                    if chan not in chan_cat_threads_id:
                        to_delete.append((serv, chan))

        print("Server not in bot for these channels... probably testing version")
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
