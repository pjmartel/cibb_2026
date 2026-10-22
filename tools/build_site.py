"""Build the committed static Pages site and student download bundles."""
from pathlib import Path
from html import escape
import json
import re
import shutil
from zipfile import ZipFile, ZIP_DEFLATED
import markdown

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CONFIG = json.loads((ROOT / "course.json").read_text())
TITLE = CONFIG["title"]
PRACTICAL_READY = CONFIG["practical_status"] == "ready"
# This supplied PDF is the publication master. Never regenerate it from images.
LECTURE_PDF = DOCS / "downloads/TSB_2026.pdf"
if not LECTURE_PDF.is_file():
    raise SystemExit("Missing lecture PDF: place your PowerPoint PDF export at docs/downloads/TSB_2026.pdf, then rebuild.")
pdf_bytes = LECTURE_PDF.read_bytes()
if not pdf_bytes.startswith(b"%PDF-") or b"%%EOF" not in pdf_bytes[-2048:]:
    raise SystemExit("Invalid lecture PDF: export a complete PDF to docs/downloads/TSB_2026.pdf, then rebuild.")
PDF_SIZE = f"{len(pdf_bytes) / 1_000_000:.1f} MB"
NAV = [("notes.html", "Student notes"), ("slides.html", "Slides"), ("practical.html", "Practical"),
       ("toolkit.html", "PyMOL toolkit"), ("resources.html", "Resources")]


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def external_links(text):
    return re.sub(r'<a href="(https?://[^"]+)"', r'<a target="_blank" rel="noopener noreferrer" href="\1"', text)


def md_file(path):
    md = markdown.Markdown(extensions=["toc", "tables", "fenced_code"], output_format="html")
    body = md.convert(path.read_text(encoding="utf-8"))
    body = body.replace('src="../docs/assets/', 'src="assets/')
    return external_links(body), md.toc


def head(title, description):
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)} | CIBB 2026</title><meta name="description" content="{escape(description)}">
<meta property="og:title" content="{escape(title)}"><meta property="og:description" content="{escape(description)}">
<meta property="og:type" content="website"><meta property="og:image" content="assets/images/myoglobin.webp">
<link rel="preconnect" href="https://api.fontshare.com"><link rel="preconnect" href="https://cdn.fontshare.com" crossorigin>
<link rel="stylesheet" href="assets/base.css"><link rel="stylesheet" href="assets/site.css">
<script src="assets/site.js" defer></script></head>'''


def page(filename, title, description, body, extra=""):
    links = "".join(f'<a href="{url}"'+(' aria-current="page"' if url == filename else '')+f'>{label}</a>' for url, label in NAV)
    header = f'''<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header"><div class="wrap nav-wrap"><a class="wordmark" href="index.html">CIBB<span> / 2026</span></a>
<button class="menu-toggle" data-menu aria-expanded="false" aria-controls="main-navigation">Menu</button>
<nav id="main-navigation" class="main-nav" aria-label="Primary">{links}</nav></div></header>'''
    footer = '''<footer class="site-footer"><div class="wrap footer-inner">
