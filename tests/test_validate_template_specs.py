from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_template_specs.py"
TEMPLATES = (
    ROOT / "skills/app-store-assets/references/promotional-template.yml",
    ROOT / "skills/app-store-assets/references/feature-graphic-template.yml",
)


class ValidateTemplateSpecsTests(unittest.TestCase):
    def run_validator(self, *paths: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *(str(path) for path in paths)],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_repository_templates_pass(self) -> None:
        result = self.run_validator(*TEMPLATES)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_invalid_safe_area_fails(self) -> None:
        source = TEMPLATES[0].read_text(encoding="utf-8")
        invalid = source.replace("  left: 96\n", "  left: 1600\n", 1)
        with TemporaryDirectory() as directory:
            path = Path(directory) / "invalid-template.yml"
            path.write_text(invalid, encoding="utf-8")

            result = self.run_validator(path)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("horizontal safe area must leave usable width", result.stdout)


if __name__ == "__main__":
    unittest.main()
