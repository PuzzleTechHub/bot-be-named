from modules.error_logging import error_constants
from datetime import datetime
from nextcord import Webhook
import aiohttp
import os

"""
Logging utils. Sends errors to log and to a specific private webhook used for BBN errors and command usage.
Used by all modules.
"""

webhook_url = os.getenv("WEBHOOK_URL")
session = aiohttp.ClientSession()
webhook = None
if webhook_url is not None and webhook_url != "":
    webhook = Webhook.from_url(webhook_url, session=session)


def log_to_file(filename: str, text: str):
    """Appends the message to the log file"""
    with open(filename, "a") as f:
        f.write(f"[ {datetime.now().strftime('%m-%d-%Y, %H:%M:%S')} ] {text}\n\n")


async def send_to_webhook(text: str):
    """Send log to webhook"""
    if webhook is not None:
        await webhook.send(text)
    log_to_file(error_constants.ERROR_WEBHOOKFILE, text)


async def log_command(command: str, guild, channel, author: str) -> None:
    """Log the command used, what channel it's in, and who used it"""
    if not hasattr(guild, "name"):
        text = f"Received `{command}` from `{author}` in DMs"
    else:
        text = f"Received `{command}` from `{author}` in `{guild.name}` : `#{channel.name}`"
    print(f"[ {datetime.now().strftime('%m-%d-%Y, %H:%M:%S')} ] {text}")
    try:
        await send_to_webhook(text)
    except Exception:
        print("Webhook failed")


async def close_session():
    session.close()
