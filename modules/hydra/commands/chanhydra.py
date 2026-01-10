"""
chanhydra command - Creates puzzle channels and tabs in batch.
"""

import shlex

import emoji
from nextcord.ext import commands

from modules.hydra.hydra_utils import sheet_utils as hydra_sheet_utils
from utils import command_predicates, discord_utils, logging_utils


def setup_cmd(cog):
    """
    Register the chanhydra command with the bot.

    Args:
        cog: The HydraCog instance providing shared resources.
    """

    @command_predicates.is_solver()
    @cog.bot.command(name="chanhydra")
    async def chanhydra(ctx: commands.Context, *, content: str = ""):
        """Creates a new tab and a new channel for a new feeder puzzle and then updates the info in the sheet accordingly.

        Requires that the sheet has Overview and Template tabs.
        Supports creating multiple channels in parallel delimited by new lines (CTRL + Enter).

        Permission Category : Solver Roles only.
        Usage: ~chanhydra "Puzzle Name"
        Usage: ~chanhydra PuzzleName "http://www.linktopuzzle.com"
        Usage:
        ~chanhydra
        APuzzle "http://linktoapuzzle.com"
        "B Puzzle" "http://linktobpuzzle.com"
        3rdPuzzle
        """

        await logging_utils.log_command(
            "chanhydra", ctx.guild, ctx.channel, str(ctx.author)
        )
        embed = discord_utils.create_embed()

        content = content.strip()

        if not content:
            embed.add_field(
                name="Failed",
                value="You need to provide at least a puzzle name.",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return

        # Parse all puzzle configurations
        puzzle_configs = []
        lines = [line.strip() for line in content.split("\n") if line.strip()]

        for line in lines:
            try:
                parts = shlex.split(line)
            except ValueError as e:
                embed.add_field(
                    name="Failed",
                    value=f"Error parsing line `{line}`... continuing parsing the rest.\nError: {str(e)}",
                    inline=False,
                )
                await discord_utils.send_message(ctx, embed)
                continue

            if not parts:
                continue

            puzzle_name = parts[0]
            puzzle_url = parts[1] if len(parts) > 1 else ""
            puzzle_configs.append((puzzle_name, puzzle_url))

        if not puzzle_configs:
            embed.add_field(
                name="Failed",
                value="No data passed into the command!",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return

        # Batch create all channels and sheets
        results = await hydra_sheet_utils.batch_create_puzzle_channels(
            cog.bot,
            ctx,
            cog.gspread_client,
            puzzle_configs,
        )

        # Report results
        success_count = sum(1 for r in results if r[0] is not None)
        success_messages = []
        failed_messages = []

        for result in results:
            if result[0] is not None:  # Success
                channel = result[2]
                puzzle_name = result[3]
                success_messages.append(
                    f"- Channel `{puzzle_name}` created as {channel.mention}, posts pinned!"
                )
            else:  # Failed
                puzzle_name = result[3]
                failed_messages.append(f"- `{puzzle_name}`")

        if success_count > 0:
            embed = discord_utils.create_embed()
            embed.add_field(
                name="Sucess",
                value=(
                    f"Successfully created {success_count} puzzle channel(s):\n\n"
                    "\n".join(success_messages)
                    if success_messages
                    else f"Successfully created {success_count} puzzle channel(s)!"
                ),
                inline=False,
            )
            await ctx.message.add_reaction(emoji.emojize(":check_mark_button:"))
            await discord_utils.send_message(ctx, embed)

        if success_count < len(puzzle_configs):
            failed_count = len(puzzle_configs) - success_count
            embed = discord_utils.create_embed()
            embed.add_field(
                name="Failed",
                value=f"Failed to create {failed_count} puzzle channel(s). Check earlier messages for details.\n\n"
                + "\n".join(failed_messages),
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
