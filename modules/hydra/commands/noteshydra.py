"""
noteshydra command - Sets or updates notes information on the Overview sheet.
"""

from typing import Optional

import emoji
import gspread
import nextcord
from nextcord.ext import commands

from modules.hydra.hydra_utils.sheet_command_base import SheetCommandBase
from utils import command_predicates, discord_utils, logging_utils, sheets_constants


def setup_cmd(cog):
    """Register the noteshydra command with the bot."""

    @command_predicates.is_solver()
    @cog.bot.command(name="noteshydra")
    async def noteshydra(ctx: commands.Context, notes: Optional[str] = None):
        """Sets or updates the notes information on the Overview sheet. Passing no argument retrieves the current notes.

        Permission Category : Solver Roles only
        Usage: `~noteshydra` (retrieves current notes)
        Usage: `~noteshydra "This puzzle has unclued anagrams."` (sets notes)
        """

        await logging_utils.log_command(
            "noteshydra", ctx.guild, ctx.channel, str(ctx.author)
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

        notes_col = sheets_constants.NOTES_COLUMN

        try:
            if notes is None:
                # If no arg passed, retrieve current notes and tell user
                current_notes = overview_sheet.get_cell_value(
                    notes_col + str(row_to_find)
                )
                if current_notes is None or current_notes == "":
                    embed.add_field(
                        name="Current Notes",
                        value=f"The current notes for {ctx.channel.mention} are not set.",
                        inline=False,
                    )
                else:
                    embed.add_field(
                        name="Current Notes",
                        value=f"The current notes for {ctx.channel.mention} are `{current_notes}`.",
                        inline=False,
                    )
                await discord_utils.send_message(ctx, embed)
            else:
                # Update notes instead
                current_notes = overview_sheet.get_cell_value(
                    notes_col + str(row_to_find)
                )

                overview_sheet.worksheet.update_acell(
                    notes_col + str(row_to_find), notes
                )

                if current_notes:
                    embed.add_field(
                        name="Success",
                        value=f"Successfully updated notes for {ctx.channel.mention} from `{current_notes}` to `{notes}`",
                        inline=False,
                    )
                else:
                    embed.add_field(
                        name="Success",
                        value=f"Successfully updated notes for {ctx.channel.mention} to `{notes}`",
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
