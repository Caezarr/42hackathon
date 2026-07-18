from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from starlette.testclient import TestClient
from twilio.request_validator import RequestValidator

from fredo.app import create_app
from fredo.ginse import AuthenticationError, PROFILE, SQLiteIdempotencyStore
from fredo.models import CallRequest
from fredo.settings import Settings
from fredo.telephony import MockTelephony, TelephonyError


DESTINATION = "+33612345678"
ENDPOINT_SECRET = "endpoint-secret-at-least-24-characters"
DEMO_SESSION_ID = "demo_0123456789abcdef"
VALID_EXPIRES_AT = (
    (datetime.now(UTC) + timedelta(minutes=10))
    .replace(microsecond=0)
    .isoformat()
    .replace("+00:00", "Z")
)


def _settings(*, provider: str = "mock", **overrides: object) -> Settings:
    values: dict[str, object] = {
        "deepgram_api_key": "dg-secret",
        "twilio_account_sid": "AC-test",
        "twilio_auth_token": "twilio-secret",
        "twilio_phone_number": "+33102030405",
        "endpoint_secret": ENDPOINT_SECRET,
        "allowed_numbers": frozenset({DESTINATION}),
        "public_url": "https://voice.example.test",
        "telephony_provider": provider,
    }
    values.update(overrides)
    return Settings(**values)


def _payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "to": DESTINATION,
        "intent": "Demander si la démonstration fonctionne",
        "consent": True,
        "confirmed": True,
        "profile": PROFILE,
        "demo_session_id": DEMO_SESSION_ID,
        "expires_at": VALID_EXPIRES_AT,
    }
    payload.update(overrides)
    return payload


def _auth(secret: str = ENDPOINT_SECRET) -> dict[str, str]:
    return {"Authorization": f"Bearer {secret}"}


def _start_headers(
    idempotency_key: str = "idempotency-key-001",
    *,
    secret: str = ENDPOINT_SECRET,
) -> dict[str, str]:
    return {**_auth(secret), "Idempotency-Key": idempotency_key}


def _twilio_signature(path_and_query: str, params: dict[str, str]) -> str:
    validator = RequestValidator("twilio-secret")
    return validator.compute_signature(f"https://voice.example.test{path_and_query}", params)


@dataclass
class RecordingMockTelephony(MockTelephony):
    calls: list[tuple[CallRequest, str]] = field(default_factory=list)

    async def place_call(self, request: CallRequest, call_id: str) -> str:
        self.calls.append((request, call_id))
        return await super().place_call(request, call_id)


@dataclass
class HoldingTelephony:
    calls: list[tuple[CallRequest, str]] = field(default_factory=list)

    async def place_call(self, request: CallRequest, call_id: str) -> str:
        self.calls.append((request, call_id))
        return f"CA-{call_id}"

    async def hangup(self, provider_call_id: str) -> None:
        del provider_call_id


async def _raw_ginse_request(
    app: Any,
    *,
    headers: list[tuple[bytes, bytes]],
    chunks: list[tuple[bytes, bool]],
) -> tuple[int, dict[str, object], int]:
    received = 0
    sent: list[dict[str, Any]] = []

    async def receive() -> dict[str, Any]:
        nonlocal received
        if received < len(chunks):
            body, more_body = chunks[received]
            received += 1
            return {"type": "http.request", "body": body, "more_body": more_body}
        return {"type": "http.disconnect"}

    async def send(message: dict[str, Any]) -> None:
        sent.append(message)

    await app(
        {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "POST",
            "scheme": "https",
            "path": "/run",
            "raw_path": b"/run",
            "query_string": b"",
            "root_path": "",
            "headers": headers,
            "client": ("127.0.0.1", 12345),
            "server": ("provider.example.test", 443),
        },
        receive,
        send,
    )

    start = next(message for message in sent if message["type"] == "http.response.start")
    body = b"".join(
        message.get("body", b"")
        for message in sent
        if message["type"] == "http.response.body"
    )
    return int(start["status"]), json.loads(body), received


def test_call_api_requires_exact_bearer_auth_before_any_transport_action() -> None:
    transport = RecordingMockTelephony()
    app = create_app(_settings(), telephony=transport)

    with TestClient(app) as client:
        for headers in ({}, _auth("wrong-secret"), {"Authorization": ENDPOINT_SECRET}):
            response = client.post("/v1/calls", json=_payload(), headers=headers)
            assert response.status_code == 401
            assert response.json() == {"error": "unauthorized"}

    assert transport.calls == []


