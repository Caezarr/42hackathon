from __future__ import annotations

import stat
from pathlib import Path

from dotenv import dotenv_values

from fredo.configurator import configure_env


def test_configure_preserves_provider_and_host_fields(
    tmp_path: Path,
    monkeypatch,
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "FREDO_PUBLIC_URL=https://fredo.example\n"
        "FREDO_GINSE_AUDIENCE=fredo-provider\n"
        "FREDO_GINSE_DATABASE=/data/ginse.sqlite3\n",
        encoding="utf-8",
    )
    secret_answers = iter(("deepgram-secret", "twilio-secret"))
    plain_answers = iter(("AC0123456789", "+33123456789", "+33612345678"))
    monkeypatch.setattr("getpass.getpass", lambda _prompt: next(secret_answers))
    monkeypatch.setattr("builtins.input", lambda _prompt: next(plain_answers))

    configured = configure_env(env_file)
    values = dotenv_values(configured)

    assert values["FREDO_PUBLIC_URL"] == "https://fredo.example"
    assert values["FREDO_GINSE_AUDIENCE"] == "fredo-provider"
    assert values["FREDO_GINSE_DATABASE"] == "/data/ginse.sqlite3"
    assert values["FREDO_ALLOWED_NUMBERS"] == "+33612345678"
    assert stat.S_IMODE(configured.stat().st_mode) == 0o600
