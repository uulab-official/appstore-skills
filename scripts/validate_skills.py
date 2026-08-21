#!/usr/bin/env python3
"""Validate the repository-local skill pack with only the Python standard library."""

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LOCAL_LINK_RE = re.compile(r"\]\((?!https?://|mailto:|#)([^)#]+)\)")
FRONTMATTER_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):", re.MULTILINE)
MAX_SKILL_LINES = 500


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)


def validate_skill(skill_dir: Path, errors: list[str]) -> None:
    name = skill_dir.name
    skill_file = skill_dir / "SKILL.md"
    metadata_file = skill_dir / "agents" / "openai.yaml"

    if not NAME_RE.fullmatch(name):
        fail(f"{skill_dir}: invalid skill directory name", errors)
    if not skill_file.is_file():
        fail(f"{skill_dir}: missing SKILL.md", errors)
        return
    if not metadata_file.is_file():
        fail(f"{skill_dir}: missing agents/openai.yaml", errors)

    text = skill_file.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        fail(f"{skill_file}: missing YAML frontmatter", errors)
        return
    parts = text.split("---\n", 2)
    if len(parts) != 3:
        fail(f"{skill_file}: malformed YAML frontmatter", errors)
        return

    frontmatter, body = parts[1], parts[2]
    frontmatter_keys = FRONTMATTER_KEY_RE.findall(frontmatter)
    if set(frontmatter_keys) != {"name", "description"}:
        fail(
            f"{skill_file}: frontmatter must contain only name and description",
            errors,
        )
    frontmatter_names = re.findall(r"^name:\s*(\S+)\s*$", frontmatter, re.MULTILINE)
    descriptions = re.findall(r"^description:\s*(.+?)\s*$", frontmatter, re.MULTILINE)
    if frontmatter_names != [name]:
        fail(f"{skill_file}: frontmatter name must be {name!r}", errors)
    if len(descriptions) != 1 or descriptions[0].startswith("[TODO"):
        fail(f"{skill_file}: missing usable description", errors)
    elif "Use when" not in descriptions[0]:
        fail(f"{skill_file}: description must include a Use when trigger", errors)
    if re.search(r"\[TODO|\bTODO\s*:", body):
        fail(f"{skill_file}: contains TODO placeholder", errors)
    if len(text.splitlines()) > MAX_SKILL_LINES:
        fail(f"{skill_file}: exceeds {MAX_SKILL_LINES} lines", errors)

    for relative in LOCAL_LINK_RE.findall(text):
        if relative.startswith("/"):
            fail(f"{skill_file}: local links must be relative: {relative}", errors)
            continue
        if not (skill_dir / relative).is_file():
            fail(f"{skill_file}: missing referenced file {relative}", errors)

    if metadata_file.is_file():
        metadata = metadata_file.read_text(encoding="utf-8")
        for key in ("display_name", "short_description", "default_prompt"):
            if not re.search(rf"^\s+{key}:\s*.+$", metadata, re.MULTILINE):
                fail(f"{metadata_file}: missing interface.{key}", errors)


def main() -> int:
    errors: list[str] = []
    for required in (ROOT / "README.md", ROOT / "LICENSE", ROOT / "CONTRIBUTING.md"):
        if not required.is_file():
            fail(f"missing repository file: {required.relative_to(ROOT)}", errors)

    if not SKILLS.is_dir():
        fail("missing skills directory", errors)
    else:
        skill_dirs = sorted(path for path in SKILLS.iterdir() if path.is_dir())
        if not skill_dirs:
            fail("skills directory is empty", errors)
        for skill_dir in skill_dirs:
            validate_skill(skill_dir, errors)

    if errors:
        print("Skill validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Validated {len(list(SKILLS.iterdir()))} skills successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
