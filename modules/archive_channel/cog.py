import discord
from discord.ext import commands
from dotenv.main import load_dotenv
import constants
import os
import shutil
import zipfile
from modules.code import utils
load_dotenv(override=True)

#channel_id = 800462258484019230
channel_id = 799271641669697537

ARCHIVE = 'archive'
IMAGES = 'images'
TEXT_LOG_PATH = 'channel_text_log.txt'
client = discord.Client()

class ArchiveChannelCog(commands.Cog, name="Archive Channel"):
    """Downloads a channel's history and sends it as a file to the user"""
    def __init__(self, bot):
        self.bot = bot
        self.compression = zipfile.ZIP_DEFLATED

        if os.path.exists(ARCHIVE):
            shutil.rmtree(ARCHIVE)
        os.mkdir(ARCHIVE)
        os.mkdir(os.path.join(ARCHIVE, IMAGES))



    @commands.command(name="archivechannel")
    async def archivechannel(self, ctx, *args):
        """Command to download channel's history"""
        print("Received archivechannel")
        embed = utils.create_embed()
        # Check if the user supplied a channel
        if len(args) > 0:
            # Allows them to do e.g. ~archivechannel #MH-general
            channel_id = int(args[0].replace('>', '').replace('<#', ''))
            channel = self.bot.get_channel(channel_id)
            # Write the chat log. Replace attachments with their filename (for easy reference)
            with open(os.path.join(ARCHIVE, TEXT_LOG_PATH), 'w') as f:
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
                        original_path = os.path.join(ARCHIVE, IMAGES, attachment.filename)
                        proposed_path = original_path
                        dupe_counter = 1
                        while os.path.exists(proposed_path):
                            proposed_path = original_path.split('.')[0] + f' ({dupe_counter})' + original_path.split('.')[1]
                            dupe_counter += 1
                        await attachment.save(proposed_path)
                    f.write("\n")
            ZIP_FILENAME = channel.name + '_archive.zip'
            with zipfile.ZipFile(ZIP_FILENAME, mode='w') as zf:
                for root, directories, files in os.walk(ARCHIVE):
                    for filename in files:
                        zf.write(os.path.join(root, filename), compress_type=self.compression)

            file = discord.File(ZIP_FILENAME)
            embed.add_field(name=f"{constants.SUCCESS}", value=f"Here is the archive")
            try:
                await ctx.send(embed=embed, file=file)
            except discord.errors.HTTPException:
                await ctx.send("Images too large. Only sending chat history")
                await ctx.send(file=discord.File(os.path.join(ARCHIVE, TEXT_LOG_PATH)))
            print("Sent embed")
            shutil.rmtree(ARCHIVE)
            os.mkdir(ARCHIVE)
            os.mkdir(os.path.join(ARCHIVE, IMAGES))
        else:
            embed.add_field(name=f"{constants.FAILED}!", value=f"You must specify a channel!")
            await ctx.send(embed=embed)

        #messages = await channel.history(limit=None, oldest_first=True).flatten()
        #print(len(messages))
        #time.sleep(2)
        #for msg in messages:
        #    print(f"{msg.created_at.strftime('%m/%d/%Y, %H:%M:%S')} - {msg.author.display_name}: {msg.clean_content}")
        #with open('archived_channel', 'w') as f:
        #async for msg in channel.history(limit=None, oldest_first=True):
        #    print(f"{msg.created_at} - {msg.author.display_name}: {msg.clean_content}")
        #    f.write(f"{msg.created_at} - {msg.author.display_name}: {msg.clean_content}")


def setup(bot):
    bot.add_cog(ArchiveChannelCog(bot))