# Policy and accessibility review adapters

The optional review adapters make human review state explicit without making a
legal, policy, accessibility, or store-approval decision. They are opt-in,
read-only readers of evidence files that already exist.

The registry contains:

- `policy-review` for claims, rights, privacy-sensitive copy, subscriptions,
  permissions, and platform policy questions
- `accessibility-review` for contrast, text scaling, VoiceOver/TalkBack,
  touch targets, motion, and localized layout review

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
  --project-root ./my-app \
  --output-root ./store-assets \
  --adapter policy-review \
  --adapter accessibility-review
```

The default is informational. Use `--fail-on-pending` or
`--fail-on-blocked` only when the workflow intentionally gates on human review.
The adapters never run scanners, open a simulator, call a store API, upload,
publish, or approve on behalf of a reviewer.
