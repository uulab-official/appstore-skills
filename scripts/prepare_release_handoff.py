#!/usr/bin/env python3
"""Prepare a read-only dry-run handoff from an app project to store assets."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

from inspect_evidence_providers import inspect_provider
from validate_release_approval import parse_approval, validate as validate_approval


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
BUILD_SIGNAL_NAMES = (
    "package.json",
    "app.json",
    "app.config.js",
    "app.config.ts",
    "eas.json",
    "gradlew",
    "build.gradle",
    "build.gradle.kts",
    "fastlane",
    "ios",
    "android",
)
REQUIRED_OUTPUT_FILES = (
    "brand-context.yml",
    "manifest.yml",
    "QA.md",
    "release-report.md",
)
DEFAULT_PROVIDER_FILE = (
    Path(__file__).resolve().parents[1]
    / "skills/app-store-assets/references/evidence-providers.yml"
)


def quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def git_revision(project_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(project_root), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    revision = result.stdout.strip()
    return revision if result.returncode == 0 and revision else "unavailable"


def find_build_signals(project_root: Path) -> list[str]:
    found: list[str] = []
    for name in BUILD_SIGNAL_NAMES:
        if (project_root / name).exists():
            found.append(name)
    found.extend(path.name for path in sorted(project_root.glob("*.xcodeproj")))
    found.extend(path.name for path in sorted(project_root.glob("*.xcworkspace")))
    return found


def find_capture_files(project_root: Path, output_root: Path) -> list[str]:
    candidates = (
        output_root / "screenshots" / "source",
        project_root / "screenshots" / "source",
        project_root / "assets" / "screenshots",
        project_root / "assets" / "screens",
    )
    captures: list[str] = []
    seen: set[Path] = set()
    for directory in candidates:
        if not directory.is_dir():
            continue
        for path in sorted(directory.rglob("*")):
            if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES and path not in seen:
                seen.add(path)
                captures.append(str(path))
    return captures


def first_existing(root: Path, candidates: tuple[str, ...]) -> str | None:
    for relative in candidates:
        if (root / relative).is_file():
            return relative
    return None


def check(check_id: str, status: str, details: str) -> dict[str, str]:
    return {"id": check_id, "status": status, "details": details}


def human_approval_check(
    approval_file: Path | None,
) -> tuple[dict[str, str], str]:
    if approval_file is None:
        return (
            check(
                "human-approval",
                "pending",
                "no release-approval.yml supplied",
            ),
            "not-supplied",
        )

    approval_file = approval_file.resolve()
    if not approval_file.is_file():
        return (
            check("human-approval", "blocked", f"approval file is missing: {approval_file}"),
            str(approval_file),
        )

    errors = validate_approval(approval_file)
    if errors:
        return (
            check(
                "human-approval",
                "blocked",
                "invalid approval record: " + "; ".join(errors),
            ),
            str(approval_file),
        )

    approval = parse_approval(approval_file)
    status = str(approval.get("status", "pending"))
    scope = approval.get("scope", [])
    scope_text = ", ".join(str(item) for item in scope) if isinstance(scope, list) else "unknown"
    if status == "approved":
        owner = str(approval.get("owner", "unknown"))
        return (
            check(
                "human-approval",
                "pass",
                f"approved by {owner} for scope: {scope_text}",
            ),
            str(approval_file),
        )
    if status == "pending":
        return (
            check(
                "human-approval",
                "pending",
                f"approval is pending for scope: {scope_text}",
            ),
            str(approval_file),
        )
    return (
        check("human-approval", "blocked", f"approval status is {status}"),
        str(approval_file),
    )


def prepare_handoff(
    project_root: Path,
    output_root: Path,
    platforms: list[str],
    approval_file: Path | None = None,
    provider_file: Path | None = None,
    providers: list[str] | None = None,
    max_evidence_age_days: int | None = None,
    require_current_revision: bool = False,
    locales: list[str] | None = None,
    device_families: list[str] | None = None,
) -> dict[str, object]:
    project_root = project_root.resolve()
    output_root = output_root.resolve()
    build_signals = find_build_signals(project_root) if project_root.is_dir() else []
    captures = find_capture_files(project_root, output_root)
    source_revision = git_revision(project_root) if project_root.is_dir() else "unavailable"
    requested_locales = locales or []
    requested_device_families = device_families or []
    build_evidence = first_existing(
        output_root,
        ("evidence/build.yml", "evidence/build.json", "build-evidence.yml", "build.yml"),
    )
    selected_providers = providers or []
    provider_results: dict[str, dict[str, object]] = {}
    if selected_providers:
        selected_provider_file = provider_file or DEFAULT_PROVIDER_FILE
        for provider_id in selected_providers:
            provider_results[provider_id] = inspect_provider(
                provider_id,
                project_root,
                output_root,
                selected_provider_file,
                max_age_days=max_evidence_age_days,
                expected_revision=source_revision if source_revision != "unavailable" else None,
                require_current_revision=require_current_revision,
                expected_platforms=platforms,
                expected_locales=requested_locales,
                expected_device_families=requested_device_families,
            )
    checks: list[dict[str, str]] = []

    if project_root.is_dir():
        checks.append(check("project-root", "pass", str(project_root)))
    else:
        checks.append(check("project-root", "blocked", "project root does not exist"))

    if build_signals:
        checks.append(
            check("build-config", "pass", "found: " + ", ".join(build_signals))
        )
    else:
        checks.append(check("build-config", "blocked", "no supported build signal found"))

    build_provider = provider_results.get("build-record")
    if build_provider is not None:
        checks.append(
            check(
                "build-identity",
                "pass" if build_provider["status"] == "pass" else "blocked",
                f"provider build-record: {build_provider['details']}",
            )
        )
    elif build_evidence:
        checks.append(check("build-identity", "pass", build_evidence))
    else:
        checks.append(
            check(
                "build-identity",
                "blocked",
                "no evidence/build.yml or equivalent build record found",
            )
        )

    simulator_provider = provider_results.get("simulator-source-captures")
    if simulator_provider is not None:
        checks.append(
            check(
                "simulator-captures",
                "pass" if simulator_provider["status"] == "pass" else "blocked",
                f"provider simulator-source-captures: {simulator_provider['details']}",
            )
        )
    elif captures:
        checks.append(
            check("simulator-captures", "pass", f"found {len(captures)} image capture(s)")
        )
    else:
        checks.append(
            check(
                "simulator-captures",
                "blocked",
                "no real source capture found under screenshots/source or project capture folders",
            )
        )

    missing_output = [
        relative for relative in REQUIRED_OUTPUT_FILES if not (output_root / relative).is_file()
    ]
    if not missing_output:
        checks.append(check("store-output", "pass", "required package files exist"))
    else:
        checks.append(check("store-output", "blocked", "missing: " + ", ".join(missing_output)))

    release_report = output_root / "release-report.md"
    if release_report.is_file():
        checks.append(check("release-report", "pass", str(release_report)))
    else:
        checks.append(check("release-report", "blocked", "release-report.md is missing"))

    approval_check, approval_path = human_approval_check(approval_file)
    checks.append(approval_check)
    for provider_id, provider_result in provider_results.items():
        if provider_result["kind"] == "unknown":
            checks.append(
                check(
                    f"evidence-provider:{provider_id}",
                    "blocked",
                    str(provider_result["details"]),
                )
            )
    blocked = any(item["status"] == "blocked" for item in checks)
    pending_approval = any(item["status"] == "pending" for item in checks)
    next_actions: list[str] = []
    if not build_evidence:
        next_actions.append("Record the inspected build revision and artifact identity in evidence/build.yml.")
    if not captures:
        next_actions.append("Capture real iOS/Android screens and place source images under screenshots/source/.")
    if missing_output:
        next_actions.append("Complete the store package contract before handoff.")
    if approval_check["status"] == "pending":
        if approval_file is None:
            next_actions.append("Record an explicit human decision in release-approval.yml.")
        else:
            next_actions.append("Record the product-owner decision in the supplied approval file.")
    elif approval_check["status"] == "blocked":
        next_actions.append("Fix or replace the release approval record before handoff.")
    if any(item["status"] == "blocked" for item in provider_results.values()):
        next_actions.append("Resolve blocked opt-in evidence provider checks before handoff.")
    build_provider_details = str(provider_results.get("build-record", {}).get("details", ""))
    if "revision does not match" in build_provider_details:
        next_actions.append("Regenerate evidence/build.yml from the current project revision before handoff.")
    elif "current project revision is unavailable" in build_provider_details:
        next_actions.append("Run the revision-bound handoff from a Git project with a readable HEAD revision.")
    if "platform does not match requested platforms" in build_provider_details:
        next_actions.append("Record build evidence for a requested target platform before handoff.")
    simulator_provider_details = str(provider_results.get("simulator-source-captures", {}).get("details", ""))
    if "platform does not match requested platforms" in simulator_provider_details:
        next_actions.append("Capture source images for a requested target platform before handoff.")
    if "locale does not match requested locales" in simulator_provider_details:
        next_actions.append("Capture source images for a requested locale before handoff.")
    if "device family does not match requested device families" in simulator_provider_details:
        next_actions.append("Capture source images for a requested device family before handoff.")
    if not next_actions:
        next_actions.append("Handoff is approved for read-only execution review; publishing remains disabled.")

    if blocked:
        handoff_status = "blocked"
    elif pending_approval:
        handoff_status = "pending_approval"
    else:
        handoff_status = "ready_for_handoff"

    return {
        "schema_version": 1,
        "handoff": {
            "mode": "dry-run",
            "status": handoff_status,
            "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "project_root": str(project_root),
            "output_root": str(output_root),
            "source_revision": source_revision,
            "platforms": platforms,
            "locales": requested_locales,
            "device_families": requested_device_families,
            "provider_mode": "opt-in-read-only",
            "evidence_max_age_days": max_evidence_age_days,
            "require_current_revision": require_current_revision,
            "provider_file": str((provider_file or DEFAULT_PROVIDER_FILE).resolve())
            if selected_providers
            else "not-supplied",
            "providers": selected_providers,
            "approval_file": approval_path,
            "publish_status": "not-run",
            "checks": checks,
            "next_actions": next_actions,
        },
    }


def render_yaml(report: dict[str, object]) -> str:
    handoff = report["handoff"]
    assert isinstance(handoff, dict)
    lines = ["schema_version: 1", "handoff:"]
    scalar_keys = (
        "mode",
        "status",
        "generated_at",
        "project_root",
        "output_root",
        "source_revision",
        "provider_mode",
        "evidence_max_age_days",
        "require_current_revision",
        "provider_file",
        "approval_file",
        "publish_status",
    )
    for key in scalar_keys:
        value = handoff[key]
        if key == "evidence_max_age_days":
            lines.append(
                "  evidence_max_age_days: null"
                if value is None
                else f"  evidence_max_age_days: {value}"
            )
        elif isinstance(value, bool):
            lines.append(f"  {key}: {'true' if value else 'false'}")
        else:
            lines.append(f"  {key}: null" if value is None else f"  {key}: {quote(str(value))}")
    platforms = handoff["platforms"]
    if platforms:
        lines.append("  platforms:")
        for platform in platforms:
            lines.append(f"    - {quote(str(platform))}")
    else:
        lines.append("  platforms: []")
    locales = handoff["locales"]
    if locales:
        lines.append("  locales:")
        for locale in locales:
            lines.append(f"    - {quote(str(locale))}")
    else:
        lines.append("  locales: []")
    device_families = handoff["device_families"]
    if device_families:
        lines.append("  device_families:")
        for device_family in device_families:
            lines.append(f"    - {quote(str(device_family))}")
    else:
        lines.append("  device_families: []")
    lines.append("  providers:")
    for provider in handoff["providers"]:
        lines.append(f"    - {quote(str(provider))}")
    lines.append("  checks:")
    for item in handoff["checks"]:
        lines.append(f"    - id: {quote(item['id'])}")
        lines.append(f"      status: {quote(item['status'])}")
        lines.append(f"      details: {quote(item['details'])}")
    lines.append("  next_actions:")
    for action in handoff["next_actions"]:
        lines.append(f"    - {quote(str(action))}")
    return "\n".join(lines) + "\n"


def render_summary(report: dict[str, object]) -> str:
    handoff = report["handoff"]
    assert isinstance(handoff, dict)
    lines = [
        f"Release handoff: {handoff['status']}",
        f"Mode: {handoff['mode']}",
        f"Publish: {handoff['publish_status']}",
        f"Source revision: {handoff['source_revision']}",
        f"Evidence providers: {', '.join(handoff['providers']) or 'none selected'}",
        (
            f"Evidence max age: {handoff['evidence_max_age_days']} days"
            if handoff["evidence_max_age_days"] is not None
            else "Evidence max age: disabled"
        ),
        f"Revision binding: {'required' if handoff['require_current_revision'] else 'disabled'}",
        f"Locales: {', '.join(handoff['locales']) or 'none specified'}",
        f"Device families: {', '.join(handoff['device_families']) or 'none specified'}",
        f"Approval file: {handoff['approval_file']}",
        "Checks:",
    ]
    for item in handoff["checks"]:
        lines.append(f"- {item['status']}: {item['id']} — {item['details']}")
    lines.append("Next actions:")
    lines.extend(f"- {action}" for action in handoff["next_actions"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--platform", action="append", default=[])
    parser.add_argument("--format", choices=("yaml", "summary"), default="yaml")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--provider-file", type=Path)
    parser.add_argument("--provider", action="append", default=[])
    parser.add_argument(
        "--max-evidence-age-days",
        type=int,
        help="Optionally block selected build/capture evidence older than this many days.",
    )
    parser.add_argument(
        "--require-current-revision",
        action="store_true",
        help="Require selected build evidence revision to match the project Git revision.",
    )
    parser.add_argument(
        "--locale",
        action="append",
        default=[],
        help="Optionally require selected source captures to match a requested locale.",
    )
    parser.add_argument(
        "--device-family",
        action="append",
        default=[],
        help="Optionally require selected source captures to match a requested device family.",
    )
    parser.add_argument("--approval-file", type=Path)
    parser.add_argument("--fail-on-blocked", action="store_true")
    parser.add_argument("--fail-on-pending-approval", action="store_true")
    args = parser.parse_args()

    if not args.project_root.is_dir():
        print(f"Project root does not exist: {args.project_root}", file=sys.stderr)
        return 2
    if not args.output_root.is_dir():
        print(f"Output root does not exist: {args.output_root}", file=sys.stderr)
        return 2
    if args.max_evidence_age_days is not None and args.max_evidence_age_days < 0:
        print("--max-evidence-age-days must be zero or greater", file=sys.stderr)
        return 2

    report = prepare_handoff(
        args.project_root,
        args.output_root,
        args.platform,
        approval_file=args.approval_file,
        provider_file=args.provider_file,
        providers=args.provider,
        max_evidence_age_days=args.max_evidence_age_days,
        require_current_revision=args.require_current_revision,
        locales=args.locale,
        device_families=args.device_family,
    )
    rendered = render_yaml(report) if args.format == "yaml" else render_summary(report)
    if args.output:
        if args.output.exists() and not args.overwrite:
            print(f"Refusing to overwrite existing handoff: {args.output}", file=sys.stderr)
            return 2
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(f"Wrote release handoff: {args.output}")
    else:
        print(rendered, end="")

    handoff = report["handoff"]
    assert isinstance(handoff, dict)
    if args.fail_on_blocked and handoff["status"] == "blocked":
        return 1
    if args.fail_on_pending_approval and handoff["status"] == "pending_approval":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
