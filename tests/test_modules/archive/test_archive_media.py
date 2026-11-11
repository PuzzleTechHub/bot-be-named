import os
import zipfile
from unittest.mock import MagicMock

import constants
from modules.archive import archive_constants, archive_utils
from modules.archive.cog import ArchiveCog

MB = 1_000_000


def test_pick_media_to_skip_fits_already():
    media = [("media/a.jpg", 5 * MB)]
    assert archive_utils.pick_media_to_skip(media, 8 * MB, 10 * MB) == []


def test_pick_media_to_skip_drops_biggest_first():
    media = [
        ("media/big.jpg", 43 * MB),
        ("media/mid.jpg", 11 * MB),
        ("media/small.jpg", 5 * MB),
        ("media/avatar.png", MB),
    ]
    # 62 MB zip, 10 MB limit: dropping big and mid leaves 8 MB
    skipped = archive_utils.pick_media_to_skip(media, 62 * MB, 10 * MB)
    assert [path for path, _ in skipped] == ["media/big.jpg", "media/mid.jpg"]


def test_pick_media_to_skip_can_drop_everything():
    media = [("media/a.jpg", 2 * MB), ("media/b.jpg", MB)]
    skipped = archive_utils.pick_media_to_skip(media, 20 * MB, 10 * MB)
    assert skipped == media


def test_media_display_name_strips_dce_hash():
    path = os.path.join("media", "Snow-covered_Cemetery_6-8c82f2abb4714f71.jpg")
    assert archive_utils.media_display_name(path) == "Snow-covered_Cemetery_6.jpg"


def test_media_display_name_url_decodes():
    path = os.path.join("media", "Fontanka_embamkment%2C_24-6aa674d8c4bb074c.jpg")
    assert archive_utils.media_display_name(path) == "Fontanka_embamkment,_24.jpg"


def test_media_display_name_keeps_names_without_hash():
    assert archive_utils.media_display_name("media/image.png") == "image.png"


def _fake_export(out_dir, sizes):
    """An export folder with one HTML file and random (incompressible) media files"""
    media_dir = os.path.join(out_dir, archive_constants.MEDIA)
    os.makedirs(media_dir)
    with open(os.path.join(out_dir, "chat.html"), "w") as f:
        f.write("<html>" + "hello " * 1000 + "</html>")
    for name, size in sizes.items():
        with open(os.path.join(media_dir, name), "wb") as f:
            f.write(os.urandom(size))


def test_zip_without_biggest_media(tmp_path):
    out_dir = str(tmp_path / "export")
    _fake_export(
        out_dir,
        {"big-0123456789abcdef.jpg": 300_000, "mid.jpg": 150_000, "small.png": 40_000},
    )
    cog = ArchiveCog.__new__(ArchiveCog)
    cog.compression = zipfile.ZIP_DEFLATED
    full = str(tmp_path / "full.zip")
    full_size = cog.zip_dir(out_dir, full)

    smaller = str(tmp_path / "smaller.zip")
    size, skipped, all_skipped = cog.zip_without_biggest_media(
        out_dir, smaller, full_size, 250_000
    )
    assert size <= 250_000
    assert not all_skipped
    assert [os.path.basename(p) for p, _ in skipped] == ["big-0123456789abcdef.jpg"]
    with zipfile.ZipFile(smaller) as zf:
        names = {os.path.basename(n) for n in zf.namelist()}
    assert names == {"chat.html", "mid.jpg", "small.png"}


def test_zip_without_biggest_media_html_only_when_nothing_fits(tmp_path):
    out_dir = str(tmp_path / "export")
    _fake_export(out_dir, {"a.jpg": 100_000, "b.jpg": 100_000})
    cog = ArchiveCog.__new__(ArchiveCog)
    cog.compression = zipfile.ZIP_DEFLATED
    full_size = cog.zip_dir(out_dir, str(tmp_path / "full.zip"))

    size, skipped, all_skipped = cog.zip_without_biggest_media(
        out_dir, str(tmp_path / "smaller.zip"), full_size, 20_000
    )
    assert all_skipped
    assert len(skipped) == 2


def test_list_skipped_caps_lines():
    skipped = [
        (f"media/f{i}-0123456789abcdef.jpg", (20 - i) * constants.BYTES_TO_MEGABYTES)
        for i in range(12)
    ]
    text = ArchiveCog.list_skipped(skipped)
    lines = text.split("\n")
    assert len(lines) == 9
    assert lines[0] == "`f0.jpg` (20.00MB)"
    assert lines[-1] == "...and 4 more"


def test_get_file_and_embed_partial(tmp_path, monkeypatch):
    monkeypatch.setattr(archive_constants, "ARCHIVE", str(tmp_path))
    out_dir = str(tmp_path / "export")
    _fake_export(out_dir, {"big.jpg": 300_000, "small.png": 40_000})
    cog = ArchiveCog.__new__(ArchiveCog)
    cog.compression = zipfile.ZIP_DEFLATED
    zip_path = str(tmp_path / "chan_archive.zip")
    zip_size = cog.zip_dir(out_dir, zip_path)
    channel = MagicMock()
    channel.name = "chan"
    channel.mention = "<#1>"

    file, embed = cog.get_file_and_embed(channel, 250_000, out_dir, zip_path, zip_size)
    assert file.filename == "chan_archive_smaller.zip"
    field = embed.fields[0]
    assert field.name == "WARNING: Attachments Too Big"
    assert "I left out the 1 biggest files" in field.value
    assert "`big.jpg`" in field.value
    assert len(field.value) <= 1024
