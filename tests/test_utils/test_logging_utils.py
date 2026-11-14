import re
from types import SimpleNamespace

import pytest

from modules.error_logging import error_constants
from utils import logging_utils

TIMESTAMP = r"\[ \d\d-\d\d-\d{4}, \d\d:\d\d:\d\d \]"


class FakeWebhook:
    def __init__(self, fail=False):
        self.sent = []
        self.fail = fail

    async def send(self, text):
        if self.fail:
            raise RuntimeError("webhook down")
        self.sent.append(text)


@pytest.fixture(autouse=True)
def in_tmp_dir(tmp_path, monkeypatch):
    """Log files are written to the working directory."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _webhook_log(tmp_path):
    return (tmp_path / error_constants.ERROR_WEBHOOKFILE).read_text()


def test_log_to_file_appends_with_timestamp(in_tmp_dir):
    logging_utils.log_to_file("log.txt", "first")
    logging_utils.log_to_file("log.txt", "second")
    text = (in_tmp_dir / "log.txt").read_text()
    assert re.fullmatch(rf"{TIMESTAMP} first\n\n{TIMESTAMP} second\n\n", text)


def test_print_with_timestamp(capsys):
    logging_utils.print_with_timestamp("hello")
    assert re.fullmatch(rf"{TIMESTAMP} hello\n", capsys.readouterr().out)


async def test_send_to_webhook(in_tmp_dir, monkeypatch):
    webhook = FakeWebhook()
    monkeypatch.setattr(logging_utils, "webhook", webhook, raising=False)
    await logging_utils.send_to_webhook("text")
    assert webhook.sent == ["text"]
    assert _webhook_log(in_tmp_dir).rstrip().endswith("] text")


async def test_send_to_webhook_without_webhook_still_logs(in_tmp_dir, monkeypatch):
    monkeypatch.setattr(logging_utils, "webhook", None, raising=False)
    await logging_utils.send_to_webhook("text")
    assert "text" in _webhook_log(in_tmp_dir)


async def test_log_command_in_server(in_tmp_dir, monkeypatch, capsys):
    webhook = FakeWebhook()
    monkeypatch.setattr(logging_utils, "webhook", webhook, raising=False)
    guild = SimpleNamespace(name="Test server")
    channel = SimpleNamespace(name="puzzle-1")
    await logging_utils.log_command("~solved", guild, channel, "solver")
    assert webhook.sent == [
        "Received `~solved` from `solver` in `Test server` : `#puzzle-1`"
    ]
    assert "Received `~solved`" in capsys.readouterr().out


async def test_log_command_in_dms(monkeypatch):
    webhook = FakeWebhook()
    monkeypatch.setattr(logging_utils, "webhook", webhook, raising=False)
    await logging_utils.log_command("~help", None, None, "solver")
    assert webhook.sent == ["Received `~help` from `solver` in DMs"]


async def test_log_command_survives_webhook_failure(monkeypatch, capsys):
    monkeypatch.setattr(logging_utils, "webhook", FakeWebhook(fail=True), raising=False)
    await logging_utils.log_command("~help", None, None, "solver")
    assert "Webhook failed" in capsys.readouterr().out


async def test_open_and_close_session(monkeypatch):
    monkeypatch.setattr(logging_utils, "webhook_url", None)
    monkeypatch.setattr(logging_utils, "webhook", None, raising=False)
    await logging_utils.open_session()
    session = logging_utils.session
    assert not session.closed
    assert logging_utils.webhook is None
    await logging_utils.close_session()
    assert session.closed


async def test_open_session_with_url(monkeypatch):
    token = "a" * 64  # Discord webhook tokens are 60-68 characters
    url = f"https://discord.com/api/webhooks/123456789012345678/{token}"
    monkeypatch.setattr(logging_utils, "webhook_url", url)
    monkeypatch.setattr(logging_utils, "webhook", None, raising=False)
    await logging_utils.open_session()
    try:
        assert logging_utils.webhook.id == 123456789012345678
        assert logging_utils.webhook.token == token
    finally:
        await logging_utils.close_session()
