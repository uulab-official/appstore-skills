# Demo asset QA

## Scope

- Project: Example App (fictional)
- Run type: concept review fixture
- Locale: en-US
- Platforms: shared, web
- Generated: 2026-08-21

## Passed

- Four six-candidate icon batches were preserved for comparison.
- The icon design brief records the hero object, secondary component, material,
  palette, and avoid list; it remains `review` because product-owner approval
  does not exist for this fictional fixture.
- The fourth batch was screened for generic category symbols, product-family
  resemblance, and component hierarchy at
  180×180 and 32×32.
- A1 v4 was selected because its shell, recessed cavity, coral priority
  capsule, inset panel, and capture tab remain legible without becoming a
  generic ring, shield, or device.
- A1 v4 was refined once to remove the cylindrical hinge and preserve the
  requested task-capture tab before raster exports were produced.
- The selected icon is square, centered, text-free, and visually consistent
  with the example brand context.
- Icon exports were resized from one selected master.
- Favicon and OG SVGs use the same cobalt/coral visual system.
- OG copy is exact SVG text, the PNG export is 1200×630, and both include a
  visible demo disclaimer.
- Promotional and feature-graphic template specs record canvas, safe area,
  layout, copy limits, hero asset, claims, evidence, and output paths.
- Promotional and feature-graphic SVG concept masters were rendered from
  those specs and reviewed at full size and thumbnail size.
- The platform adapter map separates Apple, Google Play, and Web branches and
  records execution-time checks without claiming current platform acceptance.
- Amazon Appstore and Samsung Galaxy Store profiles are included as blocked,
  documentation-linked adapters; no live store submission is claimed.
- The evidence adapter map separates project facts, build identity, simulator
  captures, and release review; unavailable build and simulator evidence stays
  `blocked`.
- The evidence provider registry is explicitly opt-in and read-only; its build
  and simulator providers report missing evidence without running a project
  command.
- The release handoff was exercised in dry-run mode; it reports blockers and
  never runs a build, simulator, upload, or publish action.
- The release approval record is explicit and remains `pending`; technical
  checks cannot infer or bypass product-owner approval.
- Every manifest asset exists and is non-empty.

## Blocked or review-required

- No real app screens exist, so App Store and Google Play screenshots are
  intentionally not generated.
- Icon has not been approved as a production mark or checked against live
  trademark requirements.
- Apple, Google Play, and web platform requirements were not checked for a real
  submission.
- The feature-graphic artboard is a working concept; its current Play Console
  acceptance dimensions and crop behavior still require execution-time review.
- The adapter map is a review plan; no Apple or Android device captures are
  available to verify those branches.
- Build and simulator evidence adapters are blocked because this repository has
  no app project, build artifact, or real device capture.
- The handoff remains `blocked` until build identity and real source captures
  are supplied.
- Even after those checks pass, the handoff remains `pending_approval` until
  the approval record is completed.
- The release approval record has no owner, decision, decision time, or
  evidence because this fixture intentionally has no approving human.
- The provider registry snapshot is kept in the demo package so the exact
  read-only checks used by the handoff are inspectable.
- The localization plan includes en-US source copy and a ko-KR review draft;
  the terminology validator confirms required mappings and forbidden terms.
- Store copy is a draft and has not passed product, policy, or platform field
  review.
- The ko-KR copy has not received native or designated reviewer approval and
  no localized screenshot/UI capture is supplied.

## Decision

This package is a review fixture only. It must remain `blocked` until real app
screens, product approval, current platform checks, and any required legal or
localization review are available.
