# Security and abuse boundaries

This project touches phone numbers, audio, credentials, and public telecom networks. Safety gates are product requirements, not optional polish.

## Prohibited product behavior

- arbitrary caller-ID spoofing;
- emergency, premium-rate, or prohibited destination dialing;
- anonymous robocalling or bulk dialing;
- scraping contacts and calling them without an explicit operator action;
- bypassing carrier verification, consent, or recording law;
- exporting transcripts, audio, or credentials by default.

## Required controls

- explicit operator confirmation before a live call;
- destination normalization and policy checks before dispatch;
- per-call idempotency keys;
- duration and concurrency caps;
- verified caller identity;
- encrypted local secrets;
- redacted logs;
- recording disabled by default;
- a local kill switch;
- no auto-update that executes unverified artifacts.
- one-use confirmation bound to the destination, intent, caller identity, and duration;
- automated synthetic-voice disclosure at the beginning of the call;
- a Ginse boundary that accepts only a platform profile and returns only a bootstrap plan.

## Ginse data boundary

The public Ginse provider must never receive phone numbers, contacts, call intents, SIP credentials, audio, transcripts, or call results. Bootstrap plans contain immutable source identifiers and digests, not request-supplied shell commands.

## Reporting a vulnerability

Use GitHub's private security advisory flow for this repository. Do not publish credentials, phone numbers, recordings, or exploitable details in a public issue.
