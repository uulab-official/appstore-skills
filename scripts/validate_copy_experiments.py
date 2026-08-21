#!/usr/bin/env python3
"""Validate reversible store-copy experiment records and approval history."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import re


ALLOWED_STATUSES = {"draft", "review", "verified", "blocked"}
ALLOWED_APPROVALS = {"pending", "approved", "rejected", "expired"}
TOP_FIELD_LINE = re.compile(r"^\s{2}([a-z][a-z0-9_-]*):\s*(.*?)\s*$")
VARIANT_LINE = re.compile(r"^\s{4}-\s+id:\s*(.*?)\s*$")
HISTORY_LINE = re.compile(r"^\s{4}-\s+at:\s*(.*?)\s*$")
ITEM_FIELD_LINE = re.compile(r"^\s{6}([a-z][a-z0-9_-]*):\s*(.*?)\s*$")


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


def parse_experiment(text: str) -> tuple[dict[str, str], list[dict[str, object]], list[dict[str, str]]]:
    fields: dict[str, str] = {}
    variants: list[dict[str, object]] = []
    history: list[dict[str, str]] = []
    in_experiment = False
    section = "fields"
    current_variant: dict[str, object] | None = None
    current_history: dict[str, str] | None = None
    for line in text.splitlines():
        if line == "experiment:":
            in_experiment = True
            continue
        if not in_experiment:
            continue
        top_match = TOP_FIELD_LINE.match(line)
        if top_match:
            key, value = top_match.groups()
            if key == "variants":
                section = "variants"
                continue
            if key == "history":
                section = "history"
                continue
            fields[key] = unquote(value)
            continue
        if section == "variants":
            variant_match = VARIANT_LINE.match(line)
            if variant_match:
                if current_variant is not None:
                    variants.append(current_variant)
                current_variant = {"id": unquote(variant_match.group(1))}
                continue
            if current_variant is not None:
                item_match = ITEM_FIELD_LINE.match(line)
                if item_match:
                    key, value = item_match.groups()
                    current_variant[key] = parse_list(value) if key == "evidence" else unquote(value)
        elif section == "history":
            history_match = HISTORY_LINE.match(line)
            if history_match:
                if current_history is not None:
                    history.append(current_history)
                current_history = {"at": unquote(history_match.group(1))}
                continue
            if current_history is not None:
                item_match = ITEM_FIELD_LINE.match(line)
                if item_match:
                    key, value = item_match.groups()
                    current_history[key] = unquote(value)
    if current_variant is not None:
        variants.append(current_variant)
    if current_history is not None:
        history.append(current_history)
    return fields, variants, history


def valid_timestamp(value: str) -> bool:
    try:
        datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def validate(path: Path, package_root: Path) -> list[str]:
    if not path.is_file():
        return [f"copy experiment file does not exist: {path}"]
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    if not re.search(r"^schema_version:\s*1\s*$", text, re.MULTILINE):
        errors.append(f"{path}: must declare schema_version: 1")
    if re.search(r"^\s{2,}(commands?|shell|exec):", text, re.MULTILINE):
        errors.append(f"{path}: command execution fields are not allowed")
    fields, variants, history = parse_experiment(text)
    for key in ("id", "status", "source_locale", "objective", "measurement"):
        if not fields.get(key):
            errors.append(f"{path}: experiment.{key} is required")
    if fields.get("status") not in ALLOWED_STATUSES:
        errors.append(f"{path}: experiment.status is unsupported")
    if fields.get("measurement") != "manual-review":
        errors.append(f"{path}: experiment.measurement must be manual-review")
    if len(variants) < 2:
        errors.append(f"{path}: experiment.variants must contain at least two variants")
    if not history:
        errors.append(f"{path}: experiment.history must contain at least one event")

    seen_ids: set[str] = set()
    seen_files: set[str] = set()
    for variant in variants:
        variant_id = str(variant.get("id", ""))
        prefix = f"{path}: variant {variant_id or '<unnamed>'}"
        if variant_id in seen_ids:
            errors.append(f"{prefix}: duplicate id")
        seen_ids.add(variant_id)
        for key in ("status", "label", "copy_file", "hypothesis", "approval_status"):
            if not variant.get(key):
                errors.append(f"{prefix}.{key} is required")
        if variant.get("status") not in ALLOWED_STATUSES:
            errors.append(f"{prefix}.status is unsupported")
        approval = str(variant.get("approval_status", ""))
        if approval not in ALLOWED_APPROVALS:
            errors.append(f"{prefix}.approval_status is unsupported")
        relative = Path(str(variant.get("copy_file", "")))
        if relative.is_absolute() or ".." in relative.parts or not str(relative):
            errors.append(f"{prefix}.copy_file must be a safe relative path")
        else:
            relative_text = relative.as_posix()
            if relative_text in seen_files:
                errors.append(f"{prefix}.copy_file is reused by another variant")
            seen_files.add(relative_text)
            copy_path = package_root / relative
            if not copy_path.is_file():
                errors.append(f"{prefix}.copy_file does not exist: {relative_text}")
            else:
                copy_text = copy_path.read_text(encoding="utf-8")
                locale_match = re.search(r"^locale:\s*(.*?)\s*$", copy_text, re.MULTILINE)
                if not locale_match or unquote(locale_match.group(1)) != fields.get("source_locale"):
                    errors.append(f"{prefix}.copy_file must use source locale {fields.get('source_locale')}")
        if approval == "approved":
            if not variant.get("approval_owner"):
                errors.append(f"{prefix}: approved variant requires approval_owner")
            decided_at = str(variant.get("decided_at", ""))
            if not valid_timestamp(decided_at):
                errors.append(f"{prefix}: approved variant requires ISO-8601 decided_at")
            evidence = variant.get("evidence", [])
            if not isinstance(evidence, list) or not evidence:
                errors.append(f"{prefix}: approved variant requires evidence")
        if variant.get("status") == "verified" and approval != "approved":
            errors.append(f"{prefix}: verified variant requires approved approval_status")

    for index, event in enumerate(history, start=1):
        for key in ("at", "action", "actor", "note"):
            if not event.get(key):
                errors.append(f"{path}: history event {index}.{key} is required")
        if event.get("at") and not valid_timestamp(str(event["at"])):
            errors.append(f"{path}: history event {index}.at is not ISO-8601")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="Copy experiment record")
    parser.add_argument("--package-root", type=Path, required=True)
    args = parser.parse_args()

    try:
        errors = validate(args.path, args.package_root.resolve())
    except (OSError, UnicodeDecodeError) as error:
        errors = [str(error)]
    if errors:
        print("Copy experiment validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Validated copy experiment: {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
