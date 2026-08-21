# Skill map

Use the smallest Skill that covers the request. Use the integrated workflow
when multiple asset families must share one brand context.

| Need | Skill | Main output |
| --- | --- | --- |
| App icon | [`app-icon`](../skills/app-icon/SKILL.md) | Icon directions, selected master, raster exports, QA |
| Store screenshots | [`app-store-screenshots`](../skills/app-store-screenshots/SKILL.md) | Storyboard, real-screen compositions, platform variants |
| Complete store package | [`app-store-assets`](../skills/app-store-assets/SKILL.md) | Coordinated asset root, manifest, QA report |
| Google Play only | [`play-store-assets`](../skills/play-store-assets/SKILL.md) | Android icon, phone/tablet screenshots, Play graphics |
| Browser icons | [`favicon`](../skills/favicon/SKILL.md) | SVG/raster favicon family and optional head integration |
| Social previews | [`og-image`](../skills/og-image/SKILL.md) | Branded OG image and optional metadata integration |
| Listing copy | [`store-copy`](../skills/store-copy/SKILL.md) | Platform-mapped, evidence-backed metadata drafts |
| New locales | [`localization`](../skills/localization/SKILL.md) | Locale-specific copy, screenshots, manifests, review status |
| Final audit | [`release-check`](../skills/release-check/SKILL.md) | Blockers, warnings, evidence, release report |

## Recommended composition

```text
app project
    -> app-store-assets
        -> app-icon
        -> app-store-screenshots
        -> store-copy
        -> localization
        -> release-check
```

Use `play-store-assets` when Android-specific source captures or Play-only
outputs need their own workflow. Use `favicon` and `og-image` for web surfaces;
do not force those outputs into an app-store screenshot workflow.

## Shared context

All related Skills should read and preserve the same `brand-context.yml`. It
should contain evidence-backed product facts, visual decisions, source paths,
and explicit assumptions. Update confirmed values carefully; do not let a
single generated asset silently redefine the product.

## Status vocabulary

Generated asset manifests use:

- `draft` — concept or incomplete output
- `review` — visually complete but awaiting approval or a required check
- `verified` — source, file, and current platform checks passed
- `blocked` — a missing source, requirement, license, locale, or approval stops
  delivery

