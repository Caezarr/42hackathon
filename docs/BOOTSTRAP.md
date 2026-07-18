# Fredo first-run bootstrap

Status: hackathon implementation contract.

The supported first run begins in Ginse and ends with a healthy local Fredo runtime. A live call must never discover a missing model or dependency and start an implicit download.

## Entry flow

```text
Ginse BootstrapPlan
  -> validate schema, repository, commit and manifest digest
  -> show local writes, downloads, disk cost and privileges
  -> explicit human approval
  -> install pinned Fredo Codex plugin
  -> fredo bootstrap apply
  -> fredo doctor --json
  -> explicit handoff to a fresh Codex task that loads the plugin
```

Ginse returns declarations only. It never returns arbitrary shell to execute.

## Target commands

```text
fredo bootstrap plan --from <verified-plan.json> --json
fredo bootstrap apply --from <verified-plan.json> --resume --json
fredo doctor --json
fredo doctor --offline --json
fredo up --offline --json
```

These commands are planned until implementation and tests land.

## Reference profile

`mac-m4pro-24gb` resolves only for:

- macOS `arm64`;
- Apple Silicon with at least 24 GB RAM;
- sufficient free disk reported before approval;
- a working local container runtime when the chosen media path needs it;
- permission to create a Fredo data root and isolated runtimes.

The reference machine's system Python is 3.14.3. Fredo creates a pinned Python 3.12 environment for components that do not support the system interpreter.

## State machine

```text
PLAN_RECEIVED
  -> VALIDATED
  -> APPROVED
  -> DOWNLOADING
  -> VERIFIED
  -> INSTALLED
  -> CONFIGURED
  -> HEALTHY
  -> ACTIVE
```

Every transition is journaled locally. An interrupted bootstrap resumes from verified artifacts and never treats a partial file as complete.

## Plan validation

Before any write, Fredo checks:

- exact supported schema version;
- allowlisted repository owner and URL;
- full immutable Git SHA;
- HTTPS manifest origin;
- valid SHA-256 format and matching manifest bytes;
- supported platform/profile pair;
- expiration time;
- required disk, ports, binaries and permissions.

Unknown fields may be preserved for forward compatibility but never interpreted as commands.

## Artifact manifest

Every downloaded artifact records:

- stable identifier and role;
- source URL;
- immutable revision or digest;
- expected byte size;
- SHA-256;
- declared source/model license;
- local cache path.

The hackathon does not require release signing, generalized rollback or air-gap bundles. Checksums and immutable revisions are mandatory.

## Download behavior

- use content-addressed cache paths;
- download to `.part` files;
- resume ranges when the origin supports them;
- verify the full digest before activation;
- never use `latest` or `curl | sh`;
- never run package lifecycle hooks received from Ginse;
- record transferred bytes and elapsed time.

## Activation

The profile becomes `ACTIVE` only after:

- the Fredo plugin is visible to Codex;
- `fredod` starts and opens its Unix socket;
- SQLite migrations succeed;
- local STT, LLM and TTS health checks pass;
- a loopback voice turn completes;
- LiveKit/Asterisk checks required by the selected path pass;
- the configured carrier identity is verified without placing an unconfirmed call.

## Offline contract

`doctor --offline` and `up --offline` fail if a model or runtime artifact is missing instead of resolving it from the network.

“Offline” applies to Fredo intelligence and runtime. A public phone call still uses SIP/RTP and the carrier network. The hackathon Codex session uses a local OSS provider.

## Measured proof

The bootstrap phase is complete when:

- cold install finishes in at most 30 minutes on the recorded reference network;
- one deliberately interrupted download resumes;
- `doctor --json` passes;
- a second `bootstrap apply` transfers zero artifact bytes;
- `doctor --offline --json` passes after restart;
- the exact Fredo Git SHA and artifact manifest digest are reported.
