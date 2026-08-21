# Release check checklist

## Package integrity

- Confirm the output root, run identity, generated date, and source revision.
- Confirm `brand-context.yml`, `manifest.yml`, and `QA.md` are present when
  required by the workflow.
- Confirm every manifest path exists and every generated file is readable.
- Confirm file type, dimensions, color profile, transparency, and file size.
- Confirm no secrets, private data, test content, or internal URLs are present.

## Product fidelity

- Confirm screenshots show real product UI or are labeled concepts.
- Confirm icon, copy, screenshots, promotional art, and OG images describe the
  same product.
- Confirm every advertised feature has evidence.
- Confirm source captures, licenses, trademarks, and supplied assets have a
  recorded approval path.

## Platform and locale

- Confirm each target platform and device family has the requested outputs.
- Check current official requirements and record URLs and dates.
- Confirm locale paths, translations, typography, RTL behavior, and localized
  UI captures where required.
- Confirm platform metadata fields and current character or file limits.

## Report schema

Use a compact table in `release-report.md`:

| Check | Scope | Status | Evidence | Action |
| --- | --- | --- | --- | --- |
| Screenshot UI fidelity | Apple iPhone, en-US | pass | source capture path | None |
| Google Play tablet output | Google Play | block | Missing tablet source | Capture tablet UI |

End with:

```yaml
summary_status: blocked
blockers: []
warnings: []
platform_docs_checked: []
human_review_required: true
```

