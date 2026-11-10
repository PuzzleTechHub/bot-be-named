from types import SimpleNamespace

import pytest
from sqlalchemy.orm import Session

import database
from utils import sheet_utils, sheets_constants

SHEET_KEY = "1AbCdEfGhIjKlMnOpQrStUvWxYz0123456789"
OTHER_KEY = "1ZyXwVuTsRqPoNmLkJiHgFeDcBa9876543210"
CATEGORY_ID = 100
CHANNEL_ID = 200


def _link(key, suffix="/edit"):
    return f"https://docs.google.com/spreadsheets/d/{key}{suffix}"


def _tether(channel_or_cat_id, sheet_link):
    with Session(database.DATABASE_ENGINE) as session:
        session.add(
            database.SheetTethers(
                server_id=1,
                server_name="Test server",
                channel_or_cat_id=channel_or_cat_id,
                channel_or_cat_name="test",
                sheet_link=sheet_link,
            )
        )
        session.commit()


def _ctx():
    channel = SimpleNamespace(
        id=CHANNEL_ID, category_id=CATEGORY_ID, mention=f"<#{CHANNEL_ID}>"
    )
    return SimpleNamespace(message=SimpleNamespace(channel=channel))


# normalize_status


@pytest.mark.parametrize("status", list(sheets_constants.status_dict))
def test_normalize_status_any_case(status):
    assert sheet_utils.normalize_status(status.lower()) == status
    assert sheet_utils.normalize_status(status.upper()) == status
    assert sheet_utils.normalize_status(status) == status


def test_normalize_status_not_a_puzzle():
    assert sheet_utils.normalize_status("not a puzzle") == "Not a puzzle"


def test_normalize_status_unknown_unchanged():
    assert sheet_utils.normalize_status("Waiting on meta") == "Waiting on meta"


# get_new_puzzle_tab_index


def _tabs(*titles):
    return [SimpleNamespace(title=t, index=i) for i, t in enumerate(titles)]


def test_new_tab_goes_after_templates():
    tabs = _tabs("Overview", "Template", "Meta Template", "P1")
    assert sheet_utils.get_new_puzzle_tab_index(tabs) == 3


def test_new_tab_without_template_goes_last():
    tabs = _tabs("Overview", "P1", "P2")
    assert sheet_utils.get_new_puzzle_tab_index(tabs) == 3


def test_later_template_after_puzzle_tab_ignored():
    tabs = _tabs("Overview", "Template", "P1", "Old Template")
    assert sheet_utils.get_new_puzzle_tab_index(tabs) == 2


# findsheettether


def test_findsheettether_channel_beats_category():
    _tether(CATEGORY_ID, _link(OTHER_KEY))
    _tether(CHANNEL_ID, _link(SHEET_KEY))
    result, tether_type = sheet_utils.findsheettether(CATEGORY_ID, CHANNEL_ID)
    assert result.sheet_link == _link(SHEET_KEY)
    assert tether_type == sheets_constants.CHANNEL == "channel"


def test_findsheettether_falls_back_to_category():
    _tether(CATEGORY_ID, _link(OTHER_KEY))
    result, tether_type = sheet_utils.findsheettether(CATEGORY_ID, CHANNEL_ID)
    assert result.sheet_link == _link(OTHER_KEY)
    assert tether_type == sheets_constants.CATEGORY


def test_findsheettether_none():
    assert sheet_utils.findsheettether(CATEGORY_ID, CHANNEL_ID) == (
        None,
        "category",
    )


# get_sheet_keys


def test_get_sheet_keys_no_links_no_tether():
    keys, bad, embed = sheet_utils.get_sheet_keys(_ctx(), [])
    assert (keys, bad) == ([], [])
    assert embed.fields[0].name == "Failed"
    assert f"<#{CHANNEL_ID}>" in embed.fields[0].value


def test_get_sheet_keys_uses_tether():
    _tether(CATEGORY_ID, _link(SHEET_KEY))
    assert sheet_utils.get_sheet_keys(_ctx(), []) == ([SHEET_KEY], [], None)


def test_get_sheet_keys_dedupes_and_keeps_order():
    links = [
        _link(OTHER_KEY),
        "not a link",
        _link(SHEET_KEY, "/edit"),
        _link(OTHER_KEY, "/edit#gid=1"),
        _link(SHEET_KEY, "#gid=1"),
        "also bad",
    ]
    assert sheet_utils.get_sheet_keys(_ctx(), links) == (
        [OTHER_KEY, SHEET_KEY],
        ["not a link", "also bad"],
        None,
    )
