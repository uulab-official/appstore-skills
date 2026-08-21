# Evidence providers

Evidence providers are opt-in readers for evidence that already exists. They
do not build an app, launch a simulator, install an APK/IPA, capture a screen,
upload a file, or publish anything.

The registry in
[`evidence-providers.yml`](evidence-providers.yml) is deliberately explicit:

- `build-record` reads `evidence/build.yml` and checks that the inspected
  revision, artifact identity, target platform, source, and timestamp are
  recorded.
- `simulator-source-captures` reads `evidence/captures.yml`, checks capture
  metadata, confirms each path stays under `screenshots/source/`, and verifies
  basic PNG/JPEG/WebP file signatures.

## Build evidence

Create `evidence/build.yml` from the inspected build, for example:

```yaml
schema_version: 1
revision: abc1234
artifact: ExampleApp-1.2.3.ipa
platform: ios
inspected_at: "2026-08-21T10:00:00Z"
source: release artifact supplied by the app project
```

This is an identity record, not a build command. A package version without a
revision or artifact identity remains blocked.

## Simulator/source capture evidence

Create `evidence/captures.yml` alongside real source images:

```yaml
schema_version: 1
captures:
  - path: screenshots/source/home.png
    platform: apple
    device_family: iphone
    locale: en-US
    captured_at: "2026-08-21T10:05:00Z"
    provenance: ios-simulator
```

The provider validates file identity and metadata; it cannot prove that a
human-operated simulator session was honest or that private data is absent.
Keep visual fidelity, privacy, accessibility, and product review in `QA.md`
and `release-report.md`.

## Usage

Inspect only the providers explicitly selected:

```bash
python scripts/inspect_evidence_providers.py \
  --provider-file skills/app-store-assets/references/evidence-providers.yml \
  --project-root ./my-app \
  --output-root ./my-app/store-assets \
  --platform apple \
  --locale en-US \
  --device-family iphone \
  --require-scope-coverage \
  --provider build-record \
  --provider simulator-source-captures \
  --format summary
```

`prepare_release_handoff.py` accepts the same provider selections. Without
`--provider`, it performs its existing filesystem checks and does not invoke a
provider. With a provider selected, the provider remains read-only and its
validated result replaces the corresponding handoff check.

Use `--max-age-days <days>` with the inspector or
`--max-evidence-age-days <days>` with the handoff when build and capture
evidence must be refreshed on a cadence. These options are opt-in and block
stale or future-dated timestamps. To bind `build-record` to the current Git
checkout, add `--require-current-revision` to either command. Exact revisions
and unambiguous hexadecimal prefixes are accepted; a non-Git project or a
mismatch remains blocked in this strict mode.
When `--platform` is supplied, the build record must match at least one
requested platform. The built-in compatibility aliases include `apple`/`ios`
and `google-play`/`android`; omit the flag when platform scope is intentionally
not being checked. The same scope is applied to every simulator source
capture, so an iOS capture cannot satisfy a Google Play-only handoff. Use
`--locale` to apply the same explicit scope to capture locales; separators are
normalized (`en_US` and `en-US` are equivalent), but locale scope is never
inferred. Use `--device-family` to require a named capture family such as
`iphone`, `ipad`, `android-phone`, or `android-tablet`; documented aliases such
as `ios-phone` are normalized, while device-family scope is also never inferred.
Add `--require-scope-coverage` when every requested platform × locale × device
family combination must have a source capture. This stricter check is opt-in;
without it, each capture only needs to match at least one requested value.
