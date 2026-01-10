"""Shared pytest fixtures for bot testing."""

import pytest
from unittest.mock import AsyncMock, MagicMock
import sys
import nextcord

database_mock = MagicMock()
sys.modules["database"] = database_mock
sys.modules["database.models"] = database_mock
sys.modules["database.database_utils"] = database_mock


@pytest.fixture
def mock_bot():
    """Create a mock bot instance with basic functionality."""
    bot = MagicMock()
    bot.user = MagicMock()
    bot.user.name = "TestBot"
    bot.user.id = 123456789

    # Mock get_channel to return a mock channel by default
    mock_channel = MagicMock()
    mock_channel.send = AsyncMock()
    mock_channel.id = 987654321
    mock_channel.name = "test-channel"
    mock_channel.mention = "<#987654321>"

    bot.get_channel = MagicMock(return_value=mock_channel)

    return bot


@pytest.fixture
def mock_channel():
    """Create a mock Discord channel."""
    channel = MagicMock()
    channel.id = 111222333
    channel.name = "test-channel"
    channel.mention = "<#111222333>"
    channel.send = AsyncMock()
    channel.guild = MagicMock()
    channel.guild.id = 444555666
    channel.category = MagicMock()
    channel.category.name = "Test Category"
    return channel


@pytest.fixture
def mock_message():
    """Create a mock Discord message."""
    message = MagicMock()
    message.id = 777888999
    message.content = "test message"
    message.author = MagicMock()
    message.author.id = 111111111
    message.author.name = "TestUser"
    message.add_reaction = AsyncMock()
    return message


@pytest.fixture
def mock_ctx(mock_channel, mock_message):
    """Create a mock command context."""
    ctx = MagicMock()
    ctx.channel = mock_channel
    ctx.message = mock_message
    ctx.author = mock_message.author
    ctx.guild = mock_channel.guild
    ctx.send = AsyncMock()
    return ctx


@pytest.fixture
def mock_gspread_client():
    """Create a mock gspread client with spreadsheet and worksheet mocks."""
    client = MagicMock()

    # Create mock spreadsheet
    spreadsheet = MagicMock()
    spreadsheet.title = "Test Spreadsheet"

    # Create mock worksheet (sheet1)
    worksheet = MagicMock()
    worksheet.title = "Sheet1"
    worksheet.get_all_values = MagicMock(return_value=[])
    worksheet.get = MagicMock(return_value=[])
    worksheet.update = MagicMock()
    worksheet.batch_update = MagicMock()

    spreadsheet.sheet1 = worksheet
    spreadsheet.worksheet = MagicMock(return_value=worksheet)
    spreadsheet.get_worksheet = MagicMock(return_value=worksheet)

    client.open_by_url = MagicMock(return_value=spreadsheet)
    client.open = MagicMock(return_value=spreadsheet)

    return client


@pytest.fixture
def mock_embed():
    """Create a mock Discord embed."""
    embed = MagicMock(spec=nextcord.Embed)
    embed.fields = []
    embed.add_field = MagicMock(
        side_effect=lambda name, value, inline=False: embed.fields.append(
            {"name": name, "value": value, "inline": inline}
        )
    )
    embed.title = None
    embed.description = None
    embed.color = None
    return embed
