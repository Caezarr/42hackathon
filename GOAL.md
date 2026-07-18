# GOAL — Fredo

Status: normative hackathon acceptance specification

Version: `0.3-draft`

Target: Apple M4 Pro, 24 GB, macOS 26.5, `arm64`

Last audited: 2026-07-18

## 1. Purpose and authority

Build **Fredo**, a generic phone capability that a judge can discover through Ginse and use from Codex with one natural-language prompt.

This file defines **what must be true** for the hackathon goal to pass. It is the normative source for product behavior, safety properties, service levels, and evidence. `ROADMAP.md` orders the work; `docs/ARCHITECTURE.md` and ADRs may choose implementation technologies but may not weaken this contract.

The terms **MUST**, **MUST NOT**, **SHOULD**, and **MAY** are normative. Fredo is complete only when every mandatory gate in Section 12 passes against the exact release candidate and `EvidenceIndex` verifies every mapped requirement.

Acceptance items use stable identifiers (`GP.*`, `G0.*` through `G6.*`). The invariants in Section 8.3 use `I-01` through `I-12`. `EvidenceIndex` MUST map every acceptance item and invariant to a test oracle and immutable evidence; supporting normative clauses are verified through the item that cites their section.

## 2. Current implementation truth

At this revision, the end-to-end product does not exist.

| Capability | Current evidence | Status |
| --- | --- | --- |
| Product contract and architecture notes | repository documentation | present |
| Pinned upstream source candidates | `deploy/upstreams.lock.json` | partial; runtime/model digests absent |
| Local voice-cloning experiment | `voice-clone-poc/` | present, Windows-oriented, not integrated, stretch only |
| Fredo Codex plugin and skill | no plugin manifest or skill in repository | missing |
| `fredo` runtime and durable call control | no implementation | missing |
| Ginse `/run` provider and manifest | no implementation | missing |
| Demo-access authority and telecom gateway | no implementation | missing |
| Local realtime voice loop | no implementation | missing |
| Real PSTN call from Codex | no evidence | missing |

Documentation, a passing unit test, or an isolated voice-cloning POC MUST NOT be represented as proof that Fredo works.

## 3. Demonstration theorem

The exact judged use case is:

> “Use Ginse to prepare Fredo, then call `<PHONE_E164>`. This number belongs to a consenting judge. Introduce Fredo in French, disclose immediately that you are an automated synthetic voice, ask whether the demonstration works, then return the answer here.”

`<PHONE_E164>` is supplied once in the prompt and canonicalized locally to E.164. The destination remains in the Codex task and is never included in a Ginse request.

### 3.1 Meaning of “one prompt”

One prompt means exactly one natural-language message typed by the judge. The flow MAY request these named interactions:

1. one Codex approval for declared downloads and local writes;
2. standard macOS permission or administrator dialogs required by the signed installer;
3. one Fredo-owned native confirmation dialog after the exact call preview is shown.

The judge MUST NOT have to type a shell command, paste a credential, edit a file, configure an environment variable, install a prerequisite manually, or write a second natural-language prompt.

Before `/run`, the Ginse app version points to an immutable `BootstrapApprovalEnvelope` at the provider's same-origin `/.well-known/fredo-bootstrap-approval.json` path. Its SHA-256 and release-signing-key fingerprint are pinned in the verified app metadata. The envelope declares its schema/app version, monotonic policy version, issue/expiry time, maximum download bytes, peak disk, local paths, Keychain/device-key write, executable identities, and privilege classes. The Ginse shim verifies origin, digest, signature, expiry, app binding, and anti-downgrade state before Codex displays it and obtains the single local-write/download approval. The returned `BootstrapPlan` may narrow but never widen it; any wider or incomparable plan fails closed instead of asking for another approval.

Codex documentation establishes that a newly installed plugin becomes available only in a new chat or CLI session. Therefore the bootstrap task MUST invoke the installed `fredo` executable directly for the first call. Plugin discovery in a fresh session is a separate post-install verification and MUST NOT block the first run.

The already-installed and authorized Ginse use capability is the bootstrap shim. Under the declared local-write approval, it creates a protected device signing key before `/run`, then generates `install_id` internally from 128 CSPRNG bits, encoded as exactly 22 unpadded base64url characters. Neither the identifier nor key material is accepted from the prompt, model, or user; both are generated independently of every prompt value. The request carries only the public-key thumbprint, never private key material. The shim validates the public Fredo action schema and invokes Ginse before any Fredo code exists locally. No undisclosed Fredo prerequisite may be assumed.

### 3.2 Observable success

The demonstration succeeds only if the same Codex task:

