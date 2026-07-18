# ADR 0003: Fredo hackathon contract

Status: accepted on 2026-07-18.

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

Ginse is mandatory. Its single public action returns a pinned `BootstrapPlan`; Codex applies that plan locally. Ginse never routes calls or receives call data.

The team operates a minimal public HTTPS Fredo provider for that action. This required bootstrap service is a separate role from the optional public telecom edge. Because a newly installed Codex plugin is loaded by a fresh task, the judged first-use flow includes an explicit task handoff after `fredo doctor`.

The hackathon reference is the inspected Apple M4 Pro Mac with 24 GB RAM. Live-call STT, LLM and TTS run locally. The judged flow uses Codex CLI with a local OSS provider.

The success path calls the real phone of a consenting jury member through an operator-owned SIP trunk and verified caller identity.

The target stack may combine Pipecat, LiveKit, LiveKit SIP and Asterisk, with simpler evidence-backed fallbacks. SQLite WAL is the MVP state store. Moshi-MLX and voice cloning are experimental.

The spoken candidate “Miro 2.5” remains unidentified. It is a research item, not an accepted dependency.

## Consequences

- [`GOAL.md`](../../GOAL.md) becomes the only completion contract.
- [`ROADMAP.md`](../../ROADMAP.md) becomes the canonical ordered plan.
- Ginse verification and publication happen before the project can pass.
- The call path remains usable after Ginse becomes unavailable post-install.
- No hosted STT, LLM, TTS or voice-agent API is part of the reference demo.
- The initial installer supports only the reference Mac.
- Postgres, Valkey, multi-machine packaging, rollback and air-gap work are deferred.
- No product claim is made until its corresponding evidence gate passes.
