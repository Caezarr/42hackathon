# GOAL — Fredo

## Status

Hackathon execution contract. Fredo is complete only when every mandatory gate below has recorded evidence on the reference machine.

## North star

Build **Fredo**, the local phone for Codex.

From a Codex task, a user can ask Fredo to call a real phone number, review exactly what will happen, confirm once, hold a bidirectional conversation powered by local models, interrupt or cancel it, and receive a structured result back in Codex.

The hackathon moment is deliberately simple:

> “Fredo, call the judge, introduce the project, ask whether the demo works, then summarize the answer.”

The judge's real phone must ring from a verified caller number.

## Ginse is the front door

Ginse is not an optional integration. It is how the hackathon user discovers and starts Fredo.

Ginse invokes one fixed HTTPS action, so it cannot directly install software on a user's Mac or call `localhost`. The Fredo Ginse action therefore returns a deterministic, versioned `BootstrapPlan`. Codex validates that plan, asks for local execution approval, installs the Fredo plugin and pinned runtime, then runs Fredo locally.

```text
Use Ginse to bootstrap Fredo
  -> Ginse returns BootstrapPlan
  -> Codex verifies repository, commit and manifest digest
  -> Codex installs the Fredo plugin
  -> fredo bootstrap applies the local profile
  -> fredo doctor proves readiness
  -> future calls stay local
```

Ginse never receives the destination number, call intent, SIP credentials, audio, transcript, or call result.

## Product boundary

Fredo is generic telephony infrastructure for Codex. It is not an administrative-call assistant, call-center SaaS, spoofing service, or shared carrier.

Every installation owns its:

- compute and models;
- SIP credentials and verified caller identity;
- phone numbers, call state, transcripts and logs;
- policies, retention and telecom costs.

There is no shared Fredo call backend.

For the hackathon, “local” means:

- Codex CLI uses a local OSS provider;
- STT, dialogue, TTS, audio, state and transcripts run on the Mac;
- no hosted inference, voice-agent, STT or TTS API is configured;
- GitHub, Ginse and model registries are used only for the explicit bootstrap;
- the SIP carrier remains the unavoidable external path to the public phone network.

Hosted Codex can be supported later, with its cloud boundary stated explicitly, but it is not the zero-cloud demo path.

## Reference machine

The only mandatory hackathon target is the machine inspected on 2026-07-18:

| Property | Reference |
| --- | --- |
| Architecture | `arm64` |
| Chip | Apple M4 Pro |
| Memory | 24 GB |
| macOS | 26.5 |
| System Python | 3.14.3 |
| Rust | 1.94.1 |

Moshi currently recommends Python 3.12 for its MLX package. Fredo must therefore create an isolated, pinned Python runtime instead of depending on the system Python.

Docker services may run locally on the Mac. One small team-owned HTTPS provider is mandatory because Ginse must be able to invoke Fredo's public `/run` action. It stores only bootstrap-plan idempotency data and may be colocated with a telecom edge, but the two roles remain independent. A public SIP/RTP edge is allowed only if carrier networking requires it; it is not a prerequisite for the first local voice loop.

## Integration contract

The canonical interface is the local `fredo` CLI with structured JSON input and output. A native daemon owns long-running calls over a Unix socket and persists jobs in SQLite WAL.

The Codex package is a plugin containing:

- a Fredo skill for the user workflow;
- the CLI bootstrap and invocation rules;
- an optional local STDIO MCP adapter over the exact same CLI/domain contract.

MCP is useful for typed tools, but no business logic may exist only in MCP. If MCP is unavailable, the skill can still invoke the CLI.

Target command surface:

```text
fredo bootstrap plan|apply
fredo doctor
fredo call prepare
fredo call confirm
fredo call start
fredo call status
fredo call cancel
fredo call result
```

## Reference runtime hypothesis

```text
Ginse BootstrapPlan
  -> Codex plugin + Fredo skill
  -> fredo CLI
  -> fredod + SQLite event journal
  -> Pipecat orchestration
  -> local STT + local LLM + local TTS on Apple Metal/MLX
  -> LiveKit media room
  -> LiveKit SIP and/or Asterisk transport boundary
  -> operator-owned SIP trunk
  -> judge's phone
```

The deliberately excessive Pipecat + LiveKit + Asterisk path stays only if it produces evidence. PyVoIP is a fast direct SIP/RTP laboratory adapter, not the trusted judge-call transport. Moshi-MLX is a full-duplex experiment behind a feature flag, not the default engine.

## Mandatory scope

