#!/usr/bin/env python3
"""Validate locale plans, terminology mappings, and store-copy files."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import re
import unicodedata


ALLOWED_PLAN_STATUSES = {"source", "draft", "review", "verified", "blocked"}
ALLOWED_COPY_STATUSES = {"draft", "review", "verified", "blocked"}
SECTION_FIELD_LINE = re.compile(r"^\s{2}([a-z][a-z0-9_-]*):\s*(.*?)\s*$")
LOCALE_LINE = re.compile(r"^\s{4}-\s+code:\s*(.*?)\s*$")
LOCALE_FIELD_LINE = re.compile(r"^\s{6}([a-z][a-z0-9_-]*):\s*(.*?)\s*$")
ENTRY_LINE = re.compile(r"^\s{4}-\s+id:\s*(.*?)\s*$")
ENTRY_FIELD_LINE = re.compile(r"^\s{6}([a-z][a-z0-9_-]*):\s*(.*?)\s*$")
COPY_FIELD_LINE = re.compile(r"^(\s{0,2})([a-z][a-z0-9_-]*):\s*(.*?)\s*$")
COPY_PLATFORM_SECTIONS = {"apple", "google_play"}
ASCII_ALNUM = re.compile(r"[a-z0-9]")


def unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def normalize_for_matching(value: str) -> str:
    return unicodedata.normalize("NFKC", value).casefold()


def contains_term(text: str, term: str) -> bool:
    """Match Latin/number terms by token while preserving CJK substring matching."""
    normalized_text = normalize_for_matching(text)
    normalized_term = normalize_for_matching(term).strip()
    if not normalized_term:
        return False
    if ASCII_ALNUM.search(normalized_term):
        pattern = rf"(?<![a-z0-9]){re.escape(normalized_term)}(?![a-z0-9])"
        return re.search(pattern, normalized_text) is not None
    return normalized_term in normalized_text


def parse_list(value: str) -> list[str]:
    value = value.strip()
    if not (value.startswith("[") and value.endswith("]")):
        return []
    contents = value[1:-1].strip()
    if not contents:
        return []
    return [unquote(item.strip()) for item in contents.split(",") if item.strip()]


def parse_localization_plan(text: str) -> tuple[dict[str, str], list[dict[str, str]]]:
    section: dict[str, str] = {}
    locales: list[dict[str, str]] = []
    in_localization = False
    current: dict[str, str] | None = None
    for line in text.splitlines():
        if line == "localization:":
            in_localization = True
            continue
        if not in_localization:
            continue
        section_match = SECTION_FIELD_LINE.match(line)
        if section_match:
            key, value = section_match.groups()
            section[key] = unquote(value)
            continue
        locale_match = LOCALE_LINE.match(line)
        if locale_match:
            if current is not None:
                locales.append(current)
            current = {"code": unquote(locale_match.group(1))}
            continue
        if current is not None:
            field_match = LOCALE_FIELD_LINE.match(line)
            if field_match:
                key, value = field_match.groups()
                current[key] = unquote(value)
    if current is not None:
        locales.append(current)
    return section, locales


def parse_glossary(text: str) -> tuple[dict[str, str], list[dict[str, object]]]:
    section: dict[str, str] = {}
    entries: list[dict[str, object]] = []
    in_glossary = False
    current: dict[str, object] | None = None
    for line in text.splitlines():
        if line == "glossary:":
            in_glossary = True
            continue
        if not in_glossary:
            continue
        if line.startswith("  source_locale:"):
            section["source_locale"] = unquote(line.split(":", 1)[1])
            continue
        entry_match = ENTRY_LINE.match(line)
        if entry_match:
            if current is not None:
                entries.append(current)
            current = {"id": unquote(entry_match.group(1))}
            continue
        if current is not None:
            field_match = ENTRY_FIELD_LINE.match(line)
            if field_match:
                key, value = field_match.groups()
                current[key] = parse_list(value) if key == "do_not_use" else unquote(value)
    if current is not None:
        entries.append(current)
    return section, entries


def copy_metadata(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for key in ("schema_version", "locale", "status", "reviewer", "reviewed_at"):
        match = re.search(rf"^{key}:\s*(.*?)\s*$", text, re.MULTILINE)
        if match:
            values[key] = unquote(match.group(1))
    return values


def valid_timestamp(value: str) -> bool:
    try:
        datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def copy_platform_fields(text: str) -> set[str]:
    fields: set[str] = set()
    current_section: str | None = None
    for line in text.splitlines():
        match = COPY_FIELD_LINE.match(line)
        if not match:
            continue
        indentation, key, _ = match.groups()
        if len(indentation) == 0:
            current_section = key
            if key in COPY_PLATFORM_SECTIONS:
                fields.add(key)
        elif len(indentation) == 2 and current_section in COPY_PLATFORM_SECTIONS:
            fields.add(f"{current_section}.{key}")
    return fields


def validate(
    plan_path: Path,
    glossary_path: Path,
    package_root: Path,
) -> list[str]:
    errors: list[str] = []
    for path, label in ((plan_path, "localization plan"), (glossary_path, "terminology glossary")):
        if not path.is_file():
            errors.append(f"{label} does not exist: {path}")
    if errors:
        return errors

    plan_text = plan_path.read_text(encoding="utf-8")
    glossary_text = glossary_path.read_text(encoding="utf-8")
    if not re.search(r"^schema_version:\s*1\s*$", plan_text, re.MULTILINE):
        errors.append(f"{plan_path}: must declare schema_version: 1")
    if not re.search(r"^schema_version:\s*1\s*$", glossary_text, re.MULTILINE):
        errors.append(f"{glossary_path}: must declare schema_version: 1")

    plan, locales = parse_localization_plan(plan_text)
    glossary, entries = parse_glossary(glossary_text)
    source_locale = plan.get("source_locale", "")
    if not source_locale:
        errors.append(f"{plan_path}: localization.source_locale is required")
    if plan.get("status") not in ALLOWED_PLAN_STATUSES:
        errors.append(f"{plan_path}: localization.status is unsupported")
    if glossary.get("source_locale") != source_locale:
        errors.append(f"{glossary_path}: glossary.source_locale must match {source_locale}")
    if not locales:
        errors.append(f"{plan_path}: localization.locales must contain at least one locale")
    if sum(item.get("code") == source_locale for item in locales) != 1:
        errors.append(f"{plan_path}: source locale must occur exactly once")

    locale_codes = [str(item.get("code", "")) for item in locales]
    if len(set(locale_codes)) != len(locale_codes):
        errors.append(f"{plan_path}: locale codes must be unique")

    copy_texts: dict[str, str] = {}
    copy_paths: dict[str, Path] = {}
    copy_platform_field_sets: dict[str, set[str]] = {}
    for locale in locales:
        code = str(locale.get("code", ""))
        prefix = f"{plan_path}: locale {code or '<unnamed>'}"
        if locale.get("status") not in ALLOWED_PLAN_STATUSES:
            errors.append(f"{prefix}.status is unsupported")
        if locale.get("status") == "verified":
            if not str(locale.get("reviewer", "")).strip():
                errors.append(f"{prefix}.reviewer is required when status is verified")
            reviewed_at = str(locale.get("reviewed_at", ""))
            if not valid_timestamp(reviewed_at):
                errors.append(f"{prefix}.reviewed_at must be ISO-8601 when status is verified")
        relative = Path(str(locale.get("copy_file", "")))
        if not str(relative) or relative.is_absolute() or ".." in relative.parts:
            errors.append(f"{prefix}.copy_file must be a safe relative path")
            continue
        copy_path = package_root / relative
        if not copy_path.is_file():
            errors.append(f"{prefix}.copy_file does not exist: {relative}")
            continue
        text = copy_path.read_text(encoding="utf-8")
        copy_texts[code] = text
        copy_paths[code] = copy_path
        copy_platform_field_sets[code] = copy_platform_fields(text)
        metadata = copy_metadata(text)
        if metadata.get("schema_version") != "1":
            errors.append(f"{copy_path}: must declare schema_version: 1")
        if metadata.get("locale") != code:
            errors.append(f"{copy_path}: locale must be {code}")
        if metadata.get("status") not in ALLOWED_COPY_STATUSES:
            errors.append(f"{copy_path}: unsupported copy status")
        if metadata.get("status") == "verified":
            if not metadata.get("reviewer", "").strip():
                errors.append(f"{copy_path}: reviewer is required when status is verified")
            if not valid_timestamp(metadata.get("reviewed_at", "")):
                errors.append(f"{copy_path}: reviewed_at must be ISO-8601 when status is verified")
        if locale.get("status") == "verified" and metadata.get("status") != "verified":
            errors.append(f"{copy_path}: verified locale requires copy status verified")

    source_platform_fields = copy_platform_field_sets.get(source_locale, set())
    if source_platform_fields:
        for code, platform_fields in copy_platform_field_sets.items():
            if code == source_locale:
                continue
            missing_fields = sorted(source_platform_fields - platform_fields)
            extra_fields = sorted(platform_fields - source_platform_fields)
            if missing_fields:
                errors.append(
                    f"{copy_paths[code]}: "
                    f"missing platform copy fields from {source_locale}: {', '.join(missing_fields)}"
                )
            if extra_fields:
                errors.append(
                    f"{copy_paths[code]}: "
                    f"unexpected platform copy fields relative to {source_locale}: {', '.join(extra_fields)}"
                )

    seen_ids: set[str] = set()
    for entry in entries:
        entry_id = str(entry.get("id", ""))
        prefix = f"{glossary_path}: term {entry_id or '<unnamed>'}"
        if entry_id in seen_ids:
            errors.append(f"{prefix}: duplicate id")
        seen_ids.add(entry_id)
        for key in ("status", "source"):
            if not entry.get(key):
                errors.append(f"{prefix}.{key} is required")
        if entry.get("status") != "approved":
            errors.append(f"{prefix}.status must be approved before use")
        for code in locale_codes:
            localized = entry.get(code.lower())
            if not localized:
                errors.append(f"{prefix}: missing mapping for {code}")
                continue
            if str(entry.get("required", "false")).lower() != "true":
                continue
            copy_text = copy_texts.get(code, "")
            if not contains_term(copy_text, str(localized)):
                errors.append(f"{prefix}: required term missing from {code} copy")
        forbidden = entry.get("do_not_use", [])
        if isinstance(forbidden, list):
            for code, copy_text in copy_texts.items():
                for term in forbidden:
                    if contains_term(copy_text, str(term)):
                        errors.append(f"{prefix}: do_not_use term {term!r} found in {code} copy")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path, help="Localization plan")
    parser.add_argument("glossary", type=Path, help="Terminology glossary")
    parser.add_argument("--package-root", type=Path, required=True)
    args = parser.parse_args()

    try:
        errors = validate(args.plan, args.glossary, args.package_root.resolve())
    except (OSError, UnicodeDecodeError) as error:
        errors = [str(error)]
    if errors:
        print("Localization validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Validated localization plan and glossary: {args.plan}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
