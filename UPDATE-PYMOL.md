# Update the existing course repository

This update replaces the initially generated helpers with Paulo Martel's supplied `ligalign.py` and `struct_diff.py`. The supplied Python files are unchanged, and the working GitHub Pages workflow is not altered by the incremental update.

## Recommended: apply the small update archive

Download `CIBB_2026-PyMOL-update.zip` and enter your existing local course repository. The following example extracts the update to a temporary directory and copies its `CIBB_2026/` contents into the current checkout:

```bash
# First cd into your EXISTING course repository.
git status --short
# Preserve any uncommitted work before merging overlapping files.
python3 -m zipfile -e /path/to/CIBB_2026-PyMOL-update.zip /tmp/cibb-pymol-update
cp -a /tmp/cibb-pymol-update/CIBB_2026/. .
```

The archive contains only the changed/new course files, including the already-built website and downloads. It contains no `.git/` directory and no `.github/workflows/` changes; copying it does not replace your Git history or working deployment configuration.

Remove the two superseded generated scripts:

```bash
git rm --ignore-unmatch pymol_scripts/ligand_align.py pymol_scripts/alignment_analysis.py
```

If either old file is untracked rather than tracked, remove that specific file manually as well. The repository validator checks that these obsolete files are absent.

Then review and publish the update:

```bash
git add -A
git diff --cached --stat
git commit -m "Use author-supplied PyMOL visualisation tools"
git push
```

The existing push-triggered Pages workflow will rebuild and deploy the site. No new Pages source selection is required.

## What changes

- `pymol_scripts/`: original author scripts, checksums, updated help and two demonstration PML files.
- `tools/`, `tests/` and maintainer notes: source-integrity checks, revised tests and the integration review.
- `content/notes.md`, generated pages and student downloads: correct tool names and usage distinctions.
- Course README: current repository tree and updated instructions.

The incremental archive does not change lecture PNG/SVG files, the practical's availability, scientific reference coordinates or the Pages workflow. For a fresh checkout, the separately supplied full `CIBB_2026.zip` contains the complete current repository instead.

## Check the tools locally

Start PyMOL from the repository root:

```pml
@pymol_scripts/examples/demo_ligalign.pml
@pymol_scripts/examples/demo_struct_diff.pml
```

Read `pymol_scripts/README.md` for the distinction between pose RMSD and fitted geometry, the B-value overwrite warning and sequence-viewer guidance. No MnMT4 model or practical answer has been added.
