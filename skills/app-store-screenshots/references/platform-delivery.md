# Platform delivery verification

Store requirements change. Use this document as a process checklist, not as a
table of permanent dimensions.

## Verify at execution time

1. Identify the exact store, device family, locale, and submission surface.
2. Open the current official Apple documentation for App Store product-page
   screenshots and the current official Google Play documentation for store
   listing graphics and screenshots.
3. Record the documentation URLs and the date checked in `QA.md`.
4. Confirm accepted image formats, pixel dimensions, aspect ratio, file-size
   limits, screenshot count, and device-family coverage.
5. Confirm whether the platform resizes or reuses an export across device
   families; do not infer this from a previous project.
6. Validate every file after export and map the result to `manifest.yml`.

## Keep platform output separate

Use one source composition when practical, but export separate platform files:

```text
screenshots/
├── source/
├── apple/
│   ├── iphone/
│   └── ipad/
└── google-play/
    ├── phone/
    └── tablet/
```

Do not use a device frame that conflicts with the target platform. Preserve
safe areas for system UI, store overlays, and translated copy. Treat any
platform-specific crop as a new QA item.

## Report status clearly

Use `verified` only when the current official requirements and the actual file
have both been checked. Use `review` when the asset is visually complete but
awaits platform or product approval. Use `blocked` when a source capture,
translation, license, or requirement is missing.

