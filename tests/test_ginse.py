from __future__ import annotations

import json
import logging
import os
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from fredo.ginse import (
    ACTION_LABEL,
    AuthenticationError,
    Ed25519BearerValidator,
    IdempotencyConflict,
    IdempotencyKeyError,
    INPUT_SCHEMA,
    InputValidationError,
    OUTPUT_SCHEMA,
    PLATFORM,
    PROFILE,
    SQLiteIdempotencyStore,
    build_manifest,
    canonical_json,
    handle_run,
    prepare_fredo_demo,
    prepare_fredo_demo_run,
    request_fingerprint,
    validate_bearer_jwt,
    validate_input,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
VALID_INPUT = {"platform": PLATFORM, "profile": PROFILE}
FIXED_NOW = datetime(2026, 7, 18, 12, 0, tzinfo=UTC)
OPERATION_ID = "op_0123456789abcdef0123456789abcdef"
OWNERSHIP_TOKEN = "owner_0123456789abcdef"

GINSE_MANIFEST_SCHEMA_V3: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schema_version",
        "slug",
        "display_name",
        "description",
        "presentation",
        "price",
        "run_url",
        "input_schema",
        "output_schema",
        "example",
        "ownership_token",
    ],
    "properties": {
        "schema_version": {"const": "2"},
        "slug": {
            "type": "string",
            "minLength": 2,
            "maxLength": 63,
            "pattern": "^[a-z0-9]+(?:-[a-z0-9]+)*$",
        },
        "display_name": {
            "type": "string",
            "minLength": 2,
            "maxLength": 80,
        },
        "description": {
            "type": "string",
            "minLength": 10,
            "maxLength": 500,
        },
        "presentation": {
            "type": "object",
            "additionalProperties": False,
            "required": ["action", "input", "output"],
            "properties": {
                "action": {"type": "string", "minLength": 2, "maxLength": 28},
                "input": {"$ref": "#/$defs/flowEndpoint"},
                "output": {"$ref": "#/$defs/flowEndpoint"},
            },
        },
        "price": {
            "type": "object",
            "additionalProperties": False,
            "required": ["amount_cents", "currency"],
            "properties": {
                "amount_cents": {"type": "integer", "minimum": 1, "maximum": 100000},
                "currency": {"const": "EUR"},
            },
        },
        "run_url": {"type": "string", "format": "uri", "pattern": "^https://"},
        "input_schema": {"type": "object"},
        "output_schema": {"type": "object"},
        "example": {
            "type": "object",
            "additionalProperties": False,
            "required": ["input"],
            "properties": {"input": {}},
        },
        "ownership_token": {"type": "string", "minLength": 16},
    },
    "$defs": {
        "flowEndpoint": {
            "type": "object",
            "additionalProperties": False,
            "required": ["label", "icon"],
            "properties": {
                "label": {"type": "string", "minLength": 2, "maxLength": 32},
                "icon": {
                    "enum": [
                        "archive",
                        "audio",
                        "calculator",
                        "code",
                        "document",
                        "generic",
                        "image",
                        "link",
                        "location",
                        "number",
                        "presentation",
                        "table",
                        "text",
                        "video",
                    ]
                },
            },
        }
    },
}


def _output(operation_id: str, *, now: datetime = FIXED_NOW) -> dict[str, Any]:
    return prepare_fredo_demo(VALID_INPUT, provider_operation_id=operation_id, now=now)


def test_checked_in_schemas_match_runtime_contract() -> None:
    input_schema = json.loads(
        (REPO_ROOT / "schemas" / "ginse-input.schema.json").read_text(encoding="utf-8")
    )
    output_schema = json.loads(
        (REPO_ROOT / "schemas" / "ginse-output.schema.json").read_text(encoding="utf-8")
    )
    example_input = json.loads(
        (REPO_ROOT / "schemas" / "ginse-example-input.json").read_text(encoding="utf-8")
    )

    assert input_schema == INPUT_SCHEMA
    assert output_schema == OUTPUT_SCHEMA
    assert input_schema["additionalProperties"] is False
    assert input_schema["required"] == ["platform", "profile"]
    assert input_schema["properties"] == {
        "platform": {"const": "macos-arm64"},
        "profile": {"const": "hosted-voice-mvp"},
    }
    assert output_schema["additionalProperties"] is False
    assert example_input == VALID_INPUT
    assert build_manifest("https://provider.example/run", OWNERSHIP_TOKEN)["example"] == {
        "input": example_input
    }
    assert set(output_schema["properties"]) == {
        "product",
        "profile",
        "compatible",
        "demo_session_id",
        "expires_at",
    }


