# Fredo telephony plan

Fredo supplies call control and local voice intelligence. Each installer supplies a real telecom transport and caller identity they own.

## Hackathon target

- outbound calls only;
- one active call;
- one operator-owned SIP trunk;
- one carrier-verified caller number;
- one controlled destination before the judge call;
- PCMA/PCMU acceptable for the first public call;
- recording disabled.

The first judged destination is the real phone of a consenting jury member.

## Hero path

```text
Pipecat
  <-> LiveKit room
  <-> LiveKit SIP
  <-> Asterisk PJSIP
  <-> registered SIP trunk
  <-> PSTN
  <-> judge phone
```

This path is intentionally excessive:

- Pipecat controls the conversation graph and interruptions;
- LiveKit provides the realtime room and supervision;
- LiveKit SIP bridges room media to SIP;
- Asterisk handles carrier registration, codec/DTMF quirks, CDR and later hardware transports.

It remains the hero path only if it completes two consecutive real calls.

## Fallback ladder

1. **LiveKit SIP -> carrier directly.** Remove Asterisk when the carrier works cleanly without it.
2. **Pipecat -> Asterisk -> carrier.** Remove LiveKit supervision when it blocks the first real call.
3. **PyVoIP diagnostic.** Use a minimal pure-Python SIP/RTP client to isolate registration, G.711 and RTP problems.

Never keep two failing paths active during the same debugging window.

## PyVoIP boundary

[PyVoIP](https://github.com/tayler6000/pyVoIP) is a useful laboratory dependency because it is pure Python and documents PCMA, PCMU and telephone-event support. It does not provide a sound layer, and its documented G.711 path is 8 kHz mono. Fredo must own buffering, resampling and integration with the voice pipeline.

PyVoIP is GPL-3.0. It remains an isolated development dependency until redistribution and combined-work licensing are reviewed.

It is not the judged carrier abstraction for NAT, secure media, observability or operator diversity.

## Mac-first networking

The first attempt runs locally on the M4 Pro Mac:

- native Fredo daemon and local inference;
- local containers for LiveKit, LiveKit SIP and Asterisk when selected;
- registered outbound SIP trunk;
- explicit UDP port and advertised-address configuration.

Typical planned ports must be made configurable:

- SIP UDP/TCP 5060 or TLS 5061;
- LiveKit SIP RTP UDP 10000–20000;
- LiveKit RTC media on a separate configured UDP range;
- local HTTPS/WSS endpoints with valid certificates only when browser access requires them.

A public telecom edge plus WireGuard is introduced only if:

- the carrier requires a stable public peer;
- CGNAT prevents correct RTP return;
- Docker Desktop networking cannot satisfy the media path;
- the team chooses to colocate the already-required public Ginse provider with telecom services.

The edge never runs Fredo models or stores transcripts.

## Audio boundary

Public telephony commonly delivers 8 kHz G.711 audio. Local engines may expect 16 kHz or 24 kHz. Fredo must measure and test:

```text
carrier 8 kHz -> jitter buffer -> resampler -> local voice engine
local voice engine -> resampler -> G.711 packetizer -> carrier
```

Moshi's Mimi codec uses 24 kHz audio. The Moshi experiment is not accepted until the complete 8 kHz PSTN round trip remains intelligible and meets latency gates.

## Identity and policy

Caller-ID spoofing is outside scope. Fredo presents only an identity verified by the configured carrier.

Before the transport receives a dial command, Fredo must:

- normalize the destination to E.164;
- apply country and destination policy;
- block emergencies, premium-rate numbers, short codes and prohibited ranges;
- verify a fresh one-use confirmation bound to number and intent;
- claim the local idempotency key;
- enforce the one-active-call limit.

## Transport contract

Every implementation exposes:

```text
configure -> doctor -> dial -> events -> send_audio -> receive_audio -> hangup
```

Required normalized events:

```text
trying, ringing, answered, media_started, dtmf, media_stopped, hung_up, failed
```

Every event carries the same Fredo `call_id` and a monotonic local timestamp.

## Proof before the judge

- carrier registration survives ten minutes;
- two consecutive controlled calls complete;
- expected caller ID appears;
- ring, answer, DTMF and hangup events are observed;
- bidirectional audio runs for 90 seconds;
- one barge-in works;
- no secret or complete phone number appears in public logs;
- repeating an idempotency key creates no second carrier call.
