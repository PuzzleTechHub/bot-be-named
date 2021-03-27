import discord
from discord.ext import commands
from dotenv.main import load_dotenv
import constants
import os
import shutil
import zipfile
from utils import discord_utils
load_dotenv(override=True)


class ArchiveChannelCog(commands.Cog, name="Archive Channel"):
    """Downloads a channel's history and sends it as a file to the user"""
    def __init__(self, bot):
        self.bot = bot
        self.compression = zipfile.ZIP_DEFLATED

        if os.path.exists(constants.ARCHIVE):
            shutil.rmtree(constants.ARCHIVE)
        os.mkdir(constants.ARCHIVE)
        os.mkdir(os.path.join(constants.ARCHIVE, constants.IMAGES))



    @commands.command(name="archivechannel")
    async def archivechannel(self, ctx, *args):
        """Command to download channel's history"""
        # TODO: Need error handling for asking a channel we don't have access to or invalid channel name
        print("Received archivechannel")
        # Check if the user supplied a channel
        if len(args) > 0:
            # Allows them to do e.g. ~archivechannel #MH-general
            if isinstance(args[0], str):
                channel_id = int(args[0].replace('>', '').replace('<#', ''))
            else:
                channel_id = args[0]
            channel = self.bot.get_channel(channel_id)
            # Write the chat log. Replace attachments with their filename (for easy reference)
            text_log_path = os.path.join(constants.ARCHIVE, channel.name + '_' + constants.TEXT_LOG_PATH)
            with open(text_log_path, 'w') as f:
                async for msg in channel.history(limit=None, oldest_first=True):
                    #print(f"{msg.created_at} - {msg.author.display_name.rjust(25, ' ')}: {msg.clean_content}")
                    f.write(f"[ {msg.created_at.strftime('%m-%d-%Y, %H:%M:%S')} ] "
                            f"{msg.author.display_name.rjust(25, ' ')}: "
                            f"{msg.clean_content}")
                    # Save attachments TODO is this necessary? Might waste space
                    for attachment in msg.attachments:
                        f.write(f" {attachment.filename}")
                        # change duplicate filenames
                        # img.png would become img (1).png
                        original_path = os.path.join(constants.ARCHIVE, constants.IMAGES, attachment.filename)
                        proposed_path = original_path
                        dupe_counter = 1
                        while os.path.exists(proposed_path):
                            proposed_path = original_path.split('.')[0] + f' ({dupe_counter}).' + original_path.split('.')[1]
                            dupe_counter += 1
                        await attachment.save(proposed_path)
                    # Important: Write the newline after each comment is done
                    f.write("\n")
            ZIP_FILENAME = channel.name + '_archive.zip'
            # Create a zipfile and then walk through all the saved chatlogs and images, and zip em up
            with zipfile.ZipFile(ZIP_FILENAME, mode='w') as zf:
                for root, directories, files in os.walk(constants.ARCHIVE):
                    for filename in files:
                        zf.write(os.path.join(root, filename), compress_type=self.compression)
            # TODO: It may often be the case that we will be above 8MB (max filesize).
            # In that case, maybe we should split into multiple zips
            file = discord.File(ZIP_FILENAME)
            try:
                await ctx.send(file=file)
            except discord.errors.HTTPException:
                await ctx.send("Images too large. Only sending chat history")
                await ctx.send(file=discord.File(constants.TEXT_LOG_PATH))
            print("Sent embed")
            # Remove the archive directory and remake
            shutil.rmtree(constants.ARCHIVE)
            os.mkdir(constants.ARCHIVE)
            os.mkdir(os.path.join(constants.ARCHIVE, constants.IMAGES))
        # No arguments provided
        else:
            await ctx.send(embed=discord_utils.create_no_argument_embed('channel'))

    @commands.command(name="archivecategory")
    async def archivecategory(self, ctx, *args):
        """Command to download the history of every text channel in the category"""
        print("Received archivecategory")
        embed = discord_utils.create_embed()
        # Check if the user supplied a channel
        if len(args) > 0:
            channel_id = int(args[0].replace('>', '').replace('<#', ''))
            channel = self.bot.get_channel(channel_id)
            print(channel.name)
            print(channel.text_channels)
            for text_channel in channel.text_channels:
                try:
                    await self.archivechannel(ctx, text_channel.id)
                except discord.errors.Forbidden:
                    continue
        # No arguments provided
        else:
            await ctx.send(embed=discord_utils.create_no_argument_embed('category'))


def setup(bot):
    bot.add_cog(ArchiveChannelCog(bot))