from discord.ext import commands

from modules.help import help_command


# Dont forget to shoutout my guy Jonah Lawrence aka DenverCoder1
# As this module was copied (with minimal modification)
# from his repo https://github.com/DenverCoder1/weasley-chess-bot
class HelpCog(commands.Cog, name="Help"):
    """Help"""
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
