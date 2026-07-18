from __future__ import annotations

import platform
import subprocess

from .settings import Settings


def build_preview(to: str, intent: str, settings: Settings) -> str:
    caller = settings.twilio_phone_number or "caller identity not configured"
    return (
        f"Destination: {to}\n"
        f"Caller identity: {caller}\n"
        f"Purpose: {intent}\n"
        "Disclosure: automated synthetic voice, call not recorded\n"
        f"Maximum duration: {settings.max_duration_seconds} seconds\n"
        "Policy: pre-enrolled consenting number, one active call"
    )


def confirm_call(to: str, intent: str, settings: Settings) -> bool:
    preview = build_preview(to, intent, settings)
    if platform.system() == "Darwin":
        script = """
on run argv
  set previewText to item 1 of argv
  display dialog previewText with title "Fredo — Confirm call" buttons {"Cancel", "Call"} default button "Call" cancel button "Cancel" with icon caution
  return button returned of result
end run
"""
        result = subprocess.run(
            ["osascript", "-e", script, preview],
            check=False,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0 and result.stdout.strip() == "Call"

    print(preview)
    answer = input("Type CALL to confirm: ").strip()
    return answer == "CALL"
