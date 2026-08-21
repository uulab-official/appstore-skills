from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_evidence_specs.py"
EVIDENCE_MAP = ROOT / "skills/app-store-assets/references/evidence-adapters.yml"


class ValidateEvidenceSpecsTests(unittest.TestCase):
    def run_validator(self, *paths: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *(str(path) for path in paths)],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_repository_evidence_map_passes(self) -> None:
        result = self.run_validator(EVIDENCE_MAP)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_kind_fails(self) -> None:
        source = EVIDENCE_MAP.read_text(encoding="utf-8")
        invalid = source.replace("    kind: simulator\n", "    kind: capture\n", 1)
        with TemporaryDirectory() as directory:
            path = Path(directory) / "invalid-evidence.yml"
            path.write_text(invalid, encoding="utf-8")

            result = self.run_validator(path)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("kind must be one of", result.stdout)


if __name__ == "__main__":
    unittest.main()
