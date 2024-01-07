import googleapiclient
from utils import discord_utils, google_utils, logging_utils, command_predicates
from modules.sheets import sheets_constants, sheet_utils
import constants
import nextcord
from nextcord import TextChannel, CategoryChannel, Guild
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
        if not self.prune_sheets_scheduled.is_running():
            self.prune_sheets_scheduled.start()



    ## Sheet management:
    # set_sheet <sheet-link> <target>
    # unset_sheet
    # prune_sheets
    # prune_sheets_scheduled

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
        sheet_link : str,
        target : Union[TextChannel, CategoryChannel, Guild, str] = 'category'
    ):
        """Sets the sheet for the given channel, category, or guild; use 'category','channel', or 'guild' for the current such."""
        logging_utils.log_command('setsheet', ctx.guild, ctx.channel, ctx.author)
        
        if isinstance(target, str):
            #branch based on common prefix
            if 'category'.startswith(target) and len(target) > 1:
                target = ctx.channel.category
            elif 'channel'.startswith(target) and len(target) > 1:
                target = ctx.channel
            elif 'guild'.startswith(target) or 'template'.startswith(target):
                target = ctx.guild
            else:
                raise commands.BadArgument('Argument 2 must be "channel", "category", "template", or "guild" or the name of such.')
        
        if isinstance(target, TextChannel):
            ttype = 'channel'
            tname = target.mention
        elif isinstance(target, CategoryChannel):
            ttype = 'category'
            tname = f'**{target.mention}**'
        elif isinstance(target, Guild):
            ttype = 'guild'
            tname = f'***{target.name}***'
        else:
            raise commands.BadArgument('Argument 2 must refer to a channel, category, or guild.')

        #open the sheet
        sheet = sheet_utils.open_by_url_or_key(self.gspread_client, sheet_link)

        if sheet is None:
            error = f'Unable to open the sheet "{sheet_link}". Did you forget to set "Anyone with the link can edit?"'
        else:
            #check the sheet
            error = self.validate_sheet(sheet)

        if error is None:
            #add to the database
            sheet_utils.set_sheet_generic(sheet.url, ctx.guild, target)
            status = constants.SUCCESS
            message = f'The {ttype} {tname} is now tethered to [the given sheet]({sheet.url}).'
        else:
            status = constants.FAILED
            message = f'Error tethering {ttype} {tname}: {error}'

        #report results
        await discord_utils.send_embed(ctx, name=f'{status}!',value=message,inline=False)
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
        
        await discord_utils.send_embed(ctx, name=f'{status}', value=message, inline=False)


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

        await discord_utils.send_embed(ctx,
            name=f"{constants.SUCCESS}!",
            value=f"**{len(pruned)}** tethers deleted.",
            inline=False,
        )

    @loop(hours=12)
    async def prune_sheets_scheduled(self):
        """Function which runs periodically to remove all tethers to channels which have been deleted"""
        #TODO: how do we log this?
        sheet_utils.prune_sheets(self.bot.guilds)

    ## Puzzle management
    # new_round : creates a category linked to a copy of the guild template sheet
    # new_puzzle : create a new tab in the category's sheet
    # status : set puzzle status, change channel name?
    # archive : move puzzle to archive category

    async def new_round(self, ctx, round_name : str, channel_name : str = 'main-not-a-puzzle'):
        logging_utils.log_command("create_from_template", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()
        
        #create the category and a single channel in it
        category_name = round_name.upper()
        category, error = None,None
        try:
            category = await ctx.guild.create_category(category_name)
            channel = await ctx.guild.create_text_channel(channel_name, category=category)
        except nextcord.Forbidden:
            error = 'Permission denied!'
        except:
            error = 'Failed!'
        if error is not None:
            await discord_utils.send_embed(ctx, name=f'{constants.FAILED}!',
                value=f'Failed to create category "{category_name}" and/or channel "{channel_name}": {error}',
                inline=False)
            return
        message = f'Round created with category **{category_name}** and channel {channel.mention}.'
        #now copy the template and link it to the category
        template, _ = sheet_utils.get_sheet((ctx.guild.id))
        
        if template is None:
            await discord_utils.send_embed(ctx, name=f'{constants.SUCCESS}!',
                value=f'{message}. No sheet template was found, use `~setsheet SHEET_URL` to set the round\'s sheet. Use `~setsheet SHEET_URL template` to set the template sheet.',
                inline=False)
            return

        try:
            template = self.gspread_client.open_by_url(template)

            new_sheet = self.gspread_client.copy(
                file_id=template.id,
                title=category_name,
                copy_permissions=True,
                folder_id=None,
                copy_comments=True)

            overview = new_sheet.worksheet("Overview")
            overview.update("C1", hunturl)
        except gspread.exceptions.APIError:
            embed.add_field(name=f'{constants.SUCCESS} but also {constants.FAILED}!',
                value=f'{message} but failed to copy the [template sheet]({template.url}). Are the permissions set correctly?',
                inline=False)
            await ctx.send(embed=embed)
            return

        sheet_utils.set_sheet_generic(new_sheet.url, ctx.guild, category)


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

        curr_chan_or_cat_row, id_index = sheet_utils.get_sheet((curr_thread_id, curr_chan_id, curr_cat_id))
        
        if curr_chan_or_cat_row is not None:
            tether_type = (sheets_constants.THREAD, sheets_constants.CHANNEL, sheets_constants.CATEGORY)[id_index]
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
            tether_db_result, _ = sheet_utils.get_sheet((
                ctx.channel.id, ctx.channel.category.id
            ))
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
