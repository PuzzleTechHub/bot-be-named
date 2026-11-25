import asyncio

from modules.archive import archive_utils
from modules.archive.cog import ArchiveCog
from tests.fakes import FakeChannel, FakeContext, FakeGuild


# ~archivecategory


async def test_archivecategory_deletes_its_delay_message(monkeypatch):
    monkeypatch.setattr(archive_utils, "dce_installed", lambda: True)
    ctx = FakeContext(FakeGuild(categories=[]), FakeChannel(20, "bot-commands"))
    cog = ArchiveCog(bot=None)

    # Hold the lock so the command sends "Warning: Delay!" and waits.
    await cog.lock.acquire()
    task = asyncio.create_task(
        cog.archivecategory.callback(cog, ctx, "No such category")
    )
    for _ in range(20):
        await asyncio.sleep(0)
        if ctx.sent:
            break
    cog.lock.release()
    await task

    delay, error = ctx.sent
    assert delay.embed.fields[0].name == "Warning: Delay!"
    assert delay.deleted
    # The error embed no longer carries the delay field.
    assert [field.name for field in error.embed.fields] == [
        "ERROR: Cannot find category"
    ]
