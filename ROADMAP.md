# Fredo product roadmap

This roadmap orders work by proof, not architectural prestige. The current goal is defined in [`GOAL.md`](GOAL.md).

## Product direction

Fredo is a generic local phone capability for Codex.

The product enters through Ginse, installs on the user's machine, and then performs calls locally through the user's own verified telecom transport. The hackathon reference is one Apple M4 Pro Mac with 24 GB RAM and one outbound SIP trunk.

The intentionally excessive target is:

```text
Ginse -> Codex plugin -> Fredo CLI/daemon -> SQLite -> Pipecat
      -> native local voice models -> LiveKit -> Asterisk -> SIP -> PSTN
```

Every layer must earn its place with a measured improvement or operational necessity.

## Delivery rules

- Ginse is present in the first vertical slice, not added at the end.
- The CLI/domain contract is canonical; the skill and optional MCP adapter remain thin.
- Inference runs natively on Apple Silicon when containers would lose Metal/MLX performance.
- Docker Compose packages the mandatory public Ginse provider and may package media, telecom and observability.
- The public Ginse provider and an optional public telecom edge are separate deployment roles, even if the team colocates them.
- One proven call path beats several half-working transports.
- Each phase ends with stored evidence before the next phase starts.
- Every implementation decision or replaced assumption gets a short ADR.

## P0 — Contract, machine and carrier

### Deliver

- Fredo name, product boundary and [`GOAL.md`](GOAL.md).
- JSON schemas for `BootstrapPlan`, call preview, confirmation and terminal result.
- Inventory of the M4 Pro reference Mac.
- Working SIP account, verified caller number and controlled destination.
- Chosen team-controlled public HTTPS Docker host and DNS name for the Fredo Ginse provider.
- Repository marketplace shape for an installable Fredo Codex plugin.
- Ginse action contract: `platform profile -> BootstrapPlan`.

### Exit evidence

- Schemas validate one safe example and reject malformed input.
- SIP credentials register using a throwaway diagnostic client.
- A human-originated test call reaches the controlled phone from the verified number.
- The exact Mac, available disk, Python strategy and container runtime status are recorded.

### Cut line

Do not tune models before the carrier account and Ginse action shape are proven.

## P1 — Ginse-to-local vertical slice

### Deliver

- Minimal public Fredo Ginse provider with one fixed-price `/run` action.
- Ed25519 bearer verification and durable Ginse idempotency.
- Schema-valid `BootstrapPlan` pinned to a Fredo commit and manifest digest.
- Minimal `.codex-plugin/plugin.json`, Fredo skill and repo marketplace entry.
- `fredo bootstrap plan`, `fredo bootstrap apply` and `fredo doctor --json` stubs.

### Exit evidence

From a fresh Codex task:

1. invoke the published Ginse action;
2. receive and validate the plan;
3. install the Fredo plugin from the pinned repository revision;
4. run the local bootstrap stub after approval;
5. see a structured doctor result.

No phone number or call data may appear in the Ginse request or response.

### Cut line

The first implementation may support only `mac-m4pro-24gb` and the team machine. General installers are explicitly deferred.

## P2 — Voice-engine shootout

### Deliver

A repeatable local benchmark harness for:

- modular path: streaming STT -> compact local LLM -> generic local TTS;
- Moshi-MLX q4 full-duplex experiment;
- resampling between PSTN 8 kHz G.711 audio and each engine's native sample rate.

Reference candidates:

