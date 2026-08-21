# Demo store assets

This directory is a review fixture for `appstore-skills`, built from
[`../brand-context.yml`](../brand-context.yml). It is intentionally labeled as
demo work because this repository does not contain a real app project or real
screen captures.

## What this demonstrates

- a generated app-icon concept and size family
- a matching favicon SVG
- a branded OG image SVG/PNG with exact, inspectable copy
- evidence-backed English store-copy draft
- manifest, QA, and release-check output

## What is intentionally blocked

Final store screenshots are not generated here. Creating synthetic product UI
would violate the source-fidelity rule. Supply real app or emulator captures,
then rerun `app-store-screenshots` and `release-check` before treating the
package as submission-ready.

Run the deterministic package check from the repository root:

```bash
python scripts/validate_store_output.py examples/demo-store-assets
```
