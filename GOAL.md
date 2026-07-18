# GOAL.md — Fredo hackathon MVP

Version: `0.4-draft`
Active profile: `hosted-voice-mvp`
Target: one real, consented jury call from Codex, with Ginse in the loop.

## 1. Outcome

Build **Fredo**, a generic guarded phone capability for Codex.

For the hackathon, a judge gives Codex one natural-language request containing
an exact consenting French mobile number and a short purpose. Fredo must:

1. invoke Fredo's single paid test action through Ginse without sending Ginse
   the destination or call intent;
2. install or verify the pinned Fredo checkout and runtime;
3. run `fredo doctor --json`;
4. show a Fredo-owned macOS call preview and require a human click;
5. make the real phone ring from the team's verified caller identity;
6. disclose immediately that Fredo is an automated synthetic voice and that
   the demo is not recorded;
7. ask whether the demonstration works, end the current call, and return a
   faithful structured result to the same Codex task.

The project name is **Fredo**. It is not AgentCall.

## 2. Honest architecture boundary

The active hackathon profile intentionally favors a working call over the
longer all-local research path:

```text
Codex + Fredo CLI on team Mac
  -> Ginse: one fixed-price data-only demo preparation action
  -> native macOS confirmation
  -> Twilio: verified caller identity and PSTN
  -> local Twilio Media Stream bridge
  -> Deepgram Voice Agent: hosted STT + LLM + TTS
  -> consenting judge phone
```

- Control, exact allowlisting, confirmation, tunnel lifecycle and current-call
  state run on the team Mac.
- Live audio, prompt and conversation context are processed by Deepgram.
- Destination and intent are necessarily sent to Twilio and Deepgram as part of
  the call, but never to Ginse.
- Ginse provider output is untrusted data. It may return a typed demo session
  result; it never authorizes a shell command, download URL or tool call.
- No caller-ID spoofing is supported. Fredo uses one verified Twilio number.
- The Deepgram and Twilio master credentials are team-demo secrets. They are
  supplied through an ignored mode-0600 `.env` or deployment secret store,
  never Git, Ginse, plugin files, logs or structured results.

The future `local-voice` profile may replace Deepgram with local STT, dialogue
and TTS after the hackathon. It is not part of this MVP's pass criteria.

## 3. Current truth

As of 2026-07-18:

| Capability | State |
| --- | --- |
| Python package and `fredo` CLI | implemented |
| French Deepgram Voice Agent configuration | implemented, not live-qualified |
| Twilio outbound call + Media Stream bridge | implemented, not live-qualified |
| Exact +336/+337 allowlist, consent and confirmation checks | implemented |
| macOS native preview | implemented |
| 180-second cap and one-call concurrency | implemented |
| Twilio callback signature verification | implemented |
| API idempotency against concurrent duplicate requests | implemented in-process |
| Automatic Cloudflare quick tunnel | implemented, not live-qualified |
| Codex plugin and repo marketplace | implemented |
| Unit test suite and package build | implemented |
| Ginse provider, manifest, durable replay and CLI handoff | implemented, offline-tested |
| Published Ginse listing | missing |
| Real PSTN acceptance call | blocked by missing Twilio credentials/number |
| Crash-safe durable at-most-once dialing | not implemented |
| Clean unknown-Mac bootstrap with no preinstalled `uv`/tunnel | not implemented |

Nothing in this table is evidence of a real phone call until a controlled live
test passes Section 7.

## 4. Judge experience

The target request is:

> Use Ginse to prepare Fredo from `github.com/Caezarr/42hackathon`, then call
> `<PHONE_E164>`. This number belongs to a consenting judge. Introduce Fredo in
> French, disclose immediately that you are an automated synthetic voice, ask
> whether the demo works, then return the answer and a concise factual summary here.

One prompt means one message typed by the judge. The flow may display:

- one Codex approval for declared downloads/local writes;
- one OAuth approval if the judge's Ginse agent connection is not ready;
- one Fredo native call-confirmation dialog.

The judge must not paste Deepgram/Twilio credentials, edit `.env`, choose a
model, start a tunnel, or type a second prompt. Team credentials and the exact
judge allowlist are provisioned before judging.

Codex loads a newly installed plugin only in a new task. Therefore the first
task may invoke the newly installed `fredo` executable directly. A fresh task
verifies plugin discovery afterward.

## 5. Product contract

### 5.1 Command surface

```text
fredo configure
fredo doctor --json
fredo demo --ginse-profile <profile> --ginse-demo-session-id <id> \
  --ginse-expires-at <rfc3339> --to <E164> --intent <text>
fredo call <same Ginse receipt flags> --to <E164> --intent <text> [--server <url>]
fredo serve [--ginse-only]
```

`fredo demo` is the judged one-shot path: preflight, native confirmation,
automatic tunnel, local service, real call, result, teardown.

The three Ginse receipt arguments come from the successful fixed-price action.
Fredo rejects a missing, malformed, wrong-profile or expired handoff before the
native preview, tunnel and carrier request. This is structural flow linkage,
not cryptographic dial authorization.

The command refuses the `mock` provider. A successful process exit without a
carrier-backed terminal result is never presented as a successful real call.

### 5.2 Ginse action

Fredo publishes exactly one fixed-price action:

- display name: `Fredo — 42hackathon`;
- action: `Prepare Fredo demo`;
- price: EUR 0.42 of hackathon test balance;
- request: exact `platform=macos-arm64` and
  `profile=hosted-voice-mvp` only;
- response: typed compatibility flag, opaque demo session identifier and
  expiry; no URL, command, phone number, intent, credential or call result.

