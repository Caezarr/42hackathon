# ADR 0001: Per-user self-hosting

Status: accepted on 2026-07-18; Ginse distribution amended by [ADR 0003](0003-fredo-hackathon-contract.md).

## Context

The product should let anyone deploy their own instance and run calls with their own compute, models, data, and phone transport.

## Decision

Fredo is distributed as a Codex plugin plus a local runtime. The project does not operate a shared call backend or central broker.

## Consequences

- A Git-backed Codex plugin marketplace and pinned Fredo artifacts are the local distribution channel.
- Every operator supplies their own SIP account or SIM.
- Every operator owns storage, retention, quotas, and telecom costs.
- The Fredo skill and CLI are the default Codex integration; MCP is an optional adapter.
- One Ginse app resolves bootstrap plans and never executes user calls.
