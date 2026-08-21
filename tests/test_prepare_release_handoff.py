from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "prepare_release_handoff.py"


def create_output(root: Path, with_evidence: bool, with_capture: bool) -> None:
    (root / "brand-context.yml").write_text("schema_version: 1\n", encoding="utf-8")
    (root / "manifest.yml").write_text("schema_version: 1\n", encoding="utf-8")
    (root / "QA.md").write_text("# QA\n", encoding="utf-8")
    (root / "release-report.md").write_text("# Report\n", encoding="utf-8")
    if with_evidence:
        (root / "evidence").mkdir()
        (root / "evidence" / "build.yml").write_text("revision: test\n", encoding="utf-8")
    if with_capture:
        (root / "screenshots" / "source").mkdir(parents=True)
        (root / "screenshots" / "source" / "home.png").write_bytes(b"capture")


def create_approval(root: Path, status: str = "approved") -> Path:
    path = root / "release-approval.yml"
    if status == "approved":
        path.write_text(
            """schema_version: 1
approval:
  status: approved
  owner: Product Owner
  scope:
    - apple
    - google-play
  decision: approved
  decided_at: 2026-08-21T10:00:00Z
  evidence:
    - review-ticket-123
  notes: approved for handoff test
""",
            encoding="utf-8",
        )
    else:
        path.write_text(
            """schema_version: 1
approval:
  status: pending
  owner: ""
  scope:
    - apple
  decision: ""
  decided_at: ""
  evidence: []
  notes: waiting
""",
            encoding="utf-8",
        )
    return path


class PrepareReleaseHandoffTests(unittest.TestCase):
    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_missing_build_and_capture_is_blocked_without_failing(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory) / "app"
            output = project / "store-assets"
            project.mkdir()
            output.mkdir()
            (project / "package.json").write_text("{}\n", encoding="utf-8")
            create_output(output, with_evidence=False, with_capture=False)

            result = self.run_script(
                "--project-root", str(project), "--output-root", str(output), "--format", "summary"
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Release handoff: blocked", result.stdout)
            self.assertIn("Publish: not-run", result.stdout)
            self.assertIn("simulator-captures", result.stdout)

    def test_complete_evidence_waits_for_approval(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory) / "app"
            output = project / "store-assets"
            project.mkdir()
            output.mkdir()
            (project / "package.json").write_text("{}\n", encoding="utf-8")
            create_output(output, with_evidence=True, with_capture=True)

            result = self.run_script(
                "--project-root", str(project), "--output-root", str(output), "--format", "yaml"
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('status: "pending_approval"', result.stdout)
            self.assertIn('publish_status: "not-run"', result.stdout)

    def test_approved_evidence_is_ready_for_handoff(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory) / "app"
            output = project / "store-assets"
            project.mkdir()
            output.mkdir()
            (project / "package.json").write_text("{}\n", encoding="utf-8")
            create_output(output, with_evidence=True, with_capture=True)
            approval = create_approval(output)

            result = self.run_script(
                "--project-root", str(project),
                "--output-root", str(output),
                "--approval-file", str(approval),
                "--format", "summary",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Release handoff: ready_for_handoff", result.stdout)
            self.assertIn("pass: human-approval", result.stdout)

    def test_fail_on_pending_approval_is_opt_in(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory) / "app"
            output = project / "store-assets"
            project.mkdir()
            output.mkdir()
            (project / "package.json").write_text("{}\n", encoding="utf-8")
            create_output(output, with_evidence=True, with_capture=True)
            approval = create_approval(output, status="pending")

            result = self.run_script(
                "--project-root", str(project),
                "--output-root", str(output),
                "--approval-file", str(approval),
                "--fail-on-pending-approval",
            )

            self.assertEqual(result.returncode, 1)

    def test_fail_on_blocked_is_opt_in(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory) / "app"
            output = project / "store-assets"
            project.mkdir()
            output.mkdir()
            create_output(output, with_evidence=False, with_capture=False)

            result = self.run_script(
                "--project-root", str(project), "--output-root", str(output), "--fail-on-blocked"
            )

            self.assertEqual(result.returncode, 1)


if __name__ == "__main__":
    unittest.main()
