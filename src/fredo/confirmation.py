from __future__ import annotations

import platform
import subprocess

from .settings import Settings


def build_preview(to: str, intent: str, settings: Settings) -> str:
    caller = settings.twilio_phone_number or "identité appelante non configurée"
    return (
        f"Destination : {to}\n"
        f"Identité appelante : {caller}\n"
        f"But : {intent}\n"
        "Divulgation : voix synthétique automatisée, appel non enregistré\n"
        f"Durée maximale : {settings.max_duration_seconds} secondes\n"
        "Politique : numéro consentant pré-enregistré, un seul appel actif"
    )


def confirm_call(to: str, intent: str, settings: Settings) -> bool:
    preview = build_preview(to, intent, settings)
    if platform.system() == "Darwin":
        script = """
on run argv
  set previewText to item 1 of argv
  display dialog previewText with title "Fredo — Confirmer l'appel" buttons {"Annuler", "Appeler"} default button "Appeler" cancel button "Annuler" with icon caution
  return button returned of result
end run
"""
        result = subprocess.run(
            ["osascript", "-e", script, preview],
            check=False,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0 and result.stdout.strip() == "Appeler"

    print(preview)
    answer = input("Tapez APPELER pour confirmer : ").strip()
    return answer == "APPELER"
