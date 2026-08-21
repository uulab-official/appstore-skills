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
```

In GitHub Actions, add `--github-actions` to turn blockers and warnings into
pull-request annotations. The annotation command is informational by default;
use `--fail-on-blockers` when a workflow should gate on unresolved blockers.
