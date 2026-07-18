# ADR 0001: Per-user self-hosting

Status: accepted on 2026-07-18; Ginse distribution amended by [ADR 0003](0003-fredo-hackathon-contract.md), and the judged telecom-ownership exception amended by [ADR 0004](0004-one-prompt-demo-access.md).

## Context

The long-term product should let anyone deploy their own instance and run calls with their own compute, models, data, and phone transport. The judged milestone also needs a zero-configuration telecom path for consenting judges who do not yet have carrier credentials.

## Decision

Fredo is distributed as a Codex plugin plus a local runtime. The project does not operate shared inference, dialogue, transcript, or durable call-state infrastructure.

For the judged milestone only, the team operates a server-side SIP policy gateway using its verified carrier account. The gateway is a bounded telecom transport and enforcement boundary, not a shared Fredo intelligence backend. It is the only Fredo component permitted to hold the shared carrier master credential.

After the hackathon, bring-your-own carrier credentials and per-install transport ownership remain the default product direction.

## Consequences

- A Git-backed Codex plugin marketplace and pinned Fredo artifacts are the local distribution channel.
- Every installation owns local compute, models, call state, transcript storage, and retention.
- During judging, an installation receives only a short-lived, install-bound gateway capability under team-funded server-side quotas; it never receives the carrier master credential.
- After the judged milestone, every operator supplies and funds their own SIP account or SIM unless a separately specified managed transport is introduced.
- The Fredo skill and CLI are the default Codex integration; MCP is an optional adapter.
- One Ginse app resolves bootstrap plans and may relay an opaque, non-dialing `LeaseClaim`; it never executes or authorizes a user call.
- Destination, intent, caller identity, audio, transcript, model state, summary, and call result remain outside Ginse and the Fredo provider.
