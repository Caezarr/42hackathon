from __future__ import annotations

import pytest

from fredo.models import CallRequest, CallStatus
from fredo.registry import CallRegistry


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


@pytest.mark.asyncio
async def test_terminal_status_is_sticky_while_error_metadata_can_be_refined() -> None:
    registry = CallRegistry()
    record, _ = await registry.reserve(_request(), idempotency_key="terminal-state-key")

    await registry.update(record.call_id, CallStatus.FAILED, error_code="voice_error")
    await registry.update(record.call_id, CallStatus.COMPLETED)

    snapshot = await registry.snapshot(record.call_id)
    assert snapshot is not None
    assert snapshot["status"] == "failed"
    assert snapshot["error_code"] == "voice_error"


@pytest.mark.asyncio
async def test_non_terminal_status_never_regresses() -> None:
    registry = CallRegistry()
    record, _ = await registry.reserve(_request(), idempotency_key="ordered-state-key")

    await registry.update(record.call_id, CallStatus.RINGING)
    await registry.update(record.call_id, CallStatus.DIALING)

    snapshot = await registry.snapshot(record.call_id)
    assert snapshot is not None
    assert snapshot["status"] == "ringing"


@pytest.mark.asyncio
async def test_twilio_identity_can_bind_from_stream_before_rest_response() -> None:
    registry = CallRegistry()
    record, _ = await registry.reserve(_request(), idempotency_key="stream-race-key")

    stream_binding = await registry.bind_twilio(record.call_id, "CA-first")
    rest_replay = await registry.bind_twilio(record.call_id, "CA-first")
    mismatch = await registry.bind_twilio(record.call_id, "CA-different")

    assert stream_binding is not None
    assert rest_replay is stream_binding
    assert mismatch is None
    assert await registry.by_twilio_sid("CA-first") is stream_binding