1. invokes the single Fredo action on Ginse;
2. installs the pinned release without source edits;
3. obtains bounded demo telecom access without exposing a carrier master key;
4. passes the required local, network, and policy health checks;
5. shows a canonical call preview and obtains one-use confirmation;
6. makes the consenting judge's real phone ring from the expected verified caller number;
7. sustains a disclosed, bidirectional, interruptible conversation powered by local call-side models;
8. returns a structured result to Codex after hangup.

## 4. Scope and explicit boundaries

### 4.1 Mandatory hackathon scope

- one Apple Silicon profile;
- French, outbound calls only;
- one active call per installation;
- one verified team caller identity;
- Ginse as the mandatory discovery and bootstrap front door;
- local call-side STT, reasoning, TTS, state, and transcript processing;
- temporary team-funded telecom access for judges;
- explicit local confirmation before every dial;
- durable at-most-once call creation, cancellation, recovery, and result retrieval;
- a public, reproducible Git and Ginse release.

### 4.2 Meaning of “local”

“Local” applies to the **live conversation intelligence and durable Fredo state**, not to every control-plane or telecom packet.

- Codex MAY use its hosted control plane to interpret the initial prompt and orchestrate bootstrap.
- Ginse and the Fredo provider are remote bootstrap dependencies.
- The demo-access authority, SIP gateway, carrier, and PSTN are remote telecom dependencies.
- Call-side STT, dialogue inference, TTS, call state, and transcripts MUST run on the judge's Mac.
- Raw call audio MUST NOT be sent to Codex, Ginse, hosted inference, or model registries.
- A telecom gateway MAY relay SIP/RTP and therefore process call media in transit; it MUST NOT record audio or receive prompts, transcripts, model state, or summaries.

The optional `codex --oss` profile is valuable but is not a clean-machine prerequisite for the judged one-prompt flow.

### 4.3 Non-goals for this milestone

- arbitrary caller-ID presentation, anonymous calls, bulk dialing, scraping, or emergency calling;
- general support for every Mac, Linux, Windows, mobile, or every carrier;
- production multi-tenancy, multi-call concurrency, or formal telecom certification;
- inbound calls, voicemail handling, or unattended campaigns;
- BYOK during judging;
- voice cloning on the critical path;
- a production claim that a judge-controlled machine can keep a reusable secret unextractable.

## 5. Actors, trust, and data boundaries

| Actor | Role | Trusted for | MUST NOT receive |
| --- | --- | --- | --- |
| Judge | supplies destination, approves install and call | explicit consent and confirmation | carrier master credential |
| Codex task | bootstrap and call-control orchestration | executing approved local actions | raw call audio, telecom master credential |
| Ginse | marketplace discovery and fixed-price invocation | app identity, request transport, immutable listing version | destination, call intent, caller identity, audio, transcript, call result |
| Fredo provider | returns one deterministic bootstrap plan | release selection, Ginse auth, durable idempotency | destination, call content, transcript |
| Fredo local runtime | conversation, policy client, state and result | local secrets and call lifecycle | none beyond operator policy |
| Native confirmation helper | renders exact preview and signs one-use human authorization | local click and authorization-key custody | carrier credential, transcript, call audio |
| Demo-access authority | exchanges one-time claims for install-bound gateway capability | lease issuance, revocation, quotas | prompt, transcript, model state |
| SIP policy gateway | enforces server-side telecom limits and uses the team carrier account | destination policy, signaling, RTP relay | prompt, transcript, model state; audio retention forbidden |
| Carrier/PSTN | terminates the public phone call | verified caller identity and network delivery | application prompt, local transcript |

### 5.1 Explicit trust assumptions

For the hackathon, Ginse's verified app metadata, HTTPS to the declared provider, the allowlisted `Caezarr/42hackathon` repository, and the release signing key are roots of trust. Compromise of all those roots simultaneously is outside this milestone. A single compromised artifact origin, replayed response, modified manifest, or extracted local gateway token is inside the threat model.

### 5.2 Data classification

- **Public:** source, schemas, artifact digests, model licences, redacted evidence.
- **Operational:** install ID, release ID, provider operation ID, health and latency metrics.
- **Sensitive:** destination, caller identity, SIP metadata, transcript, unredacted CDR.
- **Secret:** provider signing key, carrier credential, gateway signing key, install-bound capability.

Secret values MUST never enter Git, Ginse plaintext output, stdout/stderr, SQLite, diagnostics, crash reports, public evidence, or Codex results.

## 6. Preconditions and clean-machine fixture

### 6.1 Reference host

