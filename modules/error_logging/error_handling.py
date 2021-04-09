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
        elif isinstance(self.error, errors.MissingAnyRole):
            # Get the missing role list. Some may be integers (role IDs)
            # Others might be strings TODO: only use one or the other?
            # If it's an int, we want to convert to a string for the people to understand
            # It might be a channel specific role, so in that case it would come back as none
            # We don't want to add none (for the join later on)
            # If it's a string, just append it
            missing_role_list = []
            for missing_role in self.error.missing_roles:
                if isinstance(missing_role, int):
                    role = self.message.guild.get_role(missing_role)
                    if role is not None:
                        missing_role_list.append(role)
                else:
                    missing_role_list.append(missing_role)
            # Some integers might have the same role name so just remove duplicates
            missing_role_list = set(missing_role_list)
            # Send all possible perms to give them access to the command
            if len(missing_role_list) > 1:
                return f"You must have one of the following roles to use this command: " \
                       f"{', '.join(missing_role_list)}"
            # This would happen if the perm is not available in that server.
            elif len(missing_role_list) <= 0:
                return f"You don't have the necessary permissions to use that command! Speak with kevslinger to " \
                       f"get your permissions set up for that."
            else:
                # One role for the command.
                return f"You must have the {next(iter(missing_role_list))} role to use this command."
        else:
            return None

    def __log_to_file(self, filename: str, text: str):
        """Appends the error to the error log file"""
        with open(filename, "a") as f:
            f.write(f"[ {datetime.now().strftime('%m-%d-%Y, %H:%M:%S')} ] {text}\n\n")
