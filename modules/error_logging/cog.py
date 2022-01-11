from discord.ext import commands
from modules.error_logging.error_handling import ErrorHandler
from modules.error_logging import error_constants
from utils import discord_utils, logging_utils
import sys
import os


# Big thanks to denvercoder1 and his professor-vector-discord-bot repo
# https://github.com/DenverCoder1/professor-vector-discord-bot
class ErrorLogCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="errorlog")
    @commands.is_owner()
    async def errorlog(self, ctx, num_lines: int = 50):
        """Shows errors in reverse chronological order

        Category : Bot Owner Only.
        Usage: `~errorlog`
        """
        logging_utils.log_command("errorlog", ctx.guild, ctx.channel, ctx.author)
        if not os.path.exists(error_constants.ERROR_LOGFILE):
            embed = discord_utils.create_embed()
            embed.add_field(
                name="Error!",
                value=f"Is this an error? Is it a blessing in disguise? I don't know, but there have been "
                f"no errors since I've last started!",
            )
            await ctx.send(embed=embed)
            return

        with open(error_constants.ERROR_LOGFILE, "r") as f:
            lines = f.readlines()
            last_n_lines = "".join(lines[-num_lines:])
            # Trim the length of the log messages
            if len(last_n_lines) > 1990:
                last_n_lines = f"...\n{last_n_lines[-1990:]}"
            await ctx.send(f"```{last_n_lines}```")


async def on_error(event, *args, **kwargs):
    """When an exception is raised, log it in err.log and bot log channel"""
    print(f"Printing from on_error: {args[0]}")
    _, error, _ = sys.exc_info()
    embed = discord_utils.create_embed()
    # error while handling message
    if event in [
        "message",
        "on_message",
        "message_discarded",
        "on_message_discarded",
        "on_command_error",
    ]:
        msg = f"**Error while handling a message**"
        user_error = ErrorHandler(args[0], error, msg).handle_error()
        if user_error:
            embed.add_field(name="Error!", value=user_error, inline=False)
    # other errors
    else:
        msg = f"An error occurred during an event and was not reported: {event}"
        user_error = ErrorHandler(
            args[0], error, msg
        ).handle_error()  # TODO: change args[0] to ""
        if user_error:
            embed = discord_utils.create_embed()
            embed.add_field(name="Error!", value=user_error, inline=False)
    await args[0].channel.send(embed=embed)


async def on_command_error(ctx, error):
    """When a command exception is raised, log it in err.log and bot log channel"""
    details = f"**Error while running command**\n'''\n{ctx.message.clean_content}\n'''"
    user_error = ErrorHandler(ctx.message, error, details).handle_error()
    if user_error:
        embed = discord_utils.create_embed()
        embed.add_field(name="Error!", value=user_error, inline=False)
        await ctx.send(embed=embed)
    else:
        print("on_command_error has no user_error")


def setup(bot):
    bot.add_cog(ErrorLogCog(bot))
    bot.on_error = on_error
    bot.on_command_error = on_command_error
