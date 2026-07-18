from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from fredo.models import CallRequest
from fredo.policy import (
    GINSE_PROFILE,
    PolicyError,
    destination_hint,
    normalize_e164,
    validate_call_request,
    validate_ginse_demo_receipt,
)
from fredo.settings import Settings


MOBILE_6 = "+33612345678"
MOBILE_7 = "+33787654321"
DEMO_SESSION_ID = "demo_0123456789abcdef"
VALID_EXPIRES_AT = (
    (datetime.now(UTC) + timedelta(minutes=10))
    .replace(microsecond=0)
    .isoformat()
    .replace("+00:00", "Z")
)


def _settings(*numbers: str) -> Settings:
    return Settings(allowed_numbers=frozenset(numbers))


def _payload(to: object = MOBILE_6, **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "to": to,
        "intent": "Demander si la démonstration fonctionne",
        "consent": True,
        "confirmed": True,
        "profile": GINSE_PROFILE,
        "demo_session_id": DEMO_SESSION_ID,
        "expires_at": VALID_EXPIRES_AT,
    }
    payload.update(overrides)
    return payload


@pytest.mark.parametrize("destination", [MOBILE_6, MOBILE_7])
def test_exact_enrolled_french_mobile_is_allowed(destination: str) -> None:
    request = validate_call_request(_payload(destination), _settings(MOBILE_6, MOBILE_7))

    assert request == CallRequest(
        to=destination,
        intent="Demander si la démonstration fonctionne",
        consent=True,
        confirmed=True,
        profile=GINSE_PROFILE,
        demo_session_id=DEMO_SESSION_ID,
        expires_at=VALID_EXPIRES_AT,
    )


def test_display_format_is_canonicalized_before_exact_allowlist_match() -> None:
    request = validate_call_request(_payload("+33 (6) 12 34 56 78"), _settings(MOBILE_6))

    assert request.to == MOBILE_6


@pytest.mark.parametrize("destination", ["+31636409680", "+447700900123"])
def test_international_e164_destination_is_allowed_when_exactly_enrolled(destination: str) -> None:
    request = validate_call_request(_payload(destination), _settings(destination))

    assert request.to == destination


def test_mobile_prefix_is_not_a_wildcard_allowlist() -> None:
    with pytest.raises(PolicyError) as caught:
        validate_call_request(_payload(MOBILE_6), _settings("+336"))

    assert caught.value.code == "destination_not_allowed"


def test_another_valid_mobile_is_denied_without_exact_enrollment() -> None:
    with pytest.raises(PolicyError) as caught:
        validate_call_request(_payload(MOBILE_7), _settings(MOBILE_6))

    assert caught.value.code == "destination_not_allowed"


def test_unknown_fields_are_rejected_and_reported_deterministically() -> None:
    with pytest.raises(PolicyError) as caught:
        validate_call_request(
            _payload(MOBILE_6, zeta="ignored", admin=True),
            _settings(MOBILE_6),
        )

    assert caught.value.code == "unknown_fields"
    assert str(caught.value) == "Unknown fields: admin, zeta"


@pytest.mark.parametrize("consent", [None, False, 1, "true"])
def test_explicit_boolean_recipient_consent_is_required(consent: object) -> None:
    with pytest.raises(PolicyError) as caught:
        validate_call_request(_payload(consent=consent), _settings(MOBILE_6))

    assert caught.value.code == "consent_required"


@pytest.mark.parametrize("confirmed", [None, False, 1, "true"])
def test_explicit_boolean_native_confirmation_is_required(confirmed: object) -> None:
    with pytest.raises(PolicyError) as caught:
        validate_call_request(_payload(confirmed=confirmed), _settings(MOBILE_6))

    assert caught.value.code == "confirmation_required"


@pytest.mark.parametrize("payload", [None, [], "request"])
def test_request_must_be_a_json_object(payload: object) -> None:
    with pytest.raises(PolicyError) as caught:
        validate_call_request(payload, _settings(MOBILE_6))

    assert caught.value.code == "invalid_request"


@pytest.mark.parametrize("destination", [None, 33612345678, "0612345678", "+33612/34/56"])
def test_invalid_e164_values_are_rejected(destination: object) -> None:
    with pytest.raises(PolicyError) as caught:
        normalize_e164(destination)

    assert caught.value.code == "invalid_destination"


def test_intent_is_trimmed_collapsed_and_bounded() -> None:
    request = validate_call_request(
        _payload(intent="  Demander   si\nla démo fonctionne  "),
        _settings(MOBILE_6),
    )
    assert request.intent == "Demander si la démo fonctionne"

    with pytest.raises(PolicyError) as caught:
        validate_call_request(_payload(intent="x" * 501), _settings(MOBILE_6))
    assert caught.value.code == "invalid_intent"


def test_destination_hint_does_not_expose_complete_number() -> None:
    hint = destination_hint(MOBILE_6)

    assert hint == "+336••••78"
    assert MOBILE_6 not in hint


def test_ginse_receipt_is_a_closed_short_lived_structural_handoff() -> None:
    now = datetime(2026, 7, 18, 12, 0, tzinfo=UTC)
    receipt = validate_ginse_demo_receipt(
        profile=GINSE_PROFILE,
        demo_session_id=DEMO_SESSION_ID,
        expires_at="2026-07-18T12:15:00Z",
        now=now,
    )

    assert receipt.profile == GINSE_PROFILE
    assert receipt.demo_session_id == DEMO_SESSION_ID
    assert receipt.expires_at == "2026-07-18T12:15:00Z"


@pytest.mark.parametrize(
    ("overrides", "code"),
    [
        ({"profile": "other-profile"}, "invalid_ginse_profile"),
        ({"demo_session_id": "not-a-session"}, "invalid_ginse_receipt"),
        ({"expires_at": "2026-07-18T12:15:00+00:00"}, "invalid_ginse_receipt"),
        ({"expires_at": "2026-07-18T11:59:59Z"}, "expired_ginse_receipt"),
        ({"expires_at": "2026-07-18T12:21:00Z"}, "invalid_ginse_receipt"),
    ],
)
def test_ginse_receipt_rejects_wrong_profile_shape_or_freshness(
    overrides: dict[str, str],
    code: str,
) -> None:
    values = {
        "profile": GINSE_PROFILE,
        "demo_session_id": DEMO_SESSION_ID,
        "expires_at": "2026-07-18T12:15:00Z",
    }
    values.update(overrides)

    with pytest.raises(PolicyError) as caught:
        validate_ginse_demo_receipt(
            **values,
            now=datetime(2026, 7, 18, 12, 0, tzinfo=UTC),
        )

    assert caught.value.code == code


@pytest.mark.parametrize("missing", ["profile", "demo_session_id", "expires_at"])
def test_call_request_requires_every_ginse_handoff_field(missing: str) -> None:
    payload = _payload()
    del payload[missing]

    with pytest.raises(PolicyError):
        validate_call_request(payload, _settings(MOBILE_6))
