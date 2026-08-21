---
name: app-store-assets
description: Orchestrate a complete App Store and Google Play asset package from an app project, including project and brand analysis, shared context, app icon, marketing screenshots, optional promotional assets, metadata support, platform adaptation, and QA. Use when a user wants the full store-ready asset workflow rather than one individual asset.
---

# App Store assets

Coordinate the complete last-mile asset workflow for an app. Treat the app
icon, screenshots, promotional graphics, and metadata as one brand system, and
preserve a clear record of what was discovered, generated, verified, or left
for the user.

## Run the workflow

### 1. Inspect the project and establish the run

Choose an output directory without overwriting existing work. Prefer
`store-assets/`; if it already contains generated files, create a dated run
directory or ask the user before replacing anything. Inspect:

- product and brand sources (`README.md`, app metadata, theme files, logos)
- actual app screens and navigation
- existing icon and store assets
- target platforms, locales, device families, and requested deliverables

Create an evidence log with source paths and separate confirmed facts from
assumptions. Use
[`references/evidence-adapters.yml`](references/evidence-adapters.yml) to
separate project, build, simulator, and release evidence. Read
[`references/evidence-adapters.md`](references/evidence-adapters.md) and keep
an adapter `blocked` when the app, build, or real screen capture is missing.

### 2. Create shared brand context

Write `brand-context.yml` before generating assets. Keep it factual and reuse
it for every child workflow:

```yaml
schema_version: 1
brand:
  name: Product name
  personality: [friendly, modern]
product:
  category: product category
  audience: primary audience
  value_proposition: evidence-backed value proposition
  core_features: []
visual:
  style: minimal
  typography: modern sans serif
  radius: rounded
  density: spacious
colors:
  primary: "#000000"
  secondary: "#FFFFFF"
  background: "#F5F5F5"
evidence: []
assumptions: []
```

If a context file already exists, preserve its confirmed values and record
any proposed changes rather than silently changing the brand.

### 3. Plan and confirm the asset set

Create a plan covering:

- icon directions and selected export family
- screenshot story, source screens, copy, locales, and device families
- optional promotional, feature graphic, OG, or metadata deliverables
- current platform rules to verify
- output paths and QA owner

Ask for approval at this checkpoint when the user is available. If the request
explicitly asks for a complete run without review, choose conservative defaults
and record them in `manifest.yml`.

### 4. Run the child workflows

Read and follow the repository-local skills:

- [`../app-icon/SKILL.md`](../app-icon/SKILL.md) for icon strategy,
  generation, evaluation, and export
- [`../app-store-screenshots/SKILL.md`](../app-store-screenshots/SKILL.md) for
  real-screen discovery, storyboarding, composition, and platform exports

Pass the same `brand-context.yml`, evidence map, output root, target locales,
and platform scope to both. Do not let a screenshot workflow invent an icon
palette or let an icon workflow infer unsupported product claims.

### 5. Add optional assets only when requested

Generate promotional art, feature graphics, OG images, or store metadata only
when the user requests them or the project explicitly includes them in scope.
For promotional and feature-graphic work, start from the reusable contracts in
[`references/promotional-template.yml`](references/promotional-template.yml)
and [`references/feature-graphic-template.yml`](references/feature-graphic-template.yml).
Fill their content and visual slots from the app evidence before rendering;
do not treat a blank template as an approved design. Read
[`references/marketing-template-qa.md`](references/marketing-template-qa.md)
before exporting channel variants. Keep platform-specific content in separate
folders. Treat copy and claims as product content: ground them in project
evidence, preserve locale, and flag missing translations or approvals.

For web outputs, read [`../favicon/SKILL.md`](../favicon/SKILL.md) and
[`../og-image/SKILL.md`](../og-image/SKILL.md) instead of improvising browser or
social-preview conventions. For a Google Play-only run, prefer
[`../play-store-assets/SKILL.md`](../play-store-assets/SKILL.md) so Android
screens, adaptive-icon sources, and Play-specific QA remain explicit.

For listing text, read [`../store-copy/SKILL.md`](../store-copy/SKILL.md). For
additional locales, read [`../localization/SKILL.md`](../localization/SKILL.md)
after the source-locale assets are approved. Run
[`../release-check/SKILL.md`](../release-check/SKILL.md) over the final output
before calling the package ready for human submission review.

### 6. Verify platform rules and package outputs

Check current official Apple and Google documentation for every platform and
device family in scope. Requirements can change; never use remembered sizes or
submission rules as proof of readiness.

For every requested platform, fill the adapter map in
[`references/platform-adapters.yml`](references/platform-adapters.yml) and
follow [`references/platform-adapters.md`](references/platform-adapters.md).
Keep source masters separate from platform outputs, name each transformation,
and leave the adapter in `review` or `blocked` until the current platform
documentation and source-fidelity checks are recorded.

Write `manifest.yml` with one record per deliverable:

```yaml
schema_version: 1
project: Example App
generated_at: "2026-01-01T00:00:00Z"
platforms: [apple, google-play]
assets:
  - path: icon/icon-master.png
    kind: app-icon
    platform: shared
    status: review
    source: generated from direction A1
    checks: [square, small-size-review]
assumptions: []
```

Use statuses such as `draft`, `review`, `verified`, and `blocked`. Only mark
an asset `verified` when its source fidelity, dimensions, and current platform
requirements have actually been checked.

For every rendered promotional or feature-graphic image, declare `format` and
`dimensions` in the manifest. Validate filled template specs with
`python scripts/validate_template_specs.py <template.yml>` before rendering.

### 7. Perform final QA and deliver

Write `QA.md` and summarize:

- generated assets and their paths
- selected icon direction and screenshot story
- source screens and evidence used
- platform and locale coverage
- checks passed, assumptions, and blockers
- exact next steps required before submission

Use the output layout below, omitting empty directories:

```text
store-assets/
├── brand-context.yml
├── manifest.yml
├── icon/
├── screenshots/
│   ├── source/
│   ├── apple/
│   └── google-play/
├── promotional/
├── feature-graphic/
├── web-assets/
│   ├── favicon/
│   └── og/
├── metadata/
└── QA.md
```

## Quality gates

Do not call the package production-ready when any of these is true:

- the icon or screenshot copy is unsupported by project evidence
- final screenshots use synthetic UI instead of actual app screens
- a requested locale or platform has no output or an explicit blocker
- an asset is clipped, unreadable, incorrectly colored, or mislabeled
- current platform requirements were not checked
- existing outputs were overwritten without permission

For the detailed output and status contract, read
[references/output-contract.md](references/output-contract.md).
