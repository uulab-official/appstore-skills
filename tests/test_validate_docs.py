from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_docs.py"


class ValidateDocsTests(unittest.TestCase):
    def run_validator(self, root: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(root)],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_repository_docs_pass(self) -> None:
        result = self.run_validator(ROOT)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_local_link_fails(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text("[missing](missing.md)\n", encoding="utf-8")

            result = self.run_validator(root)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing.md", result.stdout)

    def test_absolute_local_link_fails(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text("[absolute](/tmp/file.md)\n", encoding="utf-8")

            result = self.run_validator(root)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("absolute local link", result.stdout)


if __name__ == "__main__":
    unittest.main()
