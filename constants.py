###############
# DISCORD BOT #
###############
DEFAULT_BOT_PREFIX = "~"
EMBED_COLOR = 0xd4e4ff
BOT_NAME = "The Bot Who Must Not Be Named"
PREFIX_JSON_FILE = "command_prefixes.json"
PREFIX_TAB_NAME = "Command Prefixes"
VERIFIED_TAB_NAME = "Verified Roles"

# Roles
# TODO: Use role ID instead of string?
BOT_WHISPERER = "bot-whisperer"
VERIFIED_PUZZLER = "Verified Puzzler"
ARITHMANCY_BOT_WHISPERER_ROLE_ID = 817232692117504072
ARITHMANCY_TASK_ROLE_ID = 817232692117504072
ARITHMANCY_VERIFIED_ROLE_ID = 737471501841727529
TA_VERIFIED_PUZZLER_ROLE_ID = 812906479794520135
SONI_SERVER_TESTER_ROLE = 799271918845952001
KEV_SERVER_TESTER_ROLE = 838034207157518367

VERIFIED = [TA_VERIFIED_PUZZLER_ROLE_ID,SONI_SERVER_TESTER_ROLE,KEV_SERVER_TESTER_ROLE]
ROLELIST = ["Verified","Bot Whisperer"]
VERIFIEDS = {}


# Command success/fail
SUCCESS = "Success"
FAILED = "Failed"

###########
# MODULES #
###########
ADMIN = "Admin"
ARCHIVE = "Archive"
CHANNEL_MANAGEMENT = "Channel Management"
CIPHER_RACE = "Cipher Race"
DISCORD = "Discord"
LOOKUP = "Lookup"
MUSIC_RACE = "Music Race"
PERFECT_PITCH = "Perfect Pitch"
SHEETS = "Sheets"
SOLVED = "Solved"
TIME = "Time"

MODULES_DIR = "modules"
MODULES = [ADMIN, ARCHIVE, CHANNEL_MANAGEMENT, CIPHER_RACE, DISCORD, LOOKUP, MUSIC_RACE, PERFECT_PITCH, SHEETS, SOLVED, TIME]

#################
# GOOGLE SHEETS #
#################

JSON_PARAMS = ["type", "project_id", "private_key_id", "private_key", "client_email", "client_id", "auth_uri",
               "token_uri", "auth_provider_x509_cert_url", "client_x509_cert_url"]




