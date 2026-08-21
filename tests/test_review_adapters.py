from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]
VALIDATE_SCRIPT = ROOT / "scripts/validate_review_adapter_specs.py"
INSPECT_SCRIPT = ROOT / "scripts/inspect_review_adapters.py"
REGISTRY = ROOT / "skills/release-check/references/review-adapters.yml"


class ReviewAdapterTests(unittest.TestCase):
    def run_validator(self, *paths: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(VALIDATE_SCRIPT), *(str(path) for path in paths)],
            check=False,
            capture_output=True,
            text=True,
        )

    def run_inspector(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(INSPECT_SCRIPT), *args],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_registry_passes(self) -> None:
        result = self.run_validator(REGISTRY)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_optional_records_are_pending(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory) / "app"
            output = project / "store-assets"
            project.mkdir()
            output.mkdir()

            result = self.run_inspector(
                "--adapter-file", str(REGISTRY),
                "--project-root", str(project),
                "--output-root", str(output),
                "--adapter", "policy-review",
                "--adapter", "accessibility-review",
                "--adapter", "privacy-review",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("pending: policy-review", result.stdout)
            self.assertIn("pending: accessibility-review", result.stdout)
            self.assertIn("pending: privacy-review", result.stdout)

    def test_passing_record_requires_reviewer_evidence(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory) / "app"
            output = project / "store-assets"
            evidence = output / "evidence"
            project.mkdir()
            evidence.mkdir(parents=True)
            (evidence / "policy-review.yml").write_text(
                """schema_version: 1
review:
  status: pass
  reviewer: Product reviewer
  scope:
    - claims
  reviewed_at: 2026-08-21T10:00:00Z
  evidence:
    - review-ticket-1
  notes: reviewed
""",
                encoding="utf-8",
            )

            result = self.run_inspector(
                "--adapter-file", str(REGISTRY),
                "--project-root", str(project),
                "--output-root", str(output),
                "--adapter", "policy-review",
                "--format", "json",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('"status": "pass"', result.stdout)

    def test_privacy_record_uses_the_same_evidence_contract(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory) / "app"
            output = project / "store-assets"
            evidence = output / "evidence"
            project.mkdir()
            evidence.mkdir(parents=True)
            (evidence / "privacy-review.yml").write_text(
                """schema_version: 1
review:
  status: pass
  reviewer: Privacy reviewer
  scope: [collection, disclosure]
  reviewed_at: 2026-08-21T10:00:00Z
  evidence:
    - privacy-review-ticket
  notes: reviewed
""",
                encoding="utf-8",
            )

            result = self.run_inspector(
                "--adapter-file", str(REGISTRY),
                "--project-root", str(project),
                "--output-root", str(output),
                "--adapter", "privacy-review",
                "--format", "json",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('"status": "pass"', result.stdout)

    def test_invalid_terminal_record_can_gate(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory) / "app"
            output = project / "store-assets"
            evidence = output / "evidence"
            project.mkdir()
            evidence.mkdir(parents=True)
            (evidence / "policy-review.yml").write_text(
                """schema_version: 1
review:
  status: pass
  reviewer: ""
  scope: [claims]
  reviewed_at: ""
  evidence: []
""",
                encoding="utf-8",
            )

            result = self.run_inspector(
                "--adapter-file", str(REGISTRY),
                "--project-root", str(project),
                "--output-root", str(output),
                "--adapter", "policy-review",
                "--fail-on-blocked",
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("blocked: policy-review", result.stdout)


if __name__ == "__main__":
    unittest.main()