def test_provider_compose_never_loads_voice_credentials() -> None:
    compose = (REPO_ROOT / "compose.yaml").read_text(encoding="utf-8")
    provider_example = (REPO_ROOT / ".env.ginse.example").read_text(encoding="utf-8")

    assert "env_file:" not in compose
    assert "FREDO_GINSE_DATABASE: /data/ginse.sqlite3" in compose
    for forbidden in (
        "DEEPGRAM_API_KEY",
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
        "TWILIO_PHONE_NUMBER",
        "FREDO_ENDPOINT_SECRET",
    ):
        assert forbidden not in compose
        assert forbidden not in provider_example


@pytest.mark.parametrize(
    "payload",
    [
        None,
        {},
        {"platform": PLATFORM},
        {"platform": PLATFORM, "profile": "other"},
        {"platform": "linux-x64", "profile": PROFILE},
        {**VALID_INPUT, "phone": "+33123456789"},
        {**VALID_INPUT, "intent": "place a call"},
        {**VALID_INPUT, "command": "run something"},
        {**VALID_INPUT, "url": "https://example.test"},
    ],
)
def test_input_validation_rejects_every_non_contract_shape(payload: object) -> None:
    with pytest.raises(InputValidationError):
        validate_input(payload)


def test_action_is_deterministic_and_output_is_data_only() -> None:
    first = prepare_fredo_demo(VALID_INPUT, provider_operation_id=OPERATION_ID, now=FIXED_NOW)
    second = prepare_fredo_demo(VALID_INPUT, provider_operation_id=OPERATION_ID, now=FIXED_NOW)

    assert first == second
    assert first == {
        "product": "fredo",
        "profile": "hosted-voice-mvp",
        "compatible": True,
        "demo_session_id": first["demo_session_id"],
        "expires_at": "2026-07-18T12:15:00Z",
    }
    serialized = canonical_json(first).lower()
    for forbidden in ("url", "command", "phone", "number", "intent"):
        assert forbidden not in serialized


def test_manifest_has_fixed_ginse_v3_offer() -> None:
    manifest = build_manifest("https://provider.example/run", OWNERSHIP_TOKEN)

    assert manifest["schema_version"] == "2"
    assert manifest["price"] == {"amount_cents": 42, "currency": "EUR"}
    assert manifest["presentation"] == {
        "action": ACTION_LABEL,
        "input": {"label": "Mac demo profile", "icon": "code"},
        "output": {"label": "Fredo demo session", "icon": "audio"},
    }
    assert manifest["run_url"] == "https://provider.example/run"
    assert manifest["ownership_token"] == OWNERSHIP_TOKEN
    assert manifest["example"] == {"input": VALID_INPUT}
    assert manifest["input_schema"] == INPUT_SCHEMA
    assert manifest["output_schema"] == OUTPUT_SCHEMA


def test_ginse_init_script_invokes_the_exact_manifest_contract(tmp_path: Path) -> None:
    capture = tmp_path / "argv.txt"
    runner = tmp_path / "ginse-cli-verified.mjs"
    runner.write_text(
        "#!/bin/sh\nprintf '%s\\n' \"$@\" > \"$FREDO_TEST_CAPTURE\"\n",
        encoding="utf-8",
    )
    runner.chmod(0o700)
    script = REPO_ROOT / "scripts" / "ginse-init.sh"
    run_url = "https://provider.example/run"
    env = os.environ.copy()
    env["FREDO_TEST_CAPTURE"] = str(capture)

    subprocess.run(
        [str(script), str(runner), run_url],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )

    assert capture.read_text(encoding="utf-8").splitlines() == [
        "apps",
        "init",
        "fredo-demo",
        "--display-name",
        "Fredo — 42hackathon",
        "--description",
        "Prepare a compatible hosted Fredo voice demo session.",
        "--price-cents",
        "42",
        "--run-url",
        run_url,
        "--input-schema",
        str(REPO_ROOT / "schemas" / "ginse-input.schema.json"),
        "--output-schema",
        str(REPO_ROOT / "schemas" / "ginse-output.schema.json"),
        "--input-label",
        "Mac demo profile",
        "--input-icon",
        "code",
        "--action-label",
        "Prepare Fredo demo",
        "--output-label",
        "Fredo demo session",
        "--output-icon",
        "audio",
        "--example",
        str(REPO_ROOT / "schemas" / "ginse-example-input.json"),
        "--json",
    ]


def test_manifest_matches_machine_readable_ginse_v3_schema_when_available() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    manifest = build_manifest("https://provider.example/run", OWNERSHIP_TOKEN)

    jsonschema.Draft202012Validator(GINSE_MANIFEST_SCHEMA_V3).validate(manifest)


