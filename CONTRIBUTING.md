# Contributing

Read [README.md](README.md), [GOAL.md](GOAL.md), [ROADMAP.md](ROADMAP.md),
[AGENTS.md](AGENTS.md) and [SECURITY.md](SECURITY.md) first.

## Principles

- Prefer one verified end-to-end call path over extra providers or UI.
- Keep Ginse mandatory but free of destination, intent and call content.
- Keep native confirmation, exact allowlisting, verified caller ID and the
  180-second cap.
- Call the active profile `hosted-voice-mvp`; Deepgram performs hosted voice
  processing.
- Never commit `.env`, credentials, real phone numbers, transcripts or recordings.
- Pin dependencies/upstreams and preserve third-party notices.
- Label mocked, offline-tested, live-qualified and planned behavior separately.

## Verify a change

```bash
uv sync --frozen --extra dev
uv run ruff check src tests
uv run pytest
uv build
git diff --check
```

For live tests, use only an exact pre-enrolled consenting fixture. Record the
Git SHA, models, caller ID hint, result and timings without storing the full
number, audio or credentials.

## Pull requests

- Explain the product outcome and affected Goal gate.
- State what was tested offline and what was tested against real services.
- Include failure/abuse cases and remaining blockers.
- Do not publish Git/Ginse releases whose bytes or configuration differ from
  the qualified candidate.
