from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import secrets
import sys
from typing import Any

import httpx

from .confirmation import confirm_call
from .doctor import checks_payload, run_checks
from .models import CallRequest, GinseDemoReceipt, TERMINAL_STATUSES
from .policy import validate_call_request, validate_ginse_demo_receipt
from .settings import Settings


def _json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


def _authorization(settings: Settings) -> dict[str, str]:
    if not settings.endpoint_secret:
        raise RuntimeError("FREDO_ENDPOINT_SECRET is missing")
    return {"Authorization": f"Bearer {settings.endpoint_secret}"}


def _is_successful_real_result(result: object) -> bool:
    if not isinstance(result, dict):
        return False
    outcome = result.get("outcome")
    return bool(
        result.get("status") == "completed"
        and not result.get("error_code")
        and isinstance(outcome, dict)
        and outcome.get("mock") is not True
        and isinstance(outcome.get("works"), bool)
        and isinstance(outcome.get("answer"), str)
        and outcome["answer"].strip()
        and isinstance(outcome.get("summary"), str)
        and outcome["summary"].strip()
    )


def _receipt_from_args(args: argparse.Namespace) -> GinseDemoReceipt:
    return validate_ginse_demo_receipt(
        profile=args.ginse_profile,
        demo_session_id=args.ginse_demo_session_id,
        expires_at=args.ginse_expires_at,
    )


def _validated_call_from_args(args: argparse.Namespace, settings: Settings) -> CallRequest:
    receipt = _receipt_from_args(args)
    return validate_call_request(
        {
            "to": args.to,
            "intent": args.intent,
            "consent": True,
            "confirmed": True,
            "profile": receipt.profile,
            "demo_session_id": receipt.demo_session_id,
            "expires_at": receipt.expires_at,
        },
        settings,
    )