@pytest.mark.parametrize(
    ("run_url", "ownership_token"),
    [
        ("http://provider.example/run", OWNERSHIP_TOKEN),
        ("/run", OWNERSHIP_TOKEN),
        ("https://user:password@provider.example/run", OWNERSHIP_TOKEN),
        ("https://provider.example/run", "too-short"),
    ],
)
def test_manifest_rejects_unsafe_parameters(run_url: str, ownership_token: str) -> None:
    with pytest.raises(ValueError) as raised:
        build_manifest(run_url, ownership_token)
    assert OWNERSHIP_TOKEN not in str(raised.value)
    assert "password" not in str(raised.value)


def test_fingerprint_uses_key_order_independent_canonical_json() -> None:
    left = {"platform": PLATFORM, "profile": PROFILE}
    right = {"profile": PROFILE, "platform": PLATFORM}

    assert canonical_json(left) == canonical_json(right)
    assert request_fingerprint(left) == request_fingerprint(right)
    assert request_fingerprint(left) != request_fingerprint({**left, "extra": True})


def test_store_replays_exact_result_after_restart(tmp_path: Path) -> None:
    database = tmp_path / "ginse.sqlite3"
    calls = 0

    def create_output(operation_id: str) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        return _output(operation_id)

    first_store = SQLiteIdempotencyStore(
        database,
        operation_id_factory=lambda: OPERATION_ID,
    )
    first = first_store.execute("idem-1", VALID_INPUT, create_output)

    replay_store = SQLiteIdempotencyStore(
        database,
        operation_id_factory=lambda: "op_should-not-be-used",
    )
    replay = replay_store.execute(
        "idem-1",
        {"profile": PROFILE, "platform": PLATFORM},
        create_output,
    )

    assert calls == 1
    assert first.replayed is False
    assert replay.replayed is True
    assert replay.provider_operation_id == first.provider_operation_id == OPERATION_ID
    assert replay.output == first.output
    assert replay.as_dict() == {**first.as_dict(), "replayed": True}


def test_store_rejects_divergent_reuse_before_factory(tmp_path: Path) -> None:
    store = SQLiteIdempotencyStore(
        tmp_path / "ginse.sqlite3",
        operation_id_factory=lambda: OPERATION_ID,
    )
    store.execute("idem-divergent", VALID_INPUT, _output)

    def must_not_run(operation_id: str) -> dict[str, Any]:
        raise AssertionError(operation_id)

    with pytest.raises(IdempotencyConflict):
        store.execute(
            "idem-divergent",
            {"platform": PLATFORM, "profile": "different"},
            must_not_run,
        )


def test_store_rolls_back_failed_output_creation(tmp_path: Path) -> None:
    store = SQLiteIdempotencyStore(
        tmp_path / "ginse.sqlite3",
        operation_id_factory=lambda: OPERATION_ID,
    )

    def fail(_operation_id: str) -> dict[str, Any]:
        raise RuntimeError("simulated crash before commit")

    with pytest.raises(RuntimeError):
        store.execute("idem-retry", VALID_INPUT, fail)
    retried = store.execute("idem-retry", VALID_INPUT, _output)

    assert retried.replayed is False
    assert retried.provider_operation_id == OPERATION_ID


@pytest.mark.parametrize("key", [None, "", "with space", "line\nbreak", "x" * 256])
def test_store_rejects_invalid_idempotency_keys(tmp_path: Path, key: str | None) -> None:
    store = SQLiteIdempotencyStore(tmp_path / "ginse.sqlite3")
    with pytest.raises(IdempotencyKeyError):
        store.execute(key, VALID_INPUT, _output)


def test_store_claim_is_atomic_across_connections(tmp_path: Path) -> None:
    database = tmp_path / "ginse.sqlite3"
    stores = [
        SQLiteIdempotencyStore(database, operation_id_factory=lambda: OPERATION_ID)
        for _ in range(20)
    ]
    barrier = threading.Barrier(20)
    counter_lock = threading.Lock()
    factory_calls = 0

    def invoke(store: SQLiteIdempotencyStore) -> Any:
        nonlocal factory_calls
        barrier.wait()

        def create_output(operation_id: str) -> dict[str, Any]:
            nonlocal factory_calls
            with counter_lock:
                factory_calls += 1
            return _output(operation_id)

        return store.execute("idem-concurrent", VALID_INPUT, create_output)

    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(invoke, stores))

    assert factory_calls == 1
    assert {result.replayed for result in results} == {False, True}
    assert {result.provider_operation_id for result in results} == {OPERATION_ID}
    assert all(result.output == results[0].output for result in results)


