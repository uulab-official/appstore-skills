# Localization QA checklist

## Language and meaning

- Confirm the target locale and source locale are explicit.
- Check product names, feature names, glossary terms, tone, and formality.
- Check that benefits, limitations, pricing, permissions, and legal conditions
  retain the source meaning.
- Identify untranslated strings, machine-translation artifacts, false friends,
  and culturally confusing phrases.

## Layout and assets

- Check text expansion, line breaks, truncation, alignment, and safe areas.
- Check right-to-left layout where applicable.
- Check locale-specific dates, numbers, currencies, units, and punctuation.
- Verify fonts contain every character used in the asset.
- Use localized UI captures when the UI is visible and the locale supports it.

## Platform and delivery

- Verify current platform field limits and locale support at execution time.
- Confirm each output path and locale is recorded in `manifest.yml`.
- Confirm source and target assets are not accidentally mixed.
- Mark missing review or unsupported locale behavior as `review` or `blocked`.

