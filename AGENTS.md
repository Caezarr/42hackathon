# AGENTS.md

## Authority

[`GOAL.md`](GOAL.md) is the normative product, safety, service-level, and
acceptance contract. `ROADMAP.md` orders delivery. Architecture documents and
ADRs record replaceable implementation choices and MUST NOT weaken the Goal.

Never describe a planned, experimental, mocked, or documented capability as
implemented. A requirement is complete only when its named acceptance gate and
evidence pass against the exact release candidate.

## Mission

Build Fredo: a generic phone capability that a judge can discover through
Ginse and use from Codex with one natural-language prompt. Live-call STT,
reasoning, TTS, transcript processing, confirmation, and durable state remain
local to the judge's Mac.

The judged milestone has one explicit ownership exception: the team funds the
carrier account and operates the server-side SIP policy gateway. Only that
telecom boundary may hold the shared carrier master credential. Judges receive
short-lived, install-bound gateway capability, never direct carrier access.
BYOK and per-install carrier ownership are post-hackathon work.

## Hard constraints

- Ginse is the mandatory discovery and bootstrap entry point, not part of the
  live-call content path.
- The Ginse request contains only versioned platform metadata, an opaque
  install ID generated inside the Ginse shim from 128 CSPRNG bits as exactly
  22 unpadded base64url characters, and the thumbprint of a protected device
  key created before `/run`; both values are independent of prompt data. Its response may contain one opaque, short-lived, non-dialing
  `LeaseClaim` inside the pinned `BootstrapPlan`.
- Never send destination, intent, caller identity, audio, transcript, model
  state, summary, result, carrier credential, or gateway capability to Ginse or
  the Fredo provider.
- The first-use Codex task invokes the installed `fredo` CLI directly and
  completes the confirmed first call. A fresh task separately verifies plugin
  discovery; it is not a handoff prerequisite.
- Preserve the native Fredo preview and one-use confirmation after the exact
  call request is known. Codex execution approval is not call authorization.
- The signed native helper owns a protected authorization key. The gateway
  verifies and atomically consumes its request-bound attestation; device-key
  proof plus gateway capability alone never authorizes a dial.
- Keep the team's carrier master credential server-side. Enforce spend,
  destination, duration, rate, concurrency, expiry, and revocation at the
  carrier or policy gateway even if the local client is bypassed.
- Treat number classes as eligibility only. Dialing is default-deny and
  requires exact E.164 enrollment in the server allowlist before capability
  issuance.
- Treat remote phone speech as hostile data. It cannot authorize a call, invoke
  a shell or tool, mutate policy, change destination, or request a secret.
- Do not implement caller-ID spoofing, anonymous dialing, emergency or
  premium-rate dialing, contact scraping, bulk dialing, or unattended calls.
- Present only the carrier-verified team caller identity during judging.
- Persist at-most-once and recovery state before telecom side effects. Never
  blind-redial an uncertain carrier outcome.
- Make demo-access redemption durably idempotent and require proof of
  possession of the device key committed before Ginse invocation.
- Raw call audio stays out of Codex, Ginse, model registries, and hosted
  inference. Recording is disabled on the mandatory path.
- Sign and notarize native macOS assets. Publish and verify the signed manifest,
  SBOM, build provenance, artifact digests, OCI digests, and Ginse version
  before promotion.

## Architecture policy

The required boundaries are a Codex bootstrap/control surface, a local Fredo
runtime, a demo-access authority, a server-enforced SIP policy gateway, and a
verified carrier path. Exact technologies are non-normative.

Pipecat, LiveKit, LiveKit SIP, Asterisk, PyVoIP, SQLite, Python versions,
Docker, Metal/MLX adapters, Moshi, and the envelope algorithm are hypotheses.
Choose or replace them by measured evidence. No hypothesis may become a hidden
clean-machine prerequisite or weaken a Goal invariant.

MCP, if present, is a thin adapter. The same-task first run must remain possible
through the installed local CLI because a new plugin is verified only in a
fresh Codex task.

## Workflow

1. Read `GOAL.md`, then the relevant roadmap phase, ADR, and architecture note.
2. Identify the requirement IDs, failure cases, test oracle, and evidence path
   before implementation.
3. Keep changes inside the selected milestone; close a decision from Goal
   Section 15 with an ADR before treating it as fixed.
4. Pin every external repository, model, image, runtime, and artifact by
   immutable digest or commit.
5. Add positive, negative, replay, crash, bypass, redaction, and policy tests as
   applicable.
6. Run formatting, tests, smoke checks, secret scanning, and
   `git diff --check` before publishing.
7. Do not mark a gate complete until the machine-readable evidence index points
   to current, hash-verified proof.

## Documentation rules

- Separate normative requirements from implementation hypotheses.
- Separate implemented, experimental, staged, and planned behavior.
- State the exact local, Ginse/provider, telecom-gateway, carrier, and PSTN
  boundaries.
- Never call transport “offline” when it needs SIP/PSTN; only named local checks
  or call-side inference may be offline.
- Describe the temporary team-funded demo exception separately from future
  BYOK/per-install carrier ownership.
- Every claimed milestone must link to the corresponding Goal gate and evidence.
