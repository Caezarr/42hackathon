# Fredo delivery roadmap

Status: implementation order for [`GOAL.md`](GOAL.md) `0.4-draft` and the
`hosted-voice-mvp` profile.

The order is evidence-first: make one guarded real call work, put Ginse in the
actual path, then package and harden it. The all-local voice stack remains a
post-hackathon profile.

## Current snapshot

| Workstream | State |
| --- | --- |
| CLI/package/configuration | implemented |
| French Deepgram agent + Twilio Media Stream | implemented, offline-tested |
| macOS confirmation + policy checks | implemented, offline-tested |
| quick tunnel | implemented, not live-qualified |
| Codex plugin/marketplace | implemented, locally validated |
| Ginse provider core + CLI receipt handoff | implemented, offline-tested |
| public Ginse version | missing |
| live Twilio call | blocked on team Twilio credentials and number |
| clean judge rehearsal | missing |

## P0 — Runtime vertical slice

Deliver:

- Python 3.12 package and `fredo` CLI;
- `configure`, `doctor`, `demo`, `call`, `serve`;
- exact +336/+337 allowlist and explicit consent/confirmation checks;
- native macOS preview;
- Twilio outbound call with fixed verified caller ID;
- local μ-law 8 kHz bridge to Deepgram Voice Agent;
- French Flux Multilingual + Aura-2 Agathe configuration;
- tool-limited structured `finish_demo` result;
- automatic Cloudflare quick tunnel and teardown;
- Twilio signature validation, duration cap and concurrency one.

Exit:

- offline suite and lint pass;
- wheel/sdist build;
- mock mode can never be reported as a real call;
- secrets absent from source, diagnostics and results.

Status: **implemented; live qualification pending**.

## P1 — Ginse action in the real path

Deliver exactly one action: `Prepare Fredo demo` at EUR 0.42 test balance.

- strict input: `macos-arm64` + `hosted-voice-mvp`;
- strict data-only output: compatibility, opaque session ID, expiry;
- required, expiring receipt handoff into the local Fredo CLI;
- no destination, intent, caller ID, secret, URL, command or call result;
- Ed25519 bearer validation;
- SQLite transaction before output generation;
- stable provider operation ID;
- exact replay and divergent-replay rejection;
- schema-valid `/.well-known/ginse.json`;
- container/persistent HTTPS deployment.

Exit:

- all provider tests pass, including 20 concurrent duplicates;
- public manifest passes `ginse apps verify`;
- immutable staging version can be invoked from the Fredo judge prompt;
- captured wire data proves call fields are absent.

Status: **implemented and offline-tested; public deployment/verification pending**.

## P2 — First controlled real call

Prerequisites owned by the team:

- paid/non-trial Twilio account or accepted trial limitation;
- verified caller number with France geographic permissions;
- exact consenting fixture phone in the allowlist;
- Deepgram key provisioned through `fredo configure` or deployment secrets;
- stable Wi-Fi and Mac sleep disabled for the run.

Qualification order:

1. `fredo doctor --json` all green;
2. reject native dialog and prove zero Twilio call;
3. connect tunnel and validate signed Twilio status callback;
4. make one call to the team fixture;
5. confirm French greeting/disclosure, user response, barge-in and result;
6. confirm hard hangup and no Twilio recording;
7. repeat five times and retain timings/errors.

Exit: `GOAL.md` G2 and G3 pass against one commit.

Status: **blocked on Twilio credentials/number; code path ready for test**.

## P3 — Judge one-prompt rehearsal

Deliver:

- pinned public Git commit;
- repo-scoped marketplace and install instructions;
- same-task direct CLI fallback after plugin installation;
- preprovisioned team secrets and exact judge allowlist;
- copyable prompt naming Ginse and the public repository;
- operator runbook and immediate kill procedure.

Rehearse from a clean checkout on the team Mac:

```text
one prompt -> Ginse preparation receipt -> doctor -> native confirmation
           -> real call -> structured answer in same Codex task
```

Exit:

- warm prompt-to-ring under 90 seconds;
- no terminal typing or credential paste by the judge;
- a later fresh task discovers the plugin;
- three complete unassisted rehearsals before judging.

## P4 — Publish unchanged

- Tag the exact accepted commit.
- Build the same wheel/container used in rehearsal.
- Publish the immutable Ginse version.
- Run one production smoke call.
- Link Git commit, artifact digest, Ginse version and evidence summary.

Any code, configuration, caller identity, prompt, model or manifest change after
acceptance returns to P2.

## P5 — Immediate post-hackathon hardening

1. Move Twilio and Deepgram master credentials behind a dial broker.
2. Issue short-lived install-bound capabilities through the Ginse session.
3. Persist `DIAL_COMMITTED` and provider SID before returning; reconcile unknown
   outcomes without blind redial.
4. Replace the quick tunnel with a stable authenticated media endpoint.
5. Bundle Python/uv/tunnel for a clean Mac and sign/notarize the helper.
6. Add BYOK, then independent self-hosted deployments.

## P6 — Optional all-local voice profile

Only after the working hackathon release:

- benchmark local streaming STT, dialogue and French TTS on Apple Silicon;
- qualify barge-in and p95 latency against the hosted profile;
- keep audio/transcripts local and document model licenses;
- promote `local-voice` only if it passes a separate 100-turn benchmark and five
  real calls.

Moshi, Pipecat, LiveKit, Asterisk, PyVoIP and voice cloning remain experiments,
not dependencies of the judged path.
