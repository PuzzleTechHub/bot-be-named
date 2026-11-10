import pytest

from utils import sheets_constants

REQUIRED_KEYS = {"color", "is_solve", "prefix", "update_ans"}


@pytest.mark.parametrize("status", list(sheets_constants.status_dict))
def test_status_has_required_fields(status):
    info = sheets_constants.status_dict[status]
    assert REQUIRED_KEYS <= info.keys()
    if info["prefix"]:
        assert info.get("prefix_name")


def test_solve_statuses():
    assert sheets_constants.solve_statuses == ["Solved", "Backsolved", "Postsolved"]