<p>CIBB 2026 · Tools for structural Bioinformatics</p>
<p><a href="sources.html">Sources &amp; reuse</a><a href="resources.html">Resource directory</a></p>
</div></footer>'''
    write(DOCS / filename, head(title, description) + "<body>" + header + body + footer + extra + "</body></html>\n")


def heading(kicker, title, description, actions=""):
    return f'''<div class="page-head"><p class="eyebrow">{kicker}</p><h1>{title}</h1><p>{description}</p>
{f'<div class="actions">{actions}</div>' if actions else ''}</div>'''


def reading_page(filename, title, kicker, source, description, actions=""):
    body, toc = md_file(source)
    page(filename, title, description, f'<main id="main" class="wrap">{heading(kicker,title,description,actions)}'
         f'<div class="reading-layout"><aside class="toc" aria-label="On this page">{toc}</aside>'
         f'<article class="article">{body}</article></div></main>')


DOCS.mkdir(exist_ok=True)
for filename in ("base.css", "site.css", "site.js", "slides.js"):
    shutil.copy2(ROOT / "web" / filename, DOCS / "assets" / filename)
write(DOCS / ".nojekyll", "")

page("index.html", TITLE, "A graduate-level class connecting protein sequences, structural predictions, comparison and molecular interactions. Lecture materials, notes and PyMOL tools.",
f'''<main id="main"><div class="wrap">
<section class="hero" aria-labelledby="course-title"><div>
<p class="eyebrow">Graduate class · CIBB 2026</p><h1 id="course-title">{TITLE}</h1>
<p class="lede">From sequences to structural hypotheses. A modern, evidence-led view of protein models, molecular interactions and the experiments that follow.</p>
<div class="hero-actions"><a class="button" href="slides.html">Open lecture slides <span aria-hidden="true">↗</span></a>
<a class="text-link" href="notes.html">Read student notes <span aria-hidden="true">→</span></a></div>
</div><figure class="hero-figure"><p class="figure-label">Experimental reference / myoglobin</p>
<img src="assets/images/myoglobin.webp" width="640" height="600" alt="Teal cartoon of the experimental sperm-whale myoglobin fold" fetchpriority="high">
<figcaption>1MBN, chain A. Protein cartoon; heme omitted. <a href="https://www.rcsb.org/structure/1MBN" target="_blank" rel="noopener noreferrer">View structure record ↗</a></figcaption>
</figure></section>
<div class="course-strip"><span><strong>45 min</strong> online lecture</span><span><strong>45 min</strong> practical</span><span><strong>MSc / PhD</strong> biosciences</span></div>
<section class="section" aria-labelledby="materials-title"><div class="section-heading"><h2 id="materials-title">Class materials</h2>
<p>Follow the lecture, keep an evidence record, and get your molecular workspace ready.</p></div>
<div class="materials"><article class="featured-material"><p class="eyebrow">Lecture / PDF</p>
<a href="slides.html"><img src="assets/images/foldseek-search.webp" width="1200" height="675" loading="lazy" alt="Lecture illustration showing the real myoglobin Foldseek search and the PDB100 caveat"></a>
<h3><a href="slides.html">The structural evidence workflow</a></h3><p>Sequence information, model assessment, structural search, complexes, ensembles and design.</p>
<a class="text-link" href="slides.html">View the lecture <span aria-hidden="true">→</span></a></article>
<div><a class="material-link" href="notes.html"><div class="row"><h3>Student notes</h3><span class="arrow" aria-hidden="true">↗</span></div><p>A lecture companion with key distinctions, primary links and a downloadable notes template.</p></a>
<a class="material-link" href="toolkit.html"><div class="row"><h3>PyMOL toolkit</h3><span class="arrow" aria-hidden="true">↗</span></div><p>Use Paulo Martel's symmetry-aware ligand comparison and structural-difference tools.</p></a>
<a class="material-link" href="resources.html"><div class="row"><h3>Tools &amp; databases</h3><span class="arrow" aria-hidden="true">↗</span></div><p>Official entry points for the tools used in the class, with access and interpretation notes.</p></a></div></div></section>
<section class="practical-banner" aria-labelledby="practical-title"><div><span class="status">{"Materials available" if PRACTICAL_READY else "In preparation"}</span><h2 id="practical-title">The MnMT4 practical</h2>
<p>{"The student worksheet, approved inputs and offline materials are available in the practical section." if PRACTICAL_READY else "A place for the student worksheet, approved inputs and offline materials. The activity will appear here once it has been designed and tested."}</p></div>
<a class="button secondary" href="practical.html">Practical preparation <span aria-hidden="true">→</span></a></section>
</div></main>''')

reading_page("notes.html", "Student notes", "Lecture companion",
             ROOT / "content/notes.md", "Concepts, caveats and source links to accompany the 45-minute lecture. Keep observations, predictions and hypotheses distinguishable.",
             '<a class="button" href="downloads/lecture-notes.md" download>Download lecture notes</a><a class="button secondary" href="downloads/student-notes-template.md" download>Download notes template</a>')

status = "In preparation" if CONFIG["practical_status"] != "ready" else "Practical"
reading_page("practical.html", "Practical", status, ROOT / "content/practical.md",
             "The 45-minute practical will apply the lecture framework to MnMT4. Materials are clearly marked according to their current availability.",
             '<a class="button secondary" href="toolkit.html">Prepare PyMOL</a><a class="text-link" href="resources.html">Browse resources →</a>')

page("slides.html", "Lecture slides", "Open or download the lecture PDF for Tools for structural Bioinformatics, with companion student notes.",
     f'''<main id="main" class="wrap">{heading("45-minute lecture / PDF","Lecture slides",
     TITLE + ". Open the lecture in your browser or download a copy to keep.",
     '<a class="button" href="downloads/TSB_2026.pdf" target="_blank" rel="noopener noreferrer">Open lecture PDF ↗</a>'
     '<a class="button secondary" href="downloads/TSB_2026.pdf" download="TSB_2026.pdf">Download lecture PDF</a>')}
