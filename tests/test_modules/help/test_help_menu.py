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
from utils import command_predicates, google_utils

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


async def test_overview_lists_modules_not_commands(helper):
    [(name, overview), *_] = await helper.help_pages()
    assert name is None
    bot = helper.context.bot
    modules = {field.name: field.value for field in overview.fields}
    assert modules["Hydra"] == bot.get_cog("Hydra").description
    command_names = {f"~{command.name}" for command in bot.commands}
    for value in modules.values():
        assert not command_names & set(value.split())


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
    assert message.embed.title == f"~{command.qualified_name}"
    assert fields["Module"] == command.cog.qualified_name
    assert f"~{command.aliases[0]}" in fields["Aliases"]
    assert fields["Usage"].startswith("`")
    assert message.view is None


async def test_command_help_moves_usage_and_permission_out_of_the_description(helper):
    await helper.send_command_help(helper.context.bot.get_command("deletehydra"))
    [message] = helper.context.channel.sent
    embed = message.embed
    fields = {field.name: field.value for field in embed.fields}
    assert "triggers archiving and cleans up the overview." in embed.description
    assert "Usage" not in embed.description
    assert "Permission Category" not in embed.description
    assert "`~deletehydra #puzzle-channel`" in fields["Usage"]
    assert fields["Required permission(s)"] == (
        "Trusted Roles: See `~addperm Trusted @role`."
    )
    check_embed(embed)


async def test_command_help_usage_field_when_docstring_has_none(helper):
    # Every real command has Usage lines now, so use a made-up one
    @commands.command(help="Says hello.")
    async def hello(ctx, name: str):
        pass

    await helper.send_command_help(hello)
    [message] = helper.context.channel.sent
    fields = {field.name: field.value for field in message.embed.fields}
    assert fields["Usage"] == "`~hello <name>`"


async def test_every_command_help_page_is_valid(helper):
    cogs = helper.context.bot.cogs.values()
    for command in [c for cog in cogs for c in cog.walk_commands()]:
        helper.context.channel.sent.clear()
        await helper.send_command_help(command)
        [message] = helper.context.channel.sent
        fields = {field.name: field.value for field in message.embed.fields}
        assert fields["Usage"], command.qualified_name
        assert "Usage:" not in message.embed.description, command.qualified_name
        assert "Required permission(s)" in fields, command.qualified_name


def test_usage_formats_in_docstrings():
    def usage(doc):
        @commands.command(help=doc)
        async def thing(ctx):
            pass

        return help_command.usage_lines(thing, "~")

    assert usage("Usage: `~a b`") == ["`~a b`"]
    assert usage("Usage:`~a b` (all roles)") == ["`~a b` (all roles)"]
    assert usage("Usage : `~a b`") == ["`~a b`"]
    assert usage('Usage: ~a "B C" (uses the plain tab)') == [
        '`~a "B C"` (uses the plain tab)'
    ]
    assert usage("Usage: ~a b") == ["`~a b`"]
    assert usage("Usage:(as a reply) `~a here`") == ["(as a reply) `~a here`"]
    assert usage("Usage:\n~a\nB\n3rd\n\nAfter.") == ["```\n~a\nB\n3rd\n```"]
    assert usage("Usage: `~a b\n    c`") == ["`~a b c`"]


def test_who_can_use_names_the_category_and_how_to_get_it():
    @command_predicates.is_trusted()
    @commands.command()
    async def thing(ctx):
        pass

    @commands.command()
    async def anyone(ctx):
        pass

    assert help_command.who_can_use(thing, "!") == (
        "Trusted Roles: See `!addperm Trusted @role`."
    )
    assert help_command.who_can_use(anyone, "~") == "Everyone"


def test_unwrap_keeps_separate_lines():
    doc = (
        "Adds a role\n    to the list.\n\nPermission Category : Admin.\n"
        "Usage: `~addperm Verified @Role`\nUsage: `~addperm Trusted @everyone`"
    )
    assert help_command.unwrap(doc) == (
        "Adds a role to the list.\n\nPermission Category : Admin.\n"
        "Usage: `~addperm Verified @Role`\nUsage: `~addperm Trusted @everyone`"
    )


