# Output contract

The integrated skill should produce an auditable package, not only a folder of
images. Omit directories that have no requested deliverables.

## Required files

### `brand-context.yml`

Store the shared product and visual context. Include `evidence` and
`assumptions` so later runs can distinguish discovery from invention.

### `manifest.yml`

Record one asset per entry:

```yaml
schema_version: 1
project: Example App
generated_at: "2026-01-01T00:00:00Z"
platforms: [apple, google-play]
assets:
  - path: screenshots/apple/iphone/01-hook.png
    kind: marketing-screenshot
    platform: apple
    device_family: iphone
    locale: en-US
    status: review
    source: screenshots/source/home.png
    checks: [factual-copy, ui-fidelity, dimensions]
    format: png
    dimensions: 1290x2796
    color_type: rgba
assumptions: []
```

Use paths relative to the output root. Keep statuses honest: `draft`,
`review`, `verified`, or `blocked`. For image records, `format` and
`dimensions` make the file contract machine-checkable. The repository
validator currently supports `png` and `svg`; SVG dimensions are checked
against the numeric `viewBox`, and PNG `color_type` is optional.

### `QA.md`

Document the generated date, source evidence, official platform documentation
checked, image validation, UI-fidelity review, copy and locale review,
assumptions, blockers, and next steps.

### Promotional and feature-graphic templates

When either surface is in scope, preserve the filled template spec next to the
rendered output. It must record the working canvas, safe area, layout zones,
copy limits, hero asset, claims, evidence, assumptions, and output paths. Use
the repository templates as starting points:

- [`promotional-template.yml`](promotional-template.yml) for shared campaign
  compositions
- [`feature-graphic-template.yml`](feature-graphic-template.yml) for a Google
  Play-oriented working artboard

The template validator checks the structural contract; platform acceptance must
still be verified against current official documentation at execution time.

When more than one platform is in scope, preserve a filled adapter map using
[`platform-adapters.yml`](platform-adapters.yml). It must identify the shared
source master, output root, named transformations, requested surfaces, and
execution-time checks for each platform.

When the app, build, simulator, or release system is available, preserve an
evidence map using [`evidence-adapters.yml`](evidence-adapters.yml). It must
separate project facts, build identity, real screen captures, and release
approvals. Missing build or simulator evidence is a blocker for claims that
depend on it.

Optionally preserve the read-only handoff result as `release-handoff.yml`.
Keep `mode: dry-run` and `publish_status: not-run`; a handoff report is a
review aid, not a submission or upload record.

## Recommended layout

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
│   └── store-copy.en-US.yml
├── locales/
├── release-report.md
└── QA.md
```

Keep generated output separate from the source app and never silently delete
or overwrite a previous run. If a rerun is needed, use a new run directory or
obtain explicit permission to replace files.
