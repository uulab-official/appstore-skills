#!/usr/bin/env python3
"""Validate the opt-in, read-only evidence provider registry."""

from __future__ import annotations

import argparse
from pathlib import Path
import re


ALLOWED_KINDS = {"build", "simulator"}
ALLOWED_STATUSES = {"draft", "review", "verified", "blocked"}
FIELD_LINE = re.compile(r"^\s{4}([a-z][a-z0-9_-]*):\s*(.*?)\s*$")
SECTION_FIELD_LINE = re.compile(r"^\s{2}([a-z][a-z0-9_-]*):\s*(.*?)\s*$")
PROVIDER_LINE = re.compile(r"^\s{2}-\s+id:\s*(\S+)\s*$")


def unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def provider_records(text: str) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for line in text.splitlines():
        provider_match = PROVIDER_LINE.match(line)
        if provider_match:
            if current is not None:
                records.append(current)
            current = {"id": unquote(provider_match.group(1))}
            continue
        if current is None:
            continue
        field_match = FIELD_LINE.match(line)
        if field_match:
            key, value = field_match.groups()
            current[key] = unquote(value)
    if current is not None:
        records.append(current)
    return records


def section_values(text: str, name: str) -> dict[str, str]:
    values: dict[str, str] = {}
    lines = text.splitlines()
    start = next((index for index, line in enumerate(lines) if line == f"{name}:"), None)
    if start is None:
        return values
    for line in lines[start + 1 :]:
        if line and not line.startswith(" "):
            break
        match = SECTION_FIELD_LINE.match(line)
        if match:
            key, value = match.groups()
            values[key] = unquote(value)
    return values


def validate(path: Path) -> list[str]:
    if not path.is_file():
        return [f"evidence provider registry does not exist: {path}"]

    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    if not re.search(r"^schema_version:\s*1\s*$", text, re.MULTILINE):
        errors.append(f"{path}: must declare schema_version: 1")

    provider_set = section_values(text, "provider_set")
    for key in ("id", "status", "mode", "execution", "source_of_truth"):
        if not provider_set.get(key):
            errors.append(f"{path}: provider_set.{key} is required")
    if provider_set.get("status") not in ALLOWED_STATUSES:
        errors.append(f"{path}: provider_set.status is unsupported")
    if provider_set.get("mode") != "read-only":
        errors.append(f"{path}: provider_set.mode must be read-only")
    if provider_set.get("execution") != "opt-in":
        errors.append(f"{path}: provider_set.execution must be opt-in")

    records = provider_records(text)
    if not records:
        errors.append(f"{path}: providers must contain at least one record")
        return errors

    seen_ids: set[str] = set()
    seen_kinds: set[str] = set()
    required = (
        "kind",
        "status",
        "enabled_by_default",
        "evidence_path",
        "required_fields",
        "proves",
        "side_effects",
        "required_checks",
    )
    for record in records:
        provider_id = record.get("id", "")
        prefix = f"{path}: provider {provider_id or '<unnamed>'}"
        if provider_id in seen_ids:
            errors.append(f"{prefix}: duplicate id")
        seen_ids.add(provider_id)
        for key in required:
            if not record.get(key):
                errors.append(f"{prefix}.{key} is required")
        kind = record.get("kind", "")
        if kind not in ALLOWED_KINDS:
            errors.append(f"{prefix}.kind must be one of {sorted(ALLOWED_KINDS)}")
        if kind in seen_kinds:
            errors.append(f"{prefix}: duplicate kind")
        seen_kinds.add(kind)
        if record.get("status") not in ALLOWED_STATUSES:
            errors.append(f"{prefix}.status is unsupported")
        if record.get("enabled_by_default") != "false":
            errors.append(f"{prefix}.enabled_by_default must be false")
        if record.get("side_effects") != "none":
            errors.append(f"{prefix}.side_effects must be none")
        if "command" in record or "commands" in record:
            errors.append(f"{prefix}: command fields are not allowed")
        if kind == "simulator" and not record.get("capture_root"):
            errors.append(f"{prefix}.capture_root is required for simulator providers")

    missing_kinds = ALLOWED_KINDS - seen_kinds
    if missing_kinds:
        errors.append(f"{path}: missing provider kinds {sorted(missing_kinds)}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="Evidence provider registries")
    args = parser.parse_args()

    errors: list[str] = []
    for path in args.paths:
        try:
            errors.extend(validate(path))
        except (OSError, UnicodeDecodeError) as error:
            errors.append(f"{path}: {error}")
    if errors:
        print("Evidence provider validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Validated {len(args.paths)} evidence provider registry(ies) successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
