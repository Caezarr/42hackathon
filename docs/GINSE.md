# Ginse contract for Fredo

Ginse is the hackathon entry point for Fredo. A successful demo starts with Ginse discovery and ends with a local Fredo call.

Ginse does not host Fredo, install files on the user's Mac, or route phone calls. It invokes one self-hosted HTTPS action with one fixed price. Fredo uses that action to resolve a safe local bootstrap plan.

The team therefore operates one mandatory, minimal Fredo provider on a public HTTPS Docker host chosen in P0. This host is independent from the user's Mac and from any optional SIP/RTP edge. It stores only provider authentication/idempotency state and immutable bootstrap plans.

Canonical references:

- [Use Ginse from Codex](https://app.ginse.ai/agent.md)
- [Ginse v3 provider contracts](https://app.ginse.ai/contracts/v3/README.md)

## Marketplace action

Working listing:

- display name: `Fredo — 42hackathon`;
- action: `Resolve a local Fredo bootstrap plan`;
- proposed hackathon price: EUR 0.42 in the fake ledger;
- input icon: `code`;
- output icon: `document`.

Flow preview:

```text
Mac profile -> resolve pinned Fredo bootstrap -> verified BootstrapPlan
```

This is one deterministic marketplace action. Calling, status, cancellation and result retrieval are local Fredo operations, not separate Ginse products.

## Input

The first published version supports only the team profile:

```json
{
  "platform": "macos-arm64",
  "profile": "mac-m4pro-24gb",
  "codex_plugin_api": 1
}
```

Unknown platforms, profiles or API versions are rejected. The request never contains a phone number, SIP account, user prompt, contact, audio or transcript.

## Output

```json
{
  "schema_version": 1,
  "product": "fredo",
  "profile": "mac-m4pro-24gb",
  "source": {
    "repository": "https://github.com/Caezarr/42hackathon",
    "commit": "<immutable-git-sha>"
  },
  "plugin": {
    "marketplace": "Caezarr/42hackathon",
    "name": "fredo"
  },
  "manifest_url": "https://provider.example/releases/fredo-mac-v1.json",
  "manifest_sha256": "<sha256>",
  "expires_at": "2026-07-19T00:00:00Z"
}
```

The provider returns declarations, never arbitrary shell. The repository owner, exact commit, allowed manifest origin and digest format are validated again locally before Codex asks to execute anything.

## Provider behavior

`POST /run` must:

- verify the short-lived Ginse Ed25519 bearer token;
- validate the published input schema;
- atomically claim `Idempotency-Key` before accepting the run;
- bind the key to a canonical input fingerprint;
- persist one stable opaque `provider_operation_id`;
- return the same stored plan with `replayed:true` for exact duplicates;
- reject a reused key with different input;
- validate the final plan against the advertised output schema;
- expose a same-origin status URL only if plan resolution is asynchronous.

Plan resolution should normally return synchronously with status `succeeded`. The provider stores no call data because it never receives call data.

The generated manifest is served unchanged at `/.well-known/ginse.json` and verified before publication.

## Codex consumer flow

The copyable usage prompt should cause this sequence:

```text
1. Invoke Fredo on Ginse for mac-m4pro-24gb.
2. Validate the returned BootstrapPlan schema and allowlisted repository.
3. Show commit, downloads, disk use and permissions.
4. Ask once before local writes or dependency downloads.
5. Add the pinned Fredo Codex plugin marketplace.
6. Install the Fredo plugin.
7. Run fredo bootstrap apply with the verified manifest.
8. Run fredo doctor --json.
9. End the bootstrap task with an explicit handoff.
10. Start a fresh Codex task so the newly installed Fredo plugin is loaded.
11. Continue locally through the Fredo skill.
```

The current Codex CLI provides stable plugin marketplace and plugin installation commands. Fredo must pin the Git ref rather than tracking an unqualified branch.

## Locality boundary

Ginse is intentionally essential to acquisition and bootstrap, but absent from the live-call path.

```text
Ginse knows: supported platform profile, Fredo release selection, provider operation
Ginse never knows: destination, intent, caller identity, credentials, audio, transcript, result
```

After installation, losing Ginse connectivity must not prevent `fredo doctor`, local preparation or a SIP call using already downloaded artifacts.

## Hackathon proof

The Ginse milestone passes only when:

- provider authentication, schema validation and idempotent replay tests pass;
- the manifest verification status is `passed`;
- the app is published and has an immutable listing version;
- a fresh Codex task invokes the copyable prompt;
- Codex installs Fredo from the returned pinned plan without source edits;
- the bootstrap task hands off cleanly and a fresh task loads the installed Fredo plugin;
- a second plan invocation replays safely;
- the subsequent judge call contains no Ginse request;
- captured Ginse payloads contain no call data.

## Explicit non-goal

Each Fredo user does **not** publish a separate Ginse call endpoint. One Fredo Ginse app resolves installation plans; every installed Fredo instance executes calls locally.
