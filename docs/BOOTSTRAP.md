# First-run bootstrap

Status: implementation contract.

The installation experience is download-heavy once and quiet afterwards. A call must never discover that a model or runtime is missing and begin an implicit download.

## Target commands

```text
phone-stack init --compute auto --transport browser|sip|gsm-sip|android-bt
phone-stack plan
phone-stack bootstrap --resume
phone-stack transport configure
phone-stack transport pair android-bt
phone-stack doctor --offline
phone-stack up --offline
phone-stack bundle export ./stack.phonebundle
phone-stack bundle import ./stack.phonebundle
phone-stack update --download-only
phone-stack update --apply
phone-stack rollback
```

These commands are planned until an implementation and tests land. `phone-stack` is only a neutral CLI placeholder while the project name remains undecided.

## State machine

```text
DETECTED
  -> RESOLVED
  -> APPROVED
  -> DOWNLOADING
  -> VERIFIED
  -> STAGED
  -> CONFIGURED
  -> HEALTHY
  -> ACTIVE
```

An interrupted bootstrap resumes from its durable journal. It never treats a partial file as verified.

## Resolution

`plan` detects and reports:

- OS and architecture;
- RAM, free disk, and available ports;
- Apple Silicon, CPU-only, or NVIDIA compute;
- CUDA driver and container-toolkit readiness without installing them silently;
- selected transport requirements;
- download sizes and licenses;
- privileges, firewall changes, and hardware access that require consent.

Compute and transport resolve separately. For example, `mac-metal + gsm-sip` is valid while `mac-metal + android-bt` is rejected.

## Artifact policy

- repository sources use immutable commits;
- OCI images use `repository@sha256:digest`;
- models use immutable revisions plus SHA-256 and expected size;
- Python dependencies use a locked offline wheelhouse;
- release manifests are signed;
- no `latest`, `curl | sh`, or executable hooks from remote manifests.

Downloads use `.part` files and resume where supported. A complete digest check happens before atomic activation into a content-addressed cache.

## Activation and rollback

Each release stages a new runtime generation. The `current` pointer changes only after:

- services start;
- database migrations complete or safely roll back;
- local inference passes a health check;
- browser loopback completes STT → LLM → TTS;
- the selected phone transport passes its own doctor check.

The previous generation remains available for rollback.

## Offline guarantee

`doctor --offline` and `up --offline` block registry and model-hub resolution. Missing artifacts cause a clear error instead of a network fallback.

“Offline” applies to intelligence and local runtime. SIP still needs the internet and GSM still needs the cellular network during a public phone call.

## Air-gapped installation

`bundle export` packages the signed release manifest, pinned OCI content, wheelhouse, and selected models. `bundle import` verifies the same signatures and hashes before staging them on another machine.
