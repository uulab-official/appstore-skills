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

### v0.5.0 — Extended platform integrations

- Amazon Appstore and Samsung Galaxy Store adapter profiles with current
  documentation references
- Project, build, simulator, and release-system evidence adapters

### v0.6.0 — Safe release-system handoff

- Optional dry-run handoff with build, simulator, and release evidence
- Publish-disabled handoff reports and explicit blocker gates

### v0.7.0 — Approval-gated handoff

- Explicit human approval records and `blocked` → `pending_approval` →
  `ready_for_handoff` states without automatic publishing
- Opt-in, read-only build and simulator capture evidence providers with field,
  path, timestamp, and image-signature checks

### v0.8.0 — Localization and copy governance

- Locale plans, terminology mappings, forbidden-term checks, and review-state
  preservation for localized store copy
- Store-copy experiment records with approval history and reversible variants

### Operational tooling

- Dependency-free Skill metadata validator
- Dependency-free generated-output manifest validator
- Manifest-declared PNG/SVG format and dimension validation
- SVG `viewBox` and optional PNG color-type metadata validation
- Dependency-free template-spec and adapter-map validators with regression tests
- Dependency-free project/build/simulator/release evidence-adapter validator
- Unit tests for path, manifest, and image metadata safety checks
- GitHub Actions validation on pushes and pull requests
- Manual GitHub Actions workflow for repository-relative store output

### v0.9.0 — Review workflow ergonomics

- Structured reviewer handoff summaries and diff-friendly package reports
  from stable manifest metadata
- Optional project-specific policy and accessibility review adapters with
  pending-visible, read-only states

### v1.0.0 — Evidence-backed review extensions

- Project-specific policy, accessibility, and privacy evidence templates
- Reviewer assignment and chronological decision-history ergonomics without
  automatic approval

## Next

### v1.1.0 — Review packet quality

- More granular reviewer scopes and evidence references across platform,
  localization, privacy, and accessibility review
- Baseline-aware reviewer assignment deltas for status, ownership, scope,
  evidence, and history changes
- Optional project-owned evidence integrations that remain user-approved and
  read-only

## Longer term

- More localization and terminology tooling
- Provider integrations for project-specific, user-approved evidence sources

## Scope rule

Keep generated assets factual, reversible, and separate from source projects.
Verify unstable platform requirements at execution time and never turn a
design draft into a submission claim without evidence and human review.
