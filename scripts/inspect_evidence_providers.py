#!/usr/bin/env python3
"""Inspect selected evidence providers without executing project commands."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import re
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


def valid_timestamp(value: str) -> bool:
    try:
        datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


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


def inspect_build(provider: dict[str, str], output_root: Path) -> dict[str, object]:
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
    if errors:
        return result(provider_id, "build", "blocked", "; ".join(errors))
    return result(provider_id, "build", "pass", f"validated {provider['evidence_path']}")


def inspect_simulator(provider: dict[str, str], output_root: Path) -> dict[str, object]:
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
    for index, record in enumerate(records, start=1):
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
        if not valid_timestamp(record["captured_at"]):
            errors.append(f"capture {index} captured_at is not an ISO-8601 timestamp")
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
) -> dict[str, object]:
    del project_root
    provider_file = provider_file.resolve()
    registry_errors = validate_provider_registry(provider_file)
    if registry_errors:
        return result(provider_id, "unknown", "blocked", "invalid provider registry: " + "; ".join(registry_errors))
    text = provider_file.read_text(encoding="utf-8")
    provider = next((item for item in provider_records(text) if item.get("id") == provider_id), None)
    if provider is None:
        return result(provider_id, "unknown", "blocked", "provider is not declared in the registry")
    if provider["kind"] == "build":
        return inspect_build(provider, output_root.resolve())
    return inspect_simulator(provider, output_root.resolve())


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
    parser.add_argument("--format", choices=("summary", "json"), default="summary")
    parser.add_argument("--fail-on-blocked", action="store_true")
    args = parser.parse_args()

    if not args.project_root.is_dir():
        print(f"Project root does not exist: {args.project_root}", file=sys.stderr)
        return 2
    if not args.output_root.is_dir():
        print(f"Output root does not exist: {args.output_root}", file=sys.stderr)
        return 2

    results = [
        inspect_provider(provider_id, args.project_root, args.output_root, args.provider_file)
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
