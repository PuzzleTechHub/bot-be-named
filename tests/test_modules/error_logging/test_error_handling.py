import inspect
from types import SimpleNamespace

import nextcord
from nextcord.ext import commands
from nextcord.ext.commands import errors

from modules.error_logging.error_handling import ErrorHandler
from tests.fakes import check_embed
from utils import command_predicates


def test_missing_permissions_message_lists_the_permissions():
    error = errors.MissingPermissions(["manage_channels", "manage_roles"])
    message = ErrorHandler(None, error, None).handle_error()
    assert message == (
        "You are missing the following permissions required to run the"
        " command: manage_channels, manage_roles."
    )


async def _addperm(ctx, role_permissions: str, *args):
    """Add a permission.

    Permission Category : Admin or Bot Owner only.
    Usage: `~addperm Verified @VerifiedRoleName`
    Usage: `~addperm Trusted @everyone`
    """


async def _ping(ctx, target: str):
    """No usage lines here."""


def _ctx(callback, checks=(), prefix="~"):
    command = commands.Command(callback, name=callback.__name__.lstrip("_"))
    for check in checks:
        command = check(command)
    return SimpleNamespace(command=command, clean_prefix=prefix)


def _handled(error, ctx=None):
    """The message for the user, and the embed on_command_error would send."""
    handler = ErrorHandler(None, error, None, ctx)
    message = handler.handle_error()
    embed = nextcord.Embed(description="")
    embed.add_field(name="Error!", value=message, inline=False)
    handler.add_details(embed)
    check_embed(embed)
    return message, {field.name: field.value for field in embed.fields}


def _missing(name):
    return errors.MissingRequiredArgument(
        inspect.Parameter(name, inspect.Parameter.POSITIONAL_OR_KEYWORD)
    )


def test_missing_argument_adds_the_help_page_usage_and_a_help_pointer():
    message, fields = _handled(_missing("role_permissions"), _ctx(_addperm))
    assert message == "Missing `role_permissions`."
    assert fields["Usage"] == (
        "`~addperm Verified @VerifiedRoleName`\n`~addperm Trusted @everyone`"
    )
    assert fields["More help"] == "`~help addperm`"


def test_missing_argument_falls_back_to_signature_with_server_prefix():
    _, fields = _handled(_missing("target"), _ctx(_ping, prefix="!"))
    assert fields["Usage"] == "`!ping <target>`"
    assert fields["More help"] == "`!help ping`"


def test_bad_argument_and_quote_errors_get_usage():
    ctx = _ctx(_ping)
    message, fields = _handled(errors.BadArgument("Channel not found."), ctx)
    assert message == "Bad argument: Channel not found."
    assert "Usage" in fields
    message, fields = _handled(errors.ExpectedClosingQuoteError('"'), ctx)
    assert message.startswith("Expected closing")
    assert fields["More help"] == "`~help ping`"


def test_input_errors_without_a_command_have_only_the_message():
    message, fields = _handled(_missing("target"))
    assert message == "Missing `target`."
    assert list(fields) == ["Error!"]


def test_check_failure_says_who_can_use_it():
    ctx = _ctx(_addperm, checks=[command_predicates.is_bot_owner_or_admin()])
    message, fields = _handled(errors.CheckFailure(), ctx)
    assert message == (
        "You can't use `~addperm`. Please speak with a server admin if you need access."
    )
    assert fields["Required permission(s)"] == (
        "Admin or Bot Owner: Server admins, or whoever runs the bot."
    )
    assert "Usage" not in fields


def test_check_failure_without_a_known_category_keeps_the_old_text():
    unknown = commands.check(lambda ctx: False)
    for ctx in (None, _ctx(_ping, checks=[unknown])):
        message, fields = _handled(errors.CheckFailure(), ctx)
        assert message.startswith(
            "You do not have the required perms to use this command."
        )
        assert list(fields) == ["Error!"]


def test_dm_and_discord_permission_failures_add_no_fields():
    ctx = _ctx(_addperm, checks=[command_predicates.is_admin()])
    for error in (errors.NoPrivateMessage(), errors.MissingPermissions(["ban"])):
        _, fields = _handled(error, ctx)
        assert list(fields) == ["Error!"]


def test_command_crash_says_it_was_logged_not_the_details():
    error = commands.CommandInvokeError(RuntimeError("secret token abc"))
    message, fields = _handled(error, _ctx(_ping))
    assert message == (
        "Something went wrong while running `~ping`. The error has been logged."
    )
    assert list(fields) == ["Error!"]


def test_unknown_error_no_longer_returns_the_traceback():
    message = ErrorHandler(None, RuntimeError("secret token abc"), None).handle_error()
    assert message == "Something went wrong. The error has been logged."


def test_command_not_found_stays_silent():
    assert (
        ErrorHandler(None, errors.CommandNotFound("nope"), None).handle_error() is None
    )
