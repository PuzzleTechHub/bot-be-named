import sys
from discord.ext import commands
from modules.error_logging.error_handling import ErrorHandler
from utils import discord_utils
from modules.error_logging import error_constants

## Big thanks to denvercoder1 and his professor-vector-discord-bot repo
## https://github.com/DenverCoder1/professor-vector-discord-bot
class ErrorLogCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.error_channel = self.bot.get_channel(error_constants.ERROR_LOG_CHANNEL_ID)

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
            embed.add_field(name="Error!",
                            value=user_error,
                            inline=False)
    # other errors
    else:
        msg = f"An error occurred during and event and was not reported: {event}"
        user_error = ErrorHandler(args[0], error, msg).handle_error()# TODO: change args[0] to ""
        if user_error:
            embed = discord_utils.create_embed()
            embed.add_field(name="Error!",
                            value=user_error,
                            inline=False)
    await args[0].channel.send(embed=embed)
    #await error_channel.send(embed=embed)

async def on_command_error(ctx, error):
    """When a command exception is raised, log it in err.log and bot log channel"""
    print(f"Printing from on_command_error: {error}")
    details = f"**Error while running command**\n'''\n{ctx.message.clean_content}\n'''"
    user_error = ErrorHandler(ctx.message, error, details).handle_error()
    if user_error:
        embed = discord_utils.create_embed()
        embed.add_field(name="Error!",
                        value=user_error,
                        inline=False)
        await ctx.send(embed=embed)
    else:
        print("None")


def setup(bot):
    bot.add_cog(ErrorLogCog(bot))
    bot.on_error = on_error
    bot.on_command_error = on_command_error