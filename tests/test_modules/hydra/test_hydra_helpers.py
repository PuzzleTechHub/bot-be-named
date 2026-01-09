"""Tests for modules/hydra/hydra_utils/hydra_helpers.py"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import gspread
import nextcord
from modules.hydra.hydra_utils.hydra_helpers import (
    handle_gspread_error,
    create_success_embed,
    create_failure_embed,
    send_and_react_success,
    get_ordinal_suffix,
)


class TestGetOrdinalSuffix:
    """Test suite for get_ordinal_suffix function."""

    def test_first(self):
        """Test 1st."""
        assert get_ordinal_suffix(1) == "st"

    def test_second(self):
        """Test 2nd."""
        assert get_ordinal_suffix(2) == "nd"

    def test_third(self):
        """Test 3rd."""
        assert get_ordinal_suffix(3) == "rd"

    def test_fourth_through_tenth(self):
        """Test 4th through 10th."""
        for n in range(4, 11):
            assert get_ordinal_suffix(n) == "th", f"Expected 'th' for {n}"

    def test_eleventh_special_case(self):
        """Test 11th (special case - not 11st)."""
        assert get_ordinal_suffix(11) == "th"

    def test_twelfth_special_case(self):
        """Test 12th (special case - not 12nd)."""
        assert get_ordinal_suffix(12) == "th"

    def test_thirteenth_special_case(self):
        """Test 13th (special case - not 13rd)."""
        assert get_ordinal_suffix(13) == "th"

    def test_twenty_first(self):
        """Test 21st."""
        assert get_ordinal_suffix(21) == "st"

    def test_twenty_second(self):
        """Test 22nd."""
        assert get_ordinal_suffix(22) == "nd"

    def test_twenty_third(self):
        """Test 23rd."""
        assert get_ordinal_suffix(23) == "rd"

    def test_twenty_fourth(self):
        """Test 24th."""
        assert get_ordinal_suffix(24) == "th"

    def test_one_hundred_eleventh(self):
        """Test 111th (special case in hundreds)."""
        assert get_ordinal_suffix(111) == "th"

    def test_one_hundred_twenty_first(self):
        """Test 121st."""
        assert get_ordinal_suffix(121) == "st"

    def test_large_numbers(self):
        """Test large numbers maintain correct suffix."""
        assert get_ordinal_suffix(1001) == "st"
        assert get_ordinal_suffix(1002) == "nd"
        assert get_ordinal_suffix(1003) == "rd"
        assert get_ordinal_suffix(1011) == "th"


class TestCreateSuccessEmbed:
    """Test suite for create_success_embed function."""

    def test_creates_embed_with_success_field(self):
        """Test that success embed is created with correct structure."""
        with patch(
            "modules.hydra.hydra_utils.hydra_helpers.discord_utils"
        ) as mock_discord_utils:
            mock_embed = MagicMock()
            mock_embed.fields = []
            mock_discord_utils.create_embed.return_value = mock_embed

            result = create_success_embed("Operation completed")

            # Verify create_embed was called
            mock_discord_utils.create_embed.assert_called_once()

            # Verify add_field was called with correct parameters
            mock_embed.add_field.assert_called_once_with(
                name="Success",
                value="Operation completed",
                inline=False,
            )

    def test_message_content_preserved(self):
        """Test that the message content is preserved exactly."""
        with patch(
            "modules.hydra.hydra_utils.hydra_helpers.discord_utils"
        ) as mock_discord_utils:
            mock_embed = MagicMock()
            mock_discord_utils.create_embed.return_value = mock_embed

            test_message = "This is a test with **formatting** and ||spoilers||"
            create_success_embed(test_message)

            call_args = mock_embed.add_field.call_args
            assert call_args[1]["value"] == test_message


class TestCreateFailureEmbed:
    """Test suite for create_failure_embed function."""

    def test_creates_embed_with_failed_field(self):
        """Test that failure embed is created with correct structure."""
        with patch(
            "modules.hydra.hydra_utils.hydra_helpers.discord_utils"
        ) as mock_discord_utils:
            mock_embed = MagicMock()
            mock_embed.fields = []
            mock_discord_utils.create_embed.return_value = mock_embed

            result = create_failure_embed("Operation failed")

            # Verify create_embed was called
            mock_discord_utils.create_embed.assert_called_once()

            # Verify add_field was called with correct parameters
            mock_embed.add_field.assert_called_once_with(
                name="Failed",
                value="Operation failed",
                inline=False,
            )

    def test_message_content_preserved(self):
        """Test that the message content is preserved exactly."""
        with patch(
            "modules.hydra.hydra_utils.hydra_helpers.discord_utils"
        ) as mock_discord_utils:
            mock_embed = MagicMock()
            mock_discord_utils.create_embed.return_value = mock_embed

            test_message = "Error: something went wrong!"
            create_failure_embed(test_message)

            call_args = mock_embed.add_field.call_args
            assert call_args[1]["value"] == test_message


@pytest.mark.asyncio
class TestSendAndReactSuccess:
    """Test suite for send_and_react_success function."""

    async def test_adds_reaction_and_sends_message(self, mock_ctx):
        """Test that reaction is added and message is sent."""
        mock_embed = MagicMock()

        with patch(
            "modules.hydra.hydra_utils.hydra_helpers.emoji"
        ) as mock_emoji, patch(
            "modules.hydra.hydra_utils.hydra_helpers.discord_utils"
        ) as mock_discord_utils:

            mock_emoji.emojize.return_value = "✅"
            mock_discord_utils.send_message = AsyncMock()

            await send_and_react_success(mock_ctx, mock_embed)

            # Verify emoji was emojized
            mock_emoji.emojize.assert_called_once_with(":check_mark_button:")

            # Verify reaction was added
            mock_ctx.message.add_reaction.assert_called_once_with("✅")

            # Verify message was sent
            mock_discord_utils.send_message.assert_called_once_with(
                mock_ctx, mock_embed
            )

    async def test_custom_reaction(self, mock_ctx):
        """Test that custom reaction emoji can be specified."""
        mock_embed = MagicMock()

        with patch(
            "modules.hydra.hydra_utils.hydra_helpers.emoji"
        ) as mock_emoji, patch(
            "modules.hydra.hydra_utils.hydra_helpers.discord_utils"
        ) as mock_discord_utils:

            mock_emoji.emojize.return_value = "✅"
            mock_discord_utils.send_message = AsyncMock()

            await send_and_react_success(
                mock_ctx, mock_embed, reaction=":check_mark_button:"
            )

            # Verify custom emoji was used
            mock_emoji.emojize.assert_called_once_with(":check_mark_button:")
            mock_ctx.message.add_reaction.assert_called_once_with("✅")


@pytest.mark.asyncio
class TestHandleGspreadError:
    """Test suite for handle_gspread_error function."""

    async def test_permission_denied_error(self, mock_ctx):
        """Test handling of PERMISSION_DENIED error."""
        # Create mock APIError
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": {
                "code": 403,
                "status": "PERMISSION_DENIED",
                "message": "Permission denied",
            }
        }

        error = gspread.exceptions.APIError(mock_response)

        with patch(
            "modules.hydra.hydra_utils.hydra_helpers.discord_utils"
        ) as mock_discord_utils:
            mock_embed = MagicMock()
            mock_discord_utils.create_embed.return_value = mock_embed
            mock_discord_utils.send_message = AsyncMock()

            result = await handle_gspread_error(mock_ctx, error)

            # Verify permission denied message was added
            mock_embed.add_field.assert_called_once()
            call_args = mock_embed.add_field.call_args
            assert call_args[1]["name"] == "Failed"
            assert "permission was denied" in call_args[1]["value"]

            # Verify message was sent
            mock_discord_utils.send_message.assert_called_once_with(
                mock_ctx, mock_embed
            )

    async def test_unknown_error(self, mock_ctx):
        """Test handling of unknown GSheets API error."""
        # Create mock APIError with unknown status
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": {
                "code": 500,
                "status": "UNKNOWN_ERROR",
                "message": "Something went wrong",
            }
        }

        error = gspread.exceptions.APIError(mock_response)

        with patch(
            "modules.hydra.hydra_utils.hydra_helpers.discord_utils"
        ) as mock_discord_utils:
            mock_embed = MagicMock()
            mock_discord_utils.create_embed.return_value = mock_embed
            mock_discord_utils.send_message = AsyncMock()

            result = await handle_gspread_error(mock_ctx, error)

            # Verify unknown error message was added
            call_args = mock_embed.add_field.call_args
            assert "Unknown GSheets API Error" in call_args[1]["value"]
            assert "Something went wrong" in call_args[1]["value"]

    async def test_uses_provided_embed(self, mock_ctx):
        """Test that provided embed is used instead of creating new one."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": {"code": 403, "status": "PERMISSION_DENIED", "message": "Test"}
        }

        error = gspread.exceptions.APIError(mock_response)
        provided_embed = MagicMock()

        with patch(
            "modules.hydra.hydra_utils.hydra_helpers.discord_utils"
        ) as mock_discord_utils:
            mock_discord_utils.send_message = AsyncMock()

            result = await handle_gspread_error(mock_ctx, error, embed=provided_embed)

            # Verify create_embed was NOT called
            mock_discord_utils.create_embed.assert_not_called()

            # Verify the provided embed was used
            provided_embed.add_field.assert_called_once()

            # Verify message was sent with provided embed
            mock_discord_utils.send_message.assert_called_once_with(
                mock_ctx, provided_embed
            )

    async def test_returns_embed(self, mock_ctx):
        """Test that the function returns the embed."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": {"code": 403, "status": "PERMISSION_DENIED", "message": "Test"}
        }

        error = gspread.exceptions.APIError(mock_response)

        with patch(
            "modules.hydra.hydra_utils.hydra_helpers.discord_utils"
        ) as mock_discord_utils:
            mock_embed = MagicMock()
            mock_discord_utils.create_embed.return_value = mock_embed
            mock_discord_utils.send_message = AsyncMock()

            result = await handle_gspread_error(mock_ctx, error)

            assert result == mock_embed
