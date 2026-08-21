#!/usr/bin/env python3
"""Validate local Markdown links with only the Python standard library."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys


MARKDOWN_LINK = re.compile(r"\]\(([^)\s]+)(?:\s+['\"][^)]*['\"])?\)")


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    markdown_files = sorted(
        path
        for path in root.rglob("*.md")
        if ".git" not in path.parts
    )
    for source in markdown_files:
        text = source.read_text(encoding="utf-8")
        for target in MARKDOWN_LINK.findall(text):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            if target.startswith("/"):
                errors.append(f"{source.relative_to(root)}: absolute local link {target}")
                continue
            target_path = target.split("#", 1)[0]
            if not target_path:
                continue
            resolved = (source.parent / target_path).resolve()
            if not resolved.exists():
                errors.append(f"{source.relative_to(root)}: {target}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        print(f"Documentation root does not exist: {root}", file=sys.stderr)
        return 2

    errors = validate(root)
    if errors:
        print("Documentation link validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Validated Markdown links under {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
