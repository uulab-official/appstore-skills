---
name: og-image
description: Design and export a branded Open Graph and social sharing image from a web or app project, using grounded product copy, real UI or approved brand assets, and channel-aware metadata. Use when an agent needs to create or refresh link-preview images for websites, product pages, documentation, or app launch pages.
---

# OG image

Create a social preview image that makes a shared URL identifiable and useful
without pretending to be a product screen. Use the shared brand context and
evidence-backed copy, then keep the image composition readable when a social
platform crops or scales it.

## Discover the page

Inspect:

- the page title, description, route, and existing Open Graph metadata
- `brand-context.yml`, logo, app icon, design tokens, and typography
- the page's actual UI or a supplied screenshot when it helps explain the
  shared link
- locale, audience, and channel requirements requested by the user

Separate confirmed page claims from marketing suggestions. Do not expose
private user data, tokens, internal URLs, unreleased features, or content that
the page does not actually contain.

## Workflow

### 1. Define the message

Choose one message for the shared URL:

- product name and concise value proposition
- article or documentation title and useful category
- launch or campaign headline grounded in the supplied brief

Keep copy short enough to survive thumbnail rendering. Preserve the page's
language and spelling. Avoid unsupported claims such as rankings, guarantees,
user counts, or performance promises.

### 2. Choose the composition

Use the brand context to define background, mark placement, type hierarchy,
contrast, and safe zones. Use actual UI only when it helps identify the page;
otherwise prefer a clean brand composition. Keep the primary message away from
edges likely to be cropped and ensure it remains legible without hover or
interaction.

Create one primary direction and up to two alternatives when the brand or
message is ambiguous. Ask for approval when possible. If the user requests an
uninterrupted generation pass, choose the most conservative direction and
record the assumption.

### 3. Export and integrate

Generate a high-quality master and the requested channel variants. Use the
standard Open Graph baseline only when it matches the target channels; verify
any channel-specific requirements at execution time. A typical package is:

```text
web-assets/og/
├── og-image-master.png
├── og-image.png
└── social-variants/
```

If integration is requested, update the page's metadata using the existing
framework conventions. Preserve existing title and description values unless
the user asks to change them. A typical HTML shape is:

```html
<meta property="og:title" content="Evidence-backed page title">
<meta property="og:description" content="Evidence-backed page summary">
<meta property="og:image" content="https://example.com/og-image.png">
```

Use an absolute, publicly reachable URL when the deployment requires it and
record any environment-specific limitation.

### 4. Validate the preview

Inspect the output at full size, thumbnail size, light/dark context, and likely
crop positions. Verify text legibility, contrast, asset URL, image dimensions,
metadata consistency, and locale. Check a deployed or production-like page
when available; a local path alone does not prove that a social crawler can
fetch the image.

Read [references/og-image-qa.md](references/og-image-qa.md) for the detailed
checklist.

## Guardrails

- Keep the preview faithful to the linked page and supplied brand assets.
- Never include secrets, private data, or fabricated testimonials in a public
  social image.
- Keep concept compositions outside the final public asset directory until
  approved.
- Do not overwrite existing metadata or image files without preserving the
  current state or receiving permission.