<div class="slide-shell"><p class="slide-description">TSB_2026.pdf · PDF · {PDF_SIZE}</p>
<a class="text-link" href="notes.html">Read companion notes →</a></div></main>''')

toolkit_html, _ = md_file(ROOT / "pymol_scripts/README.md")
toolkit_html = re.sub(r"<h1\b[^>]*>.*?</h1>", "", toolkit_html, count=1)
page("toolkit.html", "PyMOL toolkit", "Download Paulo Martel's ligalign.py and struct_diff.py, with symmetry-aware ligand comparison and structural-difference examples.",
     f'''<main id="main" class="wrap">{heading("Visualisation / coordinate analysis","PyMOL toolkit","Small, inspectable helpers for working with structures. No docking, model generation or MnMT4 solutions are included.")}
<div class="toolkit-lead"><section class="toolkit-panel"><p class="eyebrow">Software</p><h2>Get PyMOL</h2>
<p>Use the official downloads and check your institutional licence. An open-source installation route is listed in the resource directory.</p>
<a class="button" href="https://pymol.org/2/" target="_blank" rel="noopener noreferrer">Official PyMOL downloads ↗</a>
<p class="resource-url">https://pymol.org/2/</p><a class="text-link" href="resources.html">Installation alternatives →</a></section>
<section class="toolkit-panel"><p class="eyebrow">Author-supplied tools</p><h2>ligalign &amp; struct_diff</h2>
<p>Paulo Martel's standalone scripts, unchanged. Includes symmetry-aware benzene comparison and a myoglobin–leghemoglobin difference-mapping example.</p>
<a class="button secondary" href="downloads/pymol-toolkit.zip" download>Download PyMOL toolkit</a>
<p><a href="downloads/ligalign.py" download>ligalign.py</a> · <a href="downloads/struct_diff.py" download>struct_diff.py</a></p>
<p>Python / PML · UTF-8 · Linux LF line endings</p></section></div>
<article class="article toolkit-read">{toolkit_html}</article></main>''')

categories = sorted({r["category"] for r in CONFIG["resources"]})
category_options = '<option>All</option>' + "".join(f"<option>{escape(c)}</option>" for c in categories)
resource_html = ""
for r in CONFIG["resources"]:
    resource_html += f'''<article class="resource" data-resource data-category="{escape(r['category'])}">
<p class="eyebrow">{escape(r['category'])}</p><h2><a href="{r['url']}" target="_blank" rel="noopener noreferrer">{escape(r['name'])} ↗</a></h2>
<p>{escape(r['description'])}</p><span class="resource-url">{escape(r['url'])}</span></article>'''
page("resources.html", "Tools & databases", "Official links to structural-bioinformatics tools, databases, downloads and documentation used in the lecture and future practical.",
     f'''<main id="main" class="wrap">{heading("Class directory","Tools &amp; databases","Official entry points, not endorsements or promises of free hosted compute. Check current inputs, access terms and data-sharing policies before submitting research sequences.")}
<div class="resource-controls"><label for="resource-search">Find a resource<input id="resource-search" type="search" placeholder="Try Foldseek, ligands or PyMOL"></label>
<label for="resource-category">Topic<select id="resource-category">{category_options}</select></label></div>
<p class="resource-count" data-resource-count aria-live="polite">{len(CONFIG['resources'])} resources</p>
<div class="resource-grid">{resource_html}</div><div class="empty" data-empty hidden><h2>No matching resources</h2><p>Try a broader term or reset the topic filter.</p><button class="button secondary" data-reset-resources>Reset filters</button></div></main>''')

sources = '''## Data and molecular figures

The molecular illustrations are renderings of actual coordinate references, not generated protein shapes. The lecture retains experimental-versus-predicted labels and separates illustrative workflows from computed results.

