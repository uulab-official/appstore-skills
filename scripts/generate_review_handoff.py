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
from validate_review_assignments import compare_assignments, summarize as summarize_assignment


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


def review_assignment_data(
    package_root: Path,
    assignment_file: Path | None = None,
    max_terminal_decision_age_days: int | None = None,
) -> dict[str, object]:
    path = assignment_file or package_root / "review-assignment.yml"
    if not path.is_file():
        return {
            "status": "not-supplied",
            "details": "no review-assignment.yml supplied",
            "owner": "not assigned",
            "reviewers": [],
            "history_events": 0,
        }
    result = summarize_assignment(path, max_terminal_decision_age_days=max_terminal_decision_age_days)
    result["path"] = str(path)
    return result


def review_assignment_diff_data(
    package_root: Path,
    previous_package_root: Path | None,
    assignment_file: Path | None = None,
    previous_assignment_file: Path | None = None,
) -> dict[str, object]:
    current_path = assignment_file or package_root / "review-assignment.yml"
    previous_path = previous_assignment_file
    if previous_path is None and previous_package_root is not None:
        previous_path = previous_package_root / "review-assignment.yml"
    if previous_path is None:
        return {"status": "not-supplied", "baseline": "not-supplied", "changes": [], "details": "no previous reviewer assignment supplied"}
    if not current_path.is_file():
        return {"status": "not-supplied", "baseline": previous_path.parent.name, "changes": [], "details": "current review-assignment.yml is missing"}
    if not previous_path.is_file():
        return {"status": "unavailable", "baseline": previous_path.parent.name, "changes": [], "details": f"missing {previous_path.name}"}
    changes, errors = compare_assignments(current_path, previous_path)
    if errors:
        return {"status": "invalid", "baseline": previous_path.parent.name, "changes": [], "details": "; ".join(errors)}
    return {
        "status": "compared",
        "baseline": previous_path.parent.name,
        "changes": changes,
        "details": f"{len(changes)} reviewer assignment change(s)",
    }


def review_assignment_coverage_data(
    review_assignment: dict[str, object],
    selected_adapters: list[str],
) -> dict[str, object]:
    if not selected_adapters:
        return {"status": "not-checked", "rows": [], "details": "no review adapters selected"}
    if review_assignment.get("status") in {"not-supplied", "invalid"}:
        return {
            "status": "unavailable",
            "rows": [],
            "details": "review assignment is not available for adapter coverage",
        }
    reviewers = review_assignment.get("reviewers", [])
    if not isinstance(reviewers, list):
        return {"status": "unavailable", "rows": [], "details": "reviewer rows are not available"}
    rows: list[dict[str, object]] = []
    for adapter_id in selected_adapters:
        matches = [
            {
                "id": str(reviewer.get("id", "")),
                "status": str(reviewer.get("status", "")),
            }
            for reviewer in reviewers
            if isinstance(reviewer, dict) and adapter_id in reviewer.get("coverage", [])
        ]
        rows.append({
            "adapter": adapter_id,
            "status": "covered" if matches else "missing",
            "reviewers": matches,
        })
    missing = [row["adapter"] for row in rows if row["status"] == "missing"]
    return {
        "status": "missing" if missing else "covered",
        "rows": rows,
        "details": f"missing coverage for: {', '.join(str(item) for item in missing)}" if missing else "all selected adapters have reviewer coverage",
    }


