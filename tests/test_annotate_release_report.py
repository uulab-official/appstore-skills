from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "annotate_release_report.py"
REPORT = ROOT / "examples/demo-store-assets/release-report.md"


class AnnotateReleaseReportTests(unittest.TestCase):
    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_demo_report_emits_annotations(self) -> None:
        result = self.run_script(str(REPORT), "--github-actions")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Release report status: blocked", result.stdout)
        self.assertIn("::error file=", result.stdout)
        self.assertIn("::warning file=", result.stdout)

    def test_fail_on_blockers_is_opt_in(self) -> None:
        result = self.run_script(str(REPORT), "--fail-on-blockers")

        self.assertEqual(result.returncode, 1)
        self.assertIn("Release blocker:", result.stdout)

    def test_missing_summary_fails(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "release-report.md"
            path.write_text("# Report\n", encoding="utf-8")

            result = self.run_script(str(path))

            self.assertEqual(result.returncode, 2)
            self.assertIn("fenced YAML summary", result.stderr)


if __name__ == "__main__":
    unittest.main()
