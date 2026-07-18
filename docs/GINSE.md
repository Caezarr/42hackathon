# Ginse integration

Ginse is an optional marketplace and invocation layer for self-hosted operators, but it is required for the team's hackathon demo. It does not host Agent Call, install containers, or call a user's `localhost`.

Canonical references:

- [Use Ginse from Codex](https://app.ginse.ai/agent.md)
- [Ginse v3 contracts](https://app.ginse.ai/contracts/v3/README.md)

## Fixed endpoint constraint

A published Ginse app version has one fixed public HTTPS `run_url`. One universal listing therefore cannot invoke many unrelated local installations without a central broker.

Agent Call deliberately has no central broker.

## Supported model

Every operator who wants Ginse publishes their own installation:

```text
operator-owned Ginse listing
  -> operator-owned HTTPS /run
  -> operator-owned Agent Call appliance
  -> operator-owned SIP or SIM transport
```

Users who want a fully local workflow use the MCP server and skip Ginse entirely.

For hackathon judging, the team will expose one clearly labelled demo installation. That is a required demonstration endpoint, not the product architecture.

## One marketplace action

The MVP action is:

```text
consented callback request -> local AI phone call -> structured outcome
```

Marketplace input never carries an arbitrary phone number. It references a contact already stored and allowlisted inside that operator's installation:

```json
{
  "contact_id": "contact_demo_requester",
  "request": "Explain the appointment change and ask whether the new time works.",
  "language": "en",
  "max_duration_seconds": 90
}
```

`POST /run` creates a durable `waiting_for_operator_confirmation` operation. A caller-provided boolean is never treated as consent. The local operator must approve the resolved destination and call intent before any dial side effect. Verification uses a controlled local contact.

Suggested terminal output:

```json
{
  "call_id": "call_01JEXAMPLE",
  "outcome": "completed",
  "summary": "The requester accepted the new time.",
  "duration_seconds": 42,
  "next_actions": []
}
```

## Provider requirements

Each installation that enables Ginse must:

- verify the short-lived Ed25519 bearer token;
- validate the published input schema;
- atomically claim `Idempotency-Key` before dialing;
- bind the key to a canonical request fingerprint;
- persist one stable `provider_operation_id`;
- return `202` and a same-origin status URL for pending calls;
- replay stored results without repeating the call;
- reject a key reused with different input;
- validate terminal output against the published schema;
- serve that installation's generated manifest unchanged.

The status endpoint must expose the non-terminal approval state without leaking the resolved phone number.

App identity, ownership token, display name, price, manifest, and public URL belong to one installation and must not be copied into a universal project manifest.