def test_mock_call_completes_without_network_and_returns_only_public_state() -> None:
    transport = RecordingMockTelephony()
    app = create_app(_settings(), telephony=transport)

    with TestClient(app) as client:
        response = client.post("/v1/calls", json=_payload(), headers=_start_headers())

        assert response.status_code == 202
        body = response.json()
        assert body["replayed"] is False
        assert body["status"] == "completed"
        assert body["destination_hint"] == "+336••••78"
        assert body["outcome"] == {
            "mock": True,
            "works": False,
            "answer": "No real call placed",
            "summary": "No real call placed",
        }
        assert "twilio_sid" not in body
        assert DESTINATION not in response.text
        assert len(transport.calls) == 1
        assert transport.calls[0][0].to == DESTINATION

        status = client.get(f"/v1/calls/{body['call_id']}", headers=_auth())
        assert status.status_code == 200
        expected_status = {key: value for key, value in body.items() if key != "replayed"}
        assert status.json() == expected_status


def test_call_status_requires_auth_and_unknown_id_is_404() -> None:
    app = create_app(_settings(), telephony=RecordingMockTelephony())

    with TestClient(app) as client:
        assert client.get("/v1/calls/not-found").status_code == 401
        response = client.get("/v1/calls/not-found", headers=_auth())

    assert response.status_code == 404
    assert response.json() == {"error": "not_found"}


def test_second_call_is_rejected_as_busy_without_a_second_transport_attempt() -> None:
    transport = HoldingTelephony()
    app = create_app(_settings(provider="real"), telephony=transport)

    with TestClient(app) as client:
        first = client.post(
            "/v1/calls",
            json=_payload(),
            headers=_start_headers("first-call-key"),
        )
        second = client.post(
            "/v1/calls",
            json=_payload(intent="Une seconde demande"),
            headers=_start_headers("second-call-key"),
        )

    assert first.status_code == 202
    assert first.json()["status"] == "dialing"
    assert second.status_code == 409
    assert second.json() == {"error": "call_in_progress"}
    assert len(transport.calls) == 1


@pytest.mark.parametrize(
    ("provider_status", "public_status"),
    [
        ("initiated", "dialing"),
        ("ringing", "ringing"),
        ("in-progress", "connected"),
        ("completed", "failed"),
        ("canceled", "cancelled"),
        ("busy", "failed"),
        ("failed", "failed"),
        ("no-answer", "failed"),
    ],
)
def test_twilio_status_callback_updates_public_call_status(
    provider_status: str,
    public_status: str,
) -> None:
    transport = HoldingTelephony()
    app = create_app(_settings(provider="real"), telephony=transport)

    with TestClient(app) as client:
        started = client.post("/v1/calls", json=_payload(), headers=_start_headers())
        call_id = started.json()["call_id"]
        path = f"/twilio/status?call_id={call_id}"
        form = {"CallStatus": provider_status}
        callback = client.post(
            path,
            data=form,
            headers={"X-Twilio-Signature": _twilio_signature(path, form)},
        )
        status = client.get(f"/v1/calls/{call_id}", headers=_auth())

    assert callback.status_code == 200
    assert callback.json() == {"ok": True}
    assert status.json()["status"] == public_status
    if provider_status == "completed":
        assert status.json()["error_code"] == "missing_outcome"


def test_terminal_carrier_failure_cannot_be_overwritten_by_completed_callback() -> None:
    transport = HoldingTelephony()
    app = create_app(_settings(provider="real"), telephony=transport)

    with TestClient(app) as client:
        started = client.post("/v1/calls", json=_payload(), headers=_start_headers())
        call_id = started.json()["call_id"]
        path = f"/twilio/status?call_id={call_id}"
        for provider_status in ("no-answer", "completed"):
            form = {"CallStatus": provider_status}
            callback = client.post(
                path,
                data=form,
                headers={"X-Twilio-Signature": _twilio_signature(path, form)},
            )
            assert callback.status_code == 200
        status = client.get(f"/v1/calls/{call_id}", headers=_auth())

    assert status.json()["status"] == "failed"
    assert status.json()["error_code"] == "carrier_no_answer"


