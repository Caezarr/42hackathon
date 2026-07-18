# Fredo telephony plan

Status: non-normative implementation plan subordinate to `GOAL.md` `0.3-draft`.

The hackathon path uses a team-funded carrier account behind a mandatory SIP policy gateway. Judges do not paste a SIP key and installations never receive the shared carrier credential. BYOK and per-install carrier ownership are post-hackathon work.

## Judged target

- French outbound calls only;
- one verified team caller identity;
- one active call per installation and three globally;
- a short-lived install-bound gateway capability;
- the real phone of a consenting judge as the final destination;
- local call-side STT, dialogue and TTS on the reference Mac;
- a native preview and one-use authorization before every dial;
- PCMA/PCMU acceptable if the measured round trip passes;
- recording disabled at Fredo, gateway and carrier where configurable.

## Mandatory topology

```text
local conversation runtime
  <-> local SIP/RTP adapter
  <-> team SIP policy gateway
  <-> verified team carrier trunk
  <-> PSTN
  <-> consenting judge phone
```

The gateway remains in the judged path even when the Mac could reach the carrier directly. It contains the carrier credential and enforces policy when the local client is bypassed. It may relay RTP, but it must not record, transcribe, infer over or retain call audio.

## Candidate “aberrant” media stack

```text
Pipecat
  <-> local LiveKit room
  <-> LiveKit SIP
  <-> mandatory SIP policy gateway
  <-> registered team trunk
  <-> PSTN
```

This is a hypothesis, not the acceptance contract:

- Pipecat may compose VAD, interruption and local model adapters;
- LiveKit may provide the realtime room and supervision;
- LiveKit SIP may bridge local room media to the policy gateway;
- the gateway may use Asterisk or another policy-capable SIP implementation for carrier registration, codec/DTMF normalization and redacted CDR evidence.

The stack survives only if it meets the full qualification suite. Complexity that degrades latency, recovery or clean-machine bootstrap is removed.

## Fallback ladder

The mandatory gateway never disappears. Only the local media chain changes:

1. **Small local SIP/RTP adapter -> gateway.** Prefer this when it reaches the benchmark fastest.
2. **Pipecat -> LiveKit SIP -> gateway.** Keep the room when its supervision is useful and measured.
3. **Pipecat -> local Asterisk -> gateway.** Use for codec or SIP interop isolation if direct bridging fails.
4. **PyVoIP laboratory adapter -> gateway.** Diagnose registration, G.711, telephone events and RTP without making it the trusted judged abstraction.

Never keep two failing paths active during one debugging window. Promote a fallback only after it passes the same authorization, idempotency, gateway-policy and evidence tests as the hero path.

## Demo access and shared credential boundary

The Ginse `BootstrapPlan` carries a `LeaseClaim` with no dial authority, pre-bound to the device-key thumbprint created before `/run`, and a TTL of exactly 45 minutes from its signed issue time. This leaves at least 15 minutes for redemption after a conforming 30-minute cold bootstrap. After installation, Fredo proves possession of that key and redeems the claim idempotently with the separate demo-access authority.

The resulting gateway capability is bound to:

- `install_id`;
- device public key;
- native-helper authorization-key thumbprint;
- release SHA;
- policy digest;
- lease ID and expiry.

Its TTL is at most eight hours and never exceeds the published judging window. It is revocable per installation. The carrier master credential remains exclusively at the gateway; it never transits Ginse, Codex, the repository, logs or the judge's Mac.

BYOK later replaces the team-funded carrier binding, not the safety contract.

## Native consent and dial authorization

Before a transport sees a dial command, Fredo must:

1. normalize the destination to E.164;
2. apply the versioned destination policy;
3. create the canonical `DialRequest` and idempotency key;
4. render a Fredo-owned native `DialPreview` showing the full destination, verified caller identity, purpose, synthetic-voice disclosure, 180-second cap and policy/cost profile;
5. obtain one explicit local confirmation;
6. have the signed native helper create a server-verifiable, single-use `DialAuthorization` bound to the canonical hash of every request field, capability, policy, release, and authorization-key thumbprint.

The authorization expires within 60 seconds. The gateway verifies its helper signature and bindings and atomically consumes its unique ID with the dial idempotency key. Gateway capability plus device-key proof without this attestation cannot dial. Changing any request field requires a new preview and confirmation. Rejection, expiry, mutation, policy failure, or cancellation before `DIAL_COMMITTED` must produce zero SIP `INVITE`; cancellation after commit emits only the matching persisted `CANCEL`/`BYE`, never a new `INVITE`.

The remote participant must already have consented to the demo. The automated synthetic-voice disclosure is the first substantive outbound audio and starts no later than five seconds after connection.

## Server-enforced demo policy

The Mac checks policy for fast feedback; the gateway independently enforces it as the authority for carrier access.

| Control | Judged value |
| --- | --- |
| Gateway capability | at most 8 hours; never past judging-window end |
| Lease claim | exactly 45 minutes from signed issue time |
| Completed calls | judge profile: at most 3; qualification profile: at most 6 |
| Total dial attempts | judge profile: at most 6; qualification profile: at most 10 |
| Attempt rate | at most 2 per minute per installation |
| Global judging window | at most 30 completed calls and 60 dial attempts |
| Claim/capability issuance | 1 active per device key; at most 30 claims and 30 capabilities in the judging window |
| Per-destination attempts | judge profile: at most 6; qualification profile: at most 10 |
| Concurrency | 1 per installation; 3 globally |
| Duration | hard stop at 180 seconds |
| Spend | carrier-account cap at EUR 50 for the complete judging window |
| Eligible class | French mobile `+336` and `+337` only; no wildcard authorization |
| Dial allowlist | default deny; exact E.164 enrollment before capability issuance |
| Revocation | new attempts denied within 30 seconds |
| Recording | disabled at Fredo, gateway and carrier where configurable |

