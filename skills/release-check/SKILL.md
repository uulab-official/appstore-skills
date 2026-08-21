---
name: release-check
description: Audit an App Store and Google Play asset package before submission for file integrity, source fidelity, copy, localization, platform requirements, legal risks, and manifest completeness. Use when an agent needs a final release-readiness report without submitting assets or claiming store approval.
---

# Store release check

Audit the generated package as a release candidate. Find blockers and evidence
gaps before submission, distinguish warnings from failures, and produce a
reproducible report. Never submit to a store or call a package approved merely
because files exist.

## Inputs

Accept a store asset root such as `store-assets/` or
`play-store-assets/`. Inspect:

- `brand-context.yml`, `manifest.yml`, `QA.md`, and evidence logs
- every referenced image, source capture, copy file, and locale variant
- target platforms, device families, locales, and requested deliverables
- current official Apple and Google requirements for the exact surfaces in
  scope

If the package lacks a manifest, build a temporary inventory and report the
missing required file as a blocker rather than silently treating the folder as
complete.

## Workflow

### 1. Inventory and integrity

Check that every manifest path exists, every deliverable has one clear kind and
platform, and no unexpected private or source-only files are included. Verify
image readability, dimensions, format, color profile, transparency, and file
size against current requirements.

Check for duplicate files, broken links, placeholder names, stale generated
dates, and outputs that are outside the declared run directory.

### 2. Product and brand fidelity

Compare icons, screenshots, promotional graphics, OG images, and copy with
`brand-context.yml` and evidence sources. Confirm:

- final screenshots use real app UI or are clearly labeled concepts
- marketing copy does not advertise unsupported features or outcomes
- icon and visual system are consistent across platforms
- localized variants preserve product meaning and approved terminology
- no private data, test accounts, secrets, or internal URLs are visible

### 3. Platform and policy review

Verify current official requirements for each platform, device family, locale,
and asset type. Record the URL and date checked. Review obvious policy risks
such as fabricated ratings, misleading claims, prohibited imagery, unapproved
trademarks, missing subscription disclosures, and unresolved rights for supplied
assets. Flag items for human or legal review instead of making a legal ruling.

### 4. Assign statuses

Use these statuses:

- `pass` — the check was performed and evidence supports success
- `warn` — the asset may proceed but needs explicit review or has a known risk
- `block` — submission should stop until the issue is resolved
- `not_applicable` — the check is outside the declared scope

Treat missing source evidence, missing required platform outputs, unreadable
files, unsupported claims, and unverified requirements as `block` or `warn`
according to impact. Do not downgrade a blocker to make the package pass.

### 5. Write the release report

Create:

```text
store-assets/release-report.md
```

Include the run path, commit or source revision when available, scope, checks,
evidence, platform documentation URLs and dates, blockers, warnings, passed
checks, and exact next actions. Add a summary status of `ready_for_review`,
`blocked`, or `incomplete`; reserve `ready_for_submission` for packages where
all in-scope checks actually pass and the user explicitly accepts the remaining
human review.

Read [references/release-checklist.md](references/release-checklist.md) for
the detailed checks and report fields.

When running in GitHub Actions, surface the report in the pull request with
`python scripts/annotate_release_report.py <release-report.md> --github-actions`.
This emits blocker and warning annotations and appends a Step Summary when the
runner provides `GITHUB_STEP_SUMMARY`; use `--fail-on-blockers` only when the
workflow should gate on the report status.

For a final read-only handoff, run
`python scripts/prepare_release_handoff.py --project-root <app> --output-root <store-assets> --approval-file <store-assets>/release-approval.yml --format summary`.
Read [the handoff contract](../app-store-assets/references/release-handoff.md)
and [the approval-gated handoff](../app-store-assets/references/approval-gated-handoff.md)
before using it. A technically complete package without an explicit approval
record remains `pending_approval`. It must remain a dry-run and must never be
treated as a submission record. Use `--fail-on-pending-approval` only when the
workflow intentionally requires the human decision. When build or source
capture evidence files already exist, select the opt-in providers described in
[`evidence-providers.yml`](../app-store-assets/references/evidence-providers.yml);
they only inspect files and do not execute the app project.

## Non-goals

- Do not upload or submit to App Store Connect or Play Console.
- Do not approve legal, accessibility, privacy, or policy questions on behalf
  of the project owner.
- Do not silently rewrite assets or metadata while auditing them.
- Do not call a missing check successful because a similar previous run passed.
