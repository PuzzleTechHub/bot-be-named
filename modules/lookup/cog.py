import html
import re
import urllib.parse

import aiohttp
import nextcord
from nextcord.ext import commands

from utils import discord_utils, paging_utils

"""
Lookup module. Nutrimatic and similar puzzle-hunt lookups.
"""

NUTRIMATIC_URL = "https://nutrimatic.org/"
# Seconds to wait for nutrimatic.org before giving up.
NUTRIMATIC_TIMEOUT = 60
# Results shown on each page of the reply.
RESULTS_PER_PAGE = 15

# Each result is <span style='font-size: 4.280885em'>word</span>, bigger = more likely
RESULT_RE = re.compile(r"<span style='font-size: ([\d.]+)em'>(.*?)</span>", re.S)
# Messages such as "No more results found." or a red "error: can't parse ..." are bold
MESSAGE_RE = re.compile(r"<b>(.*?)</b>", re.S)
TAG_RE = re.compile(r"<[^>]+>")


def nutrimatic_url(query: str) -> str:
    return NUTRIMATIC_URL + "?" + urllib.parse.urlencode({"q": query, "go": "Go"})


def parse_nutrimatic(page: str) -> tuple[list[tuple[str, float]], str | None]:
    """Reads a nutrimatic.org results page.

    Returns ([(result, score)], message), where message is the page's own note, like
    "No results found, sorry." or a syntax error, or None if it has none."""
    results = [
        (html.unescape(word), float(score)) for score, word in RESULT_RE.findall(page)
    ]
    messages = MESSAGE_RE.findall(page)
    message = html.unescape(TAG_RE.sub("", messages[-1])).strip() if messages else None
    return results, message or None


def nutrimatic_pages(
    query: str, url: str, results: list[tuple[str, float]], message: str | None
) -> list[nextcord.Embed]:
    """The reply: RESULTS_PER_PAGE results per embed, with the page's note at the end."""
    lines = [f"{word}{'.' * 20}{round(score, 3)}" for word, score in results]
    chunks = [
        lines[i : i + RESULTS_PER_PAGE] for i in range(0, len(lines), RESULTS_PER_PAGE)
    ] or [[]]
    if message:
        chunks[-1].append(message)

    embeds = []
    for number, chunk in enumerate(chunks, start=1):
        embed = nextcord.Embed(
            title="Your nutrimatic link",
            url=url,
            colour=nextcord.Colour.magenta(),
            description="\n".join(chunk) or "No results.",
        )
        footer = f"Query: {query}"
        if len(chunks) > 1:
            footer += f" • Page {number}/{len(chunks)}"
        embed.set_footer(text=footer[:2048])
        embeds.append(embed)
    return embeds


async def fetch_page(url: str) -> str:
    """Gets a page without blocking the bot. Raises aiohttp.ClientError or TimeoutError."""
    timeout = aiohttp.ClientTimeout(total=NUTRIMATIC_TIMEOUT)
    async with (
        aiohttp.ClientSession(timeout=timeout) as session,
        session.get(url) as response,
    ):
        response.raise_for_status()
        return await response.text()


class LookupCog(commands.Cog, name="Lookup"):
    """
    Nutrimatic and similar puzzle-hunt lookups.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="nutrimatic", aliases=["n", "nu", "nut", "nutri"])
    async def nutrimatic(self, ctx: commands.Context, *, query=None):
        """Searches nutrimatic.org for words and phrases matching a pattern.

        The most likely results come first. Use the buttons to see more.
        See https://nutrimatic.org for the pattern syntax.

        Usage: `~nutrimatic <asympote_>`
        Usage: `~nut c*t`
        """
        # Backticks are only Discord formatting, and nutrimatic has no use for backslashes
        query = (query or "").replace("`", "").replace("\\", "").strip()
        if not query:
            await discord_utils.send_failure(
                ctx, f"Give me a pattern to search, e.g. `{ctx.prefix}nut <asympote_>`"
            )
            return

        url = nutrimatic_url(query)
        try:
            page = await fetch_page(url)
        except (aiohttp.ClientError, TimeoutError):
            await discord_utils.send_failure(
                ctx,
                f"nutrimatic.org didn't answer. Try again later, or open the "
                f"[search]({url}) yourself.",
            )
            return

        results, message = parse_nutrimatic(page)
        await paging_utils.send_pages(
            ctx, nutrimatic_pages(query, url, results, message)
        )


def setup(bot):
    bot.add_cog(LookupCog(bot))
