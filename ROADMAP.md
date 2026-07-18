# Fredo delivery roadmap

Status: delivery order derived from [`GOAL.md`](GOAL.md) `0.3-draft`.

`GOAL.md` is normative. This roadmap orders the proofs needed to satisfy it; it does not relax its invariants, service levels, or gates.

## Current truth

The repository does not yet contain an end-to-end Fredo product. It contains the acceptance specification, architecture research, pinned upstream candidates, and an isolated Windows-oriented voice-cloning experiment. The Codex plugin, `fredo` runtime, Ginse provider, demo-access authority, policy gateway, local realtime loop, and real-call evidence are all still missing.

No phase is complete because its document exists. A phase exits only with the stated executable evidence against one identified release candidate.

## Frozen judged path

The judge types this single parameterized message:

> “Use Ginse to prepare Fredo, then call `<PHONE_E164>`. This number belongs to a consenting judge. Introduce Fredo in French, disclose immediately that you are an automated synthetic voice, ask whether the demonstration works, then return the answer here.”

The same Codex task MUST:

1. create a protected device key and invoke Fredo's single Ginse action with its thumbprint and a locally generated `install_id`;
2. install and verify the pinned Fredo release after the declared approval;
3. redeem the returned non-dialing `LeaseClaim` for an install-bound gateway capability;
4. invoke the installed `fredo` executable directly;
5. show the native call preview and obtain its one-use confirmation;
6. place the call through the mandatory demo policy gateway;
7. return the structured result after hangup.

The phone number remains local and never enters Ginse. A fresh Codex task is used only afterward to verify that the installed plugin is discoverable; it is not part of first-call bootstrap.

## Delivery principles

- Ginse is the mandatory discovery and bootstrap front door from the first vertical slice.
- The exact schemas and state machines in `GOAL.md` precede implementation.
- Call-side STT, dialogue inference, TTS, state, and transcript processing run locally on the Mac.
- Hosted Codex may orchestrate bootstrap; no call audio enters Codex, Ginse, or hosted inference.
- The team carrier master credential remains at the gateway. The client receives only a short-lived, install-bound capability.
- The gateway is mandatory for the judged flow because it enforces policy even if the local client is bypassed.
- Pipecat, LiveKit, Asterisk, SQLite, Python, Docker, and individual models are replaceable hypotheses, not milestones.
- Each phase ends with hashed evidence linked to a release SHA and configuration digest.

## Gate traceability

| Phase | Normative acceptance owned |
| --- | --- |
| P0 | `GP.*`, `G0.1`, `G0.3` |
| P1 | `G0.2`, `G0.4`, server-control prerequisites for `G3.4`–`G3.5` |
| P2 | `G0.5`, `G1.*`, bootstrap portion of `G5.2`–`G5.3` |
| P3 | `G2.*` |
| P4 | `G3.*`, `G5.1`, local portions of `G5.3`–`G5.4` |
| P5 | `G4.*`, telecom portions of `G5.3`–`G5.4` |
| P6 | `G5.5`, `G6.*`, final cross-gate verification |

## P0 — Preconditions, contracts, and trust

### Deliver

- Freeze the exact one-prompt text and France demo policy.
- Record the M4 Pro, 24 GB, macOS 26.5 clean-machine fixture and qualified network.
- Prove one verified outbound caller identity, two consenting controlled destinations, a EUR 50 account cap, and an operator kill switch.
- Select a server-enforced SIP policy gateway path.
- Add JSON Schemas and positive/negative vectors for every interface listed in `GOAL.md` Section 7.
- Document trust roots, signing identities, canonical JSON hashing, downgrade rules, and credential boundaries.

### Exit evidence

- `GP` and the contract portion of `G0` are executable, not aspirational.
- Malformed and unknown security-boundary fields are rejected.
- Destination and intent are structurally absent from `BootstrapRequest` and `BootstrapPlan`.
- Carrier and gateway diagnostics prove caller ID, quota enforcement, spend cap, revocation path, and zero recording.

### Cut line

Do not tune voice models before carrier readiness, gateway enforcement, and schemas are proven.

## P1 — Ginse, release plan, and demo access

