import pytest

from utils import custom_command_utils as ccu


@pytest.mark.parametrize(
    "content, arguments",
    [
        ("~issue 312", ["312"]),
        ("~issue", []),
        ("~say  hello   world ", ["hello", "world"]),
        ('~say "two words" three', ["two words", "three"]),
        ("~say don't stop", ["don't", "stop"]),
        ("~say don't won't", ["don't", "won't"]),
        ("~say it's Pat's", ["it's", "Pat's"]),
        (r"~say C:\Users\me", [r"C:\Users\me"]),
        ("~say “two words” three", ["two words", "three"]),  # phone quotes
        ('~say "unclosed quote', ['"unclosed', "quote"]),
        ("!!say a b", ["a", "b"]),
    ],
)
def test_arguments_after_command(content, arguments):
    prefix = "!!" if content.startswith("!!") else "~"
    assert ccu.arguments_after_command(content, prefix) == arguments


@pytest.mark.parametrize(
    "reply, arguments, expected",
    [
        ("https://github.com/x/issues/$1", ["29"], "https://github.com/x/issues/29"),
        ("$2 then $1", ["a", "b"], "b then a"),
        ("you said: $*", ["hi", "there"], "you said: hi there"),
        ("no placeholders", ["ignored"], "no placeholders"),
        # Missing arguments leave the placeholder alone, e.g. prices
        ("Entry costs $5", [], "Entry costs $5"),
        ("Entry costs $5", ["x"], "Entry costs $5"),
        ("all: $*", [], "all: $*"),
        ("$10 and $1", [str(n) for n in range(1, 11)], "10 and 1"),
        ("$0 is not a parameter", ["x"], "$0 is not a parameter"),
        # An argument that looks like a placeholder is not filled in again
        ("$1 $2", ["$2", "b"], "$2 b"),
    ],
)
def test_fill_parameters(reply, arguments, expected):
    assert ccu.fill_parameters(reply, arguments) == expected
