# Contributing to appstore-skills

Thanks for helping make appstore-skills more useful for app teams and AI
coding agents.

## Before opening a change

1. Read the relevant `SKILL.md` and its references.
2. Keep each skill independently understandable and reusable.
3. Prefer concise instructions and progressive disclosure over long background
   explanations.
4. Never add real app secrets, private customer data, or unlicensed assets.
5. Treat Apple and Google requirements as changeable; link to or describe a
   verification step instead of assuming a permanent size or policy.

## Skill changes

Every skill must have:

- valid YAML frontmatter with `name` and `description`
- an imperative workflow that another agent can follow
- explicit input discovery and output expectations
- a factuality and QA checkpoint
- updated `agents/openai.yaml` metadata when its scope changes

Use `references/` for detailed, conditional guidance. Keep the main
`SKILL.md` under 500 lines and avoid duplicating the same source of truth in
multiple places unless a skill must remain independently portable.

## Pull requests

Explain the user-facing problem, the affected skill(s), and how you validated
the change. Include example prompts or output trees when they make behavior
clear. Keep unrelated formatting changes out of the pull request.

## Validation

Run the repository checks that are available in your environment, including
the skill validator described in the skill-creator guidance. If a validator
cannot run because of a missing local dependency, report that explicitly and
perform a manual frontmatter and file-structure check.

