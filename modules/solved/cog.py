import discord

import constants
from discord.ext import commands
from modules.solved.prefix import Prefix
from modules.solved import solved_constants
from utils import discord_utils, logging_utils, admin_utils


# TODO: It's awkward but right now the solved constants have a hyphen at the end
# Which is why we have [:-1] for all the prefixes. We don't want to have that prefix
# Sent to the users, but we do need it for prepending to the channel.
# Big thanks to denvercoder1 and his professor-vector-discord-bot repo
# https://github.com/DenverCoder1/professor-vector-discord-bot
class SolvedCog(commands.Cog):
    """Checks for `solved` and `unsolved` command
    Toggles `solved-` prefix on channel name"""
    def __init__(self, bot):
        self.bot = bot

    def add_prefix(self, channel, prefix: str):
        """Adds prefix to channel name"""
        # create prefix checking object
        p = Prefix(channel, prefix)
        new_channel_name = None
        # check if already solved
        if not p.has_prefix():
            # Abusing p notation here
            # Remove other prefixes that might be present
            # e.g. ~backsolved on solved-channel should remove solved- and add backsolved-
            for other_prefix in [op for op in solved_constants.PREFIXES if op != prefix]:
                p = Prefix(channel, other_prefix)
                if p.has_prefix():
                    new_channel_name = p.remove_prefix()
            if new_channel_name is None:
                p = Prefix(channel, prefix)
            else:
                p = Prefix(new_channel_name, prefix)
            new_channel_name = p.add_prefix()
        return new_channel_name

    def remove_prefix(self, channel, prefix: str) -> str:
        """Remove prefix from channel name"""
        # create prefix checking object
        p = Prefix(channel, prefix)
        new_channel_name = None
        # check if already solved
        if p.has_prefix():
            # edit channel name to remove prefix
            new_channel_name = p.remove_prefix()
        return new_channel_name

    @commands.command(name="solved")
    @commands.has_any_role(*constants.VERIFIED)
    async def solved(self, ctx: commands.Context):
        """Changes channel name to solved-<channel-name>

        Usage: ~solved"""
        # log command in console
        logging_utils.log_command("solved", ctx.channel, ctx.author)
        channel = ctx.message.channel
        embed = discord_utils.create_embed()
        new_channel_name = self.add_prefix(channel, solved_constants.SOLVED_PREFIX)
        if new_channel_name:
            await channel.edit(name=new_channel_name)
            embed.add_field(name=f"{constants.SUCCESS}!",
                            value=f"Marking {channel.mention} as {solved_constants.SOLVED_PREFIX[:-1]}!",
                            inline=False)
        else:
            embed.add_field(name=f"{constants.FAILED}!",
                            value=f"Channel already marked as {solved_constants.SOLVED_PREFIX[:-1]}!",
                            inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="solvedish")
    @commands.has_any_role(*constants.VERIFIED)
    async def solvedish(self, ctx: commands.Context):
        """Changes channel name to solvedish-<channel-name>

        Usage: ~solvedish"""
        # log command in console
        logging_utils.log_command("solvedish", ctx.channel, ctx.author)
        channel = ctx.message.channel
        embed = discord_utils.create_embed()
        new_channel_name = self.add_prefix(ctx.message.channel, solved_constants.SOLVEDISH_PREFIX)
        if new_channel_name:
            await channel.edit(name=new_channel_name)
            embed.add_field(name=f"{constants.SUCCESS}!",
                            value=f"Marking {channel.mention} as {solved_constants.SOLVEDISH_PREFIX[:-1]}!",
                            inline=False)
        else:
            embed.add_field(name=f"{constants.FAILED}!",
                            value=f"Channel already marked as {solved_constants.SOLVEDISH_PREFIX[:-1]}!",
                            inline=False)
        await channel.edit(name=new_channel_name)
        await ctx.send(embed=embed)

    @commands.command(name="backsolved")
    @commands.has_any_role(*constants.VERIFIED)
    async def backsolved(self, ctx: commands.Context):
        """Changes channel name to backsolved-<channel-name>

        Usage: ~backsolved"""
        # log command in console
        logging_utils.log_command("backsolved", ctx.channel, ctx.author)
        channel = ctx.message.channel
        embed = discord_utils.create_embed()
        new_channel_name = self.add_prefix(channel, solved_constants.BACKSOLVED_PREFIX)
        if new_channel_name:
            await channel.edit(name=new_channel_name)
            embed.add_field(name=f"{constants.SUCCESS}",
                            value=f"Marking {channel.mention} as {solved_constants.BACKSOLVED_PREFIX[:-1]}!",
                            inline=False)
        else:
            embed.add_field(name=f"{constants.FAILED}",
                            value=f"Channel already marked as {solved_constants.BACKSOLVED_PREFIX[:-1]}!",
                            inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="unsolved")
    @commands.has_any_role(*constants.VERIFIED)
    async def unsolved(self, ctx: commands.context):
        """removes one of the solved prefixes from channel name

        Usage: ~unsolved"""
        # log command in console
        logging_utils.log_command("unsolved", ctx.channel, ctx.author)
        channel = ctx.message.channel
        embed = discord_utils.create_embed()
        for prefix in solved_constants.PREFIXES:
            new_channel_name = self.remove_prefix(ctx.message.channel, prefix)
            if new_channel_name:
                await channel.edit(name=new_channel_name)
                embed.add_field(name=f"{constants.SUCCESS}!",
                                value=f"Marking {channel.mention} as un{prefix[:-1]}!",
                                inline=False)
                await ctx.send(embed=embed)
                return
        embed.add_field(name=f"{constants.FAILED}!",
                        value=f"Channel is not marked as {solved_constants.SOLVED_PREFIX[:-1]}!",
                        inline=False)
        await ctx.send(embed=embed)

    # TODO: move to some utils file somewhere. This function can be very useful and generalized to fit more needs
    def sort_channels(self, channel_list: list) -> list:
        """Sort channels according to unsolved, solvedish, backsolved, solved"""
        channel_list_sorted = sorted(channel_list, key=lambda x: x.name)

        solvedish = list(filter(lambda x: x.name.startswith(solved_constants.SOLVEDISH_PREFIX), channel_list_sorted))
        backsolved = list(filter(lambda x: x.name.startswith(solved_constants.BACKSOLVED_PREFIX), channel_list_sorted))
        solved = list(filter(lambda x: x.name.startswith(solved_constants.SOLVED_PREFIX), channel_list_sorted))
        unsolved = list(filter(lambda x: x not in solved and x not in backsolved and x not in solvedish, channel_list_sorted))

        return unsolved + solvedish + backsolved + solved

    @admin_utils.is_owner_or_admin()
    @commands.command(name="reorderchannels")
    async def reorderchannels(self, ctx):
        """Reorder channels within a category, in order of unsolved, solvedish, backsolved, solved
        and alphabetical order within each of those"""
        logging_utils.log_command("reorderchannels", ctx.channel, ctx.author)
        category = ctx.channel.category
        text_channels = category.text_channels

        channel_order = self.sort_channels(text_channels)
        for position, channel in enumerate(channel_order):
            try:
                await channel.edit(position=position)
            except discord.Forbidden:
                embed = discord_utils.create_embed()
                embed.add_field(name=f"{constants.FAILED}!",
                                value="I do not have permission to reorder the channels.")
                await ctx.send(embed=embed)
                return

        embed = discord_utils.create_embed()
        embed.add_field(name=f"{constants.SUCCESS}!",
                        value="Channels sorted successfully")
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(SolvedCog(bot))
