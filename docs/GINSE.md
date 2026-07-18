# Ginse contract for Fredo

Status: implementation contract subordinate to [`GOAL.md`](../GOAL.md) `0.3-draft`; not implemented yet.

Ginse is the mandatory hackathon discovery and bootstrap front door. It invokes exactly one fixed-price Fredo action. It does not place calls, route media, install files, or receive call data.

The judged prompt is:

> “Use Ginse to prepare Fredo, then call `<PHONE_E164>`. This number belongs to a consenting judge. Introduce Fredo in French, disclose immediately that you are an automated synthetic voice, ask whether the demonstration works, then return the answer here.”

`<PHONE_E164>` stays in the Codex task and local Fredo runtime. It MUST NOT appear in a Ginse request or response.

Canonical Ginse references:

- [Use Ginse from Codex](https://app.ginse.ai/agent.md)
- [Ginse v3 provider contracts](https://app.ginse.ai/contracts/v3/README.md)

## Single marketplace action

- Display name: `Fredo — 42hackathon`.
- Action: `Resolve a Fredo demo bootstrap`.
- Proposed fake-ledger price: EUR 0.42.
- Transport: one self-hosted HTTPS `/run` action.

Calling, status, cancellation, and result retrieval are local Fredo operations, never additional Ginse products.

## Request

The `BootstrapRequest` contains exactly the bootstrap selectors, an installation identifier generated inside the trusted Ginse shim from 128 CSPRNG bits, and the thumbprint of a protected device signing key created locally before `/run`. The ID is encoded as exactly 22 unpadded base64url characters; the SHA-256 thumbprint as exactly 43. Neither can be supplied by the prompt, model, or user:

```json
{
  "schema_version": 1,
  "platform": "macos-arm64",
  "profile": "mac-m4pro-24gb",
  "codex_plugin_api": 1,
  "install_id": "<22-char-base64url>",
  "device_key_thumbprint": "<43-char-base64url-sha256>"
}
```

The published JSON Schema is authoritative. Unknown fields and unsupported platform/profile/API combinations are rejected.

The schema has no fields for destination, call intent, caller identity, carrier credential, prompt, audio, transcript, or call result and rejects unknown fields. Because arbitrary strings can be covert channels, schema shape alone is insufficient: deterministic taint tests and captured wire payloads MUST prove that every permitted value, including `install_id` and `device_key_thumbprint`, is independent of call data.

## Response

The provider returns a `BootstrapPlan` containing only:

- explicit `schema_version` and supported profile;
- immutable repository commit SHA;
- signed release-manifest URL and SHA-256;
- pinned Codex marketplace and plugin identities;
- one non-dialing `LeaseClaim`, pre-bound to the install ID, device-key thumbprint, release, and policy, with a signed issue time and exactly 45 minutes of validity;
- demo-access authority URL, policy digest, and plan expiry equal to the claim expiry.

The exact document is governed by `schemas/BootstrapPlan`. A conceptual example is:

```json
{
  "schema_version": 1,
  "product": "fredo",
  "profile": "mac-m4pro-24gb",
  "source": {
    "repository": "https://github.com/Caezarr/42hackathon",
    "commit": "<full-immutable-git-sha>"
  },
  "plugin": {
    "marketplace": "Caezarr/42hackathon",
    "name": "fredo"
  },
  "manifest_url": "https://provider.example/releases/fredo-mac-v1.json",
  "manifest_sha256": "<sha256>",
  "demo_access": {
    "authority_url": "https://access.example",
    "policy_sha256": "<sha256>",
    "lease_claim": "<opaque-one-time-non-dialing-claim>",
    "claim_expires_at": "<rfc3339-issued-at-plus-45-minutes>"
  },
  "expires_at": "<rfc3339>"
}
```

The Ginse response envelope, outside `BootstrapPlan`, carries the stable `provider_operation_id` and replay flag required by the Ginse contract. Those transport fields MUST NOT be confused with product-plan fields.

The provider returns declarations, never arbitrary shell. Fredo locally revalidates repository owner, commit, manifest origin, digest, signature, expiry, profile, and downgrade policy before any activation.

## Lease claim boundary

`LeaseClaim` is allowed to transit Ginse only because it grants no dialing authority. It MUST be:

- opaque, contain no carrier secret, and grant no dialing authority;
- bound to `install_id`, device-key thumbprint, release, and policy;
- valid for exactly 45 minutes from its signed issue time, leaving at least 15 minutes after a conforming cold bootstrap;
- single-use and atomically consumed;
- redacted from provider, Ginse-consumer, Codex, and diagnostic logs.

After installation, Fredo recovers the precommitted device-key reference and redeems the claim directly with the demo-access authority using proof of possession. It first persists a random `redemption_id`; the authority persists the canonical terminal result before replying, replays that exact result for an identical retry, and rejects divergent reuse. The resulting `GatewayCapability` is bound to the install, device public key, release SHA, policy digest, and expiry and requires proof of possession at the gateway. It grants access only to the mandatory policy gateway; the carrier master credential never leaves that gateway.

Ginse is not involved in redemption or in the live call.

## Provider behavior

`POST /run` MUST:

- verify the short-lived Ginse Ed25519 bearer token;
- validate the exact input schema before processing;
- atomically claim `Idempotency-Key`;
- bind it to RFC 8785 canonical input plus SHA-256;
- persist one stable opaque provider operation ID;
- return the exact stored response with `replayed: true` for an identical retry;
- reject reuse with different canonical input;
- validate the final plan against its advertised schema;
- redact the lease claim and all secret canaries from every log and error;
- expose a same-origin status URL only if resolution is asynchronous.

Synchronous `succeeded` resolution is preferred. Provider persistence is limited to authentication/idempotency state, immutable plans, and claim metadata. It stores no call data.

The Ginse app manifest is served unchanged at `/.well-known/ginse.json`, verified in staging, and promoted as an immutable app version.

## Exact Codex consumer flow

The already-installed and authorized Ginse use capability is the only bootstrap shim. Under the declared local-write approval, it creates the protected device signing key, generates `install_id` internally with the format and data-independence rules above, validates the public request schema, and invokes Ginse before Fredo exists locally.

Before `/run`, the immutable Ginse app version points to `/.well-known/fredo-bootstrap-approval.json` on the provider origin. Its SHA-256 and release-key fingerprint are pinned in verified app metadata. The shim validates its schema, origin, digest, signature, app/version binding, monotonic policy version, expiry, and anti-downgrade state. The envelope declares maximum download bytes, peak disk, writes, device-key creation, executable identities, and privilege classes. Codex displays it and obtains the single local-write/download approval; the returned plan may narrow but never widen or become incomparable with those bounds.

The single judged task performs:

```text
1. Parse <PHONE_E164> locally and retain it outside Ginse.
2. Verify and show the signed bounded bootstrap envelope; obtain the allowed approval.
3. Create the protected device signing key and generate `install_id` inside the trusted shim, independently of prompt values.
4. Invoke Fredo's single Ginse action with the public-key thumbprint.
5. Validate the response envelope and ensure BootstrapPlan stays within the approved bounds.
6. Install and verify the pinned Fredo release and Codex plugin.
7. Create the protected confirmation key, persist `redemption_id`, and redeem LeaseClaim with both key thumbprints and device-key proof.
8. Run fredo doctor --json.
9. Invoke the installed fredo executable directly with the retained call request.
10. Show Fredo's native DialPreview and obtain its one-use confirmation.
11. Return Fredo's structured result after hangup.
```

Codex loads a newly installed plugin only in a new chat or CLI session. Therefore plugin discovery in a later fresh task is a post-install verification, not a handoff required for the first call.

The judge MUST NOT type a shell command, paste a key, edit a file or environment variable, install a prerequisite manually, or send a second natural-language prompt.

## Locality and failure boundary

```text
Ginse receives: profile selectors, install_id, device-key thumbprint, release resolution, provider operation
Ginse never receives: destination, intent, caller identity, call credential, audio, transcript, result
```

Hosted Codex may orchestrate bootstrap. Live call-side STT, dialogue inference, TTS, state, and transcript processing run on the Mac. SIP/RTP may traverse the gateway and carrier, but no call audio enters Ginse, Codex, a model registry, or hosted inference.

After a plan is redeemed and artifacts are installed, loss of Ginse connectivity MUST NOT prevent local health checks or an already authorized gateway-backed call. Authority, gateway, or policy unavailability still fails closed where the capability contract requires it.

## Acceptance evidence

The Ginse integration passes only when:

- authentication, schema, exact replay, divergent replay, expiry, and redaction tests pass;
- claim theft, replay, wrong binding, and downgrade tests fail closed;
- captured payloads prove call data is absent by schema and on the wire;
- a staging version drives the same-task install and direct-CLI first-call path;
- a later fresh session discovers the installed plugin;
- clean-machine and telecom acceptance use the exact staging artifacts;
- the accepted version is promoted unchanged to immutable public Git and Ginse releases;
- a production smoke call uses that exact public version.

## Current implementation truth

No Fredo provider, Ginse manifest, schema set, lease authority, or published action exists in this repository yet. This document is a contract for implementation and verification, not evidence of a functioning integration.
