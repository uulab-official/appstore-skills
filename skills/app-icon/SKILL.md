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

### 2. Propose icon directions

Propose three materially different directions before committing to a final
concept:

1. **Symbolic** — express the core product action or value through one simple
   shape.
2. **Character** — use a distinctive, ownable character only when it fits the
   product personality and can survive reduction.
3. **Abstract** — express a brand idea through geometry, motion, or negative
   space when a literal symbol would be generic.

For each direction, state the symbol, silhouette, palette, relationship to the
product, and the main small-size risk. Ask for a choice when the user is
available. When the request explicitly asks for generation without a review
step, select the strongest direction, record the decision, and continue.

### 3. Generate candidate concepts

Generate six candidates by default: two variants for each direction. Keep
every candidate:

- square and centered with a deliberate safe area
- recognizable as a silhouette at 32×32 pixels
- high contrast with a restrained palette
- free of UI screenshots, tiny details, illegible text, and unnecessary
  decorative background elements
- consistent with the shared brand context

Use an image-generation or image-editing tool when available. Use an existing
logo as a reference only when the user has the right to use it. Do not copy
third-party trademarks, stock art, or another app's distinctive icon.

### 4. Evaluate and select

Render or inspect each candidate at 1024px, 180px, and 32px. Score clarity,
distinctiveness, contrast, brand fit, and platform safety. Reject candidates
whose key idea disappears after reduction, whose edges are clipped, or whose
details depend on color alone.

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

For the detailed review checklist, read
[references/icon-qa.md](references/icon-qa.md).

