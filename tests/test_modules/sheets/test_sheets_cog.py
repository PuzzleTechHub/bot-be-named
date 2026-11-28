from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import constants
import database
from modules.sheets import cog as sheets_cog
from modules.sheets.cog import SheetsCog
from tests.fakes import (
    FakeCategory,
    FakeChannel,
    FakeContext,
    FakeGuild,
    FakeThread,
    add_tether,
    watch_threads,
)
from utils import google_utils, sheet_utils

CHANNEL_SHEET = "https://docs.google.com/spreadsheets/d/channel/edit"


@pytest.fixture
def cog(monkeypatch):
    monkeypatch.setattr(google_utils, "create_gspread_client", MagicMock())
    monkeypatch.setattr(google_utils, "get_gdrive_credentials", MagicMock())
    return SheetsCog(MagicMock())


async def test_showtether_in_thread_names_parent_channel(cog):
    channel = FakeChannel(201, "puzzle-1", FakeCategory(100, "GPH 1 Puzzles"))
    thread = FakeThread(300, "thread", channel)
    add_tether(201, CHANNEL_SHEET)
    ctx = FakeContext(FakeGuild(categories=[channel.category]), thread)
    await cog.displaysheettether.callback(cog, ctx)
    [embed] = ctx.sent_embeds
    assert embed.fields[0].name == "Result"
    assert f"The channel {channel.mention} is currently tethered" in (
        embed.fields[0].value
    )


async def test_removetether_without_category(cog):
    lone = FakeChannel(201, "lone")
    add_tether(201, CHANNEL_SHEET)
    ctx = FakeContext(FakeGuild(), lone)
    await cog.removesheettether.callback(cog, ctx)
    [embed] = ctx.sent_embeds
    assert embed.fields[0].name == "Success"


async def test_downloadsheet_without_category_or_tether(cog):
    """Used to crash on ctx.channel.category.id."""
    lone = FakeChannel(201, "lone")
    ctx = FakeContext(FakeGuild(), lone)
    await cog.downloadsheet.callback(cog, ctx)
    [embed] = ctx.sent_embeds
    assert embed.fields[0].value.startswith(
        f"There is no sheet tethered to {lone.mention}. You'll need"
    )


async def test_prune_tethers_removes_only_missing_channels(cog):
    category = FakeCategory(100, "GPH 1 Puzzles")
    channel = FakeChannel(201, "puzzle-1", category)
    thread = FakeThread(300, "thread", channel)
    guild = FakeGuild(categories=[category])
    guild.channels = [category, channel]
    guild.threads = [thread]
    cog.bot.guilds = [guild]
    for place_id in (100, 201, 300, 999, guild.id):
        add_tether(place_id, CHANNEL_SHEET)
    add_tether(555, CHANNEL_SHEET, server_id=42)  # a server the bot isn't in

    to_delete = await cog.prune_tethers.coro(cog)

    assert to_delete == [(guild.id, 999)]
    kept = {row.channel_or_cat_id for row in database.get_all_tethers()}
    assert kept == {100, 201, 300, 555, guild.id}


# Google calls and database queries run in worker threads, off the event loop


def _not_on_loop(calls):
    assert calls
    assert [name for name, on_loop in calls if on_loop] == []


@pytest.mark.parametrize("command", ["addsheettether", "addchannelsheettether"])
async def test_tether_commands_off_the_event_loop(cog, monkeypatch, command):
    channel = FakeChannel(201, "puzzle-1", FakeCategory(100, "GPH 1 Puzzles"))
    ctx = FakeContext(FakeGuild(categories=[channel.category]), channel)
    monkeypatch.setattr(
        sheet_utils,
        "addsheettethergeneric",
        lambda client, link, guild, place: MagicMock(url=CHANNEL_SHEET),
    )
    calls = watch_threads(monkeypatch, sheet_utils, "addsheettethergeneric")

    await getattr(cog, command).callback(cog, ctx, CHANNEL_SHEET)

    assert ctx.sent_embeds[-1].fields[0].name == "Success"
    _not_on_loop(calls)


async def test_removetether_off_the_event_loop(cog, monkeypatch):
    channel = FakeChannel(201, "puzzle-1", FakeCategory(100, "GPH 1 Puzzles"))
    add_tether(201, CHANNEL_SHEET)
    ctx = FakeContext(FakeGuild(categories=[channel.category]), channel)
    calls = watch_threads(monkeypatch, sheet_utils, "find_channel_tether")
    watch_threads(monkeypatch, database, "delete_tether", calls=calls)

    await cog.removesheettether.callback(cog, ctx)

    assert database.get_tether(201) is None
    assert [name for name, _ in calls] == ["find_channel_tether", "delete_tether"]
    _not_on_loop(calls)


async def test_downloadsheet_lookups_off_the_event_loop(cog, monkeypatch):
    channel = FakeChannel(201, "puzzle-1", FakeCategory(100, "GPH 1 Puzzles"))
    add_tether(201, CHANNEL_SHEET)
    ctx = FakeContext(FakeGuild(categories=[channel.category]), channel)
    monkeypatch.setattr(
        sheet_utils, "get_sheet_from_key_or_link", lambda client, link: None
    )
    calls = watch_threads(
        monkeypatch, sheet_utils, "find_channel_tether", "get_sheet_from_key_or_link"
    )

    await cog.downloadsheet.callback(cog, ctx)

    assert ctx.sent_embeds[-1].fields[0].value.startswith("I can't find that sheet")
    assert [name for name, _ in calls] == [
        "find_channel_tether",
        "get_sheet_from_key_or_link",
    ]
    _not_on_loop(calls)


