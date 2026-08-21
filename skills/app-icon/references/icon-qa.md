# App icon QA checklist

Use this checklist after selecting a candidate and before calling an export
submission-ready.

## Candidate-set checks

- Confirm the batch contains the requested independent candidates, labeled
  `A1` through `C2` by direction when the default six-candidate workflow is
  used.
- Preserve every returned candidate and its prompt or direction rationale;
  do not silently filter or overwrite a candidate.
- Compare candidates at the same scale and against the same brand context.
- Reject a candidate whose only identity is a generic category symbol such as
  a checkmark, bell, lock, gear, cloud, document, or card stack.
- Require a product-specific silhouette or negative-space relationship that is
  still recognizable without text or a color legend.

## Visual checks

- Confirm the canvas is square and the subject has a deliberate safe area.
- Inspect the silhouette at 1024px, 180px, and 32px.
- Confirm the main idea remains legible without relying on tiny details.
- Confirm the candidate is ownable enough to justify selection; if none pass,
  generate another batch instead of selecting the least-bad generic symbol.
- Confirm foreground and background have sufficient contrast.
- Check that no unintended clipping, halos, seams, or transparent pixels
  remain at the edge.
- Check that the color profile and image mode are appropriate for the export.
- Compare the icon with the app UI and `brand-context.yml` for brand fit.

## Product and legal checks

- Confirm the symbol represents the app and does not promise an unsupported
  feature.
- Confirm supplied logos and reference images are licensed for this use.
- Check for accidental resemblance to a third-party trademark or another app's
  distinctive icon.
- Remove text unless the user explicitly approved it and the text remains
  readable in the smallest target context.

## Delivery checks

- Preserve the selected source/master and candidate rationale.
- If geometry is simple, preserve the generated reference and the refined
  vector master separately, then derive raster exports from the vector master.
- Confirm every requested export exists at the path recorded in the report.
- Verify dimensions against current official platform documentation.
- Record unresolved issues as blockers instead of silently shipping them.
