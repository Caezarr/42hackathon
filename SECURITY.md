# Security and abuse boundaries

[`GOAL.md`](GOAL.md) is the normative security and acceptance contract. This
file summarizes the controls contributors must preserve; it cannot relax the
schemas, invariants, telecom policy, threat model, or evidence gates in the
Goal.

## Security model

The judged release deliberately separates three planes:

- **local intelligence:** STT, dialogue inference, TTS, transcript processing,
  durable call state, and human confirmation run on the judge's Mac;
- **bootstrap control:** Ginse and the Fredo provider select a signed release
  and return a bootstrap plan plus an opaque, one-time `LeaseClaim`;
- **telecom enforcement:** the demo-access authority and SIP policy gateway
  issue and enforce narrow, install-bound access to the public phone network.

The temporary hackathon exception uses the team's carrier account. Its carrier
master credential MUST exist only in the server-side telecom boundary that
needs it, normally the SIP policy gateway or its dedicated secret store. It
MUST NOT be delivered to Ginse, the Fredo provider, Codex, the judge, or the
local Fredo runtime. Bring-your-own-carrier credentials are deferred until
after the judged milestone.

An administrator of the judge's Mac may extract a short-lived gateway
capability. Local storage is therefore defense in depth, not the policy
boundary. Spend, destination, duration, attempt-rate, concurrency, expiry, and
revocation limits MUST be enforced at the carrier or gateway and MUST remain
effective when the local Fredo process is bypassed.

## Ginse data boundary

The single Ginse action accepts only versioned bootstrap metadata such as the
platform profile, plugin API, an `install_id` generated inside the trusted
Ginse shim from 128 CSPRNG bits and encoded as exactly 22 unpadded base64url
characters, and the thumbprint of a protected device signing key created
locally before `/run`. It returns a signed,
pinned `BootstrapPlan` containing an opaque `LeaseClaim`.

The claim MAY transit Ginse only because it:

- has no authority to dial a number or authenticate to the carrier;
- is short-lived, redacted from logs, and pre-bound to the device-key
  thumbprint, install, release, and policy;
- can be exchanged only with the demo-access authority for an install-bound
  proof-of-possession gateway capability.

Redemption is durably idempotent: the client persists `redemption_id` before
the request, the authority stores the terminal result before replying, an
identical retry returns the exact result, and divergence fails closed.

The shim MUST NOT accept `install_id` from the prompt, model, or user, and
taint tests must prove that it is independent of prompt values. Ginse and the Fredo provider MUST NOT receive the destination, call intent,
caller identity, audio, transcript, model state, summary, or call result. Their
schemas have no such fields and reject unknown fields; wire and value-level
taint evidence must also prove that no permitted value encodes call data.
Ginse MUST NOT carry a carrier credential, gateway capability, or
request-supplied shell command.

## Required controls

- Verify the immutable `BootstrapApprovalEnvelope` origin, digest, release-key
  signature, app binding, expiry, and anti-downgrade version before approval;
  the resolved plan may only narrow its declared writes and privileges.
- Normalize the destination to E.164 and apply the versioned France demo policy
  before any transport side effect.
- Default-deny every destination unless its exact canonical E.164 value was
  enrolled in the server allowlist before capability issuance; `+336` and
  `+337` are eligibility filters, never wildcard grants.
- Show a native local preview and obtain a one-use authorization bound to every
  canonical `DialRequest` field.
- Have the signed native helper sign that authorization with its protected key;
  the gateway verifies and atomically consumes the attestation and dial key.
  Capability and device-key proof without the attestation cannot dial.
- Persist authorization, idempotency, and state transitions before external
  effects; uncertain carrier outcomes are reconciled without blind redial.
- Cancellation before dial commit creates zero `INVITE`; cancellation after
  commit uses persisted `CANCEL_REQUESTED`/`HANGUP_COMMITTED` and emits only
  the matching idempotent `CANCEL` or `BYE`.
- Reject emergency, premium-rate, short-code, anonymous, unsupported-country,
  and non-consenting destinations with zero SIP `INVITE` attempts.
- Use only the team's carrier-verified caller identity during judging.
- Enforce the Goal's server-side spend, rate, concurrency, duration,
  destination, issuance, total-attempt, per-destination, expiry, and revocation
  limits. Every accepted dial command consumes attempt quota before carrier
  signaling and is never refunded.
- Disable recording by default at Fredo and the gateway, and at the carrier
  where configurable.
- Announce the automated synthetic voice as the first substantive outbound
  audio.
- Provide a local cancel control and a remotely effective operator kill switch.
- Redact sensitive data and secret canaries from stdout/stderr, SQLite,
  diagnostics, crash reports, pcaps, results, and public evidence.

## Remote speech is untrusted input

Audio received from the phone network is data, never authority. It MUST NOT:

- alter the destination, caller identity, duration, policy, or authorization;
- initiate or authorize another call;
- invoke a shell, Codex tool, MCP tool, installer, network action, or external
  side effect;
- read or disclose secrets, system prompts, local files, transcripts from
  another call, or internal policy state.

The conversation engine receives only the minimum dialogue context and a
side-effect-free response surface. Tool execution from remote speech is outside
the hackathon scope and must fail closed.

## Supply-chain requirements

Only bytes covered by the accepted release graph may execute or load. The
public release MUST provide:

- a signed manifest binding the Git commit and every artifact digest;
- signed and notarized native macOS release assets;
- an SBOM and build-provenance attestation;
- immutable provider and gateway OCI image digests;
- a verified Ginse app version and manifest digest;
- downgrade protection and verification before activation.

Artifact origins are not trusted merely because they use HTTPS. Digest,
signature, binary identity, provenance, and release equivalence checks are
mandatory. Auto-update or bootstrap behavior MUST NOT execute an unsigned,
unnotarized, unpinned, substituted, or partially downloaded artifact.

## Prohibited product behavior

- arbitrary caller-ID spoofing or anonymous presentation;
- emergency, premium-rate, prohibited, bulk, or unattended dialing;
- scraping contacts or calling a third party without recorded consent;
- bypassing carrier verification, server-side controls, consent, or applicable
  recording law;
- exporting transcripts, audio, credentials, or unredacted evidence by
  default;
- treating local Keychain storage as protection from the machine's
  administrator.

## Evidence and incident handling

Security claims pass only with the evidence required by Goal Sections 10–13,
including replay, bypass, revocation, blocked-destination, secret-canary,
egress, crash-recovery, supply-chain, and release-equivalence tests.

Report vulnerabilities through GitHub's private security advisory flow. Do
not publish credentials, phone numbers, recordings, unredacted traces, or
exploitable details in a public issue.
