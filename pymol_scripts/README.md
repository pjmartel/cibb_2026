# PyMOL visualisation helpers

These scripts support inspection and explicitly defined coordinate operations. They do not dock ligands, infer chemical equivalence, generate AI structures or validate binding/catalysis.

## Setup

Install PyMOL from the [official download page](https://pymol.org/2/), checking your institution's licence arrangements. A separate [open-source edition](https://github.com/schrodinger/pymol-open-source) is available, including a [conda-forge package](https://anaconda.org/conda-forge/pymol-open-source).

One open-source environment option on Linux is:

```bash
conda create -n cibb2026 -c conda-forge python=3.11 pymol-open-source numpy
conda activate cibb2026
pymol
```

The packaged helpers were tested using open-source PyMOL 3.2 in Python 3.11. A graphical PyMOL installation and a headless `pymol2` environment are different execution contexts; use the GUI for the class.

From the repository root, start PyMOL and enter:

```pml
@pymol_scripts/startup.pml
```

If using the ZIP download, extract it first and start from its top-level directory. Alternatively use absolute paths in PyMOL's `run` command.

## Rigid ligand aligner

```pml
run pymol_scripts/ligand_align.py
ligand_align mobile and resn BNZ, reference and resn BNZ
```

With no atom map, both selections must have the same residue name and heavy-atom names. For different naming or different molecules, supply an explicit, one-to-one map of chemically equivalent atoms:

```pml
ligand_align mobile_ligand, reference_ligand, C1:C7|C2:C8|O1:O2, fitted_ligand, ligand
```

The syntax is:

```text
ligand_align mobile, reference, pairs="", output=ligand_fitted, scope=object, state=1
```

- `scope=object` makes a new single-state copy of the complete mobile object and moves it as one rigid body, preserving protein–ligand geometry.
- `scope=ligand` copies only the selected ligand residue.
- At least three non-collinear heavy-atom pairs are required; duplicate names, ambiguous conformers and element mismatches are rejected.
- Inputs are not overwritten. Choose a fresh output name for every run.
- The RMSD is for the mapped atom set after fitting. It is not docking accuracy, affinity or a reaction score.

Atom-name agreement is only a convenience, not a proof of equivalent chemistry. Symmetric molecules can have several valid correspondences; this tool does not enumerate graph automorphisms or identify a minimum over them.

Use `|` between pairs in PyMOL command lines. Python calls also accept `;`, but an unquoted semicolon is a command separator in PyMOL.

## Multiple-alignment analysis

```pml
run pymol_scripts/alignment_analysis.py
class_multi_align reference, mobile1 mobile2, class_alignment
alignment_report class_alignment, analysis-results/alignment, reference
```

`class_multi_align` creates fitted mobile copies with the `fit_` prefix and a CA alignment object, leaving the input mobiles unchanged. It uses PyMOL's sequence-based `align` with no outlier rejection, so it is not a replacement for a structural-search or distant-fold alignment method ([PyMOL align documentation](https://pymolwiki.org/index.php/Align)).

The helper builds reference-anchored columns: unmatched reference positions have missing mobile entries, while mobile insertions without a reference position are omitted. Use single-state objects, or first copy the state you want to inspect into state 1.

CA fitting uses blank/A alternate locations, so alternative atoms are not counted twice as distinct residues. For another conformer choice, prepare a single-conformer source object first; the report rejects repeated CA residue positions.

You may instead provide an existing CA alignment object containing two or more models:

```text
alignment_report alignment=class_alignment, prefix=analysis-results/alignment, reference="", state=1
```

Outputs are:

- `.columns.csv`: occupancy, residue-name consensus, agreement fraction, RMS coordinate dispersion and distances to the specified reference.
- `.pairs.csv`: CA RMSD over each pair's common columns, in the current frame, with no additional fit.
- `.summary.json`: model names, reference, column count and interpretation warnings.

Missing residues are reported as absent rather than zero distance. Dispersion depends on alignment and superposition; it is not a flexibility, dynamics or confidence measurement. Residue-name agreement among selected structures is not a population-based evolutionary conservation score.

## Try the bundled demo

```pml
@pymol_scripts/examples/demo_helpers.pml
```

The demo makes displaced copies of the same experimental lysozyme–benzene reference and fits them back. Near-zero RMSDs verify the coordinate operations; they do not demonstrate independent predictive accuracy.

The separate myoglobin and leghemoglobin files are available for inspecting real structural differences. No MnMT4 structure, ligand pose or practical answer is included.
