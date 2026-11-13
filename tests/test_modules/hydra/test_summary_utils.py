from types import SimpleNamespace
from typing import Any
import gspread
import nextcord
import pytest

from modules.hydra.hydra_utils import summary_utils
from tests.fakes import (
    FakeCategory,
    FakeChannel,
    FakeContext,
    FakeGuild,
    FakeMember,
    FakeRole,
    add_grant,
    add_tether,
    patch_overview_sheets,
)

GPH1_SHEET = "https://docs.google.com/spreadsheets/d/gph1/edit"
GPH2_SHEET = "https://docs.google.com/spreadsheets/d/gph2/edit"

ALLOW = nextcord.PermissionOverwrite(view_channel=True)
DENY = nextcord.PermissionOverwrite(view_channel=False)


def _overview(*channels):
    """Overview rows, two headers, and one row per channel (A is the ID)"""
    rows = [["Channel ID", "Name"], ["", ""]]
    rows += [[str(channel.id), channel.name] for channel in channels]
    return rows


@pytest.fixture
def server():
    """Plausible server setup"""
    s = SimpleNamespace()

    s.gph1 = FakeRole(11, "GPH1")
    s.gph2 = FakeRole(12, "GPH2")
    s.everyone = FakeRole(1, "@everyone")

    s.gph1_cat = FakeCategory(101, "GPH 1 Puzzles", {s.gph1: ALLOW})
    s.gph2_cat = FakeCategory(102, "GPH 2 Puzzles", {s.gph2: ALLOW})

    # Both teams can see this category and channel but has no tethers nor upzzles
    s.shared_cat = FakeCategory(103, "GPH General", {s.gph1: ALLOW, s.gph2: ALLOW})
    s.archive_cat = FakeCategory(104, "GPH 1 Archive", {s.gph1: ALLOW})
    s.mods_cat = FakeCategory(105, "Mods", {s.everyone: DENY})
    s.bot_cat = FakeCategory(106, "Bot")

    s.p1 = FakeChannel(201, "puzzle-1", s.gph1_cat)
    s.p2 = FakeChannel(202, "puzzle-2", s.gph1_cat)
    s.hidden = FakeChannel(203, "hidden-puzzle", s.gph1_cat, {s.gph1: DENY})
    s.p3 = FakeChannel(204, "puzzle-3", s.gph2_cat)
    s.discussion = FakeChannel(206, "gph-discussion", s.shared_cat)
    s.p_archived = FakeChannel(205, "archived-puzzle", s.archive_cat)
    s.mods = FakeChannel(207, "mods-chat", s.mods_cat)
    s.bot = FakeChannel(208, "bot-commands", s.bot_cat)

    s.guild = FakeGuild(
        roles=[s.everyone, s.gph1, s.gph2],
        categories=[
            s.gph1_cat,
            s.gph2_cat,
            s.shared_cat,
            s.archive_cat,
            s.mods_cat,
            s.bot_cat,
        ],
    )
    return s


def _ctx(server, *roles) -> Any:
    return FakeContext(server.guild, server.bot, FakeMember(roles=roles))


# get_allowed_roles


async def test_get_allowed_roles(server):
    add_grant(server.bot, server.gph1)
    add_grant(server.bot, server.gph2)
    add_grant(server.mods, server.everyone)  # another channel's grant
    assert summary_utils.get_allowed_roles(server.guild, server.bot.id) == [
        server.gph1,
        server.gph2,
    ]


def test_get_allowed_roles_skips_deleted_roles(server):
    add_grant(server.bot, server.gph1)
    add_grant(server.bot, FakeRole(99, "Deleted role"))
    assert summary_utils.get_allowed_roles(server.guild, server.bot.id) == [server.gph1]


def test_get_allowed_roles_none(server):
    assert summary_utils.get_allowed_roles(server.guild, server.bot.id) == []


# get_matched_roles


async def test_get_matched_roles_not_set_up(server):
    ctx = _ctx(server, server.gph1)
    assert await summary_utils.get_matched_roles(ctx) == []
    [embed] = ctx.sent_embeds
    assert embed.fields[0].name == "Failed"
    assert "aren't set up in this channel" in embed.fields[0].value


async def test_get_matched_roles_caller_lacks_role(server):
    add_grant(server.bot, server.gph1)
    ctx = _ctx(server, server.gph2)
    assert await summary_utils.get_matched_roles(ctx) == []
    [embed] = ctx.sent_embeds
    assert embed.fields[0].name == "Failed"
    assert embed.fields[0].value == "You need a role allowed here."


async def test_get_matched_roles_only_callers_roles(server):
    add_grant(server.bot, server.gph1)
    add_grant(server.bot, server.gph2)
    ctx = _ctx(server, server.everyone, server.gph2)
    assert await summary_utils.get_matched_roles(ctx) == [server.gph2]
    assert ctx.sent == []


async def test_get_mached_roles_grant_in_other_channel_ignored(server):
    add_grant(server.mods, server.gph1)
    ctx = _ctx(server, server.gph1)
    assert await summary_utils.get_matched_roles(ctx) == []
    assert "aren't set up" in ctx.sent_embeds[0].fields[0].value


# get_role_categories


