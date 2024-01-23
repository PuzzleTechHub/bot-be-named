##################
##### SHEETS #####
##################
"""
See: sheet_utils.py
"""

THREAD = "thread"
CHANNEL = "channel"
CATEGORY = "category"

# Use for downloading sheets
MIMETYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

# status of all sheet/prefix constants. This order matters for ~sortcat.
status_dict = {
    "Solved": {
        "color": [106, 168, 79],
        "update_ans": True,
        "prefix": True,
        "prefix_name": "solved",
    },
    "Solvedish": {
        "color": [217, 234, 211],
        "update_ans": True,
        "prefix": True,
        "prefix_name": "solvedish",
    },
    "Backsolved": {
        "color": [60, 120, 216],
        "update_ans": True,
        "prefix": True,
        "prefix_name": "backsolved",
    },
    "Postsolved": {
        "color": [182, 215, 168],
        "update_ans": True,
        "prefix": True,
        "prefix_name": "postsolved",
    },
    "Unstarted": {
        "color": [217, 217, 217],
        "update_ans": False,
        "prefix": False,
    },
    "Unsolvable": {
        "color": [102, 102, 102],
        "update_ans": False,
        "prefix": False,
    },
    "Stuck": {
        "color": [255, 255, 135],
        "update_ans": False,
        "prefix": False,
    },
    "Abandoned": {
        "color": [102, 102, 102],
        "update_ans": False,
        "prefix": False,
    },
    "In Progress": {
        "color": [230, 145, 56],
        "update_ans": False,
        "prefix": False,
    },
    "None": {
        "color": [230, 145, 56],
        "update_ans": True,
        "prefix": False,
    },
}

UNSTARTED_NAME = "Unstarted"
# ["solved","solvedish","backsolved"...]
solved_prefixes = [status_dict[x].get("prefix_name") for x in status_dict]
solved_prefixes = [y for y in solved_prefixes if y is not None]

DISCORD_CHANNEL_ID_COLUMN = "A"
SHEET_TAB_ID_COLUMN = "B"
OVERVIEW_COLUMN = "G"

PUZZLE_NAME_COLUMN_LOCATION = "A1"  # C in TM sheet
STATUS_COLUMN_LOCATION = "B1"  # D in TM sheet
ANSWER_COLUMN_LOCATION = "A2"  # E in TM sheet

TAB_CHAN_NAME_LOCATION = "A1"
TAB_URL_LOCATION = "B1"
TAB_ANSWER_LOCATION = "B3"

# To be used in chanhydra, clonehydra and hunthydra
OVERVIEW_HUNTURL_LOCATION = "C1"
