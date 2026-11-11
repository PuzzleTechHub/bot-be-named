from modules.archive import archive_constants
from utils import discord_utils
import asyncio
import os
import re
import shutil
import urllib.parse
from typing import List, Tuple


def get_delay_embed():
    embed = discord_utils.create_embed()
    embed.add_field(
        name="Warning: Delay!",
        value="Hi! It appears we're a little busy at the moment, so our archiving may take a while. "
        "Sorry about that! We'll get to it as soon as possible.",
        inline=False,
    )
    return embed


def reset_archive_dir():
    # Remove the archive directory and remake.
    # On Windows, antivirus or OneDrive can briefly lock new media files, so don't crash on that.
    shutil.rmtree(archive_constants.ARCHIVE, ignore_errors=True)
    os.makedirs(archive_constants.ARCHIVE, exist_ok=True)


def dce_installed() -> bool:
    return os.path.isfile(archive_constants.DCE_PATH)


async def run_export(
    channel_id: int, out_dir: str, include_threads: bool
) -> Tuple[int, str, List[str]]:
    """Export one channel (and its threads) to HTML with DiscordChatExporter.

    Returns the exit code, DCE's stderr, and the channels DCE says failed.
    DCE exits 0 if at least one channel worked, so check the failed list too.
    """
    args = [
        archive_constants.DCE_PATH,
        "export",
        "-c",
        str(channel_id),
        "--media",
        "--reuse-media",
        "--media-dir",
        os.path.join(out_dir, archive_constants.MEDIA),
        # The trailing separator tells DCE this is a folder, not a file name
        "-o",
        os.path.join(out_dir, ""),
    ]
    if include_threads:
        args += ["--include-threads", "all"]
    # DCE reads DISCORD_TOKEN from the environment, so the token stays off the command line.
    # FUCK_RUSSIA=1 turns off DCE's console banner.
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
        env={**os.environ, "FUCK_RUSSIA": "1"},
    )
    try:
        _, stderr_bytes = await asyncio.wait_for(
            proc.communicate(), archive_constants.DCE_TIMEOUT
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return -1, "Timed out", []

    stderr = stderr_bytes.decode(errors="replace")
    lines = [line.strip() for line in stderr.splitlines()]
    failed = []
    if archive_constants.DCE_FAILED_HEADER in lines:
        for line in lines[lines.index(archive_constants.DCE_FAILED_HEADER) + 1 :]:
            if not line:
                break
            failed.append(line)
    return proc.returncode, stderr, failed


def first_error(stderr: str) -> str:
    """The readable part of DCE's error output, without the stack trace"""
    for line in stderr.splitlines():
        line = line.strip()
        if line and line != "ERROR" and not line.startswith("at "):
            # Drop the exception type, e.g. "DiscordChatExporter...Exception: "
            return line.split("Exception: ", 1)[-1][:500]
    return "Unknown error"


def list_media(out_dir: str) -> List[Tuple[str, int]]:
    """Every file in the export's media folder as (path relative to out_dir, size), biggest first"""
    media_dir = os.path.join(out_dir, archive_constants.MEDIA)
    files = []
    for root, _, names in os.walk(media_dir):
        for name in names:
            path = os.path.join(root, name)
            files.append((os.path.relpath(path, out_dir), os.path.getsize(path)))
    return sorted(files, key=lambda f: f[1], reverse=True)


def pick_media_to_skip(
    media: List[Tuple[str, int]], zip_size: int, filesize_limit: int
) -> List[Tuple[str, int]]:
    """Pick the biggest media files to leave out so the zip should fit under the limit.

    media is (path, size) sorted biggest first. Media is mostly images and videos,
    which barely compress, so leaving a file out shrinks the zip by about its size.
    """
    skipped = []
    for path, size in media:
        if zip_size <= filesize_limit:
            break
        skipped.append((path, size))
        zip_size -= size
    return skipped


def media_display_name(path: str) -> str:
    """Turn DCE's media file name back into the original one, e.g.
    media/Big_photo-8c82f2abb4714f71.jpg -> Big_photo.jpg"""
    name = urllib.parse.unquote(os.path.basename(path))
    stem, ext = os.path.splitext(name)
    return re.sub(r"-[0-9a-f]{16}$", "", stem) + ext


def safe_filename(name: str, max_len: int = 80) -> str:
    """A channel or thread name made safe to use in a file name on Linux and Windows.
    Thread and forum post names can contain / ? * : and so on, which can't go in a path."""
    safe = re.sub(r"[^\w\- .]", "_", name).strip(" .")
    return safe[:max_len] or "channel"


def list_for_embed(names: List[str], limit: int = 1024) -> str:
    """One name per line, cut off with "...and N more" so it fits in an embed field
    (Discord allows 1024 characters per field)"""
    lines = []
    used = 0
    for i, name in enumerate(names):
        line = name[:100]
        more = f"...and {len(names) - i} more"
        if used + len(line) + 1 + len(more) > limit:
            lines.append(more)
            break
        lines.append(line)
        used += len(line) + 1
    return "\n".join(lines)
