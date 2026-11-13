import asyncio
import os

import pytest

from modules.archive import archive_constants, archive_utils

FAILED = archive_constants.DCE_FAILED_HEADER


# get_delay_embed


def test_get_delay_embed():
    [field] = archive_utils.get_delay_embed().fields
    assert field.name == "Warning: Delay!"
    assert field.value is not None
    assert "may take a while" in field.value


# reset_archive_dir / dce_installed


def test_reset_archive_dir_empties_it(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    archive = tmp_path / archive_constants.ARCHIVE
    (archive / "old").mkdir(parents=True)
    (archive / "old" / "file.html").write_text("x")
    archive_utils.reset_archive_dir()
    assert archive.is_dir()
    assert list(archive.iterdir()) == []


def test_reset_archive_dir_creates_it(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    archive_utils.reset_archive_dir()
    assert (tmp_path / archive_constants.ARCHIVE).is_dir()


def test_dce_installed(tmp_path, monkeypatch):
    dce = tmp_path / "DiscordChatExporter.Cli"
    monkeypatch.setattr(archive_constants, "DCE_PATH", str(dce))
    assert not archive_utils.dce_installed()
    dce.write_text("")
    assert archive_utils.dce_installed()


def test_dce_folder_is_not_installed(tmp_path, monkeypatch):
    monkeypatch.setattr(archive_constants, "DCE_PATH", str(tmp_path))
    assert not archive_utils.dce_installed()


# first_error


def test_first_error_skips_header_and_stack():
    stderr = (
        "\nERROR\n"
        "DiscordChatExporter.Core.Exceptions.DiscordChatExporterException: "
        "Requested resource does not exist.\n"
        "   at DiscordChatExporter.Core.Discord.DiscordClient.GetJsonResponseAsync()\n"
    )
    assert archive_utils.first_error(stderr) == "Requested resource does not exist."


def test_first_error_plain_line():
    assert archive_utils.first_error("Access is forbidden.") == "Access is forbidden."


def test_first_error_capped():
    assert len(archive_utils.first_error("x" * 2000)) == 500


@pytest.mark.parametrize("stderr", ["", "\n\nERROR\n   at Foo()\n"])
def test_first_error_unknown(stderr):
    assert archive_utils.first_error(stderr) == "Unknown error"


# list_media


def test_list_media_biggest_first(tmp_path):
    media = tmp_path / archive_constants.MEDIA
    (media / "sub").mkdir(parents=True)
    (media / "small.png").write_bytes(b"x")
    (media / "sub" / "big.mp4").write_bytes(b"x" * 100)
    (media / "mid.jpg").write_bytes(b"x" * 10)
    (tmp_path / "channel.html").write_bytes(b"x" * 1000)  # not media

    assert archive_utils.list_media(str(tmp_path)) == [
        (os.path.join(archive_constants.MEDIA, "sub", "big.mp4"), 100),
        (os.path.join(archive_constants.MEDIA, "mid.jpg"), 10),
        (os.path.join(archive_constants.MEDIA, "small.png"), 1),
    ]


def test_list_media_no_media_folder(tmp_path):
    assert archive_utils.list_media(str(tmp_path)) == []


# run_export


class FakeProcess:
    def __init__(self, returncode=0, stderr="", hang=False):
        self.returncode = returncode
        self.stderr = stderr.encode()
        self.hang = hang
        self.killed = False

    async def communicate(self):
        if self.hang:
            await asyncio.sleep(10)
        return b"", self.stderr

    def kill(self):
        self.killed = True

    async def wait(self):
        return self.returncode


@pytest.fixture
def dce(monkeypatch):
    """Replaces the DCE subprocess. Set .process; .calls records (args, kwargs)."""

    class FakeDce:
        process = FakeProcess()
        calls = []

    fake = FakeDce()

    async def create_subprocess_exec(*args, **kwargs):
        fake.calls.append((args, kwargs))
        return fake.process

    monkeypatch.setattr(asyncio, "create_subprocess_exec", create_subprocess_exec)
    monkeypatch.setenv("DISCORD_TOKEN", "secret-token")
    return fake


async def test_run_export_arguments(dce, tmp_path):
    out_dir = str(tmp_path)
    assert await archive_utils.run_export(42, out_dir, False) == (0, "", [])
    [(args, kwargs)] = dce.calls
    assert args == (
        archive_constants.DCE_PATH,
        "export",
        "-c",
        "42",
        "--media",
        "--reuse-media",
        "--media-dir",
        os.path.join(out_dir, archive_constants.MEDIA),
        "-o",
        os.path.join(out_dir, "%C [%c].html"),
    )
    # Token is passed through the environment, never on the command line
    assert "secret-token" not in args
    assert kwargs["env"]["DISCORD_TOKEN"] == "secret-token"
    assert kwargs["env"]["FUCK_RUSSIA"] == "1"


async def test_run_export_threads(dce, tmp_path):
    await archive_utils.run_export(42, str(tmp_path), True)
    args = dce.calls[0][0]
    assert args[-2:] == ("--include-threads", "all")


async def test_run_export_reads_failed_channels(dce, tmp_path):
    dce.process = FakeProcess(
        0,
        f"Exporting...\n{FAILED}\n  puzzle-1 [1]: Forbidden\n  puzzle-2 [2]: Gone\n\nDone\n",
    )
    code, stderr, failed = await archive_utils.run_export(42, str(tmp_path), True)
    assert code == 0
    assert FAILED in stderr
    assert failed == ["puzzle-1 [1]: Forbidden", "puzzle-2 [2]: Gone"]


async def test_run_export_error_exit(dce, tmp_path):
    dce.process = FakeProcess(1, "ERROR\nSomething broke")
    assert await archive_utils.run_export(42, str(tmp_path), False) == (
        1,
        "ERROR\nSomething broke",
        [],
    )


async def test_run_export_timeout_kills_process(dce, tmp_path, monkeypatch):
    monkeypatch.setattr(archive_constants, "DCE_TIMEOUT", 0.01)
    dce.process = FakeProcess(hang=True)
    assert await archive_utils.run_export(42, str(tmp_path), False) == (
        -1,
        "Timed out",
        [],
    )
    assert dce.process.killed
