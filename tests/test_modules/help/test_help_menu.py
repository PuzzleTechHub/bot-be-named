"""Tests for the interactive ~help menu"""

import importlib
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import nextcord
import pytest
from nextcord.ext import commands

from modules.help import help_command
from tests.fakes import check_embed
from utils import google_utils

COG_MODULES = sorted(
    f"modules.{path.parent.name}.cog"
    for path in (Path(__file__).parents[3] / "modules").glob("*/cog.py")
)
AUTHOR_ID = 1000


class FakeDestination:
    def __init__(self):
        self.sent = []

    async def send(self, embed=None, view=None):
        check_embed(embed)
        message = SimpleNamespace(embed=embed, view=view, edits=[])

        async def edit(**kwargs):
            message.edits.append(kwargs)

        message.edit = edit
        self.sent.append(message)
        return message


class FakeResponse:
    def __init__(self):
        self.edited = []
        self.messages = []

    async def edit_message(self, embed=None, view=None):
        check_embed(embed)
        self.edited.append(embed)

    async def send_message(self, content, ephemeral=False):
        self.messages.append((content, ephemeral))


def interaction(user_id=AUTHOR_ID):
    return SimpleNamespace(user=SimpleNamespace(id=user_id), response=FakeResponse())


@pytest.fixture
def helper(monkeypatch):
    """A HelpCommand over all real cogs, ignoring permission checks."""
    monkeypatch.setattr(google_utils, "create_gspread_client", MagicMock())
    monkeypatch.setattr(google_utils, "get_gdrive_credentials", MagicMock())
    intents = nextcord.Intents.default()
    intents.message_content = True
    intents.members = True
    bot = commands.Bot(command_prefix="~", intents=intents, help_command=None)
    for name in COG_MODULES:
        importlib.import_module(name).setup(bot)
    helper = help_command.HelpCommand(verify_checks=False)
    helper.cog = bot.get_cog("Help")
    helper.context = SimpleNamespace(
        bot=SimpleNamespace(
            cogs=bot.cogs,
            commands=bot.commands,
            description=None,
            user=SimpleNamespace(
                name="Bot Be Named",
                display_avatar=SimpleNamespace(url="https://example.com/a.png"),
            ),
            get_cog=bot.get_cog,
            get_command=bot.get_command,
        ),
        author=SimpleNamespace(id=AUTHOR_ID),
        channel=FakeDestination(),
        clean_prefix="~",
        command=None,
        guild=None,
    )
    return helper


async def test_every_page_is_a_valid_embed(helper):
    pages = await helper.help_pages()
    names = [name for name, _ in pages]
    assert names[0] is None
    for _, embed in pages:
        check_embed(embed)
    for cog in helper.context.bot.cogs.values():
        if cog.get_commands():
            assert cog.qualified_name in names


async def test_big_module_is_split_into_pages(helper):
    hydra = helper.context.bot.get_cog("Hydra")
    pages = [embed for name, embed in await helper.help_pages() if name == "Hydra"]
    assert len(pages) > 1
    assert all(len(embed.fields) <= help_command.COMMANDS_PER_PAGE for embed in pages)
    assert sum(len(embed.fields) for embed in pages) == len(hydra.get_commands())
    assert pages[0].title == f"Hydra Commands (1/{len(pages)})"


async def test_help_sends_public_menu_on_overview(helper):
    await helper.send_bot_help(helper.get_bot_mapping())
    [message] = helper.context.channel.sent
    view = message.view
    assert isinstance(view, help_command.HelpMenu)
    assert message.embed.title == "Bot Commands"
    assert message.embed.footer.text.startswith(f"Page 1/{len(view.pages)}")
    assert view.previous_button.disabled
    assert not view.next_button.disabled
    assert len(view.module_select.options) <= help_command.MAX_SELECT_OPTIONS


async def test_every_control_has_a_custom_id(helper):
    """Discord refuses a message whose buttons or dropdown lack a custom_id."""
    view = help_command.HelpMenu(AUTHOR_ID, await helper.help_pages())
    components = [
        component for row in view.to_components() for component in row["components"]
    ]
    assert len(components) == 3
    for component in components:
        assert isinstance(component.get("custom_id"), str)
        assert component["custom_id"]


async def test_cog_help_opens_menu_at_that_module(helper):
    await helper.send_cog_help(helper.context.bot.get_cog("Hydra"))
    [message] = helper.context.channel.sent
    assert message.embed.title.startswith("Hydra Commands (1/")
    assert message.view.pages[message.view.index][0] == "Hydra"


async def test_buttons_step_through_pages(helper):
    pages = await helper.help_pages()
    view = help_command.HelpMenu(AUTHOR_ID, pages)
    press = interaction()
    await view.next_page(press)
    assert view.index == 1
    assert press.response.edited == [pages[1][1]]
    assert not view.previous_button.disabled
    await view.previous_page(interaction())
    assert view.index == 0
    assert view.previous_button.disabled

    view.index = len(pages) - 2
    await view.next_page(interaction())
    assert view.next_button.disabled
    await view.next_page(interaction())
    assert view.index == len(pages) - 1


async def test_dropdown_jumps_to_first_page_of_module(helper):
    pages = await helper.help_pages()
    view = help_command.HelpMenu(AUTHOR_ID, pages)
    view.module_select._selected_values = ["Hydra"]
    await view.select_module(interaction())
    assert pages[view.index][0] == "Hydra"
    assert pages[view.index - 1][0] != "Hydra"

    view.module_select._selected_values = ["Overview"]
    await view.select_module(interaction())
    assert view.index == 0


async def test_only_the_caller_can_use_the_menu(helper):
    view = help_command.HelpMenu(AUTHOR_ID, await helper.help_pages())
    assert await view.interaction_check(interaction(AUTHOR_ID))
    other = interaction(AUTHOR_ID + 1)
    assert not await view.interaction_check(other)
    [(content, ephemeral)] = other.response.messages
    assert ephemeral
    assert "Only the person who ran" in content


async def test_timeout_disables_controls(helper):
    await helper.send_bot_help(helper.get_bot_mapping())
    [message] = helper.context.channel.sent
    await message.view.on_timeout()
    assert all(item.disabled for item in message.view.children)
    assert message.edits == [{"view": message.view}]


async def test_command_help_shows_module_aliases_and_usage(helper):
    command = next(
        c for c in helper.context.bot.commands if c.aliases and c.cog is not None
    )
    await helper.send_command_help(command)
    [message] = helper.context.channel.sent
    fields = {field.name: field.value for field in message.embed.fields}
    assert fields["Module"] == command.cog.qualified_name
    assert f"~{command.aliases[0]}" in fields["Aliases"]
    assert fields["Usage"].startswith(f"`~{command.qualified_name}")
    assert message.view is None
