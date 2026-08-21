from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_release_approval.py"
REFERENCE = ROOT / "skills/app-store-assets/references/release-approval.yml"


class ValidateReleaseApprovalTests(unittest.TestCase):
    def run_validator(self, *paths: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *(str(path) for path in paths)],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_pending_reference_passes(self) -> None:
        result = self.run_validator(REFERENCE)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_approved_record_requires_audit_fields(self) -> None:
        approved = """schema_version: 1
approval:
  status: approved
  owner: ""
  scope:
    - apple
  decision: approved
  decided_at: 2026-08-21T10:00:00Z
  evidence:
    - ticket-123
  notes: reviewed
"""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "approval.yml"
            path.write_text(approved, encoding="utf-8")

            result = self.run_validator(path)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("requires approval.owner", result.stdout)

    def test_rejected_record_requires_matching_decision(self) -> None:
        rejected = """schema_version: 1
approval:
  status: rejected
  owner: Product Owner
  scope:
    - apple
  decision: approved
  decided_at: 2026-08-21T10:00:00Z
  evidence:
    - ticket-123
  notes: rejected for test
"""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "approval.yml"
            path.write_text(rejected, encoding="utf-8")

            result = self.run_validator(path)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("decision must match", result.stdout)

    def test_approved_record_accepts_inline_lists(self) -> None:
        approved = """schema_version: 1
approval:
  status: approved
  owner: Product Owner
  scope: [apple, google-play]
  decision: approved
  decided_at: 2026-08-21T10:00:00Z
  evidence: [ticket-123]
  notes: reviewed
"""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "approval.yml"
            path.write_text(approved, encoding="utf-8")

            result = self.run_validator(path)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
