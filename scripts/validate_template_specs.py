#!/usr/bin/env python3
"""Validate repository-local promotional and feature-graphic template specs."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys


ALLOWED_KINDS = {"promotional", "feature-graphic"}
ALLOWED_STATUSES = {"draft", "review", "verified", "blocked"}
ALLOWED_FORMATS = {"png", "svg"}
SECTION_LINE = re.compile(r"^([a-z][a-z0-9_-]*):\s*$")
FIELD_LINE = re.compile(r"^\s{2}([a-z][a-z0-9_-]*):\s*(.*?)\s*$")


def unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def section_values(text: str, name: str) -> dict[str, str]:
    values: dict[str, str] = {}
    lines = text.splitlines()
    start = next((index for index, line in enumerate(lines) if line == f"{name}:"), None)
    if start is None:
        return values

    for line in lines[start + 1 :]:
        if line and not line.startswith(" "):
            break
        match = FIELD_LINE.match(line)
        if match:
            key, value = match.groups()
            values[key] = unquote(value)
    return values


def positive_int(value: str | None) -> int | None:
    if value is None or not re.fullmatch(r"[1-9]\d*", value.strip()):
        return None
    return int(value)


def validate(path: Path) -> list[str]:
    if not path.is_file():
        return [f"template spec does not exist: {path}"]

    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    if not re.search(r"^schema_version:\s*1\s*$", text, re.MULTILINE):
        errors.append(f"{path}: must declare schema_version: 1")

    template = section_values(text, "template")
    for key in ("id", "kind", "status", "purpose"):
        if not template.get(key):
            errors.append(f"{path}: template.{key} is required")
    if template.get("kind") not in ALLOWED_KINDS:
        errors.append(
            f"{path}: template.kind must be one of {sorted(ALLOWED_KINDS)}"
        )
    if template.get("status") not in ALLOWED_STATUSES:
        errors.append(
            f"{path}: template.status must be one of {sorted(ALLOWED_STATUSES)}"
        )

    canvas = section_values(text, "canvas")
    width = positive_int(canvas.get("width"))
    height = positive_int(canvas.get("height"))
    if width is None or height is None:
        errors.append(f"{path}: canvas.width and canvas.height must be positive integers")
    if canvas.get("format") not in ALLOWED_FORMATS:
        errors.append(f"{path}: canvas.format must be one of {sorted(ALLOWED_FORMATS)}")

    safe_area = section_values(text, "safe_area")
    safe_values = {key: positive_int(safe_area.get(key)) for key in ("left", "right", "top", "bottom")}
    if any(value is None for value in safe_values.values()):
        errors.append(f"{path}: safe_area left/right/top/bottom must be positive integers")
    elif width is not None and height is not None:
        if safe_values["left"] + safe_values["right"] >= width:
            errors.append(f"{path}: horizontal safe area must leave usable width")
        if safe_values["top"] + safe_values["bottom"] >= height:
            errors.append(f"{path}: vertical safe area must leave usable height")

    layout = section_values(text, "layout")
    for key in ("type", "text_zone", "visual_zone", "focal_point"):
        if not layout.get(key):
            errors.append(f"{path}: layout.{key} is required")

    content = section_values(text, "content")
    for key in ("headline", "supporting_line", "max_headline_chars", "max_supporting_line_chars"):
        if key not in content:
            errors.append(f"{path}: content.{key} is required")
    for key in ("max_headline_chars", "max_supporting_line_chars"):
        if key in content and positive_int(content[key]) is None:
            errors.append(f"{path}: content.{key} must be a positive integer")

    visual = section_values(text, "visual")
    if "hero_asset" not in visual:
        errors.append(f"{path}: visual.hero_asset is required")
    for key in ("background_treatment", "material_limit", "key_light_count", "detail_budget"):
        if key not in visual:
            errors.append(f"{path}: visual.{key} is required")
    for key in ("material_limit", "key_light_count"):
        if key in visual and positive_int(visual[key]) is None:
            errors.append(f"{path}: visual.{key} must be a positive integer")

    outputs = section_values(text, "outputs")
    if not outputs.get("master"):
        errors.append(f"{path}: outputs.master is required")

    if template.get("kind") == "feature-graphic":
        platform = section_values(text, "platform")
        if platform.get("submission_dimensions") != "verify-at-execution":
            errors.append(
                f"{path}: feature-graphic submission_dimensions must be verify-at-execution"
            )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="Template spec files")
    args = parser.parse_args()

    errors: list[str] = []
    for path in args.paths:
        errors.extend(validate(path))
    if errors:
        print("Template validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Validated {len(args.paths)} template specs successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
