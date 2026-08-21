#!/usr/bin/env python3
"""Generate a deterministic, diff-friendly reviewer handoff summary."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys

from annotate_release_report import parse_report
from inspect_review_adapters import inspect_adapter
from validate_release_approval import parse_approval, validate as validate_approval


ASSET_PATH_LINE = re.compile(r"^\s+-\s+path:\s*(.*?)\s*$")
ASSET_FIELD_LINE = re.compile(r"^\s{4}([a-z][a-z0-9_-]*):\s*(.*?)\s*$")
ALLOWED_REVIEW_STATUSES = {"blocked", "pending_approval", "review", "ready_for_handoff"}
DIFF_FIELDS = ("kind", "platform", "locale", "status", "format", "dimensions", "source")
DEFAULT_ADAPTER_FILE = Path(__file__).resolve().parents[1] / "skills/release-check/references/review-adapters.yml"


def unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def parse_manifest(path: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8")
    records: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for line in text.splitlines():
        path_match = ASSET_PATH_LINE.match(line)
        if path_match:
            if current is not None:
                records.append(current)
            current = {"path": unquote(path_match.group(1))}
            continue
        if current is None:
            continue
        field_match = ASSET_FIELD_LINE.match(line)
        if field_match:
            key, value = field_match.groups()
            current[key] = unquote(value)
    if current is not None:
        records.append(current)
    return sorted(records, key=lambda item: item["path"])


def asset_map(records: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {record["path"]: record for record in records}


def compare_manifests(
    current: list[dict[str, str]],
    previous: list[dict[str, str]] | None,
) -> list[dict[str, str]]:
    current_map = asset_map(current)
    if previous is None:
        return [
            {"change": "baseline", "path": path, **{key: record.get(key, "") for key in DIFF_FIELDS}}
            for path, record in current_map.items()
        ]

    previous_map = asset_map(previous)
    changes: list[dict[str, str]] = []
    for path in sorted(set(current_map) | set(previous_map)):
        current_record = current_map.get(path)
        previous_record = previous_map.get(path)
        if previous_record is None and current_record is not None:
            changes.append({"change": "added", "path": path, **{key: current_record.get(key, "") for key in DIFF_FIELDS}})
        elif current_record is None and previous_record is not None:
            changes.append({"change": "removed", "path": path, **{key: previous_record.get(key, "") for key in DIFF_FIELDS}})
        elif current_record is not None and previous_record is not None:
            if any(current_record.get(key, "") != previous_record.get(key, "") for key in DIFF_FIELDS):
                changes.append({"change": "changed", "path": path, **{key: current_record.get(key, "") for key in DIFF_FIELDS}})
    return changes


def approval_status(package_root: Path) -> tuple[str, str]:
    path = package_root / "release-approval.yml"
    if not path.is_file():
        return "not-supplied", "no release-approval.yml supplied"
    errors = validate_approval(path)
    if errors:
        return "invalid", "; ".join(errors)
    approval = parse_approval(path)
    status = str(approval.get("status", "pending"))
    owner = str(approval.get("owner", "")).strip()
    return status, f"owner: {owner or 'not assigned'}"


def release_report_data(package_root: Path) -> tuple[str, list[str], list[str]]:
    path = package_root / "release-report.md"
    if not path.is_file():
        return "not-available", [], ["release-report.md is missing"]
    try:
        status, lists, _ = parse_report(path)
    except (OSError, UnicodeDecodeError, ValueError) as error:
        return "invalid", [], [f"release report could not be parsed: {error}"]
    return status, [message for _, message in lists["blockers"]], [message for _, message in lists["warnings"]]


def build_summary(
    package_root: Path,
    previous_package_root: Path | None,
    adapter_file: Path | None = None,
    adapters: list[str] | None = None,
) -> dict[str, object]:
    manifest_path = package_root / "manifest.yml"
    blockers: list[str] = []
    warnings: list[str] = []
    if not manifest_path.is_file():
        blockers.append("manifest.yml is missing")
        current_records: list[dict[str, str]] = []
    else:
        current_records = parse_manifest(manifest_path)
    if not current_records:
        blockers.append("manifest.yml contains no asset records")

    previous_records: list[dict[str, str]] | None = None
    if previous_package_root is not None:
        previous_manifest = previous_package_root / "manifest.yml"
        if previous_manifest.is_file():
            previous_records = parse_manifest(previous_manifest)
        else:
            warnings.append("previous package has no manifest.yml; baseline diff is unavailable")

    release_status, report_blockers, report_warnings = release_report_data(package_root)
    blockers.extend(report_blockers)
    warnings.extend(report_warnings)
    approval, approval_detail = approval_status(package_root)
    if approval == "invalid":
        blockers.append(f"release approval is invalid: {approval_detail}")

    selected_adapters = adapters or []
    review_adapters: list[dict[str, object]] = []
    if selected_adapters:
        selected_adapter_file = adapter_file or DEFAULT_ADAPTER_FILE
        review_adapters = [
            inspect_adapter(adapter_id, package_root, selected_adapter_file)
            for adapter_id in selected_adapters
        ]
        for adapter in review_adapters:
            if adapter["status"] == "blocked":
                blockers.append(f"{adapter['id']} review adapter is blocked: {adapter['details']}")
            elif adapter["status"] == "pending":
                warnings.append(f"{adapter['id']} review adapter is pending: {adapter['details']}")

    status_counts = Counter(record.get("status", "unknown") for record in current_records)
    review_statuses = sum(status_counts.get(status, 0) for status in ("review", "draft"))
    if status_counts.get("blocked", 0):
        blockers.append(f"{status_counts['blocked']} manifest asset(s) are blocked")
    if blockers:
        review_status = "blocked"
    elif approval in {"pending", "not-supplied"}:
        review_status = "pending_approval"
    elif any(item["status"] == "pending" for item in review_adapters):
        review_status = "review"
    elif review_statuses:
        review_status = "review"
    else:
        review_status = "ready_for_handoff"

    changes = compare_manifests(current_records, previous_records)
    next_actions: list[str] = []
    if blockers:
        next_actions.append("Resolve the listed blockers and regenerate the review handoff.")
    if approval in {"pending", "not-supplied"}:
        next_actions.append("Record explicit human approval before treating the package as ready.")
    if review_statuses:
        next_actions.append(f"Review {review_statuses} draft/review asset(s) with the product owner.")
    if any(item["status"] == "pending" for item in review_adapters):
        next_actions.append("Complete the selected policy/accessibility adapter reviews.")
    if not next_actions:
        next_actions.append("Complete final human review; publish_status remains not-run.")

    return {
        "schema_version": 1,
        "package": package_root.name,
        "review_status": review_status,
        "release_report_status": release_status,
        "approval_status": approval,
        "approval_detail": approval_detail,
        "publish_status": "not-run",
        "asset_counts": dict(sorted(status_counts.items())),
        "assets_total": len(current_records),
        "changes": changes,
        "blockers": sorted(dict.fromkeys(blockers)),
        "warnings": sorted(dict.fromkeys(warnings)),
        "review_adapters": review_adapters,
        "next_actions": next_actions,
        "baseline": previous_package_root.name if previous_package_root is not None else "not-supplied",
    }


def markdown_table(rows: list[dict[str, str]], columns: tuple[str, ...]) -> list[str]:
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(row.get(column, "").replace("|", "\\|") for column in columns) + " |")
    return lines


def render_markdown(summary: dict[str, object]) -> str:
    counts = summary["asset_counts"]
    assert isinstance(counts, dict)
    changes = summary["changes"]
    assert isinstance(changes, list)
    lines = [
        "# Review handoff",
        "",
        "```yaml",
        f"schema_version: {summary['schema_version']}",
        f"package: {summary['package']}",
        f"review_status: {summary['review_status']}",
        f"release_report_status: {summary['release_report_status']}",
        f"approval_status: {summary['approval_status']}",
        f"publish_status: {summary['publish_status']}",
        "```",
        "",
        "This is a read-only reviewer aid. It does not approve, submit, upload, publish, or allocate experiment traffic.",
        "",
        "## Review snapshot",
        "",
        f"- Package: `{summary['package']}`",
        f"- Release report: `{summary['release_report_status']}`",
        f"- Approval: `{summary['approval_status']}` ({summary['approval_detail']})",
        f"- Baseline: `{summary['baseline']}`",
        f"- Assets: `{summary['assets_total']}`",
        "",
        "| Asset status | Count |",
        "| --- | ---: |",
    ]
    for status, count in counts.items():
        lines.append(f"| {status} | {count} |")
    lines.extend(["", "## Manifest diff", ""])
    if changes:
        lines.extend(markdown_table(changes, ("change", "path", "kind", "platform", "locale", "status")))
    else:
        lines.append("No manifest changes detected against the supplied baseline.")
    lines.extend(["", "## Optional review adapters", ""])
    adapters = summary["review_adapters"]
    assert isinstance(adapters, list)
    if adapters:
        lines.extend(
            markdown_table(
                [
                    {"id": str(item["id"]), "kind": str(item.get("kind", "")), "status": str(item["status"]), "details": str(item["details"])}
                    for item in adapters
                ],
                ("id", "kind", "status", "details"),
            )
        )
    else:
        lines.append("No optional policy/accessibility adapters selected.")
    for heading, key in (("Blockers", "blockers"), ("Warnings", "warnings")):
        lines.extend(["", f"## {heading}", ""])
        values = summary[key]
        assert isinstance(values, list)
        lines.extend(f"- {value}" for value in values) if values else lines.append("- None")
    lines.extend(["", "## Next actions", ""])
    lines.extend(
        f"{index}. {action}"
        for index, action in enumerate(summary["next_actions"], start=1)
    )
    lines.extend(["", "## Safety", "", "`publish_status` is permanently `not-run`; this summary must not be used as a store submission record.", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--previous-package-root", type=Path)
    parser.add_argument("--adapter-file", type=Path)
    parser.add_argument("--adapter", action="append", default=[])
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    if not args.package_root.is_dir():
        print(f"Package root does not exist: {args.package_root}", file=sys.stderr)
        return 2
    if args.previous_package_root and not args.previous_package_root.is_dir():
        print(f"Previous package root does not exist: {args.previous_package_root}", file=sys.stderr)
        return 2
    summary = build_summary(
        args.package_root.resolve(),
        args.previous_package_root.resolve() if args.previous_package_root else None,
        adapter_file=args.adapter_file.resolve() if args.adapter_file else None,
        adapters=args.adapter,
    )
    rendered = render_markdown(summary) if args.format == "markdown" else json.dumps(summary, indent=2, ensure_ascii=False)
    rendered += "\n" if not rendered.endswith("\n") else ""
    if args.output:
        if args.output.exists() and not args.overwrite:
            print(f"Refusing to overwrite existing review handoff: {args.output}", file=sys.stderr)
            return 2
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(f"Wrote review handoff: {args.output}")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
