from __future__ import annotations

import asyncio
import hmac
import json
import logging
import os
from datetime import UTC, datetime, timedelta
from urllib.parse import urlsplit
from uuid import uuid4

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route, WebSocketRoute
from starlette.websockets import WebSocket, WebSocketDisconnect

from .models import CallRequest, CallStatus
from .ginse import (
    BearerValidator,
    Ed25519BearerValidator,
    ProviderError,
    SQLiteIdempotencyStore,
    build_manifest,
    debug_auth_claims,
    debug_input_shape,
    prepare_fredo_demo_run,
)
from .policy import PolicyError, normalize_e164, validate_call_request
from .registry import CallBusyError, CallRegistry, IdempotencyConflictError
from .security import validate_twilio_signature
from .settings import Settings
from .telephony import MockTelephony, Telephony, TelephonyError, telephony_from_settings
from .voice_agent import VoiceAgentSession

logger = logging.getLogger(__name__)

GINSE_MAX_BODY_BYTES = 4096


class _GinsePayloadTooLarge(ValueError):
    pass


class _GinseInvalidContentLength(ValueError):
    pass


class HostedRequestError(ProviderError):
    def __init__(self, code: str, message: str, status_code: int):
        self.code = code
        self.status_code = status_code
        super().__init__(message)


async def _read_ginse_json(request: Request) -> object:
    """Read one Ginse request without trusting Content-Length as the limit."""

    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            declared_length = int(content_length)
        except ValueError as exc:
            raise _GinseInvalidContentLength from exc
        if declared_length < 0:
            raise _GinseInvalidContentLength
        if declared_length > GINSE_MAX_BODY_BYTES:
            raise _GinsePayloadTooLarge

    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > GINSE_MAX_BODY_BYTES:
            raise _GinsePayloadTooLarge
        body.extend(chunk)
    return json.loads(body)


def missing_for_ginse_provider(settings: Settings) -> list[str]:
    """Return provider-only readiness gaps without exposing configured values."""

    missing: list[str] = []
    if not settings.ginse_public_key_pem:
        missing.append("FREDO_GINSE_PUBLIC_KEY_PEM")
    if not settings.ginse_audience:
        missing.append("FREDO_GINSE_AUDIENCE")
    if not settings.ginse_ownership_token or len(settings.ginse_ownership_token) < 16:
        missing.append("FREDO_GINSE_OWNERSHIP_TOKEN")
    if not settings.public_url:
        missing.append("FREDO_PUBLIC_URL")
    else:
        parsed = urlsplit(settings.public_url)
        if parsed.scheme != "https" or not parsed.netloc:
            missing.append("FREDO_PUBLIC_URL")
    return missing


def _authorized(request: Request, settings: Settings) -> bool:
    if not settings.endpoint_secret:
        return False
    expected = f"Bearer {settings.endpoint_secret}"
    supplied = request.headers.get("authorization", "")
    return hmac.compare_digest(supplied, expected)


