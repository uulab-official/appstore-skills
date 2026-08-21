from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_adapter_specs.py"
ADAPTER_MAP = ROOT / "skills/app-store-assets/references/platform-adapters.yml"


class ValidateAdapterSpecsTests(unittest.TestCase):
    def run_validator(self, *paths: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *(str(path) for path in paths)],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_repository_adapter_map_passes(self) -> None:
        result = self.run_validator(ADAPTER_MAP)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_duplicate_platform_fails(self) -> None:
        source = ADAPTER_MAP.read_text(encoding="utf-8")
        invalid = source.replace("    platform: google-play\n", "    platform: apple\n", 1)
        with TemporaryDirectory() as directory:
            path = Path(directory) / "invalid-adapters.yml"
            path.write_text(invalid, encoding="utf-8")

            result = self.run_validator(path)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("duplicate platform", result.stdout)


if __name__ == "__main__":
    unittest.main()
