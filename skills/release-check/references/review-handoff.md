# Review handoff summary

`generate_review_handoff.py` creates a compact, diff-friendly review packet
from an existing store-asset package. It is a reviewer aid, not a release
approval, store submission, or publishing action.

The summary keeps these decisions separate:

- `release_report_status` comes from the existing release report.
- `approval_status` comes from the explicit release approval record.
- `review_status` is derived for triage: `blocked`, `pending_approval`,
  `review`, or `ready_for_handoff`.
- manifest changes are compared by stable relative path and selected metadata;
  generated timestamps are intentionally excluded from the diff.

Use `--previous-package-root` to compare two package manifests. Without a
baseline, the report labels every current asset as `baseline` rather than
pretending that additions and removals are known.

The generator never rewrites the source manifest or release report. It refuses
to overwrite an existing summary unless `--overwrite` is explicit.

```bash
python scripts/generate_review_handoff.py \
  --package-root ./store-assets \
  --previous-package-root ./previous-store-assets \
  --output ./store-assets/review-handoff.md
```
