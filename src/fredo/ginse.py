"""Reusable, side-effect-free core for Fredo's single Ginse action.

The module deliberately has no network client and does not log request data,
credentials, or provider output.  A web adapter only needs to extract three
headers/a JSON body, call :func:`handle_run`, and map :class:`ProviderError` to
its ``status_code``.
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
import secrets
import sqlite3
from collections.abc import Callable, Mapping
from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import urlsplit


ACTION_LABEL = "Prepare Fredo demo"
PLATFORM = "macos-arm64"
PROFILE = "hosted-voice-mvp"
DEMO_SESSION_TTL = timedelta(minutes=15)

INPUT_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Prepare Fredo demo input",
    "type": "object",
    "additionalProperties": False,
    "required": ["platform", "profile"],
    "properties": {
        "platform": {"const": PLATFORM},
        "profile": {"const": PROFILE},
    },
}

OUTPUT_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Prepare Fredo demo output",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "product",
        "profile",
        "compatible",
        "demo_session_id",
        "expires_at",
    ],
    "properties": {
        "product": {"const": "fredo"},
        "profile": {"const": PROFILE},
        "compatible": {"const": True},
        "demo_session_id": {
            "type": "string",
            "pattern": r"^demo_[A-Za-z0-9_-]{16,64}$",
        },
        "expires_at": {"type": "string", "format": "date-time"},
    },
}

_INPUT_KEYS = frozenset(("platform", "profile"))
_OUTPUT_KEYS = frozenset(("product", "profile", "compatible", "demo_session_id", "expires_at"))
_DEMO_SESSION_ID = re.compile(r"\Ademo_[A-Za-z0-9_-]{16,64}\Z")
_IDEMPOTENCY_KEY = re.compile(r"\A[!-~]{1,255}\Z")
_OPERATION_ID = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9._:-]{7,199}\Z")


class ProviderError(Exception):
    """An adapter-safe error whose message never includes request data."""

    code = "provider_error"
    status_code = 500


class AuthenticationError(ProviderError):
    code = "unauthorized"
    status_code = 401


class RuntimeDependencyError(ProviderError):
    code = "authentication_unavailable"
    status_code = 503


class InputValidationError(ProviderError):
    code = "invalid_input"
    status_code = 422


class OutputValidationError(ProviderError):
    code = "invalid_output"
    status_code = 500


class IdempotencyKeyError(ProviderError):
    code = "invalid_idempotency_key"
    status_code = 400


class IdempotencyConflict(ProviderError):
    code = "idempotency_conflict"
    status_code = 409


class StoreCorruptionError(ProviderError):
    code = "idempotency_store_corrupt"
    status_code = 500


class BearerValidator(Protocol):
    def __call__(self, authorization: str | None) -> Mapping[str, Any]: ...


JwtDecoder = Callable[..., Mapping[str, Any]]
OutputFactory = Callable[[str], Mapping[str, Any]]
OperationIdFactory = Callable[[], str]


def validate_input(payload: object) -> dict[str, str]:
    """Validate and normalize the exact advertised Ginse input object."""

    if not isinstance(payload, dict) or frozenset(payload) != _INPUT_KEYS:
        raise InputValidationError("input must contain exactly platform and profile")
    if payload.get("platform") != PLATFORM or payload.get("profile") != PROFILE:
        raise InputValidationError("unsupported Fredo demo profile")
    return {"platform": PLATFORM, "profile": PROFILE}


def validate_output(payload: object) -> dict[str, Any]:
    """Validate the closed, data-only provider output."""

    if not isinstance(payload, dict) or frozenset(payload) != _OUTPUT_KEYS:
        raise OutputValidationError("output does not match the advertised schema")
    if (
        payload.get("product") != "fredo"
        or payload.get("profile") != PROFILE
        or payload.get("compatible") is not True
    ):
        raise OutputValidationError("output does not match the advertised schema")

    session_id = payload.get("demo_session_id")
    if not isinstance(session_id, str) or _DEMO_SESSION_ID.fullmatch(session_id) is None:
        raise OutputValidationError("output does not match the advertised schema")

    expires_at = payload.get("expires_at")
    if not isinstance(expires_at, str) or not expires_at.endswith("Z"):
        raise OutputValidationError("output does not match the advertised schema")
    try:
        parsed_expiry = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise OutputValidationError("output does not match the advertised schema") from exc
    if parsed_expiry.tzinfo is None:
        raise OutputValidationError("output does not match the advertised schema")

    return {
        "product": "fredo",
        "profile": PROFILE,
        "compatible": True,
        "demo_session_id": session_id,
        "expires_at": expires_at,
    }


def canonical_json(value: object) -> str:
    """Return the canonical JSON form used by this closed Ginse contract.

    The action schema only admits fixed ASCII strings, so sorted keys and the
    compact JSON representation are also its RFC 8785 representation.
    """

    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise InputValidationError("input is not canonicalizable JSON") from exc


def request_fingerprint(payload: object) -> str:
    """Return the lowercase SHA-256 fingerprint of canonical input JSON."""

    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def build_manifest(run_url: str, ownership_token: str) -> dict[str, Any]:
    """Build a Ginse v3 manifest for the one fixed-price Fredo action."""

    parsed_url = urlsplit(run_url)
    if (
        parsed_url.scheme != "https"
        or not parsed_url.netloc
        or parsed_url.username is not None
        or parsed_url.password is not None
    ):
        raise ValueError("run_url must be an HTTPS URL without embedded credentials")
    if not isinstance(ownership_token, str) or len(ownership_token) < 16:
        raise ValueError("ownership_token must contain at least 16 characters")

    return {
        "schema_version": "2",
        "slug": "fredo-demo",
        "display_name": "Fredo — 42hackathon",
        "description": "Prepare a compatible hosted Fredo voice demo session.",
        "presentation": {
            "action": ACTION_LABEL,
            "input": {"label": "Mac demo profile", "icon": "code"},
            "output": {"label": "Fredo demo session", "icon": "audio"},
        },
        "price": {"amount_cents": 42, "currency": "EUR"},
        "run_url": run_url,
        "input_schema": deepcopy(INPUT_SCHEMA),
        "output_schema": deepcopy(OUTPUT_SCHEMA),
        "example": {"input": {"platform": PLATFORM, "profile": PROFILE}},
        "ownership_token": ownership_token,
    }


def ginse_manifest(run_url: str, ownership_token: str) -> dict[str, Any]:
    """Alias with a route-friendly name for :func:`build_manifest`."""

    return build_manifest(run_url, ownership_token)


def validate_bearer_jwt(
    authorization: str | None,
    *,
    public_key_pem: str | bytes,
    issuer: str,
    audience: str,
    decoder: JwtDecoder | None = None,
) -> dict[str, Any]:
    """Verify a Ginse Ed25519 JWT and return its claims.

    PyJWT is imported only when this function is called.  ``decoder`` exists
    for dependency injection; it must implement the ``jwt.decode`` signature.
    """

    if not authorization:
        raise AuthenticationError("missing bearer token")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1]:
        raise AuthenticationError("invalid bearer token")

    if decoder is None:
        try:
            import jwt  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeDependencyError("PyJWT with Ed25519 support is required") from exc
        decoder = jwt.decode

    try:
        claims = decoder(
            parts[1],
            public_key_pem,
            algorithms=["EdDSA"],
            issuer=issuer,
            audience=audience,
            options={"require": ["exp", "iat", "iss", "aud"]},
        )
    except Exception as exc:
        # Never reflect the JWT, claim values, or decoder detail to the caller.
        raise AuthenticationError("invalid bearer token") from exc

    if not isinstance(claims, Mapping):
        raise AuthenticationError("invalid bearer token")
    required_claims = {"exp", "iat", "iss", "aud"}
    if not required_claims.issubset(claims):
        raise AuthenticationError("invalid bearer token")
    return dict(claims)


@dataclass(frozen=True, slots=True)
class Ed25519BearerValidator:
    """Callable authentication dependency suitable for a Starlette adapter."""

    public_key_pem: str | bytes
    issuer: str
    audience: str
    decoder: JwtDecoder | None = None

    def __call__(self, authorization: str | None) -> dict[str, Any]:
        return validate_bearer_jwt(
            authorization,
            public_key_pem=self.public_key_pem,
            issuer=self.issuer,
            audience=self.audience,
            decoder=self.decoder,
        )


@dataclass(frozen=True, slots=True)
class RunResult:
    provider_operation_id: str
    output: dict[str, Any]
    replayed: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": "succeeded",
            "provider_operation_id": self.provider_operation_id,
            "replayed": self.replayed,
            "output": deepcopy(self.output),
        }


def _default_operation_id() -> str:
    return f"op_{secrets.token_hex(16)}"


class SQLiteIdempotencyStore:
    """Durable atomic Ginse idempotency records backed by SQLite.

    Each call opens its own connection and uses ``BEGIN IMMEDIATE``.  This
    serializes a key claim across threads/processes and commits the stable
    operation ID and terminal output together before returning success.
    """

    def __init__(
        self,
        database: str | Path,
        *,
        timeout_seconds: float = 5.0,
        operation_id_factory: OperationIdFactory = _default_operation_id,
    ) -> None:
        if str(database) == ":memory:":
            raise ValueError("a file-backed SQLite database is required for durable idempotency")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self._database = str(database)
        self._timeout_seconds = timeout_seconds
        self._operation_id_factory = operation_id_factory
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self._database,
            timeout=self._timeout_seconds,
            isolation_level=None,
        )
        connection.execute(f"PRAGMA busy_timeout = {int(self._timeout_seconds * 1000)}")
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("PRAGMA synchronous = FULL")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS ginse_operations (
                    idempotency_key TEXT PRIMARY KEY,
                    request_fingerprint TEXT NOT NULL,
                    provider_operation_id TEXT NOT NULL UNIQUE,
                    output_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def execute(
        self,
        idempotency_key: str | None,
        payload: object,
        output_factory: OutputFactory,
    ) -> RunResult:
        """Atomically create a result or replay the exact stored result."""

        if (
            not isinstance(idempotency_key, str)
            or _IDEMPOTENCY_KEY.fullmatch(idempotency_key) is None
        ):
            raise IdempotencyKeyError("a printable Idempotency-Key is required")

        fingerprint = request_fingerprint(payload)
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                """
                SELECT request_fingerprint, provider_operation_id, output_json
                FROM ginse_operations
                WHERE idempotency_key = ?
                """,
                (idempotency_key,),
            ).fetchone()
            if row is not None:
                stored_fingerprint, operation_id, output_json = row
                if not secrets.compare_digest(stored_fingerprint, fingerprint):
                    raise IdempotencyConflict(
                        "Idempotency-Key was already used for a different request"
                    )
                try:
                    stored_output = validate_output(json.loads(output_json))
                except (json.JSONDecodeError, OutputValidationError) as exc:
                    raise StoreCorruptionError("stored provider output is invalid") from exc
                connection.commit()
                return RunResult(operation_id, stored_output, replayed=True)

            operation_id = self._operation_id_factory()
            if not isinstance(operation_id, str) or _OPERATION_ID.fullmatch(operation_id) is None:
                raise ValueError("operation_id_factory returned an invalid provider operation ID")
            output = validate_output(dict(output_factory(operation_id)))
            output_json = canonical_json(output)
            created_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
            connection.execute(
                """
                INSERT INTO ginse_operations (
                    idempotency_key,
                    request_fingerprint,
                    provider_operation_id,
                    output_json,
                    created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (idempotency_key, fingerprint, operation_id, output_json, created_at),
            )
            connection.commit()
            return RunResult(operation_id, output, replayed=False)
        except Exception:
            if connection.in_transaction:
                connection.rollback()
            raise
        finally:
            connection.close()

    def run(
        self,
        idempotency_key: str | None,
        payload: object,
        output_factory: OutputFactory,
    ) -> RunResult:
        """Route-friendly alias for :meth:`execute`."""

        return self.execute(idempotency_key, payload, output_factory)


