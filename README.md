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

The archive already includes a custom workflow at `.github/workflows/pages.yml`, named **Validate and deploy course**. This is a workflow supplied with this repository, not an action to search for in the GitHub Marketplace.

1. First, open the repository's **Code** tab and check that `.github/workflows/pages.yml` exists at the repository root, alongside `docs/`, `content/` and `README.md`. Do not upload the ZIP itself as the repository contents or put the entire course inside an extra nested `CIBB_2026/` folder.
2. Open **Settings → Pages → Build and deployment → Source** and select **GitHub Actions**. GitHub may show template suggestions such as Static HTML and Jekyll; skip the templates because this repository already supplies its own publishing workflow ([GitHub's publishing-source instructions](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)).
3. Leave Settings and click the repository's top-level **Actions** tab. In its left sidebar, select **Validate and deploy course**. Do not use the **New workflow** template gallery or Marketplace search to find this custom workflow.
4. Click **Run workflow**, choose `main`, and confirm **Run workflow**. The manual-run button requires the workflow's `workflow_dispatch` configuration to be present on the repository's default branch; the supplied YAML includes this configuration ([GitHub's manual-run instructions](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow)).
5. Open the run to see its build and deploy jobs. The supplied workflow builds, checks and deploys **only `docs/`**; future pushes to `main` also trigger it.

If the custom workflow is missing from the Actions sidebar, first check the file in the **Code** tab rather than choosing a template. `.github/` is a hidden directory on Linux and can be missed when copying only visible files. From the local repository root, check:

```bash
ls -l .github/workflows/pages.yml
git status --short
```

If the file exists locally but is absent from GitHub, commit and push it:

```bash
git add .github/workflows/pages.yml
git commit -m "Add course Pages workflow"
git push
```

If the file is already tracked, Git may correctly report nothing to commit; confirm you pushed the correct branch and remote instead. If GitHub shows the course files inside an extra nested directory, fix the repository layout so `.github/` and `docs/` are at the top level.

If an older copy of the workflow fails during Python setup with `No file ... matched to [**/requirements.txt or **/pyproject.toml]`, add `cache-dependency-path: requirements-dev.txt` beneath `cache: pip`, at the same indentation level. This repository uses a custom dependency filename, which must be named explicitly for caching ([setup-python caching documentation](https://github.com/actions/setup-python)).

```yaml
      - uses: actions/setup-python@v7
        with:
          python-version: "3.11"
          cache: pip
          cache-dependency-path: requirements-dev.txt
```

Commit the workflow change to `main` and inspect the new run. The corrected workflow is already included in this archive; no Pages source-setting change is needed for this error.

GitHub reports the final Pages address in the deployment. A project site normally sits under the repository name, so all internal assets and links use relative paths rather than assuming a domain-root deployment ([GitHub Pages documentation](https://docs.github.com/en/pages/getting-started-with-github-pages)).

For a branch-based alternative, the already-generated site can be published by selecting **Deploy from a branch**, choosing `main` and `/docs`, and clicking **Save** ([GitHub's branch-publishing instructions](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)). Use only one deployment method: disable the custom publishing workflow if switching to branch publishing, and rebuild and commit `docs/` after future source edits. GitHub Actions is the default supplied here.

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
│   ├── ligalign.py              # Owner's symmetry-aware ligand comparison
│   ├── struct_diff.py           # Owner's post-superposition difference viewer
│   ├── source-manifest.json     # Checksums of the unchanged supplied scripts
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

- **ligalign.py:** Paulo Martel's graph- and symmetry-aware ligand comparison, with distinct in-place and fitted RMSDs. By default it moves the whole mobile object; choose `fit=0` or `transform=0` for non-moving comparisons.
- **struct_diff.py:** Paulo Martel's pairwise geometric-difference colouring after superposition, with correspondence diagnostics and a TSV report option. It overwrites B-values in the working selections, so the examples use copies.

Both supplied scripts are unchanged, with source hashes recorded in `pymol_scripts/source-manifest.json`. Their embedded help remains authoritative; neither needs auxiliary files, and RDKit is optional for the ligand MCS route rather than the benzene graph-isomorphism example.

The examples are experimental non-MnMT4 references or explicitly transformed copies, not Boltz predictions. Numerical tests exercise the actual supplied pure functions with NumPy; optional `pymol2` integration tests exercise both tools and the real PyMOL command-line demonstrations.

For an existing checkout, see `UPDATE-PYMOL.md` for the small update archive and the two superseded files to remove. Do not overwrite your `.git` directory or change your working Pages configuration.

To create a fresh source ZIP after an update, run `python tools/package_repo.py`. It validates the site, then writes `CIBB_2026.zip` and its SHA-256 sidecar one directory above the repository, omitting Git history, local environments, caches and generated analysis reports.

## Add the practical later

Edit `content/practical.md`, add approved student files to the practical directories, and update `practical_status` in `course.json` when those materials have actually been tested. Run `python tools/build_site.py`; it will rebuild the page and copy the student practical files into the published downloads.

Keep unpublished research data and instructor solutions in a separate private location, not merely outside `docs/`. The entire GitHub repository is readable when the repository is public.

## Publication and provenance

The lecture includes the explicit PDB100 caveat: redundancy reduction does not guarantee one returned hit per unique amino-acid sequence. The exact cause of the saved monomer search's duplicate full-length myoglobin sequences is not asserted.

All included text files use UTF-8 and Unix LF line endings, including Python, PML, Markdown, HTML, CSS, JavaScript, JSON, YAML and the example coordinate files. `tools/check_repo.py` verifies those conditions, local links, slide availability and the absence of machine-specific paths.

The slide images and examples work without live prediction services. Fonts use an optional Fontshare CDN with local system fallbacks; external tool sites require network access and may require accounts or suitable compute.