| Property | Required fixture |
| --- | --- |
| Architecture | `arm64` |
| Chip | Apple M4 Pro |
| Memory | 24 GB unified memory |
| Operating system | macOS 26.5, fresh user account |
| Codex | CLI 0.144.1 or an explicitly tested compatible version, installed and authenticated |
| Ginse | current use capability installed and authorized before the judged prompt |
| Disk | final manifest peak-space requirement plus 20% headroom; never a hard-coded guess |
| Network qualification | measured before run; downstream at least 200 Mbit/s, RTT at most 40 ms to artifact mirror, packet loss below 1% |

The fixture MUST have no Fredo checkout, Fredo plugin, Fredo configuration, model cache, telecom capability, Docker Desktop, Homebrew, Python runtime prepared for Fredo, or manually staged artifact.

Fredo MUST package or fetch every mandatory dependency through the approved bootstrap. The mandatory path MUST NOT require an interactive third-party EULA, reboot, or a preinstalled container runtime. Optional architecture experiments may use Docker but cannot make it a judged prerequisite.

### 6.2 Telecom readiness precondition

Before any release candidate enters end-to-end qualification, the team MUST record:

- one carrier account and caller number verified for outbound presentation;
- one France-focused policy profile;
- a server-side account spend cap of at most EUR 50 for the judging window;
- a gateway path capable of enforcing the policy in Section 9 even if Fredo is bypassed;
- at least two consenting controlled test destinations;
- a default-deny exact-E.164 server allowlist containing only those controlled destinations and any jury destination enrolled before its capability is issued;
- the exact revocation procedure and an operator kill switch.

If the carrier cannot enforce one required limit, the SIP policy gateway is mandatory. Bootstrap MUST fail closed when neither the carrier nor gateway proves every server-side control.

## 7. Normative interfaces

Every Fredo-owned JSON payload, persisted document, and exported evidence document MUST have a JSON Schema checked into `schemas/`, use an explicit integer `schema_version`, reject unknown fields at security boundaries, and have positive and negative golden vectors. Third-party transport wrappers, including the Ginse `/run` envelope, follow their upstream contract and are validated separately. Canonical hashes of Fredo-owned documents MUST use RFC 8785 JSON Canonicalization Scheme plus SHA-256.

Required schemas:

- `BootstrapRequest`;
- `BootstrapApprovalEnvelope`;
- `BootstrapPlan`;
- `ArtifactManifest`;
- `LeaseClaim`, `RedemptionRequest`, `RedemptionResult`, and `GatewayCapability`;
- `DialRequest`;
- `DialPreview`;
- `DialAuthorization`;
- `CallEvent`;
- `DoctorReport`;
- `CallResult`;
- `EvidenceIndex`.

### 7.1 Single Ginse action

Fredo exposes exactly one fixed-price Ginse action: **Resolve a Fredo demo bootstrap**.

Its input contains only:

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

Its output is one `BootstrapPlan` containing:

- an immutable repository commit SHA;
- the release-manifest URL and SHA-256;
- the pinned Codex marketplace and plugin identity;
- a one-time, non-dialing `LeaseClaim`, cryptographically bound to `install_id`, the device-key thumbprint, release, and policy, issued with a 45-minute TTL that leaves at least 15 minutes for redemption after a conforming 30-minute cold bootstrap;
- the demo-access authority URL, policy digest, and plan expiry equal to the claim expiry.

The Ginse response envelope, outside the `BootstrapPlan`, carries the stable provider operation ID and replay flag required by the Ginse contract.

The request MUST NOT contain the destination or call intent. The `install_id` schema accepts exactly 22 base64url characters and `device_key_thumbprint` accepts the 43-character unpadded base64url SHA-256 of the canonical public-key encoding. The trusted Ginse shim is the only component allowed to populate them and MUST prove through deterministic taint tests that neither depends on prompt content. The provider MUST implement Ginse Ed25519 bearer verification, schema validation, atomic idempotency, stable operation IDs, exact replay, and divergent-replay rejection.

The one-time claim MAY transit Ginse because it has no dial authority. It MUST be redacted from logs and atomically consumed when the installed Fredo runtime exchanges it for an install-bound gateway capability.

### 7.2 Demo-access exchange

After installation, the signed native confirmation helper creates a separate protected authorization signing key that it uses only after rendering a canonical preview and receiving the local click. Fredo then recovers the precommitted device-key reference and redeems the `LeaseClaim` directly with the demo-access authority. Before its first network attempt it MUST durably persist a CSPRNG `redemption_id` and a canonical `RedemptionRequest` containing the authorization-key thumbprint. Redemption MUST:

