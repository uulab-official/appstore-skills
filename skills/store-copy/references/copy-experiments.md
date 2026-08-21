# Copy experiments

Use a copy experiment record when comparing evidence-backed listing directions
before release. The record is a review artifact, not an A/B testing system.

Each variant must have:

- a unique ID, label, hypothesis, and reversible `copy_file`
- a `review`/`draft`/`verified`/`blocked` status
- an explicit approval state independent from technical validation
- a named owner, decision time, and evidence before its approval becomes
  `approved`

Keep `measurement: manual-review` unless the project supplies a separate,
approved measurement plan. Never imply conversion, retention, ranking, or
performance results without current evidence. The validator rejects unsafe
paths, duplicate variants, missing files, invalid approval records, and
experiment records that declare command execution.

Validate a record with:

```bash
python scripts/validate_copy_experiments.py \
  ./store-assets/metadata/copy-experiments.yml \
  --package-root ./store-assets
```

Preserve prior variants and append decisions to `history`; do not overwrite an
approved copy silently. Human or platform review is still required before any
variant is used in a store submission or external experiment.
