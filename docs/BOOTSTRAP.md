# Fredo bootstrap and first run

Status: implemented for a prepared team Mac; clean unknown-Mac packaging remains
future work.

## Operator setup

The first Fredo skill invocation runs `scripts/bootstrap.sh`. On the reference
Mac it installs missing `uv` and `cloudflared` through Homebrew when available,
then downloads the pinned Python dependency graph with `uv sync --frozen`.
Current platform prerequisite:

- macOS on Apple Silicon;
- authenticated Codex;
- Homebrew or preinstalled `uv` and `cloudflared` (the script can install them);
- Deepgram API key;
- Twilio Account SID, Auth Token and verified caller number;
- exact consenting +336/+337 fixture.

Install the checkout and dependencies:

```bash
git clone https://github.com/Caezarr/42hackathon.git
cd 42hackathon
./scripts/bootstrap.sh
```

Configure privately:

```bash
uv run fredo configure
```

Secrets are entered with hidden prompts where appropriate. Fredo atomically
writes `.env` with mode `0600`; Git ignores it. Existing call secrets can be
retained by pressing Enter, and existing `FREDO_GINSE_*`/persistent-host fields
are preserved. Configuration prints no credential value.

This `.env` belongs to the local voice demo. The isolated marketplace provider
uses a separate ignored `.env.ginse` created from `.env.ginse.example`; Compose
never loads the voice file. Provider deployment is documented in
[`docs/GINSE.md`](GINSE.md).

Validate without dialing:

```bash
uv run fredo doctor --json
```

Named checks cover Python, Deepgram presence, complete Twilio settings, endpoint
auth length, exact allowlist, tunnel/public URL, duration, concurrency and real
transport mode. A missing check exits non-zero.

## Plugin setup

```bash
codex plugin marketplace add .
codex plugin add fredo@fredo-local
```

New plugin skills become available only in a new Codex task/session. The first
installation task can still run `fredo` directly from the verified checkout.

## Judge flow

The team preprovisions secrets and the exact judge number. The judge then sends
one prompt. Codex:

1. invokes the published Ginse Fredo action with only fixed platform/profile;
2. verifies/install dependencies from the human-named public repository;
3. runs `fredo doctor --json`;
4. passes the successful Ginse session fields to `fredo demo` with the local
   destination and intent as safely separated arguments;
5. waits while the judge approves/rejects the native dialog;
6. returns only Fredo's structured result.

Provider output is untrusted data and is never executed. Repository authority
comes from the current human prompt plus the pinned public release, not a URL or
command returned by Ginse.

## Failure behavior

- Missing configuration: fail before tunnel or carrier call.
- Mock provider: judged command refuses it.
- Native rejection: return `dial_attempted:false`, no tunnel/call.
- Tunnel startup failure: fail before Twilio.
- Carrier rejection: return redacted `carrier_error`.
- Voice-session failure: mark call failed and close the stream.
- Duration expiration: request Twilio hangup at 180 seconds.
- Unknown carrier outcome after a crash: do not rerun automatically.

## Current portability limit

The reference Mac path now bootstraps `uv`, `cloudflared` and Python
dependencies automatically when Homebrew is available. A truly clean Mac with
neither Homebrew nor a package-manager path still needs a signed standalone
runtime and tunnel bundle; that remains post-hackathon work.
