import asyncio
import urllib.parse

import aiohttp
import pytest
from aiohttp import web

from modules.lookup import cog as lookup
from tests.fakes import FakeChannel, FakeContext, FakeGuild, check_embed
from utils import paging_utils

FORM = "<form action='' method=get><input type=search name=q value='x'></form>\n"


def results_page(words, note=None):
    """A page shaped like nutrimatic.org's, scores falling from 4.0."""
    spans = "".join(
        f"<span style='font-size: {4 - n * 0.01:.6f}em'>{word}</span><br>\n"
        for n, word in enumerate(words)
    )
    tail = f"<p><b>{note}</b></p>" if note else "<p><a href='?start=100'>page 2</a></p>"
    return f"<html><body>{FORM}{spans}{tail}</body></html>"


def _ctx():
    return FakeContext(FakeGuild(), FakeChannel(201, "puzzle-1"))


@pytest.fixture
def cog():
    return lookup.LookupCog(None)


@pytest.fixture
def serve(monkeypatch):
    """Points fetch_page's URL at a fake page; returns the URLs it was asked for."""
    asked = []

    def use(page=None, error=None):
        async def fetch_page(url):
            asked.append(url)
            if error is not None:
                raise error
            return page

        monkeypatch.setattr(lookup, "fetch_page", fetch_page)
        return asked

    return use


# Parsing


def test_parse_reads_results_and_scores():
    results, message = lookup.parse_nutrimatic(results_page(["asymptote", "a b"]))
    assert results == [("asymptote", 4.0), ("a b", 3.99)]
    assert message is None


def test_parse_reads_the_closing_note():
    page = results_page(["cat"], note="No more results found.")
    assert lookup.parse_nutrimatic(page) == ([("cat", 4.0)], "No more results found.")


def test_parse_reads_a_syntax_error_without_its_markup():
    page = (
        f"<html><body>{FORM}<p><b><font color=red>error: can&#x27;t parse "
        "&quot;(ab&quot;</font></b></p></body></html>"
    )
    assert lookup.parse_nutrimatic(page) == ([], 'error: can\'t parse "(ab"')


def test_parse_of_an_unexpected_page_does_not_crash():
    assert lookup.parse_nutrimatic("<html>502 Bad Gateway</html>") == ([], None)


def test_url_encodes_the_query():
    url = lookup.nutrimatic_url("a&b #c+<d>")
    query = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
    assert query == {"q": ["a&b #c+<d>"], "go": ["Go"]}


# Pages


def test_pages_hold_fifteen_results_and_the_note_goes_last():
    results = [(f"word{n}", 1.0) for n in range(40)]
    pages = lookup.nutrimatic_pages("q", "https://x", results, "No more results.")
    assert len(pages) == 3
    assert [len(page.description.splitlines()) for page in pages] == [15, 15, 11]
    assert pages[-1].description.endswith("No more results.")
    assert pages[0].footer.text == "Query: q • Page 1/3"
    for page in pages:
        check_embed(page)


def test_a_single_page_has_no_page_number():
    [page] = lookup.nutrimatic_pages("q", "https://x", [], "No results found, sorry.")
    assert page.description == "No results found, sorry."
    assert page.footer.text == "Query: q"


# The command


async def test_full_page_of_results_is_one_message_with_buttons(cog, serve):
    asked = serve(results_page([f"word{n}" for n in range(100)]))
    ctx = _ctx()

    await cog.nutrimatic.callback(cog, ctx, query="`<asympote_>`")

    assert asked == [lookup.nutrimatic_url("<asympote_>")]
    [message] = ctx.sent
    assert isinstance(message.view, paging_utils.PageView)
    assert len(message.view.embeds) == 7
    assert message.embed.url == asked[0]
    assert message.embed.description.splitlines()[0] == "word0....................4.0"


async def test_no_results_is_one_message_without_buttons(cog, serve):
    serve(results_page([], note="No results found, sorry."))
    ctx = _ctx()

    await cog.nutrimatic.callback(cog, ctx, query="qxzj")

    [message] = ctx.sent
    assert message.view is None
    assert message.embed.description == "No results found, sorry."


@pytest.mark.parametrize("error", [aiohttp.ClientError(), asyncio.TimeoutError()])
async def test_nutrimatic_down_says_so(cog, serve, error):
    serve(error=error)
    ctx = _ctx()

    await cog.nutrimatic.callback(cog, ctx, query="c*t")

    [embed] = ctx.sent_embeds
    assert embed.fields[0].name == "Failed"
    assert "nutrimatic.org didn't answer" in embed.fields[0].value


async def test_empty_query_shows_an_example(cog, serve):
    asked = serve("")
    ctx = _ctx()
    ctx.prefix = "~"

    await cog.nutrimatic.callback(cog, ctx, query="``")

    assert asked == []
    [embed] = ctx.sent_embeds
    assert "~nut <asympote_>" in embed.fields[0].value


# fetch_page against a real local server


@pytest.fixture
async def server():
    """A local web server: /page answers, /moved redirects to /page, /slow never answers."""
    hang = asyncio.Event()

    async def page(request):
        return web.Response(text=results_page(["cat"]), content_type="text/html")

    async def moved(request):
        raise web.HTTPFound("/page")

    async def slow(request):
        await hang.wait()

    app = web.Application()
    app.add_routes(
        [web.get("/page", page), web.get("/moved", moved), web.get("/slow", slow)]
    )
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]
    yield f"http://127.0.0.1:{port}"
    hang.set()
    await runner.cleanup()


async def test_fetch_page_follows_redirects(server):
    """nutrimatic.org/ redirects to its current version, e.g. /2024/."""
    page = await lookup.fetch_page(server + "/moved")
    assert lookup.parse_nutrimatic(page) == ([("cat", 4.0)], None)


async def test_fetch_page_gives_up_after_the_timeout(server, monkeypatch):
    monkeypatch.setattr(lookup, "NUTRIMATIC_TIMEOUT", 0.2)
    with pytest.raises(asyncio.TimeoutError):
        await lookup.fetch_page(server + "/slow")
