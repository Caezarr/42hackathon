# ADR 0005: Hosted voice MVP for the immediate hackathon demo

Status: accepted on 2026-07-18 for the temporary `hosted-voice-mvp`
profile and incorporated into [`GOAL.md`](../../GOAL.md) `0.4-draft`. The
longer local architecture from Goal `0.3-draft` is deferred, not silently
claimed by this profile.

## Context

The complete local-inference and self-hosted SIP path described by the Goal is
not ready for an immediate end-to-end telephone demonstration. Finishing and
qualifying local STT, dialogue inference, TTS, durable crash recovery, a signed
confirmation helper, and a bypass-resistant SIP policy gateway would delay the
first real call beyond the hackathon window.

Deepgram publishes an outbound-telephony Voice Agent reference that connects a
hosted STT/LLM/TTS session to Twilio Media Streams. It provides a shorter path
to one guarded, consented demonstration call while preserving a small local
Fredo control surface.

This ADR records that shortcut honestly. Goal `0.4-draft` makes it the active
hackathon profile and defines new evidence gates. This decision does not make
an acceptance gate pass or permit this profile to be described as all-local.

## Decision

### Temporary named profile

For the immediate hackathon MVP, use the explicit `hosted-voice-mvp` profile.
It replaces the local call-side inference stack and complex self-hosted SIP
path for this profile only:

| Boundary | Responsibility and data received |
| --- | --- |
| Team Mac | Codex/CLI orchestration, exact-destination policy check, native preview and confirmation, public-tunnel lifecycle, Twilio/Deepgram media bridge, in-process call state, transcript/result handling, and hangup control. |
| Deepgram Voice Agent | Hosted live STT, LLM dialogue, and TTS. It necessarily receives the call audio, configured agent prompt and call intent, transcript context, and generated responses. |
| Twilio | Outbound PSTN access, the verified team caller identity, destination and call metadata, Media Streams, status callbacks, and terminal hangup. No separate LiveKit, Asterisk, or custom SIP gateway is required by this profile. |
| Public tunnel | Routes Twilio HTTPS/WebSocket callbacks to the service on the team Mac. It has no policy or conversation role. |
| Ginse and Fredo provider | Mandatory fixed-price preparation receipt only. They never receive the phone number, call intent, caller identity, audio, transcript, summary, or result. |

Ginse remains a mandatory step in the demonstrated flow. Its request contains
exactly `platform=macos-arm64` and `profile=hosted-voice-mvp`; its typed output
contains only compatibility, an opaque short-lived demo session ID and expiry.
The destination and intent remain outside both the Ginse request and response.
They enter the local Fredo flow only after the Ginse handoff; the confirmed
intent is then sent directly from the team-controlled runtime to Deepgram as
part of the hosted agent configuration.

### Credentials and narrow operating policy

Deepgram and Twilio credentials, plus the callback endpoint secret, are
injected through process environment variables on the team-controlled Mac or
team-operated server running this profile. They are never committed, returned
to Codex, included in Ginse payloads, or intentionally logged. The checked-in
environment example contains names only, never values.

The `hosted-voice-mvp` profile is limited to the following controls:

- dialing is default-deny and accepts only exact canonical E.164 destinations
  pre-enrolled in the local allowlist; French number-class validation is an
  additional eligibility check, never a wildcard authorization;
- the complete destination, verified caller identity, intent, disclosure, and
  duration cap are shown in a Fredo-owned native confirmation before dialing;
- at most one call may be active in the team runtime;
- every call has a hard maximum duration of 180 seconds and is terminated
  through Twilio when that bound is reached;
- recording remains disabled, and remote speech has no tool other than the
  bounded function that records the demo answer and ends the current call.

These are MVP controls in the local team process. They are not represented as
equivalent to Goal v0.3's server-enforced policy or signed authorization
protocol when the client is bypassed.

### Pinned reference

The required reference implementation is Deepgram's official
`deepgram-devs/deepgram-voice-agent-outbound-telephony` repository, pinned in
`deploy/upstreams.lock.json` at commit
`e748852e653f6b8f184429d6aa79e7ea2e5007f9` under the
`hosted-voice-mvp` profile. The repository is MIT licensed. The pin is a source
reference, not proof that Fredo's release dependencies or deployed services are
fully locked.

## Differences from the retired Goal v0.3 architecture

This decision replaced mandatory parts of the former Goal `0.3-draft` for the
hackathon milestone. The table remains as an explicit record of what moved to
post-hackathon work:

| Goal requirement | `hosted-voice-mvp` reality |
| --- | --- |
| Sections 4.1-4.2, `I-09`, `G2.1-G2.3`: call-side STT, reasoning, TTS, transcripts, and raw audio stay local | Deepgram performs hosted STT/LLM/TTS and receives live audio, the intent, and transcript context. |
| Sections 6.2 and 9, `G3.4-G3.5`: a carrier or SIP gateway enforces destination, spend, duration, rate, concurrency, expiry, and revocation even when Fredo is bypassed | The MVP talks directly to Twilio. Its exact allowlist, 180-second cap, and single-call limit are enforced primarily by the local team runtime and do not prove bypass resistance. |
| Sections 7.2-7.3, `I-01`: an install-bound capability plus a signed, one-use native `DialAuthorization` is consumed server-side | The MVP uses a local native confirmation dialog but has no signed helper attestation or gateway-side atomic consumption. |
| Sections 8.2-8.3, `I-02-I-05`, `G3.2`, `G5.1`: durable at-most-once state and crash reconciliation precede telecom effects | Call state is local and in-process; it is not the Goal's durable journal or crash-safe at-most-once protocol. |
| Sections 5.2 and 7.2: the carrier master credential exists only at the telecom gateway boundary | The temporary Twilio credential is supplied to the team-controlled Mac/server process through its environment. |
| `G1.*`, `G4.*`, `G5.*`, and `G6.*`: clean-machine, telephony, privacy, evidence, signing, and release-equivalence gates pass | This ADR supplies no such evidence and makes no completion claim. |

Preserving Ginse minimization, exact allowlisting, explicit confirmation,
180-second duration, and concurrency one reduces the temporary demo risk. It
does not provide the deferred guarantees. The profile must be labelled
`experimental` and `hosted` until the Goal `0.4-draft` live-call and release
gates pass.

## Consequences

- A real PSTN demonstration can be attempted sooner with fewer moving parts.
- Availability, latency, privacy, and cost now depend on Deepgram, its selected
  LLM provider, Twilio, and the public tunnel.
- Deepgram is a live-call content processor and Twilio is a telecom/media
  processor; neither may be described as a content-blind transport.
- The local controls reduce accidental misuse but do not satisfy the Goal's
  malicious-client bypass or carrier-credential isolation requirements.
- Results from this profile may prove the product interaction, but they cannot
  be reused as evidence for the local-inference, durable-state, gateway-policy,
  or release-equivalence gates.
- ADR 0003's and ADR 0004's local-inference, `LeaseClaim` and SIP-gateway
  mechanisms are superseded only for this named, immediate profile. Their
  long-term safety direction remains.

## Future conforming path

The complete local path remains planned after the hackathon MVP: local STT,
LLM, TTS, transcript processing and durable state on the judge's Mac; a signed
and notarized confirmation helper; install-bound authorization; and a
server-enforced carrier/SIP policy boundary with crash-safe at-most-once
recovery. It must receive a distinct profile and pass its own future acceptance
gates before Fredo is claimed to provide the deferred local architecture.
