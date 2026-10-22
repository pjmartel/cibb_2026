"""Offline validation: text hygiene, static paths, supplied PDF and downloads."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
from zipfile import ZipFile
import ast
from hashlib import sha256
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
TEXT = {".md", ".txt", ".py", ".pml", ".html", ".css", ".js", ".json", ".yml", ".yaml",
        ".svg", ".pdb", ".cff"}
EXCLUDE = {".git", ".venv", "__pycache__", "analysis-results", "test-results", ".pytest_cache"}
errors = []
text_files = 0


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.references = []
        self.h1 = 0
        self.ids = set()
        self.external = []

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == "h1":
            self.h1 += 1
        if "id" in attrs:
            if attrs["id"] in self.ids:
                errors.append(f"Duplicate HTML id: {attrs['id']}")
            self.ids.add(attrs["id"])
        if tag == "img" and "alt" not in attrs:
            errors.append("Image without alt text")
        for attr in ("href", "src"):
            if attr in attrs:
                self.references.append(attrs[attr])
        if tag == "a" and attrs.get("href", "").startswith(("http://", "https://")):
            if attrs.get("target") != "_blank" or "noopener" not in attrs.get("rel", ""):
                errors.append(f"Unsafe external link: {attrs['href']}")


for path in ROOT.rglob("*"):
    if not path.is_file() or any(part in EXCLUDE for part in path.parts):
        continue
    if path.suffix in TEXT or path.name in (".editorconfig", ".gitattributes", ".gitignore"):
        raw = path.read_bytes()
        text_files += 1
        if b"\r" in raw:
            errors.append(f"Non-LF text: {path.relative_to(ROOT)}")
        if raw and not raw.endswith(b"\n"):
            errors.append(f"No final LF: {path.relative_to(ROOT)}")
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            errors.append(f"Not UTF-8: {path.relative_to(ROOT)}")
            continue
        if ("/home" + "/user/") in text:
            errors.append(f"Machine-specific path: {path.relative_to(ROOT)}")
        if path.suffix == ".py":
            try:
                ast.parse(text)
            except SyntaxError as e:
                errors.append(f"Python syntax: {path.name}: {e}")
    if path.stat().st_size > 95 * 1024**2:
        errors.append(f"Asset too large for a normal Git repository: {path.name}")

pages = {}
for path in DOCS.glob("*.html"):
    parser = Page()
    parser.feed(path.read_text())
    pages[path.name] = parser
    if parser.h1 != 1:
        errors.append(f"{path.name}: expected one h1, got {parser.h1}")
for name, page in pages.items():
    for reference in page.references:
        url = urlsplit(reference)
        if url.scheme or reference.startswith("//") or not url.path:
            continue
        if url.path.startswith("/"):
            errors.append(f"Domain-root path fails project Pages prefix: {name} → {reference}")
            continue
        target = (DOCS / unquote(url.path)).resolve()
        if not target.is_relative_to(DOCS.resolve()) or not target.is_file():
            errors.append(f"Missing local target: {name} → {reference}")
        if url.fragment and target.name in pages:
            if url.fragment not in pages[target.name].ids:
                errors.append(f"Missing fragment: {name} → {reference}")
lecture_pdf = DOCS / "downloads/TSB_2026.pdf"
if not lecture_pdf.is_file():
    errors.append("Missing lecture PDF: docs/downloads/TSB_2026.pdf")
else:
    raw_pdf = lecture_pdf.read_bytes()
    if not raw_pdf.startswith(b"%PDF-") or b"%%EOF" not in raw_pdf[-2048:]:
        errors.append("Invalid or incomplete lecture PDF")
slides_html = (DOCS / "slides.html").read_text(encoding="utf-8")
if slides_html.count('href="downloads/TSB_2026.pdf"') != 2:
    errors.append("Slides page must offer both Open and Download links to the supplied PDF")
if 'download="TSB_2026.pdf"' not in slides_html or 'target="_blank"' not in slides_html:
    errors.append("Missing PDF download or new-tab action")
if any(old in slides_html for old in ("lecture-slides.zip", 'id="current-slide"', 'id="slide-data"', "assets/slides.js", ".svg")):
    errors.append("Slides page still offers the old image viewer or image downloads")
for note in (ROOT / "content/notes.md", DOCS / "downloads/lecture-notes.md"):
    if "PDB100" not in note.read_text(encoding="utf-8"):
        errors.append(f"Missing PDB100 companion-note caveat: {note.relative_to(ROOT)}")
for path in (DOCS / "downloads").glob("*.zip"):
    with ZipFile(path) as archive:
        if archive.testzip():
            errors.append(f"Corrupt ZIP: {path.name}")
        for name in archive.namelist():
            if name.startswith("/") or ".." in Path(name).parts:
                errors.append(f"Unsafe ZIP member: {name}")
            if Path(name).suffix in TEXT and b"\r" in archive.read(name):
                errors.append(f"Non-LF ZIP member: {path.name}/{name}")
expected = {"index.html", "notes.html", "slides.html", "practical.html", "toolkit.html", "resources.html", "sources.html"}
if set(pages) != expected:
    errors.append("Unexpected public page set")
source_manifest = ROOT / "pymol_scripts/source-manifest.json"
if not source_manifest.is_file():
    errors.append("Missing author-script source manifest")
else:
    supplied = json.loads(source_manifest.read_text())["files"]
    for filename, entry in supplied.items():
        for location in (ROOT / "pymol_scripts", DOCS / "downloads"):
            script = location / filename
            if not script.is_file() or sha256(script.read_bytes()).hexdigest() != entry["sha256"]:
                errors.append(f"Supplied source differs or is missing: {script.relative_to(ROOT)}")
    toolkit = DOCS / "downloads/pymol-toolkit.zip"
    with ZipFile(toolkit) as archive:
        for filename, entry in supplied.items():
            member = "pymol_scripts/" + filename
            if member not in archive.namelist() or sha256(archive.read(member)).hexdigest() != entry["sha256"]:
                errors.append(f"Supplied source differs inside toolkit ZIP: {filename}")
    for obsolete in ("ligand_align.py", "alignment_analysis.py"):
        if (ROOT / "pymol_scripts" / obsolete).exists():
            errors.append(f"Superseded helper still present: {obsolete}")
        if "pymol_scripts/" + obsolete in archive.namelist():
            errors.append(f"Superseded helper still in toolkit ZIP: {obsolete}")
workflow_path = ROOT / ".github/workflows/pages.yml"
if not workflow_path.is_file():
    errors.append("Missing GitHub Pages workflow at repository root")
else:
    workflow = workflow_path.read_text(encoding="utf-8")
    if re.search(r"^\s+cache:\s*['\"]?pip['\"]?\s*$", workflow, re.MULTILINE):
        dependency = re.search(r"^\s+cache-dependency-path:\s*([^\s#]+)", workflow, re.MULTILINE)
        if not dependency:
            errors.append("Pip cache must explicitly name the course dependency manifest with cache-dependency-path")
        elif not (ROOT / dependency.group(1).strip("'\"")).is_file():
            errors.append("Pip cache dependency manifest does not exist at the configured path")
if errors:
    print("\n".join(errors), file=sys.stderr)
    raise SystemExit(1)
print(f"PASS: {len(pages)} pages, supplied lecture PDF, {text_files} UTF-8/LF text files, local links, ZIPs and workflow cache path valid.")
