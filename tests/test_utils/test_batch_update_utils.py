import pytest

from utils.batch_update_utils import BatchUpdateBuilder


def _only_request(builder):
    [request] = builder.build()["requests"]
    return request


def test_empty_build():
    assert BatchUpdateBuilder().build() == {"requests": []}


def test_requests_kept_in_order():
    builder = BatchUpdateBuilder()
    builder.unhide_sheet(1)
    builder.rename_sheet(2, "Puzzle")
    builder.duplicate_sheet(3)
    kinds = [next(iter(request)) for request in builder.build()["requests"]]
    assert kinds == ["updateSheetProperties", "updateSheetProperties", "duplicateSheet"]


def test_duplicate_sheet():
    builder = BatchUpdateBuilder()
    builder.duplicate_sheet(
        5, insert_sheet_index=2, new_sheet_id=9, new_sheet_name="New"
    )
    assert _only_request(builder) == {
        "duplicateSheet": {
            "sourceSheetId": 5,
            "insertSheetIndex": 2,
            "newSheetId": 9,
            "newSheetName": "New",
        }
    }


def test_duplicate_sheet_defaults_to_none():
    builder = BatchUpdateBuilder()
    builder.duplicate_sheet(5)
    request = _only_request(builder)["duplicateSheet"]
    assert request["sourceSheetId"] == 5
    assert request["insertSheetIndex"] is None
    assert request["newSheetId"] is None
    assert request["newSheetName"] is None


def test_unhide_sheet():
    builder = BatchUpdateBuilder()
    builder.unhide_sheet(7)
    assert _only_request(builder) == {
        "updateSheetProperties": {
            "properties": {"sheetId": 7, "hidden": False},
            "fields": "hidden",
        }
    }


def test_rename_sheet():
    builder = BatchUpdateBuilder()
    builder.rename_sheet(7, "Solved puzzle")
    assert _only_request(builder) == {
        "updateSheetProperties": {
            "properties": {"sheetId": 7, "title": "Solved puzzle"},
            "fields": "title",
        }
    }


def test_color_update_scales_to_0_1():
    builder = BatchUpdateBuilder()
    builder.color_update(7, (255, 0, 51))
    request = _only_request(builder)["updateSheetProperties"]
    assert request["fields"] == "tabColor"
    assert request["properties"]["sheetId"] == 7
    assert request["properties"]["tabColor"] == {"red": 1.0, "green": 0.0, "blue": 0.2}


@pytest.mark.parametrize(
    "is_formula, key", [(False, "stringValue"), (True, "formulaValue")]
)
def test_update_cell_by_index(is_formula, key):
    builder = BatchUpdateBuilder()
    builder.update_cell_by_index(
        7,
        column_index=2,
        row_index=4,
        value="x",
        is_formula=is_formula,
    )
    request = _only_request(builder)["updateCells"]
    assert request["fields"] == "userEnteredValue"
    assert request["rows"] == [{"values": [{"userEnteredValue": {key: "x"}}]}]
    assert request["start"] == {"sheetId": 7, "rowIndex": 4, "columnIndex": 2}


@pytest.mark.parametrize(
    "label, column_index, row_index", [("A1", 0, 0), ("C5", 2, 4), ("AA10", 26, 9)]
)
def test_update_cell_by_label_is_zero_indexed(label, column_index, row_index):
    builder = BatchUpdateBuilder()
    builder.update_cell_by_label(7, label, "=1+1", is_formula=True)
    request = _only_request(builder)["updateCells"]
    assert request["start"] == {
        "sheetId": 7,
        "rowIndex": row_index,
        "columnIndex": column_index,
    }
    assert request["rows"][0]["values"][0]["userEnteredValue"] == {
        "formulaValue": "=1+1"
    }