The provider must verify Ginse's Ed25519 bearer, claim `Idempotency-Key`
atomically in SQLite before producing an output, replay the exact stored result
for an identical retry, and reject divergent reuse.

### 5.3 Call policy

The hackathon profile is default-deny:

| Control | Required value |
| --- | --- |
| Eligible class | French mobile `+336` or `+337` |
| Authorization | exact E.164 entry in `FREDO_ALLOWED_NUMBERS` |
| Consent | explicit in the current human request |
| Confirmation | Fredo-owned native dialog; closing/rejecting means zero dial |
| Caller identity | one verified Twilio number; never arbitrary/spoofed |
| Concurrency | one active call |
| Duration | hard maximum 180 seconds |
| Recording | disabled |
| Voice disclosure | first substantive audio, target under five seconds |
| Remote tools | only `finish_demo` for result + current-call termination |
| Emergency/short/premium/other-country numbers | rejected before Twilio |

Phone audio cannot change the destination, start another call, invoke a shell,
read secrets, modify policy or widen the allowlist.

## 6. Required setup before judging

The team performs this once on the demo Mac:

```bash
git clone https://github.com/Caezarr/42hackathon.git
cd 42hackathon
./scripts/bootstrap.sh
uv run fredo configure
uv run fredo doctor --json
```

The interactive configuration stores secrets only in ignored `.env` with mode
`0600`. The Deepgram key shared during development must be rotated after the
hackathon. Twilio geographic permissions, caller number and the judge's exact
destination must be qualified before the live run.

The repository marketplace is added to Codex and Fredo installed before the
official judge prompt, or installed by the initial task and used directly via
CLI in that same task.

## 7. Measurable acceptance gates

### G0 — Build and static safety

- `uv sync --frozen --extra dev` succeeds on Python 3.12.
- `uv run ruff check src tests` passes.
- `uv run pytest` passes with no network or credentials.
- `uv build` produces an sdist and wheel.
- Git contains no Deepgram key, Twilio token, full judge number, `.env`,
  transcript or recording.

### G1 — Ginse is real, not decorative

- The public `/.well-known/ginse.json` passes `ginse apps verify`.
- The immutable app version is published at EUR 0.42.
- Missing/invalid bearer returns 401/403.
- Twenty simultaneous identical `/run` requests create one operation and one
  stored output; all replays return the same operation ID.
- Same idempotency key with changed input returns conflict.
- Captured Ginse input/output contains no destination, intent, caller identity,
  audio, transcript, secret or call result.
- Missing, malformed, wrong-profile or expired session fields stop the local
  flow before the preview, tunnel and Twilio.
- The Codex skill passes the exact typed session ID and expiry from the one
  successful Ginse run; it never synthesizes or substitutes them.

### G2 — No confirmation, no call

- Closing or rejecting the macOS dialog produces zero Twilio `Calls.create`.
- A non-allowlisted, malformed, non-French-mobile, emergency, short or
  premium-rate target produces zero Twilio `Calls.create`.
- Two concurrent distinct requests cause at most one carrier attempt.
- Twenty concurrent exact API replays with one idempotency key cause exactly
  one carrier attempt in a single process.
- Invalid Twilio callback and Media Stream signatures are rejected.

### G3 — Controlled real call

Run five calls to pre-enrolled consenting team/judge fixtures:

- five out of five phones ring from the expected verified caller number;
- synthetic-voice disclosure is audible within five seconds of connection;
- French speech is intelligible in both directions;
- the callee can interrupt Fredo and outbound buffered audio clears;
- Fredo asks whether the demo works and returns a faithful boolean, answer and
  concise factual summary;
- every call terminates voluntarily or at the 180-second hard cap;
- no Twilio recording resource is created;
- median answer-to-first-agent-audio latency is under 1.5 seconds, p95 under
  2.5 seconds on the qualified hackathon network.

### G4 — Judge path

From a clean checkout on the prepared team Mac:

- one natural-language prompt reaches the native preview without shell input;
- the judge only handles declared Codex/Ginse approvals and the Fredo call
  confirmation;
- the real phone rings and the result returns to the same task;
- a later fresh Codex task discovers the installed Fredo plugin;
- total time from prompt to ringing is under 90 seconds warm and under five
  minutes after a fresh checkout.

### G5 — Release honesty

- README, Goal, ADR, Git release and Ginse listing all call this profile
  `hosted-voice-mvp`.
- They state that Deepgram performs hosted STT/LLM/TTS.
- They do not claim clean-machine portability, crash-safe at-most-once dialing,
  local inference or production readiness without their separate evidence.
- The public Git commit tested in G3/G4 matches the published Ginse version.

## 8. Definition of done

The hackathon MVP is done only when **G0 through G5 pass against the same Git
commit and Ginse version**, including five controlled real calls and the final
one-prompt jury path.

Until Twilio credentials are configured and G3 passes, the correct status is:

> Runtime implemented and unit-tested; real PSTN call not yet verified.

## 9. After the hackathon

Prioritized follow-up:

1. move Deepgram/Twilio master credentials behind a team dial broker issuing
   short-lived install-bound capabilities;
2. persist call state and idempotency before every carrier side effect, then
   reconcile uncertain Twilio outcomes without blind redial;
3. package `uv`, Python and tunnel/runtime artifacts for a clean Mac;
4. add BYOK for independent installations;
5. benchmark and optionally promote a `local-voice` profile with local STT,
   dialogue and TTS;
6. sign/notarize the native confirmation helper and release artifacts.
