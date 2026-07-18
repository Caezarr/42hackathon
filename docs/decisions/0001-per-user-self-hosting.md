# ADR 0001: Per-user self-hosting

Status: accepted on 2026-07-18.

## Context

The product should let anyone deploy their own instance and run calls with their own compute, models, data, and phone transport.

## Decision

The stack is distributed as an appliance. The project does not operate a shared call backend or central broker.

## Consequences

- GitHub releases and signed OCI artifacts are the distribution channel.
- Every operator supplies their own SIP account or SIM.
- Every operator owns storage, retention, quotas, and telecom costs.
- Local MCP is the default Codex integration.
- A Ginse listing, when enabled, belongs to one public installation.
