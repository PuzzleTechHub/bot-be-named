import discord

import constants
from discord.ext import commands
from modules.solved.prefix import Prefix
from modules.solved import solved_constants
from utils import discord_utils, logging_utils, command_predicates

# TODO: It's awkward but right now the solved constants have a hyphen at the end
# Which is why we have [:-1] for all the prefixes. We don't want to have that prefix
# Sent to the users, but we do need it for prepending to the channel.

# Big thanks to denvercoder1 and his professor-vector-discord-bot repo
# https://github.com/DenverCoder1/professor-vector-discord-bot
class SolvedCog(commands.Cog):
    """Updates channel names as teams are progressing through puzzlehunts"""
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

    @command_predicates.is_verified()
    @commands.command(name="solved")
    async def solved(self, ctx: commands.Context):
        """Changes channel name to solved-<channel-name>

        Category : Verified Roles only.
        Usage: `~solved`
        """
        # log command in console
        logging_utils.log_command("solved", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        new_channel_name = self.add_prefix(ctx.channel, solved_constants.SOLVED_PREFIX)
        if new_channel_name:
            try:
                await ctx.channel.edit(name=new_channel_name)
            except discord.Forbidden:
                embed.add_field(name=f"{constants.FAILED}!",
                                value=f"Unable to prepend `solved` to {ctx.channel.mention}. Do I have the `manage_channels` permissions?")
                await ctx.send(embed=embed)
                return
            embed.add_field(name=f"{constants.SUCCESS}!",
                            value=f"Marking {ctx.channel.mention} as {solved_constants.SOLVED_PREFIX[:-1]}!",
                            inline=False)
        else:
            embed.add_field(name=f"{constants.FAILED}!",
                            value=f"Channel already marked as {solved_constants.SOLVED_PREFIX[:-1]}!",
                            inline=False)
        await ctx.send(embed=embed)

    @command_predicates.is_verified()
    @commands.command(name="solvedish")
    async def solvedish(self, ctx: commands.Context):
        """Changes channel name to solvedish-<channel-name>

        Category : Verified Roles only.
        Usage: `~solvedish`
        """
        # log command in console
        logging_utils.log_command("solvedish", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        channel = ctx.message.channel
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

    @command_predicates.is_verified()
    @commands.command(name="backsolved")
    async def backsolved(self, ctx: commands.Context):
        """Changes channel name to backsolved-<channel-name>

        Category : Verified Roles only.
        Usage: `~backsolved`
        """
        # log command in console
        logging_utils.log_command("backsolved", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        channel = ctx.message.channel
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

    @command_predicates.is_verified()
    @commands.command(name="unsolved")
    async def unsolved(self, ctx: commands.context):
        """removes one of the solved prefixes from channel name

        Category : Verified Roles only.
        Usage: `~unsolved`
        """
        # log command in console
        logging_utils.log_command("unsolved", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        channel = ctx.message.channel
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

    @command_predicates.is_verified()
    @commands.command(name="movetoarchive", aliases=["mta"])
    async def movetoarchive(self, ctx):
        """Finds a category with `<category_name> Archive`, and moves the channel to that category. 
        Fails if there is no such category, or is the category is full (i.e. 50 Channels).

        Category : Verified Roles only.
        Usage: `~movetoarchive`
        """
        logging_utils.log_command("movetoarchive", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        # Find category with same name + Archive (or select combinations)
        archive_category = await discord_utils.find_category(ctx, f"{ctx.channel.category.name} Archive") or \
                           await discord_utils.find_category(ctx, f"Archive: {ctx.channel.category.name}") or \
                           await discord_utils.find_category(ctx, f"{ctx.channel.category.name} archive")

        if archive_category is None:
            embed.add_field(name=f"{constants.FAILED}!",
                            value=f"There is no category named `{ctx.channel.category.name} Archive` or "
                                  f"`Archive: {ctx.channel.category.name}`, so I cannot move {ctx.channel.mention}.")
            await ctx.send(embed=embed)
            return

        if discord_utils.category_is_full(archive_category):
            embed.add_field(name=f"{constants.FAILED}!",
                            value=f"`{archive_category}` is already full, max limit is 50 channels. Consider renaming"
                                  f" `{archive_category}` and creating a new `{archive_category}`.")
            await ctx.send(embed=embed)
            return

        try:
            # move channel
            await ctx.channel.edit(category=archive_category)
            await ctx.channel.edit(position=1)
        except discord.Forbidden:
            embed.add_field(name=f"{constants.FAILED}!",
                            value=f"Can you check my permissions? I can't seem to be able to move "
                                  f"{ctx.channel.mention} to `{archive_category.name}`")
            await ctx.send(embed=embed)
            return

        embed.add_field(name=f"{constants.SUCCESS}!",
                        value=f"Moved channel {ctx.channel.mention} to `{archive_category.name}`")
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(SolvedCog(bot))
