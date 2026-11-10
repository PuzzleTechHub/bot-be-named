"""
Downloads DiscordChatExporter (https://github.com/Tyrrrz/DiscordChatExporter),
which the archive module uses to export channels.

Usage: `python scripts/install_dce.py`
Does nothing if the pinned version is already installed in tools/dce/.
"""

import hashlib
import io
import os
import platform
import shutil
import stat
import sys
import urllib.request
import zipfile
from pathlib import Path

VERSION = "2.48"
# SHA-256 of each release zip, from the GitHub release page
SHA256 = {
    "linux-x64": "3e253e28ec7ea034b2201443fa84571142945299296541ecbe196ffceef8bc3c",
    "linux-arm64": "02a47fc8e0192fd509fbb082aadd9322035b18feae96849699fefc424a1e3379",
    "osx-x64": "91b4eae3525df85d084969004f3a287edad4eeaafd664e4869b26bb8422e2e88",
    "osx-arm64": "623f9d2dce568e17a46b8fbd366a18dca49803d386216f4ba24507d2c000fee9",
    "win-x64": "9f6706f6311f1387bc29d536e951d6c758716a57f59a2f2ce1718616ea6574b1",
}
DCE_DIR = Path(__file__).resolve().parent.parent / "tools" / "dce"


def get_platform() -> str:
    system = {"Linux": "linux", "Darwin": "osx", "Windows": "win"}[platform.system()]
    arch = "arm64" if platform.machine().lower() in ("arm64", "aarch64") else "x64"
    return f"{system}-{arch}"


def main():
    version_file = DCE_DIR / "VERSION"
    if version_file.exists() and version_file.read_text().strip() == VERSION:
        print(f"DiscordChatExporter {VERSION} is already installed in {DCE_DIR}")
        return

    plat = get_platform()
    if plat not in SHA256:
        sys.exit(f"No DiscordChatExporter build listed for {plat}")
    url = (
        "https://github.com/Tyrrrz/DiscordChatExporter/releases/download/"
        f"{VERSION}/DiscordChatExporter.Cli.{plat}.zip"
    )
    print(f"Downloading {url}")
    with urllib.request.urlopen(url) as response:
        data = response.read()
    if hashlib.sha256(data).hexdigest() != SHA256[plat]:
        sys.exit("Checksum mismatch, not installing")

    if DCE_DIR.exists():
        shutil.rmtree(DCE_DIR)
    DCE_DIR.mkdir(parents=True)
    zipfile.ZipFile(io.BytesIO(data)).extractall(DCE_DIR)
    # zipfile drops the executable bit
    if os.name != "nt":
        exe = DCE_DIR / "DiscordChatExporter.Cli"
        exe.chmod(exe.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    version_file.write_text(VERSION)
    print(f"Installed DiscordChatExporter {VERSION} in {DCE_DIR}")


if __name__ == "__main__":
    main()