def test_get_role_catgories_needs_explicit_allow_and_skips_archive(server):
    # Not GPH 2 (no overwrite), GPH 1 Archive (archive), Mods (denies @everyone only)
    assert summary_utils.get_role_categories(server.guild, server.gph1) == [
        server.gph1_cat,
        server.shared_cat,
    ]
    assert summary_utils.get_role_categories(server.guild, server.gph2) == [
        server.gph2_cat,
        server.shared_cat,
    ]


def test_get_role_categories_deny_excluded(server):
    server.bot_cat.overwrites[server.gph1] = DENY
    assert server.bot_cat not in summary_utils.get_role_categories(
        server.guild, server.gph1
    )


@pytest.mark.parametrize(
    "name, kept",
    [
        ("GPH 1 Archive", False),
        ("GPH 1 Archive 2", False),
        ("Archive", False),
        ("GPH 1 Puzzles", True),
    ],
)
def test_get_role_categories_archives_names(server, name, kept):
    category = FakeCategory(300, name, {server.gph1: ALLOW})
    server.guild.categories = [category]
    result = summary_utils.get_role_categories(server.guild, server.gph1)
    assert result == ([category] if kept else [])


# get_roles_channels


async def test_get_roles_channels_drops_denied_and_untethered(server, monkeypatch):
    add_tether(server.gph1_cat.id, GPH1_SHEET)
    rows = _overview(server.p1, server.p2, server.hidden)
    opened = patch_overview_sheets(monkeypatch, {GPH1_SHEET: rows})
    ctx = _ctx(server, server.gph1)
    categories = summary_utils.get_role_categories(server.guild, server.gph1)
    assert server.shared_cat in categories

    found, failed = await summary_utils.get_roles_channels(
        None,
        ctx,
        server.gph1,
        categories,
    )

    # hidden-puzzle denies GPH1, gph-discussion has no tether
    assert [channel for channel, _, _ in found] == [server.p1, server.p2]
    assert failed == []
    assert opened == [GPH1_SHEET]
    assert ctx.sent == []


async def test_get_roles_channels_untethered_discussion_on_tethered_sheet(
    server, monkeypatch
):
    """A  channel should be left out even in a tethered category if it has no corresponding sheet"""
    add_tether(server.shared_cat.id, GPH1_SHEET)
    patch_overview_sheets(monkeypatch, {GPH1_SHEET: _overview(server.p1)})
    ctx = _ctx(server, server.gph2)

    found, failed = await summary_utils.get_roles_channels(
        None, ctx, server.gph2, [server.shared_cat]
    )

    assert (found, failed) == ([], [])


# find channel_rows


async def test_find_channel_rows_found_with_row_numbers(server, monkeypatch):
    add_tether(server.gph1_cat.id, GPH1_SHEET)
    rows = _overview(server.p2, server.p1)
    patch_overview_sheets(monkeypatch, {GPH1_SHEET: rows})

    found, failed, missing = await summary_utils.find_channel_rows(
        None, _ctx(server), [server.p1, server.p2]
    )

    # Rows are 1 indexed and counted from the top
    assert found == [(server.p1, 4, rows), (server.p2, 3, rows)]
    assert (failed, missing) == ([], [])


async def test_find_channel_rows_open_sheet_once(server, monkeypatch):
    add_tether(server.gph1_cat.id, GPH1_SHEET)
    add_tether(server.gph2_cat.id, GPH2_SHEET)
    opened = patch_overview_sheets(
        monkeypatch,
        {
            GPH1_SHEET: _overview(server.p1, server.p2),
            GPH2_SHEET: _overview(server.p3),
        },
    )

    found, _, _ = await summary_utils.find_channel_rows(
        None, _ctx(server), [server.p1, server.p3, server.p2]
    )

    # Group by sheet in order of first that is needed
    assert opened == [GPH1_SHEET, GPH2_SHEET]
    assert [channel for channel, _, _ in found] == [server.p1, server.p2, server.p3]


async def test_find_channel_rows_missing(server, monkeypatch):
    add_tether(server.gph1_cat.id, GPH1_SHEET)
    patch_overview_sheets(monkeypatch, {GPH1_SHEET: _overview(server.p1)})

    # p2 is tethered but not on the Overview; p3 has no tether at all
    found, failed, missing = await summary_utils.find_channel_rows(
        None, _ctx(server), [server.p1, server.p2, server.p3]
    )

    assert [channel for channel, _, _ in found] == [server.p1]
    assert failed == []
    assert missing == [server.p3, server.p2]


async def test_find_channel_rows_failed_sheet(server, monkeypatch):
    add_tether(server.gph1_cat.id, GPH1_SHEET)
    add_tether(server.gph2_cat.id, GPH2_SHEET)
    patch_overview_sheets(
        monkeypatch,
        {
            GPH1_SHEET: gspread.exceptions.SpreadsheetNotFound(),
            GPH2_SHEET: _overview(server.p3),
        },
    )
    ctx = _ctx(server)

    found, failed, missing = await summary_utils.find_channel_rows(
        None, ctx, [server.p1, server.p2, server.p3]
    )

    assert [channel for channel, _, _ in found] == [server.p3]
    assert failed == [server.p1, server.p2]
    assert missing == []
    [embed] = ctx.sent_embeds
    assert embed.fields[0].name == "Failed"
    assert "no tab named 'Overview'" in embed.fields[0].value


async def test_find_channel_rows_no_channels(server, monkeypatch):
    _ = patch_overview_sheets(monkeypatch, {})
    assert await summary_utils.find_channel_rows(None, _ctx(server), []) == (
        [],
        [],
        [],
    )
