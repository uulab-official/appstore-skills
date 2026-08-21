# Platform adapters

Use `platform-adapters.yml` as the handoff map between shared source masters
and platform-specific outputs. An adapter is a transformation plan, not proof
that a platform accepts an asset.

## Adapter rules

- Keep one approved source master and separate output roots for each platform.
- Name the transformation for every surface; do not silently reuse an export
  whose crop, device chrome, safe area, or metadata differs.
- Source Apple screenshots from Apple captures and Android screenshots from
  Android captures. A shared marketing composition may not fabricate UI.
- Record `current-official-docs` and the documentation URL/date before marking
  an adapter `verified`.
- Keep platform dimensions and limits out of permanent templates when they can
  change; resolve them at execution time and record the checked values in QA.
- Preserve the same `brand-context.yml`, copy evidence, locale, and approval
  state across every adapter branch.

## Adapter sequence

1. Select the shared icon, screenshot story, copy, and marketing template.
2. Fill one adapter record for every requested platform and surface.
3. Apply only the named transformation and write a separate output path.
4. Run the image metadata validator on rendered images.
5. Check platform documentation, crop/safe-area behavior, and source fidelity.
6. Record the result in `manifest.yml`, `QA.md`, and `release-report.md`.

Use the Apple, Google Play, Web, Amazon Appstore, and Samsung Galaxy Store
records in the reference map as starting points. The Amazon and Samsung
profiles include documentation URLs checked on 2026-08-21, but their rules
remain execution-time checks. Add a new adapter only when its source fidelity,
output family, and verification checks can be described explicitly.
