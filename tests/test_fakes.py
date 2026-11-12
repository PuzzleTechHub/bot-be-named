import nextcord
import pytest

from tests.fakes import FakeCategory, FakeChannel, FakeContext, FakeGuild, FakeRole


def test_role_equality_and_overwrites():
    role = FakeRole(1, "GPH1")
    category = FakeCategory(
        10, "GPH 1 Puzzles", {role: nextcord.PermissionOverwrite(view_channel=True)}
    )
    assert FakeRole(1, "renamed") == role
    assert category.overwrites_for(FakeRole(1, "GPH1")).view_channel is True
    assert category.overwrites_for(FakeRole(2, "GPH2")).view_channel is None


def test_channel_joins_its_category():
    category = FakeCategory(10, "GPH 1 Puzzles")
    channel = FakeChannel(20, "puzzle", category)
    guild = FakeGuild(categories=[category])
    assert category.text_channels == [channel]
    assert channel.category is not None
    assert channel.category.id == 10
    assert guild.get_channel(20) is channel
    assert str(channel) == "puzzle"


async def test_second_delete_rasies_not_found():
    ctx = FakeContext(FakeGuild(), FakeChannel(20, "puzzle"))
    message = await ctx.send("hi")
    await message.delete()
    with pytest.raises(nextcord.NotFound):
        await message.delete()


@pytest.mark.parametrize(
    "name, value",
    [("", "value"), ("name", ""), ("x" * 257, "value"), ("name", "x" * 1025)],
)
async def test_send_rejects_bad_fields(name, value):
    ctx = FakeContext(FakeGuild(), FakeChannel(20, "puzzle"))
    embed = nextcord.Embed()
    embed.add_field(name=name, value=value)
    with pytest.raises(ValueError):
        await ctx.send(embed=embed)
    assert ctx.sent == []


async def test_sends_records_embeds():
    ctx = FakeContext(FakeGuild(), FakeChannel(20, "puzzle"))
    embed = nextcord.Embed()
    embed.add_field(name="Success", value="Done")
    await ctx.send(embed=embed)
    assert ctx.sent_embeds == [embed]
