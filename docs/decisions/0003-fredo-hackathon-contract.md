# ADR 0003: Fredo hackathon contract

Status: accepted on 2026-07-18; one-prompt bootstrap and judged demo access amended by [ADR 0004](0004-one-prompt-demo-access.md).

## Context

The first documentation pass diverged between an administrative-call assistant and a generic phone appliance. It also treated Ginse as optional and assumed production-grade distribution before the hackathon path existed.

The product owner clarified the intended project:

- generic phone calls from Codex;
- autonomous local execution with as few APIs as possible;
- Ginse as the essential hackathon entry point;
- a real call to the jury as the wow moment;
- Mac-first implementation;
- an intentionally ambitious local stack;
- voice cloning as a nice-to-have;
- first installation only needs to work on the team machine;
- Fredo as the working name.

## Decision

The product is named **Fredo** for the hackathon.

Fredo is distributed as an installable Codex plugin with a skill. The local `fredo` CLI and daemon are the canonical implementation contract. A STDIO MCP adapter is optional and must remain a thin wrapper.

Ginse is mandatory. Its single public action returns a pinned `BootstrapPlan` containing an opaque, one-time `LeaseClaim` with no dial authority; Codex applies the plan locally. Ginse never routes or authorizes calls and receives no destination, intent, caller identity, audio, transcript, model state, summary, or result.

The team operates a minimal public HTTPS Fredo provider for that action. This required bootstrap service is separate from the mandatory judged SIP policy gateway. The original Codex task invokes the newly installed `fredo` CLI directly through `doctor`, native call confirmation, and the first call. A later fresh task verifies that Codex discovers the installed plugin; no handoff may block or replace the same-task first run.

The hackathon reference is the inspected Apple M4 Pro Mac with 24 GB RAM. Live-call STT, dialogue inference, TTS, transcript processing, confirmation, and durable Fredo state run locally. Codex may use its hosted control plane for the initial prompt and bootstrap orchestration; raw call audio never enters it.

The success path calls the real phone of a consenting jury member through the team's policy-enforced gateway, carrier account, and verified caller identity. Only the gateway may hold the shared carrier master credential. The local runtime redeems the Ginse-delivered claim for a short-lived, install-bound gateway capability.

Pipecat, LiveKit, LiveKit SIP, Asterisk, PyVoIP, SQLite, Python versions, Docker, Metal/MLX adapters, and the envelope algorithm are non-normative architecture hypotheses. They may be replaced by any implementation that preserves the Goal invariants and passes its gates. Moshi-MLX and voice cloning remain experiments off the critical path.

The spoken candidate “Miro 2.5” remains unidentified. It is a research item, not an accepted dependency.

## Consequences

- [`GOAL.md`](../../GOAL.md) becomes the only completion contract.
- [`ROADMAP.md`](../../ROADMAP.md) becomes the canonical ordered plan.
- Ginse verification and publication happen before the project can pass.
- The active call path does not depend on Ginse after claim redemption, but it does depend on the demo gateway and carrier.
- No hosted call-side STT, dialogue, TTS, or voice-agent API is part of the reference demo.
- The initial installer supports only the reference clean-machine fixture.
- Remote phone speech is untrusted and cannot invoke tools, mutate policy, authorize another call, change destination, or request a secret.
- Native assets, manifests, SBOM, provenance, OCI images, and the Ginse version must form the signed release-equivalence graph required by the Goal.
- Postgres, Valkey, multi-machine packaging, rollback and air-gap work are deferred.
- No product claim is made until its corresponding evidence gate passes.
