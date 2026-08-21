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

## Scope and non-goals

This project focuses on the last-mile design and packaging work after an app
exists. It does not submit builds, manage store accounts, fabricate app UI,
guarantee store approval, or replace legal and accessibility review.

## Status

The current public milestone is `v0.3.0`:

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

The repository also includes deterministic, dependency-free checks for skill
metadata and generated output manifests:

```bash
python scripts/validate_skills.py
python -m unittest discover -s tests
python scripts/validate_store_output.py ./store-assets
```

The next roadmap milestone focuses on operational maturity:

- deterministic image and metadata validators
- richer promotional and feature-graphic templates
- release report integrations for CI and pull requests
- more platform-specific adapters

Later candidates include richer promotional assets, release checklists, and
platform-specific automation where the target agent can safely support it.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). Contributions should improve the
agent workflow, preserve factual fidelity to the source app, and keep
platform-specific rules current without hard-coding unstable requirements.

## License

MIT. See [`LICENSE`](LICENSE).
