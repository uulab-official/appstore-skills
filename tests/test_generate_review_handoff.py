from pathlib import Path
import json
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/generate_review_handoff.py"
DEMO = ROOT / "examples/demo-store-assets"


class GenerateReviewHandoffTests(unittest.TestCase):
    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_demo_summary_is_blocked_and_diff_friendly(self) -> None:
        result = self.run_script("--package-root", str(DEMO), "--format", "markdown")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("review_status: blocked", result.stdout)
        self.assertIn("Baseline: `not-supplied`", result.stdout)
        self.assertIn("publish_status` is permanently `not-run`", result.stdout)

    def test_previous_manifest_reports_added_removed_and_changed(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            current = root / "current"
            previous = root / "previous"
            current.mkdir()
            previous.mkdir()
            (current / "manifest.yml").write_text(
                "schema_version: 1\nassets:\n"
                "  - path: icon.png\n"
                "    status: review\n"
                "    kind: app-icon\n"
                "  - path: new.png\n"
                "    status: review\n"
                "    kind: screenshot\n",
                encoding="utf-8",
            )
            (previous / "manifest.yml").write_text(
                "schema_version: 1\nassets:\n"
                "  - path: icon.png\n"
                "    status: draft\n"
                "    kind: app-icon\n"
                "  - path: removed.png\n"
                "    status: review\n",
                encoding="utf-8",
            )
            (current / "new.png").write_text("x", encoding="utf-8")
            (current / "icon.png").write_text("x", encoding="utf-8")
            (previous / "removed.png").write_text("x", encoding="utf-8")
            (previous / "icon.png").write_text("x", encoding="utf-8")

            result = self.run_script(
                "--package-root", str(current),
                "--previous-package-root", str(previous),
                "--format", "json",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            changes = json.loads(result.stdout)["changes"]
            self.assertEqual({item["change"] for item in changes}, {"added", "changed", "removed"})

    def test_output_refuses_overwrite(self) -> None:
        with TemporaryDirectory() as directory:
            output = Path(directory) / "review-handoff.md"
            output.write_text("existing\n", encoding="utf-8")

            result = self.run_script("--package-root", str(DEMO), "--output", str(output))

            self.assertEqual(result.returncode, 2)
            self.assertIn("Refusing to overwrite", result.stderr)


if __name__ == "__main__":
    unittest.main()
