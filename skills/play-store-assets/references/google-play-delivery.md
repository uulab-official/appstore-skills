# Google Play delivery verification

Google Play requirements and Play Console surfaces can change. Use this as a
repeatable verification process rather than a permanent dimension table.

## Verify each run

1. Identify the exact Play Console listing, device family, locale, and asset
   type in scope.
2. Open the current official Google Play Console help for store listing
   graphics and screenshot requirements.
3. Record the documentation URL and date checked in `QA.md`.
4. Confirm accepted formats, pixel dimensions, aspect ratio, file-size limits,
   screenshot count, and localization behavior.
5. Check whether the asset is a listing image, an in-app resource, an adaptive
   icon source, or a flattened upload export.
6. Validate the actual output file and map every check to `manifest.yml`.

## Android fidelity

- Capture Android screens from the correct build or emulator configuration.
- Preserve Android navigation, system bars, font rendering, and responsive
  layout when they are visible in the source capture.
- Keep phone and tablet source captures separate.
- Do not label a concept or simulated responsive layout as a final screenshot.

## Status rules

Use `draft` for an unreviewed concept, `review` for a visually complete asset,
`verified` only after current Play checks and product approval, and `blocked`
when a source capture, locale, license, or requirement is missing.

