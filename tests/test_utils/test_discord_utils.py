import nextcord
import pytest

import constants
from utils import discord_utils

# Discord's own limits, which split_embed must stay within.
DISCORD_EMBED_LIMIT = 6000
DISCORD_DESCRIPTION_LIMIT = 4096
DISCORD_FIELD_VALUE_LIMIT = 1024


@pytest.mark.parametrize(
    "n, expected",
    [
        (0, "th"),
        (1, "st"),
        (2, "nd"),
        (3, "rd"),
        (4, "th"),
        (11, "th"),
        (12, "th"),
        (13, "th"),
        (21, "st"),
        (101, "st"),
        (111, "th"),
        (112, "th"),
        (113, "th"),
    ],
)
def test_get_ordinal_suffix(n, expected):
    assert discord_utils.get_ordinal_suffix(n) == expected


@pytest.mark.parametrize(
    "make_embed, field_name",
    [
        (discord_utils.create_success_embed, "Success"),
        (discord_utils.create_failure_embed, "Failed"),
    ],
)
def test_success_and_failure_embeds(make_embed, field_name):
    embed = make_embed("hello")
    assert len(embed.fields) == 1
    field = embed.fields[0]
    assert field.name == field_name
    assert field.value == "hello"
    assert field.inline is False
    assert embed.color.value == constants.EMBED_COLOR == 0xD4E4FF


def _assert_within_discord_limits(embeds):
    for embed in embeds:
        description = embed.description or ""
        assert len(description) <= DISCORD_DESCRIPTION_LIMIT
        for field in embed.fields:
            assert field.name
            assert len(field.value) <= DISCORD_FIELD_VALUE_LIMIT
        assert len(embed) <= DISCORD_EMBED_LIMIT


def test_split_embed_long_description():
    embed = nextcord.Embed(description="word " * 900)  # 4,500 characters
    embeds = discord_utils.split_embed(embed)
    assert [len(e.description) for e in embeds] == [2000, 2000, 500]
    assert "".join(e.description for e in embeds) == embed.description
    _assert_within_discord_limits(embeds)


def test_split_embed_long_fields():
    embed = nextcord.Embed(description="")
    for name in ["A", "B", "C"]:
        embed.add_field(name=name, value="word " * 300)  # 1,500 characters
    embeds = discord_utils.split_embed(embed)
    pieces = [(f.name, len(f.value)) for e in embeds for f in e.fields]
    assert pieces == [
        ("A", 1000),
        ("A", 500),
        ("B", 1000),
        ("B", 500),
        ("C", 1000),
        ("C", 500),
    ]
    _assert_within_discord_limits(embeds)


def test_split_embed_short_embed_unchanged():
    embed = nextcord.Embed(title="Title", description="Short", color=0x123456)
    embed.add_field(name="Field", value="Value", inline=True)
    [result] = discord_utils.split_embed(embed)
    assert result.title == "Title"
    assert result.description == "Short"
    assert result.color.value == 0x123456
    assert [(f.name, f.value, f.inline) for f in result.fields] == [
        ("Field", "Value", True)
    ]


def test_merge_embed_keeps_field_order():
    first = nextcord.Embed()
    first.add_field(name="1", value="a")
    first.add_field(name="2", value="b")
    second = nextcord.Embed()
    second.add_field(name="3", value="c", inline=False)
    second.add_field(name="4", value="d")

    merged = discord_utils.merge_embed(first, second)

    assert merged is first
    assert [(f.name, f.value, f.inline) for f in merged.fields] == [
        ("1", "a", True),
        ("2", "b", True),
        ("3", "c", False),
        ("4", "d", True),
    ]
