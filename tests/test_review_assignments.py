from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/validate_review_assignments.py"
REGISTRY = ROOT / "skills/release-check/references/review-adapters.yml"
DEMO = ROOT / "examples/demo-store-assets/review-assignment.yml"


class ReviewAssignmentTests(unittest.TestCase):
    def run_validator(self, *paths: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *(str(path) for path in paths)],
            check=False,
            capture_output=True,
            text=True,
        )

    def run_validator_with_registry(self, path: Path, *adapters: str) -> subprocess.CompletedProcess[str]:
        command = [
            sys.executable,
            str(SCRIPT),
            str(path),
            "--adapter-file",
            str(REGISTRY),
        ]
        for adapter in adapters:
            command.extend(["--adapter", adapter])
        return subprocess.run(command, check=False, capture_output=True, text=True)

    def test_demo_assignment_passes_and_stays_pending(self) -> None:
        result = self.run_validator(DEMO)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_selected_registry_adapters_require_coverage(self) -> None:
        result = self.run_validator_with_registry(
            DEMO,
            "policy-review",
            "accessibility-review",
            "privacy-review",
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_unknown_coverage_id_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "review-assignment.yml"
            path.write_text(
                DEMO.read_text(encoding="utf-8").replace(
                    "coverage: [policy-review]",
                    "coverage: [legal-review]",
                    1,
                ),
                encoding="utf-8",
            )

            result = self.run_validator_with_registry(path, "policy-review")

            self.assertEqual(result.returncode, 1)
            self.assertIn("coverage references unknown review adapter: legal-review", result.stdout)

    def test_selected_adapter_without_coverage_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "review-assignment.yml"
            path.write_text(
                DEMO.read_text(encoding="utf-8").replace(
                    "coverage: [accessibility-review]",
                    "coverage: [locale-review]",
                    1,
                ),
                encoding="utf-8",
            )

            result = self.run_validator_with_registry(
                path,
                "policy-review",
                "accessibility-review",
                "privacy-review",
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("selected review adapter has no reviewer coverage: accessibility-review", result.stdout)

    def test_declared_status_must_match_reviewer_states(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "review-assignment.yml"
            path.write_text(
                DEMO.read_text(encoding="utf-8").replace(
                    "  status: pending\n  owner:",
                    "  status: approved\n  owner:",
                    1,
                ),
                encoding="utf-8",
            )

            result = self.run_validator(path)

            self.assertEqual(result.returncode, 1)
            self.assertIn("does not match reviewer-derived status pending", result.stdout)

    def test_required_not_applicable_reviewers_can_complete_assignment(self) -> None:
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
      status: not_applicable
      scope: [claims]
      coverage: [policy-review]
      assigned_to: Product owner
      assigned_at: 2026-08-21T10:00:00Z
      decision: not_applicable
      decided_at: 2026-08-21T11:00:00Z
      evidence: [ticket-1]
      notes: outside scope
  history:
    - at: 2026-08-21T10:00:00Z
      action: decided
      actor: Product owner
      reviewer: owner
      note: scope marked not applicable
""",
                encoding="utf-8",
            )

            result = self.run_validator(path)

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
      coverage: [policy-review]
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
      coverage: [policy-review]
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
