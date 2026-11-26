import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

import database

REPO = Path(__file__).parent.parent
CACHES = [
    "PREFIXES",
    "VERIFIEDS",
    "TRUSTEDS",
    "SOLVERS",
    "TESTERS",
    "CUSTOM_COMMANDS",
    "CHANNEL_MIRRORS",
]
TABLES = [
    database.Prefixes,
    database.Verifieds,
    database.CustomCommands,
    database.ChannelMirrors,
]


@pytest.fixture
def clean_tables():
    """Empty the tables load_all reads, and reload the caches afterwards."""

    def wipe():
        with Session(database.DATABASE_ENGINE) as session:
            for table in TABLES:
                session.query(table).delete()
            session.commit()

    wipe()
    yield
    wipe()
    database.load_all()


def add_rows():
    with Session(database.DATABASE_ENGINE) as session:
        session.add(database.Prefixes(server_id=1, server_name="s", prefix="!"))
        for role_id, permissions in [
            (10, "Verified"),
            (11, "Verified"),
            (20, "Trusted"),
        ]:
            session.add(
                database.Verifieds(
                    server_id=1,
                    server_name="s",
                    role_id=role_id,
                    role_name="r",
                    permissions=permissions,
                    role_id_permissions=f"{role_id}_{permissions}",
                )
            )
        session.add(
            database.CustomCommands(
                server_id=1,
                server_name="s",
                server_id_command="1 hello",
                command_name="Hello",
                command_return="hi",
                image=False,
                responses=None,
            )
        )
        session.add(
            database.ChannelMirrors(
                server_id=1,
                server_name="s",
                source_channel_id=100,
                source_channel_name="a",
                target_channel_id=200,
                target_channel_name="b",
            )
        )
        session.commit()


def test_load_all_fills_caches(clean_tables):
    add_rows()
    database.load_all()
    assert database.PREFIXES == {1: "!"}
    assert database.VERIFIEDS == {1: [10, 11]}
    assert database.TRUSTEDS == {1: [20]}
    assert database.SOLVERS == {}
    assert database.TESTERS == {}
    assert database.CUSTOM_COMMANDS == {1: {"hello": ("hi", False, None)}}
    assert database.CHANNEL_MIRRORS == {100: {200}}


def test_load_all_refills_the_same_dicts(clean_tables):
    before = {name: getattr(database, name) for name in CACHES}
    database.PREFIXES[999] = "stale"
    add_rows()
    database.load_all()
    for name in CACHES:
        assert getattr(database, name) is before[name]
    assert 999 not in database.PREFIXES
    assert database.PREFIXES == {1: "!"}


def test_importing_does_not_touch_the_database():
    cogs = sorted(
        f"modules.{p.parent.name}.cog" for p in (REPO / "modules").glob("*/cog.py")
    )
    code = (
        "import importlib, database\nfor m in %r:\n    importlib.import_module(m)\n"
        % cogs
    )
    env = dict(os.environ, DATABASE_URL="postgresql://nobody:nothing@127.0.0.1:1/none")
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "url",
    [
        "postgres://u:p@127.0.0.1:1/db",
        "postgresql://u:p@127.0.0.1:1/db",
        "postgresql+psycopg2://u:p@127.0.0.1:1/db",
    ],
)
def test_postgres_urls_use_psycopg2(url):
    # SQLAlchemy 2.1 would pick psycopg (v3) for a plain postgresql:// URL
    code = "import database; print(database.DATABASE_ENGINE.url.drivername)"
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPO,
        env=dict(os.environ, DATABASE_URL=url),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "postgresql+psycopg2"


# sheet tethers

LINK = "https://docs.google.com/spreadsheets/d/one/edit"
OTHER_LINK = "https://docs.google.com/spreadsheets/d/two/edit"


def test_set_tether_adds_row():
    database.set_tether(1, "Server", 100, "puzzles", LINK)
    row = database.get_tether(100)
    assert (row.server_id, row.server_name, row.channel_or_cat_name) == (
        1,
        "Server",
        "puzzles",
    )
    assert row.sheet_link == LINK


def test_set_tether_again_only_changes_link():
    database.set_tether(1, "Server", 100, "puzzles", LINK)
    database.set_tether(2, "Renamed", 100, "renamed", OTHER_LINK)
    [row] = database.get_all_tethers()
    assert (row.server_id, row.channel_or_cat_name, row.sheet_link) == (
        1,
        "puzzles",
        OTHER_LINK,
    )


def test_get_tether_missing_or_none():
    database.set_tether(1, "Server", 100, "puzzles", LINK)
    assert database.get_tether(200) is None
    assert database.get_tether(None) is None


def test_get_tethers_several_at_once():
    database.set_tether(1, "Server", 100, "puzzles", LINK)
    database.set_tether(1, "Server", 200, "puzzle-1", OTHER_LINK)
    tethers = database.get_tethers([100, 200, 300, None])
    assert {place_id: row.sheet_link for place_id, row in tethers.items()} == {
        100: LINK,
        200: OTHER_LINK,
    }