def _utc_now(value: datetime | None) -> datetime:
    current = value or datetime.now(UTC)
    if current.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    return current.astimezone(UTC)


def _demo_session_id(provider_operation_id: str) -> str:
    digest = hashlib.sha256(f"fredo-demo:{provider_operation_id}".encode()).digest()[:18]
    encoded = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return f"demo_{encoded}"


def prepare_fredo_demo(
    payload: object,
    *,
    provider_operation_id: str,
    now: datetime | None = None,
    ttl: timedelta = DEMO_SESSION_TTL,
) -> dict[str, Any]:
    """Produce the deterministic, data-only output for one accepted operation."""

    normalized_input = validate_input(payload)
    if _OPERATION_ID.fullmatch(provider_operation_id) is None:
        raise ValueError("provider_operation_id is invalid")
    if ttl <= timedelta(0):
        raise ValueError("ttl must be positive")
    expires_at = (_utc_now(now) + ttl).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return validate_output(
        {
            "product": "fredo",
            "profile": normalized_input["profile"],
            "compatible": True,
            "demo_session_id": _demo_session_id(provider_operation_id),
            "expires_at": expires_at,
        }
    )


def prepare_fredo_demo_run(
    store: SQLiteIdempotencyStore,
    *,
    idempotency_key: str | None,
    payload: object,
    now: datetime | None = None,
    ttl: timedelta = DEMO_SESSION_TTL,
) -> RunResult:
    """Validate, execute, and durably replay the single Fredo Ginse action."""

    normalized_input = validate_input(payload)
    accepted_at = _utc_now(now)
    return store.execute(
        idempotency_key,
        normalized_input,
        lambda operation_id: prepare_fredo_demo(
            normalized_input,
            provider_operation_id=operation_id,
            now=accepted_at,
            ttl=ttl,
        ),
    )


def handle_run(
    *,
    authorization: str | None,
    idempotency_key: str | None,
    payload: object,
    store: SQLiteIdempotencyStore,
    bearer_validator: BearerValidator,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Synchronous core for a Starlette ``POST /run`` route."""

    bearer_validator(authorization)
    return prepare_fredo_demo_run(
        store,
        idempotency_key=idempotency_key,
        payload=payload,
        now=now,
    ).as_dict()


__all__ = [
    "ACTION_LABEL",
    "AuthenticationError",
    "DEMO_SESSION_TTL",
    "Ed25519BearerValidator",
    "IdempotencyConflict",
    "IdempotencyKeyError",
    "INPUT_SCHEMA",
    "InputValidationError",
    "OUTPUT_SCHEMA",
    "OutputValidationError",
    "PLATFORM",
    "PROFILE",
    "ProviderError",
    "RunResult",
    "RuntimeDependencyError",
    "SQLiteIdempotencyStore",
    "StoreCorruptionError",
    "build_manifest",
    "canonical_json",
    "ginse_manifest",
    "handle_run",
    "prepare_fredo_demo",
    "prepare_fredo_demo_run",
    "request_fingerprint",
    "validate_bearer_jwt",
    "validate_input",
    "validate_output",
]
