"""
Hydra-specific versions of lion commands with additional features.
These wrap or extend the lion commands with hydra-specific functionality.
"""

import gspread
from utils import discord_utils, sheets_constants
from modules.hydra import constants as hydra_constants
from modules.hydra.hydra_utils.hydra_helpers import get_ordinal_suffix


async def send_solve_notification(bot, ctx, overview_sheet, answer: str = None):
    """
    Send a notification to the bot stream channel when a puzzle is solved.

    Args:
        bot: The bot instance
        ctx: The command context
        overview_sheet: The overview sheet object to count solves from
        answer: The puzzle answer (optional)
    """
    if hydra_constants.TM_BOT_STREAM_CHANNEL_ID is None:
        return

    try:
        bot_stream_channel = bot.get_channel(hydra_constants.TM_BOT_STREAM_CHANNEL_ID)
        if bot_stream_channel is None:
            return

        # Count solved puzzles from overview sheet
        solve_count = 0
        try:
            overview_data = overview_sheet.overview_data
            status_col_letter = overview_sheet.get_cell_value(
                sheets_constants.STATUS_COLUMN_LOCATION
            )
            _, status_col_idx = gspread.utils.a1_to_rowcol(status_col_letter + "1")
            for row in overview_data:
                if len(row) >= status_col_idx:
                    row_status = row[status_col_idx - 1]
                    if row_status in ["Solved", "Backsolved"]:
                        solve_count += 1
        except Exception:
            solve_count = 0

        answer_display = f"||{answer.upper()}||" if answer else "*(no answer provided)*"
        stream_embed = discord_utils.create_embed()

        if solve_count > 0:
            suffix = get_ordinal_suffix(solve_count)
            stream_embed.add_field(
                name="🎉 Puzzle Solved!",
                value=f"Puzzle {ctx.channel.mention} solved with answer {answer_display}!\n\n"
                f"This is our **{solve_count}{suffix}** solve of the hunt.",
                inline=False,
            )
        else:
            stream_embed.add_field(
                name="🎉 FIRST PUZZLE SOLVED!",
                value=f"Puzzle {ctx.channel.mention} is our first puzzle solved with answer {answer_display}! "
                f"Let's keep the momentum going!\n\n",
                inline=False,
            )

        await bot_stream_channel.send(embed=stream_embed)
    except Exception:
        pass  # Silently fail if bot stream notification fails


