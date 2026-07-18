from __future__ import annotations

from collections.abc import Mapping

from twilio.request_validator import RequestValidator

from .settings import Settings


def validate_twilio_signature(
    settings: Settings,
    *,
    path_and_query: str,
    params: Mapping[str, object],
    signature: str | None,
    websocket: bool = False,
) -> bool:
    if not settings.twilio_auth_token or not settings.public_url or not signature:
        return False
    validator = RequestValidator(settings.twilio_auth_token)
    base = settings.public_url.rstrip("/")
    https_url = f"{base}{path_and_query}"
    if validator.validate(https_url, dict(params), signature):
        return True
    if websocket:
        wss_url = "wss://" + https_url.removeprefix("https://")
        return validator.validate(wss_url, dict(params), signature)
    return False
