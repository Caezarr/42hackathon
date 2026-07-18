# Fredo first-run bootstrap

Status: implementation contract derived from [`GOAL.md`](../GOAL.md) `0.3-draft`; commands and runtime are not implemented yet.

The supported first run begins with Fredo's single Ginse action and, in the same Codex task, ends with a healthy local runtime invoking the first call. A live call MUST NOT discover a missing dependency or trigger an implicit model download.

## Exact first-run contract

The judge supplies one message containing `<PHONE_E164>`. Under the declared local-write approval, the already-installed Ginse use capability creates a protected device signing key and generates `install_id` internally from 128 CSPRNG bits. The ID is encoded as exactly 22 unpadded base64url characters, the public-key SHA-256 thumbprint as exactly 43, and both are independent of prompt data; the destination stays local.

```text
one judged prompt
  -> retain and canonicalize <PHONE_E164> locally
  -> show signed public bootstrap bounds and obtain one approval
  -> create protected device key before /run under that approval
  -> invoke Ginse with platform, profile, plugin API, install_id, key thumbprint
  -> validate BootstrapPlan and non-dialing LeaseClaim within approved bounds
  -> fetch, verify, and install the pinned Fredo release and plugin
  -> persist redemption_id
  -> redeem LeaseClaim with key proof for an install-bound GatewayCapability
  -> fredo doctor --json
  -> invoke the installed fredo executable directly in this task
  -> native DialPreview and one-use Fredo confirmation
  -> policy-gateway call and structured result
```

The judge does not type a shell command, paste a credential, edit source or configuration, install a prerequisite, or send another prompt.

Codex discovers a newly installed plugin only in a new chat or CLI session. A later fresh task MUST verify plugin discovery, but it MUST NOT be required to complete the first call.

Ginse returns declarations and a non-dialing claim only. It never returns arbitrary shell to execute.

## Reference fixture

The judged profile is exactly:

- Apple Silicon `arm64`, M4 Pro, 24 GB unified memory;
- macOS 26.5, fresh user account;
- Codex CLI 0.144.1 or an explicitly tested compatible version, installed and authenticated;
- Ginse use capability installed and authorized;
- qualified network: at least 200 Mbit/s downstream, at most 40 ms RTT to the artifact mirror, below 1% packet loss;
- free disk equal to signed-manifest peak space plus 20% headroom.

The fixture has no Fredo checkout, plugin, configuration, model cache, telecom capability, Docker Desktop, Homebrew, or Fredo-ready Python runtime.

Fredo MUST package or fetch every mandatory runtime dependency through the approved bootstrap. The mandatory path cannot require a preinstalled container runtime, interactive third-party EULA, reboot, manual compiler toolchain, or unrecorded local step. Python and container choices are implementation hypotheses, not fixture requirements.

## Planned command surface

The exact CLI may be refined without weakening the schemas or one-task flow. The planned machine-readable surface is:

```text
fredo bootstrap plan --from <verified-plan.json> --json
fredo bootstrap apply --from <verified-plan.json> --resume --json
fredo access redeem --from <verified-plan.json> --json
fredo doctor --json
fredo doctor --offline --json
fredo call prepare --request <dial-request.json> --json
fredo call start --authorization <authorization.json> --json
fredo call result --call-id <id> --json
```

These commands are planned until implementation and tests land. The judged Codex task invokes them; the human does not.

## Bootstrap lifecycle

The durable state machine is:

```text
UNINITIALIZED -> PLANNED -> APPROVED -> FETCHING -> VERIFIED
              -> INSTALLED -> LEASED -> HEALTHY -> ACTIVE
```

`FAILED` is reachable from every non-terminal state. Each transition is persisted before its external effect. Resume continues only from the last durably verified artifact or transition; partial bytes never activate.

## Plan validation

Before `/run`, the Ginse shim verifies the immutable `BootstrapApprovalEnvelope` schema at the same-origin `/.well-known/fredo-bootstrap-approval.json` URL, Ginse-pinned SHA-256 and release-key fingerprint, signature, app/version binding, issue/expiry time, monotonic policy version, and anti-downgrade state. After `/run` and before any additional write or claim redemption, Fredo verifies:

- exact `BootstrapPlan` schema and integer version;
- allowlisted repository owner and canonical URL;
- full immutable Git commit SHA;
- HTTPS manifest origin and permitted redirect policy;
- manifest digest, release signature, signing identity, and downgrade rules;
- supported platform, profile, and Codex plugin API;
- `install_id`, plan expiry, policy digest, and `LeaseClaim` TTL;
- device-key thumbprint binding and proof-of-possession algorithm compatibility;
- declared artifact sizes, peak disk, ports, writes, binaries, and permissions;
- that the plan contains declarations only, never executable shell.
- that every write, byte, path, executable, key operation, and privilege is equal to or narrower than the approved envelope; incomparable or wider plans fail closed.

Unknown fields are rejected at security boundaries. Canonical hashes use RFC 8785 JSON canonicalization and SHA-256.

## Signed artifact manifest

Every executable, runtime, model, plugin, helper, and configuration artifact records:

- stable identifier, role, and immutable source revision;
- source URL and permitted mirror/fallback;
- exact byte size and SHA-256;
- source/model licence;
- platform and compatibility constraints;
- content-addressed cache and activation path.

The release record also binds the source commit, signing/notarization identity, SBOM, build provenance, provider and gateway image digests, policy digest, and Ginse app version.

Checksums alone are insufficient: release signing, notarization where applicable, SBOM, and provenance are mandatory before acceptance and public promotion.

## Download and install behavior

