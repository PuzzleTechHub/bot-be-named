##################
##### SHEETS #####
##################

# Put column names for tether sheet here
CATEGORY_TAB = "Category Tethers"

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
    "Unstarted": {"color": [217, 217, 217], "update_ans": False, "prefix": False},
    "Unsolvable": {"color": [102, 102, 102], "update_ans": False, "prefix": False},
    "Stuck": {"color": [255, 255, 135], "update_ans": False, "prefix": False},
    "Abandoned": {"color": [102, 102, 102], "update_ans": False, "prefix": False},
    "In Progress": {"color": [230, 145, 56], "update_ans": False, "prefix": False},
    "None": {"color": [230, 145, 56], "update_ans": True, "prefix": False},
}

# ["solved","solvedish","backsolved"...]
solved_prefixes = [
    y for y in [status_dict[x].get("prefix_name") for x in status_dict] if y is not None
]
