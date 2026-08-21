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
pretending that additions and removals are known. When both packages contain
`review-assignment.yml`, the same baseline comparison also reports reviewer
additions, removals, scope changes, status/assignment changes, evidence
reference changes, and event-level history additions, removals, or rewrites.
It also flags any baseline history that is no longer an unchanged prefix. Use
`--previous-assignment-file` when the previous assignment record is stored
outside the previous package root.

When review adapters are selected with repeated `--adapter` flags, the handoff
also renders an adapter coverage matrix from reviewer `coverage` entries. A
missing owner is a visible warning and never an inferred pass.
Use `--max-evidence-age-days` to opt into freshness enforcement for terminal
adapter evidence. Stale or future-dated terminal records become blockers in
the handoff; pending records remain pending and the default is unchanged.
Use `--max-reviewer-decision-age-days` to apply the same opt-in freshness gate
to terminal reviewer decisions in `review-assignment.yml`; stale or future
`decided_at` values become reviewer-assignment blockers.

The generator never rewrites the source manifest or release report. It refuses
to overwrite an existing summary unless `--overwrite` is explicit.

```bash
python scripts/generate_review_handoff.py \
  --package-root ./store-assets \
  --previous-package-root ./previous-store-assets \
  --output ./store-assets/review-handoff.md
```

The assignment delta is informational. It does not infer approval from a
changed status, and it never mutates either assignment record.
