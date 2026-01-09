"""Tests for modules/hydra/hydra_utils/old_lion_command_helpers.py"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
import gspread
from modules.hydra.hydra_utils.old_lion_command_helpers import send_solve_notification


@pytest.mark.asyncio
class TestSendSolveNotification:
    """Test suite for send_solve_notification function."""

    async def test_no_stream_env_no_action(self, mock_bot, mock_ctx, monkeypatch):
        """Test that function returns early when TM_BOT_STREAM_CHANNEL_ID is not set."""
        # Unset the environment variable
        monkeypatch.delenv("TM_BOT_STREAM_CHANNEL_ID", raising=False)
        
        # Call the function
        await send_solve_notification(mock_bot, mock_ctx, "TEST")
        
        # Verify bot.get_channel was never called
        mock_bot.get_channel.assert_not_called()

    async def test_stream_channel_not_found_no_action(self, mock_bot, mock_ctx, monkeypatch):
        """Test that function returns early when get_channel returns None."""
        monkeypatch.setenv("TM_BOT_STREAM_CHANNEL_ID", "123456")
        
        # Make get_channel return None
        mock_bot.get_channel.return_value = None
        
        with patch("modules.hydra.hydra_utils.old_lion_command_helpers.google_utils") as mock_google_utils:
            await send_solve_notification(mock_bot, mock_ctx, "TEST")
            
            # Verify google_utils was never accessed
            mock_google_utils.create_gspread_client.assert_not_called()

    async def test_big_board_missing_columns_counts_zero_first_solve_message(
        self, mock_bot, mock_ctx, mock_channel, monkeypatch
    ):
        """Test that missing big board config results in 'FIRST PUZZLE SOLVED' message."""
        monkeypatch.setenv("TM_BOT_STREAM_CHANNEL_ID", "123456")
        # Don't set TM_BIG_BOARD_URL or TM_BIG_BOARD_STATUS_COLUMN
        monkeypatch.delenv("TM_BIG_BOARD_URL", raising=False)
        monkeypatch.delenv("TM_BIG_BOARD_STATUS_COLUMN", raising=False)
        
        stream_channel = mock_channel
        mock_bot.get_channel.return_value = stream_channel
        
        with patch("modules.hydra.hydra_utils.old_lion_command_helpers.discord_utils") as mock_discord_utils:
            mock_embed = MagicMock()
            mock_embed.add_field = MagicMock()
            mock_discord_utils.create_embed.return_value = mock_embed
            
            await send_solve_notification(mock_bot, mock_ctx, "ANSWER")
            
            # Verify channel.send was called
            stream_channel.send.assert_called_once()
            
            # Verify embed has "FIRST PUZZLE SOLVED" message
            mock_embed.add_field.assert_called_once()
            call_args = mock_embed.add_field.call_args
            assert "FIRST PUZZLE SOLVED" in call_args[1]["name"]

    async def test_big_board_gspread_api_error_treated_as_zero(
        self, mock_bot, mock_ctx, mock_channel, monkeypatch
    ):
        """Test that gspread APIError is caught and treated as zero solves."""
        monkeypatch.setenv("TM_BOT_STREAM_CHANNEL_ID", "123456")
        monkeypatch.setenv("TM_BIG_BOARD_URL", "https://docs.google.com/spreadsheets/d/test")
        monkeypatch.setenv("TM_BIG_BOARD_STATUS_COLUMN", "D")
        
        stream_channel = mock_channel
        mock_bot.get_channel.return_value = stream_channel
        
        with patch("modules.hydra.hydra_utils.old_lion_command_helpers.google_utils") as mock_google_utils, \
             patch("modules.hydra.hydra_utils.old_lion_command_helpers.discord_utils") as mock_discord_utils:
            
            # Make gspread raise an exception
            mock_google_utils.create_gspread_client.side_effect = Exception("API Error")
            
            mock_embed = MagicMock()
            mock_embed.add_field = MagicMock()
            mock_discord_utils.create_embed.return_value = mock_embed
            
            await send_solve_notification(mock_bot, mock_ctx, "TEST")
            
            # Verify "FIRST PUZZLE SOLVED" (count = 0) message is sent
            call_args = mock_embed.add_field.call_args
            assert "FIRST PUZZLE SOLVED" in call_args[1]["name"]

    async def test_counts_and_ordinal_suffix_single(
        self, mock_bot, mock_ctx, mock_channel, mock_gspread_client, monkeypatch
    ):
        """Test counting logic with 1 solve shows '1st'."""
        monkeypatch.setenv("TM_BOT_STREAM_CHANNEL_ID", "123456")
        monkeypatch.setenv("TM_BIG_BOARD_URL", "https://docs.google.com/spreadsheets/d/test")
        monkeypatch.setenv("TM_BIG_BOARD_STATUS_COLUMN", "C")
        
        stream_channel = mock_channel
        mock_bot.get_channel.return_value = stream_channel
        
        # Mock big board data with 1 solved puzzle
        mock_gspread_client.open_by_url.return_value.sheet1.get_all_values.return_value = [
            ["Puzzle 1", "Description", "Solved"],
        ]
        
        with patch("modules.hydra.hydra_utils.old_lion_command_helpers.google_utils") as mock_google_utils, \
             patch("modules.hydra.hydra_utils.old_lion_command_helpers.discord_utils") as mock_discord_utils:
            
            mock_google_utils.create_gspread_client.return_value = mock_gspread_client
            
            mock_embed = MagicMock()
            mock_embed.add_field = MagicMock()
            mock_discord_utils.create_embed.return_value = mock_embed
            
            await send_solve_notification(mock_bot, mock_ctx, "ANSWER")
            
            # Verify "1st" appears in the message
            call_args = mock_embed.add_field.call_args
            assert "1st" in call_args[1]["value"]

    async def test_counts_and_ordinal_suffix_teens(
        self, mock_bot, mock_ctx, mock_channel, mock_gspread_client, monkeypatch
    ):
        """Test counting logic with 11 solves shows '11th' (not '11st')."""
        monkeypatch.setenv("TM_BOT_STREAM_CHANNEL_ID", "123456")
        monkeypatch.setenv("TM_BIG_BOARD_URL", "https://docs.google.com/spreadsheets/d/test")
        monkeypatch.setenv("TM_BIG_BOARD_STATUS_COLUMN", "C")
        
        stream_channel = mock_channel
        mock_bot.get_channel.return_value = stream_channel
        
        # Mock big board data with 11 solved puzzles
        mock_data = [[f"Puzzle {i}", "Description", "Solved"] for i in range(1, 12)]
        mock_gspread_client.open_by_url.return_value.sheet1.get_all_values.return_value = mock_data
        
        with patch("modules.hydra.hydra_utils.old_lion_command_helpers.google_utils") as mock_google_utils, \
             patch("modules.hydra.hydra_utils.old_lion_command_helpers.discord_utils") as mock_discord_utils:
            
            mock_google_utils.create_gspread_client.return_value = mock_gspread_client
            
            mock_embed = MagicMock()
            mock_embed.add_field = MagicMock()
            mock_discord_utils.create_embed.return_value = mock_embed
            
            await send_solve_notification(mock_bot, mock_ctx, "TEST")
            
            # Verify "11th" appears (special case for teen numbers)
            call_args = mock_embed.add_field.call_args
            assert "11th" in call_args[1]["value"]

    async def test_answer_masking_and_uppercase(
        self, mock_bot, mock_ctx, mock_channel, monkeypatch
    ):
        """Test that answer is uppercased and spoiler-wrapped."""
        monkeypatch.setenv("TM_BOT_STREAM_CHANNEL_ID", "123456")
        monkeypatch.delenv("TM_BIG_BOARD_URL", raising=False)
        
        stream_channel = mock_channel
        mock_bot.get_channel.return_value = stream_channel
        
        with patch("modules.hydra.hydra_utils.old_lion_command_helpers.discord_utils") as mock_discord_utils:
            mock_embed = MagicMock()
            mock_embed.add_field = MagicMock()
            mock_discord_utils.create_embed.return_value = mock_embed
            
            await send_solve_notification(mock_bot, mock_ctx, "abc123")
            
            # Verify answer is uppercased and spoiler-wrapped
            call_args = mock_embed.add_field.call_args
            assert "||ABC123||" in call_args[1]["value"]

    async def test_non_integer_stream_env_silently_ignored(
        self, mock_bot, mock_ctx, monkeypatch
    ):
        """Test that non-integer channel ID is handled gracefully."""
        monkeypatch.setenv("TM_BOT_STREAM_CHANNEL_ID", "not-a-number")
        
        # Should not raise an exception
        await send_solve_notification(mock_bot, mock_ctx, "TEST")

    async def test_exception_in_send_silently_ignored(
        self, mock_bot, mock_ctx, mock_channel, monkeypatch
    ):
        """Test that exceptions during send are silently caught."""
        monkeypatch.setenv("TM_BOT_STREAM_CHANNEL_ID", "123456")
        
        stream_channel = mock_channel
        stream_channel.send = AsyncMock(side_effect=Exception("Send failed"))
        mock_bot.get_channel.return_value = stream_channel
        
        with patch("modules.hydra.hydra_utils.old_lion_command_helpers.discord_utils") as mock_discord_utils:
            mock_embed = MagicMock()
            mock_discord_utils.create_embed.return_value = mock_embed
            
            # Should not raise an exception
            await send_solve_notification(mock_bot, mock_ctx, "TEST")

    async def test_counts_multiple_rows_counting_logic(
        self, mock_bot, mock_ctx, mock_channel, mock_gspread_client, monkeypatch
    ):
        """Test that only 'Solved' and 'Backsolved' statuses are counted."""
        monkeypatch.setenv("TM_BOT_STREAM_CHANNEL_ID", "123456")
        monkeypatch.setenv("TM_BIG_BOARD_URL", "https://docs.google.com/spreadsheets/d/test")
        monkeypatch.setenv("TM_BIG_BOARD_STATUS_COLUMN", "C")
        
        stream_channel = mock_channel
        mock_bot.get_channel.return_value = stream_channel
        
        # Mock big board with mixed statuses
        mock_gspread_client.open_by_url.return_value.sheet1.get_all_values.return_value = [
            ["Puzzle 1", "Description", "Solved"],
            ["Puzzle 2", "Description", "Backsolved"],
            ["Puzzle 3", "Description", "In Progress"],
            ["Puzzle 4", "Description", "Not Started"],
            ["Puzzle 5", "Description", "Solved"],
        ]
        
        with patch("modules.hydra.hydra_utils.old_lion_command_helpers.google_utils") as mock_google_utils, \
             patch("modules.hydra.hydra_utils.old_lion_command_helpers.discord_utils") as mock_discord_utils:
            
            mock_google_utils.create_gspread_client.return_value = mock_gspread_client
            
            mock_embed = MagicMock()
            mock_embed.add_field = MagicMock()
            mock_discord_utils.create_embed.return_value = mock_embed
            
            await send_solve_notification(mock_bot, mock_ctx, "TEST")
            
            # Should count 3 (2 Solved + 1 Backsolved)
            call_args = mock_embed.add_field.call_args
            assert "3rd" in call_args[1]["value"]

    async def test_integration_with_get_ordinal_suffix_various(
        self, mock_bot, mock_ctx, mock_channel, mock_gspread_client, monkeypatch
    ):
        """Test various ordinal suffixes through integration."""
        monkeypatch.setenv("TM_BOT_STREAM_CHANNEL_ID", "123456")
        monkeypatch.setenv("TM_BIG_BOARD_URL", "https://docs.google.com/spreadsheets/d/test")
        monkeypatch.setenv("TM_BIG_BOARD_STATUS_COLUMN", "C")
        
        stream_channel = mock_channel
        mock_bot.get_channel.return_value = stream_channel
        
        test_cases = [
            (2, "2nd"),
            (3, "3rd"),
            (4, "4th"),
            (21, "21st"),
            (22, "22nd"),
            (23, "23rd"),
        ]
        
        for count, expected_suffix in test_cases:
            # Reset mock
            stream_channel.send.reset_mock()
            
            # Create mock data with specific count
            mock_data = [[f"Puzzle {i}", "Desc", "Solved"] for i in range(1, count + 1)]
            mock_gspread_client.open_by_url.return_value.sheet1.get_all_values.return_value = mock_data
            
            with patch("modules.hydra.hydra_utils.old_lion_command_helpers.google_utils") as mock_google_utils, \
                 patch("modules.hydra.hydra_utils.old_lion_command_helpers.discord_utils") as mock_discord_utils:
                
                mock_google_utils.create_gspread_client.return_value = mock_gspread_client
                
                mock_embed = MagicMock()
                mock_embed.add_field = MagicMock()
                mock_discord_utils.create_embed.return_value = mock_embed
                
                await send_solve_notification(mock_bot, mock_ctx, "TEST")
                
                call_args = mock_embed.add_field.call_args
                assert expected_suffix in call_args[1]["value"], f"Expected {expected_suffix} for count {count}"

    async def test_no_answer_produces_placeholder(
        self, mock_bot, mock_ctx, mock_channel, monkeypatch
    ):
        """Test that None answer produces placeholder text."""
        monkeypatch.setenv("TM_BOT_STREAM_CHANNEL_ID", "123456")
        monkeypatch.delenv("TM_BIG_BOARD_URL", raising=False)
        
        stream_channel = mock_channel
        mock_bot.get_channel.return_value = stream_channel
        
        with patch("modules.hydra.hydra_utils.old_lion_command_helpers.discord_utils") as mock_discord_utils:
            mock_embed = MagicMock()
            mock_embed.add_field = MagicMock()
            mock_discord_utils.create_embed.return_value = mock_embed
            
            await send_solve_notification(mock_bot, mock_ctx, None)
            
            # Verify placeholder appears
            call_args = mock_embed.add_field.call_args
            assert "*(no answer provided)*" in call_args[1]["value"]
