# GOAL — Fredo

## Status

Hackathon execution contract. Fredo is complete only when every mandatory gate below has recorded evidence on the reference machine.

## North star

Build **Fredo**, the local phone for Codex.

From a Codex task, a user can ask Fredo to call a real phone number, review exactly what will happen, confirm once, hold a bidirectional conversation powered by local models, interrupt or cancel it, and receive a structured result back in Codex.

The hackathon moment is deliberately one-prompt:

> “Use Ginse to get Fredo ready, then call the judge, introduce the project, ask whether the demo works, and summarize the answer.”

“One prompt” means one natural-language message typed by the judge. The flow may ask for named approval clicks: Codex download/local-execution approval, a standard macOS administrator approval if installation requires it, and one explicit Fredo call-confirmation click after the destination preview. Asking the judge to open or type in a shell, edit a file, paste a key, source an environment, or write a second prompt is not allowed.

The original Codex task must invoke the newly installed `fredo` CLI directly after `doctor` and finish the first call. If fresh-task plugin discovery is technically required, the bootstrap may also create a machine-readable handoff for later verification, but that handoff cannot block or replace the one-prompt first run. The judge's real phone must ring from a verified caller number.

## Ginse is the front door

Ginse is not an optional integration. It is how the hackathon user discovers and starts Fredo.

Ginse invokes one fixed HTTPS action, so it cannot directly install software on a user's Mac or call `localhost`. The Fredo Ginse action therefore returns a deterministic, versioned `BootstrapPlan`. Codex validates that plan, asks for local execution approval, installs the Fredo plugin and pinned runtime, then runs Fredo locally.

```text
Use Ginse to bootstrap Fredo
  -> Ginse returns BootstrapPlan
  -> Codex verifies repository, commit and manifest digest
  -> Codex installs the Fredo plugin
  -> fredo bootstrap applies the local profile
  -> a scoped demo telecom credential is provisioned
  -> fredo doctor proves readiness
  -> the same Codex task performs the confirmed first call
```

Ginse never receives the destination number, call intent, audio, transcript, or call result. Neither Git, plaintext Ginse output nor Fredo logs may contain a raw telecom credential. The preferred demo path uses carrier-issued short-lived subcredentials. If the selected carrier cannot issue them, the provider uses a disposable team demo credential, never the team's long-lived production master key. In both cases Ginse carries only an envelope encrypted to a pre-bootstrap public key generated on the judge's Mac.

## Product boundary

Fredo is generic telephony infrastructure for Codex. It is not an administrative-call assistant, call-center SaaS, spoofing service, or shared carrier.

Outside the temporary hackathon exception below, every installation owns its:

- compute and models;
- SIP credentials and verified caller identity;
- phone numbers, call state, transcripts and logs;
- policies, retention and telecom costs.

There is no shared Fredo inference, orchestration, state, audio or transcript backend.

### Temporary demo credential exception

During the judged demo window, all judges may use one team-owned telephony account through automatically provisioned disposable credentials. This exception covers telecom access only: inference, dialogue state and transcripts remain local. The carrier, and a team-controlled SIP gateway if the fallback requires one, necessarily processes the minimum signaling and media needed to place the call.

The provisioned material must:

- be short-lived, or be a disposable demo key disabled immediately after the demo;
- be scoped to dialing only when the carrier supports scopes;
- have carrier-account-side spend limits that cannot be bypassed from the judge's machine;
- enforce rate, concurrency, country and number-class policy at the carrier or team SIP gateway;
- reject emergency, premium-rate, short-code and prohibited numbers;
- be redacted from command output, process diagnostics, logs and results;
- be remotely revocable and rotated immediately after the demo;
- never expose the carrier's raw master key in Git or plaintext output.

A decrypted short-lived subcredential or disposable demo credential may temporarily exist on the judge's machine. Because the judge controls that machine, local restrictions alone are not a security boundary and the credential may be extractable. This is intentional time-bounded exposure, not a production security claim. Bring-your-own-key and per-install carrier ownership are post-hackathon requirements.

Credential delivery contract for every demo credential:

1. Before the first Ginse request, the same Codex task uses macOS `/usr/bin/openssl` to generate a temporary RSA-3072 keypair, random install ID and nonce. This path was verified against the reference Mac's built-in LibreSSL; it does not require Fredo to be installed first.
2. The private key stays in a `0700` temporary directory as a `0600` file and is never printed. The Ginse request contains only the public key, install ID, nonce and supported profile; provider idempotency binds them to the selected Fredo commit and expiry.
3. The provider encrypts a small credential payload with RSA-OAEP-SHA256. The encrypted payload contains the install ID, profile, Fredo commit and expiry so Fredo can reject substitution or replay.
4. After installation, Fredo validates the plan, decrypts the envelope, compares every bound field, stores only the telecom credential in macOS Keychain with access limited to the Fredo runtime, and immediately removes the temporary private-key directory. It never writes credential plaintext to a repository, config file, environment dump, output or log.
5. An aborted bootstrap cleans the temporary key on expiry or the next resume. Credential expiry or central revocation makes the transport fail closed; Fredo deletes the Keychain item and cached envelope after the demo.

If a SIP gateway is needed to enforce policy, it may retain only redacted operational metadata required for limits and audit. It must not receive prompts, model state or transcripts, and it must not record audio.

For the hackathon, “local” means:

- Codex CLI uses a local OSS provider;
- STT, dialogue, TTS, audio, state and transcripts run on the Mac;
- no hosted inference, voice-agent, STT or TTS API is configured;
- GitHub, Ginse and model registries are used only for the explicit bootstrap;
- the team demo carrier remains the unavoidable external path to the public phone network.

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

### Clean-machine acceptance baseline

The reproducible “clean Mac” gate starts from:

- the M4 Pro, 24 GB, `arm64`, macOS 26.5 profile above with a fresh user account;
- Codex CLI 0.144.1 or the release's declared compatible minimum already installed and authenticated, with the Ginse capability authorized;
- working internet, microphone/audio permissions when required, and at least 60 GB free disk;
- only macOS system tools plus Codex available to the user.

It must have no Fredo checkout, plugin, config, model cache, runtime, carrier credential, Homebrew, Docker, Python 3.12 or manually prepared environment. Fredo may install its own pinned dependencies after the named approvals above.

Docker services may run locally on the Mac. One small team-owned HTTPS provider is mandatory because Ginse must be able to invoke Fredo's public `/run` action. It stores bootstrap idempotency plus minimal credential-lease metadata for expiry, limits and revocation; it stores no call content. It may be colocated with a telecom edge, but the roles remain independent. A public SIP/RTP edge is allowed only if carrier networking requires it; it is not a prerequisite for the first local voice loop.

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
  -> temporary team-owned demo trunk; later user-owned trunk
  -> judge's phone