### Deliver

- One publicly reachable HTTPS `/run` provider behind an unlisted or clearly labelled staging Ginse app version; the marketplace listing remains non-public until G6 promotion.
- Ginse Ed25519 bearer verification, atomic idempotency, stable operation IDs, exact replay, and divergent-replay rejection.
- A schema-valid `BootstrapPlan` pinned to a full repository SHA and signed manifest digest.
- A one-time non-dialing `LeaseClaim`, issued for 45 minutes so a conforming 30-minute cold bootstrap leaves redemption margin, bound to `install_id`, device-key thumbprint, release, and policy.
- A demo-access authority with durable idempotent redemption, proof of possession, exact replay after response loss, and only a short-lived, install/device/release/policy-bound gateway capability.
- A protected signing key created before `/run` plus a 128-bit CSPRNG `install_id` generated inside the Ginse shim, with fixed encodings and prompt-taint tests.
- Server-side redaction and canary tests proving no carrier master secret or call-derived bootstrap value enters Ginse, logs, or client storage.

### Exit evidence

- Ginse authentication, schema, replay, redaction, claim-first theft, proof-of-possession, redemption response-loss/replay, expiry, binding, and downgrade tests pass.
- Captured Ginse payloads contain no destination, intent, caller identity, audio, transcript, or call result.
- Direct use of a stolen or mismatched claim/capability fails closed.
- Bypassing the local Fredo client does not bypass gateway policy.

### Cut line

The provider resolves bootstrap only. Calling, status, cancellation, and results MUST NOT become extra Ginse actions.

## P2 — Signed bootstrap and same-task continuation

### Deliver

- Signed/notarized macOS release assets, signed `ArtifactManifest`, SBOM, and build provenance.
- Signed, versioned `BootstrapApprovalEnvelope` pinned by the Ginse app metadata, with origin, digest, signature, downgrade, and plan-narrowing verification.
- Content-addressed, resumable download and verified activation.
- Packaged mandatory runtime with no Homebrew, Docker Desktop, Python, source checkout, reboot, or interactive third-party EULA prerequisite.
- Installable Codex marketplace/plugin identity and native `fredo` executable.
- Structured `bootstrap plan`, `bootstrap apply`, lease redemption, and named `doctor` checks.
- Bootstrap continuation that invokes `fredo` directly in the original Codex task.

### Exit evidence

- Cold interrupted, cold uninterrupted, and warm/recovery scenarios from `GOAL.md` Section 11.4 pass.
- Each qualified cold run completes within 30 minutes; the warm run transfers zero artifact body bytes.
- Partial or substituted bytes never activate, and manifest sizes bound disk use.
- `doctor --offline` marks network checks `not_run` rather than healthy.
- The original task reaches the local call preview without a shell command or second prompt.
- A later fresh Codex session discovers the installed plugin.

### Cut line

The mandatory path may support only the frozen reference profile. Portability work waits.

## P3 — Local conversation and resource proof

### Deliver

- A repeatable local voice benchmark for viable STT/dialogue/TTS and full-duplex candidates.
- PSTN codec adaptation and interruption handling.
- Deny-by-default egress instrumentation proving live inference locality.
- Selection of one reference engine; every other engine remains optional.

### Exit evidence

- 100 measured turns: 10 sessions × 10 turns after two labelled warm-up turns per session.
- Median turn latency is at most 1.5 seconds; observed nearest-rank P95 is at most 2.5 seconds.
- 30/30 scripted barge-ins stop outbound speech within 500 ms.
- No hosted call-side inference request occurs during the measured window.
- No OOM or eviction, memory pressure stays green, swap growth stays below 1 GiB, and the five-minute idle `phys_footprint` slope/median bounds in `GOAL.md` pass.
- Raw observations, fixed corpus, model revisions, codec, thermal state, and bootstrap confidence intervals are retained.

### Cut line

Voice cloning and alternate engines stay off the critical path until the reference generic voice passes `G2`.

## P4 — Durable call control and safety

### Deliver

