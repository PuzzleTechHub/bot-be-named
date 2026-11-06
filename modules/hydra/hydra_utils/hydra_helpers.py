import gspread
import emoji
from utils import discord_utils, sheet_utils
import nextcord

"""Helper functions for hydra/cog.py. Holds small and reusable pieces of code. More sophisticated helpers to to
sheet_utils.py, discord_utils.py, etc."""

# ==============================
# INPUT / OUTPUT HELPERS
# ==============================


# ==============================
# HELPERS FOR GSHEETS
# ==============================


async def handle_gspread_error(ctx, e: gspread.exceptions.APIError, embed=None):
    """Centralized handler for gspread API errors."""
    if embed is None:
        embed = discord_utils.create_embed()

    error_json = e.response.json()
    error_status = error_json.get("error", {}).get("status")
    error_message = error_json.get("error", {}).get("message", "")

    if (
        error_status == "BAD_REQUEST"
        and "columnIndex" in error_message
        and "is after last column" in error_message
    ):
        embed.add_field(
            name="Failed",
            value="Invalid Template!\n\n"
            f"The worksheet provided is missing required columns. \n"
            f"Visit the [BBN Server](discord.gg/x8f2ywHUky) to get the correct template. \n\n"
            f"Error: `{error_message}`",
            inline=False,
        )
    elif error_status == "PERMISSION_DENIED":
        embed.add_field(
            name="Failed",
            value="Could not update the Google Sheet because permission was denied.",
            inline=False,
        )
    else:
        embed.add_field(
            name="Failed",
            value=f"Unknown GSheets API Error - `{error_message}`",
            inline=False,
        )
    await discord_utils.send_message(ctx, embed)
    return embed


def get_sheet_keys(
    ctx, sheet_links
) -> tuple[list[str], list[str], nextcord.Embed | None]:
    """Turns sheet links into spreadsheet ids, without duplicates. When no links
    are provided, uses the tethered sheet. Returns (sheet_keys, bad_links, None) or ([], [], error_embed)
    if there's no tethered sheet."""
    if len(sheet_links) == 0:
        result, _ = sheet_utils.findsheettether(
            ctx.message.channel.category_id, ctx.message.channel.id
        )
        if result is None:
            return (
                [],
                [],
                create_failure_embed(
                    f"The channel {ctx.message.channel.mention} is not tethered to any Google sheet."
                ),
            )
        sheet_links = [str(result.sheet_link)]

    sheet_keys = []
    bad_links = []
    for link in sheet_links:
        try:
            sheet_key = gspread.utils.extract_id_from_url(link)
        except gspread.exceptions.NoValidUrlKeyFound:
            bad_links.append(link)
            continue
        if sheet_key not in sheet_keys:
            sheet_keys.append(sheet_key)
    return sheet_keys, bad_links, None


# ==============================
# HELPERS FOR DISCORD
# ==============================


def create_success_embed(message: str) -> nextcord.Embed:
    """Create a standardized success embed."""
    embed = discord_utils.create_embed()
    embed.add_field(
        name="Success",
        value=message,
        inline=False,
    )
    return embed


def create_failure_embed(message: str) -> nextcord.Embed:
    """Create a standardized failure embed."""
    embed = discord_utils.create_embed()
    embed.add_field(
        name="Failed",
        value=message,
        inline=False,
    )
    return embed


async def send_and_react_success(ctx, embed, reaction=":check_mark_button:"):
    """Send a message and react with a success reaction."""
    await ctx.message.add_reaction(emoji.emojize(reaction))
    await discord_utils.send_message(ctx, embed)


def get_ordinal_suffix(n: int) -> str:
    """Return the ordinal suffix for a number (1st, 2nd, 3rd, 4th, etc.)"""
    if 11 <= (n % 100) <= 13:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
