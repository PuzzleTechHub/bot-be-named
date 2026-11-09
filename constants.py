###############
# DISCORD BOT #
###############
DEFAULT_BOT_PREFIX = "~"
EMBED_COLOR = 0xD4E4FF


DEFAULT_COMMANDS = []

# File size restriction
BYTES_TO_MEGABYTES = 1_048_576  # 1024 squared
HARDCODED_FILE_SIZE = 10_485_760

############
# DATABASE #
############

# Server id that global custom commands are stored under, in the database and in the cache.
# server_id is a BIGINT, and no real Discord server has a negative id.
DB_GLOBAL = -1