def _call_idempotency_key(
    *,
    destination: str,
    intent: str,
    receipt: GinseDemoReceipt,
) -> str:
    canonical = json.dumps(
        {
            "demo_session_id": receipt.demo_session_id,
            "expires_at": receipt.expires_at,
            "intent": intent,
            "profile": receipt.profile,
            "to": destination,
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"fredo-{hashlib.sha256(canonical).hexdigest()}"


async def _post_call(
    *,
    server_url: str,
    settings: Settings,
    destination: str,
    intent: str,
    receipt: GinseDemoReceipt,
    idempotency_key: str,
) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=30, trust_env=False) as client:
        response = await client.post(
            f"{server_url.rstrip('/')}/v1/calls",
            headers={
                **_authorization(settings),
                "Idempotency-Key": idempotency_key,
            },
            json={
                "to": destination,
                "intent": intent,
                "consent": True,
                "confirmed": True,
                "profile": receipt.profile,
                "demo_session_id": receipt.demo_session_id,
                "expires_at": receipt.expires_at,
            },
        )
        try:
            payload = response.json()
        except ValueError as exc:
            raise RuntimeError(f"Fredo server returned HTTP {response.status_code}") from exc
        if response.status_code >= 400:
            raise RuntimeError(f"Fredo rejected the call: {payload.get('error', 'unknown_error')}")
        return payload


async def _wait_for_result(
    *,
    server_url: str,
    settings: Settings,
    call_id: str,
    timeout: float,
) -> dict[str, Any]:
    deadline = asyncio.get_running_loop().time() + timeout
    async with httpx.AsyncClient(timeout=10, trust_env=False) as client:
        while asyncio.get_running_loop().time() < deadline:
            response = await client.get(
                f"{server_url.rstrip('/')}/v1/calls/{call_id}",
                headers=_authorization(settings),
            )
            payload = response.json()
            if response.status_code >= 400:
                raise RuntimeError("Unable to read Fredo call status")
            if payload.get("status") in {status.value for status in TERMINAL_STATUSES}:
                return payload
            await asyncio.sleep(0.5)
    raise RuntimeError("Call result timed out; the duration guard should terminate the carrier call")


async def _call_existing(args: argparse.Namespace, settings: Settings) -> int:
    call_request = _validated_call_from_args(args, settings)
    receipt = GinseDemoReceipt(
        profile=call_request.profile,
        demo_session_id=call_request.demo_session_id,
        expires_at=call_request.expires_at,
    )
    if not confirm_call(call_request.to, call_request.intent, settings):
        _json({"status": "cancelled", "dial_attempted": False})
        return 2
    result = await _post_call(
        server_url=args.server,
        settings=settings,
        destination=call_request.to,
        intent=call_request.intent,
        receipt=receipt,
        idempotency_key=_call_idempotency_key(
            destination=call_request.to,
            intent=call_request.intent,
            receipt=receipt,
        ),
    )
    if args.wait:
        result = await _wait_for_result(
            server_url=args.server,
            settings=settings,
            call_id=result["call_id"],
            timeout=settings.max_duration_seconds + 30,
        )
    _json(result)
    return 0 if not args.wait or _is_successful_real_result(result) else 1


async def _wait_until_started(server: Any, timeout: float = 10) -> None:
    deadline = asyncio.get_running_loop().time() + timeout
    while not server.started:
        if asyncio.get_running_loop().time() >= deadline:
            raise RuntimeError("Local Fredo server did not start")
        await asyncio.sleep(0.05)


async def _demo(args: argparse.Namespace, settings: Settings) -> int:
    call_request = _validated_call_from_args(args, settings)
    receipt = GinseDemoReceipt(
        profile=call_request.profile,
        demo_session_id=call_request.demo_session_id,
        expires_at=call_request.expires_at,
    )
    if settings.telephony_provider != "real":
        raise RuntimeError("The one-command demo refuses FREDO_TELEPHONY_PROVIDER=mock")
    checks = run_checks(settings, quick_tunnel=True)
    failed = [check.name for check in checks if not check.ok]
    if failed:
        raise RuntimeError(f"Fredo doctor failed: {', '.join(failed)}")
    if not confirm_call(call_request.to, call_request.intent, settings):
        _json({"status": "cancelled", "dial_attempted": False})
        return 2

    from uvicorn import Config, Server

    from .app import create_app
    from .tunnel import CloudflareQuickTunnel

    tunnel = CloudflareQuickTunnel(settings.port)
    server: Server | None = None
    server_task: asyncio.Task[None] | None = None
    try:
        public_url = await tunnel.start()
        runtime_settings = settings.with_public_url(public_url)
        app = create_app(runtime_settings)
        config = Config(
            app,
            host="127.0.0.1",
            port=runtime_settings.port,
            log_level="warning",
            access_log=False,
        )
        server = Server(config)
        server.install_signal_handlers = lambda: None
        server_task = asyncio.create_task(server.serve())
        await _wait_until_started(server)
        local_url = f"http://127.0.0.1:{runtime_settings.port}"
        started = await _post_call(
            server_url=local_url,
            settings=runtime_settings,
            destination=call_request.to,
            intent=call_request.intent,
            receipt=receipt,
            idempotency_key=_call_idempotency_key(
                destination=call_request.to,
                intent=call_request.intent,
                receipt=receipt,
            ),
        )
        result = await _wait_for_result(
            server_url=local_url,
            settings=runtime_settings,
            call_id=started["call_id"],
            timeout=runtime_settings.max_duration_seconds + 30,
        )
        _json(result)
        return 0 if _is_successful_real_result(result) else 1
    finally:
        if server:
            server.should_exit = True
        if server_task:
            try:
                await asyncio.wait_for(server_task, timeout=5)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                server_task.cancel()
        await tunnel.stop()


def _serve(settings: Settings, *, ginse_only: bool = False) -> int:
    from .app import create_app, missing_for_ginse_provider

    missing = (
        missing_for_ginse_provider(settings)
        if ginse_only
        else settings.missing_for_real_call()
    )
    if missing:
        raise RuntimeError(f"Missing configuration: {', '.join(missing)}")
    import uvicorn

    uvicorn.run(
        create_app(settings, ginse_only=ginse_only),
        host=settings.host,
        port=settings.port,
        log_level="info",
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
    return 0


def _add_ginse_receipt_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--ginse-profile",
        required=True,
        help="Exact profile returned by the verified Ginse run",
    )
    parser.add_argument(
        "--ginse-demo-session-id",
        required=True,
        help="demo_session_id returned by the verified Ginse run",
    )
    parser.add_argument(
        "--ginse-expires-at",
        required=True,
        help="expires_at returned by the verified Ginse run",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fredo", description="Phone from Codex, with guardrails.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Check every demo prerequisite without dialing")
    doctor.add_argument("--json", action="store_true", dest="as_json")
    doctor.add_argument(
        "--persistent",
        action="store_true",
        help="Require FREDO_PUBLIC_URL instead of the automatic quick tunnel",
    )

    subparsers.add_parser("secret", help="Generate a strong FREDO_ENDPOINT_SECRET")
    subparsers.add_parser(
        "configure",
        help="Store team demo credentials in an ignored mode-0600 .env file",
    )
    serve = subparsers.add_parser("serve", help="Run with a preconfigured public URL")
    serve.add_argument(
        "--ginse-only",
        action="store_true",
        help="Expose only the Ginse provider and health routes",
    )

    call = subparsers.add_parser("call", help="Confirm and call through an already running Fredo server")
    call.add_argument("--to", required=True)
    call.add_argument("--intent", required=True)
    call.add_argument("--server", default="http://127.0.0.1:8080")
    call.add_argument("--wait", action=argparse.BooleanOptionalAction, default=True)
    _add_ginse_receipt_arguments(call)

    demo = subparsers.add_parser("demo", help="Confirm, open a quick tunnel, call, and return the result")
    demo.add_argument("--to", required=True)
    demo.add_argument("--intent", required=True)
    _add_ginse_receipt_arguments(demo)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
    try:
        settings = Settings.from_env()
        if args.command == "doctor":
            checks = run_checks(settings, quick_tunnel=not args.persistent)
            payload = checks_payload(checks)
            if args.as_json:
                _json(payload)
            else:
                for check in checks:
                    symbol = "PASS" if check.ok else "FAIL"
                    print(f"{symbol:4} {check.name}: {check.detail}")
                print(payload["status"])
            return 0 if payload["status"] == "ready" else 1
        if args.command == "secret":
            print(secrets.token_urlsafe(32))
            return 0
        if args.command == "configure":
            from .configurator import configure_env

            path = configure_env()
            _json({"status": "configured", "path": str(path), "secrets_printed": False})
            return 0
        if args.command == "serve":
            return _serve(settings, ginse_only=args.ginse_only)
        if args.command == "call":
            return asyncio.run(_call_existing(args, settings))
        if args.command == "demo":
            return asyncio.run(_demo(args, settings))
    except KeyboardInterrupt:
        _json({"status": "cancelled", "dial_attempted": False})
        return 130
    except Exception as exc:
        _json({"status": "error", "error": str(exc)})
        return 1
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    sys.exit(main())