- STT: whisper.cpp/Metal or an equivalent MLX implementation;
- LLM: a compact model served by MLX, Ollama or LM Studio;
- TTS: Kokoro with Piper as the reliability fallback;
- full duplex: [Moshi MLX](https://github.com/kyutai-labs/moshi), behind a feature flag.

The spoken candidate “Miro 2.5” was not found in the primary repository search. It is treated as an unresolved name, possibly Moshi, and must not become a dependency until the exact project is confirmed.

### Exit evidence

- 20 measured turns for each viable path.
- Load time, peak memory, STT latency, first token, first audio and interruption latency recorded.
- One engine selected as `reference`; every other engine becomes optional.
- Reference path meets the latency and memory gates in [`GOAL.md`](GOAL.md).

### Cut line

Moshi leaves the critical path immediately if it exceeds memory or latency limits. Voice cloning is not evaluated until a generic TTS call succeeds.

## P3 — Durable Fredo core

### Deliver

- Native `fredo` CLI and `fredod` daemon communicating over a Unix socket.
- SQLite WAL database and append-only call event journal.
- State machine:

```text
draft -> awaiting_confirmation -> ready -> dialing -> ringing
      -> connected -> completed | failed | cancelled
```

- One-use confirmation bound to destination, intent, caller identity and duration.
- Idempotent prepare/start/cancel/result operations.
- Redacted structured logs.

### Exit evidence

- A pending job survives daemon restart.
- Rejecting or expiring confirmation produces zero transport attempts.
- Reusing an idempotency key cannot create a duplicate call.
- Blocked-number fixtures fail before the transport adapter is called.
- CLI commands return schema-valid JSON.

## P4 — The absurd phone sandwich

### Hero path

```text
Pipecat
  <-> LiveKit room
  <-> LiveKit SIP
  <-> Asterisk PJSIP
  <-> verified carrier trunk
  <-> real phone
```

Roles stay explicit:

- Pipecat: dialogue graph, VAD, interruption and voice-engine adapters.
- LiveKit: realtime media room and local supervision.
- Asterisk: carrier quirks, codecs, DTMF, call detail and future SIM/Bluetooth transports.
- The Mac: Fredo state and native inference.

[PyVoIP](https://github.com/tayler6000/pyVoIP) is a diagnostic adapter only. Its documented PCMA/PCMU 8 kHz and telephone-event support make it useful for a quick SIP/RTP spike, but it does not replace the judged transport.

### Fallback ladder

1. LiveKit SIP directly to the carrier trunk.
2. Pipecat through Asterisk without LiveKit supervision.
3. PyVoIP only as a redacted lab diagnostic, never as an excuse to skip the real call.

A public telecom edge and WireGuard are introduced only if the carrier/NAT path requires them. The first attempt runs locally on the Mac and its Docker runtime.

### Exit evidence

- Two consecutive calls reach a controlled real phone.
- Warm ring time is at most 20 seconds after confirmation.
- Bidirectional audio remains usable for 90 seconds.
- DTMF, answer, interruption and hangup events share one `call_id`.
- Terminal result persists within five seconds of hangup.

### Cut line

Never debug two broken telecom paths at once. Promote the first path that completes two consecutive calls; disable the rest behind feature flags.

## P5 — Codex owns the experience

### Deliver

- Fredo skill covering prepare, preview, confirm, start, status, cancel and result.
- Natural-language call flow that stays inside one Codex task after the plugin is loaded.
- Local CLI invocation as the mandatory adapter.
- Optional STDIO MCP tools over the same domain service if they reduce friction.
- Hackathon Codex CLI profile using `--oss` with a local provider.

### Exit evidence

- No manual shell command is typed during the judged flow.
- Codex displays the resolved destination and intent before confirmation.
- Codex can cancel before answer and retrieve the final result after hangup.
- Raw audio never enters Codex.
- Network capture shows no hosted AI inference during the call.

## P6 — Publish and rehearse

### Deliver

- Cold bootstrap implementation for the pinned Mac profile.
- Resumable downloads and warm zero-download reuse.
- Public Ginse manifest served unchanged and verified.
- Published Ginse listing `Fredo — 42hackathon`.
- Operator runbook, troubleshooting guide and evidence bundle.
- A single uncut demo script starting from Ginse discovery.

### Exit evidence

- Every mandatory gate in [`GOAL.md`](GOAL.md) passes twice.
- A bootstrap task completes Ginse -> install -> doctor without source edits.
- A newly started Codex task loads the installed plugin and completes the call flow.
- The first real call and a second warm call both complete.
- The team can recover from failed model, media and trunk health checks using the documented fallback ladder.

## Hackathon cut line

### Never cut

- Ginse discovery and verified bootstrap-plan action;
- local installation on the reference Mac;
- local voice inference;
- explicit confirmation;
- verified caller identity;
- real judge phone call;
- bidirectional audio;
- structured result in Codex.

### Cut in this order

1. voice cloning;
2. Moshi mode;
3. dashboard and custom UI;
4. PyVoIP outside diagnostics;
5. Asterisk if LiveKit SIP works directly;
6. LiveKit supervision if Asterisk works directly;
7. public telecom edge if local SIP works; never cut the public Ginse provider;
8. multiple models, transports, languages or machines;
9. rollback, signed releases and air-gap bundles.

## After the hackathon

### V0.2 — Installable by another Mac user

- tested clean-machine install;
- immutable runtime/model manifest;
- compatibility matrix for Apple Silicon memory tiers;
- upgrade and rollback;
- local diagnostics export with automatic redaction.

### V0.3 — More transports

- GSM/LTE-to-SIP gateway;
- Android Bluetooth through Asterisk;
- inbound calls;
- optional Linux edge appliance.

### V1 — Personal calling platform

- stable public Fredo plugin distribution;
- multiple local profiles and languages;
- policy packs and contact vault;
- optional consented voice cloning;
- local observability and evaluation suite;
- no central Fredo call execution.
