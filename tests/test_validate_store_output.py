from pathlib import Path
import struct
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
import zlib


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_store_output.py"


def png_bytes(width: int, height: int, color_type: int = 6) -> bytes:
    signature = b"\x89PNG\r\n\x1a\n"

    def chunk(kind: bytes, payload: bytes) -> bytes:
        body = kind + payload
        return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body))

    ihdr = struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0)
    return signature + chunk(b"IHDR", ihdr) + chunk(b"IEND", b"")


class ValidateStoreOutputTests(unittest.TestCase):
    def run_validator(self, output_root: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(output_root)],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_valid_package_passes(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "brand-context.yml").write_text("schema_version: 1\n", encoding="utf-8")
            (root / "QA.md").write_text("# QA\n", encoding="utf-8")
            (root / "icon").mkdir()
            (root / "icon" / "icon-master.png").write_bytes(b"not-an-image-but-not-empty")
            (root / "manifest.yml").write_text(
                "schema_version: 1\nassets:\n"
                "  - path: icon/icon-master.png\n"
                "    status: review\n",
                encoding="utf-8",
            )

            result = self.run_validator(root)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_path_traversal_fails(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "brand-context.yml").write_text("schema_version: 1\n", encoding="utf-8")
            (root / "QA.md").write_text("# QA\n", encoding="utf-8")
            (root / "manifest.yml").write_text(
                "schema_version: 1\nassets:\n"
                "  - path: ../secret.txt\n"
                "    status: review\n",
                encoding="utf-8",
            )

            result = self.run_validator(root)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must stay inside output root", result.stdout)

    def test_declared_png_metadata_passes(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "brand-context.yml").write_text("schema_version: 1\n", encoding="utf-8")
            (root / "QA.md").write_text("# QA\n", encoding="utf-8")
            (root / "icon").mkdir()
            (root / "icon" / "master.png").write_bytes(png_bytes(1024, 1024, 2))
            (root / "manifest.yml").write_text(
                "schema_version: 1\nassets:\n"
                "  - path: icon/master.png\n"
                "    status: review\n"
                "    format: png\n"
                "    dimensions: 1024x1024\n"
                "    color_type: rgb\n",
                encoding="utf-8",
            )

            result = self.run_validator(root)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_declared_png_dimensions_fail(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "brand-context.yml").write_text("schema_version: 1\n", encoding="utf-8")
            (root / "QA.md").write_text("# QA\n", encoding="utf-8")
            (root / "icon").mkdir()
            (root / "icon" / "master.png").write_bytes(png_bytes(1024, 1024))
            (root / "manifest.yml").write_text(
                "schema_version: 1\nassets:\n"
                "  - path: icon/master.png\n"
                "    status: review\n"
                "    format: png\n"
                "    dimensions: 512x512\n",
                encoding="utf-8",
            )

            result = self.run_validator(root)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("dimensions are 1024x1024, expected 512x512", result.stdout)

    def test_declared_svg_viewbox_passes(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "brand-context.yml").write_text("schema_version: 1\n", encoding="utf-8")
            (root / "QA.md").write_text("# QA\n", encoding="utf-8")
            (root / "web").mkdir()
            (root / "web" / "mark.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256"></svg>\n',
                encoding="utf-8",
            )
            (root / "manifest.yml").write_text(
                "schema_version: 1\nassets:\n"
                "  - path: web/mark.svg\n"
                "    status: review\n"
                "    format: svg\n"
                "    dimensions: 256x256\n",
                encoding="utf-8",
            )

            result = self.run_validator(root)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
