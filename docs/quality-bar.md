# Quality bar

The goal is a trustworthy store asset package, not merely a complete-looking
folder. Use this bar for new Skills, generated outputs, and documentation
changes.

## Non-negotiable gates

### 1. Product truth

- Ground product names, features, benefits, and claims in project evidence.
- Record source paths in `brand-context.yml`, copy evidence, or `QA.md`.
- Mark assumptions and unknowns explicitly.
- Never present a concept, mockup, or synthetic UI as a shipped product screen.

### 1.1 User-input fidelity

- Treat explicit user art direction as a hard constraint, not inspiration.
- Record the hero object, supporting components, material, mood, palette, and
  avoid list before generating visual candidates.
- Do not compensate for missing input with a generic metaphor; ask a focused
  question or keep the result explicitly in draft/review status.

### 2. Brand coherence

- Reuse the approved icon, colors, typography, tone, and terminology.
- Keep icon, screenshots, copy, web previews, and localized variants visibly
  connected to one product.
- Preserve approved assets and previous outputs unless replacement is explicit.

### 2.1 Icon distinctiveness

- Do not ship the clearest generic category symbol as the default icon.
- Require a product-specific silhouette, aperture, negative-space move, or
  character proportion that remains recognizable at 32px.
- Preserve rejected candidate batches and record why a stronger direction was
  generated when the first pass is too generic.

### 3. Platform correctness

- Check current official requirements for every store, device family, locale,
  image type, and metadata field in scope.
- Record the documentation URL and date checked.
- Do not label an output `verified` from memory or from a previous project.

### 4. Asset integrity

- Confirm every manifest path exists, is non-empty, and stays inside the output
  root.
- Check dimensions, format, color profile, transparency, file size, and text
  legibility for the actual asset.
- Keep source compositions, masters, and platform exports distinguishable.

### 5. Localization quality

- Preserve the source meaning, claim strength, legal conditions, and product
  terminology.
- Recompose visual assets for text expansion, RTL layout, and localized UI.
- Require the designated or native reviewer before marking a locale verified.

### 6. Safety and rights

- Exclude secrets, private data, test accounts, internal URLs, and unreleased
  content.
- Record approval or license assumptions for supplied logos, fonts, images, and
  trademarks.
- Escalate legal, policy, accessibility, privacy, and security questions to a
  human reviewer rather than guessing.

### 7. Reproducibility

- Keep `brand-context.yml`, `manifest.yml`, `QA.md`, and `release-report.md`
  aligned with the files on disk.
- Use stable relative paths and explicit locale/platform fields.
- Never overwrite a previous run silently.
- Leave a concise delivery report that explains what was generated and what is
  still blocked.

## Skill acceptance criteria

Every Skill should define:

- what to inspect before acting
- how to separate evidence from assumptions
- the generation or adaptation workflow
- the expected output paths and status vocabulary
- failure handling for missing or low-quality inputs
- a final QA and delivery report

Every change must keep `SKILL.md` concise, keep referenced files reachable, and
pass the repository validators and tests.

## Release status

Use `draft`, `review`, `verified`, and `blocked` for generated asset manifests.
Use `ready_for_review`, `incomplete`, and `blocked` for release summaries.
Reserve `verified` or `ready_for_submission` for checks that were actually
performed and documented.
