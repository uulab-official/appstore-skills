---
name: app-store-screenshots
description: Turn real app screens into coherent App Store and Google Play marketing screenshot sets with grounded copy, platform adaptations, and delivery QA. Use when an agent needs to create, refresh, storyboard, or package store screenshots from a running app, simulator captures, project assets, or supplied screen images.
---

# App Store screenshots

Make store screenshots communicate product value while remaining faithful to
the real app. Add composition, copy, device framing, and brand treatment; do
not redraw or materially alter the app UI and present a concept as a final
product screen.

## Inputs

Discover the strongest available screen sources in this order:

1. Run the app and capture representative screens when the project can be
   launched safely.
2. Use existing simulator/device captures in `screenshots/`, `assets/`, or
   `public/`.
3. Inspect routes, navigation, README content, and feature descriptions to
   understand what each screen proves.
4. Use user-supplied captures or a screen checklist when the app cannot run.

Also inspect the existing `brand-context.yml`, theme tokens, typography,
colors, and icon. Record the source path for every selected screen. If no real
screen source is available, stop short of final screenshot generation and
deliver a storyboard plus the exact captures needed to continue.

## Workflow

### 1. Establish the product story

Extract evidence-backed features and benefits. Select three to eight screens
that tell a progression such as:

```text
01 Hook          Why this app matters
02 Core value    The main job it makes easier
03 Key feature   A meaningful capability
04 Secondary     A useful supporting capability
05 Trust         Convenience, personalization, or confidence
06 Closing       A memorable product promise
```

Adjust the count to the product. Do not include a screen solely because it is
easy to capture. Prefer screens with a clear visual hierarchy and a benefit a
new user can understand quickly.

### 2. Write the storyboard and copy

Create a table before composing:

| Order | Source screen | Message | Evidence | Layout | Risk |
| --- | --- | --- | --- | --- | --- |
| 01 | `path/to/screen` | Short benefit | Feature or copy source | Copy above UI | Unsupported claim? |

Use short, specific, localized copy. Keep the headline focused on one benefit
and avoid claims about performance, security, popularity, or outcomes unless
the project provides evidence. Reuse the product's vocabulary. If the user
has not supplied a locale, use the app's existing locale and state it.

Propose the storyboard for approval when possible. If the user has already
specified the message or requested an uninterrupted run, choose the clearest
story and document the assumption.

### 3. Choose a visual system

Derive the composition from the shared brand context and real UI. Choose one
primary treatment, such as minimal, editorial, bold, playful, professional,
luxury, or developer-focused. Define the background, type scale, alignment,
device treatment, corner radius, and contrast before producing the set.

Keep the system consistent across the set while allowing a distinct opening
frame. Favor generous whitespace and a single hierarchy. Preserve readable UI
content; do not cover important controls with captions or decorative layers.

### 4. Compose with real UI

Use the selected source screen as the content layer. You may add a background,
headline, subhead, device frame, crop, shadow, or controlled decorative shape.
Do not:

- invent new screens or controls
- change the app's data, labels, navigation, or feature behavior
- blur or hide a defect merely to imply a feature works
- stretch a capture until text or controls become misleading
- use an AI-generated substitute for a real product screen in a final asset

If a source screen needs cleanup, make only non-semantic corrections such as
cropping, scaling, color-profile conversion, or removal of simulator chrome.
Label any other edit in the QA report.

### 5. Adapt for platforms

Build a source composition that can be adapted without losing the story. Then
export Apple and Google Play variants using the current official submission
requirements checked at execution time. Read
[references/platform-delivery.md](references/platform-delivery.md) for the
verification checklist.

Use a structure like:

```text
store-assets/screenshots/
├── source/
├── apple/
│   ├── iphone/
│   └── ipad/
└── google-play/
    ├── phone/
    └── tablet/
```

Keep source compositions separate from platform exports. Avoid claiming that
one size covers every device family unless the current platform rules confirm
it.

### 6. Review and report

Review the complete set in sequence and at thumbnail size. Check message
clarity, factual fidelity, UI legibility, alignment, safe areas, text clipping,
locale consistency, color contrast, and duplicate stories. Deliver a report
with the selected screens, copy sources, output paths, platform requirements
checked, assumptions, and unresolved issues.

## Failure handling

- If the app cannot run, use supplied or repository captures and mark the
  source confidence in the report.
- If a feature is only implied by code, do not advertise it as shipped without
  a visible screen or explicit product evidence.
- If a screen is too low resolution, request a new capture or produce a
  storyboard only; do not upscale it into a misleading final asset.
- If a platform requirement is unclear, verify the official documentation and
  leave the export unmarked as submission-ready until verified.
- If the user asks for a concept mockup, label every synthetic screen clearly
  and keep it outside the final submission directory.

