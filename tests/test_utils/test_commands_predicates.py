from types import SimpleNamespace

import pytest

import database
from utils import command_predicates

GUILD_ID = 111
ROLE_ID = 222
OTHER_ROLE_ID = 333


def make_ctx(role_ids=(), in_guild=True, admin=False, owner=False):
    """commands.Context for the predicates"""
    guild = SimpleNamespace(id=GUILD_ID) if in_guild else None
    author = SimpleNamespace(
        roles=[SimpleNamespace(id=role_id) for role_id in role_ids],
        guild_permissions=SimpleNamespace(administrator=admin),
    )

    async def is_owner(user):
        return owner

    return SimpleNamespace(
        guild=guild,
        author=author,
        message=SimpleNamespace(guild=guild, author=author),
        bot=SimpleNamespace(is_owner=is_owner),
    )


async def check(predicate_factory, ctx):
    return await predicate_factory().predicate(ctx)


# Each role check and the cache it reads
ROLE_CHECKS = [
    (command_predicates.is_tester, "TESTERS"),
    (command_predicates.is_solver, "SOLVERS"),
    (command_predicates.is_verified, "VERIFIEDS"),
    (command_predicates.is_trusted, "TRUSTEDS"),
    (command_predicates.is_trusted_or_bot_owner, "TRUSTEDS"),
]


@pytest.fixture(autouse=True)
def empty_role_caches(monkeypatch):
    for cache in ("TESTERS", "SOLVERS", "VERIFIEDS", "TRUSTEDS"):
        monkeypatch.setattr(database, cache, {})


@pytest.mark.parametrize("factory, cache", ROLE_CHECKS)
async def test_role_check_matching_role(monkeypatch, factory, cache):
    monkeypatch.setattr(database, cache, {GUILD_ID: [ROLE_ID]})
    assert await check(factory, make_ctx([OTHER_ROLE_ID, ROLE_ID]))


@pytest.mark.parametrize("factory, cache", ROLE_CHECKS)
async def test_role_check_no_matching_role(monkeypatch, factory, cache):
    monkeypatch.setattr(database, cache, {GUILD_ID: [ROLE_ID]})
    assert not await check(factory, make_ctx([OTHER_ROLE_ID]))


@pytest.mark.parametrize("factory, cache", ROLE_CHECKS)
async def test_role_check_server_not_in_cache(factory, cache):
    assert not await check(factory, make_ctx([ROLE_ID]))


@pytest.mark.parametrize("factory, cache", ROLE_CHECKS)
async def test_role_check_other_servers_role(monkeypatch, factory, cache):
    monkeypatch.setattr(database, cache, {GUILD_ID + 1: [ROLE_ID], GUILD_ID: []})
    assert not await check(factory, make_ctx([ROLE_ID]))


@pytest.mark.parametrize("factory, cache", ROLE_CHECKS)
async def test_role_check_in_dms(monkeypatch, factory, cache):
    monkeypatch.setattr(database, cache, {GUILD_ID: [ROLE_ID]})
    assert not await check(factory, make_ctx([ROLE_ID], in_guild=False))


async def test_role_checks_read_their_own_cache(monkeypatch):
    """A Solver role must not pass is_trusted, and so on."""
    monkeypatch.setattr(database, "SOLVERS", {GUILD_ID: [ROLE_ID]})
    ctx = make_ctx([ROLE_ID])
    results = {
        factory.__name__: bool(await check(factory, ctx)) for factory, _ in ROLE_CHECKS
    }
    assert results == {
        "is_tester": False,
        "is_solver": True,
        "is_verified": False,
        "is_trusted": False,
        "is_trusted_or_bot_owner": False,
    }


async def test_trusted_or_bot_owner_lets_owner_in_without_role():
    assert await check(command_predicates.is_trusted_or_bot_owner, make_ctx(owner=True))


async def test_trusted_or_bot_owner_owner_in_dms_refused():
    ctx = make_ctx(owner=True, in_guild=False)
    assert not await check(command_predicates.is_trusted_or_bot_owner, ctx)


@pytest.mark.parametrize("owner, expected", [(True, True), (False, False)])
async def test_is_bot_owner(owner, expected):
    assert (
        await check(command_predicates.is_bot_owner, make_ctx(owner=owner)) is expected
    )


async def test_is_bot_owner_works_in_dms():
    ctx = make_ctx(owner=True, in_guild=False)
    assert await check(command_predicates.is_bot_owner, ctx)


@pytest.mark.parametrize("admin, expected", [(True, True), (False, False)])
async def test_is_admin(admin, expected):
    assert await check(command_predicates.is_admin, make_ctx(admin=admin)) is expected


async def test_is_admin_in_dms():
    ctx = make_ctx(admin=True, in_guild=False)
    assert not await check(command_predicates.is_admin, ctx)


@pytest.mark.parametrize(
    "owner, admin, expected",
    [
        (True, False, True),
        (False, True, True),
        (True, True, True),
        (False, False, False),
    ],
)
async def test_is_bot_owner_or_admin(owner, admin, expected):
    ctx = make_ctx(owner=owner, admin=admin)
    assert await check(command_predicates.is_bot_owner_or_admin, ctx) is expected


async def test_is_bot_owner_or_admin_owner_in_dms_refused():
    ctx = make_ctx(owner=True, in_guild=False)
    assert not await check(command_predicates.is_bot_owner_or_admin, ctx)
