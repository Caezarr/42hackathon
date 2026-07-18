# Hackathon plan

## Goal

Prove that a fresh machine can become a private Codex-controlled phone appliance, place one consented call through infrastructure owned by the operator, and return a structured result.

## Must-win path

The judged MVP has one reference path. Everything else is stretch work.

| Area | Hackathon reference |
| --- | --- |
| Demo machine | Apple Silicon Mac with 24 GB RAM and at least 40 GB free disk |
| Local inference | Native Metal-capable runtime behind the local OpenAI-compatible contract |
| Media | Pipecat plus self-hosted LiveKit |
| Development transport | Browser/WebRTC |
| Public edge | One operator-owned Linux host with a stable public IP, TLS, LiveKit, LiveKit SIP, and WireGuard to the Mac |
| PSTN transport | One operator-owned registered SIP trunk and verified caller number terminating on that edge |
| Codex integration | Local MCP with confirmation, status, cancellation, and result |
| Runtime distribution | One tested local bootstrap path; no Kubernetes |
| Marketplace proof | One Ginse listing for the team's demo installation, verified against its own public `/run` |

The bootstrap release budget is at most 20 GB of compressed downloads for the reference profile. P1 must replace that budget with an exact signed artifact manifest before the installer can claim reproducibility.

Required on the reference machine:

- current macOS on Apple Silicon;
- Docker Desktop for containerized state and media services;
- enough internet access for the explicit first-run downloads;
- an operator-owned public Linux edge connected to the Mac over WireGuard;
- a controlled SIP test account, verified caller number, domain, and TLS certificates;
- no separate hosted STT, call-side LLM, or TTS provider account or key beyond the Codex interface.

Stretch goals: Linux CPU/NVIDIA compute packaging, GSM-to-SIP, Android Bluetooth, air-gap bundles, automatic rollback, and recordings.

## Definition of done

The hackathon succeeds when another participant can:

1. clone this repository on a supported clean machine;
2. inspect the exact downloads, sizes, and licenses;
3. bootstrap a selected local compute profile;
4. complete a local browser voice loop;
5. configure one owned phone transport;
6. ask Codex to start a consented call;
7. confirm the call and receive its structured result;
8. restart the appliance;
9. place a second call without downloading a model or using a hosted call-side AI API;
10. verify the team's own per-install Ginse listing against the same secured instance.

## Milestones

### P0 — Product contract

- [x] Self-hosted ownership boundary
- [x] No spoofing or central broker decision
- [x] First-run bootstrap contract
- [x] Transport matrix
- [x] Initial upstream pins

### P1 — Reproducible bootstrap

- [ ] Hardware and disk detection
- [ ] Exact runtime image digests, model revisions, hashes, sizes, and licenses
- [ ] Signed release manifest
- [ ] Resumable content-addressed downloads
- [ ] Reference Apple Silicon resolution
- [ ] Offline doctor command
- [ ] Linux CPU and Linux NVIDIA resolution *(stretch)*
- [ ] Rollback to the previous generation *(stretch)*

Exit evidence: the signed manifest lists exact artifacts and sizes; `doctor --offline` succeeds after bootstrap; rerunning bootstrap transfers zero artifact bytes.

### P2 — Local voice loop

- [ ] Pipecat worker
- [ ] LiveKit browser room
- [ ] Local STT
- [ ] Local LLM
- [ ] Local TTS
- [ ] Interruption and latency measurement

Exit evidence: a browser conversation completes locally with captured STT, first-token, first-audio, and interruption timings.

### P3 — One real phone call

- [ ] Transport interface
- [ ] User-owned SIP path
- [ ] Destination and caller-identity checks
- [ ] Call events and hangup
- [ ] Structured result
- [ ] GSM-to-SIP or Android Bluetooth proof of concept *(stretch)*

Exit evidence: one controlled number receives a call from the verified operator identity, bidirectional audio works, hangup is reported, and a structured result is stored locally.

### P4 — Codex MCP

- [ ] `doctor`
- [ ] `call_start`
- [ ] confirmation gate
- [ ] `call_status`
- [ ] `call_cancel`
- [ ] `call_result`

Exit evidence: Codex starts a confirmed call through MCP, polls its durable operation, can cancel it, and reads the terminal result without receiving raw call audio.

### P5 — Packaging and optional Ginse demo

- [ ] Reproducible Compose bundle
- [ ] Clean-machine installation guide
- [ ] Backup and restore *(stretch)*
- [ ] Per-install Ginse adapter
- [ ] Team-owned Ginse demo endpoint for judges

Exit evidence: Ginse verification passes for the team-owned demo manifest and `/run`; the listing points only to that installation and the local MCP path still works with Ginse disabled.

## Demo script

1. Show that no hosted call-side STT, LLM, or TTS key is configured.
2. Run `doctor --offline`.
3. Ask Codex to call a controlled destination.
4. Show the confirmation and policy decision.
5. Watch the local call state and transcript.
6. End the call and show the structured result.
7. Repeat without any dependency download.

## Risks to burn down first

- end-to-end audio latency;
- SIP/RTP networking on laptop environments;
- model download size and startup time;
- Bluetooth HFP/SCO device compatibility;
- accidental claims that planned commands already work;
- legal and abuse risk around phone destinations and recording.