- verify proof of possession for the precommitted device key;
- atomically bind the claim to one canonical redemption fingerprint;
- persist the terminal `RedemptionResult` before replying;
- return the exact stored result for an identical `redemption_id` retry and reject any divergent reuse or second redemption ID;
- bind the resulting capability to `install_id`, device public key, authorization-key thumbprint, release SHA, policy digest, and expiry;
- reveal no carrier master credential;
- issue only gateway access, never direct unrestricted carrier access;
- require device-key proof of possession on gateway use rather than acting as a transferable bearer secret;
- remain revocable per installation;
- fail closed on expiry, policy mismatch, replay, or authority unavailability.

The reference cryptographic construction belongs in an ADR. The normative properties are confidentiality, provider authenticity, install binding, anti-replay, anti-downgrade, rotation, and revocation.

### 7.3 Call request and human authorization

`DialRequest` MUST include the normalized destination, verified caller identity, canonical intent, maximum duration, locale, policy version, install ID, release SHA, lease ID, and idempotency key.

Fredo MUST render a native local `DialPreview` showing the full destination, caller identity, purpose, synthetic-voice disclosure, duration cap, and cost/policy profile. A Fredo-owned confirmation dialog — distinct from Codex's shell approval — transitions `PREPARED` to `AUTHORIZED`.

`DialAuthorization` MUST be a helper-signed, server-verifiable attestation with a unique authorization ID. It is single-use, expires within 60 seconds, and binds the canonical hash of every `DialRequest` field plus the capability, authorization-key thumbprint, policy, and release. The gateway MUST verify the signature and bindings and atomically consume the authorization ID with the dial idempotency key before any carrier attempt. Possession of the gateway capability and device key without this attestation MUST NOT authorize dialing.

After consumption, an identical retry MUST return the stored dial operation/status without another carrier effect; reuse with a different request, idempotency key, or authorization binding MUST fail closed.

Rejection or cancellation before `DIAL_COMMITTED` MUST create zero SIP `INVITE` attempts. Cancellation after `DIAL_COMMITTED` MUST use the persisted `CANCEL_REQUESTED`/`HANGUP_COMMITTED` path and may emit only the matching SIP `CANCEL` or `BYE`, never a new `INVITE`. Any request mutation requires a new preview and confirmation.

### 7.4 Doctor reports

`doctor` MUST emit named checks rather than one aggregate assertion:

- `local.artifacts` — every digest and size present;
- `local.runtime` — executable, model, audio, permissions, storage;
- `local.state` — migrations, durable journal, idempotency store;
- `network.bootstrap` — Ginse/provider/artifact availability, only before activation;
- `network.telecom` — gateway registration and media reachability without dialing;
- `policy.demo` — lease, server-side quotas, destination rules, kill switch;
- `release.provenance` — commit, manifest, signature and binary identity.

`doctor --offline` covers local checks only and MUST report network checks as `not_run`, never as healthy.

## 8. State machines and invariants

### 8.1 Bootstrap lifecycle

```text
UNINITIALIZED -> PLANNED -> APPROVED -> FETCHING -> VERIFIED
              -> INSTALLED -> LEASED -> HEALTHY -> ACTIVE
```

`FAILED` is reachable from every non-terminal state. Resume may continue only from the last durably verified artifact or transition. Partial bytes MUST never be activated.

### 8.2 Call lifecycle

```text
DRAFT -> PREPARED -> AUTHORIZED -> DIAL_COMMITTED -> RINGING -> CONNECTED
                                      |              |          |
                                      +-----> CANCEL_REQUESTED <-+
                                                   |
                                           HANGUP_COMMITTED
                                                   |
                    COMPLETED | CANCELLED | FAILED | RECONCILING
                                                           |
                                                   UNKNOWN_TERMINAL
```

The diagram is illustrative; this table is normative:

| From | Allowed next states |
| --- | --- |
| `DRAFT` | `PREPARED`, `CANCELLED`, `FAILED` |
| `PREPARED` | `AUTHORIZED`, `CANCELLED`, `FAILED` |
| `AUTHORIZED` | `DIAL_COMMITTED`, `CANCELLED`, `FAILED` |
| `DIAL_COMMITTED` | `RINGING`, `CONNECTED`, `CANCEL_REQUESTED`, `FAILED`, `RECONCILING` |
| `RINGING` | `CONNECTED`, `CANCEL_REQUESTED`, `FAILED`, `RECONCILING` |
| `CONNECTED` | `CANCEL_REQUESTED`, `HANGUP_COMMITTED`, `FAILED`, `RECONCILING` |
| `CANCEL_REQUESTED` | `HANGUP_COMMITTED`, `CANCELLED`, `COMPLETED`, `RECONCILING` |
| `HANGUP_COMMITTED` | `COMPLETED`, `CANCELLED`, `FAILED`, `RECONCILING` |
| `RECONCILING` | `COMPLETED`, `CANCELLED`, `FAILED`, `UNKNOWN_TERMINAL` |
| terminal states | `COMPLETED`, `CANCELLED`, `FAILED`, and `UNKNOWN_TERMINAL` have no outgoing transition |

