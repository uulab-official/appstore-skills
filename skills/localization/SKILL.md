---
name: localization
description: Localize store copy, screenshot text, icon or promotional variants, and asset manifests for specified locales while preserving product meaning and UI fidelity. Use when an agent needs to translate or culturally adapt App Store, Google Play, web, or social assets for additional markets.
---

# Store asset localization

Adapt store assets for a target locale, not merely word-for-word translate
them. Preserve the product's meaning, factual claims, visual hierarchy, and
brand personality while making language, terminology, typography, and imagery
natural for the market.

## Establish the localization contract

Confirm:

- source locale and target locales
- platform and asset types in scope
- whether copy, screenshot captions, metadata, or UI itself should change
- approved glossary, tone, product names, and untranslated terms
- review owner and whether professional or native review is required

Inspect the app's locale files, existing translations, `brand-context.yml`,
store-copy drafts, screenshots, and release metadata. Never assume the app's
language support from a store listing alone.

## Workflow

### 1. Prepare the source

Create a source inventory with stable identifiers, character counts, context,
and evidence:

| ID | Source | Context | Locale | Platform | Notes |
| --- | --- | --- | --- | --- | --- |
| `hero-01` | Screenshot headline | First store frame | en-US | Google Play | One benefit |

Freeze product facts before translating. If the source copy is unsupported or
ambiguous, resolve it in the source locale first instead of spreading the
ambiguity across every translation.

### 2. Adapt copy and terminology

Translate the meaning and user intent. Preserve:

- product names, trademarks, and approved feature names
- numbers, units, prices, dates, and legal conditions unless the locale needs
  a documented adaptation
- the distinction between a feature and a benefit
- the same evidence standard and claim strength

Create or update a glossary and record decisions for terms with multiple valid
translations. Do not introduce cultural claims, idioms, or promises that the
source does not support.

### 3. Adapt visual assets

Recompose screenshots, OG images, promotional art, or feature graphics when
translated text changes width or line breaks. Use real localized UI captures
when the UI itself is in scope. Do not paste translated text over an English
screen and label it as a fully localized product view.

Check typography support, line height, right-to-left direction, date and number
formats, text expansion, safe areas, and truncation. Keep icons and universal
symbols unchanged only when they carry the same meaning in the target market.

### 4. Package per locale

Use explicit locale and platform paths:

```text
store-assets/locales/
├── en-US/
│   ├── store-copy.yml
│   ├── screenshots/
│   └── manifest.yml
└── ko-KR/
    ├── store-copy.yml
    ├── screenshots/
    └── manifest.yml
```

Update the parent `manifest.yml` with locale, source asset, translated copy,
status, and QA checks. Mark an asset `review` until a native or designated
reviewer confirms language, meaning, and visual fit.

### 5. Review and report

Review every locale in isolation and alongside the source locale. Check
meaning, tone, terminology, claims, UI fidelity, typography, crop, metadata
fields, and current platform limits. Report untranslated strings, uncertain
terms, missing fonts, unavailable localized screenshots, and approvals needed.

Read [references/localization-qa.md](references/localization-qa.md) for the
full checklist.
For repeatable locale and terminology checks, read
[references/localization-contract.md](references/localization-contract.md) and
run `scripts/validate_localization_specs.py` against the plan, glossary, and
package root. This check also keeps every target locale's Apple and Google Play
field structure aligned with the source locale. It preserves `review` until a
designated or native reviewer confirms the localized result.

## Guardrails

- Do not claim native fluency or final approval without the required review.
- Do not localize unsupported product claims or alter legal conditions silently.
- Do not fake localized UI by changing only screenshot captions.
- Preserve source files and make locale outputs reversible.
- Keep locale codes consistent with the target platform and project metadata.
- Do not mark a locale or copy `verified` without a named reviewer and review
  timestamp in the corresponding records.
