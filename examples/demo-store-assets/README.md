# Demo store assets

This directory is a review fixture for `appstore-skills`, built from
[`../brand-context.yml`](../brand-context.yml). It is intentionally labeled as
demo work because this repository does not contain a real app project or real
screen captures.

## What this demonstrates

- four six-candidate icon batches, a review-stage design brief, a refined component-rich 3D A1 selection, and a size family
- a matching favicon SVG
- a branded OG image SVG/PNG with exact, inspectable copy
- reusable promotional and Google Play feature-graphic template specs with
  rendered SVG concept masters
- evidence-backed English store-copy draft
- manifest, QA, and release-check output

## What is intentionally blocked

Final store screenshots are not generated here. Creating synthetic product UI
would violate the source-fidelity rule. The promotional and feature-graphic
masters are concept compositions generated from the fictional brand context;
they are not approved campaign or Play assets. Supply real app or emulator
captures, verify current platform rules, and rerun `release-check` before
treating the package as submission-ready.

Run the deterministic package check from the repository root:

```bash
python scripts/validate_store_output.py examples/demo-store-assets
```
