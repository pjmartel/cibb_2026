# PyMOL visualisation tools

The class uses **Paulo Martel's supplied `ligalign.py` and `struct_diff.py`**, preserved byte-for-byte. No auxiliary data files are required by either script; the bundled structures and command files are optional teaching examples.

## Setup and help

Get PyMOL from the [official download page](https://pymol.org/2/), checking your institution's licence arrangements. A separate [open-source edition](https://github.com/schrodinger/pymol-open-source) is available, including a [conda-forge package](https://anaconda.org/conda-forge/pymol-open-source).

One open-source environment option on Linux is:

```bash
conda create -n cibb2026 -c conda-forge python=3.11 pymol-open-source numpy
conda activate cibb2026
pymol
```

`ligalign.py` imports NumPy. RDKit is optional, only for its maximum-common-substructure route; the benzene example uses graph isomorphism without RDKit.

Start PyMOL from the repository root, or the directory containing the extracted `pymol_scripts/` folder, then enter:

```pml
@pymol_scripts/startup.pml
help ligalign
help struct_diff
help struct_diff_pairs
```

Alternatively, run either standalone script directly with `run path/to/script.py`. The script headers contain the original help and attribution; references there to other manuals or commands are not runtime dependencies.

## ligalign: symmetry-aware ligand comparison

`ligalign` derives atom correspondence from molecular graphs, rather than assuming identical atom names or order. For two benzene molecules, the isomorphism route evaluates the ring's symmetry-equivalent mappings; `method=iso` is a useful classroom choice because it prevents a silent fallback to names or atom order.

### Pose RMSD versus fitted geometry

For an experimental-versus-predicted complex comparison, first superpose the proteins, preserving each protein's ligand placement. Then evaluate the ligands **without another fit**:

```pml
# Template for your own loaded complexes, not a bundled Boltz prediction:
super predicted_complex and polymer.protein, experimental_complex and polymer.protein
ligalign predicted_complex and resn BNZ, experimental_complex and resn BNZ, method=iso, fit=0, verbose=2
```

This is symmetry-aware ligand RMSD in the protein-aligned coordinate frame. Check the protein correspondence, selections, states and the reported six paired benzene heavy atoms.

To ask a different question, how similar the ligand geometries are after their own best rigid fit, use:

```pml
ligalign predicted_complex and resn BNZ, experimental_complex and resn BNZ, method=iso, fit=1, transform=0
```

`transform=0` calculates the fitted RMSD without moving the model. A small fitted-geometry RMSD does not establish a correct pose in the binding pocket.

### Movement and matching rules

- The default is `fit=1, transform=1`: it moves the **whole mobile object**, not just the selected ligand. Work on a copy, or use `fit=0` / `transform=0` as appropriate.
- The default ignores hydrogens and bond orders; it uses blank/A alternate locations. This accommodates unreliable PDB bond orders, but is not a stereochemical or protonation validation.
- `method=auto` tries graph isomorphism, a distance-derived connectivity retry, optional RDKit MCS, then name/order fallbacks. Inspect the printed method rather than assuming every auto result is graph-verified.
- MCS RMSD concerns the common subset, not necessarily the whole ligand. RDKit must be installed in the same Python environment as PyMOL for that route.
- `max_matches` limits enumeration; a cap warning means exhaustive symmetry search was not established. Do not promise a global minimum for arbitrary molecules after reaching that cap.
- `mobile_state=0` evaluates all mobile states. Give explicit state numbers if the current frame is ambiguous.

## struct_diff: colour local structural differences

`struct_diff` compares **two already superposed structures**; it does not move or fit them. It colours per-residue RMS deviations or per-atom displacements, and `struct_diff_pairs` lets you inspect the correspondence before colouring.

The globin example uses CA atoms and CE-based pairing, with no distance cutoff. This avoids making a geometric comparison depend on shared side-chain atom names or removing distant pairs with a cutoff:

```pml
load pymol_scripts/examples/myoglobin.pdb, myoglobin_source
load pymol_scripts/examples/leghemoglobin.pdb, leghemoglobin_source
create myoglobin_view, myoglobin_source
create leghemoglobin_view, leghemoglobin_source
cealign myoglobin_view, leghemoglobin_view, object=globin_alignment
struct_diff_pairs leghemoglobin_view, myoglobin_view, atoms=name CA, method=cealign, show=resi 20-23
struct_diff leghemoglobin_view, myoglobin_view, atoms=name CA, method=cealign, maximum=3.0
set seq_view, 1
```

`cealign` takes **target first, mobile second**; `struct_diff` takes **mobile first, target second**. This local CE comparison is not the lecture's saved TM-align computation, so its numerical result need not be identical.

### Interpretation and data preservation

- **B-values are overwritten in both compared selections.** Keep the source objects untouched and colour copies, especially when B-values hold experimental displacement factors or prediction confidence.
- Blue-to-red is geometric deviation on the chosen ramp, not sequence identity, flexibility, energy or confidence. With `atoms=name CA` and residue mode, the residue colour represents its paired CA displacement.
- Sequence substitutions can be inspected in the sequence viewer and in the residue names printed by `struct_diff_pairs` or written to its report. The script does not separately colour substitutions or calculate an evolutionary conservation score.
- Default `method=spatial` proposes mutual-nearest CA pairs only within `radius=3.0`. A large displacement can therefore become **unmatched**, not a large red value.
- Unmatched atoms are green by default and have B-value `-1`; unmatched is not zero deviation. A positive `cutoff` also excludes distant pairs, so report those choices.
- `maximum=3.0` fixes the displayed ramp at 0–3 Å; it does not truncate the values stored in B-factors or the report.
- `report=path/to/globins.tsv` writes a residue table. Create its parent directory first, and use a fresh filename if you need to preserve an earlier report.

## Run the supplied demonstrations

Use a fresh session for the example object names:

```pml
@pymol_scripts/examples/demo_ligalign.pml
@pymol_scripts/examples/demo_struct_diff.pml
```

Or run both with `@pymol_scripts/examples/demo_helpers.pml`. The benzene demo deliberately displaces and renames a copy of the same experimental molecule; it is a coordinate/mapping test, **not Boltz output** or an independent accuracy benchmark.

The scripts are standalone; these PML files only save typing. No MnMT4 model, ligand pose or practical answer is included.
