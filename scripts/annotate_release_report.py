#!/usr/bin/env python3
"""Surface release-report blockers and warnings in GitHub Actions."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import sys
from urllib.parse import quote


SUMMARY_STATUS_RE = re.compile(r"^summary_status:\s*(\S+)\s*$")
LIST_HEADER_RE = re.compile(r"^(blockers|warnings):\s*(.*)\s*$")
LIST_ITEM_RE = re.compile(r"^\s+-\s+(.+?)\s*$")
SCALAR_RE = re.compile(r"^(human_review_required|platform_docs_checked):\s*(.*?)\s*$")


def unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def parse_report(path: Path) -> tuple[str, dict[str, list[tuple[int, str]]], dict[str, str]]:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"```yaml\s*\n(.*?)\n```", text, re.DOTALL)
    if not match:
        raise ValueError("release report must contain a fenced YAML summary")

    summary = match.group(1)
    summary_start = text[: match.start(1)].count("\n") + 1
    status = ""
    lists: dict[str, list[tuple[int, str]]] = {"blockers": [], "warnings": []}
    scalars: dict[str, str] = {}
    active_list: str | None = None
    for offset, line in enumerate(summary.splitlines()):
        line_number = summary_start + offset
        status_match = SUMMARY_STATUS_RE.match(line)
        if status_match:
            status = unquote(status_match.group(1))
            active_list = None
            continue

        list_match = LIST_HEADER_RE.match(line)
        if list_match:
            key, value = list_match.groups()
            active_list = key if value.strip() == "[]" else key
            if value.strip() not in {"", "[]"}:
                lists[key].append((line_number, unquote(value)))
            continue

        item_match = LIST_ITEM_RE.match(line)
        if item_match and active_list in lists:
            lists[active_list].append((line_number, unquote(item_match.group(1))))
            continue

        scalar_match = SCALAR_RE.match(line)
        if scalar_match:
            key, value = scalar_match.groups()
            scalars[key] = unquote(value)
            active_list = None
            continue

        if line and not line.startswith(" "):
            active_list = None

    if not status:
        raise ValueError("release report summary_status is required")
    return status, lists, scalars


def annotation(level: str, report_path: Path, line: int, title: str, message: str) -> str:
    safe_message = quote(message, safe=" .,:;!?/'-()")
    safe_title = quote(title, safe=" .,:;!?/'-()")
    return f"::{level} file={report_path.as_posix()},line={line},title={safe_title}::{safe_message}"


def write_step_summary(
    report_path: Path,
    status: str,
    lists: dict[str, list[tuple[int, str]]],
    scalars: dict[str, str],
) -> None:
    summary_path_value = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path_value:
        return

    lines = [f"## Release report: `{report_path}`", "", f"**Summary status:** `{status}`", ""]
    for key, label in (("blockers", "Blockers"), ("warnings", "Warnings")):
        lines.append(f"### {label}")
        if lists[key]:
            lines.extend(f"- {message}" for _, message in lists[key])
        else:
            lines.append("- None")
        lines.append("")
    if scalars.get("human_review_required"):
        lines.append(f"**Human review required:** `{scalars['human_review_required']}`")
    with Path(summary_path_value).open("a", encoding="utf-8") as summary_file:
        summary_file.write("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("release_report", type=Path)
    parser.add_argument(
        "--github-actions",
        action="store_true",
        help="Emit ::error/::warning annotations for GitHub Actions",
    )
    parser.add_argument(
        "--fail-on-blockers",
        action="store_true",
        help="Return non-zero when the report contains blockers",
    )
    args = parser.parse_args()
    report_path = args.release_report

    if not report_path.is_file():
        print(f"Release report does not exist: {report_path}", file=sys.stderr)
        return 2

    try:
        status, lists, scalars = parse_report(report_path)
    except (OSError, UnicodeDecodeError, ValueError) as error:
        print(f"Release report annotation failed: {error}", file=sys.stderr)
        return 2

    print(f"Release report status: {status}")
    for key, level, title in (
        ("blockers", "error", "Release blocker"),
        ("warnings", "warning", "Release warning"),
    ):
        for line, message in lists[key]:
            if args.github_actions:
                print(annotation(level, report_path, line, title, message))
            else:
                print(f"{title}: {message}")

    write_step_summary(report_path, status, lists, scalars)
    if args.fail_on_blockers and lists["blockers"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
