import traceback
from discord import logging
from discord.ext.commands import errors
from modules.error_logging import error_constants
from datetime import datetime


# Big thanks to denvercoder1 and his professor-vector-discord-bot repo
# https://github.com/DenverCoder1/professor-vector-discord-bot
class ErrorHandler:
    """Handles errors, sends a message to user and to Error channel"""
    def __init__(self, message, error, human_readable_msg):
        self.message = message
        self.error = error
        self.human_readable_msg = human_readable_msg
        # Formats the error as traceback
        self.trace = traceback.format_exc()


    def handle_error(self):
        """Send error to user and error log channel"""
        error_details = self.trace if self.trace != "NoneType: None\n" else self.error
        logging.warning(error_details)
        self.__log_to_file(error_constants.ERROR_LOGFILE, error_details)

        return self.__user_error_message()


    def __user_error_message(self):
        if isinstance(self.error, errors.CommandNotFound):
            pass  # ignore command not found
        elif isinstance(self.error, errors.MissingRequiredArgument):
            return f"Argument {self.error.param} required."
        elif isinstance(self.error, errors.TooManyArguments):
            return f"Too many arguments given."
        elif isinstance(self.error, errors.BadArgument):
            return f"Bad argument: {self.error}"
        elif isinstance(self.error, errors.NoPrivateMessage):
            return f"That command cannot be used in DMs."
        elif isinstance(self.error, errors.MissingPermissions):
            return (
                "You are missing the following permissions required to run the"
                f' command: {", ".join(self.error.missing_perms)}.'
            )
        elif isinstance(self.error, errors.DisabledCommand):
            return f"That command is disabled or under maintenance."
        elif isinstance(self.error, errors.CommandInvokeError):
            return f"Error while executing the command."
        elif isinstance(self.error, errors.MissingAnyRole): #TODO: need MissingAnyRole?
            if len(self.error.missing_roles) > 1:
                return f"You must have one of the following roles to use this command: " \
                       f"{', '.join(self.error.missing_roles)}"
            else:
                return f"You must have the {self.error.missing_roles[0]} role to use this command."
        else:
            return None

    def __log_to_file(self, filename: str, text: str):
        """Appends the error to the error log file"""
        with open(filename, "a") as f:
            f.write(f"[ {datetime.now().strftime('%m-%d-%Y, %H:%M:%S')} ] {text}\n\n")
