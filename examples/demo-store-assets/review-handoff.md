# Review handoff

```yaml
schema_version: 1
package: demo-store-assets
review_status: blocked
release_report_status: blocked
approval_status: pending
publish_status: not-run
```

This is a read-only reviewer aid. It does not approve, submit, upload, publish, or allocate experiment traffic.

## Review snapshot

- Package: `demo-store-assets`
- Release report: `blocked`
- Approval: `pending` (owner: not assigned)
- Baseline: `not-supplied`
- Assets: `57`

| Asset status | Count |
| --- | ---: |
| blocked | 2 |
| review | 55 |

## Manifest diff

No previous package baseline was supplied; current assets are labeled `baseline`.

| change | path | kind | platform | locale | status |
| --- | --- | --- | --- | --- | --- |
| baseline | evidence-adapters.yml | evidence-adapter-map | shared |  | review |
| baseline | evidence-providers.yml | evidence-provider-registry | shared |  | review |
| baseline | feature-graphic/example-app-feature.svg | feature-graphic-master | google-play |  | review |
| baseline | feature-graphic/template.yml | feature-graphic-template | google-play |  | review |
| baseline | localization-plan.yml | localization-plan | shared |  | review |
| baseline | metadata/copy-experiments.yml | store-copy-experiment | shared | en-US | review |
| baseline | metadata/experiments/variant-visibility.en-US.yml | store-copy-experiment-variant | shared | en-US | review |
| baseline | metadata/store-copy.en-US.yml | store-copy | shared | en-US | review |
| baseline | metadata/store-copy.ko-KR.yml | localized-store-copy | shared | ko-KR | review |
| baseline | platform-adapters.yml | platform-adapter-map | shared |  | review |
| baseline | promotional/example-app-hero.svg | promotional-master | shared |  | review |
| baseline | promotional/template.yml | promotional-template | shared |  | review |
| baseline | release-approval.yml | release-approval | shared |  | review |
| baseline | release-handoff.yml | release-handoff-report | shared |  | blocked |
| baseline | review-adapters.yml | review-adapter-registry | shared |  | review |
| baseline | review-handoff.md | review-handoff-summary | shared |  | blocked |
| baseline | terminology.yml | terminology-glossary | shared |  | review |
| baseline | web-assets/favicon/favicon-16x16.png | favicon-export | web |  | review |
| baseline | web-assets/favicon/favicon-32x32.png | favicon-export | web |  | review |
| baseline | web-assets/favicon/favicon.svg | favicon | web |  | review |
| baseline | web-assets/og/og-image.png | og-image-export | web |  | review |
| baseline | web-assets/og/og-image.svg | og-image | web |  | review |

## Optional review adapters

| id | kind | status | details |
| --- | --- | --- | --- |
| policy-review | policy | pending | missing evidence/policy-review.yml |
| accessibility-review | accessibility | pending | missing evidence/accessibility-review.yml |

## Blockers

- 2 manifest asset(s) are blocked.
- Product and platform approvals are missing.
- Real app or emulator screenshots are missing.

## Warnings

- The icon and marketing masters remain review concepts.
- Amazon Appstore and Samsung Galaxy Store profiles are documentation-linked concepts, not verified submissions.
- Build and simulator evidence providers are blocked because source evidence files are absent.
- The ko-KR copy is a localization draft without native or designated reviewer approval.
- Copy experiment variants are review-only with pending approvals; no traffic allocation or store API action ran.
- No previous package baseline was supplied for change comparison.
- Policy and accessibility review adapters are pending because no designated review evidence is present.

## Next actions

1. Resolve the listed blockers and regenerate the review handoff.
2. Record explicit human approval before treating the package as ready.
3. Review 55 draft/review assets with the product owner and designated locale reviewer.
4. Complete the selected policy/accessibility adapter reviews.

## Safety

`publish_status` is permanently `not-run`; this summary must not be used as a store submission record.
