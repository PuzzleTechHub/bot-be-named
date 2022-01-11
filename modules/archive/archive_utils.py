from modules.archive import archive_constants
from utils import discord_utils
import os, shutil


def get_delay_embed():
    embed = discord_utils.create_embed()
    embed.add_field(
        name="Warning: Delay!",
        value="Hi! It appears we're a little busy at the moment, so our archiving may take a while. "
        "Sorry about that! We'll get to it as soon as possible.",
        inline=False,
    )
    return embed


def reset_archive_dir():
    # Remove the archive directory and remake
    if os.path.exists(archive_constants.ARCHIVE):
        shutil.rmtree(archive_constants.ARCHIVE)
    os.mkdir(archive_constants.ARCHIVE)
    os.mkdir(os.path.join(archive_constants.ARCHIVE, archive_constants.IMAGES))
