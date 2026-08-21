---
name: app-icon
description: Analyze an app project and design, generate, evaluate, and export a recognizable app icon for App Store and Google Play workflows. Use when an agent needs to create or refresh an app icon from README files, app configuration, UI code, existing branding, or supplied reference images.
---

# App icon

Create a small-size legible icon that belongs to the product rather than a
generic category illustration. Base decisions on evidence from the app
project, keep the icon free of text unless the user explicitly asks for a
wordmark, and preserve an auditable path from source context to final export.

## Inputs

Inspect the project root and relevant assets before designing. Look for:

- `README.md`, product copy, onboarding text, and app metadata
- `package.json`, `app.json`, `app.config.*`, `Info.plist`, and
  `AndroidManifest.xml`
- theme files, design tokens, logos, illustrations, and existing icon files
- navigation, routes, screen names, and feature descriptions
- user-supplied brand guidelines or reference images

Record evidence with file paths. Separate facts from assumptions. If an
existing icon is present, assess whether to refine, replace, or preserve it
before generating alternatives.

### Required creative brief

Do not invent the hero object or visual metaphor when the user is available.
Before generation, ask for or record an `icon-design-brief.yml` containing:

- the product promise in one sentence and the action the icon should evoke
- the requested hero object or metaphor, including what it must not resemble
- the desired personality, finish mode, material, lighting, and background
- the primary form, secondary component, and at most one small supporting cue
- must-include details, must-avoid details, palette constraints, and references

Map every requested input to a prompt decision. If a required field is missing,
pause before generation and ask a focused question. In unattended work, use
only evidence from the project, mark all proposed art direction as an
assumption, and keep the result in `draft` or `review` rather than presenting
it as the user's approved design. Use the template in
[references/icon-design-brief.yml](references/icon-design-brief.yml).

## Workflow

### 1. Build product and brand context

Extract the product name, category, audience, value proposition, personality,
primary features, existing visual language, and confirmed colors. Write or
update `brand-context.yml` in the chosen output directory using this shape:

```yaml
schema_version: 1
brand:
  name: Product name
  personality: [simple, friendly]
product:
  category: product category
  audience: primary audience
  value_proposition: evidence-backed value proposition
visual:
  style: minimal
  typography: modern sans serif
  radius: rounded
  density: spacious
colors:
  primary: "#000000"
  secondary: "#FFFFFF"
  background: "#F5F5F5"
evidence: []
assumptions: []
```

Keep the context concise and reusable by the screenshot and integrated
skills. Do not invent a brand color when the project provides no evidence;
label a proposed color as an assumption.

### 2. Convert the brief into icon directions

Propose three materially different directions before committing to a final
concept:

1. **Symbolic** — express the core product action or value through one simple
   shape.
2. **Character** — use a distinctive, ownable character only when it fits the
   product personality and can survive reduction.
3. **Abstract** — express a brand idea through geometry, motion, or negative
   space when a literal symbol would be generic.

For each direction, state the user-provided hero object, the silhouette, the
primary and secondary components, palette, relationship to the product, and the
main small-size risk. Ask for a choice when the user is available. When the
request explicitly asks for generation without a review step, select the
strongest direction only after recording which brief inputs it satisfies.

### 3. Generate candidate concepts

Generate six independent candidates by default: two variants for each
direction. Label them `A1`, `A2`, `B1`, `B2`, `C1`, and `C2`, and preserve each
full-resolution result separately. Never ask the image model for a contact
sheet and never discard a returned candidate silently. Keep a candidate sheet
only as an additional preview.

Keep every candidate:

- square and centered with a deliberate safe area
- recognizable as a silhouette at 32×32 pixels
- high contrast with a restrained palette
- free of UI screenshots, tiny details, illegible text, and unnecessary
  decorative background elements
- consistent with the shared brand context

Use an image-generation or image-editing tool when available. For prompt-based
generation, describe the visual as one clean square image rather than asking
for a logo, brand mark, app icon, or icon asset; those terms often encourage
mockups, text, borders, and presentation frames. Keep the surrounding Skill
and delivery report explicit about the store-asset purpose.

Use an existing logo as a reference only when the user has the right to use
it. Do not copy third-party trademarks, stock art, or another app's distinctive
icon.

### Candidate design contract

Apply this compact visual budget before generating a batch:

- Build one dominant silhouette from roughly four to seven broad shapes.
- Use no more than two semantic subject colors plus the background unless the
  user supplies a different brand rule.
- Keep one defining feature; remove repeated texture, tiny highlights, thin
  outlines, and decorative marks.
- Use thick rounded forms and clear negative space. Avoid sharp tips, fragile
  lines, device frames, scene props, and uncontrolled photorealism.
