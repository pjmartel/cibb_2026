# Experimental globin comparison. Colour copies, preserving source B-values.
@pymol_scripts/startup.pml
load pymol_scripts/examples/myoglobin.pdb, myoglobin_source
load pymol_scripts/examples/leghemoglobin.pdb, leghemoglobin_source
create myoglobin_view, myoglobin_source
create leghemoglobin_view, leghemoglobin_source
cealign myoglobin_view, leghemoglobin_view, object=globin_alignment
hide everything, myoglobin_view or leghemoglobin_view
show cartoon, myoglobin_view or leghemoglobin_view
struct_diff_pairs leghemoglobin_view, myoglobin_view, atoms=name CA, method=cealign, show=resi 20-23
python
import os
os.makedirs("analysis-results", exist_ok=True)
python end
struct_diff leghemoglobin_view, myoglobin_view, atoms=name CA, method=cealign, maximum=3.0, report=analysis-results/globins.tsv
disable myoglobin_source
disable leghemoglobin_source
disable benzene_*
set seq_view, 1
zoom myoglobin_view or leghemoglobin_view