def test_get_tethers_nothing_asked():
    assert database.get_tethers([]) == {}
    assert database.get_tethers([None]) == {}


def test_delete_tether_only_that_one():
    database.set_tether(1, "Server", 100, "puzzles", LINK)
    database.set_tether(1, "Server", 200, "puzzle-1", OTHER_LINK)
    database.delete_tether(100)
    assert [row.channel_or_cat_id for row in database.get_all_tethers()] == [200]
    database.delete_tether(100)


# summary grants


def _grant(channel_id, role_id, server_id=1):
    return database.add_summary_grant(
        server_id,
        "Server",
        channel_id,
        f"chan-{channel_id}",
        role_id,
        f"role-{role_id}",
    )


def test_add_summary_grant_once():
    assert _grant(200, 7) is True
    assert _grant(200, 7) is False
    [row] = database.get_server_summary_grants(1)
    assert (row.channel_id, row.role_id, row.channel_id_role_id) == (200, 7, "200_7")


def test_summary_role_ids_per_channel():
    _grant(200, 7)
    _grant(200, 8)
    _grant(201, 9)
    assert sorted(database.get_summary_role_ids(200)) == [7, 8]
    assert database.get_summary_role_ids(999) == []


def test_server_summary_grants_only_that_server():
    _grant(200, 7)
    _grant(300, 7, server_id=2)
    assert [row.channel_id for row in database.get_server_summary_grants(2)] == [300]


def test_delete_summary_grant():
    _grant(200, 7)
    _grant(200, 8)
    assert database.delete_summary_grant(200, 7) is True
    assert database.delete_summary_grant(200, 7) is False
    assert database.get_summary_role_ids(200) == [8]


def test_delete_role_and_channel_summary_grants():
    _grant(200, 7)
    _grant(201, 7)
    _grant(201, 8)
    _grant(202, 9)
    database.delete_role_summary_grants(7)
    assert database.get_summary_role_ids(201) == [8]
    database.delete_channel_summary_grants(201)
    assert [row.channel_id for row in database.get_server_summary_grants(1)] == [202]


# solve streams


def _stream(channel_id, sheet_key, server_id=1, channel_name=None):
    return database.set_solve_stream(
        server_id, "Server", channel_id, channel_name or f"chan-{channel_id}", sheet_key
    )


def test_set_solve_stream_reports_existing_and_refreshes_name():
    assert _stream(200, "sheet") is False
    assert _stream(200, "sheet", channel_name="renamed") is True
    [row] = database.get_solve_streams("sheet", 1)
    assert (row.channel_id, row.channel_name) == (200, "renamed")


def test_get_solve_streams_by_sheet_and_server():
    _stream(200, "sheet")
    _stream(201, "sheet")
    _stream(202, "other")
    _stream(300, "sheet", server_id=2)
    assert sorted(row.channel_id for row in database.get_solve_streams("sheet", 1)) == [
        200,
        201,
    ]


def test_delete_solve_streams():
    _stream(200, "sheet")
    _stream(200, "other")
    _stream(201, "sheet")
    assert database.delete_solve_stream("sheet", 200) is True
    assert database.delete_solve_stream("sheet", 200) is False
    database.delete_channel_solve_streams(201)
    assert database.get_solve_streams("sheet", 1) == []
    assert [row.channel_id for row in database.get_solve_streams("other", 1)] == [200]


# channel mirrors


def _mirror(source_id, target_id, server_id=1):
    return database.add_channel_mirror(
        server_id, "Server", source_id, f"s-{source_id}", target_id, f"t-{target_id}"
    )


def _mirror_pairs(server_id=1):
    return sorted(
        (row.source_channel_id, row.target_channel_id)
        for row in database.get_server_channel_mirrors(server_id)
    )


def test_add_channel_mirror_once_and_caches():
    assert _mirror(10, 20) is True
    assert _mirror(10, 20) is False
    _mirror(10, 21)
    assert _mirror_pairs() == [(10, 20), (10, 21)]
    assert database.CHANNEL_MIRRORS == {10: {20, 21}}


def test_delete_channel_mirror_updates_cache():
    _mirror(10, 20)
    _mirror(10, 21)
    assert database.delete_channel_mirror(10, 20) is True
    assert database.delete_channel_mirror(10, 20) is False
    assert _mirror_pairs() == [(10, 21)]
    assert database.CHANNEL_MIRRORS == {10: {21}}


def test_delete_channel_mirrors_for_source_and_target():
    _mirror(10, 20)
    _mirror(30, 10)
    _mirror(30, 40)
    _mirror(50, 60, server_id=2)
    database.delete_channel_mirrors_for(10)
    assert _mirror_pairs() == [(30, 40)]
    assert _mirror_pairs(2) == [(50, 60)]
    assert database.CHANNEL_MIRRORS == {30: {40}, 50: {60}}
