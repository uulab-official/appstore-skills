# Web favicon QA checklist

## Asset checks

- Confirm every file is square and generated from the selected master.
- Inspect SVG viewBox, filled paths, stroke behavior, and external references.
- Inspect raster files at 1:1 with no unintended blur, halo, or clipping.
- Confirm transparent pixels and background treatment match the target site.
- Check the mark against light and dark browser chrome.
- Confirm file names and paths match the integration snippet or manifest.

## Integration checks

- Search the project for existing `icon`, `shortcut`, `apple-touch-icon`, and
  manifest references before adding links.
- Confirm the final HTML or framework head output contains no duplicate or
  conflicting tags.
- Test a production-like build if the project provides one.
- Check browser tab, bookmark, and mobile home-screen previews when those
  surfaces are in scope.

## Delivery checks

- Record the source logo or app icon and any license or approval assumptions.
- Mark browser-specific or pinned-site requirements as verified only after
  checking the target's current documentation.
- Keep the master, exports, and integration changes easy to revert.