def build_summary(
    package_root: Path,
    previous_package_root: Path | None,
    adapter_file: Path | None = None,
    adapters: list[str] | None = None,
    assignment_file: Path | None = None,
    previous_assignment_file: Path | None = None,
    max_evidence_age_days: int | None = None,
    max_terminal_decision_age_days: int | None = None,
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
        selected_assignment_file = assignment_file or package_root / "review-assignment.yml"
        assignment_for_adapters = selected_assignment_file if selected_assignment_file.is_file() else None
        review_adapters = [
            inspect_adapter(
                adapter_id,
                package_root,
                selected_adapter_file,
                assignment_file=assignment_for_adapters,
                max_age_days=max_evidence_age_days,
            )
            for adapter_id in selected_adapters
        ]
        for adapter in review_adapters:
            if adapter["status"] == "blocked":
                blockers.append(f"{adapter['id']} review adapter is blocked: {adapter['details']}")
            elif adapter["status"] == "pending":
                warnings.append(f"{adapter['id']} review adapter is pending: {adapter['details']}")

    review_assignment = review_assignment_data(
        package_root,
        assignment_file,
        max_terminal_decision_age_days=max_terminal_decision_age_days,
    )
    review_assignment_diff = review_assignment_diff_data(
        package_root,
        previous_package_root,
        assignment_file=assignment_file,
        previous_assignment_file=previous_assignment_file,
    )
    review_assignment_coverage = review_assignment_coverage_data(review_assignment, selected_adapters)
    if review_assignment["status"] == "invalid":
        blockers.append(f"review assignment is invalid: {review_assignment['details']}")
    elif review_assignment["status"] in {"pending", "in_review"}:
        warnings.append(
            "Reviewer assignment is "
            f"{review_assignment['status']}: required human decisions are not complete."
        )
    elif review_assignment["status"] == "blocked":
        blockers.append("Reviewer assignment contains a blocked required review.")
    if review_assignment_diff["status"] == "invalid":
        warnings.append(f"Reviewer assignment baseline could not be compared: {review_assignment_diff['details']}")
    elif review_assignment_diff["status"] == "unavailable":
        warnings.append(f"Reviewer assignment baseline is unavailable: {review_assignment_diff['details']}")
    elif review_assignment_diff.get("changes"):
        warnings.append(f"{review_assignment_diff['details']}; review the assignment delta before handoff.")
    if review_assignment_coverage["status"] == "missing":
        warnings.append(f"Reviewer adapter coverage is incomplete: {review_assignment_coverage['details']}.")
    elif review_assignment_coverage["status"] == "unavailable":
        warnings.append(f"Reviewer adapter coverage could not be checked: {review_assignment_coverage['details']}.")

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
    elif review_assignment["status"] in {"pending", "in_review"}:
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
        next_actions.append("Complete the selected policy, accessibility, and privacy adapter reviews.")
    if review_assignment["status"] in {"pending", "in_review"}:
        next_actions.append("Assign and complete the required reviewer decisions in review-assignment.yml.")
    if review_assignment_diff.get("changes"):
        next_actions.append("Review the reviewer assignment delta against the supplied baseline.")
    if review_assignment_coverage["status"] == "missing":
        next_actions.append("Assign reviewer coverage for every selected review adapter.")
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
        "evidence_max_age_days": max_evidence_age_days,
        "reviewer_decision_max_age_days": max_terminal_decision_age_days,
        "asset_counts": dict(sorted(status_counts.items())),
        "assets_total": len(current_records),
        "changes": changes,
        "blockers": sorted(dict.fromkeys(blockers)),
        "warnings": sorted(dict.fromkeys(warnings)),
        "review_adapters": review_adapters,
        "review_assignment": review_assignment,
        "review_assignment_diff": review_assignment_diff,
        "review_assignment_coverage": review_assignment_coverage,
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
        if summary.get("evidence_max_age_days") is not None:
            lines.append(
                f"Evidence max age: `{summary['evidence_max_age_days']} days` (terminal records only)"
            )
            lines.append("")
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
        lines.append("No optional policy/accessibility/privacy adapters selected.")
    assignment = summary["review_assignment"]
    assert isinstance(assignment, dict)
    lines.extend(["", "## Reviewer assignment", ""])
    lines.append(f"- Status: `{assignment['status']}`")
    lines.append(f"- Owner: `{assignment.get('owner', 'not assigned')}`")
    lines.append(f"- History events: `{assignment.get('history_events', 0)}`")
    if summary.get("reviewer_decision_max_age_days") is not None:
        lines.append(
            "- Terminal decision max age: "
            f"`{summary['reviewer_decision_max_age_days']} days`"
        )
    if assignment["status"] == "not-supplied":
        lines.append("- No review-assignment.yml was supplied.")
    elif assignment["status"] == "invalid":
        lines.append(f"- Invalid record: {assignment['details']}")
    else:
        reviewers = assignment.get("reviewers", [])
        assert isinstance(reviewers, list)
        lines.extend(["", *markdown_table([
            {
                "id": str(item.get("id", "")),
                "role": str(item.get("role", "")),
                "required": str(item.get("required", "")),
                "status": str(item.get("status", "")),
                "scope": ", ".join(str(scope) for scope in item.get("scope", [])) or "not declared",
                "assigned_to": str(item.get("assigned_to", "")),
                "decision": str(item.get("decision", "")),
                "evidence": ", ".join(str(evidence) for evidence in item.get("evidence", [])) or "none",
            }
            for item in reviewers
        ], ("id", "role", "required", "scope", "status", "assigned_to", "decision", "evidence"))])
    assignment_diff = summary["review_assignment_diff"]
    assert isinstance(assignment_diff, dict)
    lines.extend(["", "### Assignment changes", ""])
    lines.append(f"- Baseline: `{assignment_diff.get('baseline', 'not-supplied')}`")
    if assignment_diff["status"] == "not-supplied":
        lines.append("- No previous reviewer assignment baseline supplied.")
    elif assignment_diff["status"] in {"invalid", "unavailable"}:
        lines.append(f"- Comparison unavailable: {assignment_diff['details']}")
    else:
        assignment_changes = assignment_diff.get("changes", [])
        assert isinstance(assignment_changes, list)
        if assignment_changes:
            lines.extend(markdown_table([
                {
                    "change": str(item.get("change", "")),
                    "reviewer": str(item.get("reviewer", "")),
                    "field": str(item.get("field", "")),
                    "before": str(item.get("before", "")) or "—",
                    "after": str(item.get("after", "")) or "—",
                }
                for item in assignment_changes
            ], ("change", "reviewer", "field", "before", "after")))
        else:
            lines.append("- No reviewer assignment changes detected against the supplied baseline.")
    assignment_coverage = summary["review_assignment_coverage"]
    assert isinstance(assignment_coverage, dict)
    lines.extend(["", "### Adapter coverage", ""])
    lines.append(f"- Status: `{assignment_coverage['status']}`")
    if assignment_coverage["status"] in {"not-checked", "unavailable"}:
        lines.append(f"- {assignment_coverage['details']}.")
    else:
        coverage_rows = assignment_coverage.get("rows", [])
        assert isinstance(coverage_rows, list)
        lines.extend(markdown_table([
            {
                "adapter": str(row.get("adapter", "")),
                "status": str(row.get("status", "")),
                "reviewers": ", ".join(
                    f"{item.get('id', '')} ({item.get('status', '')})"
                    for item in row.get("reviewers", [])
                ) or "none",
            }
            for row in coverage_rows
        ], ("adapter", "status", "reviewers")))
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
    parser.add_argument("--assignment-file", type=Path)
    parser.add_argument("--previous-assignment-file", type=Path)
    parser.add_argument(
        "--max-evidence-age-days",
        type=int,
        help="Optionally block selected terminal adapter evidence older than this many days.",
    )
    parser.add_argument(
        "--max-reviewer-decision-age-days",
        type=int,
        help="Optionally block terminal reviewer decisions older than this many days.",
    )
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
    if args.previous_assignment_file and not args.previous_assignment_file.is_file():
        print(f"Previous assignment file does not exist: {args.previous_assignment_file}", file=sys.stderr)
        return 2
    if args.max_evidence_age_days is not None and args.max_evidence_age_days < 0:
        print("--max-evidence-age-days must be zero or greater", file=sys.stderr)
        return 2
    if args.max_reviewer_decision_age_days is not None and args.max_reviewer_decision_age_days < 0:
        print("--max-reviewer-decision-age-days must be zero or greater", file=sys.stderr)
        return 2
    summary = build_summary(
        args.package_root.resolve(),
        args.previous_package_root.resolve() if args.previous_package_root else None,
        adapter_file=args.adapter_file.resolve() if args.adapter_file else None,
        adapters=args.adapter,
        assignment_file=args.assignment_file.resolve() if args.assignment_file else None,
        previous_assignment_file=args.previous_assignment_file.resolve() if args.previous_assignment_file else None,
        max_evidence_age_days=args.max_evidence_age_days,
        max_terminal_decision_age_days=args.max_reviewer_decision_age_days,
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
