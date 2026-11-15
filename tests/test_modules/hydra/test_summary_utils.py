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
    FakeForum,
    FakeGuild,
    FakeMember,
    FakeRole,
    FakeThread,
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


async def test_get_roles_channels_threads_and_forum_posts(server, monkeypatch):
    """Threads and forum posts on the Overview are summarised like channels"""
    thread = FakeThread(301, "thread-puzzle", server.p1)
    forum = FakeForum(302, "puzzle-forum", server.gph1_cat)
    post = FakeThread(303, "forum-puzzle", forum)
    add_tether(server.gph1_cat.id, GPH1_SHEET)
    patch_overview_sheets(monkeypatch, {GPH1_SHEET: _overview(server.p1, thread, post)})

    found, failed = await summary_utils.get_roles_channels(
        None, _ctx(server, server.gph1), server.gph1, [server.gph1_cat]
    )

    assert [channel for channel, _, _ in found] == [server.p1, thread, post]
    assert [rownum for _, rownum, _ in found] == [3, 4, 5]
    assert failed == []


async def test_get_roles_channels_threads_use_parent_permissions(server, monkeypatch):
    """A thread under a denied channel, or a post in a denied forum, is left out"""
    hidden_thread = FakeThread(301, "hidden-thread", server.hidden)
    forum = FakeForum(302, "hidden-forum", server.gph1_cat, {server.gph1: DENY})
    hidden_post = FakeThread(303, "hidden-post", forum)
    add_tether(server.gph1_cat.id, GPH1_SHEET)
    rows = _overview(server.p1, hidden_thread, hidden_post)
    patch_overview_sheets(monkeypatch, {GPH1_SHEET: rows})

    found, _ = await summary_utils.get_roles_channels(
        None, _ctx(server, server.gph1), server.gph1, [server.gph1_cat]
    )

    assert [channel for channel, _, _ in found] == [server.p1]


def _overview_with_status(*rows):
    """Overview with the status column in E (B1 holds "E"). rows are (channel, status)."""
    sheet = [["D", "E"], ["F", ""], ["", ""]]
    for channel, status in rows:
        sheet.append([str(channel.id), "", "", channel.name, status])
    return sheet


async def test_get_roles_channels_archived_threads(server, monkeypatch):
    """Idle threads and forum posts Discord archived stay in, solved archived ones (~mtahydra) drop out"""
    idle = FakeThread(301, "idle-thread", server.p1, archived=True, cached=False)
    solved = FakeThread(302, "solved-thread", server.p1, archived=True)
    backsolved = FakeThread(303, "backsolved-thread", server.p1, archived=True)
    active_solved = FakeThread(304, "solved-not-mta", server.p1)
    forum = FakeForum(310, "puzzle-forum", server.gph1_cat)
    idle_post = FakeThread(311, "idle-post", forum, archived=True, cached=False)
    solved_post = FakeThread(312, "solved-post", forum, archived=True, cached=False)
    active_post = FakeThread(313, "solved-post-not-mta", forum)
    add_tether(server.gph1_cat.id, GPH1_SHEET)
    rows = _overview_with_status(
        (server.p1, "In Progress"),
        (idle, "Unstarted"),
        (solved, "Solved"),
        (backsolved, "backsolved"),
        (active_solved, "Solved"),
        (idle_post, "In Progress"),
        (solved_post, "Postsolved"),
        (active_post, "Solved"),
    )
    patch_overview_sheets(monkeypatch, {GPH1_SHEET: rows})

    found, failed = await summary_utils.get_roles_channels(
        None, _ctx(server, server.gph1), server.gph1, [server.gph1_cat]
    )

    # Under each parent, active threads come first, then archived ones
    assert [channel for channel, _, _ in found] == [
        server.p1,
        active_solved,
        idle,
        active_post,
        idle_post,
    ]
    assert failed == []


@pytest.mark.parametrize(
    "b1, status, kept",
    [
        ("E", "Solved", False),
        ("E", "Postsolved", False),
        ("E", "Solvedish", True),
        ("E", "", True),
        ("", "Solved", True),  # no status column set, so it can't be told apart
        ("not a column", "Solved", True),
    ],
)
async def test_get_roles_channels_archived_status_column(
    server, monkeypatch, b1, status, kept
):
    thread = FakeThread(301, "archived-thread", server.p1, archived=True)
    add_tether(server.gph1_cat.id, GPH1_SHEET)
    rows = _overview_with_status((thread, status))
    rows[0][1] = b1
    patch_overview_sheets(monkeypatch, {GPH1_SHEET: rows})

    found, _ = await summary_utils.get_roles_channels(
        None, _ctx(server, server.gph1), server.gph1, [server.gph1_cat]
    )

    assert (thread in [channel for channel, _, _ in found]) == kept


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
