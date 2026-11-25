from nextcord.ext.commands import errors

from modules.error_logging.error_handling import ErrorHandler


def test_missing_permissions_message_lists_the_permissions():
    error = errors.MissingPermissions(["manage_channels", "manage_roles"])
    message = ErrorHandler(None, error, None).handle_error()
    assert message == (
        "You are missing the following permissions required to run the"
        " command: manage_channels, manage_roles."
    )
