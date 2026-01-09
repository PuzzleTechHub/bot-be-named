# Message limits
SUMMARY_CHUNK_SIZE = 12  # number of fields per summary message (catsummary)

# Watch category limits
WATCH_DEFAULT_LIMIT = 100
WATCH_MAX_LIMIT = 250
HISTORY_FETCH_LIMIT = 100  # per-channel history fetch for watchcategory

# Confirmation timeouts
DELETE_CONFIRM_TIMEOUT = 15.0  # seconds to wait for confirmation reactions

# Category/channel limits
CATEGORY_CHANNEL_LIMIT = 50  # max channels in a category before creating a new archive

# Text preview lengths
OVERVIEW_DESC_PREVIEW = 100  # characters to show in category summary

# Sheet duplication offsets
TEMPLATE_DUPLICATE_INSERT_OFFSET = 2  # insert index offset when duplicating template

# Reactions
SUCCESS_REACTION = ":check_mark_button:"
CONFIRM_EMOJI = "✅"
CANCEL_EMOJI = "❌"

# Archive constants
ARCHIVE_REGEX_PATTERN = r"\s*Archive\s*\d*$"

# TM constants
TM_BOT_STREAM_CHANNEL_ID = None  # FIXME change this during hunt