#!/usr/bin/env python3
"""Inspect selected evidence providers without executing project commands."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from itertools import product
import json
from pathlib import Path
import re
import subprocess
import sys

from validate_provider_specs import provider_records, validate as validate_provider_registry
from validate_store_output import read_png_metadata


DEFAULT_PROVIDER_FILE = (
    Path(__file__).resolve().parents[1]
    / "skills/app-store-assets/references/evidence-providers.yml"
)
FIELD_LINE = re.compile(r"^\s{4}([a-z][a-z0-9_-]*):\s*(.*?)\s*$")
TOP_LEVEL_FIELD_LINE = re.compile(r"^\s{0,2}([a-z][a-z0-9_-]*):\s*(.*?)\s*$")
CAPTURE_LINE = re.compile(r"^\s{2}-\s+path:\s*(.*?)\s*$")
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
PLATFORM_ALIASES = {
    "apple": {"apple", "ios"},
    "google-play": {"google-play", "android"},
    "web": {"web"},
    "amazon-appstore": {"amazon-appstore", "fire"},
    "samsung-galaxy-store": {"samsung-galaxy-store", "android"},
}
DEVICE_FAMILY_ALIASES = {
    "iphone": {"iphone", "ios-phone"},
    "ipad": {"ipad", "ios-tablet"},
    "android-phone": {"android-phone", "android-handset"},
    "android-tablet": {"android-tablet", "android-large-screen"},
}


def unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def parse_list(value: str) -> list[str]:
    value = value.strip()
    if not (value.startswith("[") and value.endswith("]")):
        return []
    contents = value[1:-1].strip()
    if not contents:
        return []
    return [unquote(item.strip()) for item in contents.split(",") if item.strip()]


def read_top_level_fields(path: Path) -> tuple[dict[str, str], list[str]]:
    fields: dict[str, str] = {}
    errors: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        return {}, [f"cannot read {path}: {error}"]
    if not re.search(r"^schema_version:\s*1\s*$", text, re.MULTILINE):
        errors.append("must declare schema_version: 1")
    for line in text.splitlines():
        match = TOP_LEVEL_FIELD_LINE.match(line)
        if match:
            key, value = match.groups()
            fields[key] = unquote(value)
    return fields, errors


def capture_records(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        return [], [f"cannot read {path}: {error}"]
    errors: list[str] = []
    if not re.search(r"^schema_version:\s*1\s*$", text, re.MULTILINE):
        errors.append("must declare schema_version: 1")
    records: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for line in text.splitlines():
        capture_match = CAPTURE_LINE.match(line)
        if capture_match:
            if current is not None:
                records.append(current)
            current = {"path": unquote(capture_match.group(1))}
            continue
        if current is None:
            continue
        field_match = FIELD_LINE.match(line)
        if field_match:
            key, value = field_match.groups()
            current[key] = unquote(value)
    if current is not None:
        records.append(current)
    return records, errors


def parse_timestamp(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed


def valid_timestamp(value: str) -> bool:
    return parse_timestamp(value) is not None


def freshness_error(label: str, value: str, max_age_days: int | None) -> str | None:
    if max_age_days is None:
        return None
    parsed = parse_timestamp(value)
    if parsed is None:
        return None
    age = datetime.now(timezone.utc) - parsed
    if age.total_seconds() < 0:
        return f"{label} cannot be in the future"
    if age > timedelta(days=max_age_days):
        return f"{label} is older than max age ({max_age_days} days)"
    return None


def platform_family(value: str) -> set[str]:
    normalized = value.strip().lower().replace("_", "-").replace(" ", "-")
    for canonical, aliases in PLATFORM_ALIASES.items():
        if normalized == canonical or normalized in aliases:
            return {canonical, *aliases}
    return {normalized}


def platform_matches(recorded: str, expected: list[str]) -> bool:
    recorded_normalized = recorded.strip().lower().replace("_", "-").replace(" ", "-")
    return any(recorded_normalized in platform_family(item) for item in expected)


def locale_matches(recorded: str, expected: list[str]) -> bool:
    recorded_normalized = recorded.strip().lower().replace("_", "-")
    return any(recorded_normalized == item.strip().lower().replace("_", "-") for item in expected)


def device_family_matches(recorded: str, expected: list[str]) -> bool:
    recorded_normalized = recorded.strip().lower().replace("_", "-").replace(" ", "-")
    for item in expected:
        expected_normalized = item.strip().lower().replace("_", "-").replace(" ", "-")
        aliases = next(
            (
                aliases
                for canonical, aliases in DEVICE_FAMILY_ALIASES.items()
                if expected_normalized == canonical or expected_normalized in aliases
            ),
            {expected_normalized},
        )
        if recorded_normalized in aliases:
            return True
    return False


def scope_coverage_missing(
    records: list[dict[str, str]],
    expected_platforms: list[str],
    expected_locales: list[str],
    expected_device_families: list[str],
) -> list[tuple[str | None, str | None, str | None]]:
    dimensions = (
        ("platform", expected_platforms, platform_matches),
        ("locale", expected_locales, locale_matches),
        ("device_family", expected_device_families, device_family_matches),
    )
    if not any(values for _, values, _ in dimensions):
        return []
    options = [values or [None] for _, values, _ in dimensions]
    covered: set[tuple[str | None, str | None, str | None]] = set()
    for record in records:
        matched: list[str | None] = []
        valid = True
        for field, expected, matcher in dimensions:
            if not expected:
                matched.append(None)
                continue
            recorded = record.get(field, "")
            match = next((item for item in expected if matcher(recorded, [item])), None)
            if match is None:
                valid = False
                break
            matched.append(match)
        if valid:
            covered.add(tuple(matched))
    return [combination for combination in product(*options) if combination not in covered]


def format_scope_combination(combination: tuple[str | None, str | None, str | None]) -> str:
    labels = ("platform", "locale", "device_family")
    return ", ".join(
        f"{label}={value}"
        for label, value in zip(labels, combination)
        if value is not None
    )


def current_git_revision(project_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(project_root), "rev-parse", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    revision = result.stdout.strip()
    return revision if result.returncode == 0 and revision else None


def revisions_match(recorded: str, current: str | None) -> bool:
    if current is None:
        return False
    recorded = recorded.strip().lower()
    current = current.strip().lower()
    if recorded == current:
        return True
    if len(recorded) < 7 or len(current) < 7:
        return False
    if not all(character in "0123456789abcdef" for character in recorded + current):
        return False
    return current.startswith(recorded) or recorded.startswith(current)


def image_error(path: Path) -> str | None:
    if path.suffix.lower() not in IMAGE_SUFFIXES:
        return f"unsupported image extension: {path.name}"
    try:
        data = path.read_bytes()
    except OSError as error:
        return f"cannot read image: {error}"
    if not data:
        return "image is empty"
    suffix = path.suffix.lower()
    if suffix == ".png":
        metadata = read_png_metadata(path)
        return metadata if isinstance(metadata, str) else None
    if suffix in {".jpg", ".jpeg"}:
        if data[:2] != b"\xff\xd8" or data[-2:] != b"\xff\xd9":
            return "invalid JPEG start or end marker"
        return None
    if data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        return "invalid WebP RIFF/WEBP signature"
    return None


def result(provider_id: str, kind: str, status: str, details: str) -> dict[str, object]:
    return {"id": provider_id, "kind": kind, "status": status, "details": details}


def inspect_build(
    provider: dict[str, str],
    output_root: Path,
    max_age_days: int | None = None,
    expected_revision: str | None = None,
    require_current_revision: bool = False,
    expected_platforms: list[str] | None = None,
) -> dict[str, object]:
    provider_id = provider["id"]
    evidence_path = output_root / provider["evidence_path"]
    if not evidence_path.is_file():
        return result(provider_id, "build", "blocked", f"missing {provider['evidence_path']}")
    fields, errors = read_top_level_fields(evidence_path)
    required = parse_list(provider.get("required_fields", ""))
    missing = [field for field in required if not fields.get(field)]
    if missing:
        errors.append("missing fields: " + ", ".join(missing))
    if fields.get("inspected_at") and not valid_timestamp(fields["inspected_at"]):
        errors.append("inspected_at is not an ISO-8601 timestamp")
    if fields.get("inspected_at"):
        stale_error = freshness_error(
            "build evidence inspected_at",
            fields["inspected_at"],
            max_age_days,
        )
        if stale_error:
            errors.append(stale_error)
    if require_current_revision:
        recorded_revision = fields.get("revision", "")
        if recorded_revision:
            if expected_revision is None:
                errors.append("build evidence revision cannot be matched because current project revision is unavailable")
            elif not revisions_match(recorded_revision, expected_revision):
                errors.append(
                    "build evidence revision does not match current project revision "
                    f"(recorded: {recorded_revision}, current: {expected_revision})"
                )
    recorded_platform = fields.get("platform", "")
    if expected_platforms and recorded_platform and not platform_matches(recorded_platform, expected_platforms):
        errors.append(
            "build evidence platform does not match requested platforms "
            f"(recorded: {recorded_platform}, requested: {', '.join(expected_platforms)})"
        )
    if errors:
        return result(provider_id, "build", "blocked", "; ".join(errors))
    return result(provider_id, "build", "pass", f"validated {provider['evidence_path']}")


def inspect_simulator(
    provider: dict[str, str],
    output_root: Path,
    max_age_days: int | None = None,
    expected_platforms: list[str] | None = None,
    expected_locales: list[str] | None = None,
    expected_device_families: list[str] | None = None,
    require_scope_coverage: bool = False,
) -> dict[str, object]:
    provider_id = provider["id"]
    evidence_path = output_root / provider["evidence_path"]
    if not evidence_path.is_file():
        return result(provider_id, "simulator", "blocked", f"missing {provider['evidence_path']}")
    records, errors = capture_records(evidence_path)
    if not records:
        errors.append("captures must contain at least one record")
    required = parse_list(provider.get("required_fields", ""))
    capture_root = Path(provider["capture_root"])
    output_resolved = output_root.resolve()
    seen_capture_paths: set[str] = set()
    for index, record in enumerate(records, start=1):
        path_value = record.get("path", "")
        if path_value:
            path_key = Path(path_value).as_posix()
            if path_key in seen_capture_paths:
                errors.append(f"capture {index} path is duplicated: {path_value}")
            else:
                seen_capture_paths.add(path_key)
        missing = [field for field in required if not record.get(field)]
        if missing:
            errors.append(f"capture {index} missing fields: {', '.join(missing)}")
            continue
        relative = Path(record["path"])
        if relative.is_absolute() or ".." in relative.parts:
            errors.append(f"capture {index} path escapes output root: {record['path']}")
            continue
        try:
            relative.relative_to(capture_root)
        except ValueError:
            errors.append(f"capture {index} path is outside {capture_root}: {record['path']}")
            continue
        capture_path = (output_root / relative).resolve()
        try:
            capture_path.relative_to(output_resolved)
        except ValueError:
            errors.append(f"capture {index} path escapes output root: {record['path']}")
            continue
        if not capture_path.is_file():
            errors.append(f"capture {index} file is missing: {record['path']}")
            continue
        image_problem = image_error(capture_path)
        if image_problem:
            errors.append(f"capture {index} {record['path']}: {image_problem}")
        recorded_platform = record.get("platform", "")
        if expected_platforms and recorded_platform and not platform_matches(recorded_platform, expected_platforms):
            errors.append(
                f"capture {index} platform does not match requested platforms "
                f"(recorded: {recorded_platform}, requested: {', '.join(expected_platforms)})"
            )
        recorded_locale = record.get("locale", "")
        if expected_locales and recorded_locale and not locale_matches(recorded_locale, expected_locales):
            errors.append(
                f"capture {index} locale does not match requested locales "
                f"(recorded: {recorded_locale}, requested: {', '.join(expected_locales)})"
            )
        recorded_device_family = record.get("device_family", "")
        if expected_device_families and recorded_device_family and not device_family_matches(
            recorded_device_family,
            expected_device_families,
        ):
            errors.append(
                f"capture {index} device family does not match requested device families "
                f"(recorded: {recorded_device_family}, requested: {', '.join(expected_device_families)})"
            )
        if not valid_timestamp(record["captured_at"]):
            errors.append(f"capture {index} captured_at is not an ISO-8601 timestamp")
        stale_error = freshness_error(
            f"capture {index} captured_at",
            record["captured_at"],
            max_age_days,
        )
        if stale_error:
            errors.append(stale_error)
    if require_scope_coverage and records:
        missing_scope = scope_coverage_missing(
            records,
            expected_platforms or [],
            expected_locales or [],
            expected_device_families or [],
        )
        if missing_scope:
            preview = "; ".join(format_scope_combination(item) for item in missing_scope[:12])
            remainder = len(missing_scope) - 12
            if remainder > 0:
                preview += f"; ... and {remainder} more"
            errors.append(f"source capture scope coverage is incomplete (missing: {preview})")
    if errors:
        return result(provider_id, "simulator", "blocked", "; ".join(errors))
    return result(
        provider_id,
        "simulator",
        "pass",
        f"validated {len(records)} source capture(s) under {capture_root}",
    )


def inspect_provider(
    provider_id: str,
    project_root: Path,
    output_root: Path,
    provider_file: Path,
    max_age_days: int | None = None,
    expected_revision: str | None = None,
    require_current_revision: bool = False,
    expected_platforms: list[str] | None = None,
    expected_locales: list[str] | None = None,
    expected_device_families: list[str] | None = None,
    require_scope_coverage: bool = False,
) -> dict[str, object]:
    provider_file = provider_file.resolve()
    registry_errors = validate_provider_registry(provider_file)
    if registry_errors:
        return result(provider_id, "unknown", "blocked", "invalid provider registry: " + "; ".join(registry_errors))
    text = provider_file.read_text(encoding="utf-8")
    provider = next((item for item in provider_records(text) if item.get("id") == provider_id), None)
    if provider is None:
        return result(provider_id, "unknown", "blocked", "provider is not declared in the registry")
    if provider["kind"] == "build":
        current_revision = expected_revision
        if require_current_revision and current_revision is None:
            current_revision = current_git_revision(project_root)
        return inspect_build(
            provider,
            output_root.resolve(),
            max_age_days=max_age_days,
            expected_revision=current_revision,
            require_current_revision=require_current_revision,
            expected_platforms=expected_platforms,
        )
    return inspect_simulator(
        provider,
        output_root.resolve(),
        max_age_days=max_age_days,
        expected_platforms=expected_platforms,
        expected_locales=expected_locales,
        expected_device_families=expected_device_families,
        require_scope_coverage=require_scope_coverage,
    )


def render_summary(results: list[dict[str, object]]) -> str:
    lines = ["Evidence providers: opt-in/read-only"]
    for item in results:
        lines.append(f"- {item['status']}: {item['id']} ({item['kind']}) — {item['details']}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider-file", type=Path, default=DEFAULT_PROVIDER_FILE)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--provider", action="append", required=True)
    parser.add_argument(
        "--max-age-days",
        type=int,
        help="Optionally block build/capture evidence older than this many days.",
    )
    parser.add_argument(
        "--require-current-revision",
        action="store_true",
        help="Require build evidence revision to match the project Git revision.",
    )
    parser.add_argument(
        "--platform",
        action="append",
        default=[],
        help="Optionally require build evidence to match one requested platform.",
    )
    parser.add_argument(
        "--locale",
        action="append",
        default=[],
        help="Optionally require source captures to match one requested locale.",
    )
    parser.add_argument(
        "--device-family",
        action="append",
        default=[],
        help="Optionally require source captures to match one requested device family.",
    )
    parser.add_argument(
        "--require-scope-coverage",
        action="store_true",
        help="Require source captures for every requested platform/locale/device-family combination.",
    )
    parser.add_argument("--format", choices=("summary", "json"), default="summary")
    parser.add_argument("--fail-on-blocked", action="store_true")
    args = parser.parse_args()

    if not args.project_root.is_dir():
        print(f"Project root does not exist: {args.project_root}", file=sys.stderr)
        return 2
    if not args.output_root.is_dir():
        print(f"Output root does not exist: {args.output_root}", file=sys.stderr)
        return 2
    if args.max_age_days is not None and args.max_age_days < 0:
        print("--max-age-days must be zero or greater", file=sys.stderr)
        return 2
    if args.require_scope_coverage and not (args.platform or args.locale or args.device_family):
        print("--require-scope-coverage requires at least one scope flag", file=sys.stderr)
        return 2

    results = [
        inspect_provider(
            provider_id,
            args.project_root,
            args.output_root,
            args.provider_file,
            max_age_days=args.max_age_days,
            require_current_revision=args.require_current_revision,
            expected_platforms=args.platform,
            expected_locales=args.locale,
            expected_device_families=args.device_family,
            require_scope_coverage=args.require_scope_coverage,
        )
        for provider_id in args.provider
    ]
    if args.format == "json":
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print(render_summary(results), end="")
    if args.fail_on_blocked and any(item["status"] == "blocked" for item in results):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
