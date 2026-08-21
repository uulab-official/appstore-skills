---
name: favicon
description: Create a recognizable favicon and web icon set from an app or website project, existing app icon, logo, and brand context. Use when an agent needs to add or refresh browser-tab icons, pinned-site icons, touch icons, or related web manifest assets.
---

# Favicon

Create a compact web icon system that remains recognizable in browser tabs,
bookmarks, launchers, and link previews. Prefer a simplified derivative of the
approved app icon or logo so the web and product identity stay connected.

## Discover the source

Inspect the project before designing:

- existing `app-icon` output, logo files, and brand guidelines
- `brand-context.yml`, theme tokens, and favicon or manifest links
- `index.html`, framework metadata, `public/`, and static asset folders
- the website's background, typography, and light/dark behavior

Record the source asset and any assumptions. If no approved identity exists,
propose a simple mark and label it as a direction rather than silently
claiming brand approval.

## Workflow

### 1. Simplify the approved mark

Design one primary direction and up to two alternatives only when the source
identity does not reduce cleanly. Keep the mark:

- legible at small browser-tab sizes
- centered with a deliberate safe area
- high-contrast in both light and dark browser chrome where relevant
- free of tiny text, screenshots, and unnecessary detail
- consistent with `brand-context.yml` and the approved app icon

Do not place a full wordmark in a favicon unless the mark remains readable at
the target size and the user explicitly approves it.

### 2. Export a web icon family

Create a master source and the formats requested by the project. A typical
package is:

```text
web-assets/favicon/
├── favicon.svg
├── favicon.ico
├── favicon-32x32.png
├── favicon-16x16.png
└── apple-touch-icon.png
```

Use vector output when the mark benefits from it. Generate raster variants from
the approved master, inspect each at 1:1, and avoid repeated lossy rescaling.
Verify the final dimensions, color profile, transparency, and edge treatment.

### 3. Integrate only when in scope

If the user asks for integration, inspect the existing HTML or framework head
configuration and add the smallest correct set of links. Preserve existing
metadata and avoid duplicating tags. A typical integration may include:

```html
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
```

Adapt paths and supported formats to the project. Do not claim that the snippet
covers every browser or pinned-site surface without checking the target.

### 4. Review and report

Inspect the icon in a tab-sized preview, bookmark-sized preview, light/dark
background, and at 1:1 pixel scale. Report the source mark, chosen direction,
generated paths, integration changes, assumptions, and unresolved browser or
platform checks.

Read [references/web-favicon-qa.md](references/web-favicon-qa.md) for the
detailed review checklist.

## Guardrails

- Keep generated files outside source assets until the user requests
  integration.
- Do not overwrite an existing favicon without preserving or reviewing it.
- Do not invent a second visual identity for the web without recording the
  reason and approval state.
- Treat synthetic concepts as drafts until the actual site context has been
  checked.

