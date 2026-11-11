import asyncio
import os
import zipfile
from typing import List, Set, Tuple, Union

import nextcord
from nextcord.ext import commands

import constants
from modules.archive import archive_constants, archive_utils
from utils import command_predicates, discord_utils

"""
Archive module. Exports a channel's history as Discord-style HTML with DiscordChatExporter
and sends it as a file
"""


class ArchiveError(Exception):
    """DiscordChatExporter could not export a channel"""

    def __init__(self, message: str, forbidden: bool):
        super().__init__(message)
        self.forbidden = forbidden


class ArchiveCog(commands.Cog, name="Archive"):
    """
    Downloads a channel's history and sends it as a file
    """

    def __init__(self, bot):
        self.bot = bot
        self.compression = zipfile.ZIP_DEFLATED
        self.lock = asyncio.Lock()

        archive_utils.reset_archive_dir()

    def zip_dir(self, out_dir: str, zip_path: str, skip: Set[str] = frozenset()) -> int:
        """Zip the export in out_dir, leaving out the files in skip (paths relative
        to out_dir), and return the zip's size"""
        with zipfile.ZipFile(zip_path, mode="w") as zf:
            for root, _, files in os.walk(out_dir):  # underscore is directories
                for filename in files:
                    path = os.path.join(root, filename)
                    arcname = os.path.relpath(path, out_dir)
                    if arcname in skip:
                        continue
                    zf.write(path, arcname=arcname, compress_type=self.compression)
        return os.path.getsize(zip_path)

    def zip_without_biggest_media(
        self, out_dir: str, zip_path: str, zip_size: int, filesize_limit: int
    ) -> Tuple[int, List[Tuple[str, int]], bool]:
        """Zip the export again, leaving out the biggest media files until it fits.

        Returns the new zip's size, the files left out (biggest first), and whether
        that was every media file.
        """
        media = archive_utils.list_media(out_dir)
        skipped = archive_utils.pick_media_to_skip(media, zip_size, filesize_limit)
        # The pick is an estimate, so check the real size and leave out more if needed
        while True:
            new_size = self.zip_dir(
                out_dir, zip_path, skip={path for path, _ in skipped}
            )
            if new_size <= filesize_limit or len(skipped) == len(media):
                return new_size, skipped, len(skipped) == len(media)
            skipped.append(media[len(skipped)])

    @staticmethod
    def list_skipped(skipped: List[Tuple[str, int]], max_shown: int = 8) -> str:
        """One line per left-out file, biggest first, short enough for an embed field"""
        lines = [
            f"`{archive_utils.media_display_name(path)[:50]}` "
            f"({size / constants.BYTES_TO_MEGABYTES:.2f}MB)"
            for path, size in skipped[:max_shown]
        ]
        if len(skipped) > max_shown:
            lines.append(f"...and {len(skipped) - max_shown} more")
        return "\n".join(lines)

    @staticmethod
    def zip_path_for(channel, kind: str) -> str:
        """Where to save a zip for this channel, e.g. archive/puzzle-1_archive.zip"""
        return os.path.join(
            archive_constants.ARCHIVE,
            f"{archive_utils.safe_filename(channel.name)}_{kind}.zip",
        )

    async def archive_one_channel(
        self,
        channel: Union[nextcord.TextChannel, nextcord.ForumChannel, nextcord.Thread],
    ) -> Tuple[str, str, int, List[str]]:
        """Export a channel's history (with its threads and attachments) and zip it up"""
        out_dir = os.path.join(archive_constants.ARCHIVE, str(channel.id))
        returncode, stderr, failed = await archive_utils.run_export(
            channel.id,
            out_dir,
            # A thread has no threads of its own
            include_threads=not isinstance(channel, nextcord.Thread),
        )
        if returncode != 0:
            raise ArchiveError(
                archive_utils.first_error(stderr), "forbidden" in stderr.lower()
            )

        zip_path = self.zip_path_for(channel, "archive")
        # Do zipping off the event loop
        zip_size = await asyncio.to_thread(self.zip_dir, out_dir, zip_path)
        return out_dir, zip_path, zip_size, failed

    def get_file_and_embed(self, channel, filesize_limit, out_dir, zip_path, zip_size):
        """Check if the zip can be sent. If it's too big, leave out the biggest media
        files until it fits, and create an embed with message"""
        embed = discord_utils.create_embed()

        if zip_size > filesize_limit:
            smaller_zip_path = self.zip_path_for(channel, "archive_smaller")
            smaller_zip_size, skipped, all_media_skipped = (
                self.zip_without_biggest_media(
                    out_dir, smaller_zip_path, zip_size, filesize_limit
                )
            )
            # With every media file left out, it's just the chat log
            html_zip_path = self.zip_path_for(channel, "chat_log")
            if all_media_skipped:
                os.replace(smaller_zip_path, html_zip_path)
            html_zip_size = smaller_zip_size
            if html_zip_size > filesize_limit:
                embed.add_field(
                    name="ERROR: History Too Big",
                    value=f"Sorry about that! The chat log in {channel.mention} is too big for me to send.\n"
                    f"The max file size I can send in this server is "
                    f"`{(filesize_limit / constants.BYTES_TO_MEGABYTES):.2f}MB`, but the chat log is "
                    f"`{(html_zip_size / constants.BYTES_TO_MEGABYTES):.2f}MB`",
                    inline=False,
                )
                file = None
            elif not all_media_skipped:
                embed.add_field(
                    name="WARNING: Attachments Too Big",
                    value=f"There are too many photos in {channel.mention} for me to send. The max file size "
                    f"I can send in this server is "
                    f"`{(filesize_limit / constants.BYTES_TO_MEGABYTES):.2f}MB` but the zip is "
                    f"`{(zip_size / constants.BYTES_TO_MEGABYTES):.2f}MB`. "
                    f"I left out the {len(skipped)} biggest files, so they won't show in the archive:\n"
                    + self.list_skipped(skipped),
                    inline=False,
                )
                file = nextcord.File(smaller_zip_path)
            else:
                embed.add_field(
                    name="WARNING: Attachments Too Big",
                    value=f"There are too many photos in {channel.mention} for me to send. The max file size "
                    f"I can send in this server is "
                    f"`{(filesize_limit / constants.BYTES_TO_MEGABYTES):.2f}MB` but the zip is "
                    f"`{(zip_size / constants.BYTES_TO_MEGABYTES):.2f}MB`. I'll only be able to send you the chat log.",
                    inline=False,
                )
                file = nextcord.File(html_zip_path)
        else:
            file = nextcord.File(zip_path)
            embed = None
        return file, embed

    def add_failed_threads(self, embed, channel, failed):
        """Warn about threads DCE couldn't export, even though the channel itself worked"""
        if not failed:
            return embed
        if embed is None:
            embed = discord_utils.create_embed()
        embed.add_field(
            name="WARNING: Some threads failed",
            value=f"I couldn't archive everything in {channel.mention}:\n"
            + "\n".join(failed)[:900],
            inline=False,
        )
        return embed

    def get_error_embed(self, channel, error: ArchiveError):
        embed = discord_utils.create_embed()
        if error.forbidden:
            embed.add_field(
                name="ERROR: No access",
                value=f"Sorry! I don't have access to {channel.mention}. You'll need "
                f"to give me permission to view the channel if you want "
                f"to archive it",
                inline=False,
            )
        else:
            embed.add_field(
                name="ERROR: Failed to archive",
                value=f"Sorry! I couldn't archive {channel.mention}: {error}",
                inline=False,
            )
        return embed

    async def check_dce_installed(self, ctx) -> bool:
        if archive_utils.dce_installed():
            return True
        embed = discord_utils.create_embed()
        embed.add_field(
            name="ERROR: Archiving is not set up",
            value="I can't find DiscordChatExporter, which I need to archive channels. "
            "Whoever runs me needs to run `python scripts/install_dce.py`.",
            inline=False,
        )
        await discord_utils.send_message(ctx, embed)
        return False

    @command_predicates.is_verified()
    @commands.command(name="archivechannel", aliases=["archivechan", "archivethread"])
    async def archivechannel(
        self, ctx: commands.Context, *args: Union[nextcord.TextChannel, str]
    ):
        """Command to download channel's history

        Permission Category : Verified Roles only.
        Usage: `~archivechannel #channel`
        Usage: `~archivechannel #channel1 "channel2"`
        """
        embed = discord_utils.create_embed()
        owner = await self.bot.fetch_user(os.getenv("BOT_OWNER_DISCORD_ID"))

        # Check if the user supplied a channel
        if len(args) < 1:
            # No arguments provided
            embed = discord_utils.create_no_argument_embed("channel")
            await discord_utils.send_message(ctx, embed)
            return False
        if not await self.check_dce_installed(ctx):
            return False
        # If we don't have the lock, let the user know it may take a while.
        msg = None
        # Returned so ~deletehydra knows not to delete a channel that wasn't archived
        all_archived = True

        for channelname in args:
            if self.lock.locked():
                msgs = await discord_utils.send_message(
                    ctx, archive_utils.get_delay_embed()
                )
                msg = msgs[0]
            # LOCK EVERYTHING
            async with self.lock:
                # If we sent a message about being delayed bc of lock, we can delete that now.
                if msg:
                    await msg.delete()
                    msg = None
                archive_utils.reset_archive_dir()
                if isinstance(channelname, nextcord.TextChannel):
                    channel = channelname
                else:
                    channel = await discord_utils.find_chan_or_thread(ctx, channelname)

                    # A new embed for each error so fields don't get repeated from earlier channels
                    error_embed = discord_utils.create_embed()

                    if channel is None:
                        error_embed.add_field(
                            name="ERROR: Cannot find channel",
                            value=f"Sorry, I cannot find a channel with name {channelname}. Try mentioning the channel (e.g. `#{channelname}`)",
                            inline=False,
                        )
                        await discord_utils.send_message(ctx, error_embed)
                        all_archived = False
                        continue
                    if channel.type.name not in [
                        "text",
                        "public_thread",
                        "private_thread",
                        "forum",
                    ]:
                        error_embed.add_field(
                            name="ERROR: Cannot archive non-text channels",
                            value=f"Sorry! I can only archive text channels, but "
                            f"{channel} is a {channel.type} channel.",
                            inline=False,
                        )
                        await discord_utils.send_message(ctx, error_embed)
                        all_archived = False
                        continue
                # If we've gotten to this point, we know we have a channel so we should probably let the user know.
                start_embed = await self.get_start_embed(channel)
                msgs = await discord_utils.send_message(ctx, start_embed)
                msg = msgs[0]
                try:
                    (
                        out_dir,
                        zip_path,
                        zip_size,
                        failed,
                    ) = await self.archive_one_channel(channel)
                except ArchiveError as e:
                    await msg.delete()
                    msg = None
                    await discord_utils.send_message(
                        ctx, self.get_error_embed(channel, e)
                    )
                    all_archived = False
                    continue
                # Do off the main event loop
                file, embed = await asyncio.to_thread(
                    self.get_file_and_embed,
                    channel,
                    ctx.guild.filesize_limit * 0 + constants.HARDCODED_FILE_SIZE,
                    out_dir,
                    zip_path,
                    zip_size,
                )
                embed = self.add_failed_threads(embed, channel, failed)
                if file is None or failed:
                    all_archived = False
                # There has been an issue with AIO HTTP message sending fails, in which case discord.py crashes?
                # So adding this try/catch for runtime to catch this. I don't think it's a deterministic error
                try:
                    await ctx.send(file=file, embed=embed)
                except (RuntimeError, nextcord.HTTPException):
                    all_archived = False
                    embed = discord_utils.create_embed()
                    embed.add_field(
                        name="ERROR: Failed to send archive",
                        value=f"Sorry! I had trouble sending you the archived file for "
                        f"{channel.mention}. Please try again later, and let {owner.mention} know if this "
                        f"issue persists",
                        inline=False,
                    )
                    await discord_utils.send_message(ctx, embed)
                if msg:
                    await msg.delete()
                    msg = None
        # Clean up the archive dir
        archive_utils.reset_archive_dir()
        return all_archived

    async def archive_many_channels(self, ctx, channels, name_for_errors):
        """Archive each channel in turn and send its file, for ~archivecategory and ~archiveserver"""
        for text_channel in channels:
            archive_utils.reset_archive_dir()
            try:
                (
                    out_dir,
                    zip_path,
                    zip_size,
                    failed,
                ) = await self.archive_one_channel(text_channel)
                file, embed = await asyncio.to_thread(
                    self.get_file_and_embed,
                    text_channel,
                    ctx.guild.filesize_limit * 0 + constants.HARDCODED_FILE_SIZE,
                    out_dir,
                    zip_path,
                    zip_size,
                )
                embed = self.add_failed_threads(embed, text_channel, failed)
                await ctx.send(file=file, embed=embed)
            except ArchiveError as e:
                await discord_utils.send_message(
                    ctx, self.get_error_embed(text_channel, e)
                )
                continue
            # Same concern as above with AIO HTTP message sending failures causing discord.py to crash (TODO: Check)
            # Skip chennel when there is a HTTPException because that's Discord refusing
            except (RuntimeError, nextcord.HTTPException):
                embed = discord_utils.create_embed()
                embed.add_field(
                    name="ERROR: Failed to send archive",
                    value=f"Sorry! I had trouble sending you the archived file for "
                    f"{text_channel.mention}. Perhaps you can try again with {ctx.prefix}archivechannel"
                    f" after I've finished archiving {name_for_errors}.",
                    inline=False,
                )
                await discord_utils.send_message(ctx, embed)
                continue

    @command_predicates.is_verified()
    @commands.command(name="archivecategory", aliases=["archivecat"])
    async def archivecategory(self, ctx: commands.Context, *args: str):
        """Command to download the history of every text and forum channel in the category

        Permission Category : Verified Roles only.
        Usage: `~archivecategory "Category name"`
        """
        embed = discord_utils.create_embed()

        # Check if the user supplied a category
        if len(args) < 1:
            # No arguments provided
            embed = discord_utils.create_no_argument_embed("category")
            await discord_utils.send_message(ctx, embed)
            return
        if not await self.check_dce_installed(ctx):
            return

        # If we don't have the lock, let the user know it may take a while.
        msg = None
        if self.lock.locked():
            embed = archive_utils.get_delay_embed()
            await discord_utils.send_message(ctx, embed)
        # LOCK EVERYTHING
        async with self.lock:
            if msg:
                await msg.delete()
                msg = None
            category = await discord_utils.find_category(ctx, " ".join(args))
            if category is None:
                embed.add_field(
                    name="ERROR: Cannot find category",
                    value=f"Sorry, I cannot find a category with name {' '.join(args)}. "
                    f"Please make sure the spelling and capitalization are correct!",
                    inline=False,
                )
                await discord_utils.send_message(ctx, embed)
                return

            channels = [
                channel
                for channel in category.channels
                if isinstance(channel, (nextcord.TextChannel, nextcord.ForumChannel))
            ]
            start_embed = await self.get_start_embed(category, channels)
            msgs = await discord_utils.send_message(ctx, start_embed)

            await self.archive_many_channels(ctx, channels, category.mention)

            if msgs:
                for msg in msgs:
                    await msg.delete()
            embed = discord_utils.create_embed()
            embed.add_field(
                name="All Done!",
                value=f"Successfully archived {category}",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
        # Clean up the archive dir
        archive_utils.reset_archive_dir()

    @command_predicates.is_bot_owner_or_admin()
    @commands.command(name="archiveserver")
    async def archiveserver(self, ctx: commands.Context):
        """Command to archive every text and forum channel in the server. WARNING: This command will take *very*
        long on any reasonably aged server

        Permission Category : Admin or Bot Owner Roles only.
        Usage: `~archiveserver`
        """
        if not await self.check_dce_installed(ctx):
            return

        # If we don't have the lock, let the user know it may take a while.
        msg = None
        if self.lock.locked():
            msg = await ctx.send(embed=archive_utils.get_delay_embed())

        # LOCK EVERYTHING
        async with self.lock:
            channels = ctx.guild.text_channels + ctx.guild.forum_channels
            start_embed = await self.get_start_embed(ctx.guild, channels)
            if msg:
                await msg.delete()
                msg = None

            msgs = await discord_utils.send_message(ctx, start_embed)
            await self.archive_many_channels(ctx, channels, ctx.guild)

            if msgs:
                for msg in msgs:
                    await msg.delete()
            embed = discord_utils.create_embed()
            embed.add_field(
                name="All Done!",
                value=f"Successfully archived {ctx.guild}",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
        # Clean up the archive dir
        archive_utils.reset_archive_dir()

    async def get_start_embed(self, channel_or_guild, multiple_channels=None):
        owner = await self.bot.fetch_user(os.getenv("BOT_OWNER_DISCORD_ID"))
        embed = discord_utils.create_embed()
        embed.add_field(
            name="Archive Started",
            value=f"Your archiving of {channel_or_guild.mention if hasattr(channel_or_guild, 'mention') else channel_or_guild}"
            f" has begun! This may take a while. If I run into "
            f"any errors, I'll let you know.",
            inline=False,
        )
        if multiple_channels:
            embed.add_field(
                name="List of Channels to Archive",
                value=archive_utils.list_for_embed(
                    [channel.name for channel in multiple_channels]
                ),
                inline=False,
            )
        embed.add_field(
            name="Problems?",
            value=f"Taking too long? Let {owner.mention} know",
            inline=False,
        )
        return embed


def setup(bot):
    bot.add_cog(ArchiveCog(bot))
