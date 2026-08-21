from pathlib import Path
import json
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/generate_review_handoff.py"
DEMO = ROOT / "examples/demo-store-assets"
DEMO_ASSIGNMENT = DEMO / "review-assignment.yml"


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
        self.assertIn("## Reviewer assignment", result.stdout)
        self.assertIn("product-claims, metadata, visual-assets", result.stdout)
        self.assertIn("evidence", result.stdout)
        self.assertIn("No previous reviewer assignment baseline supplied.", result.stdout)
        self.assertIn("### Adapter coverage", result.stdout)
        self.assertIn("Status: `not-checked`", result.stdout)
        self.assertIn("Reviewer assignment is pending", result.stdout)
        self.assertIn("publish_status` is permanently `not-run`", result.stdout)

    def test_selected_adapters_report_coverage(self) -> None:
        result = self.run_script(
            "--package-root", str(DEMO),
            "--adapter-file", str(ROOT / "skills/release-check/references/review-adapters.yml"),
            "--adapter", "policy-review",
            "--adapter", "accessibility-review",
            "--adapter", "privacy-review",
            "--format", "markdown",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("policy-review | covered | product-owner (pending)", result.stdout)

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

    def test_previous_assignment_reports_reviewer_field_changes(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            current = root / "current"
            previous = root / "previous"
            current.mkdir()
            previous.mkdir()
            manifest = "schema_version: 1\nassets:\n  - path: icon.png\n    status: review\n    kind: app-icon\n"
            (current / "manifest.yml").write_text(manifest, encoding="utf-8")
            (previous / "manifest.yml").write_text(manifest, encoding="utf-8")
            current_assignment = DEMO_ASSIGNMENT.read_text(encoding="utf-8")
            previous_assignment = current_assignment.replace(
                "  status: pending\n  owner:",
                "  status: in_review\n  owner:",
                1,
            ).replace(
                "      status: pending\n      scope: [product-claims, metadata, visual-assets]",
                "      status: in_review\n      scope: [product-claims, metadata, visual-assets]",
                1,
            ).replace('      assigned_to: ""', "      assigned_to: Alice", 1)
            (current / "review-assignment.yml").write_text(current_assignment, encoding="utf-8")
            (previous / "review-assignment.yml").write_text(previous_assignment, encoding="utf-8")

            result = self.run_script(
                "--package-root", str(current),
                "--previous-package-root", str(previous),
                "--format", "json",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads(result.stdout)
            assignment_diff = summary["review_assignment_diff"]
            self.assertEqual(assignment_diff["status"], "compared")
            changed_fields = {
                item["field"] for item in assignment_diff["changes"]
                if item["reviewer"] == "product-owner"
            }
            self.assertEqual(changed_fields, {"status", "assigned_to"})

    def test_missing_adapter_coverage_is_visible(self) -> None:
        with TemporaryDirectory() as directory:
            package = Path(directory) / "package"
            package.mkdir()
            (package / "manifest.yml").write_text(
                "schema_version: 1\nassets:\n  - path: icon.png\n    status: review\n    kind: app-icon\n",
                encoding="utf-8",
            )
            assignment = DEMO_ASSIGNMENT.read_text(encoding="utf-8").replace(
                "coverage: [accessibility-review]",
                "coverage: [locale-review]",
                1,
            )
            (package / "review-assignment.yml").write_text(assignment, encoding="utf-8")

            result = self.run_script(
                "--package-root", str(package),
                "--adapter-file", str(ROOT / "skills/release-check/references/review-adapters.yml"),
                "--adapter", "policy-review",
                "--adapter", "accessibility-review",
                "--adapter", "privacy-review",
                "--format", "json",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads(result.stdout)
            coverage = summary["review_assignment_coverage"]
            self.assertEqual(coverage["status"], "missing")
            self.assertIn("accessibility-review", coverage["details"])
            self.assertTrue(any("coverage is incomplete" in warning for warning in summary["warnings"]))


if __name__ == "__main__":
    unittest.main()
