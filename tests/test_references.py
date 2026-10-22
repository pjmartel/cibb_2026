"""Lecture-only bibliography, navigation and publication regressions."""
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
APPROVED_DOIS = {
    "10.1038/s41586-021-03819-2", "10.1038/s41586-024-07487-w",
    "10.1101/2025.06.14.659707", "10.1038/s41587-023-01773-0",
    "10.1093/nar/gki524", "10.1073/pnas.1500806112",
    "10.1093/bioinformatics/bty862", "10.1038/nbt.3769",
    "10.1126/science.ade2574", "10.1126/science.adv9817",
    "10.1038/s41586-023-06415-8", "10.1126/science.aeh2982",
    "10.1038/s41592-025-02593-7", "10.1002/prot.22934",
    "10.1103/PhysRevE.87.012707", "10.1038/s41586-024-08416-7",
    "10.1073/pnas.1415940111",
}


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.h1_count = 0
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "h1":
            self.h1_count += 1
        if tag == "a":
            self.links.append(attrs)


class ReferencesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name) / "course with spaces"
        shutil.copytree(
            ROOT, cls.root,
            ignore=shutil.ignore_patterns(".git", ".venv", "__pycache__", "analysis-results", "test-results"),
        )
        cls.protected = [
            "docs/downloads/TSB_2026.pdf", ".github/workflows/pages.yml",
            "pymol_scripts/ligalign.py", "pymol_scripts/struct_diff.py",
            "docs/downloads/ligalign.py", "docs/downloads/struct_diff.py",
        ]
        cls.before = {name: sha256((cls.root / name).read_bytes()).hexdigest()
                      for name in cls.protected}
        cls.build = subprocess.run(
            [sys.executable, "tools/build_site.py"], cwd=cls.root,
            capture_output=True, text=True,
        )

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_build_accepts_existing_pdf_and_new_page(self):
        self.assertEqual(self.build.returncode, 0, self.build.stderr)
        self.assertIn("Built 8 static pages", self.build.stdout)
        self.assertTrue((self.root / "docs/references.html").is_file())

    def test_source_is_exact_approved_lecture_selection(self):
        source = (self.root / "content/references.md").read_text()
        found = {doi.rstrip(".") for doi in re.findall(r"DOI: (\S+)", source)}
        self.assertEqual(found, APPROVED_DOIS)
        self.assertEqual(source.count("\n- **"), 18)
        self.assertNotRegex(source, r"(?m)^# ")
        self.assertIn("proceedings.neurips.cc", source)
        self.assertIn("[preprint]", source)
        self.assertIn("First Release, 15 Oct 2026", source)

    def test_public_page_has_one_heading_and_safe_source_links(self):
        page = Page()
        page.feed((self.root / "docs/references.html").read_text())
        self.assertEqual(page.h1_count, 1)
        external = [a for a in page.links if a.get("href", "").startswith("https://")]
        self.assertEqual(len(external), 18)
        for a in external:
            self.assertEqual(a.get("target"), "_blank")
            self.assertIn("noopener", a.get("rel", ""))
        html = (self.root / "docs/references.html").read_text()
        self.assertIn("Merski", html)
        for doi in APPROVED_DOIS:
            self.assertIn(doi, html)

    def test_every_page_exposes_reference_navigation_and_footer(self):
        pages = list((self.root / "docs").glob("*.html"))
        self.assertEqual(len(pages), 8)
        for path in pages:
            html = path.read_text()
            self.assertIn('href="references.html">References</a>', html)
            if path.name == "references.html":
                self.assertIn('href="references.html" aria-current="page">References</a>', html)
        home = (self.root / "docs/index.html").read_text()
        self.assertIn('<h3>References</h3>', home)

    def test_download_matches_source_and_approved_document_shape(self):
        source = (self.root / "content/references.md").read_bytes()
        expected = b"# Tools for structural Bioinformatics: lecture references\n\n" + source
        self.assertEqual((self.root / "docs/downloads/lecture-references.md").read_bytes(), expected)
        self.assertEqual(expected.count(b"\n- **"), 18)
        self.assertIn(b'href="downloads/lecture-references.md" download',
                      (self.root / "docs/references.html").read_bytes())

    def test_build_preserves_protected_material(self):
        for name, digest in self.before.items():
            self.assertEqual(sha256((self.root / name).read_bytes()).hexdigest(), digest, name)
        slide = (self.root / "docs/slides.html").read_text()
        self.assertEqual(slide.count('href="downloads/TSB_2026.pdf"'), 2)
        self.assertNotIn("current-slide", slide)

    def test_repeated_build_preserves_bibliography(self):
        files = ["docs/references.html", "docs/downloads/lecture-references.md"]
        before = {name: (self.root / name).read_bytes() for name in files}
        result = subprocess.run(
            [sys.executable, "tools/build_site.py"], cwd=self.root,
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        for name, original in before.items():
            self.assertEqual((self.root / name).read_bytes(), original)

    def test_repository_validator_accepts_eight_pages(self):
        result = subprocess.run(
            [sys.executable, "tools/check_repo.py"], cwd=self.root,
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS: 8 pages", result.stdout)


if __name__ == "__main__":
    unittest.main()