def create_app(
    settings: Settings | None = None,
    *,
    telephony: Telephony | None = None,
    registry: CallRegistry | None = None,
    ginse_bearer_validator: BearerValidator | None = None,
    ginse_store: SQLiteIdempotencyStore | None = None,
    ginse_only: bool = False,
) -> Starlette:
    settings = settings or Settings.from_env()
    registry = registry or CallRegistry()
    if telephony is None and not ginse_only:
        telephony = telephony_from_settings(settings)

    ginse_configured = not missing_for_ginse_provider(settings)
    if ginse_configured and ginse_bearer_validator is None:
        ginse_bearer_validator = Ed25519BearerValidator(
            public_key_pem=settings.ginse_public_key_pem or "",
            issuer=settings.ginse_issuer,
            audience=settings.ginse_audience or "",
        )
    if ginse_configured and ginse_store is None:
        settings.ginse_database.parent.mkdir(parents=True, exist_ok=True)
        ginse_store = SQLiteIdempotencyStore(settings.ginse_database)

    async def home(request: Request) -> JSONResponse:
        del request
        return JSONResponse(
            {
                "name": "fredo",
                "version": "0.1.0",
                "status": "running",
                "mode": "ginse-provider" if ginse_only else "voice",
                "docs": "https://github.com/Caezarr/42hackathon",
            }
        )

    async def health(request: Request) -> JSONResponse:
        del request
        return JSONResponse({"status": "ok"})

    async def ready(request: Request) -> JSONResponse:
        del request
        if ginse_only:
            missing = missing_for_ginse_provider(settings)
        else:
            missing = settings.missing_for_real_call()
            if os.getenv("FREDO_HOSTED_MODE") == "1":
                missing = [item for item in missing if item not in {"FREDO_ENDPOINT_SECRET", "FREDO_ALLOWED_NUMBERS"}]
            if isinstance(telephony, MockTelephony):
                missing = []
        payload = {
                "status": "ready" if not missing else "not_ready",
                "missing": missing,
                "mode": "ginse-provider" if ginse_only else "voice",
                "configuration": settings.public_summary(),
            }
        if os.getenv("FREDO_GINSE_DEBUG_AUTH") == "1":
            payload["auth_debug"] = debug_auth_claims()
            payload["input_debug"] = debug_input_shape()
        return JSONResponse(payload, status_code=200 if not missing else 503)

    async def ginse_manifest(request: Request) -> JSONResponse:
        del request
        if not settings.public_url or not settings.ginse_ownership_token:
            return JSONResponse({"error": "ginse_not_configured"}, status_code=503)
        try:
            manifest = build_manifest(
                f"{settings.public_url.rstrip('/')}/run",
                settings.ginse_ownership_token,
            )
        except ValueError:
            return JSONResponse({"error": "ginse_not_configured"}, status_code=503)
        return JSONResponse(manifest)

    async def hosted_manifest(request: Request) -> JSONResponse:
        del request
        token = os.getenv("FREDO_HOSTED_OWNERSHIP_TOKEN")
        if not settings.public_url or not token:
            return JSONResponse({"error": "hosted_ginse_not_configured"}, status_code=503)
        return JSONResponse({
            "schema_version": "2",
            "slug": "fredo-phone",
            "display_name": "Fredo Phone — Team Fredo",
            "description": "Execute a consented phone task from a natural-language request.",
            "presentation": {
                "action": "Execute a phone task",
                "input": {"label": "Call request", "icon": "audio"},
                "output": {"label": "Call result", "icon": "audio"},
            },
            "price": {"amount_cents": 42, "currency": "EUR"},
            "run_url": f"{settings.public_url.rstrip('/')}/run",
            "input_schema": json.loads(open("schemas/hosted-phone-input.schema.json", encoding="utf-8").read()),
            "output_schema": json.loads(open("schemas/hosted-phone-output.schema.json", encoding="utf-8").read()),
            "example": {"input": json.loads(open("schemas/hosted-phone-example-input.json", encoding="utf-8").read())},
            "ownership_token": token,
        })

    async def ginse_run(request: Request) -> JSONResponse:
        if ginse_bearer_validator is None or ginse_store is None:
            return JSONResponse({"error": "ginse_not_configured"}, status_code=503)

        authorization = request.headers.get("authorization")
        try:
            await asyncio.to_thread(ginse_bearer_validator, authorization)
        except ProviderError as exc:
            return JSONResponse(
                {"error": exc.code, "message": str(exc)},
                status_code=exc.status_code,
            )
        except Exception:
            # Authentication failures must not log the bearer token or decoder details.
            logger.error("Unexpected Ginse authentication error")
            return JSONResponse({"error": "provider_error"}, status_code=500)

        try:
            payload = await _read_ginse_json(request)
        except _GinsePayloadTooLarge:
            return JSONResponse({"error": "payload_too_large"}, status_code=413)
        except _GinseInvalidContentLength:
            return JSONResponse({"error": "invalid_content_length"}, status_code=400)
        except Exception:
            return JSONResponse({"error": "invalid_json"}, status_code=400)

        provider_payload = payload
        if isinstance(payload, dict) and isinstance(payload.get("input"), dict):
            provider_payload = payload["input"]
        if isinstance(provider_payload, dict) and {"platform", "profile"}.issubset(provider_payload):
            provider_payload = {
                "platform": provider_payload["platform"],
                "profile": provider_payload["profile"],
            }

        if isinstance(provider_payload, dict) and provider_payload.get("profile") == "hosted-phone":
            try:
                if telephony is None:
                    raise HostedRequestError("provider_unavailable", "Hosted telephony is not enabled", 503)
                identity = provider_payload.get("caller_identity")
                destination = normalize_e164(provider_payload.get("destination_phone"))
                goal = provider_payload.get("call_goal")
                if not isinstance(identity, str) or not identity.strip():
                    raise HostedRequestError("invalid_input", "caller_identity is required", 422)
                if not isinstance(goal, str) or not goal.strip():
                    raise HostedRequestError("invalid_input", "call_goal is required", 422)
                if provider_payload.get("consent_confirmed") is not True:
                    raise HostedRequestError("consent_required", "consent_confirmed must be true", 422)
                if len(goal.strip()) > 500:
                    raise HostedRequestError("invalid_input", "call_goal is too long", 422)
                normalized_goal = " ".join(goal.split())
                french_markers = (" français", " francaise", " française", " en français", " bonjour", " réservation", " demander", " demande", " est-ce", " peux-tu", " tu ")
                language_prefix = "[language=fr]" if any(marker in normalized_goal.lower() for marker in french_markers) else ""
                hosted_request = CallRequest(
                    to=destination,
                    intent=f"{language_prefix}Caller {identity.strip()} asks you to: {normalized_goal}",
                    consent=True,
                    confirmed=True,
                    profile="hosted-phone",
                    demo_session_id=f"hosted_{uuid4().hex}",
                    expires_at=(datetime.now(UTC) + timedelta(minutes=20)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                )
                key = request.headers.get("idempotency-key") or f"hosted-{uuid4().hex}"
                record, replayed = await registry.reserve(hosted_request, idempotency_key=key)
                if not replayed:
                    provider_call_id = await telephony.place_call(hosted_request, record.call_id)
                    await registry.bind_twilio(record.call_id, provider_call_id)
                snapshot = await registry.snapshot(record.call_id)
                return JSONResponse({
                    "status": "succeeded",
                    "provider_operation_id": record.call_id,
                    "replayed": replayed,
                    "output": {"product": "fredo", "profile": "hosted-phone", "call_id": record.call_id, "status": snapshot["status"] if snapshot else "dialing"},
                })
            except ProviderError as exc:
                return JSONResponse({"error": exc.code, "message": str(exc)}, status_code=exc.status_code)
            except (PolicyError, CallBusyError, IdempotencyConflictError, TelephonyError) as exc:
                return JSONResponse({"error": "call_rejected", "message": str(exc)}, status_code=422)

        try:
            run_result = await asyncio.to_thread(
                prepare_fredo_demo_run,
                ginse_store,
                idempotency_key=request.headers.get("idempotency-key"),
                payload=provider_payload,
            )
            return JSONResponse(run_result.as_dict(), status_code=200)
        except ProviderError as exc:
            if os.getenv("FREDO_GINSE_DEBUG_AUTH") == "1":
                _debug_input = provider_payload if isinstance(provider_payload, dict) else {}
                from . import ginse as _ginse_module

                _ginse_module._DEBUG_INPUT.clear()
                _ginse_module._DEBUG_INPUT.update(
                    {"type": type(payload).__name__, "keys": sorted(_debug_input.keys())}
                )
            return JSONResponse({"error": exc.code, "message": str(exc)}, status_code=exc.status_code)
        except Exception:
            logger.exception("Unexpected Ginse provider error")
            return JSONResponse({"error": "provider_error"}, status_code=500)

    async def finalize_voice_call(
        call_id: str, *, missing_outcome_error: str = "missing_outcome"
    ) -> None:
        current = await registry.get(call_id)
        if current is None:
            return
        if current.outcome is not None and current.error_code is None:
            await registry.update(call_id, CallStatus.COMPLETED)
            return
        await registry.update(
            call_id,
            CallStatus.FAILED,
            error_code=current.error_code or missing_outcome_error,
        )

    async def start_call(request: Request) -> JSONResponse:
        if ginse_only:
            return JSONResponse({"error": "call_api_disabled"}, status_code=503)
        if not _authorized(request, settings):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        try:
            idempotency_key = request.headers.get("idempotency-key", "")
            if not 8 <= len(idempotency_key) <= 200:
                return JSONResponse({"error": "invalid_idempotency_key"}, status_code=400)
            payload = await request.json()
            call_request = validate_call_request(payload, settings)
            record, replayed = await registry.reserve(
                call_request,
                idempotency_key=idempotency_key,
            )
            if replayed:
                snapshot = await registry.snapshot(record.call_id)
                return JSONResponse({**(snapshot or {}), "replayed": True}, status_code=202)
            provider_call_id = await telephony.place_call(call_request, record.call_id)
            if await registry.bind_twilio(record.call_id, provider_call_id) is None:
                raise TelephonyError("Carrier call identity mismatch")
            if isinstance(telephony, MockTelephony):
                await registry.update(
                    record.call_id,
                    CallStatus.COMPLETED,
                    outcome={
                        "mock": True,
                        "works": False,
                        "answer": "No real call placed",
                        "summary": "No real call placed",
                    },
                )
            snapshot = await registry.snapshot(record.call_id)
            return JSONResponse({**(snapshot or {}), "replayed": False}, status_code=202)
        except PolicyError as exc:
            return JSONResponse({"error": exc.code, "message": str(exc)}, status_code=422)
        except CallBusyError:
            return JSONResponse({"error": "call_in_progress"}, status_code=409)
        except IdempotencyConflictError:
            return JSONResponse({"error": "idempotency_conflict"}, status_code=409)
        except TelephonyError:
            if "record" in locals():
                await registry.update(record.call_id, CallStatus.FAILED, error_code="carrier_error")
            return JSONResponse({"error": "carrier_error"}, status_code=502)
        except Exception:
            logger.exception("Unexpected error while starting a call")
            if "record" in locals():
                await registry.update(record.call_id, CallStatus.FAILED, error_code="internal_error")
            return JSONResponse({"error": "internal_error"}, status_code=500)

    async def call_status(request: Request) -> JSONResponse:
        if ginse_only:
            return JSONResponse({"error": "call_api_disabled"}, status_code=503)
        if not _authorized(request, settings):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        snapshot = await registry.snapshot(request.path_params["call_id"])
        if snapshot is None:
            return JSONResponse({"error": "not_found"}, status_code=404)
        return JSONResponse(snapshot)

    async def twilio_status(request: Request) -> JSONResponse:
        if ginse_only:
            return JSONResponse({"error": "call_api_disabled"}, status_code=503)
        call_id = request.query_params.get("call_id")
        if not call_id or not await registry.get(call_id):
            return JSONResponse({"error": "not_found"}, status_code=404)
        form = await request.form()
        path_and_query = request.url.path
        if request.url.query:
            path_and_query += f"?{request.url.query}"
        if not isinstance(telephony, MockTelephony) and not validate_twilio_signature(
            settings,
            path_and_query=path_and_query,
            params=dict(form),
            signature=request.headers.get("x-twilio-signature"),
        ):
            return JSONResponse({"error": "invalid_twilio_signature"}, status_code=403)
        provider_status = str(form.get("CallStatus", "")).lower()
        status_map = {
            "initiated": CallStatus.DIALING,
            "queued": CallStatus.DIALING,
            "ringing": CallStatus.RINGING,
            "in-progress": CallStatus.CONNECTED,
            "canceled": CallStatus.CANCELLED,
            "busy": CallStatus.FAILED,
            "failed": CallStatus.FAILED,
            "no-answer": CallStatus.FAILED,
        }
        if provider_status == "completed":
            await finalize_voice_call(call_id)
        elif provider_status in status_map:
            error_code = {
                "canceled": "carrier_canceled",
                "busy": "carrier_busy",
                "failed": "carrier_failed",
                "no-answer": "carrier_no_answer",
            }.get(provider_status)
            await registry.update(
                call_id,
                status_map[provider_status],
                error_code=error_code,
            )
        return JSONResponse({"ok": True})

    async def twilio_media(websocket: WebSocket) -> None:
        if ginse_only:
            await websocket.close(code=1008)
            return
        if not isinstance(telephony, MockTelephony) and not validate_twilio_signature(
            settings,
            path_and_query=websocket.url.path,
            params={},
            signature=websocket.headers.get("x-twilio-signature"),
            websocket=True,
        ):
            await websocket.close(code=1008)
            return
        await websocket.accept()
        call_id: str | None = None
        try:
            while True:
                data = await websocket.receive_json()
                if data.get("event") == "connected":
                    continue
                if data.get("event") != "start":
                    continue
                start = data.get("start", {})
                call_id = start.get("customParameters", {}).get("fredoCallId")
                stream_sid = start.get("streamSid")
                provider_call_id = start.get("callSid")
                break

            if not call_id or not stream_sid or not provider_call_id:
                await websocket.close(code=1008)
                return
            record = await registry.bind_twilio(call_id, provider_call_id)
            if record is None:
                await websocket.close(code=1008)
                return

            await registry.update(call_id, CallStatus.CONNECTED)

            async def on_transcript(role: str, content: str) -> None:
                await registry.append_transcript(call_id or "", role, content)

            async def on_outcome(outcome: dict[str, object]) -> None:
                await registry.update(call_id or "", CallStatus.CONNECTED, outcome=outcome)

            session = VoiceAgentSession(
                twilio_ws=websocket,
                stream_sid=stream_sid,
                provider_call_id=provider_call_id,
                intent=record.intent,
                settings=settings,
                telephony=telephony,
                on_transcript=on_transcript,
                on_outcome=on_outcome,
            )
            await session.run()
            await finalize_voice_call(call_id)
        except WebSocketDisconnect:
            if call_id and await registry.get(call_id):
                await finalize_voice_call(
                    call_id,
                    missing_outcome_error="stream_disconnected",
                )
        except Exception:
            logger.exception("Voice session failed")
            if call_id and await registry.get(call_id):
                await registry.update(call_id, CallStatus.FAILED, error_code="voice_error")
            try:
                await websocket.close(code=1011)
            except Exception:
                pass

    routes = [
        Route("/", home),
        Route("/healthz", health),
        Route("/readyz", ready),
        Route("/.well-known/ginse.json", ginse_manifest, methods=["GET"]),
        Route("/.well-known/fredo-phone.json", hosted_manifest, methods=["GET"]),
        Route("/run", ginse_run, methods=["POST"]),
    ]
    if not ginse_only:
        routes.extend(
            [
                Route("/v1/calls", start_call, methods=["POST"]),
                Route("/v1/calls/{call_id}", call_status, methods=["GET"]),
                Route("/twilio/status", twilio_status, methods=["POST"]),
                WebSocketRoute("/twilio/media", twilio_media),
            ]
        )
    app = Starlette(routes=routes)
    app.state.settings = settings
    app.state.registry = registry
    app.state.telephony = telephony
    app.state.ginse_only = ginse_only
    return app


app = create_app()
