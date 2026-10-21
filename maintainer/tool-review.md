# PyMOL tools: integration and usage review

The class now uses the course owner's supplied scripts, without code edits. The former generated helpers have been removed from the repository and student toolkit; SHA-256 checks verify that both new files, individual downloads and ZIP members match the uploaded sources.

## ligalign.py

The implementation is appropriate for the intended benzene comparison. It searches graph-based heavy-atom correspondences, includes molecular symmetry, and distinguishes an in-place calculation from a new rigid-body fit.

- **Classroom comparison:** Superpose the proteins first and use `method=iso, fit=0` to assess the ligand in the protein-aligned frame.
- **Separate geometry question:** Use `fit=1, transform=0` to calculate a best-fitted ligand RMSD without modifying its coordinates.
- **Movement:** Default `fit=1, transform=1` moves every atom of the selected mobile object's state, including a protein if the ligand belongs to a complex object.
- **Dependencies:** NumPy is imported unconditionally; RDKit is optional for the MCS route and is not needed for the benzene example.
- **Scope:** Default matching ignores hydrogens and bond orders. Name/order fallbacks are not a chemical-equivalence guarantee; MCS can return a partial match, and enumeration caps limit exhaustive claims.

The local PyMOL test renamed benzene atoms, shifted a copy by 2 Å, and evaluated twelve symmetry-equivalent isomorphisms. It returned approximately 2 Å in place and approximately zero after a ligand-only fit, while `transform=0` preserved coordinates.

The tests also verified movement of the whole mobile complex, preservation of the reference, the distance-derived connectivity retry after a missing bond, and all-state evaluation with a single-state target. These are transformed experimental copies, not independent predictions or a Boltz accuracy benchmark.

## struct_diff.py

This is a post-superposition pairwise comparison and colour-mapping tool, not a multiple-structure alignment engine. It can use PyMOL aligners to establish correspondence without changing the current placement; its spatial method instead uses mutual-nearest CA positions within a radius.

- **Globin demonstration:** Use CA atoms with CE-based pairing, inspect `struct_diff_pairs`, then colour working copies with `struct_diff`.
- **Stored data:** Both working selections have their B-values overwritten. The demonstration preserves original source objects.
- **Sequence interpretation:** Geometric colouring does not separately encode substitutions; inspect sequence letters and the paired residue names in the diagnostic or TSV.
- **Unmatched positions:** Green and B-value `-1` mean unmatched, not zero deviation. A spatial radius or positive cutoff can exclude the most displaced positions.
- **Colour ramp:** A fixed maximum keeps displays comparable but does not replace the numerical values in the report.

Using the supplied experimental myoglobin and leghemoglobin extracts, this local CE calculation gave 136 CA pairs and an overall current-frame RMSD of approximately 2.862 Å. The TSV and diagnostic include residue-name differences, for example leghemoglobin ASN 21 paired with myoglobin ASP 20 under this particular correspondence.

This calculation is deliberately distinct from the lecture's saved TM-align result; different methods and correspondence definitions must not be presented as identical. The experimental references remain [1MBN](https://www.rcsb.org/structure/1MBN) and [1FSL](https://www.rcsb.org/structure/1FSL), with the existing historical-coordinate caveat retained.

## Validation and limits

Tests cover the numerical functions, symmetry/atom-order case, source hashes, PyMOL state handling, coordinate preservation, missing-bond retry, globin colouring/reporting, diagnostic non-modification, unmatched-radius behaviour and real PML command lines. The baseline environment is open-source PyMOL 3.2 with Python 3.11.

RDKit-dependent MCS and hydrogen-inclusive matching are not part of the required classroom checks and were not exercised in this environment. No universal chemical-correctness guarantee is inferred from the tests, and no experimental-versus-Boltz pose was computed during this integration.

The supplied Python files were not modified. Only documentation, surrounding example command files, tests, packaging and the website were changed.