- Durable bootstrap and call state machines exactly matching `GOAL.md` Section 8.
- Canonical `DialRequest`, native `DialPreview`, and helper-signed, server-verifiable, single-use 60-second `DialAuthorization` binding every request field.
- At-most-once dial creation under concurrent retries and process crashes.
- Durable `CANCEL_REQUESTED`, `HANGUP_COMMITTED`, and `RECONCILING` transitions, ending in an observed terminal state or `UNKNOWN_TERMINAL` without blind redial.
- Local policy checks plus mandatory server-side quota, destination, concurrency, duration, spend, and revocation enforcement.
- Redacted structured result and evidence export.

### Exit evidence

- Reject, expiry, mutation, blocked destination, policy mismatch, and pre-commit cancellation each produce zero SIP `INVITE`; post-commit cancellation emits only idempotent `CANCEL`/`BYE`.
- Capability-plus-device-key bypass without a valid helper attestation is rejected at the gateway.
- Parallel and repeated starts create at most one carrier call per idempotency key.
- Process-kill tests at every non-terminal state produce only legal recovery transitions.
- Claim/capability issuance, per-device, per-destination, per-profile, and global attempt/completion ceilings remain enforced when the client is bypassed or reinstalled.
- Revocation denies new attempts within 30 seconds; hard hangup occurs at 180 seconds.
- Remote speech cannot authorize a call, change destination or policy, invoke a tool, or disclose a secret.

## P5 — Real telephony qualification

### Deliver

- One promoted media path from local Fredo inference through the policy gateway, verified carrier, and PSTN.
- Verified caller presentation, bidirectional audio, interruption, DTMF/event correlation, cancellation, hangup, and durable result.
- Synthetic-voice disclosure as the first substantive outbound audio and within five seconds of connection.

### Exit evidence

- 5/5 controlled calls ring, connect, disclose, exchange three intelligible facts in both directions, handle one interruption, and return a result.
- Each controlled call remains connected for at least 90 seconds.
- Every controlled call has `ring_setup <= 20 s` and `result_latency <= 5 s`.
- Two independent listeners mark all scripted facts intelligible in both directions.
- No Fredo or gateway audio recording exists.
- The jury call then succeeds once without operator workaround.

### Cut line

Debug one media path at a time. Disable failed alternatives behind feature flags.

## P6 — Acceptance, promotion, and public proof

### Deliver

- Complete evidence bundle and validating `EvidenceIndex`.
- Staging Ginse app/version for release-candidate verification.
- Uncut one-prompt demo recording from the clean fixture.
- Immutable public Git release and Ginse app version.
- Production smoke call using the exact published bytes.

### Promotion sequence

```text
candidate commit
  -> signed/notarized assets + SBOM + provenance
  -> staging Ginse verification
  -> clean-machine, safety, local-model and telecom acceptance
  -> immutable Ginse version + public Git release
  -> production smoke call of the exact published version
```

### Exit evidence

- `GP` through `G6` pass and every result resolves through the hashed evidence index.
- Source, assets, models, provider image, gateway image, policy, Ginse version, and evidence are joined by cryptographic digests.
- The promoted bytes equal the accepted bytes and the worktree is clean.
- The public copyable prompt completes the production smoke call.

## Hackathon cut line

### Never cut

- Ginse discovery and the single verified bootstrap action;
- exact one-prompt, same-task first-call flow;
- signed bootstrap integrity and clean-machine installation;
- local live conversation inference;
- native exact-call confirmation and at-most-once behavior;
- mandatory server-enforced demo policy gateway;
- verified caller identity, disclosure, real phone call, and structured result;
- acceptance-to-release digest equivalence.

### Cut in this order

1. voice cloning;
2. alternate/full-duplex voice engines;
3. dashboard and handset-side demo UI;
4. optional MCP adapter;
5. redundant media transports;
6. additional languages, platforms, carriers, and profiles;
7. BYOK, inbound calls, and generalized multi-user operation.

## After the hackathon

- BYOK and per-install carrier ownership;
- broader Apple Silicon compatibility, upgrade, and rollback;
- more transports, inbound calls, and policy packs;
- consented voice cloning;
- production multi-tenancy, compliance work, and longer-lived operations.
