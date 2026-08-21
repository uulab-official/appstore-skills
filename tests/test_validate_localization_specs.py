from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_localization_specs.py"
DEMO = ROOT / "examples/demo-store-assets"
PLAN = DEMO / "localization-plan.yml"
GLOSSARY = DEMO / "terminology.yml"


class ValidateLocalizationSpecsTests(unittest.TestCase):
    def run_validator(self, plan: Path, glossary: Path, package: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(plan), str(glossary), "--package-root", str(package)],
            check=False,
            capture_output=True,
            text=True,
        )

    def create_copy_fixture(self, package: Path) -> tuple[Path, Path]:
        metadata = package / "metadata"
        metadata.mkdir()
        (metadata / "store-copy.en-US.yml").write_text(
            (DEMO / "metadata/store-copy.en-US.yml").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        (metadata / "store-copy.ko-KR.yml").write_text(
            (DEMO / "metadata/store-copy.ko-KR.yml").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        plan = package / "localization-plan.yml"
        plan.write_text(PLAN.read_text(encoding="utf-8"), encoding="utf-8")
        glossary = package / "terminology.yml"
        glossary.write_text(GLOSSARY.read_text(encoding="utf-8"), encoding="utf-8")
        return plan, glossary

    def test_demo_localization_passes(self) -> None:
        result = self.run_validator(PLAN, GLOSSARY, DEMO)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_copy_locale_mismatch_fails(self) -> None:
        with TemporaryDirectory() as directory:
            package = Path(directory)
            metadata = package / "metadata"
            metadata.mkdir()
            (metadata / "store-copy.en-US.yml").write_text(
                "schema_version: 1\nlocale: en-US\nstatus: review\n", encoding="utf-8"
            )
            (metadata / "store-copy.ko-KR.yml").write_text(
                "schema_version: 1\nlocale: fr-FR\nstatus: review\n", encoding="utf-8"
            )
            plan = package / "localization-plan.yml"
            plan.write_text(PLAN.read_text(encoding="utf-8"), encoding="utf-8")
            glossary = package / "terminology.yml"
            glossary.write_text(GLOSSARY.read_text(encoding="utf-8"), encoding="utf-8")

            result = self.run_validator(plan, glossary, package)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("locale must be ko-KR", result.stdout)

    def test_forbidden_term_fails(self) -> None:
        with TemporaryDirectory() as directory:
            package = Path(directory)
            metadata = package / "metadata"
            metadata.mkdir()
            for locale, text in (
                ("en-US", "task reminders"),
                ("ko-KR", "할 일 알림"),
            ):
                (metadata / f"store-copy.{locale}.yml").write_text(
                    f"schema_version: 1\nlocale: {locale}\nstatus: review\ntext: {text}\n",
                    encoding="utf-8",
                )
            plan = package / "localization-plan.yml"
            plan.write_text(PLAN.read_text(encoding="utf-8"), encoding="utf-8")
            glossary = package / "terminology.yml"
            glossary.write_text(
                GLOSSARY.read_text(encoding="utf-8").replace("do_not_use: [chore]", "do_not_use: [task]"),
                encoding="utf-8",
            )

            result = self.run_validator(plan, glossary, package)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("do_not_use term 'task'", result.stdout)

    def test_target_copy_must_preserve_source_platform_fields(self) -> None:
        with TemporaryDirectory() as directory:
            package = Path(directory)
            plan, glossary = self.create_copy_fixture(package)
            target = package / "metadata/store-copy.ko-KR.yml"
            target.write_text(
                target.read_text(encoding="utf-8").replace(
                    "  promotional_text: 다음 할 일을 기록하고 계속 진행하세요.\n", ""
                ),
                encoding="utf-8",
            )

            result = self.run_validator(plan, glossary, package)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing platform copy fields from en-US: apple.promotional_text", result.stdout)

    def test_target_copy_cannot_introduce_untracked_platform_fields(self) -> None:
        with TemporaryDirectory() as directory:
            package = Path(directory)
            plan, glossary = self.create_copy_fixture(package)
            target = package / "metadata/store-copy.ko-KR.yml"
            target.write_text(
                target.read_text(encoding="utf-8").replace(
                    "  whats_new: 데모 카피입니다. 승인된 출시 노트로 교체하세요.\n",
                    "  whats_new: 데모 카피입니다. 승인된 출시 노트로 교체하세요.\n  campaign_badge: 신규\n",
                ),
                encoding="utf-8",
            )

            result = self.run_validator(plan, glossary, package)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unexpected platform copy fields relative to en-US: apple.campaign_badge", result.stdout)


if __name__ == "__main__":
    unittest.main()
