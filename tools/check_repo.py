"""Offline validation: text hygiene, static paths, availability and slide files."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
from zipfile import ZipFile
import ast
import json
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
        if url.fragment and target.name in pages and not url.fragment.startswith("slide-"):
            if url.fragment not in pages[target.name].ids:
                errors.append(f"Missing fragment: {name} → {reference}")
slides = json.loads((DOCS / "assets/slides/slide-manifest.json").read_text())["slides"]
if len(slides) != 16 or sum(s["duration_seconds"] for s in slides) != 2700:
    errors.append("Unexpected slide count or lecture duration")
for row in slides:
    for ext in ("png", "svg"):
        if not (DOCS / "assets/slides" / (row["file_stem"] + "." + ext)).is_file():
            errors.append(f"Missing slide: {row['slide']} {ext}")
slide8 = next(r for r in slides if r["slide"] == 8)
if "PDB100 is redundancy-reduced" not in (DOCS / "assets/slides" / (slide8["file_stem"] + ".svg")).read_text():
    errors.append("Missing verified PDB100 slide caveat")
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
if errors:
    print("\n".join(errors), file=sys.stderr)
    raise SystemExit(1)
print(f"PASS: {len(pages)} pages, {len(slides)} slides, {text_files} UTF-8/LF text files, local links and ZIPs valid.")
