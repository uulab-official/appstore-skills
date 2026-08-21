# appstore-skills

App Store and Google Play asset-generation skills for AI coding agents.

Turn an app project into a coherent, production-ready store asset package by
combining project analysis, brand extraction, marketing direction, asset
generation, platform adaptation, and QA.

> This repository contains agent instructions, not a standalone image generator
> or a replacement for Apple's or Google's submission tools.

## What is included

| Skill | Purpose |
| --- | --- |
| [`app-icon`](skills/app-icon/SKILL.md) | Analyze an app and create a small-size legible icon direction and export plan. |
| [`app-store-screenshots`](skills/app-store-screenshots/SKILL.md) | Turn real app screens into platform-specific marketing screenshot sets. |
| [`app-store-assets`](skills/app-store-assets/SKILL.md) | Orchestrate the complete icon, screenshot, promotional, and metadata workflow. |
| [`play-store-assets`](skills/play-store-assets/SKILL.md) | Prepare a Google Play-focused package with Android-specific outputs and QA. |
| [`favicon`](skills/favicon/SKILL.md) | Create a compact browser, bookmark, and touch-icon family for web projects. |
| [`og-image`](skills/og-image/SKILL.md) | Create branded link-preview images with grounded page metadata. |
| [`store-copy`](skills/store-copy/SKILL.md) | Draft evidence-backed App Store and Google Play listing copy. |
| [`localization`](skills/localization/SKILL.md) | Adapt copy and visual assets for target locales. |
| [`release-check`](skills/release-check/SKILL.md) | Audit a store asset package before human submission review. |

The skills share a `brand-context.yml` contract so the icon, screenshots, and
other store assets feel like one product.

New here? Start with [`docs/getting-started.md`](docs/getting-started.md).
Use [`docs/skill-map.md`](docs/skill-map.md) to choose the right workflow and
[`docs/quality-bar.md`](docs/quality-bar.md) for acceptance criteria, and
[`docs/roadmap.md`](docs/roadmap.md) to see what is implemented next.

## Quick start

Copy the skill folders into the skill directory used by your AI coding agent,
or point the agent at this repository if it supports repository-local skills.
Then run one of these prompts from an app project:

```text
$app-icon

$app-store-screenshots

$app-store-assets

$play-store-assets

$favicon

$og-image

$store-copy

$localization

$release-check
```

The agent should inspect the app project before proposing a direction. Provide
an existing logo, brand guide, simulator screenshots, or a preferred output
directory when available.

## Expected workflow

```text
App project
    -> project and brand analysis
    -> shared brand context
    -> icon direction + screenshot story
    -> platform adaptations
    -> QA and delivery report
```

The workflow deliberately keeps the real app UI intact in screenshots. It may
add copy, device framing, backgrounds, and layout treatment, but it must not
invent or materially alter product screens without clearly labeling the result
as a concept.

## Output contract

The integrated skill writes only the directories that have deliverables. A
typical package looks like this:

```text
store-assets/
├── brand-context.yml
├── manifest.yml
├── icon/
│   ├── icon-master.png
│   ├── icon-1024.png
│   └── ...
├── screenshots/
│   ├── apple/
│   └── google-play/
├── promotional/
├── feature-graphic/
├── web-assets/
│   ├── favicon/
│   └── og/
├── metadata/
│   └── store-copy.en-US.yml
├── locales/
├── release-report.md
└── QA.md
```

Exact platform sizes and submission rules must be checked against the current
official Apple and Google documentation at execution time.

## Example output

[`examples/demo-store-assets/`](examples/demo-store-assets/) contains a real
review fixture with generated icon exports, favicon, OG SVG/PNG, store-copy
draft, manifest, QA, and release report. It is deliberately marked as a demo
and blocked because this repository has no real app screens. Use it to inspect
the output contract and validator behavior, not as a production submission.

## Scope and non-goals

This project focuses on the last-mile design and packaging work after an app
exists. It does not submit builds, manage store accounts, fabricate app UI,
guarantee store approval, or replace legal and accessibility review.

## Status

The current public milestone is `v0.9.0` with operational
validation tooling:

- app icon generation workflow
- App Store and Google Play screenshot workflow
- integrated asset orchestration workflow
- shared brand context and output contracts
- Google Play-focused asset workflow
- favicon generation and optional web integration
- OG image generation and optional metadata integration
- store listing copy workflow
- localization workflow for copy and visual assets
- pre-submission release-readiness audit
- manifest-declared PNG/SVG dimensions and format validation
- SVG `viewBox` and optional PNG color-type validation
- reusable promotional and Google Play feature-graphic template contracts
- GitHub Actions annotations for release-report blockers and warnings
- Apple, Google Play, Web, Amazon Appstore, and Samsung Galaxy Store adapter
  maps with execution-time checks
- project, build, simulator, and release evidence adapter maps
- safe dry-run release handoff reports with publish disabled
- explicit approval records and approval-gated handoff states
- opt-in, read-only build and simulator evidence providers
- opt-in freshness gates for build and simulator evidence in release handoffs
- optional current-project Git revision binding for build evidence
- optional requested-platform binding for build and simulator evidence
- optional requested-locale binding for simulator evidence
- optional requested-device-family binding for simulator evidence
- optional Cartesian scope-coverage gates for simulator evidence
- duplicate source-capture path checks that prevent relabeled files from
  masquerading as multiple scope combinations
- locale plans and terminology QA that preserve review blockers
- reversible store-copy experiment records with approval history
- diff-friendly reviewer handoff summaries with manifest and reviewer-assignment baselines
- opt-in policy, accessibility, and privacy review adapters with pending-visible states
- terminal adapter evidence cross-checked against assigned reviewer coverage
- opt-in freshness gates for terminal adapter evidence in review handoffs
- reviewer assignment records with reviewer scopes, adapter coverage, deterministic status, evidence references, and chronological decision history

The repository also includes deterministic, dependency-free checks for skill
metadata and generated output manifests:

```bash
python scripts/validate_skills.py
python scripts/validate_docs.py
python scripts/validate_template_specs.py \
  skills/app-store-assets/references/promotional-template.yml \
  skills/app-store-assets/references/feature-graphic-template.yml
python scripts/validate_adapter_specs.py \
  skills/app-store-assets/references/platform-adapters.yml
python scripts/validate_evidence_specs.py \
  skills/app-store-assets/references/evidence-adapters.yml
python scripts/validate_provider_specs.py \
  skills/app-store-assets/references/evidence-providers.yml
python scripts/validate_release_approval.py \
  skills/app-store-assets/references/release-approval.yml
python scripts/validate_localization_specs.py \
  ./store-assets/localization-plan.yml \
  ./store-assets/terminology.yml \
  --package-root ./store-assets
python scripts/validate_copy_experiments.py \
  ./store-assets/metadata/copy-experiments.yml \
  --package-root ./store-assets
python scripts/generate_review_handoff.py \
  --package-root ./store-assets \
  --adapter-file ./skills/release-check/references/review-adapters.yml \
  --adapter policy-review \
  --adapter accessibility-review \
  --adapter privacy-review \
  --max-evidence-age-days 30 \
  --output ./store-assets/review-handoff.md
python scripts/validate_review_adapter_specs.py \
  skills/release-check/references/review-adapters.yml
python scripts/validate_review_assignments.py \
  --adapter-file ./skills/release-check/references/review-adapters.yml \
  ./store-assets/review-assignment.yml \
  --adapter policy-review \
  --adapter accessibility-review \
  --adapter privacy-review
python scripts/prepare_release_handoff.py \
  --project-root ./my-app \
  --output-root ./my-app/store-assets \
  --platform apple \
  --platform google-play \
  --locale en-US \
  --device-family iphone \
  --require-scope-coverage \
  --provider-file ./skills/app-store-assets/references/evidence-providers.yml \
  --provider build-record \
  --provider simulator-source-captures \
  --max-evidence-age-days 30 \
  --require-current-revision \
  --approval-file ./my-app/store-assets/release-approval.yml \
  --format summary
python -m unittest discover -s tests
python scripts/validate_store_output.py ./store-assets
python scripts/annotate_release_report.py ./store-assets/release-report.md
```

The `Validate store output` GitHub Actions workflow can run the same package
check manually against a repository-relative output directory.

See [`docs/roadmap.md`](docs/roadmap.md) for completed milestones and the next
operational automation scope.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). Contributions should improve the
agent workflow, preserve factual fidelity to the source app, and keep
platform-specific rules current without hard-coding unstable requirements.

## License

MIT. See [`LICENSE`](LICENSE).
