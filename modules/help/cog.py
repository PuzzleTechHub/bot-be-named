from nextcord.ext import commands
from modules.help import help_command


class HelpCog(commands.Cog, name="Help"):
    """
    Help module.
    Manages a `~help` command which auto-populates a list of all commands from the codebase in other cogs.
    Also manages a customised `~help commandname` command which gets autopopulated from individual function comments.
    (This is why you write good documentation yall!)

    Code copied/adapted from DenverCoder1's Weasley-Chess-Bot repo - https://github.com/DenverCoder1/weasley-chess-bot
    """

    def __init__(self, bot: commands.Bot):
        self._original_help_command = bot.help_command
        self.bot = bot
        self.bot.help_command = help_command.HelpCommand()
        self.bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self._original_help_command


# setup functions for bot
def setup(bot: commands.Bot):
    bot.add_cog(HelpCog(bot))
