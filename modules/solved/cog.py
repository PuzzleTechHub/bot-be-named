import nextcord

import constants
from nextcord.ext import commands
from modules.sheets import sheets_constants
from modules.solved import solved_utils
from utils import discord_utils, logging_utils, command_predicates

# Note: It's awkward but right now the solved constants have a hyphen at the end
# Which is why we have [:-1] for all the prefixes. We don't want to have that prefix
# Sent to the users, but we do need it for prepending to the channel.

# Big thanks to denvercoder1 and his professor-vector-discord-bot repo
# https://github.com/DenverCoder1/professor-vector-discord-bot
class SolvedCog(commands.Cog):
    """Updates channel names as teams are progressing through puzzlehunts"""

    def __init__(self, bot):
        self.bot = bot

    @command_predicates.is_solver()
    @commands.command(name="solved")
    async def solved(self, ctx: commands.Context):
        """Changes channel name to solved-<channel-name>

        Permission Category : Solver Roles only.
        Usage: `~solved`

        Note that if you use more than 2 channel renaming commands quickly, Discord automatically stops any more channel-name changes for 10 more minutes. Those channels will have to be renamed manually, or wait for the full 10 mins.
        """
        status = "Solved"
        status_prefix = sheets_constants.status_dict.get(status).get("prefix_name")
        embed = await solved_utils.status_channel(ctx, status_prefix)
        await ctx.send(embed=embed)

    @command_predicates.is_solver()
    @commands.command(name="solvedish")
    async def solvedish(self, ctx: commands.Context):
        """Changes channel name to solvedish-<channel-name>

        Permission Category : Solver Roles only.
        Usage: `~solvedish`

        Note that if you use more than 2 channel renaming commands quickly, Discord automatically stops any more channel-name changes for 10 more minutes. Those channels will have to be renamed manually, or wait for the full 10 mins.
        """
        status = "Solvedish"
        status_prefix = sheets_constants.status_dict.get(status).get("prefix_name")
        embed = await solved_utils.status_channel(ctx, status_prefix)
        await ctx.send(embed=embed)

    @command_predicates.is_solver()
    @commands.command(name="backsolved")
    async def backsolved(self, ctx: commands.Context):
        """Changes channel name to backsolved-<channel-name>

        Permission Category : Solver Roles only.
        Usage: `~backsolved`

        Note that if you use more than 2 channel renaming commands quickly, Discord automatically stops any more channel-name changes for 10 more minutes. Those channels will have to be renamed manually, or wait for the full 10 mins.
        """
        status = "Backsolved"
        status_prefix = sheets_constants.status_dict.get(status).get("prefix_name")
        embed = await solved_utils.status_channel(ctx, status_prefix)
        await ctx.send(embed=embed)

    @command_predicates.is_solver()
    @commands.command(name="unsolved")
    async def unsolved(self, ctx: commands.context):
        """removes one of the solved prefixes from channel name

        Permission Category : Solver Roles only.
        Usage: `~unsolved`

        Note that if you use more than 2 channel renaming commands quickly, Discord automatically stops any more channel-name changes for 10 more minutes. Those channels will have to be renamed manually, or wait for the full 10 mins.
        """
        # log command in console
        logging_utils.log_command("unsolved", ctx.guild, ctx.channel, ctx.author)
        embed = await solved_utils.status_remove(ctx)
        await ctx.send(embed=embed)

    @command_predicates.is_solver()
    @commands.command(name="movetoarchive", aliases=["mta"])
    async def movetoarchive(self, ctx, archive_name: str = None):
        """Finds a category with `<category_name> Archive`, and moves the channel to that category.
        Fails if there is no such category, or is the category is full (i.e. 50 Channels).

        Permission Category : Solver Roles only.
        Usage: `~movetoarchive`
        Usage: `~movetoarchive archive_category_name`
        """
        logging_utils.log_command("movetoarchive", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()
        archive_category = None
        if archive_name is None:
            # Find category with same name + Archive (or select combinations)
            archive_category = (
                await discord_utils.find_category(
                    ctx, f"{ctx.channel.category.name} Archive"
                )
                or await discord_utils.find_category(
                    ctx, f"Archive: {ctx.channel.category.name}"
                )
                or await discord_utils.find_category(
                    ctx, f"{ctx.channel.category.name} archive"
                )
            )
        else:
            archive_category = await discord_utils.find_category(ctx, archive_name)

        if archive_category is None:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"There is no category named `{ctx.channel.category.name} Archive` or "
                f"`Archive: {ctx.channel.category.name}`, so I cannot move {ctx.channel.mention}.",
            )
            await ctx.send(embed=embed)
            return

        if discord_utils.category_is_full(archive_category):
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"`{archive_category}` is already full, max limit is 50 channels. Consider renaming"
                f" `{archive_category}` and creating a new `{archive_category}`.",
            )
            await ctx.send(embed=embed)
            return

        try:
            # move channel
            await ctx.channel.edit(category=archive_category)
            await ctx.channel.edit(position=1)
        except nextcord.Forbidden:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Can you check my permissions? I can't seem to be able to move "
                f"{ctx.channel.mention} to `{archive_category.name}`",
            )
            await ctx.send(embed=embed)
            return

        embed.add_field(
            name=f"{constants.SUCCESS}!",
            value=f"Moved channel {ctx.channel.mention} to `{archive_category.name}`",
        )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(SolvedCog(bot))
