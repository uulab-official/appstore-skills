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
- Assets: `58`

| Asset status | Count |
| --- | ---: |
| blocked | 2 |
| review | 56 |

## Manifest diff

| change | path | kind | platform | locale | status |
| --- | --- | --- | --- | --- | --- |
| baseline | evidence-adapters.yml | evidence-adapter-map | shared |  | review |
| baseline | evidence-providers.yml | evidence-provider-registry | shared |  | review |
| baseline | feature-graphic/example-app-feature.svg | feature-graphic-master | google-play |  | review |
| baseline | feature-graphic/template.yml | feature-graphic-template | google-play |  | review |
| baseline | icon/concepts-v2/A1.png | app-icon-candidate | shared |  | review |
| baseline | icon/concepts-v2/A2.png | app-icon-candidate | shared |  | review |
| baseline | icon/concepts-v2/B1.png | app-icon-candidate | shared |  | review |
| baseline | icon/concepts-v2/B2.png | app-icon-candidate | shared |  | review |
| baseline | icon/concepts-v2/C1.png | app-icon-candidate | shared |  | review |
| baseline | icon/concepts-v2/C2.png | app-icon-candidate | shared |  | review |
| baseline | icon/concepts-v3/A1.png | app-icon-candidate | shared |  | review |
| baseline | icon/concepts-v3/A2.png | app-icon-candidate | shared |  | review |
| baseline | icon/concepts-v3/B1.png | app-icon-candidate | shared |  | review |
| baseline | icon/concepts-v3/B2.png | app-icon-candidate | shared |  | review |
| baseline | icon/concepts-v3/C1.png | app-icon-candidate | shared |  | review |
| baseline | icon/concepts-v3/C2.png | app-icon-candidate | shared |  | review |
| baseline | icon/concepts-v4/A1-refined.png | app-icon-refined-master | shared |  | review |
| baseline | icon/concepts-v4/A1.png | app-icon-candidate | shared |  | review |
| baseline | icon/concepts-v4/A2.png | app-icon-candidate | shared |  | review |
| baseline | icon/concepts-v4/B1.png | app-icon-candidate | shared |  | review |
| baseline | icon/concepts-v4/B2.png | app-icon-candidate | shared |  | review |
| baseline | icon/concepts-v4/C1.png | app-icon-candidate | shared |  | review |
| baseline | icon/concepts-v4/C2.png | app-icon-candidate | shared |  | review |
| baseline | icon/concepts/A1.png | app-icon-candidate | shared |  | review |
| baseline | icon/concepts/A2.png | app-icon-candidate | shared |  | review |
| baseline | icon/concepts/B1.png | app-icon-candidate | shared |  | review |
| baseline | icon/concepts/B2.png | app-icon-candidate | shared |  | review |
| baseline | icon/concepts/C1.png | app-icon-candidate | shared |  | review |
| baseline | icon/concepts/C2.png | app-icon-candidate | shared |  | review |
| baseline | icon/concepts/legacy-v1.png | app-icon-previous-concept | shared |  | review |
| baseline | icon/icon-1024.png | app-icon-export | shared |  | review |
| baseline | icon/icon-180.png | app-icon-export | shared |  | review |
| baseline | icon/icon-192.png | app-icon-export | shared |  | review |
| baseline | icon/icon-512.png | app-icon-export | shared |  | review |
| baseline | icon/icon-design-brief.yml | app-icon-design-brief | shared |  | review |
| baseline | icon/icon-master.png | app-icon-master | shared |  | review |
| baseline | icon/previous/icon-master-dimensional-v3.png | app-icon-previous-master | shared |  | review |
| baseline | icon/previous/icon-master-flat-v2.svg | app-icon-previous-master | shared |  | review |
| baseline | icon/selection.md | app-icon-selection | shared |  | review |
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
| baseline | review-assignment.yml | reviewer-assignment | shared |  | review |
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
| privacy-review | privacy | pending | missing evidence/privacy-review.yml |

## Reviewer assignment

- Status: `pending`
- Owner: `not assigned`
- History events: `1`

| id | role | required | scope | status | assigned_to | decision | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| product-owner | product | true | product-claims, metadata, visual-assets | pending | not assigned | pending | none |
| native-locale-reviewer | localization | true | localized-store-copy, terminology, localized-layout | pending | not assigned | pending | none |
| privacy-reviewer | privacy | true | data-collection, disclosures, permissions | pending | not assigned | pending | none |

### Assignment changes

- Baseline: `not-supplied`
- No previous reviewer assignment baseline supplied.

### Adapter coverage

- Status: `covered`
| adapter | status | reviewers |
| --- | --- | --- |
| policy-review | covered | product-owner (pending) |
| accessibility-review | covered | native-locale-reviewer (pending) |
| privacy-review | covered | privacy-reviewer (pending) |

## Blockers

- 2 manifest asset(s) are blocked
- Product and platform approvals are missing.
- Real app or emulator screenshots are missing.

## Warnings

- A1 v4 is a refined demo concept and not a production-approved mark.
- Amazon Appstore and Samsung Galaxy Store profiles are documentation-linked concepts, not verified submissions.
- Build and simulator evidence adapters are blocked because no real app project or device captures are present.
- Opt-in build and simulator evidence providers are blocked because their source evidence files are absent.
- Platform requirements were not checked for a live submission.
- Policy, accessibility, and privacy review adapters are opt-in and pending because no designated review evidence is present.
- Promotional and feature-graphic masters are concept compositions and not approved campaign assets.
- Reviewer assignment is pending: required human decisions are not complete.
- The copy experiment variants are review-only with pending approvals; no traffic allocation or store API action ran.
- The feature-graphic working artboard has not been checked against current Play Console requirements.
- The icon design brief is still in review because product-owner approval is missing.
- The ko-KR copy is a localization draft without native or designated reviewer approval.
- The platform adapter map is a review plan; Apple and Android source captures are missing.
- The release approval record is pending; no human decision is inferred from structural checks.
- The release handoff is a dry-run report only; no build, simulator, upload, or publish action ran.
- The review handoff summary is a diff-friendly triage aid; no previous package baseline was supplied.
- accessibility-review review adapter is pending: missing evidence/accessibility-review.yml
- policy-review review adapter is pending: missing evidence/policy-review.yml
- privacy-review review adapter is pending: missing evidence/privacy-review.yml

## Next actions

1. Resolve the listed blockers and regenerate the review handoff.
2. Record explicit human approval before treating the package as ready.
3. Review 56 draft/review asset(s) with the product owner.
4. Complete the selected policy, accessibility, and privacy adapter reviews.
5. Assign and complete the required reviewer decisions in review-assignment.yml.

## Safety

`publish_status` is permanently `not-run`; this summary must not be used as a store submission record.
