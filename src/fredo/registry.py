from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import UTC, datetime
from uuid import uuid4

from .models import CallRecord, CallRequest, CallStatus, TERMINAL_STATUSES
from .policy import destination_hint


class CallBusyError(RuntimeError):
    pass


class IdempotencyConflictError(RuntimeError):
    pass


_NON_TERMINAL_RANK = {
    CallStatus.PREPARED: 0,
    CallStatus.DIALING: 1,
    CallStatus.RINGING: 2,
    CallStatus.CONNECTED: 3,
}


class CallRegistry:
    """Small in-process state store for the one-call hackathon profile."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._calls: dict[str, CallRecord] = {}
        self._twilio_to_call: dict[str, str] = {}
        self._idempotency: dict[str, tuple[str, str]] = {}

    @staticmethod
    def request_fingerprint(request: CallRequest) -> str:
        canonical = json.dumps(
            {
                "confirmed": request.confirmed,
                "consent": request.consent,
                "demo_session_id": request.demo_session_id,
                "expires_at": request.expires_at,
                "intent": request.intent,
                "profile": request.profile,
                "to": request.to,
            },
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()

    async def reserve(
        self,
        request: CallRequest,
        *,
        idempotency_key: str,
    ) -> tuple[CallRecord, bool]:
        async with self._lock:
            fingerprint = self.request_fingerprint(request)
            existing = self._idempotency.get(idempotency_key)
            if existing:
                existing_fingerprint, call_id = existing
                if existing_fingerprint != fingerprint:
                    raise IdempotencyConflictError(
                        "Idempotency-Key was already used for a different call request"
                    )
                return self._calls[call_id], True
            if any(record.status not in TERMINAL_STATUSES for record in self._calls.values()):
                raise CallBusyError("Another Fredo call is already active")
            call_id = str(uuid4())
            record = CallRecord(
                call_id=call_id,
                destination_hint=destination_hint(request.to),
                intent=request.intent,
            )
            self._calls[call_id] = record
            self._idempotency[idempotency_key] = (fingerprint, call_id)
            return record, False

    async def bind_twilio(self, call_id: str, twilio_sid: str) -> CallRecord | None:
        """Atomically bind the first signed Twilio identity to a reserved call.

        Twilio can open its Media Stream before the REST create response reaches
        Fredo. Both paths therefore use this idempotent first-writer binding.
        """

        async with self._lock:
            record = self._calls.get(call_id)
            if record is None:
                return None
            mapped_call_id = self._twilio_to_call.get(twilio_sid)
            if mapped_call_id not in {None, call_id}:
                return None
            if record.twilio_sid not in {None, twilio_sid}:
                return None
            record.twilio_sid = twilio_sid
            if record.status == CallStatus.PREPARED:
                record.status = CallStatus.DIALING
            record.updated_at = datetime.now(UTC)
            self._twilio_to_call[twilio_sid] = call_id
            return record

    async def attach_twilio(self, call_id: str, twilio_sid: str) -> CallRecord:
        record = await self.bind_twilio(call_id, twilio_sid)
        if record is None:
            raise KeyError("Twilio call identity does not match the reservation")
        return record

    async def update(
        self,
        call_id: str,
        status: CallStatus,
        *,
        outcome: dict[str, object] | None = None,
        error_code: str | None = None,
    ) -> CallRecord:
        async with self._lock:
            record = self._calls[call_id]
            if record.status not in TERMINAL_STATUSES:
                if status in TERMINAL_STATUSES:
                    record.status = status
                elif _NON_TERMINAL_RANK[status] >= _NON_TERMINAL_RANK[record.status]:
                    record.status = status
            if outcome is not None:
                record.outcome = outcome
            if error_code is not None:
                record.error_code = error_code
            record.updated_at = datetime.now(UTC)
            return record

    async def append_transcript(self, call_id: str, role: str, content: str) -> None:
        async with self._lock:
            record = self._calls[call_id]
            record.transcript.append({"role": role, "content": content})
            record.updated_at = datetime.now(UTC)

    async def get(self, call_id: str) -> CallRecord | None:
        async with self._lock:
            return self._calls.get(call_id)

    async def by_twilio_sid(self, twilio_sid: str) -> CallRecord | None:
        async with self._lock:
            call_id = self._twilio_to_call.get(twilio_sid)
            return self._calls.get(call_id) if call_id else None

    async def snapshot(self, call_id: str) -> dict[str, object] | None:
        async with self._lock:
            record = self._calls.get(call_id)
            return record.as_public_dict() if record else None
