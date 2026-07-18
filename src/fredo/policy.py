from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta

from .models import CallRequest, GinseDemoReceipt
from .settings import Settings


E164_RE = re.compile(r"^\+[1-9][0-9]{7,14}$")
FR_MOBILE_RE = re.compile(r"^\+33[67][0-9]{8}$")
GINSE_PROFILE = "hosted-voice-mvp"
GINSE_SESSION_RE = re.compile(r"^demo_[A-Za-z0-9_-]{16,64}$")
GINSE_EXPIRY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
MAX_GINSE_RECEIPT_LIFETIME = timedelta(minutes=20)


class PolicyError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def normalize_e164(value: object) -> str:
    if not isinstance(value, str):
        raise PolicyError("invalid_destination", "Destination must be a string")
    normalized = re.sub(r"[\s().-]", "", value.strip())
    if not E164_RE.fullmatch(normalized):
        raise PolicyError("invalid_destination", "Destination must use canonical E.164")
    return normalized


def validate_ginse_demo_receipt(
    *,
    profile: object,
    demo_session_id: object,
    expires_at: object,
    now: datetime | None = None,
) -> GinseDemoReceipt:
    """Validate a short-lived Ginse marketplace handoff.

    This proves only that the fields match Fredo's closed marketplace contract.
    It deliberately does not claim cryptographic authorization for a phone call.
    """

    if profile != GINSE_PROFILE:
        raise PolicyError("invalid_ginse_profile", "Unsupported Ginse demo profile")
    if not isinstance(demo_session_id, str) or not GINSE_SESSION_RE.fullmatch(
        demo_session_id
    ):
        raise PolicyError("invalid_ginse_receipt", "Invalid Ginse demo session identifier")
    if not isinstance(expires_at, str) or not GINSE_EXPIRY_RE.fullmatch(expires_at):
        raise PolicyError("invalid_ginse_receipt", "Invalid Ginse receipt expiry")
    try:
        expiry = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PolicyError("invalid_ginse_receipt", "Invalid Ginse receipt expiry") from exc

    current = now or datetime.now(UTC)
    if current.tzinfo is None:
        current = current.replace(tzinfo=UTC)
    current = current.astimezone(UTC)
    if expiry <= current:
        raise PolicyError("expired_ginse_receipt", "Ginse demo session has expired")
    if expiry > current + MAX_GINSE_RECEIPT_LIFETIME:
        raise PolicyError(
            "invalid_ginse_receipt",
            "Ginse demo session expiry exceeds the supported lifetime",
        )
    return GinseDemoReceipt(
        profile=GINSE_PROFILE,
        demo_session_id=demo_session_id,
        expires_at=expires_at,
    )


def validate_call_request(
    payload: object,
    settings: Settings,
    *,
    now: datetime | None = None,
) -> CallRequest:
    if not isinstance(payload, dict):
        raise PolicyError("invalid_request", "Request body must be a JSON object")

    allowed_fields = {
        "to",
        "intent",
        "consent",
        "confirmed",
        "profile",
        "demo_session_id",
        "expires_at",
    }
    unknown = sorted(set(payload) - allowed_fields)
    if unknown:
        raise PolicyError("unknown_fields", f"Unknown fields: {', '.join(unknown)}")

    destination = normalize_e164(payload.get("to"))
    if not FR_MOBILE_RE.fullmatch(destination):
        raise PolicyError(
            "unsupported_destination",
            "The hackathon profile only permits French +336/+337 mobile numbers",
        )
    if destination not in settings.allowed_numbers:
        raise PolicyError("destination_not_allowed", "Destination is not pre-enrolled")

    intent = payload.get("intent")
    if not isinstance(intent, str) or not intent.strip():
        raise PolicyError("invalid_intent", "A non-empty call intent is required")
    intent = " ".join(intent.split())
    if len(intent) > 500:
        raise PolicyError("invalid_intent", "Call intent must be at most 500 characters")

    consent = payload.get("consent")
    if consent is not True:
        raise PolicyError("consent_required", "Explicit recipient consent is required")
    confirmed = payload.get("confirmed")
    if confirmed is not True:
        raise PolicyError("confirmation_required", "Native call confirmation is required")

    receipt = validate_ginse_demo_receipt(
        profile=payload.get("profile"),
        demo_session_id=payload.get("demo_session_id"),
        expires_at=payload.get("expires_at"),
        now=now,
    )

    return CallRequest(
        to=destination,
        intent=intent,
        consent=True,
        confirmed=True,
        profile=receipt.profile,
        demo_session_id=receipt.demo_session_id,
        expires_at=receipt.expires_at,
    )


def destination_hint(destination: str) -> str:
    return f"{destination[:4]}••••{destination[-2:]}"
