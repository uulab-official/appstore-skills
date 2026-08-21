from pathlib import Path
import struct
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
import zlib


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "prepare_release_handoff.py"


def png_bytes(width: int, height: int) -> bytes:
    signature = b"\x89PNG\r\n\x1a\n"

    def chunk(kind: bytes, payload: bytes) -> bytes:
        body = kind + payload
        return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body))

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return signature + chunk(b"IHDR", ihdr) + chunk(b"IEND", b"")


def create_output(root: Path, with_evidence: bool, with_capture: bool) -> None:
    (root / "brand-context.yml").write_text("schema_version: 1\n", encoding="utf-8")
    (root / "manifest.yml").write_text("schema_version: 1\n", encoding="utf-8")
    (root / "QA.md").write_text("# QA\n", encoding="utf-8")
    (root / "release-report.md").write_text("# Report\n", encoding="utf-8")
    if with_evidence:
        (root / "evidence").mkdir()
        (root / "evidence" / "build.yml").write_text(
            """schema_version: 1
revision: test-revision
artifact: ExampleApp-1.0.0.ipa
platform: apple
inspected_at: 2026-08-21T10:00:00Z
source: test fixture artifact
""",
            encoding="utf-8",
        )
    if with_capture:
        (root / "screenshots" / "source").mkdir(parents=True)
        (root / "screenshots" / "source" / "home.png").write_bytes(png_bytes(1170, 2532))
        (root / "evidence" / "captures.yml").write_text(
            """schema_version: 1
captures:
  - path: screenshots/source/home.png
    platform: apple
    device_family: iphone
    locale: en-US
    captured_at: 2026-08-21T10:05:00Z
    provenance: ios-simulator
""",
            encoding="utf-8",
        )


