from types import SimpleNamespace

import nextcord

from tests.fakes import FakeChannel, FakeContext, FakeGuild, FakeMember
from utils import paging_utils


class FakeResponse:
    def __init__(self):
        self.edited = []
        self.messages = []

    async def edit_message(self, embed=None, view=None):
        self.edited.append(embed)

    async def send_message(self, content, ephemeral=False):
        self.messages.append((content, ephemeral))


def interaction(user_id):
    return SimpleNamespace(user=SimpleNamespace(id=user_id), response=FakeResponse())


def embeds(count):
    return [nextcord.Embed(title=f"Page {n}") for n in range(1, count + 1)]


def _ctx():
    return FakeContext(FakeGuild(), FakeChannel(201, "puzzle-1"), author=FakeMember())


async def test_one_page_is_sent_without_buttons():
    ctx = _ctx()
    [page] = embeds(1)
    await paging_utils.send_pages(ctx, [page])
    [message] = ctx.sent
    assert message.embed is page
    assert message.view is None


async def test_several_pages_get_buttons_from_the_first_page():
    ctx = _ctx()
    pages = embeds(3)
    await paging_utils.send_pages(ctx, pages)
    [message] = ctx.sent
    view = message.view
    assert isinstance(view, paging_utils.PageView)
    assert message.embed is pages[0]
    assert view.message is message
    assert view.author_id == ctx.author.id
    assert view.previous_button.disabled
    assert not view.next_button.disabled


async def test_buttons_step_through_and_stop_at_the_ends():
    pages = embeds(3)
    view = paging_utils.PageView(1, pages)
    press = interaction(1)
    await view.next_page(press)
    await view.next_page(press)
    await view.next_page(press)
    assert view.index == 2
    assert press.response.edited == [pages[1], pages[2], pages[2]]
    assert view.next_button.disabled
    await view.previous_page(press)
    assert view.index == 1
    assert not view.previous_button.disabled and not view.next_button.disabled


async def test_only_the_caller_can_press():
    view = paging_utils.PageView(1, embeds(2))
    assert await view.interaction_check(interaction(1))
    other = interaction(2)
    assert not await view.interaction_check(other)
    [(content, ephemeral)] = other.response.messages
    assert ephemeral
    assert content == paging_utils.PageView.not_owner_message


async def test_timeout_disables_buttons():
    ctx = _ctx()
    await paging_utils.send_pages(ctx, embeds(2))
    [message] = ctx.sent
    await message.view.on_timeout()
    assert all(item.disabled for item in message.view.children)
    assert message.edits == [{"view": message.view}]


async def test_every_button_has_a_custom_id():
    """Discord refuses a message whose buttons lack a custom_id."""
    view = paging_utils.PageView(1, embeds(2))
    components = [c for row in view.to_components() for c in row["components"]]
    assert len(components) == 2
    assert all(c.get("custom_id") for c in components)
