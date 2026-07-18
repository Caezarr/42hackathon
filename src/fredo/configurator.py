from __future__ import annotations

import getpass
import os
import secrets
from pathlib import Path

from dotenv import dotenv_values

from .policy import normalize_e164


def _secret_prompt(label: str, existing: str | None) -> str:
    suffix = " [déjà configuré, Entrée pour conserver]" if existing else ""
    value = getpass.getpass(f"{label}{suffix}: ").strip()
    if not value and existing:
        return existing
    if not value:
        raise ValueError(f"{label} est requis")
    if "\n" in value or "\r" in value:
        raise ValueError(f"{label} contient un caractère interdit")
    return value


def _plain_prompt(label: str, existing: str | None) -> str:
    suffix = f" [{existing}]" if existing else ""
    value = input(f"{label}{suffix}: ").strip()
    return value or existing or ""


def configure_env(path: Path = Path(".env")) -> Path:
    current = {key: value or "" for key, value in dotenv_values(path).items()}
    deepgram = _secret_prompt("Clé Deepgram", current.get("DEEPGRAM_API_KEY"))
    twilio_sid = _plain_prompt("Twilio Account SID", current.get("TWILIO_ACCOUNT_SID"))
    twilio_token = _secret_prompt("Twilio Auth Token", current.get("TWILIO_AUTH_TOKEN"))
    caller = normalize_e164(
        _plain_prompt("Numéro appelant Twilio (E.164)", current.get("TWILIO_PHONE_NUMBER"))
    )
    allowed = normalize_e164(
        _plain_prompt(
            "Numéro consentant autorisé (E.164, ex. +31636409680)",
            current.get("FREDO_ALLOWED_NUMBERS"),
        )
    )
    if not twilio_sid.startswith("AC"):
        raise ValueError("TWILIO_ACCOUNT_SID doit commencer par AC")

    values = {
        **{
            key: value
            for key, value in current.items()
            if key.startswith("FREDO_GINSE_")
            or key in {"FREDO_PUBLIC_URL", "FREDO_HOST", "FREDO_PORT", "FREDO_STATE_DIR"}
        },
        "DEEPGRAM_API_KEY": deepgram,
        "TWILIO_ACCOUNT_SID": twilio_sid,
        "TWILIO_AUTH_TOKEN": twilio_token,
        "TWILIO_PHONE_NUMBER": caller,
        "FREDO_ALLOWED_NUMBERS": allowed,
        "FREDO_ENDPOINT_SECRET": current.get("FREDO_ENDPOINT_SECRET")
        or secrets.token_urlsafe(32),
        "FREDO_MAX_DURATION_SECONDS": "180",
        "FREDO_MAX_CONCURRENT_CALLS": "1",
        "FREDO_LISTEN_MODEL": "flux-general-multi",
        "FREDO_LISTEN_LANGUAGE": "en",
        "FREDO_LLM_PROVIDER": "open_ai",
        "FREDO_LLM_MODEL": "gpt-4o-mini",
        "FREDO_VOICE_MODEL": "aura-2-thalia-en",
        "FREDO_TELEPHONY_PROVIDER": "real",
    }
    lines = [
        "# Generated locally by `fredo configure`. Never commit this file.",
        *(f"{key}={value}" for key, value in values.items()),
        "",
    ]
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text("\n".join(lines), encoding="utf-8")
    os.chmod(temporary, 0o600)
    temporary.replace(path)
    os.chmod(path, 0o600)
    return path
