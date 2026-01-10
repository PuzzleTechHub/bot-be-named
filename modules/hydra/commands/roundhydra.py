"""
roundhydra command - Sets or updates round information on the Overview sheet.
"""

from typing import Optional

import emoji
import gspread
import nextcord
from nextcord.ext import commands

from modules.hydra.hydra_utils.sheet_command_base import SheetCommandBase
from utils import command_predicates, discord_utils, logging_utils, sheets_constants


def setup_cmd(cog):
    """Register the roundhydra command with the bot."""

    @command_predicates.is_solver()
    @cog.bot.command(name="roundhydra")
    async def roundhydra(ctx: commands.Context, round_name: Optional[str] = None):
        """Sets or updates the round information on the Overview sheet. Passing no argument retrieves the current round.

        Permission Category : Solver Roles only
        Usage: `~roundhydra` (retrieves current round)
        Usage: `~roundhydra "Round Name"` (sets round)
        """
        await logging_utils.log_command(
            "roundhydra", ctx.guild, ctx.channel, str(ctx.author)
        )

        # Type guard: ensure we're in a guild text channel
        if not isinstance(ctx.channel, (nextcord.TextChannel, nextcord.Thread)):
            embed = discord_utils.create_embed()
            embed.add_field(
                name="Failed",
                value="This command can only be used in a guild text channel or thread.",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return

        base = SheetCommandBase(ctx, cog.gspread_client)
        curr_sheet_link, overview_sheet, row_to_find = await base.get_sheet_context()

        if overview_sheet is None:
            return

        embed = discord_utils.create_embed()

        round_col = sheets_constants.ROUND_COLUMN

        try:
            if round_name is None:
                # If no arg passed, retrieve current round and tell user
                current_round = overview_sheet.get_cell_value(
                    round_col + str(row_to_find)
                )
                if current_round is None or current_round == "":
                    embed.add_field(
                        name="Current Round",
                        value=f"The current round for {ctx.channel.mention} is not set.",
                        inline=False,
                    )
                else:
                    embed.add_field(
                        name="Current Round",
                        value=f"The current round for {ctx.channel.mention} is `{current_round}`.",
                        inline=False,
                    )
                await discord_utils.send_message(ctx, embed)
            else:
                # Update round instead
                current_round = overview_sheet.get_cell_value(
                    round_col + str(row_to_find)
                )

                overview_sheet.worksheet.update_acell(
                    round_col + str(row_to_find), round_name
                )

                if current_round:
                    embed.add_field(
                        name="Success",
                        value=f"Successfully updated round for {ctx.channel.mention} from `{current_round}` to `{round_name}`",
                        inline=False,
                    )
                else:
                    embed.add_field(
                        name="Success",
                        value=f"Successfully updated round for {ctx.channel.mention} to `{round_name}`",
                        inline=False,
                    )

                await ctx.message.add_reaction(emoji.emojize(":check_mark_button:"))
                await discord_utils.send_message(ctx, embed)

        except gspread.exceptions.APIError as e:
            error_json = e.response.json()
            error_status = error_json.get("error", {}).get("status")
            if error_status == "PERMISSION_DENIED":
                embed.add_field(
                    name="Failed",
                    value="Could not update the sheet. Permission denied.",
                    inline=False,
                )
            else:
                embed.add_field(
                    name="Failed",
                    value=f"Unknown GSheets API Error - `{error_json.get('error', {}).get('message')}`",
                    inline=False,
                )
            await discord_utils.send_message(ctx, embed)