async def test_wrapped_first_paragraph_is_kept_whole(helper):
    pages = [embed for name, embed in await helper.help_pages() if name == "Hydra"]
    fields = {
        field.name.split()[0]: field.value for embed in pages for field in embed.fields
    }
    summary = fields["catsummaryhydra"]
    assert summary.startswith("Collates all the notes")
    assert summary.endswith("to work as expected.")
    assert "\n" not in summary
    assert "summaryallowhydra" not in summary


def test_summary_prefers_brief():
    @commands.command(brief="Short one.")
    async def thing(ctx):
        """Long first line
        that wraps."""

    assert help_command.command_summary(thing) == "Short one."


def test_summary_capped_at_field_limit():
    @commands.command(help="word " * 400)
    async def thing(ctx):
        pass

    summary = help_command.command_summary(thing)
    assert len(summary) == help_command.MAX_FIELD_VALUE
    assert summary.endswith("…")


async def test_permission_pages_list_every_command_once(helper):
    pages = helper.permission_pages()
    assert pages[0][0] is None
    listed = []
    for _, embed in pages:
        check_embed(embed)
    for _, embed in pages[1:]:
        for field in embed.fields:
            listed += field.value.split(", ")
    assert sorted(listed) == sorted(f"`~{c.name}`" for c in helper.context.bot.commands)


async def test_permission_pages_match_the_checks(helper):
    bot = helper.context.bot
    for title, embed in helper.permission_pages()[1:]:
        for field in embed.fields:
            for name in field.value.split(", "):
                command = bot.get_command(name.strip("`~"))
                category = command_predicates.permission_category(command)
                assert help_command.PERMISSION_PAGES[category][0] == title
                assert command.cog.qualified_name == field.name


async def test_permission_pages_go_from_least_to_most_restricted(helper):
    titles = [title for title, _ in helper.permission_pages()[1:]]
    order = [title for title, _ in help_command.PERMISSION_PAGES.values()]
    assert titles[0] == "Everyone"
    assert titles == sorted(titles, key=order.index)


def test_every_permission_category_has_a_page():
    categories = set(command_predicates.PERMISSION_CATEGORIES.values())
    assert categories <= set(help_command.PERMISSION_PAGES)


async def test_permission_overview_counts_each_category(helper):
    [(_, overview), *pages] = helper.permission_pages()
    assert [field.name for field in overview.fields] == [title for title, _ in pages]
    for field, (_, embed) in zip(overview.fields, pages, strict=True):
        count = sum(len(f.value.split(", ")) for f in embed.fields)
        assert field.value.endswith(f"{count} command{'s' * (count != 1)}.")


async def test_permission_pages_use_the_server_prefix(helper):
    helper.context.clean_prefix = "!"
    pages = dict(helper.permission_pages()[1:])
    assert (
        pages["Solver Roles"].description == "Roles added with `!addperm Solver @role`."
    )
    assert all(
        name.startswith("`!") for name in pages["Everyone"].fields[0].value.split(", ")
    )


@pytest.mark.parametrize("word", ["permissions", "Perms", " permission "])
async def test_help_permissions_opens_the_permission_menu(helper, word):
    await helper.command_callback(helper.context, command=word)
    [message] = helper.context.channel.sent
    assert message.embed.title == "Commands by Permission"
    assert message.view.module_select.placeholder == "Jump to a category"
    assert message.embed.footer.text.startswith(f"Page 1/{len(message.view.pages)}")


async def test_help_module_still_opens_that_module(helper):
    await helper.command_callback(helper.context, command="Hydra")
    [message] = helper.context.channel.sent
    assert message.embed.title.startswith("Hydra Commands")
    assert message.view.module_select.placeholder == "Jump to a module"


async def test_overview_points_to_help_permissions(helper):
    [(_, overview), *_] = await helper.help_pages()
    assert "`~help permissions`" in overview.description


def test_chunk_names_splits_at_the_field_limit():
    names = [f"`~command{number:03}`" for number in range(200)]
    chunks = help_command.chunk_names(names)
    assert len(chunks) > 1
    assert all(len(chunk) <= help_command.MAX_FIELD_VALUE for chunk in chunks)
    assert ", ".join(chunks) == ", ".join(names)
