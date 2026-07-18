from __future__ import annotations

import shutil
import sys
from dataclasses import dataclass

from .policy import FR_MOBILE_RE
from .settings import Settings


@dataclass(frozen=True, slots=True)
class Check:
    name: str
    ok: bool
    detail: str

    def as_dict(self) -> dict[str, object]:
        return {"name": self.name, "status": "pass" if self.ok else "fail", "detail": self.detail}


def run_checks(settings: Settings, *, quick_tunnel: bool) -> list[Check]:
    twilio_ready = bool(
        settings.twilio_account_sid
        and settings.twilio_auth_token
        and settings.twilio_phone_number
    )
    endpoint_ready = bool(settings.endpoint_secret and len(settings.endpoint_secret) >= 24)
    numbers_valid = bool(settings.allowed_numbers) and all(
        FR_MOBILE_RE.fullmatch(number) for number in settings.allowed_numbers
    )
    tunnel_ready = bool(shutil.which("cloudflared")) if quick_tunnel else bool(settings.public_url)
    return [
        Check("runtime.python", sys.version_info >= (3, 12), sys.version.split()[0]),
        Check("voice.deepgram", bool(settings.deepgram_api_key), "configured" if settings.deepgram_api_key else "missing"),
        Check("telephony.twilio", twilio_ready, "configured" if twilio_ready else "missing credentials or caller number"),
        Check("policy.endpoint_auth", endpoint_ready, "configured" if endpoint_ready else "missing or shorter than 24 characters"),
        Check("policy.allowlist", numbers_valid, f"{len(settings.allowed_numbers)} exact destination(s)"),
        Check(
            "network.tunnel",
            tunnel_ready,
            "cloudflared available" if quick_tunnel and tunnel_ready else (
                "public URL configured" if tunnel_ready else "cloudflared/public URL missing"
            ),
        ),
        Check("policy.duration", settings.max_duration_seconds <= 180, f"{settings.max_duration_seconds}s"),
        Check("policy.concurrency", settings.max_concurrent_calls == 1, str(settings.max_concurrent_calls)),
        Check("release.real_transport", settings.telephony_provider == "real", settings.telephony_provider),
    ]


def checks_payload(checks: list[Check]) -> dict[str, object]:
    return {
        "status": "ready" if all(check.ok for check in checks) else "not_ready",
        "checks": [check.as_dict() for check in checks],
    }
