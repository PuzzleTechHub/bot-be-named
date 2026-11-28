import sys
import traceback

from nextcord import logging
from nextcord.ext.commands import errors

from modules.error_logging import error_constants
from modules.help import help_command
from utils import logging_utils


# Big thanks to denvercoder1 and his professor-vector-discord-bot repo
# https://github.com/DenverCoder1/professor-vector-discord-bot
class ErrorHandler:
    """Handles errors, sends a message to user and to Error channel"""

    def __init__(self, message, error, human_readable_msg, ctx=None):
        self.message = message
        self.error = error
        self.human_readable_msg = human_readable_msg
        # Only set for command errors
        self.ctx = ctx

        # Formats the error as traceback
        self.trace = traceback.format_exc()
        traceback.print_exception(
            type(self.error), self.error, self.error.__traceback__, file=sys.stderr
        )

    def handle_error(self):
        """Log the error to the error log, and return the message for the user (None for no message)"""
        error_details = self.trace if self.trace != "NoneType: None\n" else self.error
        print("In handle_error")
        logging.warning(error_details)
        print(f"Printing from handle_error: {error_details}")

        logging_utils.log_to_file(error_constants.ERROR_LOGFILE, error_details)

        exceptions = "".join(
            traceback.format_exception(
                type(self.error), self.error, self.error.__traceback__
            )
        )
        print(exceptions)

        return self.__user_error_message()

    def __command_name(self) -> str | None:
        """The command as the user would type it, e.g. "~addperm", or None outside a command."""
        if self.ctx is None or self.ctx.command is None:
            return None
        return f"{self.ctx.clean_prefix}{self.ctx.command.qualified_name}"

    def __shows_usage(self) -> bool:
        """Input mistakes get the command's Usage lines and a pointer to its help page."""
        return self.__command_name() is not None and isinstance(
            self.error, errors.UserInputError
        )

    def __who_can_use(self) -> str | None:
        """Who can use the command, for a permission failure on one of our checks."""
        if self.__command_name() is None or not isinstance(
            self.error, errors.CheckFailure
        ):
            return None
        if isinstance(self.error, (errors.NoPrivateMessage, errors.MissingPermissions)):
            return None
        return help_command.who_can_use(self.ctx.command, self.ctx.clean_prefix)

    def add_details(self, embed):
        """Adds the same Usage and Required permission(s) fields as the command's ~help page."""
        prefix = self.ctx.clean_prefix if self.ctx is not None else ""
        if self.__shows_usage():
            help_command.add_usage_field(embed, self.ctx.command, prefix)
            embed.add_field(
                name="More help",
                value=f"`{prefix}help {self.ctx.command.qualified_name}`",
                inline=False,
            )
        who = self.__who_can_use()
        if who is not None:
            embed.add_field(name=help_command.PERMISSION_FIELD, value=who, inline=False)

    def __permission_message(self) -> str:
        if self.__who_can_use() is None:
            return (
                "You do not have the required perms to use this command. Please speak with a server "
                "admin to get the relevant role."
            )
        return (
            f"You can't use `{self.__command_name()}`. "
            "Please speak with a server admin if you need access."
        )

    def __user_error_message(self) -> str | None:
        if isinstance(self.error, errors.CommandNotFound):
            return None  # ignore command not found
        elif isinstance(self.error, errors.MissingRequiredArgument):
            return f"Missing `{self.error.param.name}`."
        elif isinstance(self.error, errors.TooManyArguments):
            return "Too many arguments given."
        elif isinstance(self.error, errors.BadArgument):
            return f"Bad argument: {self.error}"
        elif isinstance(self.error, errors.UserInputError):
            # Other input mistakes
            return str(self.error)
        elif isinstance(self.error, errors.NoPrivateMessage):
            return "That command cannot be used in DMs."
        elif isinstance(self.error, errors.MissingPermissions):
            return (
                "You are missing the following permissions required to run the"
                f" command: {', '.join(self.error.missing_permissions)}."
            )
        elif isinstance(self.error, errors.DisabledCommand):
            return "That command is disabled or under maintenance."
        elif isinstance(self.error, errors.CheckFailure):
            return self.__permission_message()
        name = self.__command_name()
        where = f" while running `{name}`" if name else ""
        # The details go to the error log (see ~errorlog), not the channel
        return f"Something went wrong{where}. The error has been logged."
