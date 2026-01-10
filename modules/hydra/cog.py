import asyncio

from nextcord.ext import commands

from modules.hydra.commands import load_commands
from utils import google_utils

"""
Hydra module. Module with more advanced GSheet-Discord interfacing. See module's README.md for more.
"""


class HydraCog(commands.Cog, name="Hydra"):
    """
    More powerful useful GSheet-Discord commands.
    """

    def __init__(self, bot):
        self.bot = bot
        self.lock = asyncio.Lock()
        self.gdrive_credentials = google_utils.get_gdrive_credentials()
        self.gspread_client = google_utils.create_gspread_client()

        # Auto-load commands from modules/hydra/commands/
        load_commands(self)

    # Commands have been migrated to individual files in modules/hydra/commands/
    # They are automatically loaded via load_commands() in __init__


def setup(bot):
    bot.add_cog(HydraCog(bot))
