#!/usr/bin/env python3
"""Validate a generated store asset package without third-party packages."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import struct
import sys


ALLOWED_STATUSES = {"draft", "review", "verified", "blocked"}
PATH_LINE = re.compile(r"^\s*-\s+path:\s*(.+?)\s*$")
ASSET_FIELD_LINE = re.compile(r"^\s{4}([A-Za-z0-9_-]+):\s*(.*?)\s*$")
DIMENSIONS_VALUE = re.compile(r"^([1-9]\d*)x([1-9]\d*)$", re.IGNORECASE)
SVG_VIEWBOX = re.compile(
    r"\bviewBox\s*=\s*['\"]\s*"
    r"([-+]?\d*\.?\d+)\s+([-+]?\d*\.?\d+)\s+"
    r"([-+]?\d*\.?\d+)\s+([-+]?\d*\.?\d+)\s*['\"]",
    re.IGNORECASE,
)

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
PNG_COLOR_TYPES = {
    0: "grayscale",
    2: "rgb",
    3: "indexed",
    4: "grayscale-alpha",
    6: "rgba",
}
SUPPORTED_IMAGE_FORMATS = {"png", "svg"}


def unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def parse_asset_records(manifest_text: str) -> list[dict[str, str]]:
    """Parse the small, stable asset subset of manifest.yml without PyYAML."""

    records: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for line in manifest_text.splitlines():
        path_match = PATH_LINE.match(line)
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
            if key in {"status", "format", "dimensions", "color_type"}:
                current[key] = unquote(value)

    if current is not None:
        records.append(current)
    return records


def parse_expected_dimensions(value: str) -> tuple[int, int] | None:
    match = DIMENSIONS_VALUE.fullmatch(value.strip())
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def read_png_metadata(path: Path) -> tuple[int, int, str] | str:
    header = path.read_bytes()[:29]
    if len(header) < 29 or header[:8] != PNG_SIGNATURE or header[12:16] != b"IHDR":
        return "invalid PNG signature or IHDR header"

    width, height = struct.unpack(">II", header[16:24])
    if width == 0 or height == 0:
        return "PNG width and height must be positive"
    color_type = PNG_COLOR_TYPES.get(header[25])
    if color_type is None:
        return f"unsupported PNG color type {header[25]}"
    return width, height, color_type


def read_svg_metadata(path: Path, require_viewbox: bool) -> tuple[float, float] | None | str:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return "SVG is not valid UTF-8 text"

    if not re.search(r"<svg\b", text, re.IGNORECASE):
        return "missing <svg> root element"
    match = SVG_VIEWBOX.search(text)
    if not match:
        if require_viewbox:
            return "missing numeric viewBox metadata"
        return None
    _, _, width, height = (float(value) for value in match.groups())
    if width <= 0 or height <= 0:
        return "viewBox width and height must be positive"
    return width, height


def validate_image_metadata(output_root: Path, record: dict[str, str]) -> list[str]:
    """Validate image fields declared on one manifest asset record."""

    declared_format = record.get("format", "").strip().lower()
    dimensions_value = record.get("dimensions", "").strip()
    declared_color_type = record.get("color_type", "").strip().lower()
    relative = record["path"]
    if not any((declared_format, dimensions_value, declared_color_type)):
        return []

    errors: list[str] = []
    if not declared_format:
        errors.append(
            f"manifest asset {relative!r} declares image metadata without format"
        )
        return errors
    if declared_format not in SUPPORTED_IMAGE_FORMATS:
        errors.append(
            f"manifest asset {relative!r} declares unsupported image format "
            f"{declared_format!r}; expected one of {sorted(SUPPORTED_IMAGE_FORMATS)}"
        )
        return errors

    expected_dimensions: tuple[int, int] | None = None
    if dimensions_value:
        expected_dimensions = parse_expected_dimensions(dimensions_value)
        if expected_dimensions is None:
            errors.append(
                f"manifest asset {relative!r} has invalid dimensions "
                f"{dimensions_value!r}; expected WIDTHxHEIGHT"
            )

    path = output_root / relative
    suffix = path.suffix.lower().lstrip(".")
    if suffix != declared_format:
        errors.append(
            f"manifest asset {relative!r} declares format {declared_format!r} "
            f"but uses .{suffix or 'no extension'}"
        )
        return errors
    if not path.is_file() or path.stat().st_size == 0:
        return errors

    if declared_format == "png":
        metadata = read_png_metadata(path)
        if isinstance(metadata, str):
            errors.append(f"manifest asset {relative!r}: {metadata}")
            return errors
        width, height, color_type = metadata
        actual_dimensions = (width, height)
        if expected_dimensions is not None and actual_dimensions != expected_dimensions:
            errors.append(
                f"manifest asset {relative!r} dimensions are "
                f"{width}x{height}, expected {dimensions_value}"
            )
        if declared_color_type and declared_color_type != color_type:
            errors.append(
                f"manifest asset {relative!r} PNG color type is {color_type!r}, "
                f"expected {declared_color_type!r}"
            )
        return errors

    metadata = read_svg_metadata(path, expected_dimensions is not None)
    if isinstance(metadata, str):
        errors.append(f"manifest asset {relative!r}: {metadata}")
        return errors
    if metadata is None:
        return errors
    width, height = metadata
    if expected_dimensions is not None and (width, height) != expected_dimensions:
        errors.append(
            f"manifest asset {relative!r} viewBox is "
            f"{width:g}x{height:g}, expected {dimensions_value}"
        )
    if declared_color_type:
        errors.append(
            f"manifest asset {relative!r} declares color_type, which is only "
            "supported for PNG assets"
        )
    return errors


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

    asset_records = parse_asset_records(manifest_text)
    asset_paths = [record["path"] for record in asset_records]
    statuses = [record["status"] for record in asset_records if "status" in record]

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

    for record in asset_records:
        relative = record["path"]
        candidate = Path(relative)
        if candidate.is_absolute() or ".." in candidate.parts:
            continue
        resolved = output_root / candidate
        if resolved.is_file() and resolved.stat().st_size > 0:
            errors.extend(validate_image_metadata(output_root, record))

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
