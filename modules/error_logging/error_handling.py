import sys
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
        traceback.print_exception(
            type(self.error), self.error, self.error.__traceback__, file=sys.stderr
        )

    def handle_error(self):
        """Send error to user and error log channel"""
        error_details = self.trace if self.trace != "NoneType: None\n" else self.error
        print(f"In handle_error")
        logging.warning(error_details)
        print(f"Printing from handle_error: {error_details}")
        self.__log_to_file(error_constants.ERROR_LOGFILE, error_details)
        user_error = self.__user_error_message()
        if user_error == -1:  # No error from __user_error_message
            return error_details
        else:
            return user_error

    def __user_error_message(self) -> str:
        if isinstance(self.error, errors.CommandNotFound):
            return None  # ignore command not found
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
        elif isinstance(self.error, errors.CheckFailure):
            return (
                f"You do not have the required perms to use this command. Please speak with a server "
                "admin to get verified."
            )
        elif isinstance(self.error, errors.MissingAnyRole):
            # Get the missing role list.
            # We need to convert the role IDs to strings for the people to understand
            # It might be a channel specific role, so in that case it would come back as none
            # We don't want to add none (for the join later on)
            # If it's a string, just append it
            missing_role_list = []
            print(self.error.missing_roles)
            for missing_role in self.error.missing_roles:
                role = self.message.guild.get_role(missing_role)
                if role is not None:
                    missing_role_list.append(role.name)
            # Send all possible perms to give them access to the command
            if len(missing_role_list) >= 1:
                return (
                    f"You must have one of the following roles to use this command: "
                    f"{', '.join(missing_role_list)}"
                )
            # This would happen if the perm is not available in that server.
            else:
                return (
                    f"You don't have the necessary permissions to use that command! Speak with kevslinger to "
                    f"get your permissions set up for that."
                )
        #elif isinstance(self.error, errors.HTTPException):
        #    return f"Some HTTPException (We don't know what's going on)"
        else:
            return -1  # No Error found

    def __log_to_file(self, filename: str, text: str):
        """Appends the error to the error log file"""
        with open(filename, "a") as f:
            f.write(f"[ {datetime.now().strftime('%m-%d-%Y, %H:%M:%S')} ] {text}\n\n")
            traceback.print_exception(
                type(self.error), self.error, self.error.__traceback__, file=f
            )