async def test_prune_tethers_off_the_event_loop(cog, monkeypatch):
    guild = FakeGuild()
    guild.channels = []
    guild.threads = []
    cog.bot.guilds = [guild]
    add_tether(999, CHANNEL_SHEET)
    calls = watch_threads(monkeypatch, database, "get_all_tethers", "delete_tether")

    assert await cog.prune_tethers.coro(cog) == [(guild.id, 999)]

    assert [name for name, _ in calls] == ["get_all_tethers", "delete_tether"]
    _not_on_loop(calls)


# ~downloadsheet


class FileContext(FakeContext):
    """Also records files sent."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.files = []

    async def send(self, content=None, embed=None, view=None, file=None):
        if file is not None:
            self.files.append(file)
        return await super().send(content, embed, view)


@pytest.fixture
def exported(cog, monkeypatch, tmp_path):
    """~downloadsheet in an empty folder, with a sheet whose export is the bytes set
    on exported.data and whose title is exported.title."""
    monkeypatch.chdir(tmp_path)
    exported = SimpleNamespace(data=b"sheet bytes", title="GPH/Round 1")
    monkeypatch.setattr(
        sheet_utils,
        "get_sheet_from_key_or_link",
        lambda client, link: SimpleNamespace(id="abc", title=exported.title),
    )
    build = MagicMock()
    build.return_value.files.return_value.export_media.return_value.execute.side_effect = (
        lambda: exported.data
    )
    monkeypatch.setattr(sheets_cog.discovery, "build", build)
    return exported


def file_context():
    channel = FakeChannel(201, "puzzle-1", FakeCategory(100, "GPH 1 Puzzles"))
    return FileContext(FakeGuild(categories=[channel.category]), channel)


async def test_downloadsheet_title_with_slash(cog, exported, tmp_path):
    """Used to fail: the title went into the path, so "/" pointed at a missing folder."""
    ctx = file_context()
    await cog.downloadsheet.callback(cog, ctx, CHANNEL_SHEET)
    [file] = ctx.files
    assert file.filename == "GPH_Round 1.xlsx"
    [field] = ctx.sent[-1].embed.fields
    assert (field.name, field.value) == ("Success", sheets_cog.DOWNLOAD_NOTE)
    assert (tmp_path / "saved_sheets" / "sheet.xlsx").read_bytes() == b"sheet bytes"


async def test_downloadsheet_title_cannot_leave_the_folder(cog, exported, tmp_path):
    exported.title = "../../escape"
    ctx = file_context()
    await cog.downloadsheet.callback(cog, ctx, CHANNEL_SHEET)
    [file] = ctx.files
    assert file.filename == "_.._escape.xlsx"
    assert sorted(path.name for path in tmp_path.rglob("*")) == [
        "saved_sheets",
        "sheet.xlsx",
    ]


async def test_downloadsheet_too_big(cog, exported, monkeypatch, tmp_path):
    """The limit used to show as literal "{(...):.2f}MB" text."""
    monkeypatch.setattr(
        constants, "HARDCODED_FILE_SIZE", 2 * constants.BYTES_TO_MEGABYTES
    )
    exported.data = b"x" * (3 * constants.BYTES_TO_MEGABYTES)
    ctx = file_context()
    await cog.downloadsheet.callback(cog, ctx, CHANNEL_SHEET)
    assert ctx.files == []
    assert ctx.sent_embeds[-1].fields[0].value == (
        "Sorry, your sheet is 3.00MB big, but I can only send files of up to 2.00MB."
    )
    assert not (tmp_path / "saved_sheets").exists()


@pytest.mark.parametrize("too_big", [False, True])
async def test_downloadsheet_progress_message(cog, exported, monkeypatch, too_big):
    """A "Download in Progress" message is shown during the export and removed after,
    whether the sheet is sent or not."""
    if too_big:
        monkeypatch.setattr(constants, "HARDCODED_FILE_SIZE", 1)
    ctx = file_context()
    await cog.downloadsheet.callback(cog, ctx, CHANNEL_SHEET)
    progress = ctx.sent[0]
    assert progress.embed.fields[0].name == "Download in Progress"
    assert progress.embed.fields[0].value == (
        "Downloading **GPH/Round 1**. Please wait..."
    )
    assert progress.deleted
    assert len(ctx.files) == (0 if too_big else 1)


@pytest.mark.parametrize(
    "title, filename",
    [
        ("Puzzles", "Puzzles.xlsx"),
        ('a\\b:c*d?e"f<g>h|i', "a_b_c_d_e_f_g_h_i.xlsx"),
        ("  ..  ", "sheet.xlsx"),
        ("", "sheet.xlsx"),
    ],
)
def test_download_filename(title, filename):
    assert sheets_cog.download_filename(title) == filename
