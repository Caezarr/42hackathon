# Contributing

Thanks for helping build Fredo during the hackathon.

## Before starting

Read:

1. [`README.md`](README.md)
2. [`AGENTS.md`](AGENTS.md)
3. [`GOAL.md`](GOAL.md)
4. [`ROADMAP.md`](ROADMAP.md)
5. [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)

## Development principles

- Treat [`GOAL.md`](GOAL.md) as the normative product and acceptance contract. Architecture notes and ADRs may select mechanisms but may not weaken its invariants or gates.
- Prefer one working end-to-end path over many unverified providers.
- Keep the live-call runtime local; Ginse is mandatory for discovery/bootstrap and the carrier is mandatory for PSTN.
- Keep the judged team-funded gateway path separate from post-hackathon BYOK work.
- Separate compute profiles from phone transports.
- Never commit secrets, phone numbers, recordings, transcripts, model weights, or unredacted evidence. Version schemas, safe manifests, digests, licences and provenance needed to reproduce a release.
- Pin dependencies and record their licenses.
- Do not weaken destination policy or confirmation to make a demo easier.
- Attach the matching `GOAL.md` evidence to every completed milestone.

## Branch and pull request flow

- Branch from `main`.
- Keep commits small and named after the delivered outcome.
- Explain what is implemented versus mocked.
- Include commands and outputs used for verification.
- Use draft pull requests until the demo path has been exercised.
- Do not promote a Ginse or Git release whose bytes differ from the accepted candidate.

## Definition of a valid contribution

A change is ready when:

- its behavior and ownership boundary are documented;
- relevant tests pass;
- failure leaves the installation in a recoverable state;
- it does not add an unpinned network dependency;
- it respects the safety constraints in [`SECURITY.md`](SECURITY.md).
