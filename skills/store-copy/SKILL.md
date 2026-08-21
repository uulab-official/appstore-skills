---
name: store-copy
description: Draft evidence-backed App Store and Google Play listing copy from an app project, including titles, subtitles, descriptions, keywords, promotional text, and release notes. Use when an agent needs to write, refresh, compare, or audit store metadata without fabricating product claims.
---

# Store copy

Write store listing copy that explains the real product clearly, fits each
platform's current fields, and gives localization a stable source. Treat every
claim as product content that needs evidence and approval.

## Discover the product

Inspect:

- README, onboarding, help content, and existing store listings
- app metadata, navigation, visible features, and actual screenshots
- `brand-context.yml`, target audience, positioning, and approved terminology
- current `metadata/`, locale files, release notes, and policy-sensitive copy

Build an evidence table with the source path for every feature or claim. Mark
assumptions explicitly. Do not infer a shipped feature from a TODO, route name,
or unused component alone.

## Workflow

### 1. Define the messaging hierarchy

Summarize the product in this order:

1. What it is.
2. Who it helps.
3. The primary job it makes easier.
4. The strongest supporting capabilities.
5. A safe, evidence-backed reason to try it.

Draft three positioning directions when the product story is ambiguous. For
each, state the audience, promise, supporting proof, and risk. Choose one after
approval when possible; otherwise select the clearest conservative direction
and record the assumption.

### 2. Map copy to platform fields

Create a structured draft rather than one unbounded paragraph:

```yaml
schema_version: 1
locale: en-US
product: Example App
apple:
  name: Example App
  subtitle: Short evidence-backed value proposition
  promotional_text: Timely message for the current release
  description: |
    Full product description.
  keywords: [example, productivity]
  whats_new: What changed in this release.
google_play:
  short_description: Short product summary
  full_description: |
    Full product description.
evidence: []
assumptions: []
status: review
```

Verify current field limits, allowed characters, and platform policy guidance
at execution time. Keep one source draft per locale and platform; do not assume
that an Apple field maps directly to a Google Play field.

### 3. Write and fact-check

Use specific, plain language from the product's vocabulary. Prefer observable
benefits over vague superlatives. Remove or flag claims about rankings,
downloads, awards, security, health outcomes, money, performance, or guarantees
unless the project includes current evidence and approval.

Check that:

- every named feature is visible, shipped, or explicitly approved
- the description matches the screenshots and icon's product story
- the call to action does not promise an outcome the app cannot guarantee
- pricing, subscriptions, trials, permissions, and account requirements are
  disclosed when relevant and supported by project metadata
- no private data, internal URLs, placeholder text, or test content remains

### 4. Deliver the draft

Write the approved or review-ready copy under the requested output root:

```text
store-assets/metadata/
├── store-copy.en-US.yml
├── evidence.md
└── copy-review.md
```

Keep `evidence.md` concise and cite source paths. Use `copy-review.md` for
unsupported claims, field-limit checks, policy questions, and approval state.
Finish with a short delivery report. Do not mark copy as final when current
platform limits or product approval are missing.

## Guardrails

- Never fabricate reviews, user counts, ratings, awards, certifications, or
  competitive claims.
- Never hide material subscription, account, permission, or access conditions.
- Do not silently replace existing approved copy; show a diff or preserve the
  previous version.
- Keep copy factual enough to translate without guessing at product meaning.

Read [references/store-copy-qa.md](references/store-copy-qa.md) for the review
checklist.

