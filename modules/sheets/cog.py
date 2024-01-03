import googleapiclient
from utils import discord_utils, google_utils, logging_utils, command_predicates
from modules.sheets import sheets_constants, sheet_utils
import constants
import nextcord
from nextcord import TextChannel, CategoryChannel
from nextcord.ext import commands
from nextcord.ext.tasks import loop

import os
import httplib2
from googleapiclient import discovery
import database
from sqlalchemy.orm import Session
import asyncio
import shutil
from typing import Union,Literal


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

    def validate_sheet(self, sheet, required_tabs = ['Template','Meta Template','Overview']):
        """Check the open sheet for required tabs
        Returns None on success or an error message on failure
        """
        
        #check for specific tabs
        for tab_name in required_tabs:
            try:
                template_id = sheet.worksheet(tab_name).id
            except gspread.exceptions.WorksheetNotFound:
                return f'The [sheet]({sheet.url}) has no "{tab_name}" tab.'
        
        #all good
        return None

    @command_predicates.is_solver()
    @commands.command(name='setsheet',aliases=['tether'])
    async def set_sheet(self, ctx,
        sheet_key_or_link : str,
        what : Union[TextChannel, CategoryChannel, str] = 'channel'
    ):
        """Sets the sheet to use for the specified category or channel; use 'category' or 'channel' for the current"""
        logging_utils.log_command('setsheet', ctx.guild, ctx.channel, ctx.author)
        
        if isinstance(what, str):
            if what.startswith('cat'):
                what = ctx.channel.category
            elif what.startswith('chan'):
                what = ctx.channel
            else:
                raise commands.BadArgument('Argument 2 must be channel or category name or "channel" or "category"')

        #open the sheet
        sheet = sheet_utils.open_by_url_or_key(self.gspread_client, sheet_key_or_link)

        if sheet is None:
            error = f'Unable to open the sheet "{sheet_key_or_link}". Did you forget to set "Anyone with the link can edit?"'
        else:
            #check the sheet
            error = self.validate_sheet(sheet)

        if error is None:
            #add to the database
            sheet_utils.set_sheet_generic(sheet.url, ctx.guild, what)
            status = constants.SUCCESS
            message = f'The {whattype} {what.mention} is now tethered to [the given sheet]({proposed_sheet.url}).'
        else:
            status = constants.FAILED
            message = f'Error: {error}'

        #report results
        embed = discord_utils.create_embed()
        embed.add_field(name=f'{status}!',value=message,inline=False)
        await ctx.send(embed=embed)
        return


    @command_predicates.is_solver()
    @commands.command(
        name='unsetsheet',
        aliases=[
            'removesheet','deletesheet','delsheet',
            'untether','deletetether','deltether'
        ],
    )
    async def unset_sheet(self, ctx):
        """Remove the Category or Channel tethering to the sheet.

        If a channel tether and a category tether both exist, the channel tether will always be removed first.
        See also `~tether` and `~sheetcrab` and `~sheetlion`.

        Permission Category : Solver Roles only.
        Usage : `~removetether`
        """
        logging_utils.log_command(
            "removesheettether", ctx.guild, ctx.channel, ctx.author
        )
        
        # Get category and channel information
        channel = ctx.message.channel
        category = channel.category
        thread = None
        thread_id = None
        if await discord_utils.is_thread(ctx, channel):
            thread = channel
            thread_id = thread.id
            channel = thread.parent
        channel_id = channel.id
        category_id = category.id

        sheet_url, tether_type = sheet_utils.unset_sheet(category_id, channel_id, thread_id)
        
        status = constants.SUCCESS
        if sheet_url is None:
            status = constants.FAILED
            message = f'No sheet tethered to category **{category}** or channel {channel.mention}.'
        elif tether_type == sheets_constants.THREAD:
            message = f'Thread {thread.mention} unlinked from [sheet]({sheet_url}).'
        elif tether_type == sheets_constants.CHANNEL:
            message = f'Channel {channel.mention} unlinked from [sheet]({sheet_url}).'
        elif tether_type == sheets_constants.CATEGORY:
            message = f'Category **{category}** unlinked from [sheet]({sheet_url}).'
        else:
            message = f'Sheet removed from tethers database: {sheet_url}'
        embed = discord_utils.create_embed()
        embed.add_field(name=f"{status}", value=message, inline=False)
        await ctx.send(embed=embed)


    @loop(hours=12)
    async def prune_sheets_scheduled(self):
        """Function which runs periodically to remove all tethers to channels which have been deleted"""
        #TODO: how do we log this?
        sheet_utils.prune_sheets(self.bot.guilds)

    @command_predicates.is_bot_owner_or_admin()
    @commands.command(
        name="prunesheets",
    )
    async def prune_sheets(self, ctx):
        """Remove all tethers from channels that no longer exist

        See also : ~addtether

        Permission Category : Owner or Admin only
        Usage : `~prunetethers`
        """
        logging_utils.log_command("prunesheets", ctx.guild, ctx.channel, ctx.author)
        
        pruned = sheet_utils.prune_sheets(self.bot.guilds)

        embed = discord_utils.create_embed()
        embed.add_field(
            name=f"{constants.SUCCESS}!",
            value=f"**{len(pruned)}** tethers deleted.",
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
        text_to_pin = " ".join(args)

        return await sheet_utils.chancrabgeneric(
            self.gspread_client,
            ctx,
            chan_name,
            "chan",
            is_meta=False,
            text_to_pin=text_to_pin,
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
        text_to_pin = " ".join(args)

        return await sheet_utils.chancrabgeneric(
            self.gspread_client,
            ctx,
            chan_name,
            chan_or_thread="chan",
            is_meta=True,
            text_to_pin=text_to_pin,
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
        if await discord_utils.is_thread(ctx, curr_chan):
            curr_thread_id = ctx.message.channel.id
            curr_chan_id = ctx.message.channel.parent.id

        curr_chan_or_cat_row, tether_type = sheet_utils.get_sheet(
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
        Usage : `~sheetmetatab TabName`
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
            tether_db_result, _ = sheet_utils.get_sheet(
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

        sheet = sheet_utils.open_by_url_or_key(
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

    


def setup(bot):
    bot.add_cog(SheetsCog(bot))
