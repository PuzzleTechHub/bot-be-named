"""
backslainhydra command - Marks puzzle as backsolved and archives it.
"""

from typing import Optional

from utils import command_predicates, logging_utils


def setup_cmd(cog):
    """Register the backslainhydra command with the bot."""

    @command_predicates.is_solver()
    @cog.bot.command(name="backslainhydra")
    async def backslainhydra(ctx, answer: Optional[str] = None):
        """Runs `~backsolvedhydra` "ANSWER" then `~mtahydra`.

        Permission Category : Solver Roles only.
        Usage: `~backslainhydra`
        Usage: `~backslainhydra ANSWER`
        Usage: `~backslainhydra "A MULTIWORD ANSWER"`
        """
        await logging_utils.log_command(
            "backslainhydra", ctx.guild, ctx.channel, ctx.author
        )

        backsolvedhydra = cog.bot.get_command("backsolvedhydra")
        mtahydra = cog.bot.get_command("mtahydra")

        await ctx.invoke(backsolvedhydra, answer=answer)
        await ctx.invoke(mtahydra)
