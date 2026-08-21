# Getting started

`appstore-skills` is a repository of instructions for AI coding agents. It is
not a standalone CLI and does not upload files to App Store Connect, Play
Console, or a social platform.

## Install the skills

Use the installation mechanism provided by your agent. For agents that scan a
local skill directory, copy the individual folders under `skills/` into that
directory while preserving each folder's `SKILL.md`, `agents/`, and
`references/` files.

For a repository-aware agent, keep this repository available and ask it to use
the relevant path directly. Do not copy only the `SKILL.md`; references contain
important QA and platform-verification rules.

## Choose a starting skill

- Need one app icon? Start with [`app-icon`](../skills/app-icon/SKILL.md).
- Need App Store and Google Play screenshots? Start with
  [`app-store-screenshots`](../skills/app-store-screenshots/SKILL.md).
- Need a coordinated package? Start with
  [`app-store-assets`](../skills/app-store-assets/SKILL.md).
- Need Android-only outputs? Start with
  [`play-store-assets`](../skills/play-store-assets/SKILL.md).
- Need browser icons or social previews? Start with
  [`favicon`](../skills/favicon/SKILL.md) or
  [`og-image`](../skills/og-image/SKILL.md).
- Need listing text or additional locales? Use
  [`store-copy`](../skills/store-copy/SKILL.md) and
  [`localization`](../skills/localization/SKILL.md).
- Have a generated package to audit? Use
  [`release-check`](../skills/release-check/SKILL.md).

## Give the agent useful context

Provide the app or website project path, target platforms, locales, existing
brand files, preferred output directory, and whether the agent may run the app.
The agent should discover product facts from the project before generating
assets.

Example:

```text
Use $app-store-assets on ./my-app.
Target Apple and Google Play, English and Korean.
Use the existing logo and simulator captures when available.
Write outputs to ./store-assets and keep existing runs untouched.
```

## Review the output

Look for:

- `brand-context.yml` — shared product and visual facts
- `manifest.yml` — one record per generated asset
- `QA.md` — evidence, platform checks, assumptions, and blockers
- `release-report.md` — final audit status when `release-check` runs

Generated files should remain separate from app source files. Treat `review`
and `blocked` statuses as work that still needs product, platform, legal, or
localization review.

## Validate the repository

From the repository root:

```bash
python scripts/validate_skills.py
python scripts/validate_docs.py
python -m unittest discover -s tests
```

To validate an actual generated package, run:

```bash
python scripts/validate_store_output.py ./store-assets
python scripts/annotate_release_report.py ./store-assets/release-report.md
python scripts/validate_adapter_specs.py ./store-assets/platform-adapters.yml
python scripts/validate_evidence_specs.py ./store-assets/evidence-adapters.yml
python scripts/validate_provider_specs.py ./store-assets/evidence-providers.yml
python scripts/validate_release_approval.py ./store-assets/release-approval.yml
python scripts/validate_localization_specs.py \
  ./store-assets/localization-plan.yml \
  ./store-assets/terminology.yml \
  --package-root ./store-assets
python scripts/validate_copy_experiments.py \
  ./store-assets/metadata/copy-experiments.yml \
  --package-root ./store-assets
python scripts/generate_review_handoff.py \
  --package-root ./store-assets \
  --adapter-file ./skills/release-check/references/review-adapters.yml \
  --adapter policy-review \
  --adapter accessibility-review \
  --adapter privacy-review \
  --max-evidence-age-days 30 \
  --output ./store-assets/review-handoff.md
python scripts/validate_review_assignments.py \
  --adapter-file ./skills/release-check/references/review-adapters.yml \
  ./store-assets/review-assignment.yml \
  --adapter policy-review \
  --adapter accessibility-review \
  --adapter privacy-review
python scripts/prepare_release_handoff.py \
  --project-root ./my-app \
  --output-root ./store-assets \
  --platform apple \
  --platform google-play \
  --locale en-US \
  --device-family iphone \
  --require-scope-coverage \
  --provider-file ./store-assets/evidence-providers.yml \
  --provider build-record \
  --provider simulator-source-captures \
  --max-evidence-age-days 30 \
  --require-current-revision \
  --approval-file ./store-assets/release-approval.yml \
  --format summary
```

In GitHub Actions, add `--github-actions` to turn blockers and warnings into
pull-request annotations. The annotation command is informational by default;
use `--fail-on-blockers` when a workflow should gate on unresolved blockers.
The release handoff command is also informational by default and never runs a
build, simulator, upload, or publish action; use `--fail-on-blocked` only when
that gate is intentional. Use `--fail-on-pending-approval` when CI must have an
explicit human decision record. Add `--max-evidence-age-days` when a project
needs terminal policy, accessibility, or privacy evidence to be refreshed on a
defined cadence; this gate is opt-in.
The same option can be passed to the provider-backed release handoff to block
stale project, build, or simulator evidence; without it, timestamp checks
remain format-only.
Add `--max-reviewer-decision-age-days` when terminal reviewer decisions must be
refreshed on a defined cadence; future or stale `decided_at` values then block
the review handoff. This reviewer-decision gate is opt-in.
Add `--require-current-revision` when the build evidence must correspond to
the current Git checkout; this strict source binding is also opt-in.
Add `--locale` when source captures must correspond to a specific localized
listing; locale separators such as `en_US` and `en-US` are normalized.
Add `--device-family` when captures must correspond to a named iPhone, iPad,
or Android device family; no family is inferred when omitted.
Add `--require-scope-coverage` when every requested platform/locale/device
family combination must have a source capture.

Add `--provider project-facts` when product discovery should be checked before
generation. It validates `evidence/project-facts.yml`, including explicit
assumptions, project-root source paths, and `private_data_screen: pass`.

For project-owned evidence integrations, keep `evidence-providers.yml` under
the project root with `provider_set.owner: project` and
`provider_set.selection: explicit`. Pass it with `--provider-file` and select
each provider explicitly. The inspector records the registry metadata, blocks
registries outside the project root, and rejects evidence paths that escape
the output root.
