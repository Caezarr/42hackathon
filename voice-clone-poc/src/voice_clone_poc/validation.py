from __future__ import annotations

import wave
from dataclasses import dataclass
from pathlib import Path


MIN_REFERENCE_SECONDS = 8.0
MAX_REFERENCE_SECONDS = 45.0
MAX_TEXT_LENGTH = 400


class InputError(ValueError):
    """An error that can be shown directly to the local user."""


@dataclass(frozen=True)
class WavMetadata:
    duration_seconds: float
    channels: int
    sample_rate: int


def validate_metadata(metadata: WavMetadata) -> None:
    if metadata.duration_seconds < MIN_REFERENCE_SECONDS:
        raise InputError("L'échantillon doit durer au moins 8 secondes.")
    if metadata.duration_seconds > MAX_REFERENCE_SECONDS:
        raise InputError("L'échantillon doit durer au maximum 45 secondes.")
    if metadata.channels not in (1, 2):
        raise InputError("Le WAV doit être mono ou stéréo.")
    if metadata.sample_rate < 16_000:
        raise InputError("Utilise un WAV d'au moins 16 kHz.")


def validate_reference(path_value: str | None) -> Path:
    if not path_value:
        raise InputError("Ajoute ou enregistre un échantillon vocal WAV.")

    path = Path(path_value)
    if not path.is_file():
        raise InputError("Le fichier vocal est introuvable.")
    if path.suffix.lower() != ".wav":
        raise InputError("Pour ce POC, utilise un fichier WAV.")

    try:
        with wave.open(str(path), "rb") as wav_file:
            frame_rate = wav_file.getframerate()
            frame_count = wav_file.getnframes()
            metadata = WavMetadata(
                duration_seconds=frame_count / frame_rate if frame_rate else 0,
                channels=wav_file.getnchannels(),
                sample_rate=frame_rate,
            )
    except (EOFError, wave.Error) as exc:
        raise InputError("Le fichier ne semble pas être un WAV PCM valide.") from exc

    validate_metadata(metadata)
    return path


def validate_text(text: str | None) -> str:
    normalized = " ".join((text or "").split())
    if not normalized:
        raise InputError("Écris la phrase à générer.")
    if len(normalized) > MAX_TEXT_LENGTH:
        raise InputError(f"La phrase est limitée à {MAX_TEXT_LENGTH} caractères pour ce POC.")
    return normalized


def require_consent(consent: bool) -> None:
    if not consent:
        raise InputError("Confirme que cette voix est la tienne ou que tu as son autorisation explicite.")
