---
name: play-store-assets
description: Prepare a Google Play-focused asset package from an app project, including the app icon, phone and tablet screenshots, feature graphic, optional promotional art, grounded listing copy support, and Play Console QA. Use when the target is Google Play only or when Android-specific store assets need separate treatment from Apple deliverables.
---

# Google Play assets

Prepare the Android-specific store package while keeping the real app UI and
product claims faithful to the source project. Use this skill for a Google
Play-only run or for the Play branch of a multi-platform release; use
`app-store-assets` when one workflow should coordinate Apple and Google outputs.

## Discover the Android product

Inspect:

- `README.md`, Android metadata, package name, app label, and launcher icon
- `AndroidManifest.xml`, Gradle configuration, adaptive icon resources, and
  existing Play assets
- routes and actual Android screens, emulator captures, or supplied device
  screenshots
- `brand-context.yml`, theme tokens, locale files, and product copy

Record source paths and distinguish shipped Android behavior from features
mentioned only in plans or code comments.

## Workflow

### 1. Define the Play listing scope

Confirm the requested deliverables, locales, device families, and whether the
run includes:

- launcher/store icon
- phone screenshots
- tablet screenshots
- feature graphic
- promotional graphics or video cover art
- store listing copy or metadata support

Do not create an empty placeholder for an unrequested surface. Write a scope
plan and ask for approval when the user is available.

### 2. Build the shared context

Reuse the existing `brand-context.yml` whenever possible. If it does not
exist, create it before generating assets and include evidence and assumptions.
Do not let the Play-specific treatment drift from the approved app icon or
cross-platform screenshot story without recording why.

### 3. Build the asset set

Use the following source-to-output mapping:

| Deliverable | Source | Required fidelity |
| --- | --- | --- |
| Store icon | Approved icon direction and Android resources | Preserve the product mark and safe area. |
| Phone screenshots | Real Android/emulator screens | Preserve UI, data meaning, and feature behavior. |
| Tablet screenshots | Real responsive tablet screens when available | Do not fake tablet layout from a phone crop. |
| Feature graphic | Brand context and listing message | Communicate the product without unsupported claims. |
| Promotional art | User brief and approved brand assets | Keep campaign claims and locale explicit. |

For screenshots, reuse the storyboard discipline from
[`../app-store-screenshots/SKILL.md`](../app-store-screenshots/SKILL.md), but
capture Android-specific navigation, system bars, typography, and responsive
layout. For the icon, reuse the evaluation discipline from
[`../app-icon/SKILL.md`](../app-icon/SKILL.md).
For a feature graphic, fill
[`../app-store-assets/references/feature-graphic-template.yml`](../app-store-assets/references/feature-graphic-template.yml)
and follow
[`../app-store-assets/references/marketing-template-qa.md`](../app-store-assets/references/marketing-template-qa.md).
Treat its artboard as a working source, not proof of current Play acceptance.
Record the Play branch in
[`../app-store-assets/references/platform-adapters.yml`](../app-store-assets/references/platform-adapters.yml)
so Android-specific outputs remain separate from shared masters.

### 4. Adapt to current Play requirements

Check the current official Google Play Console documentation for every
deliverable and device family in scope. Verify accepted formats, dimensions,
aspect ratios, file limits, screenshot counts, feature graphic rules,
localization behavior, and any policy-sensitive content.

Read [references/google-play-delivery.md](references/google-play-delivery.md)
for the verification process. Do not use remembered requirements as proof of
submission readiness.

### 5. Package and report

Use a Play-specific output root such as:

```text
play-store-assets/
├── brand-context.yml
├── manifest.yml
├── icon/
├── screenshots/
│   ├── phone/
│   └── tablet/
├── feature-graphic/
├── promotional/
├── metadata/
└── QA.md
```

Write one `manifest.yml` record per output with relative path, kind, locale,
source, status, and checks. Mark assets `verified` only after visual review,
source-fidelity review, and current Play requirement checks. Finish with the
exact blockers and next steps for Play Console submission.

## Guardrails

- Never use an Apple-specific device frame or claim it represents an Android
  screen.
- Do not make a tablet asset by stretching a phone screen unless the user
  explicitly requests a concept and it is labeled as such.
- Preserve adaptive-icon source files separately from flattened store exports.
- Do not fabricate ratings, reviews, user counts, awards, or policy claims.
- Keep generated output separate from Android source assets and never overwrite
  previous runs without permission.
