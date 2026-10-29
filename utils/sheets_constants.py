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
        "update_ans": True,
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

# Overview tab columns (row 3 is the header row, puzzles start on row 4)
DISCORD_CHANNEL_ID_COLUMN = "A"
SHEET_TAB_ID_COLUMN = "B"
ROUND_COLUMN = "C"
NOTES_COLUMN = "G"
PUZZLE_UNLOCKED_TIMESTAMP_COLUMN = "I"
PUZZLE_SOLVED_TIMESTAMP_COLUMN = "J"

# Overview cells that hold a column letter, so these columns can be moved on the sheet
PUZZLE_NAME_COLUMN_LOCATION = "A1"  # holds "D" by default
STATUS_COLUMN_LOCATION = "B1"  # holds "E" by default
ANSWER_COLUMN_LOCATION = "A2"  # holds "F" by default

# Overview cell with the hunt URL
OVERVIEW_HUNTURL_LOCATION = "C1"

# Puzzle tab cells, copied from the Template tab
TAB_CHAN_NAME_LOCATION = "A1"  # puzzle name
TAB_URL_LOCATION = "B1"  # puzzle link
TAB_ANSWER_LOCATION = "B3"  # answer, next to the "Answer" label in A3

PUZZLE_UNLOCKED_TIMESTAMP_COLUMN = "I"
PUZZLE_SOLVED_TIMESTAMP_COLUMN = "J"
