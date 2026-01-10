"""
anychanhydra command - Creates a puzzle channel from a specific template.
"""

import shlex

from modules.hydra.hydra_utils import sheet_utils as hydra_sheet_utils
from utils import command_predicates, discord_utils, logging_utils


def setup_cmd(cog):
    """Register the anychanhydra command with the bot."""

    @command_predicates.is_solver()
    @cog.bot.command(name="anychanhydra", aliases=["anyhydra"])
    async def anychanhydra(ctx, *, args):
        """Creates a new tab from a template, and a new channel for a puzzle. Then updates the info in the sheet accordingly.

        Creates a new puzzle channel based on a template in the tethered GSheet. Template must be passed in.

        Requires that the sheet has Overview following Hydra rules (FIXME).
        Requires that there is a template tab on the sheet with that name, for example passing "Acrostics" uses "Acrostics Template".
        Requires that Template tab follows Hydra rules (Cell B4 must be used for answer).

        Permission Category : Solver Roles only.

        Usage: ~anychanhydra "Puzzle Name" "TemplateName" (uses "TemplateName Template" from the sheet)
        Usage: ~anychanhydra PuzzleName "Square" "http://www.linktopuzzle.com" (uses "Square Template" from the sheet)
        """
        await logging_utils.log_command(
            "anychanhydra", ctx.guild, ctx.channel, ctx.author
        )

        arg_list = shlex.split(args)
        if len(arg_list) < 2 or len(arg_list) > 3:
            embed = discord_utils.create_embed()
            embed.add_field(
                name="Failed",
                value="Invalid arguments. Usage: `~anychanhydra [puzzle name] [template name] [puzzle url (optional)]`",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return

        puzzle_name = arg_list[0]
        template_name = arg_list[1]
        puzzle_url = arg_list[2] if len(arg_list) > 2 else None

        await hydra_sheet_utils.create_puzzle_channel_from_template(
            cog.bot,
            ctx,
            puzzle_name,
            template_name,
            puzzle_url,
            cog.gspread_client,
        )
