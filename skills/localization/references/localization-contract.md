# Localization contract

Use a localization plan and glossary beside a store-asset package when more
than one locale is in scope. The plan identifies the source locale, every
target locale, the reviewer, and the copy file. The glossary records approved
source terms, locale-specific terms, required terms, and terms to avoid.

Validate the pair with:

```bash
python scripts/validate_localization_specs.py \
  ./store-assets/localization-plan.yml \
  ./store-assets/terminology.yml \
  --package-root ./store-assets
```

The check verifies:

- every planned locale has an existing copy file with a matching `locale`
- the source locale is present exactly once
- every target copy preserves the source locale's Apple and Google Play field
  structure, with no silently missing or untracked platform fields
- every glossary entry has a status, source term, and mapping for every locale
- required localized terms occur in the corresponding copy file
- `do_not_use` terms do not occur in the copy file

This is a terminology and structure check, not a fluency or cultural review.
Keep target copies at `review` until the designated or native reviewer signs
off on meaning, tone, layout, legal conditions, and platform limits.
