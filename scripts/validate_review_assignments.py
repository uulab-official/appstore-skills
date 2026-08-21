#!/usr/bin/env python3
"""Validate reviewer assignments and append-only decision history records."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re

from validate_review_adapter_specs import adapter_records, validate as validate_adapter_registry


ALLOWED_ASSIGNMENT_STATUSES = {"pending", "in_review", "approved", "blocked"}
ALLOWED_REVIEWER_STATUSES = {"pending", "in_review", "approved", "blocked", "not_applicable"}
TERMINAL_REVIEWER_STATUSES = {"approved", "blocked", "not_applicable"}
ASSIGNMENT_DIFF_FIELDS = ("role", "required", "scope", "coverage", "status", "assigned_to", "decision", "evidence")
HISTORY_DIFF_FIELDS = ("at", "action", "actor", "reviewer", "note")
TOP_FIELD_LINE = re.compile(r"^\s{2}([a-z][a-z0-9_-]*):\s*(.*?)\s*$")
REVIEWER_LINE = re.compile(r"^\s{4}-\s+id:\s*(.*?)\s*$")
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


def parse_assignment(text: str) -> tuple[dict[str, str], list[dict[str, object]], list[dict[str, str]]]:
    """Parse the intentionally small reviewer assignment YAML contract."""

    fields: dict[str, str] = {}
    reviewers: list[dict[str, object]] = []
    history: list[dict[str, str]] = []
    in_assignment = False
    section = "fields"
    current_reviewer: dict[str, object] | None = None
    current_history: dict[str, str] | None = None
    for line in text.splitlines():
        if line == "review_assignment:":
            in_assignment = True
            section = "fields"
            continue
        if not in_assignment:
            continue
        top_match = TOP_FIELD_LINE.match(line)
        if top_match:
            key, value = top_match.groups()
            if key == "reviewers":
                section = "reviewers"
                continue
            if key == "history":
                section = "history"
                continue
            fields[key] = unquote(value)
            continue
        if section == "reviewers":
            reviewer_match = REVIEWER_LINE.match(line)
            if reviewer_match:
                if current_reviewer is not None:
                    reviewers.append(current_reviewer)
                current_reviewer = {"id": unquote(reviewer_match.group(1))}
                continue
            if current_reviewer is not None:
                item_match = ITEM_FIELD_LINE.match(line)
                if item_match:
                    key, value = item_match.groups()
                    current_reviewer[key] = parse_list(value) if key in {"scope", "coverage", "evidence"} else unquote(value)
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
    if current_reviewer is not None:
        reviewers.append(current_reviewer)
    if current_history is not None:
        history.append(current_history)
    return fields, reviewers, history


def valid_timestamp(value: str) -> bool:
    return timestamp_value(value) is not None


def timestamp_value(value: str) -> datetime | None:
    try:
        timestamp = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return timestamp


def derived_assignment_status(reviewers: list[dict[str, object]]) -> str:
    required_statuses = {
        str(item.get("status", ""))
        for item in reviewers
        if str(item.get("required", "")) == "true"
    }
    if "blocked" in required_statuses:
        return "blocked"
    if required_statuses and required_statuses <= {"approved", "not_applicable"}:
        return "approved"
    if "in_review" in required_statuses:
        return "in_review"
    return "pending"


def validate(
    path: Path,
    adapter_file: Path | None = None,
    selected_adapters: list[str] | None = None,
    max_terminal_decision_age_days: int | None = None,
) -> list[str]:
    if not path.is_file():
        return [f"review assignment file does not exist: {path}"]
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    if max_terminal_decision_age_days is not None and max_terminal_decision_age_days < 0:
        errors.append("max_terminal_decision_age_days must be zero or greater")
    if not re.search(r"^schema_version:\s*1\s*$", text, re.MULTILINE):
        errors.append(f"{path}: must declare schema_version: 1")
    if re.search(r"^\s{2,}(commands?|shell|exec):", text, re.MULTILINE):
        errors.append(f"{path}: command execution fields are not allowed")
    if "review_assignment:" not in text.splitlines():
        errors.append(f"{path}: review_assignment section is required")
        return errors

    fields, reviewers, history = parse_assignment(text)
    for key in ("id", "package", "status", "owner"):
        if key not in fields:
            errors.append(f"{path}: review_assignment.{key} is required")
    if fields.get("status") not in ALLOWED_ASSIGNMENT_STATUSES:
        errors.append(f"{path}: review_assignment.status is unsupported")
    if not reviewers:
        errors.append(f"{path}: review_assignment.reviewers must contain at least one reviewer")
    if not history:
        errors.append(f"{path}: review_assignment.history must contain at least one event")

    seen_ids: set[str] = set()
    for reviewer in reviewers:
        reviewer_id = str(reviewer.get("id", ""))
        prefix = f"{path}: reviewer {reviewer_id or '<unnamed>'}"
        if reviewer_id in seen_ids:
            errors.append(f"{prefix}: duplicate id")
        seen_ids.add(reviewer_id)
        for key in ("role", "required", "status", "scope", "coverage", "assigned_to", "assigned_at", "decision", "decided_at", "evidence", "notes"):
            if key not in reviewer:
                errors.append(f"{prefix}.{key} is required")
        required = str(reviewer.get("required", ""))
        if required not in {"true", "false"}:
            errors.append(f"{prefix}.required must be true or false")
        status = str(reviewer.get("status", ""))
        if status not in ALLOWED_REVIEWER_STATUSES:
            errors.append(f"{prefix}.status is unsupported")
        scope = reviewer.get("scope", [])
        if not isinstance(scope, list) or not scope or any(not str(item).strip() for item in scope):
            errors.append(f"{prefix}.scope must be a non-empty list")
        elif len(set(str(item) for item in scope)) != len(scope):
            errors.append(f"{prefix}.scope must not contain duplicates")
        coverage = reviewer.get("coverage", [])
        if not isinstance(coverage, list) or not coverage or any(not str(item).strip() for item in coverage):
            errors.append(f"{prefix}.coverage must be a non-empty list")
        elif len(set(str(item) for item in coverage)) != len(coverage):
            errors.append(f"{prefix}.coverage must not contain duplicates")
        evidence = reviewer.get("evidence", [])
        if not isinstance(evidence, list):
            errors.append(f"{prefix}.evidence must be a list")
        elif any(not str(item).strip() for item in evidence):
            errors.append(f"{prefix}.evidence must not contain blank references")
        if status in TERMINAL_REVIEWER_STATUSES:
            if not str(reviewer.get("assigned_to", "")).strip():
                errors.append(f"{prefix}: terminal reviewer decision requires assigned_to")
            if not valid_timestamp(str(reviewer.get("assigned_at", ""))):
                errors.append(f"{prefix}: terminal reviewer decision requires ISO-8601 assigned_at")
            if str(reviewer.get("decision", "")) != status:
                errors.append(f"{prefix}: decision must match status ({status})")
            if not valid_timestamp(str(reviewer.get("decided_at", ""))):
                errors.append(f"{prefix}: terminal reviewer decision requires ISO-8601 decided_at")
            if not isinstance(evidence, list) or not evidence:
                errors.append(f"{prefix}: terminal reviewer decision requires evidence")
            if max_terminal_decision_age_days is not None:
                decided_at = timestamp_value(str(reviewer.get("decided_at", "")))
                if decided_at is not None:
                    now = datetime.now(timezone.utc)
                    if decided_at > now:
                        errors.append(
                            f"{prefix}: decided_at cannot be in the future when the terminal decision age gate is enabled"
                        )
                    elif now - decided_at > timedelta(days=max_terminal_decision_age_days):
                        errors.append(
                            f"{prefix}: decided_at is older than max age ({max_terminal_decision_age_days} days)"
                        )
        elif status == "in_review" and not str(reviewer.get("assigned_to", "")).strip():
            errors.append(f"{prefix}: in_review requires assigned_to")

    declared_status = fields.get("status")
    derived_status = derived_assignment_status(reviewers)
    if declared_status in ALLOWED_ASSIGNMENT_STATUSES and declared_status != derived_status:
        errors.append(f"{path}: review_assignment.status {declared_status} does not match reviewer-derived status {derived_status}")
    if declared_status == "approved":
        required_statuses = {
            str(item.get("status", ""))
            for item in reviewers
            if str(item.get("required", "")) == "true"
        }
        if not required_statuses or not required_statuses <= {"approved", "not_applicable"}:
            errors.append(f"{path}: approved assignment requires every required reviewer to be approved or not_applicable")
        if not fields.get("owner", "").strip():
            errors.append(f"{path}: approved assignment requires review_assignment.owner")

    previous_timestamp: datetime | None = None
    for index, event in enumerate(history, start=1):
        for key in ("at", "action", "actor", "note"):
            if not event.get(key):
                errors.append(f"{path}: history event {index}.{key} is required")
        timestamp = str(event.get("at", ""))
        if timestamp and not valid_timestamp(timestamp):
            errors.append(f"{path}: history event {index}.at is not ISO-8601")
        if timestamp and valid_timestamp(timestamp):
            current_timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            if current_timestamp.tzinfo is None:
                current_timestamp = current_timestamp.replace(tzinfo=timezone.utc)
            if previous_timestamp is not None and previous_timestamp.tzinfo is None:
                previous_timestamp = previous_timestamp.replace(tzinfo=timezone.utc)
            if previous_timestamp is not None and current_timestamp < previous_timestamp:
                errors.append(f"{path}: history timestamps must be chronological")
            previous_timestamp = current_timestamp
    if adapter_file is not None:
        registry_errors = validate_adapter_registry(adapter_file)
        errors.extend(registry_errors)
        if not registry_errors:
            records = adapter_records(adapter_file.read_text(encoding="utf-8"))
            known_ids = {str(record.get("id", "")) for record in records}
            coverage_ids = {
                str(item)
                for reviewer in reviewers
                for item in reviewer.get("coverage", [])
                if isinstance(reviewer.get("coverage", []), list)
            }
            for coverage_id in sorted(coverage_ids - known_ids):
                errors.append(f"{path}: coverage references unknown review adapter: {coverage_id}")
            requested = selected_adapters or []
            for adapter_id in requested:
                if adapter_id not in known_ids:
                    errors.append(f"{path}: selected review adapter is not declared in registry: {adapter_id}")
                elif adapter_id not in coverage_ids:
                    errors.append(f"{path}: selected review adapter has no reviewer coverage: {adapter_id}")
    return errors


def summarize(path: Path, max_terminal_decision_age_days: int | None = None) -> dict[str, object]:
    errors = validate(path, max_terminal_decision_age_days=max_terminal_decision_age_days)
    if errors:
        return {"status": "invalid", "details": "; ".join(errors), "reviewers": [], "history_events": 0}
    fields, reviewers, history = parse_assignment(path.read_text(encoding="utf-8"))
    reviewer_rows = [
        {
            "id": str(item.get("id", "")),
            "role": str(item.get("role", "")),
            "required": str(item.get("required", "")),
            "status": str(item.get("status", "")),
            "scope": [str(scope) for scope in item.get("scope", [])] if isinstance(item.get("scope", []), list) else [],
            "coverage": [str(coverage) for coverage in item.get("coverage", [])] if isinstance(item.get("coverage", []), list) else [],
            "assigned_to": str(item.get("assigned_to", "")) or "not assigned",
            "decision": str(item.get("decision", "")),
            "evidence": [str(evidence) for evidence in item.get("evidence", [])] if isinstance(item.get("evidence", []), list) else [],
        }
        for item in reviewers
    ]
    status = derived_assignment_status(reviewers)
    return {
        "status": status,
        "declared_status": fields.get("status", ""),
        "owner": fields.get("owner", "") or "not assigned",
        "reviewers": reviewer_rows,
        "history_events": len(history),
        "details": f"{len(reviewers)} reviewer(s), {len(history)} history event(s)",
    }


def compare_assignments(current_path: Path, previous_path: Path) -> tuple[list[dict[str, str]], list[str]]:
    """Compare stable reviewer fields and append-only history between valid records."""

    errors = [*validate(current_path), *validate(previous_path)]
    if errors:
        return [], errors
    _, current_reviewers, current_history = parse_assignment(current_path.read_text(encoding="utf-8"))
    _, previous_reviewers, previous_history = parse_assignment(previous_path.read_text(encoding="utf-8"))

    def reviewer_map(records: list[dict[str, object]]) -> dict[str, dict[str, str]]:
        result: dict[str, dict[str, str]] = {}
        for record in records:
            reviewer_id = str(record.get("id", ""))
            normalized: dict[str, str] = {}
            for field in ASSIGNMENT_DIFF_FIELDS:
                value = record.get(field, "")
                if isinstance(value, list):
                    normalized[field] = ", ".join(str(item) for item in value)
                else:
                    normalized[field] = str(value)
            result[reviewer_id] = normalized
        return result

    current_map = reviewer_map(current_reviewers)
    previous_map = reviewer_map(previous_reviewers)
    changes: list[dict[str, str]] = []
    for reviewer_id in sorted(set(current_map) | set(previous_map)):
        current = current_map.get(reviewer_id)
        previous = previous_map.get(reviewer_id)
        if previous is None and current is not None:
            changes.append({"change": "added", "reviewer": reviewer_id, "field": "record", "before": "", "after": current.get("status", "")})
            continue
        if current is None and previous is not None:
            changes.append({"change": "removed", "reviewer": reviewer_id, "field": "record", "before": previous.get("status", ""), "after": ""})
            continue
        assert current is not None and previous is not None
        for field in ASSIGNMENT_DIFF_FIELDS:
            if current.get(field, "") != previous.get(field, ""):
                changes.append({
                    "change": "changed",
                    "reviewer": reviewer_id,
                    "field": field,
                    "before": previous.get(field, ""),
                    "after": current.get(field, ""),
                })
    def history_text(event: dict[str, str]) -> str:
        return " | ".join(f"{field}={event.get(field, '')}" for field in HISTORY_DIFF_FIELDS)

    current_history_values = [tuple(event.get(field, "") for field in HISTORY_DIFF_FIELDS) for event in current_history]
    previous_history_values = [tuple(event.get(field, "") for field in HISTORY_DIFF_FIELDS) for event in previous_history]
    append_only = (
        len(current_history_values) >= len(previous_history_values)
        and current_history_values[: len(previous_history_values)] == previous_history_values
    )
    for index in range(max(len(current_history), len(previous_history))):
        current_event = current_history[index] if index < len(current_history) else None
        previous_event = previous_history[index] if index < len(previous_history) else None
        if current_event is not None and previous_event is not None:
            if current_history_values[index] != previous_history_values[index]:
                changes.append({
                    "change": "changed",
                    "reviewer": "<history>",
                    "field": f"event-{index + 1}",
                    "before": history_text(previous_event),
                    "after": history_text(current_event),
                })
        elif current_event is not None:
            changes.append({
                "change": "added",
                "reviewer": "<history>",
                "field": f"event-{index + 1}",
                "before": "",
                "after": history_text(current_event),
            })
        elif previous_event is not None:
            changes.append({
                "change": "removed",
                "reviewer": "<history>",
                "field": f"event-{index + 1}",
                "before": history_text(previous_event),
                "after": "",
            })
    if not append_only:
        changes.append({
            "change": "changed",
            "reviewer": "<history>",
            "field": "append_only",
            "before": "previous history must remain an unchanged prefix",
            "after": "current history rewrites or removes a previous event",
        })
    if len(current_history) != len(previous_history):
        changes.append({
            "change": "changed",
            "reviewer": "<history>",
            "field": "events",
            "before": str(len(previous_history)),
            "after": str(len(current_history)),
        })
    return changes, []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="Reviewer assignment records")
    parser.add_argument("--adapter-file", type=Path, help="Review adapter registry for coverage cross-validation")
    parser.add_argument("--adapter", action="append", default=[], help="Selected adapter ID that must have reviewer coverage")
    parser.add_argument(
        "--max-terminal-decision-age-days",
        type=int,
        help="Optionally reject terminal reviewer decisions older than this many days.",
    )
    args = parser.parse_args()
    errors: list[str] = []
    if args.adapter and args.adapter_file is None:
        errors.append("--adapter-file is required when --adapter is provided")
    if args.max_terminal_decision_age_days is not None and args.max_terminal_decision_age_days < 0:
        errors.append("--max-terminal-decision-age-days must be zero or greater")
    for path in args.paths:
        try:
            errors.extend(
                validate(
                    path,
                    adapter_file=args.adapter_file,
                    selected_adapters=args.adapter,
                    max_terminal_decision_age_days=args.max_terminal_decision_age_days,
                )
            )
        except (OSError, UnicodeDecodeError) as error:
            errors.append(f"{path}: {error}")
    if errors:
        print("Review assignment validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Validated {len(args.paths)} reviewer assignment file(s) successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
