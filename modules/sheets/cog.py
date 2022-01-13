import googleapiclient
from utils import discord_utils, google_utils, logging_utils, command_predicates
from modules.sheets import sheets_constants
import constants
from discord.ext import commands
import discord
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

    @command_predicates.is_verified()
    @commands.command(
        name="addsheettether",
        aliases=["editsheettether", "tether", "edittether", "addtether"],
    )
    async def addsheettether(self, ctx, sheet_key_or_link: str):
        """Tethers a sheet to the current category.

        For any Google sheets commands, a tether to either category or channel (See `~chantether`) is necessary.

        See also `~sheettab`.

        Category : Verified Roles only.
        Usage : `~tether SheetLink`
        """
        logging_utils.log_command("addsheettether", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        proposed_sheet = self.addsheettethergeneric(
            sheet_key_or_link, ctx.guild, ctx.channel.category
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

    @command_predicates.is_verified()
    @commands.command(
        name="addchannelsheettether",
        aliases=["channeltether", "editchantether", "addchantether", "chantether"],
    )
    async def addchannelsheettether(self, ctx, sheet_key_or_link: str):
        """Tethers a sheet to the current channel

        For any Google sheets commands, a tether to either category (See `~tether`) or channel is necessary.

        See also `~sheettab`.

        Category : Verified Roles only.
        Usage : `~chantether SheetLink`
        """
        logging_utils.log_command(
            "addchannelsheettether", ctx.guild, ctx.channel, ctx.author
        )
        embed = discord_utils.create_embed()

        proposed_sheet = self.addsheettethergeneric(
            sheet_key_or_link, ctx.guild, ctx.channel
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

    @command_predicates.is_verified()
    @commands.command(
        name="removesheettether",
        aliases=[
            "deletetether",
            "removetether",
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

        Category : Verified Roles only.
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

        curr_chan_or_cat_row, tether_type = self.findsheettether(
            curr_chan_id, curr_cat_id
        )
        sheet_link = curr_chan_or_cat_row.sheet_link

        # If the tethering exists, remove it from the sheet.
        if curr_chan_or_cat_row is not None:
            with Session(database.DATABASE_ENGINE) as session:
                session.query(database.SheetTethers).filter_by(
                    channel_or_cat_id=curr_chan_or_cat_row.channel_or_cat_id
                ).delete()
                session.commit()
            if tether_type == sheets_constants.CHANNEL:
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

    # TODO: PETE READ THIS
    @command_predicates.is_verified()
    @commands.command(name="channelcreatetab", aliases=["channelcrab", "chancrab"])
    async def channelcreatetab(self, ctx, chan_name: str, *args):
        """Create new channel, then a New tab on the sheet that is currently tethered to this category, then pins links to the channel, if any.

        This requires a tethered sheet (See `~addtether`) and a tab named "Template" on the sheet.
        Also the sheet must be 'Anyone with the link can edit' or the bot email get edit access.

        Category : Verified Roles only.
        Usage : `~sheetcrab PuzzleName`
        Usage : `~sheetcrab PuzzleName linktopuzzle`
        """
        logging_utils.log_command(
            "channelcreatetab", ctx.guild, ctx.channel, ctx.author
        )
        embed = discord_utils.create_embed()

        # Cannot make a new channel if the category is full
        if discord_utils.category_is_full(ctx.channel.category):
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Category `{ctx.channel.category.name}` is already full, max limit is 50 channels.",
            )
            # reply to user
            await ctx.send(embed=embed)
            return

        text_to_pin = " ".join(args)
        tab_name = chan_name.replace("#", "").replace("-", " ")

        curr_sheet_link, newsheet = await self.sheetcreatetabgeneric(
            ctx, ctx.channel, ctx.channel.category, tab_name
        )

        # Error, already being handled at the generic function
        if not curr_sheet_link or not newsheet or not newsheet.id:
            return

        # This link is customized for the newly made tab
        final_sheet_link = curr_sheet_link + "/edit#gid=" + str(newsheet.id)

        # new channel created (or None)
        new_chan = await discord_utils.createchannelgeneric(
            ctx.guild, ctx.channel.category, chan_name
        )
        # Error creating channel
        if not new_chan:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Forbidden! Have you checked if the bot has the required permisisons?",
            )
            await ctx.send(embed=embed)
            return

        embed = discord_utils.create_embed()
        embed.add_field(
            name=f"{constants.SUCCESS}!",
            value=f"Tab **{tab_name}** has been created at [Tab link]({final_sheet_link}).",
            inline=False,
        )
        msg = await new_chan.send(embed=embed)
        # Try to pin the message in new channel
        embed_or_none = await discord_utils.pin_message(msg)
        # Error pinning message
        if embed_or_none is not None:
            await new_chan.send(embed=embed_or_none)

        if text_to_pin:
            embed = discord_utils.create_embed()
            embed.description = text_to_pin
            msg = await new_chan.send(embed=embed)
            # Pin message in the new channel
            embed_or_none = await discord_utils.pin_message(msg)

            # Error pinning message
            if embed_or_none is not None:
                await ctx.send(embed=embed_or_none)
            else:
                await msg.add_reaction(EMOJIS[":pushpin:"])

        embed = discord_utils.create_embed()
        # TODO: technically there's a world where the posts *weren't* pinned, although it's unclear how much that matters in this message.
        embed.add_field(
            name=f"{constants.SUCCESS}!",
            value=f"Channel `{chan_name}` created as {new_chan.mention}, posts pinned!",
            inline=False,
        )
        await ctx.send(embed=embed)

    @command_predicates.is_verified()
    @commands.command(
        name="displaysheettether",
        aliases=["showsheettether", "showtether", "displaytether"],
    )
    async def displaysheettether(self, ctx):
        """Find the sheet the category is current tethered too

        Category : Verified Roles only.
        Usage : `~showtether`
        """
        logging_utils.log_command(
            "displaysheettether", ctx.guild, ctx.channel, ctx.author
        )
        embed = discord_utils.create_embed()

        # Get category information
        curr_cat = ctx.message.channel.category
        curr_chan = ctx.message.channel

        curr_chan_row, tether_type = self.findsheettether(curr_chan.id, curr_cat.id)

        if curr_chan_row is not None:
            curr_sheet_link = curr_chan_row.sheet_link
            if tether_type == sheets_constants.CHANNEL:
                embed.add_field(
                    name=f"Result",
                    value=f"The channel {curr_chan.mention} is currently tethered to the "
                    f"[Google sheet at link]({curr_sheet_link})",
                    inline=False,
                )
            elif tether_type == sheets_constants.CATEGORY:
                embed.add_field(
                    name=f"Result",
                    value=f"The category **{curr_cat.name}** is currently tethered to the "
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
                value=f"Neither the category **{curr_cat.name}** nor the channel {curr_chan.mention} "
                f"are tethered to any Google sheet.",
                inline=False,
            )
            await ctx.send(embed=embed)
            return

    @command_predicates.is_verified()
    @commands.command(name="sheetcreatetab", aliases=["sheettab", "sheetcrab"])
    async def sheetcreatetab(self, ctx, tab_name: str):
        """Create a New tab on the sheet that is currently tethered to this category

        This requires a tethered sheet (See `~addtether`) and a tab named "Template" on the sheet.
        Also the sheet must be 'Anyone with the link can edit' or the bot email get edit access.

        Category : Verified Roles only.
        Usage : `~sheettab TabName`
        """
        logging_utils.log_command("sheetcreatetab", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        curr_chan = ctx.message.channel
        curr_cat = ctx.message.channel.category
        curr_sheet_link, newsheet = await self.sheetcreatetabgeneric(
            ctx, curr_chan, curr_cat, tab_name
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
        # TODO: Do we even care about printing out the error message if the pin failed?
        if embed_or_none is not None:
            await ctx.send(embed=embed_or_none)

    @command_predicates.is_verified()
    @commands.command(name="downloadsheet", aliases=["savesheet"])
    async def downloadsheet(self, ctx, sheet_url=None):
        """Download  the channel/category's currently tethered sheet. You can supply a URL or it will
        use the currently tethered sheet.

        Category : Verified Roles only.
        Usage: `~savesheet`
        """
        logging_utils.log_command("downloadsheet", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        http = self.gdrive_credentials.authorize(httplib2.Http())
        service = discovery.build("drive", "v3", http=http)

        if sheet_url is None:
            tether_db_result, _ = self.findsheettether(
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

        sheet = self.get_sheet_from_key_or_link(tether_db_result.sheet_link)
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

            await ctx.send(file=discord.File(download_path))

    def addsheettethergeneric(
        self,
        sheet_key_or_link: str,
        curr_guild: discord.Guild,
        curr_catorchan: Union[discord.CategoryChannel, discord.TextChannel],
    ) -> gspread.Spreadsheet:
        """Add a sheet to the current channel"""
        # We accept both sheet keys or full links
        proposed_sheet = self.get_sheet_from_key_or_link(sheet_key_or_link)

        # If we can't open the sheet, send an error and return
        if not proposed_sheet:
            return None

        # If the channel already has a sheet, then we update it.
        # Otherwise, we add the channel to our master sheet to establish the tether

        with Session(database.DATABASE_ENGINE) as session:
            result = (
                session.query(database.SheetTethers)
                .filter_by(channel_or_cat_id=curr_catorchan.id)
                .first()
            )
            # If there is already an entry, we just need to update it.
            if result is not None:
                result.sheet_link = proposed_sheet.url
            # Otherwise, we need to create an entry
            else:
                stmt = insert(database.SheetTethers).values(
                    server_id=curr_guild.id,
                    server_name=curr_guild.name,
                    channel_or_cat_name=curr_catorchan.name,
                    channel_or_cat_id=curr_catorchan.id,
                    sheet_link=proposed_sheet.url,
                )
                session.execute(stmt)
            # Commits change
            session.commit()
        return proposed_sheet

    def findsheettether(self, curr_chan_id: int, curr_cat_id: int):
        """For finding the appropriate sheet tethering for a given category or channel"""
        result = None
        tether_type = None
        # Search DB for the sheet tether, if there is one
        with Session(database.DATABASE_ENGINE) as session:
            # Search for channel's tether
            result = (
                session.query(database.SheetTethers)
                .filter_by(channel_or_cat_id=curr_chan_id)
                .first()
            )
            # If we miss on the channel ID, try the category ID
            if result is None:
                result = (
                    session.query(database.SheetTethers)
                    .filter_by(channel_or_cat_id=curr_cat_id)
                    .first()
                )
                if result is not None:
                    tether_type = sheets_constants.CATEGORY
            else:
                tether_type = sheets_constants.CHANNEL

        return result, tether_type

    def get_sheet_from_key_or_link(self, sheet_key_or_link: str) -> gspread.Spreadsheet:
        """Takes in a string, which could be a google sheet key or URL"""
        # Assume the str is a URL
        try:
            sheet = self.gspread_client.open_by_url(sheet_key_or_link)
            return sheet
        except gspread.exceptions.APIError:
            return None
        # Given str was not a link
        except gspread.exceptions.NoValidUrlKeyFound:
            pass
        # Assume the str is a sheet key
        try:
            sheet = self.gspread_client.open_by_key(sheet_key_or_link)
            return sheet
        # Entity Not Found
        except gspread.exceptions.APIError:
            return None

    async def sheetcreatetabgeneric(self, ctx, curr_chan, curr_cat, tab_name):
        """Actually creates the sheet and handles errors"""
        embed = discord_utils.create_embed()
        curr_sheet_link = None
        newsheet = None

        tether_db_result, tether_type = self.findsheettether(
            str(curr_chan.id), str(curr_cat.id)
        )

        if tether_db_result is not None:
            curr_sheet_link = tether_db_result.sheet_link
        else:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"The category **{curr_cat.name}** nor the channel **{curr_chan.name}** are not "
                f"tethered to any Google sheet.",
                inline=False,
            )
            await ctx.send(embed=embed)
            return curr_sheet_link, newsheet

        # Make sure the template tab exists on the sheet.
        try:
            curr_sheet = self.gspread_client.open_by_url(curr_sheet_link)
            template_id = curr_sheet.worksheet("Template").id
        # Error when we can't open the curr sheet link
        except gspread.exceptions.APIError:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"I'm unable to open the tethered [sheet]({curr_sheet_link}). "
                f"Did the permissions change?",
                inline=False,
            )
            await ctx.send(embed=embed)
            return curr_sheet_link, newsheet
        # Error when the sheet has no template tab
        except gspread.exceptions.WorksheetNotFound:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"The [sheet]({curr_sheet_link}) has no tab named 'Template'. "
                f"Did you forget to add one?",
                inline=False,
            )
            await ctx.send(embed=embed)
            return curr_sheet_link, newsheet
        # Make sure tab_name does not exist
        try:
            curr_sheet.worksheet(tab_name)
            # If there is a tab with the given name, that's an error!
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"The [Google sheet at link]({curr_sheet_link}) already has a tab named "
                f"**{tab_name}**. Cannot create a tab with same name.",
                inline=False,
            )
            await ctx.send(embed=embed)
            return curr_sheet_link, newsheet
        except gspread.exceptions.WorksheetNotFound:
            # If the tab isn't found, that's good! We will create one.
            pass

        # Try to duplicate the template tab and rename it to the given name
        try:
            # Index of 4 is hardcoded for Team Arithmancy server
            newsheet = curr_sheet.duplicate_sheet(
                source_sheet_id=template_id,
                new_sheet_name=tab_name,
                insert_sheet_index=4,
            )
        except gspread.exceptions.APIError:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"Could not duplicate 'Template' tab in the "
                f"[Google sheet at link]({curr_sheet_link}). "
                f"Is the permission set up with 'Anyone with link can edit'?",
                inline=False,
            )
            await ctx.send(embed=embed)
            return curr_sheet_link, None

        return curr_sheet_link, newsheet

    #################
    # LION COMMANDS #
    #################

    """
    TODO: New workflow for hunts:
    ~DONE templatelion (set the template sheet for the server)
    ~IN PROGRESS huntlion/clonelion (duplicates the sheet and then adds hunt info to the sheet, also tethers the sheet to the category)
    ~IN PROGRESS chanlion (makes a new tab for a new feeder puzzle and then updates the info in the sheet accordingly)
    ~NOT STARTED metalion (makes a new tab for a new meta puzzle and then updates the info in the meta puzzle sheet)
    ~NOT STARTED roundlion (adds a puzzle to a round)
    ~NOT STARTED taglion (tags a specific role to a puzzle)
    ~NOT STARTED mentionlion (mentions the tagged roles of that puzzle, used when you need help)
    ~NOT STARTED solvedlion/solvishedlion/backsolvedlion/unsolvedlion/unsolvablelion/workingonlion/abandonedlion (changes the color of the tab and also the sheet, also updates stats, for solved/solvedish/backsolved/unsolved, also changes the name of the discord channel)
    ~NOT STARTED hintlion/hintsentlion (hintlion expresses the intent to request a hint and puts a matter to a vote, hintsentlion signifies that a hint has been sent)
    ~NOT STARTED archivelion (is the same as regular move to archive, but also moves the sheet to the end/hides the sheet)
    """

    ## WIP code. DO NOT USE
    def findlinkedtab(self, curr_chan_id: str, overviewtab):
        """Find linked tab based on lion overview"""

        curr_chan_or_cat_cell = None
        tether_type = None
        try:
            # Search first column for the channel
            curr_chan_or_cat_cell = overviewtab.find(curr_chan_id, in_column=1)
            tether_type = sheets_constants.CHANNEL
        except gspread.exceptions.CellNotFound:
            # If there is no tether for the specific channel, check if there is one for the category.
            try:
                # Search first column for the category
                # TODO: Change to dB
                # curr_chan_or_cat_cell = self.category_tether_tab.find(curr_cat_id, in_column=1)
                tether_type = sheets_constants.CATEGORY
            except gspread.exceptions.CellNotFound:
                pass

        return curr_chan_or_cat_cell, tether_type

    ## WIP code. DO NOT USE
    # TODO: ~chanlion
    async def sheetliongeneric(self, ctx, curr_chan, curr_cat, tab_name):
        """
        Part of the Lion series of improvements to sheetcrab/chancrab.
        This function will work with Overview and create shit


        """
        curr_sheet_link = None
        newsheet = None

        # Find the tethered sheet for the channel/category from the DB
        tether_result, tether_type = self.findsheettether(
            str(curr_chan.id), str(curr_cat.id)
        )

        # Error if no such sheet exists
        if tether_result is not None:
            curr_sheet_link = tether_result.sheet_link
        else:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"The category **{curr_cat.name}** nor the channel **{curr_chan.name}** are not "
                f"tethered to any Google sheet.",
                inline=False,
            )
            await ctx.send(embed=embed)
            return curr_sheet_link, newsheet

        # Make sure the template tab exists on the sheet.
        try:
            curr_sheet = self.gspread_client.open_by_url(curr_sheet_link)
            template_id = curr_sheet.worksheet("Template").id
        # Error when we can't open the curr sheet link
        except gspread.exceptions.APIError:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"I'm unable to open the tethered [sheet]({curr_sheet_link}). "
                f"Did the permissions change?",
                inline=False,
            )
            await ctx.send(embed=embed)
            return curr_sheet_link, newsheet
        # Error when the sheet has no template tab
        except gspread.exceptions.WorksheetNotFound:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"The [sheet]({curr_sheet_link}) has no tab named 'Template'. "
                f"Did you forget to add one?",
                inline=False,
            )
            await ctx.send(embed=embed)
            return curr_sheet_link, newsheet

        # Make sure the Overview tab exists on the sheet.
        try:
            curr_sheet = self.gspread_client.open_by_url(curr_sheet_link)
            overview_id = curr_sheet.worksheet("Overview").id
        # Error when the sheet has no Overview tab
        except gspread.exceptions.WorksheetNotFound:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"The [sheet]({curr_sheet_link}) has no tab named 'Overview'. "
                f"Did you forget to add one?",
                inline=False,
            )
            await ctx.send(embed=embed)
            return curr_sheet_link, newsheet

        overviewtab = 0

        # Find the tethered sheet for the channel/category from the DB
        curr_chan_or_cat_cell, tether_type = self.findlinkedtab(
            curr_chan.id, overviewtab
        )

        # Error if no such sheet exists
        if curr_chan_or_cat_cell:
            # TODO: Change to db
            # curr_sheet_link = self.category_tether_tab.cell(curr_chan_or_cat_cell.row, curr_chan_or_cat_cell.col + 2).value
            pass
        else:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"The category **{curr_cat.name}** nor the channel **{curr_chan.name}** are not "
                f"tethered to any Google sheet.",
                inline=False,
            )
            await ctx.send(embed=embed)
            return curr_sheet_link, newsheet

        # TODO: Why would we change the cog's attribute here? Anyways, change to DB
        # self.category_tether_tab = self.gspread_client.open_by_key(os.getenv("MASTER_SHEET_KEY")).worksheet(sheets_constants.CATEGORY_TAB)

        # Make sure tab_name does not exist
        try:
            curr_sheet.worksheet(tab_name)
            # If there is a tab with the given name, that's an error!
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"The [Google sheet at link]({curr_sheet_link}) already has a tab named "
                f"**{tab_name}**. Cannot create a tab with same name.",
                inline=False,
            )
            await ctx.send(embed=embed)
            return curr_sheet_link, newsheet
        except gspread.exceptions.WorksheetNotFound:
            # If the tab isn't found, that's good! We will create one.
            pass

        # Try to duplicate the template tab and rename it to the given name
        try:
            # Index of 4 is hardcoded for Team Arithmancy server
            newsheet = curr_sheet.duplicate_sheet(
                source_sheet_id=template_id,
                new_sheet_name=tab_name,
                insert_sheet_index=4,
            )
        except gspread.exceptions.APIError:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"Could not duplicate 'Template' tab in the "
                f"[Google sheet at link]({curr_sheet_link}). "
                f"Is the permission set up with 'Anyone with link can edit'?",
                inline=False,
            )
            await ctx.send(embed=embed)
            return curr_sheet_link, None

        # TODO - Overview work.
        return curr_sheet_link, newsheet

    async def validate_template(self, ctx, proposed_sheet):
        embed = discord_utils.create_embed()

        proposed_template = self.get_sheet_from_key_or_link(proposed_sheet)

        if not proposed_template:
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"Sorry, we can't find a sheet there. "
                f"Did you forget to set your sheet as 'Anyone with the link can edit'?",
                inline=False,
            )
            await ctx.send(embed=embed)
            return None

        curr_link = proposed_template.url

        # Make sure the template tab exists on the sheet.
        try:
            curr_sheet = self.gspread_client.open_by_url(curr_link)
            template_id = curr_sheet.worksheet("Template").id
        # Error when we can't open the curr sheet link
        except gspread.exceptions.APIError:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"I'm unable to open the tethered [sheet]({curr_link}). "
                f"Did the permissions change?",
                inline=False,
            )
            await ctx.send(embed=embed)
            return None
        # Error when the sheet has no template tab
        except gspread.exceptions.WorksheetNotFound:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"The [sheet]({curr_link}) has no tab named 'Template'. "
                f"Did you forget to add one?",
                inline=False,
            )
            await ctx.send(embed=embed)
            return None

        # Make sure the Meta Template tab exists on the sheet.
        try:
            curr_sheet = self.gspread_client.open_by_url(curr_link)
            overview_id = curr_sheet.worksheet("Meta Template").id
        # Error when the sheet has no Meta Template tab
        except gspread.exceptions.WorksheetNotFound:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"The [sheet]({curr_link}) has no tab named 'Meta Template'. "
                f"Did you forget to add one?",
                inline=False,
            )
            await ctx.send(embed=embed)
            return None

        # Make sure the Overview tab exists on the sheet.
        try:
            curr_sheet = self.gspread_client.open_by_url(curr_link)
            overview_id = curr_sheet.worksheet("Overview").id
        # Error when the sheet has no Overview tab
        except gspread.exceptions.WorksheetNotFound:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"The [sheet]({curr_link}) has no tab named 'Overview'. "
                f"Did you forget to add one?",
                inline=False,
            )
            await ctx.send(embed=embed)
            return None

        return proposed_template

    @command_predicates.is_verified()
    @commands.command(
        name="settemplatelion", aliases=["settemplion", "settemplate", "settemp"]
    )
    async def settemplion(self, ctx, template_sheet_key_or_link: str):
        """Set the template Google sheets for puzzlehunts on this server.

        Replaces the current template if one already exists.

        Requires that the template has the following tabs: Overview, Template, Meta Template

        Category: Verified Roles only.
        Usage: '~settemplatelion <sheet link>'
        """
        logging_utils.log_command("settemplatelion", ctx.guild, ctx.channel, ctx.author)

        embed = discord_utils.create_embed()

        # see if our link is actually a GSheet and has the required tabs
        proposed_template = await self.validate_template(
            ctx, template_sheet_key_or_link
        )

        if not proposed_template:
            return

        # If the server already has a template, update it, otherwise insert it into the database
        with Session(database.DATABASE_ENGINE) as session:
            result = (
                session.query(database.SheetTemplates)
                .filter_by(server_id=ctx.guild.id)
                .first()
            )

            # template already exists
            if result is not None:
                result.sheet_link = proposed_template.url
            # template does not exist
            else:
                stmt = insert(database.SheetTemplates).values(
                    server_id=ctx.guild.id,
                    server_name=ctx.guild.name,
                    sheet_link=proposed_template.url,
                )
                session.execute(stmt)
            # Commits change
            session.commit()

        embed.add_field(
            name=f"{constants.SUCCESS}!",
            value=f"This server **{ctx.guild.name}** now has the hunt template "
            f"[Google sheet at link]({proposed_template.url})",
            inline=False,
        )
        await ctx.send(embed=embed)

    def findtemplate(self, ctx):
        """For finding the hunt template for a given server."""
        with Session(database.DATABASE_ENGINE) as session:
            return (
                session.query(database.SheetTemplates)
                .filter_by(server_id=ctx.guild.id)
                .first()
            )

    @command_predicates.is_verified()
    @commands.command(
        name="gettemplatelion",
        aliases=[
            "gettemplion",
            "gettemplate",
            "gettemp",
            "templatelion",
            "templion",
            "template",
            "temp",
            "showtemplatelion",
            "showtemplion",
            "showtemplate",
            "showtemp",
            "displaytemplatelion",
            "displaytemplion",
            "displaytemplate",
            "displaytemp",
        ],
    )
    async def gettemplatelion(self, ctx):
        """Find the sheet used as the puzzlehunt template for this server.

        Category: Verified Roles only.
        Usage: '~gettemplatelion'
        """
        logging_utils.log_command("gettemplatelion", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        result = self.findtemplate(ctx)

        # No template
        if result is None:
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"This server **{ctx.guild.name}** does not have a template Google Sheet.",
                inline=False,
            )
            await ctx.send(embed=embed)
            return

        # Template exists
        embed.add_field(
            name=f"{constants.SUCCESS}!",
            value=f"We found a template for this server **{ctx.guild.name}** at "
            f"[Google sheet at link]({result.sheet_link})",
            inline=False,
        )
        await ctx.send(embed=embed)

    @command_predicates.is_verified()
    @commands.command(
        name="deletetemplatelion",
        aliases=[
            "deletetemplion",
            "deletetemplate",
            "deletetemp",
            "deltemplatelion",
            "deltemplion",
            "removetemplatelion",
            "deltemplate",
            "deltemp",
            "removetemplion",
            "removetemplate",
            "removetemp",
        ],
    )
    async def deletetemplatelion(self, ctx):
        """Unbind the template from the server.

        Category: Verified Roles only.
        Usage: '~removetether'
        """
        logging_utils.log_command(
            "deletetemplatelion", ctx.guild, ctx.channel, ctx.author
        )
        embed = discord_utils.create_embed()

        sheet = self.findtemplate(ctx)

        # Remove the existing binding if it exists
        if sheet is not None:
            with Session(database.DATABASE_ENGINE) as session:
                sheet_link = sheet.sheet_link
                session.query(database.SheetTemplates).filter_by(
                    server_id=ctx.guild.id
                ).delete()
                session.commit()
            embed.add_field(
                name=f"{constants.SUCCESS}!",
                value=f"This server **{ctx.guild.name}** is no longer bound to [sheet]({sheet_link})!",
                inline=False,
            )
        else:
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"This server **{ctx.guild.name}** does not have a bound template.",
                inline=False,
            )
        await ctx.send(embed=embed)

    # TODO:
    async def huntlion(
        self,
        ctx,
        hunt_team_name: str,
        hunturl: str,
        rolename_orurl: Union[discord.Role, str] = None,
        folderurl: str = None,
    ):
        """Clone the template and names the new sheet into a new category named huntteamname.

        This new category will have 2 premade channels: #huntteamname-main and #huntteamname-bot-spam

        The category will only be visible to those with the role rolename.

        Also tethers the new sheet to the category.

        Useful when we want to make a new hunt team.

        For any lion commands, a tether using either ~clonelion or ~huntlion is necessary.

        Requires that role does not have "folder/" inside the role name

        Category: Verified Roles only.
        Usage: ~huntlion SheetName hunturl
        Usage: ~huntlion SheetName hunturl role
        Usage: ~huntlion SheetName hunturl role folderurl
        Usage: ~huntlion SheetName hunturl folderurl
        """
        pass

    # TODO:
    async def clonelion(
        self, ctx, huntroundname: str, hunturl: str, folderurl: str = None
    ):
        """Clone the template and names the new sheet. Also tethers the new sheet to the category.

        Useful when we want to make a new sheet for a new set of rounds.

        For any lion commands, a tether using either ~clonelion or ~huntlion is necessary.

        Category: Verified Roles only.
        Usage: ~clonelion SheetName hunturl
        Usage: ~clonelion SheetName hunturl folderurl
        """
        pass

    @command_predicates.is_verified()
    @commands.command(
        name="clonetemplatelion",
        aliases=["clonetemplate", "clonetemp", "clonetemplion"],
    )
    async def clonetemplatelion(self, ctx, newname, folderurl: str = None):
        """Clones the template and names the new sheet

        For developers: also returns the cloned sheet

        Category: Verified Roles only.
        Usage: ~clonetemplatelion SheetName
        """
        logging_utils.log_command(
            "clonetemplatelion", ctx.guild, ctx.channel, ctx.author
        )
        embed = discord_utils.create_embed()

        result = self.findtemplate(ctx)

        if result is None:
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"This server **{ctx.guild.name}** does not have a template Google Sheet.",
                inline=False,
            )
            await ctx.send(embed=embed)
            return None

        f_id = ""

        if folderurl:
            try:
                f_id = folderurl.split("folders/")[1]
            except IndexError:
                f_id = ""

        sheet = result.sheet_link
        curr_sheet = self.gspread_client.open_by_url(sheet)

        new_sheet = ""

        try:
            new_sheet = self.gspread_client.copy(
                file_id=curr_sheet.id,
                title=newname,
                copy_permissions=True,
                folder_id=(f_id or None),
            )
        except gspread.exceptions.APIError:
            embed.add_field(
                name=f"{constants.FAILED}",
                value="Invalid folder. Please check to see that you have the correct link and permissions.",
                inline=False,
            )
            await ctx.send(embed=embed)
            return None

        if f_id:
            embed.add_field(
                name=f"{constants.SUCCESS}!",
                value=f"Cloned sheet located at [sheet link]({new_sheet.url}) "
                f"in folder [GDrive folder link]({folderurl})",
                inline=False,
            )
        else:
            embed.add_field(
                name=f"{constants.SUCCESS}!",
                value=f"Cloned sheet located at [sheet link]({new_sheet.url})",
                inline=False,
            )

        await ctx.send(embed=embed)
        return new_sheet

    @command_predicates.is_verified()
    @commands.command(name="tetherlion")
    async def tetherlion(self, ctx, sheet_key_or_link: str):
        """Tethers a sheet to the category and also checks that it is the correct format to be used by the lion commands

        Sheet must have the following tabs: Overview, Template, Meta Template

        Usage: ~tetherlion sheeturl
        """
        logging_utils.log_command("tetherlion", ctx.guild, ctx.channel, ctx.author)
        if await self.validate_template(ctx, sheet_key_or_link) is None:
            return

        await self.addsheettether(ctx, sheet_key_or_link)


def setup(bot):
    bot.add_cog(SheetsCog(bot))
