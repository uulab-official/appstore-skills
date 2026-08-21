# Evidence adapters

Use `evidence-adapters.yml` to connect an app project and its release systems
to the asset package. Evidence is a chain of proof, not a generic confidence
label.

## Adapter meanings

- `project` proves product facts and visual decisions from inspectable source
  files. Keep facts separate from assumptions.
- `build` proves which app revision and target platform produced the inspected
  behavior. A package version string alone is not enough.
- `simulator` proves that screenshot candidates show real UI on a named device
  family and locale. If the app cannot run or no capture exists, keep this
  adapter `blocked` and produce only a storyboard.
- `release` proves that current platform checks, approvals, licenses, blockers,
  and warnings are recorded. It does not submit anything.

## Evidence sequence

1. Inspect the project and record source paths with the `project` adapter.
2. Identify the exact build or commit with the `build` adapter.
3. Capture real screens through a simulator/emulator or supplied device images
   with the `simulator` adapter. Keep each source image path unique in the
   capture manifest so one file cannot be relabeled as multiple scopes.
4. Map each selected asset to its evidence and run platform/release review with
   the `release` adapter.
5. Keep missing evidence `blocked`; do not upgrade a concept to a final asset
   because a template rendered successfully.

Pass the same evidence paths into `brand-context.yml`, `manifest.yml`,
`QA.md`, and `release-report.md`. The adapters define what must be proven;
they do not replace current platform documentation or human approval. For
existing build and capture records, use the opt-in readers in
[`evidence-providers.yml`](evidence-providers.yml); they add field and file
integrity checks without executing project commands.
