import asyncio
from types import SimpleNamespace

import nextcord
import pytest

from tests.fakes import FakeChannel, FakeContext, FakeGuild, FakeMember
from utils.paging_utils import Pages

FIRST, LEFT, RIGHT, STOP = "⏪", "◀", "▶", "❌"


class PagedMessage:
    """A sent message that records edits and reactions."""

    def __init__(self, message_id, embed):
        self.id = message_id
        self.embeds = [embed.description]
        self.reactions = []
        self.cleared = False

    async def edit(self, embed):
        self.embeds.append(embed.description)

    async def add_reaction(self, emoji):
        self.reactions.append(emoji)

    async def remove_reaction(self, reaction, user):
        pass

    async def clear_reactions(self):
        self.cleared = True


class PagedChannel(FakeChannel):
    def __init__(self):
        super().__init__(20, "lookup")
        self.messages = []

    async def send(self, embed):
        message = PagedMessage(500 + len(self.messages), embed)
        self.messages.append(message)
        return message


class FakeBot:
    """wait_for hands out queued reactions where each item is (emoji, user) or None for a timeout.
    Reactions that fail the check are skipped."""

    def __init__(self, pages_ref, queue):
        self.pages_ref = pages_ref
        self.queue = list(queue)

    async def wait_for(self, event, check, timeout):
        assert event == "reaction_add"
        while self.queue:
            item = self.queue.pop(0)
            if item is None:
                raise asyncio.TimeoutError
            emoji, user, *message_id = item
            message = self.pages_ref[0].message
            reaction = SimpleNamespace(
                emoji=emoji,
                message=SimpleNamespace(id=message_id[0] if message_id else message.id),
            )
            if check(reaction, user):
                return reaction, user
        raise asyncio.TimeoutError


def _pages(solutions, queue=(), weights=None, endflag=None, author=None):
    channel = PagedChannel()
    author = author or FakeMember()
    ctx = FakeContext(FakeGuild(), channel, author)
    ref = []
    ctx.bot = FakeBot(ref, queue)
    pages = Pages(
        ctx,
        solutions=solutions,
        weights=weights,
        embedTemp=nextcord.Embed(title="Results"),
        endflag=endflag,
    )
    ref.append(pages)
    return pages, channel, author


SOLUTIONS = [f"word{n}" for n in range(1, 41)]  # 40 results, 15 per page


# extractData


def test_first_page():
    pages, _, _ = _pages(SOLUTIONS)
    assert pages.extractData().split("\n") == SOLUTIONS[:15]


def test_last_page_partial():
    pages, _, _ = _pages(SOLUTIONS)
    pages.page = 3
    assert pages.extractData().split("\n") == SOLUTIONS[30:]


def test_page_past_the_end_steps_back():
    pages, _, _ = _pages(SOLUTIONS)
    pages.page = 4
    assert pages.extractData().split("\n") == SOLUTIONS[30:]
    assert pages.page == 3


def test_weights_shown_rounded():
    pages, _, _ = _pages(["alpha", "beta"], weights=[0.123456, 2])
    assert pages.extractData() == (
        "alpha....................0.123\nbeta....................2"
    )


def test_endflag_only_on_last_page():
    pages, _, _ = _pages(SOLUTIONS, endflag="-- end --")
    assert "-- end --" not in pages.extractData()
    pages.page = 3
    assert pages.extractData().endswith("\n-- end --")


def test_endflag_when_everything_fits():
    pages, _, _ = _pages(["alpha"], endflag="-- end --")
    assert pages.extractData() == "alpha\n-- end --"


# sendPage / pageLoop


async def test_send_page_sends_then_edits():
    pages, channel, _ = _pages(SOLUTIONS)
    await pages.sendPage()
    pages.page = 2
    await pages.sendPage()
    [message] = channel.messages
    assert pages.embed.title == "Results (pg:2)"
    assert message.embeds[1].split("\n") == SOLUTIONS[15:30]
    assert message.reactions[:4] == [FIRST, LEFT, RIGHT, STOP]


async def test_page_loop_navigation():
    author = FakeMember()
    pages, channel, _ = _pages(
        SOLUTIONS,
        queue=[
            (RIGHT, author),
            (RIGHT, author),
            (LEFT, author),
            (FIRST, author),
            (STOP, author),
        ],
        author=author,
    )
    await pages.pageLoop()
    [message] = channel.messages
    first_words = [embed.split("\n")[0] for embed in message.embeds]
    assert first_words == ["word1", "word16", "word31", "word16", "word1"]
    assert message.cleared
    assert pages.loopState is False


async def test_left_on_first_page_stays():
    author = FakeMember()
    pages, channel, _ = _pages(
        SOLUTIONS, queue=[(LEFT, author), (STOP, author)], author=author
    )
    await pages.pageLoop()
    assert pages.page == 1


async def test_page_loop_ignores_other_users_and_emoji():
    author = FakeMember(1)
    stranger = FakeMember(2)
    pages, channel, _ = _pages(
        SOLUTIONS,
        queue=[
            (RIGHT, stranger),
            ("\U0001f600", author),
            (RIGHT, author, 999),
            (STOP, author),
        ],
        author=author,
    )
    await pages.pageLoop()
    assert pages.page == 1
    assert len(channel.messages[0].embeds) == 1


async def test_page_loop_times_out():
    pages, channel, _ = _pages(SOLUTIONS, queue=[None])
    await pages.pageLoop()
    assert channel.messages[0].cleared
    assert pages.loopState is False


@pytest.mark.parametrize("presses, page", [(1, 2), (2, 3), (5, 3)])
async def test_right_stops_at_last_page(presses, page):
    author = FakeMember()
    queue = [(RIGHT, author)] * presses + [(STOP, author)]
    pages, channel, _ = _pages(SOLUTIONS, queue=queue, author=author)
    await pages.pageLoop()
    assert channel.messages[0].embeds[-1].split("\n")[0] == f"word{(page - 1) * 15 + 1}"
