"""Publication regression tests; the instructor's PDF is never regenerated."""
from hashlib import sha256
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PDF = Path("docs/downloads/TSB_2026.pdf")


class PdfPublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "course"
        shutil.copytree(
            ROOT, self.root,
            ignore=shutil.ignore_patterns(".git", ".venv", "__pycache__", "analysis-results", "test-results"),
        )

    def build(self):
        return subprocess.run(
            [sys.executable, "tools/build_site.py"], cwd=self.root,
            capture_output=True, text=True, check=False,
        )

    def test_build_preserves_pdf_and_ignores_legacy_slide_count(self):
        before = sha256((self.root / PDF).read_bytes()).hexdigest()
        # The old image manifest is not required for PDF publication.
        (self.root / "docs/assets/slides/slide-manifest.json").unlink()
        result = self.build()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(sha256((self.root / PDF).read_bytes()).hexdigest(), before)
        page = (self.root / "docs/slides.html").read_text(encoding="utf-8")
        self.assertEqual(page.count('href="downloads/TSB_2026.pdf"'), 2)
        self.assertNotIn("lecture-slides.zip", page)
        self.assertNotIn("current-slide", page)
        self.assertNotIn("16 slides", page)

    def test_missing_pdf_fails_before_pages_are_rewritten(self):
        page = self.root / "docs/slides.html"
        before = page.read_bytes()
        (self.root / PDF).unlink()
        result = self.build()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Missing lecture PDF", result.stderr)
        self.assertEqual(page.read_bytes(), before)

    def test_incomplete_pdf_fails_before_pages_are_rewritten(self):
        page = self.root / "docs/slides.html"
        before = page.read_bytes()
        (self.root / PDF).write_bytes(b"%PDF-1.7\nincomplete export\n")
        result = self.build()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Invalid lecture PDF", result.stderr)
        self.assertEqual(page.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