- Myoglobin: [1MBN](https://www.rcsb.org/structure/1MBN).
- Leghemoglobin: [1FSL](https://www.rcsb.org/structure/1FSL).
- Calmodulin experimental comparison: [1CLL](https://www.rcsb.org/structure/1CLL); prediction and confidence data: [AlphaFold model](https://alphafold.ebi.ac.uk/files/AF-P0DP23-F1-model_v6.cif).
- Barnase–barstar: [1BRS](https://www.rcsb.org/structure/1BRS), the displayed biological assembly.
- Lysozyme–benzene: [4W52](https://www.rcsb.org/structure/4W52).
- Adenylate kinase: [4AKE](https://www.rcsb.org/structure/4AKE) and [1AKE](https://www.rcsb.org/structure/1AKE).
- Constrained-design illustration: [classic RFdiffusion input example](https://github.com/RosettaCommons/RFdiffusion/blob/main/examples/design_ppi.sh), explicitly a provided target model, not a newly generated binder.

## Search provenance and limits

The Foldseek example uses a saved 1MBN-chain-A query against PDB100, with server-reported version `20240101` ([server metadata](https://search.foldseek.com/api/databases)). Identical full-length myoglobin sequences occur in the returned list; the exact reason for their retention in that monomer job has not been established ([saved response](https://search.foldseek.com/api/result/9JUQmuFtzzCi-ufQrRv0mkHE562y671NBHSwsw/0)).

The site and notes therefore do not guarantee one returned hit per unique sequence. The lecture's displayed search and alignment numbers are preserved, rather than replaced by a new live search.

## Software, fonts and reuse

External tools remain governed by their own licences and terms. PyMOL is not bundled, and this repository distributes no AI weights or service credentials.

The class visualisation scripts, `ligalign.py` and `struct_diff.py`, were supplied by Paulo Martel and are included unchanged. Their downloadable copies and toolkit ZIP preserve the same source bytes; these scripts do not generate the lecture's molecular predictions.

Typography uses Zodiak and Satoshi via [Fontshare](https://www.fontshare.com/), with system fallbacks. No blanket reuse licence has been selected for the original course material or helper code; consult the repository's licensing note before redistribution.
'''
sources_html = external_links(markdown.markdown(sources, extensions=["fenced_code"]))
page("sources.html", "Sources & reuse", "Coordinate references, search provenance, software terms and attribution for Tools for structural Bioinformatics.",
     '<main id="main" class="wrap">'+heading("Attribution","Sources &amp; reuse","Reference provenance and reuse information for the lecture and its molecular examples.")+
     '<article class="article" style="padding-bottom:var(--space-16)">'+sources_html+'</article></main>')

downloads = DOCS / "downloads"
downloads.mkdir(exist_ok=True)
for script in ("ligalign.py", "struct_diff.py"):
    shutil.copy2(ROOT / "pymol_scripts" / script, downloads / script)
write(downloads / "lecture-notes.md", (ROOT / "content/notes.md").read_text().replace("../docs/assets/", "../assets/"))
shutil.copy2(ROOT / "content/student-notes-template.md", downloads / "student-notes-template.md")
for filename, files, base in [
    ("pymol-toolkit.zip", sorted((ROOT / "pymol_scripts").rglob("*")), ROOT),
]:
    with ZipFile(downloads / filename, "w", compression=ZIP_DEFLATED, compresslevel=6) as z:
        for path in files:
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                z.write(path, path.relative_to(base))
    with ZipFile(downloads / filename) as z:
        assert z.testzip() is None

student_practical = [p for p in (ROOT / "practical").rglob("*") if p.is_file() and p.name != "README.md"]
if student_practical:
    with ZipFile(downloads / "practical-materials.zip", "w", ZIP_DEFLATED) as z:
        for path in student_practical:
            z.write(path, path.relative_to(ROOT))
    # Link only an actual student pack, not the README-only reserved directories.
    practical_page = DOCS / "practical.html"
    content = practical_page.read_text()
    content = content.replace('<div class="actions">', '<div class="actions"><a class="button" href="downloads/practical-materials.zip" download>Download practical materials</a>', 1)
    write(practical_page, content)
else:
    (downloads / "practical-materials.zip").unlink(missing_ok=True)

print("Built 7 static pages and student downloads in docs/. Supplied lecture PDF preserved unchanged.")
