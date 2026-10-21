# Example structures

- `lysozyme_benzene.pdb`: protein chain A and BNZ from experimental T4 lysozyme L99A structure [4W52](https://www.rcsb.org/structure/4W52); buffer and water records excluded ([original coordinates](https://files.rcsb.org/download/4W52.pdb)).
- `myoglobin.pdb`: standard protein records from 1MBN chain A, heme excluded ([original coordinates](https://files.rcsb.org/download/1MBN.pdb)).
- `leghemoglobin.pdb`: protein records from 1FSL chain B, matching the lecture's returned Foldseek comparison ([original coordinates](https://files.rcsb.org/download/1FSL.pdb)).

These are teaching extracts of experimental references, not predictions. Preserve the entry citations in any reuse, and consult each original record for construct, ligand and experimental details.

The historical 1MBN source includes a Gln A8 CA-chirality warning, so use it for the global fold comparison, not a local stereochemical claim. The demo's displaced copies are deliberately synthetic transforms, not independently sampled conformations.

`demo_ligalign.pml` renames and displaces a benzene copy by 2 Å to distinguish in-place pose RMSD from fitted geometry. `demo_struct_diff.pml` superposes experimental globins with PyMOL CE alignment and colours working copies, preserving source B-values.

The local CE correspondence is not the lecture's stored TM-align mapping, and its RMSD must not be presented as a reproduction of the slide's alignment score. These PML files are convenience examples, not auxiliary dependencies of the standalone scripts.
