# AGENTS.md

## Mission

Build a distributable, local-first phone appliance for Codex. Every installation owns its compute, models, data, credentials, phone transport, policy, and costs.

## Hard constraints

- Do not introduce a shared call backend, central broker, or mandatory hosted AI provider.
- Do not implement caller-ID spoofing, anonymous dialing, emergency or premium-rate dialing, contact scraping, or mass calling.
- Present only SIM-owned or carrier-verified caller identities.
- Keep browser, SIP, GSM-to-SIP, and Android Bluetooth transports behind one interface.
- Keep compute selection independent from transport selection.
- Preserve a fully local MCP path that does not require Ginse.
- Treat Ginse as optional and per installation; never imply that it hosts code or can call arbitrary localhost instances.
- Mark target behavior as target behavior until it is proven by tests.

## Architecture

- Control plane: Agent Call
- Codex boundary: local MCP
- Voice pipeline: Pipecat
- Media: self-hosted LiveKit and LiveKit SIP
- Initial inference gateway: LocalAI
- Scaled NVIDIA inference: vLLM, Speaches/faster-whisper, Kokoro
- Optional cellular bridge: Asterisk `chan_mobile` on Linux
- Packaging: Compose plus native acceleration where containers cannot access it cleanly

## Workflow

1. Read `README.md` and the relevant file in `docs/`.
2. Keep changes inside the selected milestone in `docs/HACKATHON-PLAN.md`.
3. Pin every external image, repository, model, and artifact by immutable digest or commit.
4. Add tests for any implemented command, API contract, or safety gate.
5. Run formatting, tests, smoke checks, and `git diff --check` before publishing.

## Documentation rules

- Separate implemented, experimental, and planned behavior.
- Document the user's ownership boundary explicitly.
- State when internet or the cellular network remains physically required.
- Never call a transport or feature “offline” if it still needs PSTN/SIP connectivity; only inference may be offline.
