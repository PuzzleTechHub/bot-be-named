"""
Hydra-specific versions of lion commands with additional features.
These wrap or extend the lion commands with hydra-specific functionality.
"""

import os
from typing import Optional

import gspread

from modules.hydra.hydra_utils.hydra_helpers import get_ordinal_suffix
from utils import discord_utils, google_utils


async def send_solve_notification(bot, ctx, answer: Optional[str] = None):
    """
    Send a notification to the bot stream channel when a puzzle is solved.
    Counts solved puzzles from the big board URL and column specified in .env file.

    Args:
        bot: The bot instance
        ctx: The command context
        answer: The puzzle answer (optional)
    """
    # Read TM constants from environment variables
    tm_bot_stream_channel_id = os.getenv("TM_BOT_STREAM_CHANNEL_ID")
    tm_big_board_url = os.getenv("TM_BIG_BOARD_URL")
    tm_big_board_status_column = os.getenv("TM_BIG_BOARD_STATUS_COLUMN")

    if not tm_bot_stream_channel_id:
        return

    try:
        bot_stream_channel = bot.get_channel(int(tm_bot_stream_channel_id))
        if bot_stream_channel is None:
            return

        # Count solved puzzles from big board URL if configured
        solve_count = 0
        if tm_big_board_url and tm_big_board_status_column:
            try:
                gspread_client = google_utils.create_gspread_client()
                big_board = gspread_client.open_by_url(tm_big_board_url)
                big_board_sheet = big_board.sheet1

                # Get all data from the big board
                all_data = big_board_sheet.get_all_values()

                # Convert column letter to index
                _, status_col_idx = gspread.utils.a1_to_rowcol(
                    tm_big_board_status_column + "1"
                )

                # Count solved and backsolved puzzles
                for row in all_data:
                    if len(row) >= status_col_idx:
                        row_status = row[status_col_idx - 1]
                        if row_status in ["Solved", "Backsolved"]:
                            solve_count += 1
            except Exception:
                solve_count = 0

        answer_display = (
            f"||`{answer.upper()}`||" if answer else "*(no answer provided)*"
        )
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