Emergency numbers, premium-rate numbers, short codes, anonymous calls, unsupported countries, non-allowlisted numbers, third-party targets and calls outside the judging protocol fail before a carrier attempt. `+336` and `+337` are outer eligibility filters only; every dialable number is an exact pre-enrolled E.164 entry for a consenting participant. Every gateway-accepted dial consumes per-install, per-destination, and global attempt quota before carrier signaling, even when it fails or never connects. A new install ID cannot reset device, destination, global, or spend ceilings. Voicemail is unsupported and Fredo hangs up without conducting the conversation if it is encountered. The policy dataset, both capability profiles, and their digest are versioned. The operator kill switch overrides every active capability.

## Durable call control

```text
DRAFT -> PREPARED -> AUTHORIZED -> DIAL_COMMITTED -> RINGING -> CONNECTED
                                      -> CANCEL_REQUESTED -> HANGUP_COMMITTED
                                      -> RECONCILING -> terminal state
```

Fredo persists the authorization consumption and `DIAL_COMMITTED` event before any external dial effect. It persists `CANCEL_REQUESTED` and `HANGUP_COMMITTED` before the matching SIP effect. The complete allowed-transition table in `GOAL.md` Section 8.2 governs ringing, answer, cancellation, hangup, and failure races. The gateway treats the Fredo idempotency key as an at-most-once call key across concurrent requests and retries.

If a timeout, process crash or network split makes carrier acceptance uncertain, Fredo enters `RECONCILING`. Recovery queries the gateway and carrier correlation for the existing key. It never emits a second dial automatically. Reconciliation ends in an observed terminal state or `UNKNOWN_TERMINAL`; any genuinely new attempt needs a new native authorization.

## Transport contract

Every candidate transport exposes the equivalent of:

```text
configure -> doctor -> dial -> events -> send_audio -> receive_audio -> hangup -> reconcile
```

Required normalized events include:

```text
trying, ringing, answered, media_started, dtmf, media_stopped,
hung_up, failed, cancelled, unknown_terminal
```

Every event carries the Fredo `call_id`, idempotency key, release/config identity and a monotonic local timestamp. Carrier and gateway correlation IDs are stored redacted where needed for recovery and evidence.

## Mac-first networking

Local inference and durable Fredo state run natively on the M4 Pro Mac. The selected installer may package isolated local services, but the clean-machine path cannot assume Docker Desktop, Homebrew, a prepared Python runtime or a manually configured SIP client.

All ports and advertised addresses are configuration, not hard-coded product contracts. The gateway has a stable public carrier-facing endpoint. WireGuard or another tunnel may be introduced when the chosen media path needs it, but the tunnel must not move model inference or transcripts off the Mac.

The separate Ginse provider and demo-access authority are control-plane services; neither belongs in the RTP path.

## Audio boundary

Public telephony commonly delivers 8 kHz G.711 audio. Local engines may expect 16 kHz or 24 kHz. Fredo measures the complete path:

```text
carrier 8 kHz
  -> gateway RTP transit
  -> local jitter buffer and resampler
  -> local voice engine
  -> local resampler and G.711 packetizer
  -> gateway RTP transit
  -> carrier
```

Moshi-MLX and every other speech-to-speech experiment remain feature-flagged until this PSTN round trip is intelligible and passes the latency, interruption and resource gates. No hosted STT, LLM, TTS or voice-agent endpoint may receive call audio.

## Qualification before the jury

The release candidate must complete 5/5 controlled calls on a separate team-owned installation with the `qualification` capability before the one jury call. The clean jury installation receives the `judge` profile. Both profiles are in the same signed policy bundle and use the exact candidate bytes. Each controlled call must:

- ring and connect with `ring_setup <= 20 s`;
- present the expected verified caller identity;
- disclose the synthetic voice within five seconds;
- remain connected for at least 90 seconds;
- exchange three scripted facts in both directions, judged intelligible by two independent listeners;
- handle one interruption and correlate DTMF/events;
- hang up cleanly and emit the structured result within five seconds of the terminal SIP event;
- create no recording at Fredo or the gateway.

The same candidate must also prove:

- repeating or concurrently submitting one idempotency key creates at most one carrier call;
- rejection, expiry, mutation and blocked destinations create zero carrier attempts;
- bypassing the local client does not bypass gateway quotas;
- revocation blocks a new attempt within 30 seconds;
- crash/timeout recovery never performs a blind redial;
- no secret or complete phone number appears in public logs or evidence.

The final jury call then completes once without an operator workaround using the exact promoted topology and bytes.

## Post-hackathon

- BYOK and per-install carrier accounts;
- broader destination and carrier support;
- inbound calls and hardware/SIM adapters;
- multi-call operation;
- lawful, explicit-consent recording features;
- general Linux/NVIDIA and non-Apple deployment profiles.