def test_twilio_status_for_unknown_call_has_no_effect() -> None:
    app = create_app(_settings(provider="real"), telephony=HoldingTelephony())

    with TestClient(app) as client:
        response = client.post(
            "/twilio/status?call_id=unknown",
            data={"CallStatus": "completed"},
        )

    assert response.status_code == 404
    assert response.json() == {"error": "not_found"}


def test_mock_readiness_never_claims_real_transport_configuration() -> None:
    settings = Settings(telephony_provider="mock")
    app = create_app(settings, telephony=MockTelephony())

    with TestClient(app) as client:
        response = client.get("/readyz")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["missing"] == []
    assert response.json()["configuration"]["telephony_provider"] == "mock"
    assert response.json()["configuration"]["twilio_configured"] is False


def test_real_readiness_reports_missing_names_without_exposing_credentials() -> None:
    settings = Settings(
        deepgram_api_key="dg-secret",
        endpoint_secret="endpoint-secret",
        telephony_provider="real",
    )
    app = create_app(settings, telephony=HoldingTelephony())

    with TestClient(app) as client:
        response = client.get("/readyz")

    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"
    assert "TWILIO_AUTH_TOKEN" in response.json()["missing"]
    assert "dg-secret" not in response.text
    assert "endpoint-secret" not in response.text


def test_transport_error_marks_reserved_call_failed_without_leaking_provider_error() -> None:
    class FailingTelephony(HoldingTelephony):
        async def place_call(self, request: CallRequest, call_id: str) -> str:
            self.calls.append((request, call_id))
            raise TelephonyError("provider detail with twilio-secret")

    app = create_app(_settings(provider="real"), telephony=FailingTelephony())

    with TestClient(app) as client:
        response = client.post("/v1/calls", json=_payload(), headers=_start_headers())

    assert response.status_code == 502
    assert response.json() == {"error": "carrier_error"}
    assert "twilio-secret" not in response.text


def test_idempotency_key_is_required_before_transport_action() -> None:
    transport = RecordingMockTelephony()
    app = create_app(_settings(), telephony=transport)

    with TestClient(app) as client:
        response = client.post("/v1/calls", json=_payload(), headers=_auth())

    assert response.status_code == 400
    assert response.json() == {"error": "invalid_idempotency_key"}
    assert transport.calls == []


def test_same_idempotency_key_replays_without_a_second_transport_action() -> None:
    transport = HoldingTelephony()
    app = create_app(_settings(provider="real"), telephony=transport)
    headers = _start_headers("stable-replay-key")

    with TestClient(app) as client:
        first = client.post("/v1/calls", json=_payload(), headers=headers)
        replay = client.post("/v1/calls", json=_payload(), headers=headers)

    assert first.status_code == 202
    assert first.json()["replayed"] is False
    assert replay.status_code == 202
    assert replay.json()["replayed"] is True
    assert replay.json()["call_id"] == first.json()["call_id"]
    assert len(transport.calls) == 1


def test_reusing_idempotency_key_for_different_request_is_a_conflict() -> None:
    transport = HoldingTelephony()
    app = create_app(_settings(provider="real"), telephony=transport)
    headers = _start_headers("conflicting-key")

    with TestClient(app) as client:
        first = client.post("/v1/calls", json=_payload(), headers=headers)
        conflict = client.post(
            "/v1/calls",
            json=_payload(intent="Different intent"),
            headers=headers,
        )

    assert first.status_code == 202
    assert conflict.status_code == 409
    assert conflict.json() == {"error": "idempotency_conflict"}
    assert len(transport.calls) == 1


def test_ginse_handoff_fields_are_part_of_server_idempotency_fingerprint() -> None:
    transport = HoldingTelephony()
    app = create_app(_settings(provider="real"), telephony=transport)
    headers = _start_headers("receipt-fingerprint-key")

    with TestClient(app) as client:
        first = client.post("/v1/calls", json=_payload(), headers=headers)
        conflict = client.post(
            "/v1/calls",
            json=_payload(demo_session_id="demo_fedcba9876543210"),
            headers=headers,
        )

    assert first.status_code == 202
    assert conflict.status_code == 409
    assert conflict.json() == {"error": "idempotency_conflict"}
    assert len(transport.calls) == 1


