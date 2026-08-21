# Roadmap

The roadmap describes repository scope, not an automatic promise of release
tags or store submission support. Changes are developed on `main` in small,
reviewable commits.

## Completed

### v0.1.0 — Core store assets

- App icon workflow
- App Store and Google Play screenshot workflow
- Integrated asset orchestration
- Shared brand context and output contract

### v0.2.0 — Web and Google Play surfaces

- Google Play-focused asset workflow
- Favicon workflow with optional web integration
- OG image workflow with optional metadata integration

### v0.3.0 — Copy, locales, and release review

- Evidence-backed store copy workflow
- Localization workflow for copy and visual assets
- Pre-submission release-check workflow

### v0.4.0 — Asset and release automation

- Reusable promotional and feature-graphic template contracts
- GitHub Actions annotations and Step Summary for release reports
- Apple, Google Play, and Web platform adapter maps

### Operational tooling

- Dependency-free Skill metadata validator
- Dependency-free generated-output manifest validator
- Manifest-declared PNG/SVG format and dimension validation
- SVG `viewBox` and optional PNG color-type metadata validation
- Dependency-free template-spec and adapter-map validators with regression tests
- Unit tests for path, manifest, and image metadata safety checks
- GitHub Actions validation on pushes and pull requests
- Manual GitHub Actions workflow for repository-relative store output

## Next

### v0.5.0 — Extended platform integrations

- Additional platform-specific adapters beyond the shared Apple, Google Play,
  and Web map
- Build, simulator, and release-system evidence adapters

## Longer term

- More localization and terminology tooling
- Store-copy experiments with approval history
- Safe integrations with build, simulator, and release systems
- Optional submission handoff checks without automatic publishing

## Scope rule

Keep generated assets factual, reversible, and separate from source projects.
Verify unstable platform requirements at execution time and never turn a
design draft into a submission claim without evidence and human review.
