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

status_dict = {
    "Solved": {"color": [106, 168, 79], "update_ans": True, "prefix": True},
    "Solvedish": {"color": [217, 234, 211], "update_ans": True, "prefix": True},
    "Backsolved": {"color": [60, 120, 216], "update_ans": True, "prefix": True},
    "Postsolved": {"color": [182, 215, 168], "update_ans": True, "prefix": True},
    "Unstarted": {"color": [217, 217, 217], "update_ans": False, "prefix": False},
    "Unsolvable": {"color": [102, 102, 102], "update_ans": False, "prefix": False},
    "Stuck": {"color": [255, 255, 135], "update_ans": False, "prefix": False},
    "Abandoned": {"color": [102, 102, 102], "update_ans": False, "prefix": False},
    "In Progress": {"color": [230, 145, 56], "update_ans": False, "prefix": False},
    "None": {"color": [230, 145, 56], "update_ans": True, "prefix": True},
}
