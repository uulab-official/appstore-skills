# Safe release handoff

Use `prepare_release_handoff.py` as the final read-only bridge between an app
project and a store-asset package. It creates a dry-run plan from filesystem
evidence; it does not build, launch a simulator, upload, submit, or publish.

## Handoff checks

- `project-root` confirms that the requested app project is readable.
- `build-config` finds project build signals such as package metadata, iOS or
  Android directories, EAS, Gradle, Xcode, or Fastlane configuration.
- `build-identity` requires an explicit build evidence record under `evidence/`;
  a build configuration alone is not proof that the inspected app exists.
- `simulator-captures` requires real image files under a source-capture folder;
  generated marketing art does not satisfy this check.
- `store-output` confirms the package contract files exist.
- `release-report` confirms that blockers, warnings, and human review state are
  recorded.
- `human-approval` requires a valid explicit decision record. Missing approval
  is `pending`, while invalid, rejected, or expired approval is `blocked`.

The handoff is `blocked` when build identity or simulator evidence is missing,
or when the approval record is invalid, rejected, or expired. If technical
checks pass but approval is not recorded, the status is `pending_approval`.
Only complete technical evidence plus a valid `approved` record produces
`ready_for_handoff`; that status still does not mean submission or store
acceptance.

## Usage

```bash
python scripts/prepare_release_handoff.py \
  --project-root ./my-app \
  --output-root ./my-app/store-assets \
  --platform apple \
  --platform google-play \
  --approval-file ./my-app/store-assets/release-approval.yml \
  --format summary
```

Use `--output` to write a new handoff report. Existing files are never replaced
unless `--overwrite` is explicit. The report always records
`publish_status: not-run`. Use `--fail-on-blocked` for technical or terminal
approval blockers and `--fail-on-pending-approval` when a CI job must have an
explicit approval before it succeeds.
