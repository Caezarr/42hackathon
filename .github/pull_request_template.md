## What changed

## Why

## Call-safety surface touched

- [ ] Policy / consent checks
- [ ] Telephony (Twilio) or media bridge
- [ ] Voice agent (Deepgram) configuration
- [ ] Codex plugin or Ginse schemas
- [ ] None of the above

## Test evidence

- [ ] `uv run ruff check src tests` and `uv run pytest` pass
- [ ] Real PSTN call tried (say with which number type and what was verified), or not applicable

## Privacy impact

Does this send anything new (phone number, transcript, audio) to Twilio, Deepgram or Ginse? If yes, what and why.

## Rollback
