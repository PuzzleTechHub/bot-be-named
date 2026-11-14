import json

import pytest

from utils import google_utils


@pytest.fixture
def opened(tmp_path, monkeypatch):
    """Runs in an empty folder and records which key file and scopes were loaded."""
    monkeypatch.chdir(tmp_path)
    calls = []

    def from_json_keyfile_name(filename, scopes):
        calls.append((filename, scopes))
        return "credentials"

    monkeypatch.setattr(
        google_utils.ServiceAccountCredentials,
        "from_json_keyfile_name",
        from_json_keyfile_name,
    )
    return calls


def _set_env(monkeypatch):
    for param in google_utils.JSON_PARAMS:
        monkeypatch.setenv(param, f'"{param}-value"')
    monkeypatch.setenv(
        "private_key", '"-----BEGIN KEY-----\\nabc\\n-----END KEY-----\\n"'
    )


def test_writes_key_file_from_env(tmp_path, monkeypatch, opened):
    _set_env(monkeypatch)
    assert google_utils.get_gdrive_credentials() == "credentials"

    written = json.loads((tmp_path / "client_secret.json").read_text())
    assert list(written) == google_utils.JSON_PARAMS
    # Quotes are stripped and escaped newlines become real ones
    assert written["client_email"] == "client_email-value"
    assert written["private_key"] == "-----BEGIN KEY-----\nabc\n-----END KEY-----\n"


def test_scopes(monkeypatch, opened):
    _set_env(monkeypatch)
    google_utils.get_gdrive_credentials()
    assert opened == [
        (
            "client_secret.json",
            [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ],
        )
    ]


def test_existing_key_file_kept(tmp_path, monkeypatch, opened):
    (tmp_path / "client_secret.json").write_text('{"type": "mine"}')
    for param in google_utils.JSON_PARAMS:
        monkeypatch.delenv(param, raising=False)
    google_utils.get_gdrive_credentials()
    assert (tmp_path / "client_secret.json").read_text() == '{"type": "mine"}'


def test_missing_env_var_fails(tmp_path, monkeypatch, opened):
    _set_env(monkeypatch)
    monkeypatch.delenv("client_id")
    with pytest.raises(AttributeError):
        google_utils.get_gdrive_credentials()


def test_create_gspread_client(monkeypatch, opened):
    _set_env(monkeypatch)
    monkeypatch.setattr(
        google_utils.gspread, "authorize", lambda creds: ("client", creds)
    )
    assert google_utils.create_gspread_client() == ("client", "credentials")