- Check the black silhouette and the smallest export before recommending a
  candidate.

Choose one finish mode from the brand context before generating:

- **Vector-native** — flat colors, crisp curves, deliberate negative space,
  and no gradients when the product language is graphic and minimal.
- **Dimensional product render** — one sculptural subject, one or two coherent
  materials, one key light direction, restrained bevels, and a soft ambient
  shadow. The object must still read as a clean silhouette at 32×32; do not
  add a floor, props, reflections, or tiny surface detail just to make it look
  expensive.

For dimensional work, use a detail budget instead of adding arbitrary objects:

- **Hero form** — one dominant object occupying roughly 60–75% of the subject
  area and carrying the product metaphor.
- **Secondary component** — one meaningful cavity, lens, strap, hinge, core, or
  other interaction that comes from the user's brief and supports the hero.
- **Supporting cue** — at most one small detail, only if it survives at 180px;
  omit it when it becomes noise at 32px.
- **Finish system** — no more than two materials, one key light, one ambient
  fill, and a controlled background treatment.

Use a prompt structure like this for each independent candidate:

```text
Create one complete full-bleed 1:1 square image.
Background: use <named brand background color> in every open area.
Subject: <brief hero object> expressing <product connection>.
Components: <brief secondary component>; optional supporting cue <brief cue>.
Complexity: 4–7 broad shapes, one defining feature, no tiny details, readable at 32×32.
Color: two purposeful subject colors plus the background; maintain clear separation.
Composition: <brief composition>; centered with a deliberate safe area; keep the subject dominant and upright.
Finish: use <vector-native or dimensional product-render mode>; keep the
surface treatment coherent and the silhouette simple; no text or presentation frame.
Constraints: no words, letters, numbers, watermark, UI, border, device mockup,
scene props, uncontrolled photorealism, sharp tips, thin lines, or clutter.
```

Change only the candidate's direction, subject treatment, or palette mapping
between calls so the six outputs remain useful for comparison.

Keep the brief, each candidate prompt, and the selection rationale together.
If the generated details drift from the brief, reject the result or revise the
prompt; do not retrofit a rationale after the fact.

### Distinctiveness gate

Do not select the clearest generic symbol by default. Reject a candidate when
its identity depends on a checkmark, bell, lock, gear, cloud, document, card
stack, or another category symbol that could describe many unrelated apps.
Require one product-specific silhouette decision—such as an unusual aperture,
negative-space relationship, or repeatable character proportion—that survives
without text or a color legend. If no candidate passes this gate, generate a
new batch and preserve the rejected batch for comparison.

### 4. Evaluate and select

Render or inspect each candidate at 1024px, 180px, and 32px. Score clarity,
distinctiveness, ownability, contrast, brand fit, and platform safety. Treat
distinctiveness and ownability as gates, not optional polish. Reject candidates
whose key idea disappears after reduction, whose edges are clipped, whose
details depend on color alone, or whose concept is only a generic category
symbol.

Show the candidate sheet and recommendation when interaction is possible.
Otherwise select one candidate and explain the trade-off in the delivery
report. Preserve the candidate sheet or source concepts when the user may
want to iterate.

### 5. Export and report

Create a master source and raster exports only after selection. Prefer this
layout, adding files only when requested by the target platform:

```text
store-assets/icon/
├── icon-master.png
├── icon-1024.png
├── icon-512.png
├── icon-192.png
└── icon-180.png
```

When the selected concept uses simple geometry, refine it into a vector master
before producing raster exports. Keep the generated candidate as a preserved
reference, record the refinement in the delivery report, and derive every
platform size from the refined master so curves, colors, and safe area stay
consistent.

Verify the image mode, dimensions, safe area, and background treatment. Check
current Apple and Google requirements at execution time before labeling an
export as submission-ready; do not rely on remembered platform sizes.

Finish with a concise report containing the project, chosen direction,
candidate count, export paths, assumptions, and remaining QA items. Never
report success when a requested export or validation step was skipped.

## Guardrails

- Preserve the user's existing icon unless replacement is requested or
  clearly justified.
- Avoid text in icons by default; text becomes unreadable and localizes poorly.
- Keep generated work separate from source files and never overwrite existing
  exports without consent.
- Treat generated concepts as unverified until inspected at small size.
- If the project context is too sparse to make a grounded icon, deliver the
  analysis and proposed directions first instead of fabricating product
  meaning.
- Treat explicit user art direction as a hard constraint. Do not replace a
  requested object, component, material, or mood with a more convenient
  generic metaphor.

For the detailed review checklist, read
[references/icon-qa.md](references/icon-qa.md).
