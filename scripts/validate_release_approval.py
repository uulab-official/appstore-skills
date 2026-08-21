#!/usr/bin/env python3
"""Validate the explicit human approval record used by release handoff."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import re


ALLOWED_STATUSES = {"pending", "approved", "rejected", "expired"}
TERMINAL_STATUSES = {"approved", "rejected", "expired"}
SECTION_FIELD_LINE = re.compile(r"^\s{2}([a-z][a-z0-9_-]*):\s*(.*?)\s*$")
LIST_ITEM_LINE = re.compile(r"^\s{4}-\s*(.*?)\s*$")


def unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def parse_list(value: str) -> list[str] | None:
    value = value.strip()
    if not (value.startswith("[") and value.endswith("]")):
        return None
    contents = value[1:-1].strip()
    if not contents:
        return []
    return [unquote(item.strip()) for item in contents.split(",") if item.strip()]


def parse_text(text: str) -> dict[str, object]:
    """Parse the intentionally small approval YAML contract without PyYAML."""

    approval: dict[str, object] = {}
    in_approval = False
    current_list: str | None = None
    for line in text.splitlines():
        if line.strip().startswith("#") or not line.strip():
            continue
        if line == "approval:":
            in_approval = True
            current_list = None
            continue
        if not in_approval:
            continue
        if line and not line.startswith(" "):
            break
        field_match = SECTION_FIELD_LINE.match(line)
        if field_match:
            key, value = field_match.groups()
            inline_list = parse_list(value) if key in {"scope", "evidence"} else None
            if inline_list is not None:
                approval[key] = inline_list
                current_list = key
            elif value == "":
                approval[key] = [] if key in {"scope", "evidence"} else ""
                current_list = key if key in {"scope", "evidence"} else None
            else:
                approval[key] = unquote(value)
                current_list = None
            continue
        list_match = LIST_ITEM_LINE.match(line)
        if list_match and current_list:
            values = approval.setdefault(current_list, [])
            if isinstance(values, list):
                values.append(unquote(list_match.group(1)))
    return approval


def parse_approval(path: Path) -> dict[str, object]:
    return parse_text(path.read_text(encoding="utf-8"))


def approval_errors(approval: dict[str, object], path: Path) -> list[str]:
    errors: list[str] = []
    status = approval.get("status")
    if status not in ALLOWED_STATUSES:
        errors.append(f"{path}: approval.status must be one of {sorted(ALLOWED_STATUSES)}")
        return errors

    for key in ("owner", "scope", "decision", "decided_at", "evidence"):
        if key not in approval:
            errors.append(f"{path}: approval.{key} is required")

    scope = approval.get("scope")
    evidence = approval.get("evidence")
    if scope is not None and not isinstance(scope, list):
        errors.append(f"{path}: approval.scope must be a list")
    if evidence is not None and not isinstance(evidence, list):
        errors.append(f"{path}: approval.evidence must be a list")

    if status in TERMINAL_STATUSES:
        owner = str(approval.get("owner", "")).strip()
        decision = str(approval.get("decision", "")).strip()
        decided_at = str(approval.get("decided_at", "")).strip()
        if not owner:
            errors.append(f"{path}: terminal approval requires approval.owner")
        if not isinstance(scope, list) or not scope:
            errors.append(f"{path}: terminal approval requires a non-empty approval.scope")
        if decision != status:
            errors.append(f"{path}: approval.decision must match approval.status ({status})")
        if not decided_at:
            errors.append(f"{path}: terminal approval requires approval.decided_at")
        else:
            try:
                datetime.fromisoformat(decided_at.replace("Z", "+00:00"))
            except ValueError:
                errors.append(f"{path}: approval.decided_at must be an ISO-8601 timestamp")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"{path}: terminal approval requires non-empty approval.evidence")
    return errors


def validate(path: Path) -> list[str]:
    if not path.is_file():
        return [f"release approval file does not exist: {path}"]

    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    if not re.search(r"^schema_version:\s*1\s*$", text, re.MULTILINE):
        errors.append(f"{path}: must declare schema_version: 1")
    if "approval:" not in text.splitlines():
        errors.append(f"{path}: approval section is required")
        return errors
    errors.extend(approval_errors(parse_text(text), path))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="Release approval files")
    args = parser.parse_args()

    errors: list[str] = []
    for path in args.paths:
        try:
            errors.extend(validate(path))
        except (OSError, UnicodeDecodeError) as error:
            errors.append(f"{path}: {error}")
    if errors:
        print("Release approval validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Validated {len(args.paths)} release approval file(s) successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
