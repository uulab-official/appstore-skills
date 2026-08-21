#!/usr/bin/env python3
"""Validate a generated store asset package without third-party packages."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys


ALLOWED_STATUSES = {"draft", "review", "verified", "blocked"}
PATH_LINE = re.compile(r"^\s*-\s+path:\s*(.+?)\s*$")
STATUS_LINE = re.compile(r"^\s+status:\s*(.+?)\s*$")


def unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def validate(output_root: Path) -> list[str]:
    errors: list[str] = []
    required = ("brand-context.yml", "manifest.yml", "QA.md")
    for filename in required:
        path = output_root / filename
        if not path.is_file():
            errors.append(f"missing required file: {filename}")

    manifest = output_root / "manifest.yml"
    if not manifest.is_file():
        return errors

    manifest_text = manifest.read_text(encoding="utf-8")
    if not re.search(r"^schema_version:\s*1\s*$", manifest_text, re.MULTILINE):
        errors.append("manifest.yml must declare schema_version: 1")

    asset_paths: list[str] = []
    statuses: list[str] = []
    for line in manifest_text.splitlines():
        path_match = PATH_LINE.match(line)
        if path_match:
            asset_paths.append(unquote(path_match.group(1)))
        status_match = STATUS_LINE.match(line)
        if status_match:
            statuses.append(unquote(status_match.group(1)))

    if not asset_paths:
        errors.append("manifest.yml does not list any assets")

    for status in statuses:
        if status not in ALLOWED_STATUSES:
            errors.append(
                f"manifest.yml contains unsupported asset status {status!r}; "
                f"expected one of {sorted(ALLOWED_STATUSES)}"
            )

    for relative in asset_paths:
        candidate = Path(relative)
        if candidate.is_absolute() or ".." in candidate.parts:
            errors.append(f"asset path must stay inside output root: {relative}")
            continue
        resolved = output_root / candidate
        if not resolved.is_file():
            errors.append(f"manifest asset does not exist: {relative}")
        elif resolved.stat().st_size == 0:
            errors.append(f"manifest asset is empty: {relative}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_root", type=Path, help="Generated store asset directory")
    args = parser.parse_args()
    output_root = args.output_root.resolve()

    if not output_root.is_dir():
        print(f"Output directory does not exist: {output_root}", file=sys.stderr)
        return 2

    errors = validate(output_root)
    if errors:
        print("Store output validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Validated store output: {output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