- published and verified Ginse bootstrap-plan action;
- Fredo Codex plugin and skill;
- one-command bootstrap for the reference Mac;
- local CLI and durable daemon state;
- local STT, LLM and generic TTS;
- preview and explicit one-use confirmation before dialing;
- verified outbound SIP identity;
- one active outbound call at a time;
- bidirectional audio, interruption, hangup and cancellation;
- result returned to the originating Codex task;
- second call without downloading models or runtime dependencies.

## Stretch scope

- Moshi-MLX full-duplex mode;
- consented voice cloning;
- Android Bluetooth, SIM gateway or inbound calls;
- Linux/NVIDIA inference;
- multi-user or multi-call operation;
- generalized installation across arbitrary Macs;
- dashboard, recordings, air-gap bundles and automatic rollback.

## Measurable exit gates

### G0 — Ginse entry

- The team-owned Fredo provider is reachable over public HTTPS independently of the user's Mac and passes its authentication, schema and idempotency tests.
- The Fredo manifest passes Ginse verification and the listing is published.
- A fresh Codex task can invoke the documented `Use Ginse ...` prompt and receive a schema-valid `BootstrapPlan`.
- Replaying the same Ginse idempotency key returns the same plan and performs no duplicate side effect.
- The plan pins an immutable Git commit and manifest digest; it contains no arbitrary shell supplied by the request.
- A captured provider request proves that no phone number, call intent, audio or transcript reached Ginse.

### G1 — First bootstrap

- From the Ginse plan, Codex installs Fredo without editing a source file.
- The user sees the downloads, disk cost and permissions before one explicit approval.
- Every downloaded artifact records source, immutable version, expected size, license and checksum.
- An interrupted artifact download resumes instead of restarting from zero.
- Cold bootstrap completes in at most 30 minutes on the reference network and records elapsed time plus transferred bytes.
- `fredo doctor --json` reports every mandatory subsystem healthy.
- The bootstrap task ends with an explicit handoff, and a newly started Codex task loads the installed Fredo plugin without manual configuration edits.
- A second bootstrap transfers zero model or runtime artifact bytes.

### G2 — Local voice loop

- No hosted inference credential is configured.
- At least 20 measured local conversational turns complete while hosted inference endpoints are blocked.
- Median end-of-speech to first-agent-audio latency is at most 1.5 seconds.
- P95 end-of-speech to first-agent-audio latency is at most 2.5 seconds.
- Barge-in stops agent audio within 500 milliseconds.
- Total Fredo runtime memory remains below 20 GB on the 24 GB reference Mac.

### G3 — Safe Codex control

- Codex shows destination, verified caller identity, intent and duration limit before dialing.
- Rejecting confirmation creates zero SIP dial attempts.
- A confirmation is single-use and cryptographically bound to the resolved number and intent.
- Emergency, premium-rate, short-code and prohibited destinations are rejected before transport side effects.
- Codex can query status and cancel an active call.

### G4 — Real judge call

- The judge's phone rings from the expected verified number within 20 seconds of warm confirmation.
- Bidirectional audio remains usable for at least 60 seconds.
- Fredo announces that it is an automated synthetic voice within the first five seconds.
- At least three coherent conversational turns complete.
- One interruption is handled without losing the call.
- Carrier hangup is detected and persisted within two seconds.
- Repeating the same local idempotency key never creates a second call.

### G5 — Result and recovery

- A schema-valid result is available in Codex within five seconds of hangup.
- The result includes `call_id`, terminal status, duration, summary, outcome and next actions.
- Raw audio, SIP secrets and the full destination number never enter the Codex or Ginse result.
- Killing and restarting `fredod` preserves job state and terminal results.
- After restart, `fredo doctor --offline --json` passes and a second controlled call succeeds with zero artifact downloads.

## Evidence bundle

The goal cannot be marked complete without:

- [ ] Ginse listing URL, immutable version and successful verification output;
- [ ] redacted Ginse request proving the bootstrap-only data boundary;
- [ ] reference-machine inventory;
- [ ] pinned artifact manifest with checksums and licenses;
- [ ] cold, resumed and warm bootstrap logs;
- [ ] successful `doctor --json` and `doctor --offline --json` outputs;
- [ ] network proof showing zero hosted AI inference during the call;
- [ ] latency report for at least 20 turns;
- [ ] confirmation rejection with zero SIP attempts;
- [ ] redacted SIP trace or carrier detail proving the real call;
- [ ] SQLite call-event journal and crash-recovery proof;
- [ ] cancellation and idempotency proofs;
- [ ] structured result returned in Codex;
- [ ] second-call zero-download proof;
- [ ] one uncut demo recording from Ginse discovery, through the documented task handoff, to the Codex result.

## Completion sentence

Fredo passes when a fresh bootstrap task discovers Fredo through Ginse and installs the pinned local runtime, then a fresh Fredo task calls the judge's real phone with local AI and returns the answer to Codex with the evidence above.
