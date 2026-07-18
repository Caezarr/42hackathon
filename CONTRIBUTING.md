# Contributing

Thanks for helping build Agent Call during the hackathon.

## Before starting

Read:

1. [`README.md`](README.md)
2. [`AGENTS.md`](AGENTS.md)
3. [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
4. the active milestone in [`docs/HACKATHON-PLAN.md`](docs/HACKATHON-PLAN.md)

## Development principles

- Prefer one working end-to-end path over many unverified providers.
- Keep local-first defaults and make external services optional.
- Separate compute profiles from phone transports.
- Never commit secrets, phone numbers, recordings, transcripts, model weights, or generated manifests.
- Pin dependencies and record their licenses.
- Do not weaken destination policy or confirmation to make a demo easier.

## Branch and pull request flow

- Branch from `main`.
- Keep commits small and named after the delivered outcome.
- Explain what is implemented versus mocked.
- Include commands and outputs used for verification.
- Use draft pull requests until the demo path has been exercised.

## Definition of a valid contribution

A change is ready when:

- its behavior and ownership boundary are documented;
- relevant tests pass;
- failure leaves the installation in a recoverable state;
- it does not add an unpinned network dependency;
- it respects the safety constraints in [`SECURITY.md`](SECURITY.md).
