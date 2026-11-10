import os

########################
#### ARCHIVE CHANNEL ###
########################

ARCHIVE = "archive"
MEDIA = "media"

#############################
### DISCORD CHAT EXPORTER ###
#############################

# Installed by scripts/install_dce.py. Set DCE_PATH in .env to use a copy somewhere else.
DCE_PATH = os.path.abspath(
    os.getenv("DCE_PATH")
    or os.path.join(
        "tools",
        "dce",
        "DiscordChatExporter.Cli.exe" if os.name == "nt" else "DiscordChatExporter.Cli",
    )
)
# Seconds before we give up on one export
DCE_TIMEOUT = 1800
# DCE lists channels that failed under this line in stderr
DCE_FAILED_HEADER = "Failed to export the following channel(s):"
