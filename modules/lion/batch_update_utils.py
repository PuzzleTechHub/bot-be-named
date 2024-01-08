import googleapiclient
import json
import gspread

class BatchUpdateBuilder:
    def __init__(self):
        self.requests = []

    def duplicate_sheet(
        self,
        source_sheet_id,
        insert_sheet_index=None,
        new_sheet_id=None,
        new_sheet_name=None,
    ):
        self.requests.append(
            {
                "duplicateSheet": {
                    "sourceSheetId": source_sheet_id,
                    "insertSheetIndex": insert_sheet_index,
                    "newSheetId": new_sheet_id,
                    "newSheetName": new_sheet_name,
                }
            }
        )

    def update_cell_by_label(self, sheet_id, label, value, is_formula=False):
        row,col = gspread.utils.a1_to_rowcol(label)
        self.update_cell_by_index(
            sheet_id=sheet_id, 
            column_index=col - 1,
            row_index=row - 1,
            value=value,
            is_formula=is_formula
        )

    def update_cell_by_index(self, sheet_id, column_index, row_index, value, is_formula=False):
        self.requests.append(
            {
                "updateCells": {
                    "fields": "userEnteredValue",
                    "rows": [
                        {
                            "values": [
                                {
                                    "userEnteredValue": {
                                        (
                                            "formulaValue"
                                            if is_formula
                                            else "stringValue"
                                        ): value
                                    }
                                }
                            ]
                        }
                    ],
                    "start": {
                        "sheetId": sheet_id,
                        "columnIndex": column_index,
                        "rowIndex": row_index,
                    }
                    # "range": {
                    #     "sheetId": sheet_id,
                    #     "startColumnIndex": column_index,
                    #     "startRowIndex": row_index,
                    #     "endColumnIndex": column_index,
                    #     "endRowIndex": row_index
                    # }
                }
            }
        )

    def color_update(self, sheet_id, color):
        self.requests.append(
            {
                "updateSheetProperties": {
                    "properties": {
                        "sheetId": sheet_id,
                        "tabColor": {
                            "red": color[0] / 255,
                            "green": color[1] / 255,
                            "blue": color[2] / 255,
                        },
                    },
                    "fields": "tabColor",
                }
            }
        )

    def build(self):
        result = {"requests": self.requests}
        print(result)
        return result