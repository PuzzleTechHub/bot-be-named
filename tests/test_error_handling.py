"""Error responses can be tested without connecting a Discord client."""

import contextlib
import io
import unittest
from unittest.mock import patch

from nextcord.ext.commands import errors

from modules.error_logging.error_handling import ErrorHandler


class ErrorHandlerTests(unittest.TestCase):
    def handle(self, error):
        with (
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
            patch("modules.error_logging.error_handling.logging.warning"),
            patch("modules.error_logging.error_handling.logging_utils.log_to_file"),
        ):
            return ErrorHandler(None, error, None).handle_error()

    def test_missing_permissions_lists_the_required_permissions(self):
        for permissions in (["manage_messages"], ["manage_messages", "manage_roles"]):
            with self.subTest(permissions=permissions):
                self.assertEqual(
                    self.handle(errors.MissingPermissions(permissions)),
                    "You are missing the following permissions required to run the"
                    f" command: {', '.join(permissions)}.",
                )

    def test_generic_check_failure_keeps_its_message(self):
        self.assertEqual(
            self.handle(errors.CheckFailure()),
            "You do not have the required perms to use this command. Please speak with a server "
            "admin to get the relevant role.",
        )

    def test_unknown_command_is_ignored(self):
        self.assertIsNone(self.handle(errors.CommandNotFound("unknown")))


if __name__ == "__main__":
    unittest.main()
