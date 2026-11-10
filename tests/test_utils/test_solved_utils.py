import pytest

from utils import solved_utils


class FakeChannel:
    """add_prefix and remove_prefix call str(channel), like a nextcord channel."""

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name


def test_add_prefix_to_plain_name():
    assert solved_utils.add_prefix(FakeChannel("puzzle"), "solved-") == "solved-puzzle"


def test_add_prefix_already_there():
    assert solved_utils.add_prefix(FakeChannel("solved-puzzle"), "solved-") is None


@pytest.mark.parametrize(
    "name, prefix, expected",
    [
        ("solved-x", "backsolved-", "backsolved-x"),
        ("solvedish-x", "solved-", "solved-x"),
    ],
)
def test_add_prefix_swaps_other_prefix(name, prefix, expected):
    assert solved_utils.add_prefix(FakeChannel(name), prefix) == expected


def test_remove_prefix():
    assert solved_utils.remove_prefix(FakeChannel("solved-puzzle"), "solved-") == (
        "puzzle"
    )


def test_remove_prefix_missing():
    assert solved_utils.remove_prefix(FakeChannel("puzzle"), "solved-") is None
