# Reviewer assignment and decision history

`review-assignment.yml` keeps human ownership separate from technical release
checks. It is a small, reviewable record for who is expected to inspect a
package, what decision each reviewer has made, and when the record changed.

Each reviewer must declare a non-empty `scope`, such as `privacy-disclosure`
or `localized-store-copy`, before assignment. A required reviewer remains
`pending` until a named person is assigned and records a terminal decision
with an ISO-8601 timestamp and one or more evidence references. Evidence
references can be ticket IDs, document paths, or other project-owned
traceability links; the contract does not dereference or upload them. The
validator accepts pending records with empty assignment and evidence fields so
an unassigned package is visible rather than falsely marked complete.

Each reviewer also declares non-empty `coverage` entries using the IDs from
the selected review-adapter registry, for example `privacy-review`. The handoff
generator renders a coverage matrix and warns when a selected adapter has no
reviewer coverage. Coverage identifies ownership only; it does not make the
adapter pass.

Supported reviewer states are `pending`, `in_review`, `approved`, `blocked`,
and `not_applicable`. An assignment can only be `approved` when every required
reviewer is approved and no reviewer is blocked. History events require an
actor, action, note, and chronological timestamp; the contract never infers
approval from CI or from a missing event.

Validate one or more records with:

```bash
python scripts/validate_review_assignments.py \
  --adapter-file ./skills/release-check/references/review-adapters.yml \
  ./store-assets/review-assignment.yml \
  --adapter policy-review \
  --adapter accessibility-review \
  --adapter privacy-review
```

The adapter options are optional. When supplied, every selected adapter must
be declared in the registry and covered by at least one reviewer; unknown
coverage IDs also fail validation.

The handoff generator automatically reads `review-assignment.yml` from the
package root when it exists and renders the assignment state, reviewer rows,
scope, evidence references, and history event count. This is informational
only: it does not assign a person, approve a reviewer, send a notification, or
publish a package.