Every dial, cancel, or hangup side effect MUST be preceded respectively by durable `DIAL_COMMITTED`, `CANCEL_REQUESTED`, or `HANGUP_COMMITTED`. If Fredo cannot determine whether the gateway or carrier accepted an effect after a crash or timeout, it MUST enter `RECONCILING`, query by the existing idempotency key without redialing, and end in the observed terminal state or `UNKNOWN_TERMINAL`. A later attempt always requires a new human authorization.

### 8.3 Mandatory invariants

Let `R` be a canonical `DialRequest`, `A` its authorization, `k` its idempotency key, and `D` a carrier dial.

1. **I-01 Authorization:** `D(R) => gateway_verified(A) AND unused(A) AND bind(A) = SHA256(R)`; capability proof alone is insufficient.
2. **I-02 At most once:** for every `k`, `count(carrier_call(k)) <= 1`, including concurrent retries and crash recovery.
3. **I-03 Rejection without effect:** rejected, expired, mutated, or blocked requests produce `count(SIP_INVITE) = 0`.
4. **I-04 Durability:** every state transition belongs to the graphs above and is persisted before its external effect.
5. **I-05 No blind redial:** an uncertain external result is reconciled, never retried as a new call automatically.
6. **I-06 Concurrency:** `active_calls_per_install <= 1`; gateway global concurrency MUST also hold.
7. **I-07 Bootstrap integrity:** only bytes present in the signed manifest and matching their digest may become executable or loadable.
8. **I-08 Ginse minimization:** Ginse payloads have no call-data fields, reject unknown fields, and contain no value data-dependent on destination, intent, caller ID, audio, transcript, or result; the CSPRNG `install_id` and device-key thumbprint are independently generated and taint-tested.
9. **I-09 Live local inference:** during `CONNECTED`, no call audio is sent to a hosted STT, LLM, TTS, or voice-agent endpoint.
10. **I-10 Secret isolation:** seeded secret canaries are absent from all prohibited sinks listed in Section 5.2.
11. **I-11 Remote speech is untrusted:** phone audio can never change destination, authorize another call, invoke a shell/tool, modify policy, or request a secret.
12. **I-12 Release equivalence:** the tested source, assets, provider image, Ginse version, and promoted release are linked by cryptographic digests.

## 9. Demo telecom policy

The judged policy is intentionally narrow and server-enforced:

| Control | Mandatory value |
| --- | --- |
| Capability TTL | at most 8 hours and no later than the published judging-window end |
| Lease-claim TTL | exactly 45 minutes from signed issue time |
| Completed calls | public judge capability: at most 3; team qualification capability: at most 6 |
| Total dial attempts | public judge capability: at most 6; team qualification capability: at most 10 |
| Attempt rate | at most 2 per minute per installation |
| Global judging-window ceilings | at most 30 completed calls and 60 total dial attempts |
| Claim/capability issuance | at most 1 active per device key; at most 30 claims and 30 capabilities for the judging window |
| Per-destination attempts | judge profile: at most 6; qualification profile: at most 10 |
| Concurrency | 1 per installation, 3 globally |
| Call duration | hard stop at 180 seconds |
| Spend | carrier-account cap at EUR 50 for the complete judging window |
| Eligible number class | French mobile `+336` and `+337` only; eligibility never grants access |
| Dial allowlist | default deny; exact E.164 entries enrolled server-side before capability issuance |
| Revocation propagation | new attempts denied within 30 seconds |
| Recording | disabled at Fredo, gateway, and carrier where configurable |

The capability carries either the `judge` or `qualification` profile and cannot select or widen its own profile. The `qualification` profile is issuable only to the team fixture and its higher quotas exist solely for Section 11.5. Both profiles, their exact allowlists, and all limits belong to one signed policy bundle and digest. Every gateway-accepted dial command consumes the total, per-destination, and global attempt quota before any carrier request; a failed, unanswered, cancelled, or non-connected call never refunds it. New `install_id` values cannot reset device-key, destination, global, or spend ceilings.

