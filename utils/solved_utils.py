import nextcord
import constants
from nextcord.ext import commands
from utils import sheets_constants
from utils import discord_utils

"""
Solved Utils. Used to edit "solved states" from discord channels etc. Allows us to deduplicate code when trying to edit channel names etc.
Used in any modules that combine solving and discord (solved, lion, hydra...)
"""


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
            p = Prefix(channel, other_prefix)
            if p.has_prefix():
                new_channel_name = p.remove_prefix()
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
            await ctx.channel.edit(name=new_channel_name)
        except nextcord.Forbidden:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Unable to prepend `{status_prefix}` to {ctx.channel.mention}. Do I have the `manage_channels` permissions?",
            )
            await ctx.send(embed=embed)
            return
        embed.add_field(
            name=f"{constants.SUCCESS}!",
            value=f"Marking {ctx.channel.mention} as {status_prefix}!",
            inline=False,
        )
    else:
        embed.add_field(
            name=f"{constants.FAILED}!",
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
            await channel.edit(name=new_channel_name)
            embed.add_field(
                name=f"{constants.SUCCESS}!",
                value=f"Marking {channel.mention} as un-{prefix}!",
                inline=False,
            )
            return embed
    embed.add_field(
        name=f"{constants.FAILED}!",
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
