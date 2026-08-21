from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_copy_experiments.py"
DEMO = ROOT / "examples/demo-store-assets"
EXPERIMENT = DEMO / "metadata/copy-experiments.yml"


class ValidateCopyExperimentsTests(unittest.TestCase):
    def run_validator(self, path: Path, package: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(path), "--package-root", str(package)],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_demo_experiment_passes(self) -> None:
        result = self.run_validator(EXPERIMENT, DEMO)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_verified_variant_requires_approval(self) -> None:
        with TemporaryDirectory() as directory:
            package = Path(directory)
            (package / "metadata").mkdir()
            (package / "metadata" / "control.yml").write_text("locale: en-US\n", encoding="utf-8")
            (package / "metadata" / "variant.yml").write_text("locale: en-US\n", encoding="utf-8")
            path = package / "experiment.yml"
            path.write_text(
                """schema_version: 1
experiment:
  id: test
  status: review
  source_locale: en-US
  objective: test
  measurement: manual-review
  variants:
    - id: one
      status: verified
      label: One
      copy_file: metadata/control.yml
      hypothesis: one
      approval_status: pending
      evidence: []
    - id: two
      status: review
      label: Two
      copy_file: metadata/variant.yml
      hypothesis: two
      approval_status: pending
      evidence: []
  history:
    - at: 2026-08-21T00:00:00Z
      action: created
      actor: test
      note: test
""",
                encoding="utf-8",
            )

            result = self.run_validator(path, package)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("verified variant requires approved", result.stdout)

    def test_unsafe_variant_path_fails(self) -> None:
        source = EXPERIMENT.read_text(encoding="utf-8").replace(
            "copy_file: metadata/store-copy.en-US.yml",
            "copy_file: ../outside.yml",
            1,
        )
        with TemporaryDirectory() as directory:
            package = Path(directory)
            (package / "metadata").mkdir()
            path = package / "experiment.yml"
            path.write_text(source, encoding="utf-8")

            result = self.run_validator(path, package)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("copy_file must be a safe relative path", result.stdout)


if __name__ == "__main__":
    unittest.main()
