from __future__ import annotations

from dataclasses import replace

import pytest

from fredo.doctor import Check, checks_payload, run_checks
from fredo.settings import Settings


def _ready_settings() -> Settings:
    return Settings(
        deepgram_api_key="dg-top-secret",
        twilio_account_sid="AC-test",
        twilio_auth_token="twilio-top-secret",
        twilio_phone_number="+33102030405",
        endpoint_secret="endpoint-top-secret-24-chars",
        allowed_numbers=frozenset({"+33612345678", "+33787654321"}),
        public_url="https://voice.example.test",
        max_duration_seconds=180,
        max_concurrent_calls=1,
        telephony_provider="real",
    )


def _by_name(settings: Settings, *, quick_tunnel: bool = False) -> dict[str, Check]:
    return {check.name: check for check in run_checks(settings, quick_tunnel=quick_tunnel)}


def test_fully_configured_real_profile_is_ready() -> None:
    checks = run_checks(_ready_settings(), quick_tunnel=False)
    payload = checks_payload(checks)

    assert payload["status"] == "ready"
    assert all(item["status"] == "pass" for item in payload["checks"])
    assert {check.name for check in checks} == {
        "runtime.python",
        "voice.deepgram",
        "telephony.twilio",
        "policy.endpoint_auth",
        "policy.allowlist",
        "network.tunnel",
        "policy.duration",
        "policy.concurrency",
        "release.real_transport",
    }


@pytest.mark.parametrize(
    ("changes", "failed_check"),
    [
        ({"deepgram_api_key": None}, "voice.deepgram"),
        ({"twilio_auth_token": None}, "telephony.twilio"),
        ({"endpoint_secret": "too-short"}, "policy.endpoint_auth"),
        ({"allowed_numbers": frozenset()}, "policy.allowlist"),
        ({"allowed_numbers": frozenset({"+336"})}, "policy.allowlist"),
        ({"allowed_numbers": frozenset({"+33812345678"})}, "policy.allowlist"),
        ({"public_url": None}, "network.tunnel"),
        ({"max_duration_seconds": 181}, "policy.duration"),
        ({"max_concurrent_calls": 2}, "policy.concurrency"),
        ({"telephony_provider": "mock"}, "release.real_transport"),
    ],
)
def test_any_failed_mandatory_check_makes_profile_not_ready(
    changes: dict[str, object],
    failed_check: str,
) -> None:
    settings = replace(_ready_settings(), **changes)
    checks = run_checks(settings, quick_tunnel=False)

    assert _by_name(settings)[failed_check].ok is False
    assert checks_payload(checks)["status"] == "not_ready"


def test_quick_tunnel_requires_local_cloudflared_binary(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = replace(_ready_settings(), public_url=None)
    monkeypatch.setattr("fredo.doctor.shutil.which", lambda executable: "/bin/cloudflared")

    available = _by_name(settings, quick_tunnel=True)["network.tunnel"]
    assert available.ok is True
    assert available.detail == "cloudflared available"

    monkeypatch.setattr("fredo.doctor.shutil.which", lambda executable: None)
    missing = _by_name(settings, quick_tunnel=True)["network.tunnel"]
    assert missing.ok is False
    assert missing.detail == "cloudflared/public URL missing"


def test_doctor_payload_contains_no_credentials_or_exact_destinations() -> None:
    settings = _ready_settings()
    payload = checks_payload(run_checks(settings, quick_tunnel=False))
    rendered = repr(payload)

    for sensitive in (
        "dg-top-secret",
        "twilio-top-secret",
        "endpoint-top-secret-24-chars",
        "+33612345678",
        "+33787654321",
    ):
        assert sensitive not in rendered
    assert "2 exact destination(s)" in rendered


def test_check_serialization_has_stable_status_vocabulary() -> None:
    assert Check("example", True, "ok").as_dict() == {
        "name": "example",
        "status": "pass",
        "detail": "ok",
    }
    assert Check("example", False, "missing").as_dict()["status"] == "fail"
