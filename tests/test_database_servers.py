"""Data layer for prefixes, permission roles, custom commands and leaving a server."""

import pytest
from sqlalchemy.orm import Session

import constants
import database
from database import models

SERVER = 1


@pytest.fixture(autouse=True)
def clean_tables():
    """Start from empty tables and caches, and reload the caches afterwards."""

    def wipe():
        with Session(database.DATABASE_ENGINE) as session:
            for table in (
                database.Prefixes,
                database.Verifieds,
                database.CustomCommands,
            ):
                session.query(table).delete()
            session.commit()

    wipe()
    database.load_all()
    yield
    wipe()
    database.load_all()


def _prefix_row(server_id):
    with Session(database.DATABASE_ENGINE) as session:
        return session.get(database.Prefixes, server_id)


# prefixes


def test_add_server_gives_the_default_prefix_and_empty_caches():
    database.add_server(SERVER, "s")
    assert _prefix_row(SERVER).prefix == constants.DEFAULT_BOT_PREFIX
    assert database.PREFIXES[SERVER] == constants.DEFAULT_BOT_PREFIX
    for cache in database.PERMISSION_CACHES.values():
        assert cache[SERVER] == []
    assert database.CUSTOM_COMMANDS[SERVER] == {}


def test_add_server_keeps_an_existing_prefix():
    database.add_server(SERVER, "s")
    database.set_prefix(SERVER, "!")
    database.PREFIXES.clear()
    database.add_server(SERVER, "s")  # used to crash in on_guild_join: duplicate key
    assert database.PREFIXES[SERVER] == "!"
    assert _prefix_row(SERVER).prefix == "!"


def test_set_prefix_and_get_server_prefix():
    assert database.get_server_prefix(SERVER) == constants.DEFAULT_BOT_PREFIX
    database.add_server(SERVER, "s")
    database.set_prefix(SERVER, "!")
    assert database.PREFIXES[SERVER] == "!"
    assert database.get_server_prefix(SERVER) == "!"


# permission roles


def test_add_permission_role_then_again():
    assert database.add_permission_role(SERVER, "s", 10, "r", models.TRUSTED)
    assert not database.add_permission_role(SERVER, "s", 10, "r", models.TRUSTED)
    assert database.TRUSTEDS[SERVER] == [10]
    assert database.VERIFIEDS.get(SERVER, []) == []
    # Same role in another category is fine
    assert database.add_permission_role(SERVER, "s", 10, "r", models.VERIFIED)
    assert database.get_server_permission_roles(SERVER) == {
        models.VERIFIED: [10],
        models.TRUSTED: [10],
        models.TESTER: [],
        models.SOLVER: [],
    }


def test_delete_permission_role_then_again():
    database.add_permission_role(SERVER, "s", 10, "r", models.SOLVER)
    assert database.delete_permission_role(SERVER, 10, models.SOLVER)
    assert database.SOLVERS[SERVER] == []
    assert not database.delete_permission_role(SERVER, 10, models.SOLVER)
    # Another server can't remove it
    database.add_permission_role(SERVER, "s", 10, "r", models.SOLVER)
    assert not database.delete_permission_role(2, 10, models.SOLVER)
    assert database.get_server_permission_roles(SERVER)[models.SOLVER] == [10]


def test_delete_permission_role_with_no_cache_entry():
    # removeperm used to KeyError when the server had no cache entry
    assert not database.delete_permission_role(99, 10, models.TESTER)


# custom commands


def test_add_custom_command_then_again():
    assert database.add_custom_command(SERVER, "s", "hello", ["hi", "yo"], False)
    assert database.CUSTOM_COMMANDS[SERVER]["hello"] == ("hi", False, ["hi", "yo"])
    database.CUSTOM_COMMANDS[SERVER].clear()
    # In the database but not the cache: refused, and the stored one is cached
    assert not database.add_custom_command(SERVER, "s", "hello", ["other"], True)
    assert database.CUSTOM_COMMANDS[SERVER]["hello"] == ("hi", False, ["hi", "yo"])


def test_find_custom_command_prefers_the_server_then_global():
    assert database.find_custom_command(SERVER, "hello") is None
    database.add_custom_command(constants.DB_GLOBAL, "Global", "hello", ["g"], False)
    database.CUSTOM_COMMANDS.clear()
    assert database.find_custom_command(SERVER, "hello") == ("g", False, ["g"])
    assert "hello" in database.CUSTOM_COMMANDS[constants.DB_GLOBAL]
    database.add_custom_command(SERVER, "s", "hello", ["mine"], True)
    database.CUSTOM_COMMANDS.clear()
    assert database.find_custom_command(SERVER, "hello") == ("mine", True, ["mine"])
    assert "hello" in database.CUSTOM_COMMANDS[SERVER]


def test_set_custom_command_responses_keeps_is_image():
    database.add_custom_command(SERVER, "s", "pic", ["a.png"], True)
    database.set_custom_command_responses(SERVER, "pic", ["b.png", "c.png"])
    expected = ("b.png", True, ["b.png", "c.png"])
    assert database.CUSTOM_COMMANDS[SERVER]["pic"] == expected
    assert database.get_server_custom_commands(SERVER) == {"pic": expected}


def test_delete_custom_command():
    database.add_custom_command(SERVER, "s", "hello", ["hi"], False)
    database.add_custom_command(constants.DB_GLOBAL, "Global", "hello", ["g"], False)
    database.delete_custom_command(SERVER, "hello")
    assert "hello" not in database.CUSTOM_COMMANDS[SERVER]
    assert database.get_server_custom_commands(SERVER) == {}
    assert database.get_server_custom_commands(constants.DB_GLOBAL) == {
        "hello": ("g", False, ["g"])
    }


# leaving a server


def test_delete_server_data():
    database.add_server(SERVER, "s")
    database.add_server(2, "other")
    database.add_permission_role(SERVER, "s", 10, "r", models.VERIFIED)
    database.add_custom_command(SERVER, "s", "hello", ["hi"], False)
    database.set_tether(SERVER, "s", 100, "cat", "link")
    database.add_summary_grant(SERVER, "s", 200, "chan", 10, "r")
    database.set_solve_stream(SERVER, "s", 200, "chan", "key")
    database.add_channel_mirror(SERVER, "s", 200, "a", 201, "b")
    database.add_channel_mirror(2, "other", 300, "c", 301, "d")

    database.delete_server_data(SERVER)

    assert _prefix_row(SERVER) is None
    assert database.get_server_permission_roles(SERVER)[models.VERIFIED] == []
    assert database.get_server_custom_commands(SERVER) == {}
    assert database.get_tether(100) is None
    assert database.get_server_summary_grants(SERVER) == []
    assert database.get_solve_streams("key", SERVER) == []
    assert database.get_server_channel_mirrors(SERVER) == []
    for cache in (
        database.PREFIXES,
        database.CUSTOM_COMMANDS,
        *database.PERMISSION_CACHES.values(),
    ):
        assert SERVER not in cache
    assert database.CHANNEL_MIRRORS.get(200, set()) == set()
    # The other server is untouched
    assert database.PREFIXES[2] == constants.DEFAULT_BOT_PREFIX
    assert database.CHANNEL_MIRRORS[300] == {301}


def test_delete_server_data_for_an_unknown_server():
    # on_guild_remove used to KeyError when a cache had no entry for the server
    database.delete_server_data(99)
