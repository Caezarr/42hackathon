# ADR 0004: One-prompt bootstrap and judged demo access

Status: accepted on 2026-07-18; amends [ADR 0001](0001-per-user-self-hosting.md) and [ADR 0003](0003-fredo-hackathon-contract.md).

## Context

The judged experience must begin with one natural-language Codex prompt on a
clean reference Mac. The judge cannot paste a carrier key, prepare a shell, or
restart the product flow after installation. At the same time:

- Ginse is the required marketplace and bootstrap front door;
- Ginse and the Fredo provider must not receive call content or a credential
  capable of dialing;
- a newly installed Codex plugin is discovered only in a fresh task;
- the first call must still complete in the original task;
- judges temporarily use the team's verified carrier account;
- an extracted local credential must not bypass spend and abuse controls.

The earlier ADRs did not resolve these constraints together. ADR 0001 assumed
every operator already supplied a transport, and ADR 0003 required a task
handoff before the first call. Both assumptions conflict with the normative
[`GOAL.md`](../../GOAL.md) `0.3-draft` contract.

## Decision

### One prompt and same-task first run

The already installed Ginse capability is the cold-start bootstrap shim. From
the judge's single parameterized prompt, the original Codex task invokes the
one Fredo Ginse action, applies the verified plan, runs the installed `fredo`
CLI, completes named doctor checks, obtains native local call confirmation, and
performs the first call.

The freshly installed Fredo plugin is verified in a later fresh Codex task.
Fresh-task plugin discovery is an acceptance check, not a handoff and not a
prerequisite for the same-task first call.

### Ginse carries no dialing authority

The Ginse request contains only the versioned platform/profile metadata and an
opaque `install_id` allowed by the normative `BootstrapRequest` schema. The
response contains the pinned `BootstrapPlan` and MAY contain one opaque,
single-use `LeaseClaim` with a signed issue time and exactly 45 minutes of
validity, leaving redemption margin after the bounded cold bootstrap.

Before `/run`, the trusted Ginse shim creates a protected device signing key,
generates `install_id` from 128 CSPRNG bits, and sends only the key's SHA-256
thumbprint. It emits exactly 22 and 43 unpadded base64url characters
respectively. Neither value comes from the prompt or model. Taint tests and
captured payloads prove independence from call data; schema shape alone is not
treated as proof against a covert channel.

`LeaseClaim` is deliberately non-dialing. It cannot authenticate to the SIP
gateway or carrier, select a destination, present a caller identity, or create
a call. Ginse and the Fredo provider never receive the destination, call
intent, caller identity, audio, transcript, model state, summary, or result.

After installation, Fredo recovers the precommitted key and redeems the claim
directly with proof of possession. It durably persists a random
`redemption_id` before the request. The authority stores the terminal result
before reply, returns that exact result for an identical retry after response
loss, and rejects divergence or a second redemption ID. The resulting gateway
capability is bound to the install ID, device public key, release SHA, policy
digest, and expiry and requires proof of possession on gateway use. Claim-first
theft, replay, divergence, downgrade, expiry, wrong binding, and authority
failure all fail closed.

The signed native confirmation helper owns a separate protected authorization
key registered during redemption and bound into the gateway capability. After
the local click it signs a one-use `DialAuthorization` over the complete
canonical request and release/policy bindings. The gateway verifies and
atomically consumes this attestation with the dial idempotency key. Device-key
proof and gateway capability alone do not authorize a carrier attempt.

### Shared credential remains at the gateway

For judging only, the team operates and funds a mandatory server-side SIP
policy gateway backed by its verified carrier account. The carrier master
credential exists only at that telecom boundary or its dedicated server-side
secret store. It is never returned by Ginse, the provider, demo-access
authority, or gateway, and never reaches Codex, the judge, or local Fredo.

The local capability grants access only through the gateway. The gateway or
carrier enforces the Goal's destination, caller identity, spend, duration,
attempt-rate, concurrency, expiry, and per-install revocation rules even when
Fredo is bypassed. Bring-your-own carrier ownership replaces this temporary
team-funded exception after the hackathon; it is not required during judging.

### Remote speech has no authority

Phone audio is untrusted input to a side-effect-free conversation engine. It
cannot alter the dial request or policy, authorize or initiate another call,
invoke a shell or tool, install code, access local files, or disclose a secret.
Only the local judge's native confirmation can authorize the one prepared call.

### Release trust

Bootstrap activates only artifacts in the accepted signed manifest. Native
macOS assets are signed and notarized. The promoted release binds the Git
commit, artifact digests, SBOM, build provenance, provider and gateway OCI
digests, and immutable Ginse version as required by the Goal. Technology names
remain non-normative unless a later ADR freezes them after measurement.

## Consequences

- The judged experience has one prompt and named approval dialogs, but no shell,
  secret paste, source edit, second prompt, or task handoff.
- The first run depends on the installed CLI; plugin discovery is proven in a
  separate fresh task.
- Ginse can transport a claim because the claim is opaque and non-dialing; the
  old shorthand “no credentials through Ginse” is replaced by the precise rule
  “no dial authority, gateway capability, or carrier credential through
  Ginse”.
- The demo-access authority and SIP policy gateway are mandatory judged
  infrastructure, while live intelligence and durable Fredo state remain
  local.
- The gateway necessarily sees destination signaling and may relay RTP, but it
  receives no prompt, transcript, model state, or summary and records no audio.
- Loss or extraction of a judge's gateway capability is bounded by server-side
  quotas, expiry, policy, and per-install revocation.
- ADR 0001 remains the long-term ownership direction, with a documented
  team-funded hackathon exception.
- ADR 0003's explicit first-run task handoff and mandatory local Codex OSS
  provider are superseded.
