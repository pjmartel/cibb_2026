# Synthetic displacement of experimental benzene, not a predicted pose.
@pymol_scripts/startup.pml
load pymol_scripts/examples/lysozyme_benzene.pdb, benzene_complex_source
create benzene_ref, benzene_complex_source and resn BNZ
create benzene_mobile, benzene_ref
alter benzene_mobile, name="Q%d"%index
sort benzene_mobile
translate [0, 0, 2], benzene_mobile
hide everything, benzene_*
show sticks, benzene_ref or benzene_mobile
color teal, benzene_ref
color salmon, benzene_mobile
# Expect ~2 A in place, but ~0 A after a ligand-only fit.
ligalign benzene_mobile, benzene_ref, method=iso, fit=0, verbose=2
ligalign benzene_mobile, benzene_ref, method=iso, fit=1, transform=0
# Move a copy only. Preserve the displaced example.
create benzene_fit, benzene_mobile
ligalign benzene_fit, benzene_ref, method=iso, fit=1
show sticks, benzene_fit
color yellow, benzene_fit
disable benzene_complex_source
disable benzene_fit
zoom benzene_ref or benzene_mobile
