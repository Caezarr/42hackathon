from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field
from typing import Any, Callable

import pytest
from deepgram.agent.v1 import AgentV1FunctionCallRequest
from deepgram.agent.v1.types.agent_v1function_call_request_functions_item import (
    AgentV1FunctionCallRequestFunctionsItem,
)

import fredo.voice_agent as voice_agent_module
from fredo.settings import Settings
from fredo.voice_agent import VoiceAgentSession


@dataclass
class FakeConnection:
    media: list[bytes] = field(default_factory=list)
    function_responses: list[Any] = field(default_factory=list)

    async def send_media(self, audio: bytes) -> None:
        self.media.append(audio)

    async def send_function_call_response(self, response: Any) -> None:
        self.function_responses.append(response)


@dataclass
class RecordingTelephony:
    hangups: list[str] = field(default_factory=list)

    async def place_call(self, *_args: object, **_kwargs: object) -> str:
        raise AssertionError("not used")

    async def hangup(self, provider_call_id: str) -> None:
        self.hangups.append(provider_call_id)


@dataclass
class ScriptedWebSocket:
    inbound: list[dict[str, object]] = field(default_factory=list)
    sent: list[dict[str, object]] = field(default_factory=list)
    before_receive: Callable[[int], None] | None = None
    session: VoiceAgentSession | None = None
    receive_count: int = 0

    async def receive_text(self) -> str:
        index = self.receive_count
        self.receive_count += 1
        if self.before_receive:
            self.before_receive(index)
        return json.dumps(self.inbound.pop(0))

    async def send_json(self, payload: dict[str, object]) -> None:
        self.sent.append(payload)
        if payload.get("event") == "mark" and self.session is not None:
            self.session._playback_mark_ack.set()


async def _noop(*_args: object) -> None:
    return None


def _session(
    websocket: ScriptedWebSocket,
    telephony: RecordingTelephony | None = None,
    *,
    on_outcome: Callable[[dict[str, object]], Any] = _noop,
) -> VoiceAgentSession:
    session = VoiceAgentSession(
        twilio_ws=websocket,  # type: ignore[arg-type]
        stream_sid="MZ-stream",
        provider_call_id="CA-call",
        intent="Vérifier la démonstration",
        settings=Settings(deepgram_api_key="configured"),
        telephony=telephony or RecordingTelephony(),
        on_transcript=_noop,
        on_outcome=on_outcome,
    )
    websocket.session = session
    return session


@pytest.mark.asyncio
async def test_pre_settings_twilio_audio_is_drained_but_not_forwarded() -> None:
    pre_settings = base64.b64encode(b"stale-hello").decode("ascii")
    live_audio = base64.b64encode(b"live-answer").decode("ascii")
    websocket = ScriptedWebSocket(
        inbound=[
            {"event": "media", "media": {"payload": pre_settings}},
            {"event": "media", "media": {"payload": live_audio}},
            {"event": "stop"},
        ]
    )
    session = _session(websocket)
    connection = FakeConnection()
    session._connection = connection
    websocket.before_receive = (
        lambda index: session._forward_twilio_audio.set() if index == 1 else None
    )

    await session._listen_twilio()

    assert connection.media == [b"live-answer"]


@pytest.mark.asyncio
async def test_matching_twilio_mark_acknowledges_buffer_playback() -> None:
    websocket = ScriptedWebSocket(
        inbound=[
            {"event": "mark", "mark": {"name": "fredo-finish"}},
            {"event": "stop"},
        ]
    )
    session = _session(websocket)
    session._playback_mark_name = "fredo-finish"

    await session._listen_twilio()

    assert session._playback_mark_ack.is_set()


@pytest.mark.asyncio
@pytest.mark.parametrize("audio_done_before_function", [False, True])
async def test_finish_hangup_covers_both_deepgram_event_orders(
    monkeypatch: pytest.MonkeyPatch,
    audio_done_before_function: bool,
) -> None:
    monkeypatch.setattr(
        voice_agent_module,
        "FINISH_POST_FUNCTION_AUDIO_GRACE_SECONDS",
        0.001,
    )
    monkeypatch.setattr(voice_agent_module, "FINISH_AUDIO_DONE_TIMEOUT_SECONDS", 0.1)
    monkeypatch.setattr(voice_agent_module, "FINISH_MARK_TIMEOUT_SECONDS", 0.1)
    outcomes: list[dict[str, object]] = []

    async def record_outcome(outcome: dict[str, object]) -> None:
        outcomes.append(outcome)

    websocket = ScriptedWebSocket()
    telephony = RecordingTelephony()
    session = _session(websocket, telephony, on_outcome=record_outcome)
    connection = FakeConnection()
    session._connection = connection
    session._agent_audio_done_is_current = audio_done_before_function
    if audio_done_before_function:
        session._agent_audio_done.set()
    event = AgentV1FunctionCallRequest(
        functions=[
            AgentV1FunctionCallRequestFunctionsItem(
                id="function-1",
                name="finish_demo",
                arguments=json.dumps(
                    {
                        "works": True,
                        "answer": "Oui, ça fonctionne.",
                        "summary": "Le juge confirme que la démonstration fonctionne.",
                    }
                ),
                client_side=True,
            )
        ]
    )

    await session._handle_function_call(event)
    assert session._finish_task is not None
    if not audio_done_before_function:
        session._agent_audio_done_is_current = True
        session._agent_audio_done.set()
    await session._finish_task

    assert outcomes == [
        {
            "works": True,
            "answer": "Oui, ça fonctionne.",
            "summary": "Le juge confirme que la démonstration fonctionne.",
        }
    ]
    assert len(connection.function_responses) == 1
    assert websocket.sent[-1] == {
        "event": "mark",
        "streamSid": "MZ-stream",
        "mark": {"name": "fredo-finish"},
    }
    assert telephony.hangups == ["CA-call"]