def init_git_project(project: Path) -> str:
    (project / "app.txt").write_text("fixture\n", encoding="utf-8")
    subprocess.run(
        ["git", "-C", str(project), "-c", "init.defaultBranch=main", "init", "-q"],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "-C", str(project), "add", "app.txt"],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            "git", "-C", str(project),
            "-c", "user.name=Fixture", "-c", "user.email=fixture@example.com",
            "commit", "-qm", "fixture",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    result = subprocess.run(
        ["git", "-C", str(project), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


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
            self.assertIn("evidence_max_age_days: null", result.stdout)
            self.assertIn("platforms: []", result.stdout)
            self.assertIn("locales: []", result.stdout)
            self.assertIn("device_families: []", result.stdout)
            self.assertIn("require_current_revision: false", result.stdout)
            self.assertIn("require_scope_coverage: false", result.stdout)
            self.assertEqual(result.stdout.count('provider_mode: "opt-in-read-only"'), 1)
            self.assertEqual(result.stdout.count("provider_file:"), 1)

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
                "--provider", "build-record",
                "--provider", "simulator-source-captures",
                "--approval-file", str(approval),
                "--format", "summary",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Release handoff: ready_for_handoff", result.stdout)
            self.assertIn("pass: human-approval", result.stdout)

    def test_selected_providers_replace_legacy_evidence_checks(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory) / "app"
            output = project / "store-assets"
            project.mkdir()
            output.mkdir()
            (project / "package.json").write_text("{}\n", encoding="utf-8")
            create_output(output, with_evidence=True, with_capture=True)

            result = self.run_script(
                "--project-root", str(project),
                "--output-root", str(output),
                "--provider", "build-record",
                "--provider", "simulator-source-captures",
                "--format", "summary",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("pass: build-identity — provider build-record", result.stdout)
            self.assertIn("pass: simulator-captures — provider simulator-source-captures", result.stdout)

    def test_project_owned_provider_registry_is_reported(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory) / "app"
            output = project / "store-assets"
            project.mkdir()
            output.mkdir()
            (project / "package.json").write_text("{}\n", encoding="utf-8")
            create_output(output, with_evidence=True, with_capture=True)
            registry = project / "evidence-providers.yml"
            source = (ROOT / "skills/app-store-assets/references/evidence-providers.yml").read_text(
                encoding="utf-8"
            )
            registry.write_text(
                source.replace("  owner: repository\n", "  owner: project\n", 1),
                encoding="utf-8",
            )

            result = self.run_script(
                "--project-root", str(project),
                "--output-root", str(output),
                "--provider-file", str(registry),
                "--provider", "build-record",
                "--provider", "simulator-source-captures",
                "--format", "yaml",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('provider_registry_owner: "project"', result.stdout)
            self.assertIn('provider_selection: "explicit"', result.stdout)

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

    def test_evidence_age_gate_is_forwarded_to_selected_providers(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory) / "app"
            output = project / "store-assets"
            project.mkdir()
            output.mkdir()
            (project / "package.json").write_text("{}\n", encoding="utf-8")
            create_output(output, with_evidence=True, with_capture=True)
            build = output / "evidence" / "build.yml"
            build.write_text(
                build.read_text(encoding="utf-8").replace(
                    "2026-08-21T10:00:00Z", "2000-01-01T00:00:00Z"
                ),
                encoding="utf-8",
            )

            result = self.run_script(
                "--project-root", str(project),
                "--output-root", str(output),
                "--provider", "build-record",
                "--max-evidence-age-days", "30",
                "--format", "summary",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Release handoff: blocked", result.stdout)
            self.assertIn("Evidence max age: 30 days", result.stdout)
            self.assertIn("build evidence inspected_at is older than max age (30 days)", result.stdout)

    def test_negative_evidence_age_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory) / "app"
            output = project / "store-assets"
            project.mkdir()
            output.mkdir()

            result = self.run_script(
                "--project-root", str(project),
                "--output-root", str(output),
                "--max-evidence-age-days", "-1",
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("must be zero or greater", result.stderr)

    def test_current_revision_binding_is_forwarded_to_handoff(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory) / "app"
            output = project / "store-assets"
            project.mkdir()
            output.mkdir()
            (project / "package.json").write_text("{}\n", encoding="utf-8")
            create_output(output, with_evidence=True, with_capture=True)
            revision = init_git_project(project)
            build = output / "evidence" / "build.yml"
            build.write_text(
                build.read_text(encoding="utf-8").replace("test-revision", revision[:12]),
                encoding="utf-8",
            )

            result = self.run_script(
                "--project-root", str(project),
                "--output-root", str(output),
                "--provider", "build-record",
                "--require-current-revision",
                "--format", "summary",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Release handoff: pending_approval", result.stdout)
            self.assertIn("Revision binding: required", result.stdout)
            self.assertIn("pass: build-identity — provider build-record", result.stdout)

            build.write_text(
                build.read_text(encoding="utf-8").replace(revision[:12], "deadbeef"),
                encoding="utf-8",
            )
            mismatch = self.run_script(
                "--project-root", str(project),
                "--output-root", str(output),
                "--provider", "build-record",
                "--require-current-revision",
                "--format", "summary",
            )

            self.assertEqual(mismatch.returncode, 0, mismatch.stderr)
            self.assertIn("Release handoff: blocked", mismatch.stdout)
            self.assertIn("revision does not match current project revision", mismatch.stdout)
            self.assertIn("Regenerate evidence/build.yml", mismatch.stdout)

    def test_platform_scope_is_forwarded_to_provider_checks(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory) / "app"
            output = project / "store-assets"
            project.mkdir()
            output.mkdir()
            (project / "package.json").write_text("{}\n", encoding="utf-8")
            create_output(output, with_evidence=True, with_capture=True)

            mismatch = self.run_script(
                "--project-root", str(project),
                "--output-root", str(output),
                "--platform", "google-play",
                "--provider", "build-record",
                "--format", "summary",
            )

            self.assertEqual(mismatch.returncode, 0, mismatch.stderr)
            self.assertIn("Release handoff: blocked", mismatch.stdout)
            self.assertIn("platform does not match requested platforms", mismatch.stdout)
            self.assertIn("Record build evidence for a requested target platform", mismatch.stdout)

            matching = self.run_script(
                "--project-root", str(project),
                "--output-root", str(output),
                "--platform", "apple",
                "--provider", "build-record",
                "--format", "summary",
            )

            self.assertEqual(matching.returncode, 0, matching.stderr)
            self.assertIn("Release handoff: pending_approval", matching.stdout)
            self.assertIn("pass: build-identity — provider build-record", matching.stdout)

    def test_platform_scope_blocks_mismatched_source_capture(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory) / "app"
            output = project / "store-assets"
            project.mkdir()
            output.mkdir()
            (project / "package.json").write_text("{}\n", encoding="utf-8")
            create_output(output, with_evidence=True, with_capture=True)
            build = output / "evidence" / "build.yml"
            build.write_text(
                build.read_text(encoding="utf-8").replace("platform: apple", "platform: google-play"),
                encoding="utf-8",
            )

            result = self.run_script(
                "--project-root", str(project),
                "--output-root", str(output),
                "--platform", "google-play",
                "--provider", "build-record",
                "--provider", "simulator-source-captures",
                "--format", "summary",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Release handoff: blocked", result.stdout)
            self.assertIn("capture 1 platform does not match requested platforms", result.stdout)
            self.assertIn("Capture source images for a requested target platform", result.stdout)

    def test_locale_scope_is_forwarded_to_source_capture_checks(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory) / "app"
            output = project / "store-assets"
            project.mkdir()
            output.mkdir()
            (project / "package.json").write_text("{}\n", encoding="utf-8")
            create_output(output, with_evidence=True, with_capture=True)

            mismatch = self.run_script(
                "--project-root", str(project),
                "--output-root", str(output),
                "--locale", "ko-KR",
                "--provider", "simulator-source-captures",
                "--format", "summary",
            )

            self.assertEqual(mismatch.returncode, 0, mismatch.stderr)
            self.assertIn("Release handoff: blocked", mismatch.stdout)
            self.assertIn("Locales: ko-KR", mismatch.stdout)
            self.assertIn("capture 1 locale does not match requested locales", mismatch.stdout)
            self.assertIn("Capture source images for a requested locale", mismatch.stdout)

            matching = self.run_script(
                "--project-root", str(project),
                "--output-root", str(output),
                "--locale", "en_US",
                "--provider", "simulator-source-captures",
                "--format", "summary",
            )

            self.assertEqual(matching.returncode, 0, matching.stderr)
            self.assertIn("Release handoff: pending_approval", matching.stdout)
            self.assertIn("pass: simulator-captures — provider simulator-source-captures", matching.stdout)

    def test_device_family_scope_is_forwarded_to_source_capture_checks(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory) / "app"
            output = project / "store-assets"
            project.mkdir()
            output.mkdir()
            (project / "package.json").write_text("{}\n", encoding="utf-8")
            create_output(output, with_evidence=True, with_capture=True)

            mismatch = self.run_script(
                "--project-root", str(project),
                "--output-root", str(output),
                "--device-family", "ipad",
                "--provider", "simulator-source-captures",
                "--format", "summary",
            )

            self.assertEqual(mismatch.returncode, 0, mismatch.stderr)
            self.assertIn("Release handoff: blocked", mismatch.stdout)
            self.assertIn("Device families: ipad", mismatch.stdout)
            self.assertIn("capture 1 device family does not match requested device families", mismatch.stdout)
            self.assertIn("Capture source images for a requested device family", mismatch.stdout)

            matching = self.run_script(
                "--project-root", str(project),
                "--output-root", str(output),
                "--device-family", "ios-phone",
                "--provider", "simulator-source-captures",
                "--format", "summary",
            )

            self.assertEqual(matching.returncode, 0, matching.stderr)
            self.assertIn("Release handoff: pending_approval", matching.stdout)
            self.assertIn("pass: simulator-captures — provider simulator-source-captures", matching.stdout)

    def test_scope_coverage_is_forwarded_to_source_capture_checks(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory) / "app"
            output = project / "store-assets"
            project.mkdir()
            output.mkdir()
            (project / "package.json").write_text("{}\n", encoding="utf-8")
            create_output(output, with_evidence=True, with_capture=True)

            result = self.run_script(
                "--project-root", str(project),
                "--output-root", str(output),
                "--locale", "en-US",
                "--locale", "ko-KR",
                "--require-scope-coverage",
                "--provider", "simulator-source-captures",
                "--format", "summary",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Release handoff: blocked", result.stdout)
            self.assertIn("Scope coverage: required", result.stdout)
            self.assertIn("source capture scope coverage is incomplete", result.stdout)
            self.assertIn("Add source captures for every requested platform, locale, and device-family scope", result.stdout)


if __name__ == "__main__":
    unittest.main()
