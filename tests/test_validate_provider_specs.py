from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_provider_specs.py"
REGISTRY = ROOT / "skills/app-store-assets/references/evidence-providers.yml"


class ValidateProviderSpecsTests(unittest.TestCase):
    def run_validator(self, *paths: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *(str(path) for path in paths)],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_repository_registry_passes(self) -> None:
        result = self.run_validator(REGISTRY)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_project_facts_provider_remains_optional(self) -> None:
        source = REGISTRY.read_text(encoding="utf-8")
        start = source.index("  - id: project-facts\n")
        end = source.index("  - id: simulator-source-captures\n", start)
        legacy = source[:start] + source[end:]
        with TemporaryDirectory() as directory:
            path = Path(directory) / "legacy-providers.yml"
            path.write_text(legacy, encoding="utf-8")

            result = self.run_validator(path)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_side_effects_are_rejected(self) -> None:
        source = REGISTRY.read_text(encoding="utf-8")
        invalid = source.replace("    side_effects: none\n", "    side_effects: shell\n", 1)
        with TemporaryDirectory() as directory:
            path = Path(directory) / "invalid-providers.yml"
            path.write_text(invalid, encoding="utf-8")

            result = self.run_validator(path)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("side_effects must be none", result.stdout)

    def test_provider_registry_requires_explicit_selection(self) -> None:
        source = REGISTRY.read_text(encoding="utf-8")
        invalid = source.replace("  selection: explicit\n", "  selection: automatic\n", 1)
        with TemporaryDirectory() as directory:
            path = Path(directory) / "invalid-providers.yml"
            path.write_text(invalid, encoding="utf-8")

            result = self.run_validator(path)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("provider_set.selection must be explicit", result.stdout)

    def test_provider_paths_cannot_escape_output_root(self) -> None:
        source = REGISTRY.read_text(encoding="utf-8")
        invalid = source.replace(
            "    evidence_path: evidence/build.yml\n",
            "    evidence_path: ../../outside.yml\n",
            1,
        )
        with TemporaryDirectory() as directory:
            path = Path(directory) / "invalid-providers.yml"
            path.write_text(invalid, encoding="utf-8")

            result = self.run_validator(path)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("evidence_path must stay inside the output root", result.stdout)


if __name__ == "__main__":
    unittest.main()
