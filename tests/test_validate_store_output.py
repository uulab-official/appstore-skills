from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_store_output.py"


class ValidateStoreOutputTests(unittest.TestCase):
    def run_validator(self, output_root: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(output_root)],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_valid_package_passes(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "brand-context.yml").write_text("schema_version: 1\n", encoding="utf-8")
            (root / "QA.md").write_text("# QA\n", encoding="utf-8")
            (root / "icon").mkdir()
            (root / "icon" / "icon-master.png").write_bytes(b"not-an-image-but-not-empty")
            (root / "manifest.yml").write_text(
                "schema_version: 1\nassets:\n"
                "  - path: icon/icon-master.png\n"
                "    status: review\n",
                encoding="utf-8",
            )

            result = self.run_validator(root)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_path_traversal_fails(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "brand-context.yml").write_text("schema_version: 1\n", encoding="utf-8")
            (root / "QA.md").write_text("# QA\n", encoding="utf-8")
            (root / "manifest.yml").write_text(
                "schema_version: 1\nassets:\n"
                "  - path: ../secret.txt\n"
                "    status: review\n",
                encoding="utf-8",
            )

            result = self.run_validator(root)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must stay inside output root", result.stdout)


if __name__ == "__main__":
    unittest.main()

