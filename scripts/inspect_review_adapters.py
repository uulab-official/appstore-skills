#!/usr/bin/env python3
"""Inspect selected policy/accessibility review records without side effects."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re
import sys

from validate_review_adapter_specs import adapter_records, validate as validate_registry
from validate_review_assignments import parse_assignment, validate as validate_assignment


DEFAULT_ADAPTER_FILE = Path(__file__).resolve().parents[1] / "skills/release-check/references/review-adapters.yml"
FIELD_LINE = re.compile(r"^\s{2}([a-z][a-z0-9_-]*):\s*(.*?)\s*$")
LIST_ITEM_LINE = re.compile(r"^\s{4}-\s*(.*?)\s*$")


def unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def parse_list(value: str) -> list[str]:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        return [unquote(item.strip()) for item in value[1:-1].split(",") if item.strip()]
    return []


def read_review(path: Path) -> tuple[dict[str, object], list[str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        return {}, [f"cannot read {path}: {error}"]
    errors: list[str] = []
    if not re.search(r"^schema_version:\s*1\s*$", text, re.MULTILINE):
        errors.append("must declare schema_version: 1")
    values: dict[str, object] = {}
    in_review = False
    current_list: str | None = None
    for line in text.splitlines():
        if line == "review:":
            in_review = True
            continue
        if not in_review:
            continue
        match = FIELD_LINE.match(line)
        if match:
            key, value = match.groups()
            if key in {"scope", "evidence"}:
                values[key] = parse_list(value)
                current_list = key
            else:
                values[key] = unquote(value)
                current_list = None
            continue
        list_match = LIST_ITEM_LINE.match(line)
        if list_match and current_list:
            items = values.setdefault(current_list, [])
            if isinstance(items, list):
                items.append(unquote(list_match.group(1)))
    if not in_review:
        errors.append("review section is required")
    return values, errors


def parse_timestamp(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed


def inspect_adapter(
    adapter_id: str,
    output_root: Path,
    adapter_file: Path,
    assignment_file: Path | None = None,
    max_age_days: int | None = None,
) -> dict[str, object]:
    registry_errors = validate_registry(adapter_file)
    if registry_errors:
        return {"id": adapter_id, "status": "blocked", "details": "invalid registry: " + "; ".join(registry_errors)}
    records = adapter_records(adapter_file.read_text(encoding="utf-8"))
    adapter = next((item for item in records if item.get("id") == adapter_id), None)
    if adapter is None:
        return {"id": adapter_id, "status": "blocked", "details": "adapter is not declared in the registry"}
    path = output_root / adapter["evidence_path"]
    if not path.is_file():
        return {"id": adapter_id, "kind": adapter["kind"], "status": "pending", "details": f"missing {adapter['evidence_path']}"}
    values, errors = read_review(path)
    required = parse_list(adapter.get("required_fields", ""))
    for key in required:
        if key not in values or (isinstance(values[key], list) and not values[key]):
            errors.append(f"missing field: {key}")
    allowed = parse_list(adapter.get("allowed_statuses", ""))
    status = str(values.get("status", ""))
    if status not in allowed:
        errors.append(f"status must be one of {allowed}")
    if status in {"pass", "block"}:
        if not str(values.get("reviewer", "")).strip():
            errors.append("terminal review requires reviewer")
        reviewed_at = parse_timestamp(str(values.get("reviewed_at", "")))
        if reviewed_at is None:
            errors.append("terminal review requires ISO-8601 reviewed_at")
        elif max_age_days is not None:
            age = datetime.now(timezone.utc) - reviewed_at
            if age.total_seconds() < 0:
                errors.append("terminal review reviewed_at cannot be in the future")
            elif age > timedelta(days=max_age_days):
                errors.append(f"terminal review is older than max age ({max_age_days} days)")
        if not isinstance(values.get("evidence"), list) or not values["evidence"]:
            errors.append("terminal review requires evidence")
        if assignment_file is not None and not errors:
            assignment_errors = validate_assignment(assignment_file)
            if assignment_errors:
                errors.append("review assignment is invalid: " + "; ".join(assignment_errors))
            else:
                _, reviewers, _ = parse_assignment(assignment_file.read_text(encoding="utf-8"))
                reviewer_name = str(values.get("reviewer", "")).strip()
                matched = any(
                    str(reviewer.get("assigned_to", "")).strip() == reviewer_name
                    and adapter_id in reviewer.get("coverage", [])
                    for reviewer in reviewers
                    if isinstance(reviewer.get("coverage", []), list)
                )
                if not matched:
                    errors.append(
                        "terminal review reviewer is not assigned and covered for this adapter"
                    )
    if errors:
        return {"id": adapter_id, "kind": adapter["kind"], "status": "blocked", "details": "; ".join(errors)}
    result_status = "pass" if status in {"pass", "not_applicable"} else "pending"
    return {"id": adapter_id, "kind": adapter["kind"], "status": result_status, "details": f"recorded status: {status}"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter-file", type=Path, default=DEFAULT_ADAPTER_FILE)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--assignment-file", type=Path)
    parser.add_argument(
        "--max-age-days",
        type=int,
        help="Optionally block terminal evidence older than this many days.",
    )
    parser.add_argument("--adapter", action="append", required=True)
    parser.add_argument("--format", choices=("summary", "json"), default="summary")
    parser.add_argument("--fail-on-blocked", action="store_true")
    parser.add_argument("--fail-on-pending", action="store_true")
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
    if args.assignment_file and not args.assignment_file.is_file():
        print(f"Assignment file does not exist: {args.assignment_file}", file=sys.stderr)
        return 2
    adapter_file = args.adapter_file.resolve()
    assignment_file = args.assignment_file.resolve() if args.assignment_file else None
    results = [
        inspect_adapter(
            adapter_id,
            args.output_root.resolve(),
            adapter_file,
            assignment_file=assignment_file,
            max_age_days=args.max_age_days,
        )
        for adapter_id in args.adapter
    ]
    if args.format == "json":
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print("Review adapters: opt-in/read-only")
        for item in results:
            print(f"- {item['status']}: {item['id']} ({item.get('kind', 'unknown')}) — {item['details']}")
    if args.fail_on_blocked and any(item["status"] == "blocked" for item in results):
        return 1
    if args.fail_on_pending and any(item["status"] == "pending" for item in results):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