def test_ginse_only_mode_needs_no_voice_credentials_and_closes_call_routes(
    tmp_path: Path,
) -> None:
    settings = Settings(
        public_url="https://provider.example.test",
        ginse_public_key_pem="unused-injected-key",
        ginse_audience="fredo-provider",
        ginse_ownership_token="ownership-token-at-least-16",
    )
    store = SQLiteIdempotencyStore(tmp_path / "ginse.sqlite3")
    app = create_app(
        settings,
        ginse_only=True,
        ginse_bearer_validator=lambda _authorization: {"sub": "ginse"},
        ginse_store=store,
    )

    with TestClient(app) as client:
        readiness = client.get("/readyz")
        disabled = client.post("/v1/calls", json=_payload())
        manifest = client.get("/.well-known/ginse.json")
        run = client.post(
            "/run",
            json={"platform": "macos-arm64", "profile": PROFILE},
            headers={
                "Authorization": "Bearer structurally-opaque",
                "Idempotency-Key": "ginse-only-mode-test",
            },
        )

    assert readiness.status_code == 200
    assert readiness.json()["mode"] == "ginse-provider"
    assert readiness.json()["status"] == "ready"
    assert disabled.status_code == 404
    assert manifest.status_code == 200
    assert run.status_code == 200
    assert run.json()["status"] == "succeeded"


def test_ginse_only_readiness_reports_only_provider_configuration() -> None:
    app = create_app(Settings(), ginse_only=True)

    with TestClient(app) as client:
        response = client.get("/readyz")

    assert response.status_code == 503
    assert response.json()["mode"] == "ginse-provider"
    assert "DEEPGRAM_API_KEY" not in response.json()["missing"]
    assert "TWILIO_ACCOUNT_SID" not in response.json()["missing"]
    assert "FREDO_GINSE_PUBLIC_KEY_PEM" in response.json()["missing"]


@pytest.mark.asyncio
async def test_ginse_authentication_fails_before_request_body_is_read(tmp_path: Path) -> None:
    settings = Settings(
        public_url="https://provider.example.test",
        ginse_public_key_pem="unused-injected-key",
        ginse_audience="fredo-provider",
        ginse_ownership_token="ownership-token-at-least-16",
    )

    def reject(_authorization: str | None) -> dict[str, object]:
        raise AuthenticationError("invalid bearer token")

    app = create_app(
        settings,
        ginse_only=True,
        ginse_bearer_validator=reject,
        ginse_store=SQLiteIdempotencyStore(tmp_path / "ginse.sqlite3"),
    )

    status, body, reads = await _raw_ginse_request(
        app,
        headers=[(b"authorization", b"Bearer secret-canary")],
        chunks=[(b'{"platform":"macos-arm64"}', False)],
    )

    assert status == 401
    assert body == {"error": "unauthorized", "message": "invalid bearer token"}
    assert reads == 0
    assert "secret-canary" not in json.dumps(body)


@pytest.mark.asyncio
async def test_ginse_streaming_body_limit_rejects_chunked_payload(tmp_path: Path) -> None:
    settings = Settings(
        public_url="https://provider.example.test",
        ginse_public_key_pem="unused-injected-key",
        ginse_audience="fredo-provider",
        ginse_ownership_token="ownership-token-at-least-16",
    )
    app = create_app(
        settings,
        ginse_only=True,
        ginse_bearer_validator=lambda _authorization: {"sub": "ginse"},
        ginse_store=SQLiteIdempotencyStore(tmp_path / "ginse.sqlite3"),
    )

    status, body, reads = await _raw_ginse_request(
        app,
        headers=[
            (b"authorization", b"Bearer opaque"),
            (b"idempotency-key", b"chunked-body-limit"),
            (b"transfer-encoding", b"chunked"),
        ],
        chunks=[(b"x" * 3000, True), (b"x" * 1200, False)],
    )

    assert status == 413
    assert body == {"error": "payload_too_large"}
    assert reads == 2


def test_unsigned_twilio_callback_is_rejected_without_status_mutation() -> None:
    transport = HoldingTelephony()
    app = create_app(_settings(provider="real"), telephony=transport)

    with TestClient(app) as client:
        started = client.post("/v1/calls", json=_payload(), headers=_start_headers())
        call_id = started.json()["call_id"]
        callback = client.post(
            f"/twilio/status?call_id={call_id}",
            data={"CallStatus": "completed"},
        )
        status = client.get(f"/v1/calls/{call_id}", headers=_auth())

    assert callback.status_code == 403
    assert callback.json() == {"error": "invalid_twilio_signature"}
    assert status.json()["status"] == "dialing"