```

The deliberately excessive Pipecat + LiveKit + Asterisk path stays only if it produces evidence. PyVoIP is a fast direct SIP/RTP laboratory adapter, not the trusted judge-call transport. Moshi-MLX is a full-duplex experiment behind a feature flag, not the default engine.

## Mandatory scope

- published and verified Ginse bootstrap-plan action;
- Fredo Codex plugin and skill;
- one-prompt discovery, bootstrap, doctor and first call on the reference Mac;
- automatic disposable demo-credential provisioning with bounded telecom access;
- local CLI and durable daemon state;
- local STT, LLM and generic TTS;
- preview and explicit one-use confirmation before dialing;
- verified outbound SIP identity;
- one active outbound call at a time;
- bidirectional audio, interruption, hangup and cancellation;
- result returned to the originating Codex task;
- second call without downloading models or runtime dependencies;
- public, immutable Git source release plus manifests that include or pin every required non-secret artifact; credentials are explicitly excluded.

## Stretch scope

- Moshi-MLX full-duplex mode;
- consented voice cloning;
- Android Bluetooth, SIM gateway or inbound calls;
- Linux/NVIDIA inference;
- multi-user or multi-call operation;
- generalized installation across arbitrary Macs;
- bring-your-own telephony key and per-install carrier ownership;
- dashboard, recordings, air-gap bundles and automatic rollback.

## Measurable exit gates

### G0 — Ginse entry

- The team-owned Fredo provider is reachable over public HTTPS independently of the user's Mac and passes its authentication, schema and idempotency tests.
- The Fredo manifest passes Ginse verification and the listing is published.
- A fresh Codex task can invoke the documented copyable prompt and receive a schema-valid `BootstrapPlan`.
- Replaying the same Ginse idempotency key returns the same plan and performs no duplicate side effect.
- The plan pins an immutable Git commit and manifest digest; it contains no arbitrary shell supplied by the request.
- A captured provider request proves that no phone number, call intent, audio or transcript reached Ginse.
- The plan carries only an install-bound encrypted envelope; the raw subcredential, disposable team key and long-lived master key are absent from Git, Ginse responses and logs.

### G1 — First bootstrap

- On the clean-machine baseline above, one prompt makes Codex discover, install, provision, diagnose and invoke Fredo without the judge manually opening or typing in a shell, changing source, configuring files or pasting secrets. Codex may execute the approved commands.
- The user sees the downloads, disk cost and permissions before the named Codex download/local-execution approval.
- Every downloaded artifact records source, immutable version, expected size, license and checksum.
- An interrupted artifact download resumes instead of restarting from zero.
- Cold bootstrap completes in at most 30 minutes on the reference network and records elapsed time plus transferred bytes.
- `fredo doctor --json` reports every mandatory subsystem healthy.
- The original bootstrap task invokes the installed CLI after `doctor` and reaches call confirmation without a second typed prompt.
- If bootstrap fails, Codex reports an actionable cause and the same task can resume from the last verified step.
- A later fresh Codex task loads the installed Fredo plugin without manual configuration edits; this verification is not a prerequisite for the first call.
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
- Demo access proves carrier- or gateway-side spend, rate, concurrency and destination controls that remain effective even if the local Fredo process is bypassed, and it can be revoked centrally.

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

### G6 — Publishable release

- The tested source is available at a public Git commit SHA and immutable release tag.
- The release publishes the Codex plugin, skill, marketplace metadata, Ginse manifest, provider source and deployment manifests. External runtimes and models are pinned by immutable URL, digest, byte size and license. Credentials and other secrets are excluded.
- The release record binds the Git commit SHA, every release-asset SHA-256, the provider OCI image digest, the Ginse app ID and immutable version, and the Ginse manifest digest.
- A Mac matching the clean-machine baseline reaches a successful policy-controlled real call from the single documented prompt with no manual configuration and no second typed prompt.
- Cold bootstrap is actionable and resumable after an induced failure; the next warm run downloads zero artifact bytes.
- The exact tested release can be published on Git and Ginse without local-only files, uncommitted changes or undocumented operator steps.
- Demo credentials expire or are revoked and rotated after the judging window; evidence contains no raw secret.

## Evidence bundle

The goal cannot be marked complete without:

- [ ] Ginse listing URL, immutable version and successful verification output;
- [ ] redacted Ginse request proving the bootstrap-only data boundary;
- [ ] reference-machine inventory;
- [ ] pinned artifact manifest with checksums and licenses;
- [ ] public Git commit SHA, immutable tag, release-asset SHA-256 values, provider OCI digest, and matching Ginse app ID/version plus manifest digest;
- [ ] cold, resumed and warm bootstrap logs;
- [ ] clean-Mac one-prompt recording with no manual shell use, key paste or second typed prompt;
- [ ] redacted demo-credential policy showing expiry, revocation, spend, rate, concurrency and destination limits;
- [ ] successful `doctor --json` and `doctor --offline --json` outputs;
- [ ] network proof showing zero hosted AI inference during the call;
- [ ] latency report for at least 20 turns;
- [ ] confirmation rejection with zero SIP attempts;
- [ ] redacted SIP trace or carrier detail proving the real call;
- [ ] SQLite call-event journal and crash-recovery proof;
- [ ] cancellation and idempotency proofs;
- [ ] structured result returned in Codex;
- [ ] second-call zero-download proof;
- [ ] one uncut demo recording from Ginse discovery, through bootstrap and the confirmed first call in the same task, to the Codex result;
- [ ] post-demo credential revocation and rotation proof.

## Completion sentence

Fredo passes when one copyable prompt on a clean reference Mac discovers Fredo through Ginse, installs and verifies the pinned local runtime, provisions bounded temporary telecom access, calls the judge's real phone from the same Codex task with local AI, and returns the answer with publishable Git and Ginse evidence above.
