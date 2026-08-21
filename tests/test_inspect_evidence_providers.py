from pathlib import Path
import struct
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
import zlib


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "inspect_evidence_providers.py"
PROVIDER_FILE = ROOT / "skills/app-store-assets/references/evidence-providers.yml"


def png_bytes(width: int, height: int) -> bytes:
    signature = b"\x89PNG\r\n\x1a\n"

    def chunk(kind: bytes, payload: bytes) -> bytes:
        body = kind + payload
        return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body))

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return signature + chunk(b"IHDR", ihdr) + chunk(b"IEND", b"")


def create_evidence(root: Path) -> None:
    evidence = root / "evidence"
    source = root / "screenshots" / "source"
    evidence.mkdir()
    source.mkdir(parents=True)
    (evidence / "build.yml").write_text(
        """schema_version: 1
revision: abc1234
artifact: ExampleApp-1.2.3.ipa
platform: ios
inspected_at: 2026-08-21T10:00:00Z
source: supplied release artifact
""",
        encoding="utf-8",
    )
    (source / "home.png").write_bytes(png_bytes(1170, 2532))
    (evidence / "captures.yml").write_text(
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


class InspectEvidenceProvidersTests(unittest.TestCase):
    def run_inspector(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_complete_evidence_is_read_without_side_effects(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory) / "app"
            output = project / "store-assets"
            project.mkdir()
            output.mkdir()
            create_evidence(output)

            result = self.run_inspector(
                "--provider-file", str(PROVIDER_FILE),
                "--project-root", str(project),
                "--output-root", str(output),
                "--provider", "build-record",
                "--provider", "simulator-source-captures",
                "--format", "summary",
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("pass: build-record", result.stdout)
            self.assertIn("pass: simulator-source-captures", result.stdout)

    def test_missing_capture_manifest_is_informational_by_default(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory) / "app"
            output = project / "store-assets"
            project.mkdir()
            output.mkdir()

            result = self.run_inspector(
                "--provider-file", str(PROVIDER_FILE),
                "--project-root", str(project),
                "--output-root", str(output),
                "--provider", "simulator-source-captures",
                "--format", "summary",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("blocked: simulator-source-captures", result.stdout)

    def test_fail_on_blocked_is_opt_in(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory) / "app"
            output = project / "store-assets"
            project.mkdir()
            output.mkdir()

            result = self.run_inspector(
                "--provider-file", str(PROVIDER_FILE),
                "--project-root", str(project),
                "--output-root", str(output),
                "--provider", "build-record",
                "--fail-on-blocked",
            )

            self.assertEqual(result.returncode, 1)

    def test_stale_build_evidence_can_gate(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory) / "app"
            output = project / "store-assets"
            project.mkdir()
            output.mkdir()
            create_evidence(output)
            build = output / "evidence" / "build.yml"
            build.write_text(
                build.read_text(encoding="utf-8").replace(
                    "2026-08-21T10:00:00Z", "2000-01-01T00:00:00Z"
                ),
                encoding="utf-8",
            )

            result = self.run_inspector(
                "--provider-file", str(PROVIDER_FILE),
                "--project-root", str(project),
                "--output-root", str(output),
                "--provider", "build-record",
                "--max-age-days", "30",
                "--fail-on-blocked",
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("older than max age (30 days)", result.stdout)

    def test_future_capture_evidence_can_gate(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory) / "app"
            output = project / "store-assets"
            project.mkdir()
            output.mkdir()
            create_evidence(output)
            captures = output / "evidence" / "captures.yml"
            captures.write_text(
                captures.read_text(encoding="utf-8").replace(
                    "2026-08-21T10:05:00Z", "2999-01-01T00:00:00Z"
                ),
                encoding="utf-8",
            )

            result = self.run_inspector(
                "--provider-file", str(PROVIDER_FILE),
                "--project-root", str(project),
                "--output-root", str(output),
                "--provider", "simulator-source-captures",
                "--max-age-days", "30",
                "--fail-on-blocked",
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("cannot be in the future", result.stdout)

    def test_negative_max_age_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory) / "app"
            output = project / "store-assets"
            project.mkdir()
            output.mkdir()

            result = self.run_inspector(
                "--provider-file", str(PROVIDER_FILE),
                "--project-root", str(project),
                "--output-root", str(output),
                "--provider", "build-record",
                "--max-age-days", "-1",
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("must be zero or greater", result.stderr)

    def test_build_revision_can_match_current_git_revision(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory) / "app"
            output = project / "store-assets"
            project.mkdir()
            output.mkdir()
            revision = init_git_project(project)
            create_evidence(output)
            build = output / "evidence" / "build.yml"
            build.write_text(
                build.read_text(encoding="utf-8").replace("abc1234", revision[:12]),
                encoding="utf-8",
            )

            result = self.run_inspector(
                "--provider-file", str(PROVIDER_FILE),
                "--project-root", str(project),
                "--output-root", str(output),
                "--provider", "build-record",
                "--require-current-revision",
                "--fail-on-blocked",
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("pass: build-record", result.stdout)

            build.write_text(
                build.read_text(encoding="utf-8").replace(revision[:12], "deadbeef"),
                encoding="utf-8",
            )
            mismatch = self.run_inspector(
                "--provider-file", str(PROVIDER_FILE),
                "--project-root", str(project),
                "--output-root", str(output),
                "--provider", "build-record",
                "--require-current-revision",
                "--fail-on-blocked",
            )

            self.assertEqual(mismatch.returncode, 1)
            self.assertIn("revision does not match current project revision", mismatch.stdout)

    def test_revision_binding_blocks_without_git_project(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory) / "app"
            output = project / "store-assets"
            project.mkdir()
            output.mkdir()
            create_evidence(output)

            result = self.run_inspector(
                "--provider-file", str(PROVIDER_FILE),
                "--project-root", str(project),
                "--output-root", str(output),
                "--provider", "build-record",
                "--require-current-revision",
                "--fail-on-blocked",
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("current project revision is unavailable", result.stdout)

    def test_build_platform_can_be_checked_against_requested_scope(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory) / "app"
            output = project / "store-assets"
            project.mkdir()
            output.mkdir()
            create_evidence(output)

            matching = self.run_inspector(
                "--provider-file", str(PROVIDER_FILE),
                "--project-root", str(project),
                "--output-root", str(output),
                "--provider", "build-record",
                "--platform", "apple",
                "--fail-on-blocked",
            )

            self.assertEqual(matching.returncode, 0, matching.stdout + matching.stderr)

            mismatch = self.run_inspector(
                "--provider-file", str(PROVIDER_FILE),
                "--project-root", str(project),
                "--output-root", str(output),
                "--provider", "build-record",
                "--platform", "google-play",
                "--fail-on-blocked",
            )

            self.assertEqual(mismatch.returncode, 1)
            self.assertIn("platform does not match requested platforms", mismatch.stdout)

    def test_capture_platform_can_be_checked_against_requested_scope(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory) / "app"
            output = project / "store-assets"
            project.mkdir()
            output.mkdir()
            create_evidence(output)

            matching = self.run_inspector(
                "--provider-file", str(PROVIDER_FILE),
                "--project-root", str(project),
                "--output-root", str(output),
                "--provider", "simulator-source-captures",
                "--platform", "apple",
                "--fail-on-blocked",
            )

            self.assertEqual(matching.returncode, 0, matching.stdout + matching.stderr)

            mismatch = self.run_inspector(
                "--provider-file", str(PROVIDER_FILE),
                "--project-root", str(project),
                "--output-root", str(output),
                "--provider", "simulator-source-captures",
                "--platform", "google-play",
                "--fail-on-blocked",
            )

            self.assertEqual(mismatch.returncode, 1)
            self.assertIn("capture 1 platform does not match requested platforms", mismatch.stdout)

    def test_capture_locale_can_be_checked_against_requested_scope(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory) / "app"
            output = project / "store-assets"
            project.mkdir()
            output.mkdir()
            create_evidence(output)

            matching = self.run_inspector(
                "--provider-file", str(PROVIDER_FILE),
                "--project-root", str(project),
                "--output-root", str(output),
                "--provider", "simulator-source-captures",
                "--locale", "en_US",
                "--fail-on-blocked",
            )

            self.assertEqual(matching.returncode, 0, matching.stdout + matching.stderr)

            mismatch = self.run_inspector(
                "--provider-file", str(PROVIDER_FILE),
                "--project-root", str(project),
                "--output-root", str(output),
                "--provider", "simulator-source-captures",
                "--locale", "ko-KR",
                "--fail-on-blocked",
            )

            self.assertEqual(mismatch.returncode, 1)
            self.assertIn("capture 1 locale does not match requested locales", mismatch.stdout)

    def test_capture_device_family_can_be_checked_against_requested_scope(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory) / "app"
            output = project / "store-assets"
            project.mkdir()
            output.mkdir()
            create_evidence(output)

            matching = self.run_inspector(
                "--provider-file", str(PROVIDER_FILE),
                "--project-root", str(project),
                "--output-root", str(output),
                "--provider", "simulator-source-captures",
                "--device-family", "ios-phone",
                "--fail-on-blocked",
            )

            self.assertEqual(matching.returncode, 0, matching.stdout + matching.stderr)

            mismatch = self.run_inspector(
                "--provider-file", str(PROVIDER_FILE),
                "--project-root", str(project),
                "--output-root", str(output),
                "--provider", "simulator-source-captures",
                "--device-family", "ipad",
                "--fail-on-blocked",
            )

            self.assertEqual(mismatch.returncode, 1)
            self.assertIn("capture 1 device family does not match requested device families", mismatch.stdout)

    def test_scope_coverage_can_gate_missing_capture_combinations(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory) / "app"
            output = project / "store-assets"
            project.mkdir()
            output.mkdir()
            create_evidence(output)
            source = output / "screenshots" / "source"
            (source / "google.png").write_bytes((source / "home.png").read_bytes())
            (output / "evidence" / "captures.yml").write_text(
                """schema_version: 1
captures:
  - path: screenshots/source/home.png
    platform: apple
    device_family: iphone
    locale: en-US
    captured_at: 2026-08-21T10:05:00Z
    provenance: ios-simulator
  - path: screenshots/source/google.png
    platform: google-play
    device_family: iphone
    locale: en-US
    captured_at: 2026-08-21T10:06:00Z
    provenance: android-emulator
""",
                encoding="utf-8",
            )

            result = self.run_inspector(
                "--provider-file", str(PROVIDER_FILE),
                "--project-root", str(project),
                "--output-root", str(output),
                "--provider", "simulator-source-captures",
                "--platform", "apple",
                "--platform", "google-play",
                "--locale", "en-US",
                "--locale", "ko-KR",
                "--device-family", "iphone",
                "--require-scope-coverage",
                "--fail-on-blocked",
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("source capture scope coverage is incomplete", result.stdout)
            self.assertIn("platform=apple, locale=ko-KR, device_family=iphone", result.stdout)

    def test_scope_coverage_requires_a_scope_flag(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory) / "app"
            output = project / "store-assets"
            project.mkdir()
            output.mkdir()

            result = self.run_inspector(
                "--provider-file", str(PROVIDER_FILE),
                "--project-root", str(project),
                "--output-root", str(output),
                "--provider", "simulator-source-captures",
                "--require-scope-coverage",
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("requires at least one scope flag", result.stderr)

    def test_duplicate_capture_path_is_blocked(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory) / "app"
            output = project / "store-assets"
            project.mkdir()
            output.mkdir()
            create_evidence(output)
            (output / "evidence" / "captures.yml").write_text(
                (output / "evidence" / "captures.yml").read_text(encoding="utf-8")
                + """  - path: screenshots/source/home.png
    platform: google-play
    device_family: android-phone
    locale: ko-KR
    captured_at: 2026-08-21T10:06:00Z
    provenance: android-emulator
""",
                encoding="utf-8",
            )

            result = self.run_inspector(
                "--provider-file", str(PROVIDER_FILE),
                "--project-root", str(project),
                "--output-root", str(output),
                "--provider", "simulator-source-captures",
                "--platform", "apple",
                "--platform", "google-play",
                "--locale", "en-US",
                "--device-family", "iphone",
                "--require-scope-coverage",
                "--fail-on-blocked",
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("capture 2 path is duplicated: screenshots/source/home.png", result.stdout)

    def test_project_owned_registry_can_be_selected_inside_project_root(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory) / "app"
            output = project / "store-assets"
            project.mkdir()
            output.mkdir()
            create_evidence(output)
            registry = project / "evidence-providers.yml"
            registry.write_text(
                PROVIDER_FILE.read_text(encoding="utf-8").replace(
                    "  owner: repository\n", "  owner: project\n", 1
                ),
                encoding="utf-8",
            )

            result = self.run_inspector(
                "--provider-file", str(registry),
                "--project-root", str(project),
                "--output-root", str(output),
                "--provider", "build-record",
                "--provider", "simulator-source-captures",
                "--fail-on-blocked",
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_project_owned_registry_outside_project_root_is_blocked(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory) / "app"
            output = project / "store-assets"
            project.mkdir()
            output.mkdir()
            create_evidence(output)
            registry = Path(directory) / "evidence-providers.yml"
            registry.write_text(
                PROVIDER_FILE.read_text(encoding="utf-8").replace(
                    "  owner: repository\n", "  owner: project\n", 1
                ),
                encoding="utf-8",
            )

            result = self.run_inspector(
                "--provider-file", str(registry),
                "--project-root", str(project),
                "--output-root", str(output),
                "--provider", "build-record",
                "--fail-on-blocked",
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("project-owned provider registry must be inside the project root", result.stdout)

    def test_provider_symlink_cannot_escape_output_root(self) -> None:
        with TemporaryDirectory() as directory:
            project = Path(directory) / "app"
            output = project / "store-assets"
            outside = Path(directory) / "outside"
            project.mkdir()
            output.mkdir()
            outside.mkdir()
            create_evidence(output)
            (output / "evidence" / "link").symlink_to(outside, target_is_directory=True)
            registry = project / "evidence-providers.yml"
            registry.write_text(
                PROVIDER_FILE.read_text(encoding="utf-8")
                .replace("  owner: repository\n", "  owner: project\n", 1)
                .replace(
                    "    evidence_path: evidence/build.yml\n",
                    "    evidence_path: evidence/link/build.yml\n",
                    1,
                ),
                encoding="utf-8",
            )

            result = self.run_inspector(
                "--provider-file", str(registry),
                "--project-root", str(project),
                "--output-root", str(output),
                "--provider", "build-record",
                "--fail-on-blocked",
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("provider build-record evidence_path must stay inside the output root", result.stdout)


if __name__ == "__main__":
    unittest.main()
