"""
catsummaryhydra command - Collates notes from overview sheet for all channels in a category.
"""

import gspread

from modules.hydra import constants as hydra_constants
from modules.hydra.hydra_utils import sheet_utils as hydra_sheet_utils
from utils import (
    command_predicates,
    discord_utils,
    logging_utils,
    sheet_utils,
    sheets_constants,
)


def setup_cmd(cog):
    """Register the catsummaryhydra command with the bot."""

    @command_predicates.is_solver()
    @cog.bot.command(name="catsummaryhydra", aliases=["categorysummaryhydra"])
    async def catsummaryhydra(ctx) -> None:
        """Collates all the notes on the overview sheet for each text channel in the category the command was
        called in. Silently skips channels not on the overview. The sheet will need to follow the Hydra
        requirements for this to work as expected.

        Permission Category : Solver Roles only.

        Usage: `~catsummaryhydra`
        """
        await logging_utils.log_command(
            "catsummaryhydra", ctx.guild, ctx.channel, ctx.author
        )
        embed = discord_utils.create_embed()

        currcat = ctx.message.channel.category

        start_embed = discord_utils.create_embed()
        start_embed.add_field(
            name="Summary Started",
            value=f"Your summarizing of category `{currcat.name}`"
            f" has begun! This may take a while. If I run into "
            f"any errors, I'll let you know.",
            inline=False,
        )

        # Set initial message to be variable to delete after success/failure
        initial_message = (await discord_utils.send_message(ctx, start_embed))[0]

        try:
            allchans = currcat.text_channels
            messages = []
            allsheets = []

            # Group all channels sharing the same tethered sheet. Now find the right cell
            for currchan in allchans:
                result, _ = sheet_utils.findsheettether(
                    currchan.category_id, currchan.id
                )
                if result is None:
                    continue  # Silently skip channels with no tether
                curr_sheet_link = result.sheet_link
                allsheets.append((curr_sheet_link, currchan))

            all_unique_sheets = list(set([x[0] for x in allsheets]))

            for curr_sheet_link in all_unique_sheets:
                list_curr_sheet_chans = [
                    x[1] for x in allsheets if x[0] == curr_sheet_link
                ]

                list_chan_cells_overview = await hydra_sheet_utils.findchanidcell(
                    cog.gspread_client,
                    ctx,
                    curr_sheet_link,
                    [x.id for x in list_curr_sheet_chans],
                )

                if list_chan_cells_overview is None:
                    for currchan in list_curr_sheet_chans:
                        messages.append(
                            f"- {currchan.mention} - **Failed to load sheet!**"
                        )
                    continue

                overview_col = sheets_constants.NOTES_COLUMN
                _, sample_overview, sample_values = next(
                    (t for t in list_chan_cells_overview if t[1] is not None),
                    (None, None, None),
                )

                if sample_overview is None or sample_values is None:
                    continue  # Silently skip if no valid overview found

                _, col_idx = gspread.utils.a1_to_rowcol(overview_col + "1")
                for i in range(len(list_curr_sheet_chans)):
                    currchan = list_curr_sheet_chans[i]
                    rownum, overview, overview_values = list_chan_cells_overview[i]
                    if rownum is None or overview is None:
                        continue  # Silently skip again

                    # Safe get overview values
                    try:
                        overview_desc = overview_values[rownum - 1][col_idx - 1]
                    except Exception:
                        overview_desc = None
                    if overview_desc:
                        preview = (
                            overview_desc[: hydra_constants.OVERVIEW_DESC_PREVIEW]
                            + "..."
                            if len(overview_desc)
                            > hydra_constants.OVERVIEW_DESC_PREVIEW
                            else overview_desc
                        )
                        messages.append(f"- {currchan.mention} - {preview}")
                    else:
                        messages.append(f"- {currchan.mention} - *(empty description)*")
        except Exception as e:
            embed = discord_utils.create_embed()
            embed.add_field(
                name="Failed",
                value=f"An error occurred while summarizing category `{currcat.name}`. "
                f"Error: {str(e)}",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            await initial_message.delete()
            return

        if not messages:
            embed = discord_utils.create_embed()
            embed.add_field(
                name="Failed",
                value=f"No text channels found in category `{currcat.name}`.",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            await initial_message.delete()
            return

        # Split into multiple messages
        chunk_size = hydra_constants.SUMMARY_CHUNK_SIZE
        for i in range(0, len(messages), chunk_size):
            final_embed = discord_utils.create_embed()
            chunk = messages[i : i + chunk_size]

            for j, msg in enumerate(chunk):
                parts = msg.split(" - ", 1)
                channel_part = parts[0].replace("- ", "").strip()
                desc_part = parts[1].strip() if len(parts) > 1 else "\u200b"

                final_embed.add_field(name=channel_part, value=desc_part, inline=True)

                if (j + 1) % 2 == 0:
                    final_embed.add_field(name="\u200b", value="\u200b", inline=True)

            await discord_utils.send_message(ctx, final_embed)

        await initial_message.delete()