Emergency, premium-rate, short-code, anonymous, unsupported-country, merely class-eligible, and non-allowlisted destinations MUST fail before a carrier attempt. The allowlist stores exact canonical E.164 entries; `+336` and `+337` are only an outer eligibility filter, never a wildcard authorization. Enrollment is an operator-side precondition, not a capability granted by local confirmation. The policy dataset and digest MUST be versioned. The automated-voice disclosure MUST be the first substantive outbound audio, no later than five seconds after `CONNECTED`.

The remote participant must have consented to the test. Voicemail, third-party targets, do-not-call lists, and calls outside the judging protocol are out of scope and blocked.

## 10. Threat and failure model

The acceptance suite MUST cover at least:

- missing or invalid Ginse bearer token;
- exact idempotent replay and replay with different input;
- substituted commit, manifest, artifact, policy, lease, or release downgrade;
- truncated downloads, no Range support, disk full, permission refusal, and unavailable origin;
- claim theft/replay, wrong install binding, expired/revoked capability, and clock skew;
- redemption-response loss, exact redemption retry, divergent retry, wrong device-key proof, and claim-first theft;
- model- or user-supplied `install_id`, malformed entropy/encoding, and prompt-to-bootstrap taint;
- a judge bypassing Fredo and using the gateway capability directly;
- forged, expired, mutated, or replayed helper authorization attestations;
- blocked destination classes and policy-version mismatch;
- remote-audio prompt injection and attempts to trigger tools or new calls;
- concurrent `start`, retry after timeout, cancel/ring races, and simultaneous hangup;
- process kill at every state, corrupted local journal, model crash, port conflict, and locked Keychain;
- SIP registration loss, one-way RTP, packet loss, NAT failure, and carrier rejection;
- memory pressure, thermal throttling, and swap growth;
- secret leakage through logs, diagnostics, pcaps, crash reports, and evidence export.

Accepted hackathon risk: an administrator of the judge's Mac may coerce use of its protected key and short-lived gateway capability. Server-side allowlists, quotas, expiry, install-level revocation, and the absence of a carrier master key bound that risk.

## 11. Service levels and measurement protocol

### 11.1 Instrumentation

All timing uses one monotonic clock per host. Every record carries `release_sha`, `config_digest`, `run_id`, pseudonymous `call_id`, UTC, and monotonic timestamp.

- `turn_latency = first_outbound_voiced_PCM_frame - last_inbound_voiced_PCM_frame`;
- `barge_in_latency = last_outbound_voiced_PCM_frame - first_inbound_interrupt_frame`;
- `ring_setup = first_180_ringing - authorization_committed`;
- `result_latency = result_emitted - terminal_SIP_event_persisted`.

The VAD configuration, sample rate, codec, model revisions, thermal state, network measurements, and all raw observations MUST be recorded. Warm-up observations are retained but labelled; no outlier may be silently deleted.

### 11.2 Voice benchmark

- 100 measured turns: 10 sessions × 10 turns after two labelled warm-up turns per session;
- fixed, versioned French corpus covering four voices, three utterance lengths, silence, light noise, and G.711 8 kHz degradation;
- nearest-rank empirical median and P95, with a 10,000-resample bootstrap confidence interval reported as analysis rather than a stronger certification claim;
- median turn latency at most 1.5 seconds;
- observed P95 turn latency at most 2.5 seconds;
- 30 scripted interruptions; 30/30 barge-ins at most 500 ms and zero missed interruption;
- no hosted call-side inference network request during the measured window.

### 11.3 Resource envelope

Measure every Fredo process, local model, VM, and container at 10 Hz. The run passes only with:

- no OOM or process eviction;
- macOS memory pressure remaining green;
- swap growth below 1 GiB over the 100-turn benchmark;
- after a one-minute cooldown, aggregate `phys_footprint` sampled at 10 Hz for five idle minutes has least-squares slope at most 1 MiB/minute and the last 30-second median is no more than 64 MiB above the first 30-second median;
- artifact bytes and peak disk use not exceeding the signed manifest values.

### 11.4 Bootstrap qualification

Run three controlled scenarios from the fixture in Section 6:

1. cold bootstrap with a network interruption between 30% and 70% of one large artifact;
2. cold uninterrupted bootstrap from an equivalent clean APFS volume or documented full reset;
3. warm bootstrap plus daemon crash/recovery.

Each cold bootstrap MUST complete within 30 minutes under the qualified network and final manifest-size bound. The interrupted run MUST resume verified bytes. The warm run MUST download zero artifact body bytes.

### 11.5 Telecom qualification

