import database
from modules.admin.cog import AdminCog
from tests.fakes import SERVER_ID, FakeChannel, FakeContext, FakeGuild, FakeRole


def _ctx(roles):
    ctx = FakeContext(FakeGuild(roles=roles), FakeChannel(20, "bot-commands"))
    ctx.prefix = "~"
    return ctx


# ~listperm


async def test_listperm_skips_deleted_roles(monkeypatch):
    kept = FakeRole(501, "Solvers")
    monkeypatch.setitem(database.PERMISSION_CACHES["Verified"], SERVER_ID, [501, 502])
    ctx = _ctx([kept])
    cog = AdminCog(bot=None)

    await cog.listperm.callback(cog, ctx, "Verified")

    [embed] = ctx.sent_embeds
    [field] = embed.fields
    assert field.value == kept.mention


async def test_listperm_with_only_deleted_roles_says_there_are_none(monkeypatch):
    monkeypatch.setitem(database.PERMISSION_CACHES["Verified"], SERVER_ID, [502])
    ctx = _ctx([])
    cog = AdminCog(bot=None)

    await cog.listperm.callback(cog, ctx, "Verified")

    [embed] = ctx.sent_embeds
    [field] = embed.fields
    assert field.name == "No Verified roles for Test server"
