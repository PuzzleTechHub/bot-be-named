import threading
import urllib.request

from modules.lookup.cog import LookupCog
from tests.fakes import FakeChannel, FakeContext, FakeGuild


class FakeResponse:
    def read(self):
        return b"<html><b>No results found.</b></html>"


async def test_nutrimatic_fetches_off_the_event_loop(monkeypatch):
    """A slow nutrimatic search used to freeze every other command."""
    on_loop = []

    def urlopen(url):
        on_loop.append(threading.current_thread() is threading.main_thread())
        return FakeResponse()

    monkeypatch.setattr(urllib.request, "urlopen", urlopen)
    cog = LookupCog(None)
    ctx = FakeContext(FakeGuild(), FakeChannel(201, "puzzle-1"))

    await cog.nutrimatic.callback(cog, ctx, query="<asympote_>")

    assert on_loop == [False]
    assert ctx.sent_embeds[-1].description == "No results found."