def test_bearer_validator_is_injectable_and_pins_eddsa() -> None:
    observed: dict[str, Any] = {}

    def decoder(token: str, key: str | bytes, **kwargs: Any) -> dict[str, Any]:
        observed.update({"token": token, "key": key, **kwargs})
        return {
            "exp": 2_000_000_000,
            "iat": 1_900_000_000,
            "iss": "https://issuer.example",
            "aud": "fredo-provider",
        }

    claims = validate_bearer_jwt(
        "Bearer opaque-token",
        public_key_pem="PUBLIC KEY",
        issuer="https://issuer.example",
        audience="fredo-provider",
        decoder=decoder,
    )

    assert claims["aud"] == "fredo-provider"
    assert observed == {
        "token": "opaque-token",
        "key": "PUBLIC KEY",
        "algorithms": ["EdDSA"],
        "issuer": "https://issuer.example",
        "audience": "fredo-provider",
        "options": {"require": ["exp", "iat", "iss", "aud"]},
    }


@pytest.mark.parametrize("header", [None, "", "token", "Basic token", "Bearer"])
def test_bearer_validator_rejects_missing_or_malformed_header(header: str | None) -> None:
    with pytest.raises(AuthenticationError):
        validate_bearer_jwt(
            header,
            public_key_pem="PUBLIC KEY",
            issuer="issuer",
            audience="audience",
            decoder=lambda *_args, **_kwargs: {},
        )


def test_real_ed25519_jwt_and_required_claims() -> None:
    jwt = pytest.importorskip("jwt")
    serialization = pytest.importorskip("cryptography.hazmat.primitives.serialization")
    ed25519 = pytest.importorskip("cryptography.hazmat.primitives.asymmetric.ed25519")

    private_key = ed25519.Ed25519PrivateKey.generate()
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    now = datetime.now(UTC)
    claims = {
        "exp": now + timedelta(minutes=5),
        "iat": now - timedelta(seconds=1),
        "iss": "https://ginse.example",
        "aud": "fredo-provider",
    }
    token = jwt.encode(claims, private_key, algorithm="EdDSA")
    validator = Ed25519BearerValidator(
        public_key_pem=public_pem,
        issuer="https://ginse.example",
        audience="fredo-provider",
    )

    decoded = validator(f"Bearer {token}")
    assert decoded["iss"] == "https://ginse.example"

    missing_iat = jwt.encode(
        {key: value for key, value in claims.items() if key != "iat"},
        private_key,
        algorithm="EdDSA",
    )
    with pytest.raises(AuthenticationError):
        validator(f"Bearer {missing_iat}")

    expired = jwt.encode(
        {**claims, "exp": now - timedelta(seconds=1)}, private_key, algorithm="EdDSA"
    )
    with pytest.raises(AuthenticationError):
        validator(f"Bearer {expired}")


def test_handle_run_is_starlette_adapter_ready_and_redacts_logs(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    store = SQLiteIdempotencyStore(
        tmp_path / "ginse.sqlite3",
        operation_id_factory=lambda: OPERATION_ID,
    )
    seen_headers: list[str | None] = []

    def authenticate(header: str | None) -> dict[str, Any]:
        seen_headers.append(header)
        return {"sub": "ginse"}

    first = handle_run(
        authorization="Bearer secret-canary",
        idempotency_key="idem-handler",
        payload=VALID_INPUT,
        store=store,
        bearer_validator=authenticate,
        now=FIXED_NOW,
    )
    replay = handle_run(
        authorization="Bearer secret-canary",
        idempotency_key="idem-handler",
        payload=VALID_INPUT,
        store=store,
        bearer_validator=authenticate,
        now=FIXED_NOW + timedelta(hours=1),
    )

    with caplog.at_level(logging.DEBUG):
        with pytest.raises(InputValidationError):
            handle_run(
                authorization="Bearer another-secret-canary",
                idempotency_key="+33123456789",
                payload={**VALID_INPUT, "phone": "+33123456789"},
                store=store,
                bearer_validator=authenticate,
                now=FIXED_NOW,
            )

    assert seen_headers == [
        "Bearer secret-canary",
        "Bearer secret-canary",
        "Bearer another-secret-canary",
    ]
    assert first["status"] == "succeeded"
    assert first["replayed"] is False
    assert replay == {**first, "replayed": True}
    assert "secret-canary" not in caplog.text
    assert "+33123456789" not in caplog.text


def test_prepare_run_exposes_transport_free_result(tmp_path: Path) -> None:
    store = SQLiteIdempotencyStore(
        tmp_path / "ginse.sqlite3",
        operation_id_factory=lambda: OPERATION_ID,
    )
    result = prepare_fredo_demo_run(
        store,
        idempotency_key="idem-pure",
        payload=VALID_INPUT,
        now=FIXED_NOW,
    )

    assert result.as_dict()["output"] == _output(OPERATION_ID)
    assert set(result.as_dict()) == {"status", "provider_operation_id", "replayed", "output"}
