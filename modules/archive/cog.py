import asyncio
import os
import re
import unicodedata
import zipfile
from typing import TextIO, Tuple, Union, cast
from pathlib import Path

import nextcord
from nextcord.ext import commands

import constants
from modules.archive import archive_constants, archive_utils
from utils import command_predicates, discord_utils, logging_utils

"""
Archive module. Downloads a channel's history and sends it as a file
"""

MAX_ARCHIVE_STEM_LENGTH = 80
MAX_THREAD_STEM_LENGTH = 120
MAX_ATTACHMENT_FILENAME_LENGTH = 120
MAX_EXTENSION_LENGTH = 20


class ArchiveCog(commands.Cog, name="Archive"):
    """
    Downloads a channel's history and sends it as a file
    """

    def __init__(self, bot):
        self.bot = bot
        self.compression = zipfile.ZIP_DEFLATED
        self.lock = asyncio.Lock()

        archive_utils.reset_archive_dir()

    @staticmethod
    def _slugify_filename_stem(name: str, fallback: str, max_length: int) -> str:
        safe_name = (
            unicodedata.normalize("NFKD", name)
            .encode("ascii", "ignore")
            .decode("ascii")
            .lower()
        )
        safe_name = re.sub(r"[^\w\s-]", "", safe_name)
        safe_name = re.sub(r"[-\s]+", "-", safe_name).strip("-_")
        safe_name = safe_name[:max_length].strip("-_")
        return safe_name or fallback[:max_length]

    @staticmethod
    def _stem_with_id(
        name: str,
        object_id: Union[int, str, None],
        fallback: str,
        max_length: int,
    ) -> str:
        suffix = f"-{object_id}" if object_id is not None else ""
        stem_length = max(1, max_length - len(suffix))
        stem = ArchiveCog._slugify_filename_stem(name, fallback, stem_length)
        return f"{stem}{suffix}"[:max_length]

    @staticmethod
    def _channel_archive_stem(
        channel: Union[nextcord.TextChannel, nextcord.ForumChannel, nextcord.Thread],
    ) -> str:
        return ArchiveCog._stem_with_id(
            channel.name,
            getattr(channel, "id", None),
            "channel",
            MAX_ARCHIVE_STEM_LENGTH,
        )

    @staticmethod
    def _channel_text_log_path(
        channel: Union[nextcord.TextChannel, nextcord.ForumChannel, nextcord.Thread],
    ) -> str:
        return os.path.join(
            archive_constants.ARCHIVE,
            f"{ArchiveCog._channel_archive_stem(channel)}_"
            f"{archive_constants.TEXT_LOG_PATH}",
        )

    @staticmethod
    def _channel_zip_path(
        channel: Union[nextcord.TextChannel, nextcord.ForumChannel, nextcord.Thread],
    ) -> str:
        return os.path.join(
            archive_constants.ARCHIVE,
            f"{ArchiveCog._channel_archive_stem(channel)}_archive.zip",
        )

    @staticmethod
    def _thread_dir(thread: nextcord.Thread) -> str:
        return os.path.join(
            archive_constants.ARCHIVE,
            f"{ArchiveCog._channel_archive_stem(thread.parent)}_"
            f"{archive_constants.THREADS}",
        )

    @staticmethod
    def _clean_extension(filename: str) -> str:
        extension = (
            unicodedata.normalize("NFKD", Path(filename).suffix)
            .encode("ascii", "ignore")
            .decode("ascii")
            .lower()
        )
        extension = re.sub(r"[^a-z0-9.]", "", extension)
        return extension[:MAX_EXTENSION_LENGTH]

    @staticmethod
    def _attachment_filename(filename: str, dupe_counter: int = 0) -> str:
        extension = ArchiveCog._clean_extension(filename)
        suffix = f" ({dupe_counter}){extension}" if dupe_counter else extension
        stem_length = max(1, MAX_ATTACHMENT_FILENAME_LENGTH - len(suffix))
        stem = ArchiveCog._slugify_filename_stem(
            Path(filename).stem,
            "attachment",
            stem_length,
        )
        return f"{stem}{suffix}"

    @staticmethod
    def _available_attachment_path(filename: str) -> Tuple[str, str]:
        image_dir = os.path.join(archive_constants.ARCHIVE, archive_constants.IMAGES)
        dupe_counter = 0
        while True:
            archived_filename = ArchiveCog._attachment_filename(
                filename,
                dupe_counter,
            )
            proposed_path = os.path.join(image_dir, archived_filename)
            if not os.path.exists(proposed_path):
                return proposed_path, archived_filename
            dupe_counter += 1

    @staticmethod
    async def archive_message(f: TextIO, msg: nextcord.Message):
        f.write(
            f"[ {msg.created_at.strftime('%m-%d-%Y, %H:%M:%S')} ] "
            f"{msg.author.display_name.rjust(25, ' ')}: "
            f"{msg.clean_content}"
        )
        for attachment_index, attachment in enumerate(msg.attachments):
            proposed_path, archived_filename = ArchiveCog._available_attachment_path(
                attachment.filename,
            )
            try:
                await attachment.save(proposed_path)
            except OSError:
                fallback_filename = (
                    f"attachment-{msg.id}-{attachment_index}"
                    f"{ArchiveCog._clean_extension(attachment.filename)}"
                )
                (
                    proposed_path,
                    archived_filename,
                ) = ArchiveCog._available_attachment_path(fallback_filename)
                await attachment.save(proposed_path)
            f.write(f" {archived_filename}")
        # Important: Write the newline after each comment is done
        f.write("\n")

    @staticmethod
    async def archive_thread(f: TextIO, thread: nextcord.Thread) -> int:
        thread_txt_size = 0
        f.write(f"[  {thread.id} ] {'THREAD'.rjust(25, ' ')}: ")
        f.write(thread.name + "\n")
        thread_dir = ArchiveCog._thread_dir(thread)
        norm_thread_name = ArchiveCog._stem_with_id(
            thread.name,
            thread.id,
            "thread",
            MAX_THREAD_STEM_LENGTH,
        )
        os.makedirs(thread_dir, exist_ok=True)
        thread_log_path = os.path.join(thread_dir, norm_thread_name + ".txt")
        with open(thread_log_path, "w") as thread_f:
            async for t_msg in thread.history(limit=None, oldest_first=True):
                await ArchiveCog.archive_message(thread_f, t_msg)
            thread_txt_size += f.tell()

        return thread_txt_size

    async def archive_one_channel(
        self,
        channel: Union[nextcord.TextChannel, nextcord.ForumChannel, nextcord.Thread],
    ) -> Tuple[nextcord.File, int, nextcord.File, int]:
        """Download a channel's history"""
        # Write the chat log. Replace attachments with their filename (for easy reference)
        text_log_path = ArchiveCog._channel_text_log_path(channel)
        total_thread_txt_size = 0
        with open(text_log_path, "w") as f:
            if hasattr(channel, "history"):
                channel = cast(nextcord.TextChannel | nextcord.Thread, channel)
                async for msg in channel.history(limit=None, oldest_first=True):
                    await self.archive_message(f, msg)
                    # Threads are attached to normal messages
                    if msg.flags.has_thread and msg.thread:
                        total_thread_txt_size += await self.archive_thread(
                            f, msg.thread
                        )

            elif channel.type == nextcord.ChannelType.forum:
                channel = cast(nextcord.ForumChannel, channel)
                for thread in channel.threads:
                    total_thread_txt_size += await self.archive_thread(f, thread)
                async for thread in channel.archived_threads(limit=None):
                    total_thread_txt_size += await self.archive_thread(f, thread)

            text_file_size = f.tell()

        ZIP_FILENAME = ArchiveCog._channel_zip_path(channel)
        # Create a zipfile and then walk through all the saved chatlogs and images, and zip em up
        with zipfile.ZipFile(ZIP_FILENAME, mode="w") as zf:
            for root, directories, files in os.walk(archive_constants.ARCHIVE):
                for filename in files:
                    if filename == os.path.basename(ZIP_FILENAME):
                        continue
                    zf.write(
                        os.path.join(root, filename), compress_type=self.compression
                    )
            zf_file_size = zf.fp.tell()
        return (
            nextcord.File(ZIP_FILENAME),
            zf_file_size,
            nextcord.File(text_log_path),
            text_file_size + total_thread_txt_size,
        )

    def get_file_and_embed(
        self, channel, filesize_limit, zip_file, zip_file_size, textfile, textfile_size
    ):
        """Check if zipfile and textfile can be sent or not, create embed with message"""
        embed = discord_utils.create_embed()

        if zip_file_size > filesize_limit:
            # Note that this is an underestimate, since it's not compressed! But it takes a fair amount of text to hit
            # limits.
            if textfile_size > filesize_limit:
                embed.add_field(
                    name="ERROR: History Too Big",
                    value=f"Sorry about that! The chat log in {channel.mention} is too big for me to send.\n"
                    f"The max file size I can send in this server is "
                    f"`{(filesize_limit / constants.BYTES_TO_MEGABYTES):.2f}MB`, but the chat log is "
                    f"`{(textfile_size / constants.BYTES_TO_MEGABYTES):.2f}MB`",
                    inline=False,
                )
                file = None
            else:
                embed.add_field(
                    name="WARNING: Attachments Too Big",
                    value=f"There are too many photos in {channel.mention} for me to send. The max file size "
                    f"I can send in this server is "
                    f"`{(filesize_limit / constants.BYTES_TO_MEGABYTES):.2f}MB` but the zip is "
                    f"`{(zip_file_size / constants.BYTES_TO_MEGABYTES):.2f}MB`. I'll only be able to send you the chat log.",
                    inline=False,
                )
                ZIP_FILENAME = ArchiveCog._channel_zip_path(channel)
                with zipfile.ZipFile(ZIP_FILENAME, mode="w") as zf:
                    zf.write(
                        ArchiveCog._channel_text_log_path(channel),
                        compress_type=self.compression,
                    )

                    thread_dir = Path(
                        archive_constants.ARCHIVE,
                        f"{ArchiveCog._channel_archive_stem(channel)}_"
                        f"{archive_constants.THREADS}",
                    )

                    # Glob only succeeds if thread_dir exists
                    for thread_file in thread_dir.glob("*.txt"):
                        zf.write(thread_file, compress_type=self.compression)
                file = zip_file
        else:
            file = zip_file
            embed = None
        return file, embed

    @command_predicates.is_verified()
    @commands.command(name="archivechannel", aliases=["archivechan", "archivethread"])
    async def archivechannel(self, ctx, *args: Union[nextcord.TextChannel, str]):
        """Command to download channel's history

        Permission Category : Verified Roles only.
        Usage: `~archivechannel #channel`
        Usage: `~archivechannel #channel1 "channel2"`
        """
        await logging_utils.log_command(
            "archivechannel", ctx.guild, ctx.channel, ctx.author
        )
        embed = discord_utils.create_embed()

        # Check if the user supplied a channel
        if len(args) < 1:
            # No arguments provided
            embed = discord_utils.create_no_argument_embed("channel")
            await discord_utils.send_message(ctx, embed)
            return
        # If we don't have the lock, let the user know it may take a while.
        msg = None

        for channelname in args:
            if self.lock.locked():
                embed = archive_utils.get_delay_embed()
                msgs = await discord_utils.send_message(ctx, embed)
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
                    if channel is None:
                        embed.add_field(
                            name="ERROR: Cannot find channel",
                            value=f"Sorry, I cannot find a channel with name {channelname}. Try mentioning the channel (e.g. `#{channelname}`)",
                            inline=False,
                        )
                        await discord_utils.send_message(ctx, embed)
                        return
                    if channel.type.name not in [
                        "text",
                        "public_thread",
                        "private_thread",
                        "forum",
                    ]:
                        embed.add_field(
                            name="ERROR: Cannot archive non-text channels",
                            value=f"Sorry! I can only archive text channels, but "
                            f"{channel} is a {channel.type} channel.",
                            inline=False,
                        )
                        await discord_utils.send_message(ctx, embed)
                        return
                # If we've gotten to this point, we know we have a channel so we should probably let the user know.
                start_embed = await self.get_start_embed(channel)
                msgs = await discord_utils.send_message(ctx, start_embed)
                msg = msgs[0]
                try:
                    # zipfile, textfile
                    (
                        zip_file,
                        zip_file_size,
                        textfile,
                        textfile_size,
                    ) = await self.archive_one_channel(channel)
                except nextcord.errors.Forbidden:
                    embed.add_field(
                        name="ERROR: No access",
                        value=f"Sorry! I don't have access to {channel}. You'll need "
                        f"to give me permission to view the channel if you want "
                        f"to archive it",
                        inline=False,
                    )
                    await discord_utils.send_message(ctx, embed)
                    return
                file, embed = self.get_file_and_embed(
                    channel,
                    ctx.guild.filesize_limit * 0 + constants.HARDCODED_FILE_SIZE,
                    zip_file,
                    zip_file_size,
                    textfile,
                    textfile_size,
                )
                # There has been an issue with AIO HTTP message sending fails, in which case discord.py crashes?
                # So adding this try/catch for runtime to catch this. I don't think it's a deterministic error
                try:
                    await ctx.send(file=file, embed=embed)
                except RuntimeError:
                    embed.add_field(
                        name="ERROR: Failed to send archive",
                        value=f"Sorry! I had trouble sending you the archived file for "
                        f"{channel.mention}. Please try again later, and let kev know if this "
                        f"issue persists",
                        inline=False,
                    )
                    await discord_utils.send_message(ctx, embed)
                if msg:
                    await msg.delete()
                    msg = None
            # Clean up the archive dir
            archive_utils.reset_archive_dir()

    @command_predicates.is_verified()
    @commands.command(name="archivecategory", aliases=["archivecat"])
    async def archivecategory(self, ctx, *args: str):
        """Command to download the history of every text channel in the category

        Permission Category : Verified Roles only.
        Usage: `~archivecategory "Category name"`
        """
        await logging_utils.log_command(
            "archivecategory", ctx.guild, ctx.channel, ctx.author
        )
        embed = discord_utils.create_embed()

        # Check if the user supplied a category
        if len(args) < 1:
            # No arguments provided
            embed = discord_utils.create_no_argument_embed("category")
            await discord_utils.send_message(ctx, embed)
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

            start_embed = await self.get_start_embed(category, category.text_channels)
            msgs = await discord_utils.send_message(ctx, start_embed)

            for text_channel in category.text_channels:
                archive_utils.reset_archive_dir()
                try:
                    (
                        zip_file,
                        zip_file_size,
                        textfile,
                        textfile_size,
                    ) = await self.archive_one_channel(text_channel)
                    file, embed = self.get_file_and_embed(
                        text_channel,
                        ctx.guild.filesize_limit * 0 + constants.HARDCODED_FILE_SIZE,
                        zip_file,
                        zip_file_size,
                        textfile,
                        textfile_size,
                    )
                    await ctx.send(file=file, embed=embed)
                except nextcord.errors.Forbidden:
                    embed.add_field(
                        name="ERROR: No access",
                        value=f"Sorry! I don't have access to {text_channel.mention}. You'll need "
                        f"to give me permission to view the channel if you want "
                        f"to archive it",
                        inline=False,
                    )
                    await discord_utils.send_message(ctx, embed)
                    continue
                # There has been an issue with AIO HTTP message sending fails, in which case discord.py crashes?
                # So adding this try/catch for runtime to catch this. I don't think it's a deterministic error
                except RuntimeError:
                    embed = discord_utils.create_embed()
                    embed.add_field(
                        name="ERROR: Failed to send archive",
                        value=f"Sorry! I had trouble sending you the archived file for "
                        f"{text_channel.mention}. Perhaps you can try again with {ctx.prefix}archivechannel"
                        f" after I've finished archiving {category.mention}.",
                        inline=False,
                    )
                    await discord_utils.send_message(ctx, embed)
                    continue
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
    async def archiveserver(self, ctx):
        """Command to archive every text channel in the server. WARNING: This command will take *very*
        long on any reasonably aged server

        Permission Category : Admin or Bot Owner Roles only.
        Usage: `~archiveserver`
        """
        await logging_utils.log_command(
            "archiveserver", ctx.guild, ctx.channel, ctx.author
        )
        embed = discord_utils.create_embed()

        # If we don't have the lock, let the user know it may take a while.
        msg = None
        if self.lock.locked():
            msg = await ctx.send(embed=archive_utils.get_delay_embed())

        # LOCK EVERYTHING
        async with self.lock:
            start_embed = await self.get_start_embed(ctx.guild, ctx.guild.text_channels)
            if msg:
                await msg.delete()
                msg = None

            msgs = await discord_utils.send_message(ctx, start_embed)
            for text_channel in ctx.guild.text_channels:
                archive_utils.reset_archive_dir()
                try:
                    (
                        zip_file,
                        zip_file_size,
                        textfile,
                        textfile_size,
                    ) = await self.archive_one_channel(text_channel)
                    file, embed = self.get_file_and_embed(
                        text_channel,
                        ctx.guild.filesize_limit * 0 + constants.HARDCODED_FILE_SIZE,
                        zip_file,
                        zip_file_size,
                        textfile,
                        textfile_size,
                    )
                    await ctx.send(file=file, embed=embed)
                except nextcord.errors.Forbidden:
                    embed.add_field(
                        name="ERROR: No access",
                        value=f"Sorry! I don't have access to {text_channel.mention}. You'll need "
                        f"to give me permission to view the channel if you want "
                        f"to archive it",
                        inline=False,
                    )
                    await discord_utils.send_message(ctx, embed)
                    continue
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
                value=f"{chr(10).join([channel.name for channel in multiple_channels])}",
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
