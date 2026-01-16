"""
Hydra-specific versions of lion commands with additional features.
These wrap or extend the lion commands with hydra-specific functionality.
"""

import os
from typing import Optional
from utils import discord_utils


async def send_solve_notification(bot, ctx, answer: Optional[str] = None):
    """
    Send a notification to the bot stream channel when a puzzle is solved.
    Counts solved puzzles from the big board URL and column specified in .env file.

    Args:
        bot: The bot instance
        ctx: The command context
        answer: The puzzle answer (optional)
    """
    tm_bot_stream_channel_id = os.getenv("TM_BOT_STREAM_CHANNEL_ID")
    if not tm_bot_stream_channel_id:
        return

    try:
        channel_id = int(tm_bot_stream_channel_id)

        bot_stream_channel = bot.get_channel(channel_id)
        if bot_stream_channel is None:
            bot_stream_channel = await bot.fetch_channel(channel_id)

        # Clean up answer formatting
        if answer:
            clean_answer = answer.strip().replace("\n", " ").upper()
            answer_display = f"||`{clean_answer}`||"
        else:
            answer_display = "*(no answer provided)*"

        stream_embed = discord_utils.create_embed()
        stream_embed.add_field(
            name="🎉 Puzzle Solved!",
            value=(
                f"Puzzle {ctx.channel.mention} has been solved!\n\n"
                f"**Answer:** {answer_display}"
            ),
            inline=False,
        )

        await bot_stream_channel.send(embed=stream_embed)

    except Exception:
        pass  # Silently fail if bot stream notification fails


async def scrape_for_puzzles():
    pass  # Placeholder for future implementation
