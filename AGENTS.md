# AGENTS.md

## Mission

Build Fredo, a generic local phone capability for Codex. Every installation owns its compute, models, data, credentials, phone transport, policy, and costs.

## Hard constraints

- Do not introduce a shared call backend, central broker, or mandatory hosted AI provider.
- Do not implement caller-ID spoofing, anonymous dialing, emergency or premium-rate dialing, contact scraping, or mass calling.
- Present only SIM-owned or carrier-verified caller identities.
- Keep every phone transport behind one interface.
- Keep compute selection independent from transport selection.
- Preserve a fully local CLI path; MCP is an optional thin adapter.
- Treat Ginse as the mandatory discovery/bootstrap entry point and keep it outside the live-call data path.
- Never send phone numbers, call intents, credentials, audio, transcripts, or results to Ginse.
- Mark target behavior as target behavior until it is proven by tests.

## Architecture

- Control plane: local call orchestration
- Codex boundary: plugin + skill + canonical local CLI; optional STDIO MCP
- Voice pipeline: Pipecat
- Media: self-hosted LiveKit and LiveKit SIP
- State: SQLite WAL for the hackathon profile
- Inference: benchmark-selected native Metal/MLX adapters
- Telecom: Asterisk and a verified SIP trunk, with evidence-backed bypasses
- Packaging: Fredo Codex plugin plus native runtime and local Compose services

## Workflow

1. Read `README.md` and the relevant file in `docs/`.
2. Keep changes inside the selected milestone in `ROADMAP.md`.
3. Pin every external image, repository, model, and artifact by immutable digest or commit.
4. Add tests for any implemented command, API contract, or safety gate.
5. Run formatting, tests, smoke checks, and `git diff --check` before publishing.

## Documentation rules

- Separate implemented, experimental, and planned behavior.
- Document the user's ownership boundary explicitly.
- State when internet or the cellular network remains physically required.
- Never call a transport or feature “offline” if it still needs PSTN/SIP connectivity; only inference may be offline.
- Every completed milestone must link to its measurable evidence from `GOAL.md`.