Before the jury call, the team runs qualification on a separate controlled installation using the signed `qualification` profile. The public judged prompt receives the `judge` profile on the clean jury installation. Both use the exact candidate bytes and the same signed policy bundle; only the server-issued capability profile differs.

- 5/5 controlled calls must ring, connect, disclose, exchange three scripted facts in both directions, handle one interruption, hang up, and return a result;
- each controlled call must remain connected for at least 90 seconds;
- `ring_setup` must be at most 20 seconds for every controlled call;
- `result_latency` must be at most 5 seconds for every controlled call;
- two independent listeners must mark all three scripted facts intelligible in each direction;
- the real jury call must then complete once without an operator workaround.

## 12. Acceptance gates

### GP — Preconditions

- **GP.1** Reference fixture and network qualification are recorded.
- **GP.2** Carrier, caller identity, policy gateway, two controlled destinations, spend cap, and kill switch are proven.
- **GP.3** The exact one-prompt text and France demo policy are frozen.

### G0 — Contracts and trust

- **G0.1** Every schema in Section 7 exists with positive and negative vectors.
- **G0.2** Ginse `/run` and demo-access redemption pass authentication, schema, durable idempotency, response-loss replay, divergent-reuse, proof-of-possession, and redaction tests.
- **G0.3** Release and policy trust roots, downgrade rules, provider identity, and `BootstrapApprovalEnvelope` origin/signature/app binding are documented and tested.
- **G0.4** Destination and intent fields are absent, unknown fields are rejected, and value-level taint plus wire evidence proves no Ginse value depends on destination or intent.
- **G0.5** A valid plan that narrows every approved bound passes; widened, incomparable, expired, substituted, cross-app, and downgraded approval envelopes or plans fail before local writes.

### G1 — Candidate bootstrap

- **G1.1** A release candidate is published to a non-public or clearly labelled staging Ginse app/version.
- **G1.2** All artifacts are available from a team-controlled mirror or hash-identical fallback and match the signed manifest.
- **G1.3** The three bootstrap scenarios in Section 11.4 pass without a manual shell or second typed prompt, including exact redemption replay after response loss.
- **G1.4** Local, network, policy, and provenance doctor reports have the required status semantics.
- **G1.5** A fresh Codex session discovers the installed plugin after the first-run CLI path succeeds.

### G2 — Local conversation

- **G2.1** The full benchmark and resource envelope in Sections 11.2 and 11.3 pass.
- **G2.2** A deny-by-default egress test permits only the declared phase-specific endpoints.
- **G2.3** Call audio never reaches Codex, Ginse, model registries, or hosted inference.

### G3 — Safety and at-most-once behavior

- **G3.1** Rejection, expiry, mutation, policy mismatch, and prohibited destinations generate zero carrier attempt.
- **G3.2** Parallel and repeated start requests create at most one carrier call.
- **G3.3** The native helper signs every required field and the gateway verifies and atomically consumes the one-use `DialAuthorization`; capability-plus-device-key bypass fails.
- **G3.4** Server-side allowlists and issuance, per-device, per-destination, total-attempt, completed-call, global, and spend ceilings remain effective when the local client is bypassed or new install IDs/device keys are requested.
- **G3.5** Revocation blocks a new attempt within 30 seconds.

### G4 — Real telephony

- **G4.1** All five controlled calls and the one jury call meet Section 11.5.
- **G4.2** Verified caller identity, disclosure, DTMF/event correlation, interruption, hangup, and duration cap are recorded.
- **G4.3** No audio recording exists at Fredo or the policy gateway.

### G5 — Recovery, privacy, and evidence

- **G5.1** Kill/restart at every non-terminal state produces only legal recovery transitions and never a blind redial.
- **G5.2** Offline local doctor passes with network checks correctly marked `not_run`.
- **G5.3** Secret canaries are absent from every prohibited sink.
- **G5.4** The structured result is redacted and available within the result SLO.
- **G5.5** The evidence index validates every artifact hash and external attestation.

### G6 — Promotion and public release

Promotion follows this order:

```text
candidate commit
  -> signed/notarized release assets + SBOM + provenance
  -> staging Ginse verification
  -> clean-machine and telecom acceptance
  -> immutable Ginse app version + public Git release
  -> production smoke call using the exact published version
```

The release record MUST bind:

- Git commit SHA and informational tag;
- SHA-256 for every release asset and external model/runtime artifact;
- provider and gateway OCI image digests;
- SBOM and build provenance digests;
- Ginse app ID, immutable version, manifest digest, and listing URL;
- policy digest and caller identity;
- the exact evidence-index digest.

The promoted bytes MUST equal the accepted bytes. The worktree must be clean, no local-only step may exist, and the public copyable Ginse prompt must complete one production smoke call.

