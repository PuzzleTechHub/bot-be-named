from typing import Optional

import emoji
import gspread
import nextcord
from nextcord.ext import commands
from utils import sheets_constants
from utils import discord_utils
from utils import batch_update_utils
from utils import sheet_utils

"""
Solved Utils. Used to edit "solved states" from discord channels etc. Allows us to deduplicate code when trying to edit channel names etc.
Used in any modules that combine solving and discord (solved, lion, hydra...)
"""


def get_status_info(status: str) -> dict:
    """The status_dict entry for a status. Custom statuses use the "None" entry."""
    status_info = sheets_constants.status_dict.get(status)
    if status_info is None:
        status_info = sheets_constants.status_dict.get("None")
    return status_info


def is_solve_status(status: str) -> bool:
    """Whether a status counts as a solve (Solved, Backsolved, Postsolved)."""
    return sheet_utils.normalize_status(status) in sheets_constants.solve_statuses


def answer_cell_value(status_info: dict, answer: Optional[str]) -> Optional[str]:
    """Returns what to write in the puzzle tab's answer cell, or None to leave it. Statuses that don't take an answer clear it."""
    if not status_info.get("update_ans"):
        return ""
    if answer is not None:
        return answer.upper()
    return None


def solved_time_value(
    prev_status: str, new_status: str, has_solved_time: bool, now: str
) -> Optional[str]:
    """What to write in the Overview's solved timestamp cell.
    Non-solve to solve sets the time. Solve to non-solve clears it.
    Going between solves (e.g. Solved -> Backsolved) keeps the original time,
    and going between non-solves clears any leftover time."""
    was_solve = is_solve_status(prev_status)
    is_solve = is_solve_status(new_status)
    if is_solve and not was_solve:
        return now
    if not is_solve and has_solved_time:
        return ""
    return None


async def update_puzzle_status(
    ctx: commands.Context,
    overview_sheet,
    row_to_find: int,
    status: str,
    answer: Optional[str] = None,
) -> bool:
    """Sets a puzzle's status, i.e., the answer on its tab, the status on the Overview,
    the tab colour, then the channel prefix. Sends the result to ctx.

    Returns False if the sheet couldn't be updated."""
    status = sheet_utils.normalize_status(status)
    status_info = get_status_info(status)
    embed = discord_utils.create_embed()

    try:
        status_col = overview_sheet.get_cell_value(
            sheets_constants.STATUS_COLUMN_LOCATION
        )

        tab_ans_loc = sheets_constants.TAB_ANSWER_LOCATION
        tab_cell_label = sheets_constants.SHEET_TAB_ID_COLUMN + str(row_to_find)
        tab_id = overview_sheet.get_cell_value(tab_cell_label)
        puzzle_tab = overview_sheet.spreadsheet.get_worksheet_by_id(int(tab_id))

        batch_update_builder = batch_update_utils.BatchUpdateBuilder()

        new_answer = answer_cell_value(status_info, answer)
        if new_answer is not None:
            batch_update_builder.update_cell_by_label(
                puzzle_tab.id, tab_ans_loc, new_answer
            )

        curr_status = overview_sheet.get_cell_value(status_col + str(row_to_find))
        curr_stat_info = get_status_info(curr_status)

        batch_update_builder.update_cell_by_label(
            overview_sheet.worksheet.id, status_col + str(row_to_find), status
        )

        color = status_info.get("color")
        batch_update_builder.color_update(tab_id, color)

        # An API error here (permission denied included) goes to the except
        # at the bottom. On failure the channel is not renamed.
        overview_sheet.worksheet.spreadsheet.batch_update(batch_update_builder.build())

        embed.add_field(
            name="Success",
            value="The sheet was successfully updated.",
            inline=False,
        )

        add_prefix = status_info.get("prefix")
        past_prefix = curr_stat_info.get("prefix")

        if status == curr_status:
            embed.add_field(
                name="Note",
                value=f"The puzzle status was already set to `{status}`. No changes were made to the channel name.",
                inline=False,
            )
            await ctx.message.add_reaction(emoji.emojize(":check_mark_button:"))
            await discord_utils.send_message(ctx, embed)
            return True

        new_embed = None
        if past_prefix and not add_prefix:
            new_embed = await status_remove(ctx)
        if add_prefix:
            new_embed = await status_channel(ctx, status_info.get("prefix_name"))
        # status_channel returns None when it has already sent its own error
        if new_embed is not None:
            embed = discord_utils.merge_embed(embed, new_embed)

        await ctx.message.add_reaction(emoji.emojize(":check_mark_button:"))
        await discord_utils.send_message(ctx, embed)
        return True

    except gspread.exceptions.APIError as e:
        await sheet_utils.handle_gspread_error(ctx, e)
        return False


