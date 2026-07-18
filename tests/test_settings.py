from __future__ import annotations

from pathlib import Path

import pytest

from fredo.settings import Settings


def test_empty_environment_uses_guarded_english_voice_defaults() -> None:
    settings = Settings.from_env({})

    assert settings.deepgram_api_key is None
    assert settings.allowed_numbers == frozenset()
    assert settings.host == "127.0.0.1"
    assert settings.port == 8080
    assert settings.max_duration_seconds == 180
    assert settings.max_concurrent_calls == 1
    assert settings.listen_model == "flux-general-multi"
    assert settings.listen_language == "en"
    assert settings.llm_provider == "open_ai"
    assert settings.llm_model == "gpt-4o-mini"
    assert settings.voice_model == "aura-2-thalia-en"
    assert settings.telephony_provider == "real"


def test_environment_is_parsed_and_normalized_without_widening_allowlist() -> None:
    settings = Settings.from_env(
        {
            "DEEPGRAM_API_KEY": "dg-secret",
            "TWILIO_ACCOUNT_SID": "AC123",
            "TWILIO_AUTH_TOKEN": "twilio-secret",
            "TWILIO_PHONE_NUMBER": "+33102030405",
            "FREDO_ENDPOINT_SECRET": "endpoint-secret",
            "FREDO_ALLOWED_NUMBERS": " +33612345678, +33787654321, +33612345678, ,",
            "FREDO_PUBLIC_URL": "https://voice.example.test/fredo///",
            "FREDO_HOST": "0.0.0.0",
            "FREDO_PORT": "9090",
            "FREDO_MAX_DURATION_SECONDS": "42",
            "FREDO_MAX_CONCURRENT_CALLS": "1",
            "FREDO_TELEPHONY_PROVIDER": " MOCK ",
            "FREDO_STATE_DIR": "./state",
        }
    )

    assert settings.allowed_numbers == frozenset({"+33612345678", "+33787654321"})
    assert settings.public_url == "https://voice.example.test/fredo"
    assert settings.host == "0.0.0.0"
    assert settings.port == 9090
    assert settings.max_duration_seconds == 42
    assert settings.telephony_provider == "mock"
    assert settings.state_dir == Path("state")


def test_credentials_never_appear_in_repr_or_public_diagnostics() -> None:
    secrets = ("dg-top-secret", "twilio-top-secret", "endpoint-top-secret")
    settings = Settings(
        deepgram_api_key=secrets[0],
        twilio_account_sid="AC-visible-identifier",
        twilio_auth_token=secrets[1],
        twilio_phone_number="+33102030405",
        endpoint_secret=secrets[2],
        allowed_numbers=frozenset({"+33612345678"}),
        public_url="https://voice.example.test",
    )

    diagnostics = settings.public_summary()
    rendered = f"{settings!r}\n{diagnostics!r}\n{settings.missing_for_real_call()!r}"

    assert diagnostics["deepgram_configured"] is True
    assert diagnostics["twilio_configured"] is True
    assert diagnostics["endpoint_auth_configured"] is True
    assert diagnostics["allowed_destination_count"] == 1
    for secret in secrets:
        assert secret not in rendered


def test_missing_real_call_configuration_reports_names_not_values() -> None:
    settings = Settings.from_env({"DEEPGRAM_API_KEY": "configured-secret"})

    assert settings.missing_for_real_call() == [
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
        "TWILIO_PHONE_NUMBER",
        "FREDO_ENDPOINT_SECRET",
        "FREDO_ALLOWED_NUMBERS",
        "FREDO_PUBLIC_URL",
    ]


def test_with_public_url_is_immutable_and_removes_trailing_slashes() -> None:
    original = Settings(public_url=None)

    changed = original.with_public_url("https://voice.example.test/fredo///")

    assert original.public_url is None
    assert changed.public_url == "https://voice.example.test/fredo"


@pytest.mark.parametrize("value", ["9", "181", "not-an-integer"])
def test_duration_outside_hackathon_bounds_is_rejected(value: str) -> None:
    with pytest.raises(ValueError, match="FREDO_MAX_DURATION_SECONDS"):
        Settings.from_env({"FREDO_MAX_DURATION_SECONDS": value})


@pytest.mark.parametrize("value", ["0", "2", "not-an-integer"])
def test_any_concurrency_other_than_one_is_rejected(value: str) -> None:
    with pytest.raises(ValueError, match="FREDO_MAX_CONCURRENT_CALLS"):
        Settings.from_env({"FREDO_MAX_CONCURRENT_CALLS": value})


def test_unknown_telephony_provider_is_rejected() -> None:
    with pytest.raises(ValueError, match="must be 'real' or 'mock'"):
        Settings.from_env({"FREDO_TELEPHONY_PROVIDER": "carrier-x"})
