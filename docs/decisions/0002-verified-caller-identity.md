# ADR 0002: Verified caller identity only

Status: accepted on 2026-07-18.

## Context

Some desktop calling services market arbitrary caller-ID presentation as “spoofing”. This does not remove the need for carrier infrastructure and creates fraud, blocking, and legal risk.

## Decision

Agent Call supports only caller identities owned by the operator's SIM or verified by the operator's SIP carrier.

## Consequences

- caller-ID spoofing is not implemented;
- transport configuration must prove identity ownership or carrier verification;
- destination policy blocks emergency, premium-rate, short-code, and prohibited numbers;
- public documentation must not imply anonymous or bulk calling capability.
