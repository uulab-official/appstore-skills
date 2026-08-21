# Policy, accessibility, and privacy review adapters

The optional review adapters make human review state explicit without making a
legal, policy, accessibility, or store-approval decision. They are opt-in,
read-only readers of evidence files that already exist.

The registry contains:

- `policy-review` for claims, rights, privacy-sensitive copy, subscriptions,
  permissions, and platform policy questions
- `accessibility-review` for contrast, text scaling, VoiceOver/TalkBack,
  touch targets, motion, and localized layout review
- `privacy-review` for data collection, account behavior, permissions,
  disclosure text, retention, and privacy manifest or questionnaire scope

An adapter result is:

- `pending` when no review record exists or the reviewer has not decided
- `pass` when a designated reviewer recorded a passing scope, timestamp, and
  evidence
- `blocked` when the record is invalid or the reviewer recorded a block
- `not_applicable` when the designated reviewer explicitly records that scope
  is outside the package

Inspect selected adapters with:

```bash
python scripts/inspect_review_adapters.py \
  --adapter-file skills/release-check/references/review-adapters.yml \
  --assignment-file ./store-assets/review-assignment.yml \
  --project-root ./my-app \
  --output-root ./store-assets \
  --max-age-days 30 \
  --adapter policy-review \
  --adapter accessibility-review \
  --adapter privacy-review
```

The default is informational. Use `--fail-on-pending` or
`--fail-on-blocked` only when the workflow intentionally gates on human review.
When `--assignment-file` is supplied, terminal evidence must name a reviewer
who is assigned to and covers the selected adapter. Missing or mismatched
ownership is blocked; pending records remain pending.
`--max-age-days` is optional and applies only to terminal `pass`/`block`
records. It blocks evidence older than the configured age and also blocks a
future `reviewed_at` timestamp; pending records are not aged out. The default
does not enforce freshness.
The adapters never run scanners, open a simulator, call a store API, upload,
publish, or approve on behalf of a reviewer.
