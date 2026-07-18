# Fredo stack candidates

Status: research snapshot recorded on 2026-07-18. Candidates are not implementation claims.

## Reference environment

Observed locally:

| Item | Value |
| --- | --- |
| Architecture | `arm64` |
| Chip | Apple M4 Pro |
| Memory | 24 GB |
| macOS | 26.5 |
| Codex CLI | 0.144.1 |
| Python | 3.14.3 |
| Rust | 1.94.1 |
| Docker daemon | not running during the audit |

The bootstrap must create its own supported Python environment and treat the container runtime as a doctor check, not an assumption.

## Codex surfaces

The current Codex manual and installed CLI establish:

- plugins can package skills, MCP configuration and hooks;
- Git-backed plugin marketplaces are supported;
- `codex plugin add` installs from a configured marketplace;
- local Codex clients support STDIO MCP servers;
- Codex CLI supports `--oss` with Ollama or LM Studio as local providers.

Fredo therefore uses:

1. plugin + skill for distribution and workflow;
2. local CLI as the canonical implementation contract;
3. optional STDIO MCP for typed calls;
4. Codex `--oss` for the zero-hosted-inference demo.

References:

- [Build plugins](https://learn.chatgpt.com/docs/build-plugins)
- [Build skills](https://learn.chatgpt.com/docs/build-skills)
- [MCP](https://learn.chatgpt.com/docs/extend/mcp)

## Ginse

The Ginse provider contract is one fixed-price HTTPS action. The provider keeps hosting its endpoint and must implement authentication, schema validation, durable idempotency and a stable operation ID.

It cannot directly install on a user's Mac. Fredo maps the action to a deterministic `BootstrapPlan`, then Codex performs the authorized local install.

References:

- [Ginse agent instructions](https://app.ginse.ai/agent.md)
- [Ginse v3 contract](https://app.ginse.ai/contracts/v3/README.md)

## PyVoIP

Repository: [tayler6000/pyVoIP](https://github.com/tayler6000/pyVoIP)

Pinned research revision: `2a693346cb493bc3e7a8c4c820a7c88af6deeb92` (`v1.6.9`).

Observed from the upstream README:

- pure Python SIP/RTP library;
- PCMA and PCMU codecs;
- telephone-event support;
- no bundled sound layer;
- documented G.711 audio is 8 kHz mono.

License: GPL-3.0. Keep it isolated as a lab dependency until redistribution implications are reviewed.

Decision: useful for SIP/RTP diagnostics and a fast controlled spike; not the trusted judge-call transport.

## Moshi

Repository: [kyutai-labs/moshi](https://github.com/kyutai-labs/moshi)

Pinned research revision: `e6a55d2722a65870ef52a6c9f6ecfc0e90f38362`.

Observed from the upstream README:

- full-duplex spoken dialogue with two audio streams;
- 7B temporal transformer and Mimi streaming codec;
- MLX q4/q8 variants for Mac;
- Python 3.12 recommended for `moshi_mlx`;
- bare CLI clients lack echo cancellation and lag compensation;
- model weights use CC-BY-4.0.

Decision: benchmark `moshi_mlx` q4 on the M4 Pro as a feature-flagged wow path. The reliable modular STT -> LLM -> TTS path remains mandatory.

## “Miro 2.5”

No primary repository matching the spoken name “Miro 2.5” was found in the targeted search. It may refer to Moshi or another local model. Do not add it to the runtime manifest until the exact project and license are confirmed.

## Telecom stack

Candidate roles:

| Component | Role | Critical-path rule |
| --- | --- | --- |
| Pipecat | conversation graph and interruption | keep if local voice loop passes |
| LiveKit | media room and supervision | removable if it blocks the call |
| LiveKit SIP | bridge room media to SIP | direct-to-carrier fallback |
| Asterisk | carrier behavior, DTMF, CDR, future hardware | removable if direct SIP is more reliable |
| PyVoIP | diagnostic SIP/RTP path | never the only judged path |

The winner is the smallest combination that completes two consecutive controlled PSTN calls and meets [`GOAL.md`](../GOAL.md).
