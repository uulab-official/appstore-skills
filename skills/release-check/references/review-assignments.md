# Reviewer assignment and decision history

`review-assignment.yml` keeps human ownership separate from technical release
checks. It is a small, reviewable record for who is expected to inspect a
package, what decision each reviewer has made, and when the record changed.

Each required reviewer remains `pending` until a named person is assigned and
records a terminal decision with an ISO-8601 timestamp and evidence reference.
The validator accepts pending records with empty assignment fields so an
unassigned package is visible rather than falsely marked complete.

Supported reviewer states are `pending`, `in_review`, `approved`, `blocked`,
and `not_applicable`. An assignment can only be `approved` when every required
reviewer is approved and no reviewer is blocked. History events require an
actor, action, note, and chronological timestamp; the contract never infers
approval from CI or from a missing event.

Validate one or more records with:

```bash
python scripts/validate_review_assignments.py \
  ./store-assets/review-assignment.yml
```

The handoff generator automatically reads `review-assignment.yml` from the
package root when it exists and renders the assignment state, reviewer rows,
and history event count. This is informational only: it does not assign a
person, approve a reviewer, send a notification, or publish a package.
