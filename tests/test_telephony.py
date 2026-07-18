from __future__ import annotations

from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit
from xml.etree import ElementTree

import pytest

from fredo.models import CallRequest
from fredo.settings import Settings
from fredo.telephony import (
    MockTelephony,
    TelephonyError,
    TwilioTelephony,
    _public_endpoint,
    build_twiml,
    telephony_from_settings,
)


def _request() -> CallRequest:
    return CallRequest(
        to="+33612345678",
        intent="Vérifier la démonstration",
        consent=True,
        confirmed=True,
        profile="hosted-voice-mvp",
        demo_session_id="demo_0123456789abcdef",
        expires_at="2099-01-01T00:00:00Z",
    )


def test_public_endpoint_requires_https_and_preserves_only_the_path_prefix() -> None:
    assert (
        _public_endpoint("https://voice.example.test/fredo/?ignored=yes#fragment", "/twilio/media")
        == "https://voice.example.test/fredo/twilio/media"
    )

    for unsafe_url in (
        "http://voice.example.test",
        "wss://voice.example.test",
        "//voice.example.test",
        "/local/path",
        "https:///missing-host",
    ):
        with pytest.raises(TelephonyError, match="public HTTPS URL"):
            _public_endpoint(unsafe_url, "/twilio/media")


def test_twiml_uses_wss_and_xml_escapes_url_and_call_id() -> None:
    call_id = "call<&\"'id"

    twiml = build_twiml("https://voice.example.test/prefix&tenant", call_id)
    root = ElementTree.fromstring(twiml)
    stream = root.find("./Connect/Stream")
    assert stream is not None
    assert stream.attrib["url"] == "wss://voice.example.test/prefix&tenant/twilio/media"
    parameter = stream.find("./Parameter")
    assert parameter is not None
    assert parameter.attrib == {"name": "fredoCallId", "value": call_id}
    assert "&amp;" in twiml
    assert "&lt;" in twiml
    assert "&quot;" in twiml


@pytest.mark.asyncio
async def test_twilio_call_is_bounded_and_all_transport_arguments_are_explicit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class FakeCalls:
        def create(self, **kwargs: object) -> SimpleNamespace:
            captured["create"] = kwargs
            return SimpleNamespace(sid="CA-test-call")

    class FakeClient:
        def __init__(self, account_sid: str, auth_token: str) -> None:
            captured["credentials"] = (account_sid, auth_token)
            self.calls = FakeCalls()

    monkeypatch.setattr("twilio.rest.Client", FakeClient)
    settings = Settings(
        twilio_account_sid="AC-test",
        twilio_auth_token="auth-secret",
        twilio_phone_number="+33102030405",
        public_url="https://voice.example.test/fredo",
        max_duration_seconds=37,
    )

    provider_call_id = await TwilioTelephony(settings).place_call(_request(), "call id&/?")

    assert provider_call_id == "CA-test-call"
    assert captured["credentials"] == ("AC-test", "auth-secret")
    create = captured["create"]
    assert isinstance(create, dict)
    assert create["to"] == "+33612345678"
    assert create["from_"] == "+33102030405"
    assert create["time_limit"] == 37
    assert create["status_callback_event"] == [
        "initiated",
        "ringing",
        "answered",
        "completed",
    ]
    assert create["status_callback_method"] == "POST"
    assert str(create["twiml"]).startswith('<?xml version="1.0"')
    assert 'url="wss://voice.example.test/fredo/twilio/media"' in str(create["twiml"])

    callback = urlsplit(str(create["status_callback"]))
    assert callback.scheme == "https"
    assert callback.netloc == "voice.example.test"
    assert callback.path == "/fredo/twilio/status"
    assert parse_qs(callback.query) == {"call_id": ["call id&/?"]}


@pytest.mark.asyncio
async def test_twilio_is_never_constructed_when_required_transport_config_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    constructed = False

    class ForbiddenClient:
        def __init__(self, *_: object, **__: object) -> None:
            nonlocal constructed
            constructed = True

    monkeypatch.setattr("twilio.rest.Client", ForbiddenClient)

    with pytest.raises(TelephonyError, match="not configured"):
        await TwilioTelephony(Settings()).place_call(_request(), "call-id")

    assert constructed is False


@pytest.mark.asyncio
async def test_carrier_failure_is_wrapped_in_a_stable_non_secret_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FailingCalls:
        def create(self, **_: object) -> None:
            raise RuntimeError("provider leaked auth-secret")

    class FailingClient:
        def __init__(self, *_: object) -> None:
            self.calls = FailingCalls()

    monkeypatch.setattr("twilio.rest.Client", FailingClient)
    settings = Settings(
        twilio_account_sid="AC-test",
        twilio_auth_token="auth-secret",
        twilio_phone_number="+33102030405",
        public_url="https://voice.example.test",
    )

    with pytest.raises(TelephonyError) as caught:
        await TwilioTelephony(settings).place_call(_request(), "call-id")

    assert str(caught.value) == "Carrier rejected the outbound call"
    assert "auth-secret" not in str(caught.value)


@pytest.mark.asyncio
async def test_mock_transport_is_deterministic_and_has_no_side_effects() -> None:
    transport = MockTelephony()

    assert await transport.place_call(_request(), "local-id") == "MOCK-local-id"
    assert await transport.hangup("MOCK-local-id") is None


def test_transport_factory_selects_mock_only_when_explicitly_configured() -> None:
    assert isinstance(telephony_from_settings(Settings(telephony_provider="mock")), MockTelephony)
    assert isinstance(telephony_from_settings(Settings(telephony_provider="real")), TwilioTelephony)
