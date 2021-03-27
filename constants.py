###################
## DISCORD BOT ####
###################
BOT_PREFIX = "~"
EMBED_COLOR = 0xd4e4ff
BOT_NAME = "The Bot Who Must Not Be Named"

# Roles
BOT_WHISPERER = "bot-whisperer"
VERIFIED_PUZZLER = 'verified-puzzler'

# Command success/fail
SUCCESS = "Success"
FAILED = "Failed"

####################
## GOOGLE SHEETS ###
####################

JSON_PARAMS = ["type", "project_id", "private_key_id", "private_key", "client_email", "client_id", "auth_uri",
               "token_uri", "auth_provider_x509_cert_url", "client_x509_cert_url"]

####################
## CIPHER RACE #####
####################

TIME_LIMIT = 60
BREAK_TIME = 30
BONUS_TIME = 10
NUM_LEVELS = 5
# Google Sheet
ID = "ID"
URL = "URL"
CODE = "code"
ANSWER = "Answer"
COLUMNS = [ID, URL, CODE, ANSWER]
# Answer responses
ANSWERS = 'answers'
LEVEL = 'level'
CORRECT = "Correct"
INCORRECT = "Incorrect"
CORRECT_EMOJI = ":white_check_mark:"
INCORRECT_EMOJI = ":x:"
HINT = "hint"
# Codes
PIGPEN = 'pigpen'
SEMAPHORE = 'semaphore'
MORSE = 'morse'
BRAILLE = 'braille'
CIPHERS = [PIGPEN, SEMAPHORE, MORSE, BRAILLE]
# Wordlists
HP = 'hp'
COMMON = 'common'
CHALLENGE = 'challenge'
SHEETS = [HP, COMMON, CHALLENGE]

########################
#### ARCHIVE CHANNEL ###
########################

ARCHIVE = 'archive'
IMAGES = 'images'
TEXT_LOG_PATH = 'text_log.txt'

################
#### SOLVED ####
################

SOLVED_PREFIX = 'solved'
SOLVEDISH_PREFIX = 'solvedish'
BACKSOLVED_PREFIX = 'backsolved'

################
#### LOOKUP ####
################

PAUSE_TIME= 1
QUERY_NUM = 10
DCODE = 'dcode'
DCODE_FR = 'dcode.fr'
WIKI = 'wiki'
WIKIPEDIA = 'wikipedia'
GOOGLE = 'google'
HPWIKI = 'hp'
HPWIKISITE = 'harrypotter.fandom.com/wiki'
REGISTERED_SITES = {
    DCODE: DCODE_FR,
    WIKI: WIKIPEDIA,
    GOOGLE: GOOGLE,
    HPWIKI: HPWIKISITE
}

################
##### HELP #####
################

HELP = 'Help'
CIPHER_RACE = 'Cipher Race'
CIPHER_RACE_README = 'https://github.com/kevslinger/DiscordCipherRace/tree/main/modules/code'
CREATE_CHANNEL = 'Create Channel'
CREATE_CHANNEL_README = 'https://github.com/kevslinger/DiscordCipherRace/tree/main/modules/create_channel'
MOVE_CHANNEL = 'Move Channel'
MOVE_CHANNEL_README = 'https://github.com/kevslinger/DiscordCipherRace/tree/main/modules/move_channel'
SOLVED = 'Solved'
SOLVED_README = 'https://github.com/kevslinger/DiscordCipherRace/tree/main/modules/solved'
ARCHIVE_CHANNEL = 'Archive Channel'
ARCHIVE_CHANNEL_README = 'https://github.com/kevslinger/DiscordCipherRace/tree/main/modules/archive_channel'
LOOKUP = 'Lookup'
LOOKUP_README = 'https://github.com/kevslinger/DiscordCipherRace/tree/main/modules/lookup'
MODULES = [CIPHER_RACE, CREATE_CHANNEL, MOVE_CHANNEL, SOLVED, ARCHIVE_CHANNEL, LOOKUP]
