"""Analyse CA alignment objects; coordinate dispersion is not dynamics.

PyMOL: run pymol_scripts/alignment_analysis.py
       class_multi_align reference, mobile1 mobile2
       alignment_report class_alignment, analysis-results/alignment
"""
from collections import Counter
from itertools import combinations
from pathlib import Path
import csv
import json
import numpy as np

try:
    from pymol import cmd
except ImportError:
    cmd = None


def column_metrics(coordinates, residues):
    """Unweighted occupancy-local RMS spread and residue-name agreement."""
    xyz = np.asarray(coordinates, dtype=float)
    if xyz.ndim != 2 or xyz.shape[1] != 3 or not len(xyz):
        raise ValueError("Expected a nonempty set of 3D coordinates.")
    if len(xyz) != len(residues) or not np.isfinite(xyz).all():
        raise ValueError("Residue and finite-coordinate counts must agree.")
    consensus, count = sorted(Counter(residues).items(), key=lambda v: (-v[1], v[0]))[0]
    spread = float(np.sqrt(np.mean(np.sum((xyz - xyz.mean(axis=0)) ** 2, axis=1))))
    return {"consensus_resn": consensus, "consensus_fraction": count / len(residues),
            "ca_rms_dispersion_A": spread}


def class_multi_align(reference, mobiles, alignment="class_alignment", state=1):
    """Sequence-based CA fits of new mobile copies to one unchanged reference."""
    if cmd is None:
        raise RuntimeError("Run this command inside PyMOL.")
    state = int(state)
    if state != 1:
        raise ValueError("For this helper use single-state objects; copy the desired source state to state 1 first.")
    names = [n for n in str(mobiles).replace(",", " ").split() if n]
    if not names or len(names) != len(set(names)) or reference in names:
        raise ValueError("Provide distinct mobile object names, excluding the reference.")
    known = cmd.get_names("objects")
    if reference not in known or any(n not in known for n in names):
        raise ValueError("Use existing object names, not arbitrary selections.")
    outputs = ["fit_" + n for n in names]
    if alignment in cmd.get_names("all") or any(n in cmd.get_names("all") for n in outputs):
        raise ValueError("An output name exists; use fresh object/alignment names.")
    ca_selection = "polymer.protein and name CA and (alt ''+A)"
    reference_atoms = cmd.get_model(f"{reference} and {ca_selection}", state).atom
    if not reference_atoms:
        raise ValueError("No reference CA atoms in the blank/A conformer selection.")
    merged = {a.index: {reference: a.index} for a in reference_atoms}
    temporary = [alignment + "__pair_" + str(i) for i in range(len(names))]
    if any(name in cmd.get_names("all") for name in temporary):
        raise ValueError("A temporary alignment name exists; choose a fresh alignment prefix.")
    for original, output, pair_name in zip(names, outputs, temporary):
        cmd.create(output, original, source_state=state, target_state=1)
        cmd.align(f"{output} and {ca_selection}",
                  f"{reference} and {ca_selection}",
                  cycles=0, object=pair_name, reset=1, mobile_state=1, target_state=state)
        for col in cmd.get_raw_alignment(pair_name):
            ref_index = next((index for name, index in col if name == reference), None)
            mob_index = next((index for name, index in col if name == output), None)
            if ref_index in merged and mob_index is not None:
                merged[ref_index][output] = mob_index
        cmd.delete(pair_name)
    columns = [[(name, values[name]) for name in [reference] + outputs if name in values]
               for values in merged.values()]
    cmd.set_raw_alignment(alignment, columns)
    print(f"Created {alignment} using {len(outputs)} mobile copies; original mobiles are preserved.")
    print("Reference-anchored, sequence-based CA alignment; mobile insertions without a reference position are omitted.")
    return outputs


def alignment_report(alignment="class_alignment", prefix="analysis-results/alignment", reference="", state=1):
    """Export columns, pairwise common-column distances, and a summary."""
    if cmd is None:
        raise RuntimeError("Run this command inside PyMOL.")
    state = int(state)
    raw = cmd.get_raw_alignment(alignment)
    if not raw:
        raise ValueError("No alignment columns found.")
    object_names = sorted({name for col in raw for name, _ in col})
    if len(object_names) < 2:
        raise ValueError("At least two aligned objects are required.")
    reference = reference or object_names[0]
    if reference not in object_names:
        raise ValueError("Reference object must be present in the alignment.")
    atoms = {
        name: {a.index: a for a in cmd.get_model(name, state).atom}
        for name in object_names
    }
    rows, entries, seen_positions = [], [], set()
    for column in raw:
        chosen = {}
        for name, index in column:
            atom = atoms[name].get(index)
            if atom is None or atom.name != "CA":
                continue
            if name in chosen:
                raise ValueError("More than one CA from an object in one column; inspect alignment/alternate atoms.")
            position = (name, atom.segi, atom.chain, atom.resi)
            if position in seen_positions:
                raise ValueError("Repeated CA residue across columns; resolve alternate conformers or duplicate columns first.")
            seen_positions.add(position)
            chosen[name] = atom
        if not chosen:
            continue
        metrics = column_metrics([a.coord for a in chosen.values()], [a.resn for a in chosen.values()])
        row = {"column": len(rows) + 1, "represented_models": len(chosen),
               "total_models": len(object_names), "occupancy": len(chosen) / len(object_names), **metrics}
        ref = chosen.get(reference)
        for name in object_names:
            atom = chosen.get(name)
            row[f"{name}_residue"] = f"{atom.chain}:{atom.resn}{atom.resi}" if atom else ""
            row[f"{name}_distance_to_reference_A"] = (
                float(np.linalg.norm(np.asarray(atom.coord) - ref.coord)) if atom is not None and ref is not None else ""
            )
        rows.append(row)
        entries.append(chosen)
    if not rows:
        raise ValueError("No CA-containing columns; build or select a protein CA alignment.")
    pair_rows = []
    for a, b in combinations(object_names, 2):
        common = [(col[a], col[b]) for col in entries if a in col and b in col]
        if not common:
            continue
        distances = np.array([np.linalg.norm(np.asarray(x.coord) - y.coord) for x, y in common])
        pair_rows.append({"object_a": a, "object_b": b, "common_CA_columns": len(common),
                          "current_frame_CA_rmsd_A": float(np.sqrt(np.mean(distances ** 2))),
                          "residue_name_agreement_fraction": sum(x.resn == y.resn for x, y in common) / len(common)})
    if not pair_rows:
        raise ValueError("No jointly aligned CA columns between any pair of objects.")
    out = Path(prefix).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    for suffix, data in ((".columns.csv", rows), (".pairs.csv", pair_rows)):
        with Path(str(out) + suffix).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(data[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(data)
    summary = {"alignment": alignment, "reference": reference, "objects": object_names,
               "CA_columns": len(rows), "pairwise": pair_rows,
               "interpretation": "Coordinates are measured in the current superposed frame; no refit in this report.",
               "caveat": "Dispersion is not dynamics/confidence; residue agreement is not an evolutionary conservation score."}
    Path(str(out) + ".summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Exported {len(rows)} CA columns and {len(pair_rows)} pairs to {out}.*")
    return summary


if cmd is not None:
    cmd.extend("class_multi_align", class_multi_align)
    cmd.extend("alignment_report", alignment_report)
