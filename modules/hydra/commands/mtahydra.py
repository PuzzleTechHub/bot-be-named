"""
mtahydra command - Moves puzzle channel to archive and moves tab to end of sheet.
"""

from typing import Optional

from modules.hydra.hydra_utils import discord_utils as hydra_discord_utils
from modules.hydra.hydra_utils import sheet_utils as hydra_sheet_utils
from utils import command_predicates, logging_utils


def setup_cmd(cog):
    """Register the mtahydra command with the bot."""

    @command_predicates.is_solver()
    @cog.bot.command(name="mtahydra", aliases=["movetoarchivehydra"])
    async def mtahydra(ctx, *, category_name: Optional[str] = None):
        """Finds a category with `<category_name> Archive`, and moves the channel to that category.
        Fails if there is no such category. If the category is full (50 channels), I will make a new one.
        If called from thread (instead of channel), closes the thread instead of moving channel.

        In the hydra implementation of ~mta, the archive category name is standardized.

        It must be in the form of `<category_name> Archive`, e.g. `MH21 Students Archive`.
        Your solving category should not end with Archive.

        Also moves the tab to the end of the list of tabs on the Google Sheet.

        Attempts to search smart, for example `~mtahydra "MH21 Students"` will search for "MH21 Students Archive" and "MH21 Archive" categories.
        Some other common variants for "Archive" will also be attempted.

        Permission Category : Solver Roles only.
        Usage: `~mtahydra`
        Usage: `~mtahydra archive_category_name`
        """
        await logging_utils.log_command("mtahydra", ctx.guild, ctx.channel, ctx.author)
        await hydra_sheet_utils.sheet_move_to_archive(cog.gspread_client, ctx)
        await hydra_discord_utils.category_move_to_archive(ctx, category_name)
