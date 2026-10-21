# Tools for structural Bioinformatics

`CIBB_2026` is the course repository for a 45-minute online lecture followed by a 45-minute practical, for MSc, PhD and research-level bioscience students. It contains a static GitHub Pages site, the current 16-slide lecture, student notes, resource links and tested PyMOL helpers.

The practical is explicitly **in preparation**. Its page and directories are ready for future material; there is no implied completed worksheet, model pack or MnMT4 answer key.

## Quick start on Linux

Unpack `CIBB_2026.zip` in your local repository folder. The ZIP contains a single top-level `CIBB_2026/` directory and no pre-existing `.git` history.

```bash
unzip CIBB_2026.zip
cd CIBB_2026
git init -b main
git add .
git commit -m "Initial CIBB 2026 course site"
```

Create an empty repository named `CIBB_2026` in your GitHub account, then use its actual SSH or HTTPS remote:

```bash
git remote add origin git@github.com:YOUR_GITHUB_USERNAME/CIBB_2026.git
git push -u origin main
```

Replace `YOUR_GITHUB_USERNAME`; no account name is hardcoded into the website or workflow. These instructions do not create or push a remote repository automatically.

## Enable GitHub Pages

In the GitHub repository, open **Settings → Pages → Build and deployment → Source → GitHub Actions**. Then run the **Validate and deploy course** workflow under Actions, or push another commit to `main`; the supplied workflow builds, checks and deploys **only `docs/`** ([GitHub Pages custom-workflow documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)).

GitHub reports the final Pages address in the deployment. A project site normally sits under the repository name, so all internal assets and links use relative paths rather than assuming a domain-root deployment ([GitHub Pages documentation](https://docs.github.com/en/pages/getting-started-with-github-pages)).

For a branch-based alternative, the already-generated site can be published from `main` and `/docs`; use only one deployment method. GitHub Actions is the default supplied here.

## Repository tree

```text
CIBB_2026/
├── .github/workflows/pages.yml   # Validation + Pages deployment
├── .editorconfig                # UTF-8 and LF editing defaults
├── .gitattributes               # LF text, binary assets excluded
├── .gitignore                   # Local environments and analysis outputs
├── course.json                  # Official title, availability, resource directory
├── content/
│   ├── notes.md                 # Student lecture companion
│   ├── practical.md             # Honest forthcoming-material page
│   └── student-notes-template.md
├── docs/                        # Complete, generated public website
│   ├── index.html
│   ├── slides.html
│   ├── notes.html
│   ├── practical.html
│   ├── toolkit.html
│   ├── resources.html
│   ├── sources.html
│   ├── assets/                  # Real molecular views + 16 PNG/SVG slides
│   └── downloads/               # Slides, notes and PyMOL toolkit
├── web/
│   ├── base.css
│   ├── site.css
│   ├── site.js
│   └── slides.js
├── pymol_scripts/
│   ├── ligand_align.py          # Explicit atom correspondences + rigid fit
│   ├── alignment_analysis.py    # Multi-model alignment and CSV reports
│   ├── startup.pml
│   ├── README.md
│   └── examples/                # Non-MnMT4 demonstration structures
├── practical/
│   ├── README.md
│   ├── data/README.md
│   └── worksheet/README.md
├── tools/
│   ├── build_site.py
│   ├── check_repo.py
│   └── package_repo.py
├── maintainer/QA.md
├── tests/test_helpers.py
├── requirements-dev.txt
├── serve.json                   # Optional local serve configuration
└── LICENSE.md
```

## Preview, edit and rebuild

The generated `docs/` files are committed, so the site needs no framework, Node installation or application backend to run. For a local preview:

```bash
python3 -m http.server 8000 --directory docs
# Open http://localhost:8000/
```

To regenerate pages and download bundles after editing `content/`, `course.json`, the scripts or `web/`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python tools/build_site.py
python tools/check_repo.py
python -m unittest discover -s tests -v
```

The slide viewer reads the local slide manifest; source PNG/SVG pairs are in `docs/assets/slides/`. Replacing slide assets and rebuilding updates the student download bundle without requiring an external slide-hosting service.

## PyMOL helpers

Read `pymol_scripts/README.md` before using the helpers. They do not install PyMOL or perform an AI prediction; they support explicit, inspectable visualisation and analysis operations.

- **Ligand fitting:** Produces a new fitted copy, preserves the original, requires chemically defensible atom correspondence and reports the RMSD of the fitted atom set.
- **Multiple alignment analysis:** Produces CSV/JSON summaries of an existing CA alignment, plus an optional alignment-building command. Coordinate dispersion is not model confidence, flexibility or an evolutionary coupling score.

The examples are experimental non-MnMT4 references or explicitly transformed copies. Pure mathematical tests run with NumPy; optional integration tests use `pymol2` when it is installed.

The supplied version passed all seven tests in an open-source PyMOL 3.2 / Python 3.11 environment, including the real PyMOL command-line demo. Without PyMOL, the four numerical tests run and the three integration tests are skipped.

To create a fresh source ZIP after an update, run `python tools/package_repo.py`. It validates the site, then writes `CIBB_2026.zip` and its SHA-256 sidecar one directory above the repository, omitting Git history, local environments, caches and generated analysis reports.

## Add the practical later

Edit `content/practical.md`, add approved student files to the practical directories, and update `practical_status` in `course.json` when those materials have actually been tested. Run `python tools/build_site.py`; it will rebuild the page and copy the student practical files into the published downloads.

Keep unpublished research data and instructor solutions in a separate private location, not merely outside `docs/`. The entire GitHub repository is readable when the repository is public.

## Publication and provenance

The lecture includes the explicit PDB100 caveat: redundancy reduction does not guarantee one returned hit per unique amino-acid sequence. The exact cause of the saved monomer search's duplicate full-length myoglobin sequences is not asserted.

All included text files use UTF-8 and Unix LF line endings, including Python, PML, Markdown, HTML, CSS, JavaScript, JSON, YAML and the example coordinate files. `tools/check_repo.py` verifies those conditions, local links, slide availability and the absence of machine-specific paths.

The slide images and examples work without live prediction services. Fonts use an optional Fontshare CDN with local system fallbacks; external tool sites require network access and may require accounts or suitable compute.
