import os
import zipfile
from unittest.mock import AsyncMock, MagicMock

import nextcord
import pytest

from modules.archive import archive_constants, archive_utils
from modules.archive.cog import ArchiveCog


@pytest.mark.parametrize(
    "name, expected",
    [
        ("puzzle-1", "puzzle-1"),
        ("Puzzle 1/2", "Puzzle 1_2"),
        ("what? *really*", "what_ _really_"),
        ('a:b<c>d|e"f\\g', "a_b_c_d_e_f_g"),
        ("..", "channel"),
        ("", "channel"),
        ("x" * 200, "x" * 80),
    ],
)
def test_safe_filename(name, expected):
    assert archive_utils.safe_filename(name) == expected


def test_safe_filename_can_be_zipped(tmp_path):
    # The names from the bug: these used to raise FileNotFoundError / OSError
    for name in ["Puzzle 1/2", "what? *really*", "🧩 emoji: thread"]:
        path = os.path.join(
            tmp_path, f"{archive_utils.safe_filename(name)}_archive.zip"
        )
        zipfile.ZipFile(path, "w").close()
        assert os.path.exists(path)


def test_zip_path_for_uses_safe_name(monkeypatch):
    monkeypatch.setattr(archive_constants, "ARCHIVE", "archive")
    channel = MagicMock()
    channel.name = "Puzzle 1/2"
    assert ArchiveCog.zip_path_for(channel, "archive") == os.path.join(
        "archive", "Puzzle 1_2_archive.zip"
    )


def test_list_for_embed_short_list_unchanged():
    assert archive_utils.list_for_embed(["a", "b", "c"]) == "a\nb\nc"


def test_list_for_embed_caps_long_list():
    names = [f"puzzle-channel-{i}" for i in range(107)]
    text = archive_utils.list_for_embed(names)
    assert len(text) <= 1024
    lines = text.split("\n")
    shown = len(lines) - 1
    assert lines[:shown] == names[:shown]
    assert lines[-1] == f"...and {107 - shown} more"


def test_list_for_embed_exactly_at_limit():
    # Every cut-off must still fit, whatever the name lengths
    for length in (1, 7, 50, 100):
        for count in (1, 10, 30, 200):
            text = archive_utils.list_for_embed(["n" * length] * count)
            assert len(text) <= 1024


async def test_archive_many_channels_keeps_going_after_upload_error(monkeypatch):
    cog = ArchiveCog.__new__(ArchiveCog)
    monkeypatch.setattr(archive_utils, "reset_archive_dir", lambda: None)
    sent_errors = []

    async def fake_send_message(ctx, embed):
        sent_errors.append(embed)

    monkeypatch.setattr(
        "modules.archive.cog.discord_utils.send_message", fake_send_message
    )
    cog.archive_one_channel = AsyncMock(return_value=("out", "zip", 1, []))
    cog.get_file_and_embed = MagicMock(return_value=(MagicMock(), None))

    response = MagicMock(status=413, reason="Payload Too Large")
    ctx = MagicMock()
    ctx.guild.filesize_limit = 10
    ctx.prefix = "~"
    ctx.send = AsyncMock(
        side_effect=[nextcord.HTTPException(response, "too big"), None]
    )
    first, second = MagicMock(), MagicMock()
    first.mention, second.mention = "<#1>", "<#2>"

    await cog.archive_many_channels(ctx, [first, second], "the category")

    # The second channel was still archived and sent
    assert cog.archive_one_channel.await_count == 2
    assert ctx.send.await_count == 2
    assert len(sent_errors) == 1
    assert sent_errors[0].fields[0].name == "ERROR: Failed to send archive"
    assert "<#1>" in sent_errors[0].fields[0].value
