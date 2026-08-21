# Approval-gated handoff

The release handoff separates technical evidence from the human decision to
move a package forward. Store assets can be structurally valid while still
waiting for product, legal, platform, accessibility, or localization review.

## Approval record

Start from
[`release-approval.yml`](release-approval.yml). The record is intentionally
small and explicit:

- `pending` means the package is waiting for a decision.
- `approved` means a named owner approved the listed scope at the recorded
  time and attached an auditable evidence reference.
- `rejected` and `expired` are terminal blockers until a new decision is
  recorded.

Terminal decisions require `owner`, a non-empty `scope`, a matching `decision`,
an ISO-8601 `decided_at`, and at least one `evidence` reference. An approval
cannot be inferred from a green CI run, a generated image, or the absence of
blockers.

## Handoff states

`prepare_release_handoff.py` combines technical checks and the approval record:

- `blocked` — a required technical check or the approval record is invalid,
  rejected, or expired.
- `pending_approval` — technical evidence is complete but no explicit approval
  has been recorded yet.
- `ready_for_handoff` — technical evidence and an explicit approval record are
  present. This still means read-only handoff review; it is not a submission or
  store acceptance result.

The report always keeps `publish_status: not-run`. The command never builds,
launches a simulator, uploads, submits, or publishes.

## Usage

```bash
python scripts/prepare_release_handoff.py \
  --project-root ./my-app \
  --output-root ./my-app/store-assets \
  --approval-file ./my-app/store-assets/release-approval.yml \
  --format summary
```

Use `--fail-on-pending-approval` when a CI job should require an approval
record, and use `--fail-on-blocked` when technical blockers should fail the
job. Both are opt-in so a report can be generated for review without silently
turning a review fixture into a release.
