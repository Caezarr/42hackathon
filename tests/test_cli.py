from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from fredo import cli
from fredo.models import GinseDemoReceipt
from fredo.policy import GINSE_PROFILE, PolicyError
from fredo.settings import Settings


DESTINATION = "+33612345678"
INTENT = "Vérifier la démo"
SESSION_ID = "demo_0123456789abcdef"


def _future_expiry() -> str:
    return (
        (datetime.now(UTC) + timedelta(minutes=10))
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _args(**overrides: object) -> argparse.Namespace:
    values: dict[str, object] = {
        "to": DESTINATION,
        "intent": INTENT,
        "server": "http://127.0.0.1:8080",
        "wait": False,
        "ginse_profile": GINSE_PROFILE,
        "ginse_demo_session_id": SESSION_ID,
        "ginse_expires_at": _future_expiry(),
    }
    values.update(overrides)
    return argparse.Namespace(**values)


@pytest.mark.parametrize(
    ("result", "successful"),
    [
        (
            {
                "status": "completed",
                "outcome": {"works": False, "answer": "La réponse est non."},
                "error_code": None,
            },
            True,
        ),
        ({"status": "completed", "outcome": None, "error_code": None}, False),
        (
            {
                "status": "completed",
                "outcome": {"mock": True, "works": False, "answer": "mock"},
                "error_code": None,
            },
            False,
        ),
        (
            {
                "status": "completed",
                "outcome": {"works": True, "answer": "Oui"},
                "error_code": "voice_error",
            },
            False,
        ),
        (
            {
                "status": "failed",
                "outcome": {"works": True, "answer": "Oui"},
                "error_code": None,
            },
            False,
        ),
    ],
)
def test_real_result_success_requires_completed_non_mock_outcome_without_error(
    result: dict[str, object], successful: bool
) -> None:
    assert cli._is_successful_real_result(result) is successful


@pytest.mark.parametrize("command", ["call", "demo"])
def test_call_entrypoints_require_all_ginse_receipt_flags(command: str) -> None:
    parser = cli.build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args([command, "--to", DESTINATION, "--intent", INTENT])


@pytest.mark.asyncio
async def test_expired_receipt_is_rejected_before_native_confirmation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    confirmation_attempted = False

    def forbidden_confirmation(*_args: object) -> bool:
        nonlocal confirmation_attempted
        confirmation_attempted = True
        return True

    monkeypatch.setattr(cli, "confirm_call", forbidden_confirmation)

    with pytest.raises(PolicyError) as caught:
        await cli._call_existing(
            _args(ginse_expires_at="2020-01-01T00:00:00Z"),
            Settings(),
        )

    assert caught.value.code == "expired_ginse_receipt"
    assert confirmation_attempted is False


@pytest.mark.asyncio
async def test_waiting_call_returns_nonzero_for_failed_terminal_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli, "confirm_call", lambda *_args: True)

    async def post_call(**_kwargs: Any) -> dict[str, str]:
        return {"call_id": "call-failed", "status": "dialing"}

    async def wait_for_result(**_kwargs: Any) -> dict[str, object]:
        return {"call_id": "call-failed", "status": "failed", "outcome": None}

    monkeypatch.setattr(cli, "_post_call", post_call)
    monkeypatch.setattr(cli, "_wait_for_result", wait_for_result)

    exit_code = await cli._call_existing(
        _args(wait=True),
        Settings(allowed_numbers=frozenset({DESTINATION})),
    )

    assert exit_code == 1


@pytest.mark.asyncio
async def test_call_normalizes_policy_values_before_preview_fingerprint_and_post(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    previewed: dict[str, str] = {}
    posted: dict[str, Any] = {}

    def confirm(to: str, intent: str, _settings: Settings) -> bool:
        previewed.update({"to": to, "intent": intent})
        return True

    async def post_call(**kwargs: Any) -> dict[str, str]:
        posted.update(kwargs)
        return {"call_id": "call-normalized", "status": "dialing"}

    monkeypatch.setattr(cli, "confirm_call", confirm)
    monkeypatch.setattr(cli, "_post_call", post_call)
    settings = Settings(allowed_numbers=frozenset({DESTINATION}))

    result = await cli._call_existing(
        _args(to="+33 (6) 12 34 56 78", intent="  Vérifier   la\n démo  "),
        settings,
    )

    assert result == 0
    assert previewed == {"to": DESTINATION, "intent": INTENT}
    assert posted["destination"] == DESTINATION
    assert posted["intent"] == INTENT
    receipt = posted["receipt"]
    assert isinstance(receipt, GinseDemoReceipt)
    assert posted["idempotency_key"] == cli._call_idempotency_key(
        destination=DESTINATION,
        intent=INTENT,
        receipt=receipt,
    )


@pytest.mark.asyncio
async def test_local_call_post_carries_the_closed_ginse_handoff(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    class FakeResponse:
        status_code = 202

        @staticmethod
        def json() -> dict[str, str]:
            return {"call_id": "call-1", "status": "dialing"}

    class FakeClient:
        def __init__(self, **kwargs: object) -> None:
            captured["client_options"] = kwargs

        async def __aenter__(self) -> "FakeClient":
            return self

        async def __aexit__(self, *_args: object) -> None:
            return None

        async def post(self, url: str, **kwargs: object) -> FakeResponse:
            captured["url"] = url
            captured.update(kwargs)
            return FakeResponse()

    monkeypatch.setattr(cli.httpx, "AsyncClient", FakeClient)
    receipt = GinseDemoReceipt(
        profile=GINSE_PROFILE,
        demo_session_id=SESSION_ID,
        expires_at=_future_expiry(),
    )

    result = await cli._post_call(
        server_url="http://127.0.0.1:8080/",
        settings=Settings(endpoint_secret="local-secret"),
        destination=DESTINATION,
        intent=INTENT,
        receipt=receipt,
        idempotency_key="fredo-test-key",
    )

    assert result["call_id"] == "call-1"
    assert captured["url"] == "http://127.0.0.1:8080/v1/calls"
    body = captured["json"]
    assert isinstance(body, dict)
    assert body == {
        "to": DESTINATION,
        "intent": INTENT,
        "consent": True,
        "confirmed": True,
        "profile": GINSE_PROFILE,
        "demo_session_id": SESSION_ID,
        "expires_at": receipt.expires_at,
    }


def test_client_idempotency_key_binds_call_and_ginse_handoff() -> None:
    receipt = GinseDemoReceipt(
        profile=GINSE_PROFILE,
        demo_session_id=SESSION_ID,
        expires_at=_future_expiry(),
    )
    changed_receipt = GinseDemoReceipt(
        profile=GINSE_PROFILE,
        demo_session_id="demo_fedcba9876543210",
        expires_at=receipt.expires_at,
    )

    first = cli._call_idempotency_key(
        destination=DESTINATION,
        intent=INTENT,
        receipt=receipt,
    )
    replay = cli._call_idempotency_key(
        destination=DESTINATION,
        intent=INTENT,
        receipt=receipt,
    )
    changed = cli._call_idempotency_key(
        destination=DESTINATION,
        intent=INTENT,
        receipt=changed_receipt,
    )

    assert first == replay
    assert first != changed
    assert SESSION_ID not in first


def test_serve_parser_has_explicit_ginse_only_mode() -> None:
    args = cli.build_parser().parse_args(["serve", "--ginse-only"])

    assert args.command == "serve"
    assert args.ginse_only is True