def add_prefix(channel, prefix: str):
    """Adds prefix to channel name"""
    # create prefix checking object
    p = Prefix(channel, prefix)
    new_channel_name = None
    # check if already solved
    if not p.has_prefix():
        # Abusing p notation here
        # Remove other prefixes that might be present
        # e.g. ~backsolved on solved-channel should remove solved- and add backsolved-
        for other_prefix in [
            op for op in sheets_constants.solved_prefixes if op + "-" != prefix
        ]:
            p = Prefix(channel, other_prefix + "-")
            if p.has_prefix():
                new_channel_name = p.remove_prefix()
                break
        if new_channel_name is None:
            p = Prefix(channel, prefix)
        else:
            p = Prefix(new_channel_name, prefix)
        new_channel_name = p.add_prefix()
    return new_channel_name


def remove_prefix(channel, prefix: str) -> str:
    """Remove prefix from channel name"""
    # create prefix checking object
    p = Prefix(channel, prefix)
    new_channel_name = None
    # check if already solved
    if p.has_prefix():
        # edit channel name to remove prefix
        new_channel_name = p.remove_prefix()
    return new_channel_name


async def status_channel(ctx: commands.Context, status_prefix):
    embed = discord_utils.create_embed()
    new_channel_name = add_prefix(ctx.channel, status_prefix + "-")
    if new_channel_name:
        try:
            await discord_utils.rename_channel(ctx.channel, new_channel_name)
        except nextcord.Forbidden:
            await discord_utils.send_failure(
                ctx,
                f"Unable to prepend `{status_prefix}` to {ctx.channel.mention}. Do I have the `manage_channels` permissions?",
            )
            return
        embed.add_field(
            name="Success",
            value=f"Marking {ctx.channel.mention} as {status_prefix}!",
            inline=False,
        )
    else:
        embed.add_field(
            name="Failed",
            value=f"Channel already marked as {status_prefix}!",
            inline=False,
        )
    return embed


async def status_remove(ctx: commands.Context):
    embed = discord_utils.create_embed()
    channel = ctx.message.channel
    prefixes = sheets_constants.solved_prefixes
    for prefix in prefixes:
        new_channel_name = remove_prefix(ctx.message.channel, prefix + "-")
        if new_channel_name:
            await discord_utils.rename_channel(channel, new_channel_name)
            embed.add_field(
                name="Success",
                value=f"Marking {channel.mention} as un-{prefix}!",
                inline=False,
            )
            return embed
    embed.add_field(
        name="Failed",
        value=f"Channel is not marked as `{' / '.join(prefixes)}`!",
        inline=False,
    )
    return embed


class Prefix:
    """
    Class Prefix. Used for assigning set "prefixes" to Discord channel names and navigating them
    Used in Lion and Hydra modules
    """

    def __init__(self, original: str, prefix: str):
        self.original = str(original)
        self.prefix_str = str(prefix)
        self.prefix_len = len(self.prefix_str)

    def has_prefix(self):
        return self.original[: self.prefix_len] == self.prefix_str

    def add_prefix(self):
        return f"{self.prefix_str}{self.original}"

    def remove_prefix(self):
        return self.original[self.prefix_len :]