- **G6.1** Every release record field above resolves to immutable, digest-matching material.
- **G6.2** The accepted and promoted bytes are identical and the public copyable prompt completes the production smoke call.

## 13. Evidence bundle and traceability

The canonical bundle is local until redaction; only safe derivatives and hashes may be committed.

```text
evidence/<release-id>/
  index.json
  MANIFEST.sha256
  environment/inventory.json
  release/release-lock.json
  release/sbom.cdx.json
  release/provenance.json
  ginse/verification.json
  ginse/request.redacted.json
  ginse/idempotency.json
  bootstrap/approval-envelope.json
  bootstrap/cold-interrupted.ndjson
  bootstrap/cold.ndjson
  bootstrap/warm.ndjson
  doctor/local.json
  doctor/network.json
  doctor/policy.json
  network/egress-summary.csv
  benchmark/turns.csv
  benchmark/summary.json
  safety/authorization.json
  safety/blocked-destinations.json
  safety/bypass.json
  telephony/sip-events.redacted.ndjson
  state/crash-matrix.json
  result/result.redacted.json
  credential/policy.redacted.json
  credential/redemption.redacted.json
  credential/revocation.redacted.json
  demo/uncut.mp4
```

Minimum traceability:

| Requirement group | Test oracle | Required evidence |
| --- | --- | --- |
| `G0.*`, `I-08` Ginse and approval contracts | exact replay, divergent replay refusal, schema allowlist, signed bounds and narrowing | `ginse/*`, `bootstrap/approval-envelope.json` |
| `G1.*`, `I-07` Bootstrap integrity | digest equality, resume, zero-byte warm run | `bootstrap/*`, `release/release-lock.json` |
| `G2.*`, `I-09` Local inference | egress deny, 100-turn metrics | `network/*`, `benchmark/*` |
| `G3.1`–`G3.3`, `I-01`–`I-05` Authorization | canonical hash, one-use token, zero `INVITE` on reject | `safety/authorization.json` |
| `G3.4`–`G3.5`, `I-06`, `I-10`–`I-11` Abuse controls | redemption replay, server-side bypass, issuance/attempt quotas, and revocation | `safety/bypass.json`, `credential/*` |
| `G4.*` Telephony | five controlled calls plus jury call | `telephony/*`, `demo/uncut.mp4` |
| `G5.*`, `I-04`–`I-05` Recovery and evidence | crash matrix, no blind redial, evidence validation | `state/crash-matrix.json`, `index.json` |
| `G6.*`, `I-12` Release equivalence | digest graph from source to Ginse | `release/*`, `index.json` |

`index.json` MUST identify every requirement, test ID, environment, result, evidence path, SHA-256, and external attestation. Missing, indirect, or unhashable evidence is a failure, not “not applicable”.

## 14. Deferred work and non-normative experiments

The following may proceed only after the mandatory path is green and must remain feature-flagged:

- Moshi-MLX full-duplex mode;
- consented voice cloning and integration of `voice-clone-poc/`;
- Android Bluetooth, SIM gateway, inbound calls, and Linux/NVIDIA inference;
- BYOK and per-install carrier ownership;
- general multi-Mac packaging, multi-call operation, rollback, and air-gap bundles;
- dashboard and recordings where lawful and explicitly consented;
- live phone UI that rings and shows the call in real time as a handset-side demo simulation.

Pipecat, LiveKit, LiveKit SIP, Asterisk, PyVoIP, SQLite, Python versions, Docker, and the precise envelope algorithm are architecture hypotheses, not success criteria. They may be replaced if the replacement preserves every invariant and passes every gate.

## 15. Decisions that must close before implementation lock

These are bounded design choices, not permission to weaken the goal:

1. select the carrier and prove its caller-ID and account-cap behavior;
2. select and deploy the mandatory SIP policy gateway path;
3. choose the signed plan and install-bound lease construction in an ADR;
4. choose the local STT/LLM/TTS engine from measured candidates;
5. choose the media transport that passes qualification first;
6. define the signed native macOS confirmation helper;
7. replace the unresolved spoken candidate “Miro 2.5” with an exact repository/model or remove it.

No architecture freeze occurs until GP and G0 can be executed against real artifacts.

## Completion statement

Fredo passes when one consenting judge, from the clean reference fixture, types one parameterized Ginse prompt and — after only the named approval dialogs — receives a real, disclosed, policy-bounded phone call driven by local conversation models, with an at-most-once durable result returned to the same Codex task, and when the exact tested bytes are promoted to public Git and Ginse releases with a verified evidence graph.
