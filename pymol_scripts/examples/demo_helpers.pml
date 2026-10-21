# Run from the repository/toolkit root: @pymol_scripts/examples/demo_helpers.pml
# Coordinate-operation demo only: transformed copies are not independent models.
@pymol_scripts/startup.pml
load pymol_scripts/examples/lysozyme_benzene.pdb, reference
create mobile1, reference
rotate y, 32, mobile1
translate [9, 3, -4], mobile1
create mobile2, reference
rotate x, -27, mobile2
translate [-7, -4, 6], mobile2
hide everything
show cartoon, polymer.protein
show sticks, resn BNZ
color teal, reference
color salmon, mobile1
color marine, mobile2
ligand_align mobile1 and resn BNZ, reference and resn BNZ, output=ligand_fitted
class_multi_align reference, mobile1 mobile2, class_alignment
alignment_report class_alignment, analysis-results/demo, reference
disable mobile1
disable mobile2
zoom reference
