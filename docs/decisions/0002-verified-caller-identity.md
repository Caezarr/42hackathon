# ADR 0002: Verified caller identity only

Status: accepted on 2026-07-18; judged gateway custody clarified by [ADR 0004](0004-one-prompt-demo-access.md).

## Context

Some desktop calling services market arbitrary caller-ID presentation as “spoofing”. This does not remove the need for carrier infrastructure and creates fraud, blocking, and legal risk.

## Decision

The stack supports only caller identities owned by the operator's SIM or verified by the operator's SIP carrier. For the judged milestone, the team is the telecom operator: its verified identity and carrier credential remain at the server-side SIP policy gateway.

## Consequences

- caller-ID spoofing is not implemented;
- transport configuration must prove identity ownership or carrier verification;
- judges receive no credential capable of changing or bypassing the verified caller identity;
- destination policy blocks emergency, premium-rate, short-code, and prohibited numbers;
- public documentation must not imply anonymous or bulk calling capability.
