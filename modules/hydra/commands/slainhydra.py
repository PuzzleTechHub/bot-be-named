"""
slainhydra command - Marks puzzle as solved and archives it.
"""

from typing import Optional

from utils import command_predicates, logging_utils


def setup_cmd(cog):
    """Register the slainhydra command with the bot."""

    @command_predicates.is_solver()
    @cog.bot.command(name="slainhydra", aliases=["donehydra"])
    async def slainhydra(ctx, answer: Optional[str] = None):
        """Runs `~solvedhydra` "ANSWER" then `~mtahydra`.

        Permission Category : Solver Roles only.
        Usage: `~slainhydra`
        Usage: `~slainhydra ANSWER`
        Usage: `~slainhydra "A MULTIWORD ANSWER"`
        """
        await logging_utils.log_command(
            "slainhydra", ctx.guild, ctx.channel, ctx.author
        )

        solvedhydra = cog.bot.get_command("solvedhydra")
        mtahydra = cog.bot.get_command("mtahydra")

        await ctx.invoke(solvedhydra, answer=answer)
        await ctx.invoke(mtahydra)
