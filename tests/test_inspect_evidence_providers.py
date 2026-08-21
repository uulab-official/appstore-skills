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


if __name__ == "__main__":
    unittest.main()