- Download to content-addressed `.part` files.
- Resume byte ranges only when origin behavior is validated.
- If range resume is unavailable, restart that artifact safely without activating partial bytes.
- Verify exact size, digest, signature, platform, and policy before activation.
- Never use `latest`, mutable branches, `curl | sh`, or unpinned package resolution.
- Never execute package hooks or commands supplied through Ginse data.
- Record transferred bytes, elapsed time, cache hits, and durable transitions.
- Fail closed on disk exhaustion, permission refusal, unavailable origin, signature mismatch, or downgrade.

The installer MAY trigger standard signed macOS permission or administrator dialogs already allowed by the one-prompt contract.

## Demo-access redemption

After installation, the signed confirmation helper creates its protected authorization key. Fredo recovers the precommitted device-key reference, durably persists a CSPRNG `redemption_id` and canonical request containing the authorization-key thumbprint, and sends `LeaseClaim` plus device-key proof directly to the demo-access authority. Redemption MUST:

- consume the claim exactly once;
- reject expiry, replay, wrong `install_id`, wrong device key, release mismatch, and policy mismatch;
- persist its terminal result before replying, replay it exactly for the same redemption fingerprint, and reject divergent reuse or a second redemption ID;
- bind the `GatewayCapability` to install, device, release, policy, and expiry;
- bind the capability to the authorization-key thumbprint required for every dial;
- expose no carrier master credential;
- grant access only to the mandatory SIP policy gateway;
- support per-install revocation and the server policy in `GOAL.md` Section 9.

The claim has no dialing authority and lives exactly 45 minutes from its signed issue time, leaving at least 15 minutes after the bounded cold bootstrap for redemption. The gateway capability lives at most eight hours and no later than the judging-window end, is bound to the device key, and requires proof of possession on gateway use rather than behaving as a transferable bearer secret. Secrets are stored through the signed local runtime's protected credential mechanism and never enter stdout/stderr, SQLite, Ginse, Codex results, crash reports, or public evidence.

## Health and activation

`doctor` emits independent named checks:

- `local.artifacts` — all digests and sizes match;
- `local.runtime` — executable, models, audio, permissions, and storage work;
- `local.state` — migrations, journal, and idempotency store work;
- `network.bootstrap` — Ginse/provider/artifact reachability before activation;
- `network.telecom` — gateway registration and media reachability without dialing;
- `policy.demo` — capability, server quotas, destination rules, spend cap, and kill switch;
- `release.provenance` — commit, manifest, signature, notarized binary identity, SBOM, and provenance match.

The profile becomes `ACTIVE` only when every mandatory check has the required passing status, the local voice loop completes, the install-bound capability is valid, and telecom health is proven without placing an unconfirmed call.

`doctor --offline` runs local checks only. Every network check is reported as `not_run`, never healthy. Missing local artifacts fail immediately instead of resolving them from the network.

“Local” covers call-side STT, dialogue inference, TTS, state, and transcript processing. Hosted Codex may orchestrate bootstrap; Ginse, the authority, policy gateway, carrier, and PSTN remain declared remote dependencies. Raw call audio never enters Codex, Ginse, hosted inference, or model registries.

## First-call continuation

After `ACTIVE`, the original Codex task constructs a canonical `DialRequest` from the retained `<PHONE_E164>` and prompt intent. Fredo renders its own native `DialPreview` showing destination, verified caller identity, purpose, synthetic-voice disclosure, 180-second cap, and policy/cost profile.

The signed Fredo confirmation helper creates a protected authorization key during verified installation and registers its thumbprint in demo-access redemption. Confirmation creates a helper-signed, server-verifiable `DialAuthorization` that expires within 60 seconds and binds every canonical request field, capability, policy, release, and authorization-key thumbprint. The gateway verifies and atomically consumes it; capability plus device-key proof alone cannot dial. Rejection, expiry, mutation, policy failure, or pre-commit cancellation creates zero SIP `INVITE`; post-commit cancellation emits only `CANCEL`/`BYE`. The call then uses the mandatory server-enforced gateway and returns the structured result to that same task.

## Qualification protocol

Run all three scenarios from a documented clean reset of the reference fixture:

1. cold bootstrap with one large artifact interrupted between 30% and 70%;
2. cold uninterrupted bootstrap from an equivalent clean APFS volume or documented full reset;
3. warm bootstrap plus daemon crash and recovery.

Pass criteria:

- each cold run completes within 30 minutes on the qualified network and manifest-size bound;
- interrupted download resumes verified bytes and never activates partial content;
- warm bootstrap transfers zero artifact body bytes;
- restart reaches legal durable states and never repeats an external side effect;
- full doctor status semantics pass, including offline `not_run` network checks;
- the same Codex task reaches the native call preview with no source edit, shell typing, key paste, prerequisite install, or second prompt;
- a later fresh task discovers the plugin;
- every log and evidence item is linked to release SHA, configuration digest, run ID, and artifact hashes.

## Release promotion

Bootstrap is accepted only as part of this immutable promotion chain:

```text
candidate commit
  -> signed/notarized assets + SBOM + provenance
  -> staging Ginse verification
  -> clean-machine bootstrap and full acceptance
  -> immutable public Ginse version + Git release
  -> production smoke call using identical bytes
```

Any rebuilt, repackaged, re-signed, reconfigured, or re-published byte invalidates prior acceptance and must re-enter staging.

## Current implementation truth

No Fredo installer, plugin, CLI, daemon, signed release manifest, lease redemption, health suite, or bootstrap evidence exists in the repository yet. This document defines the implementation and proof required; it does not claim those capabilities are available.
