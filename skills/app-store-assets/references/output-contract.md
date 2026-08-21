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
assumptions: []
```

Use paths relative to the output root. Keep statuses honest: `draft`,
`review`, `verified`, or `blocked`.

### `QA.md`

Document the generated date, source evidence, official platform documentation
checked, image validation, UI-fidelity review, copy and locale review,
assumptions, blockers, and next steps.

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
├── og/
├── web-assets/
│   └── favicon/
├── metadata/
│   └── store-copy.en-US.yml
├── locales/
├── release-report.md
└── QA.md
```

Keep generated output separate from the source app and never silently delete
or overwrite a previous run. If a rerun is needed, use a new run directory or
obtain explicit permission to replace files.
