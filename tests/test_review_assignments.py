from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/validate_review_assignments.py"
DEMO = ROOT / "examples/demo-store-assets/review-assignment.yml"


class ReviewAssignmentTests(unittest.TestCase):
    def run_validator(self, *paths: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *(str(path) for path in paths)],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_demo_assignment_passes_and_stays_pending(self) -> None:
        result = self.run_validator(DEMO)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_approved_reviewer_requires_decision_evidence(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "review-assignment.yml"
            path.write_text(
                """schema_version: 1
review_assignment:
  id: example
  package: example
  status: approved
  owner: Product owner
  reviewers:
    - id: owner
      role: product
      required: true
      status: approved
      scope: [claims]
      assigned_to: Product owner
      assigned_at: 2026-08-21T10:00:00Z
      decision: approved
      decided_at: 2026-08-21T11:00:00Z
      evidence: []
      notes: decision recorded
  history:
    - at: 2026-08-21T10:00:00Z
      action: assigned
      actor: Product owner
      reviewer: owner
      note: reviewer assigned
""",
                encoding="utf-8",
            )

            result = self.run_validator(path)

            self.assertEqual(result.returncode, 1)
            self.assertIn("terminal reviewer decision requires evidence", result.stdout)

    def test_reviewer_scope_is_required_even_before_assignment(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "review-assignment.yml"
            path.write_text(
                """schema_version: 1
review_assignment:
  id: example
  package: example
  status: pending
  owner: ""
  reviewers:
    - id: owner
      role: product
      required: true
      status: pending
      scope: []
      assigned_to: ""
      assigned_at: ""
      decision: pending
      decided_at: ""
      evidence: []
      notes: waiting
  history:
    - at: 2026-08-21T10:00:00Z
      action: created
      actor: owner
      reviewer: owner
      note: created
""",
                encoding="utf-8",
            )

            result = self.run_validator(path)

            self.assertEqual(result.returncode, 1)
            self.assertIn("scope must be a non-empty list", result.stdout)

    def test_history_must_be_chronological(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "review-assignment.yml"
            path.write_text(
                """schema_version: 1
review_assignment:
  id: example
  package: example
  status: pending
  owner: ""
  reviewers:
    - id: owner
      role: product
      required: true
      status: pending
      scope: [claims]
      assigned_to: ""
      assigned_at: ""
      decision: pending
      decided_at: ""
      evidence: []
      notes: waiting
  history:
    - at: 2026-08-21T11:00:00Z
      action: assigned
      actor: owner
      reviewer: owner
      note: assigned
    - at: 2026-08-21T10:00:00Z
      action: created
      actor: owner
      reviewer: owner
      note: created
""",
                encoding="utf-8",
            )

            result = self.run_validator(path)

            self.assertEqual(result.returncode, 1)
            self.assertIn("history timestamps must be chronological", result.stdout)


if __name__ == "__main__":
    unittest.main()
