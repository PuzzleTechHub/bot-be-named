import nextcord
import constants
import os
import zipfile
import asyncio
import unicodedata
import re
from nextcord.ext import commands
from typing import Tuple, Union, TextIO
from utils import discord_utils, logging_utils, command_predicates
from modules.archive import archive_constants, archive_utils

"""
Archive module. Downloads a channel's history and sends it as a file
"""


class ArchiveCog(commands.Cog, name="Archive"):
    """
    Downloads a channel's history and sends it as a file
    """

    def __init__(self, bot):
        self.bot = bot
        self.compression = zipfile.ZIP_DEFLATED
        self.lock = asyncio.Lock()

        archive_utils.reset_archive_dir()

    async def archive_message(self, f: TextIO, msg: nextcord.Message):
        f.write(
            f"[ {msg.created_at.strftime('%m-%d-%Y, %H:%M:%S')} ] "
            f"{msg.author.display_name.rjust(25, ' ')}: "
            f"{msg.clean_content}"
        )
        for attachment in msg.attachments:
            f.write(f" {attachment.filename}")
            # change duplicate filenames
            # img.png would become img (1).png
            original_path = os.path.join(
                archive_constants.ARCHIVE,
                archive_constants.IMAGES,
                attachment.filename,
            )
            proposed_path = original_path
            dupe_counter = 1
            while os.path.exists(proposed_path):
                proposed_path = (
                    original_path.split(".")[0]
                    + f" ({dupe_counter})."
                    + original_path.split(".")[1]
                )
                dupe_counter += 1
            # The discord filenames can get too long and throw an OSError
            try:
                await attachment.save(proposed_path)
            except OSError:
                await attachment.save(
                    f"path_too_long_{dupe_counter}.{original_path.split('.')[1]}"
                )
        # Important: Write the newline after each comment is done
        f.write("\n")

    async def archive_one_channel(
        self, channel: Union[nextcord.TextChannel, nextcord.Thread]
    ) -> Tuple[nextcord.File, int, nextcord.File, int]:
        """Download a channel's history"""
        # Write the chat log. Replace attachments with their filename (for easy reference)
        text_log_path = os.path.join(
            archive_constants.ARCHIVE,
            channel.name + "_" + archive_constants.TEXT_LOG_PATH,
        )
        with open(text_log_path, "w") as f:
            async for msg in channel.history(limit=None, oldest_first=True):
                await self.archive_message(f, msg)
                # Threads are attached to normal messages
                if msg.flags.has_thread and msg.thread:
                    f.write(f"[  {msg.thread.id} ] {'THREAD'.rjust(25, ' ')}: ")
                    f.write(msg.thread.name + "\n")
                    thread_dir = os.path.join(
                        archive_constants.ARCHIVE,
                        f"{channel.name}_{archive_constants.THREADS}",
                    )
                    # The thread "name" is by default the original message content. Slugify and truncate if necessary
                    norm_thread_name = (
                        unicodedata.normalize(
                            "NFKD", f"{msg.thread.id}_{msg.thread.name}"
                        )
                        .encode("ascii", "ignore")
                        .decode("ascii")
                    )
                    norm_thread_name = re.sub(r"[^\w\s-]", "", norm_thread_name.lower())
                    norm_thread_name = re.sub(r"[-\s]+", "-", norm_thread_name).strip(
                        "-_"
                    )
                    norm_thread_name = norm_thread_name[:250]
                    os.makedirs(thread_dir, exist_ok=True)
                    thread_log_path = os.path.join(
                        thread_dir, norm_thread_name + ".txt"
                    )
                    with open(thread_log_path, "w") as thread_f:
                        async for t_msg in msg.thread.history(
                            limit=None, oldest_first=True
                        ):
                            await self.archive_message(thread_f, t_msg)

            text_file_size = f.tell()

        ZIP_FILENAME = os.path.join(
            archive_constants.ARCHIVE, channel.name + "_archive.zip"
        )
        # Create a zipfile and then walk through all the saved chatlogs and images, and zip em up
        with zipfile.ZipFile(ZIP_FILENAME, mode="w") as zf:
            for root, directories, files in os.walk(archive_constants.ARCHIVE):
                for filename in files:
                    if filename == ZIP_FILENAME.split("/")[-1]:  # Don't include self
                        continue
                    zf.write(
                        os.path.join(root, filename), compress_type=self.compression
                    )
            zf_file_size = zf.fp.tell()
        return (
            nextcord.File(ZIP_FILENAME),
            zf_file_size,
            nextcord.File(text_log_path),
            text_file_size,
        )

    def get_file_and_embed(
        self, channel, filesize_limit, zip_file, zip_file_size, textfile, textfile_size
    ):
        """Check if zipfile and textfile can be sent or not, create embed with message"""
        embed = discord_utils.create_embed()

        if zip_file_size > filesize_limit:
            if textfile_size > filesize_limit:
                embed.add_field(
                    name="ERROR: History Too Big",
                    value=f"Sorry about that! The chat log in {channel.mention} is too big for me to send.\n"
                    f"The max file size I can send in this server is "
                    f"`{(filesize_limit/constants.BYTES_TO_MEGABYTES):.2f}MB`, but the chat log is "
                    f"`{(textfile_size/constants.BYTES_TO_MEGABYTES):.2f}MB`",
                    inline=False,
                )
                file = None
            else:
                embed.add_field(
                    name="WARNING: Attachments Too Big",
                    value=f"There are too many photos in {channel.mention} for me to send. The max file size "
                    f"I can send in this server is "
                    f"`{(filesize_limit/constants.BYTES_TO_MEGABYTES):.2f}MB` but the zip is "
                    f"`{(zip_file_size/constants.BYTES_TO_MEGABYTES):.2f}MB`. I'll only be able to send you the chat log.",
                    inline=False,
                )
                ZIP_FILENAME = os.path.join(
                    archive_constants.ARCHIVE, channel.name + "_archive.zip"
                )
                with zipfile.ZipFile(ZIP_FILENAME, mode="w") as zf:
                    zf.write(
                        os.path.join(
                            archive_constants.ARCHIVE,
                            channel.name + "_" + archive_constants.TEXT_LOG_PATH,
                        ),
                        compress_type=self.compression,
                    )
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
            await ctx.send(embed=discord_utils.create_no_argument_embed("channel"))
            return
        # If we don't have the lock, let the user know it may take a while.
        msg = None

        for channelname in args:
            if self.lock.locked():
                msg = await ctx.send(embed=archive_utils.get_delay_embed())
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
                        await ctx.send(embed=embed)
                        return
                    if not (
                        channel.type.name in ["text", "public_thread", "private_thread"]
                    ):
                        embed.add_field(
                            name="ERROR: Cannot archive non-text channels",
                            value=f"Sorry! I can only archive text channels, but "
                            f"{channel} is a {channel.type} channel.",
                            inline=False,
                        )
                        await ctx.send(embed=embed)
                        return
                # If we've gotten to this point, we know we have a channel so we should probably let the user know.
                start_embed = await self.get_start_embed(channel)
                msg = await ctx.send(embed=start_embed)
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
                    await ctx.send(embed=embed)
                    return
                file, embed = self.get_file_and_embed(
                    channel,
                    ctx.guild.filesize_limit,
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
                    await ctx.send(embed=embed)

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
            await ctx.send(embed=discord_utils.create_no_argument_embed("category"))
            return

        # If we don't have the lock, let the user know it may take a while.
        msg = None
        if self.lock.locked():
            msg = await ctx.send(embed=archive_utils.get_delay_embed())
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
                await ctx.send(embed=embed)
                return

            start_embed = await self.get_start_embed(category, category.text_channels)
            # SOMETIMES THE EMBED IS TOO LONG FOR DISCORD
            embeds = discord_utils.split_embed(start_embed)
            msgs = []
            for embed in embeds:
                msgs.append(await ctx.send(embed=embed))

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
                        ctx.guild.filesize_limit,
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
                    await ctx.send(embed=embed)
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
                    await ctx.send(embed=embed)
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
            await ctx.send(embed=embed)
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
            # SOMETIMES THE EMBED IS TOO LONG FOR DISCORD
            embeds = discord_utils.split_embed(start_embed)
            msgs = []
            for embed in embeds:
                msgs.append(await ctx.send(embed=embed))

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
                        ctx.guild.filesize_limit,
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
                    await ctx.send(embed=embed)
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
            await ctx.send(embed=embed)
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
