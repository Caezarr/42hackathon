# Security and abuse boundaries

[`GOAL.md`](GOAL.md) is the active acceptance contract. This file describes the
`hosted-voice-mvp` controls and their current limitations.

## Data boundaries

| Party | Receives |
| --- | --- |
| Codex/Fredo on team Mac | destination, purpose, configuration, transcript/result |
| Ginse/provider | platform, profile, idempotency/auth metadata only |
| Twilio | destination, verified caller identity, call metadata and media stream |
| Deepgram Voice Agent | live audio, agent prompt/purpose, transcript context and responses |
| Public tunnel | encrypted callback/media transit to the team Mac |

This profile is not private local inference. Do not claim that raw call audio or
transcripts stay on the Mac.

## Secrets

- Never commit or print Deepgram API keys, Twilio Auth Tokens, endpoint secrets,
  Ginse signing material or real phone numbers.
- `fredo configure` stores team demo values in ignored `.env` mode `0600` and
  reports only the path/status.
- The isolated Ginse container maps only explicit provider variables from an
  ignored `.env.ginse` or deployment secret manager. It never loads the voice
  `.env`, Deepgram key or Twilio credentials.
- Deployment values never enter Docker image layers or committed Compose data.
- The Deepgram key shared for the hackathon must be rotated afterward.
- Diagnostics expose booleans/counts only, never credential values.

## Dial controls implemented now

- strict canonical E.164 parser;
- French mobile +336/+337 eligibility;
- exact local allowlist, default deny;
- explicit consent and confirmation fields;
- required `hosted-voice-mvp` Ginse session shape and expiry before preview or
  network setup;
- native macOS preview containing destination, caller ID, purpose, disclosure,
  duration and policy;
- one active call and a 180-second Twilio/local duration guard;
- fixed configured caller ID; no caller-ID input in the API;
- endpoint bearer required for `/v1/calls`;
- required idempotency key with same-request replay and divergent conflict;
- Twilio signature verification on status callbacks and WebSocket handshake;
- recording never requested;
- one Deepgram function, `finish_demo`, limited to recording the answer and a
  factual summary, then ending the current call;
- mock transport rejected by the judged `fredo demo` command.

## Known limitations

- Call state/idempotency are in-process. A crash immediately after Twilio accepts
  a call can leave an uncertain result. Fredo must not automatically redial.
- The local Ginse handoff check validates shape/profile/expiry, not provenance
  or cryptographic authorization. Provenance evidence comes from the verified
  runner's terminal run and receipt.
- Twilio and Deepgram master credentials currently run on the team Mac/server,
  not behind an install-bound dial broker.
- Cloudflare Quick Tunnel is a development transport without a production SLA.
- `osascript` confirmation is not yet a signed/notarized helper attestation.
- Server-side spend/rate/revocation and malicious-client bypass controls are
  post-hackathon hardening.

These limitations forbid a production-ready, crash-safe-at-most-once or
independently self-hosted claim.

## Ginse boundary

The action input is exactly:

```json
{"platform":"macos-arm64","profile":"hosted-voice-mvp"}
```

Unknown fields fail. Output is compatibility/session data only. It must contain
no URL, command, phone number, purpose, caller identity, credential, audio,
transcript or call result.

The provider verifies Ginse's Ed25519 bearer and durably claims
`Idempotency-Key` in SQLite. Exact retries replay the stored operation/output;
changed input under the same key conflicts. Provider-auth material is not a
carrier credential and grants no dial authority.

## Remote speech is untrusted

Phone audio cannot:

- initiate or authorize another call;
- modify destination, caller identity, allowlist, duration or policy;
- invoke a shell, Codex/MCP tool, installer or network action;
- read secrets, local files, other transcripts or system prompts.

The only allowed side effect is storing the current demo answer/summary and
terminating the already-authorized current call.

## Prohibited behavior

- caller-ID spoofing or anonymous presentation;
- emergency, premium-rate, short-code, unsupported-country, bulk or unattended
  dialing;
- contact scraping or non-consensual calls;
- recordings or public transcripts;
- exposing master keys to judges or Ginse;
- weakening confirmation/policy for a demo;
- claiming a mock or HTTP 202 response proves a real call.

Report vulnerabilities through GitHub private security advisories. Never put a
credential, real number, recording or unredacted trace in a public issue.
