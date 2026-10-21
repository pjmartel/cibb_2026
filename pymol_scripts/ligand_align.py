"""Rigid ligand fitting from explicit atom correspondences, without docking.

PyMOL: run pymol_scripts/ligand_align.py
       ligand_align mobile and resn BNZ, reference and resn BNZ
       ligand_align mob_lig, ref_lig, C1:C7;C2:C8;O1:O2, fitted, ligand

The default creates a single-state copy of the complete mobile object.
Choose scope=ligand to copy and fit only the selected ligand.
"""
import numpy as np

try:
    from pymol import cmd
except ImportError:
    cmd = None


def rigid_fit(mobile, reference):
    """Return proper row-vector rotation, translation and mapped-atom RMSD."""
    x = np.asarray(mobile, dtype=float)
    y = np.asarray(reference, dtype=float)
    if x.shape != y.shape or x.ndim != 2 or x.shape[1] != 3 or len(x) < 3:
        raise ValueError("Provide at least three matched 3D atom pairs.")
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("Coordinates must be finite.")
    xc, yc = x - x.mean(axis=0), y - y.mean(axis=0)
    if np.linalg.matrix_rank(xc) < 2 or np.linalg.matrix_rank(yc) < 2:
        raise ValueError("The matched atoms must not be collinear.")
    u, _, vt = np.linalg.svd(xc.T @ yc)
    correction = np.eye(3)
    correction[-1, -1] = 1.0 if np.linalg.det(u @ vt) >= 0 else -1.0
    rotation = u @ correction @ vt
    translation = y.mean(axis=0) - x.mean(axis=0) @ rotation
    rmsd = float(np.sqrt(np.mean(np.sum((x @ rotation + translation - y) ** 2, axis=1))))
    return rotation, translation, rmsd


def _ligand(selection, state):
    atoms = [a for a in cmd.get_model(f"({selection}) and not hydro", state).atom]
    if not atoms:
        raise ValueError(f"No heavy atoms in selection: {selection}")
    residues = {(a.segi, a.chain, a.resi, a.resn) for a in atoms}
    if len(residues) != 1:
        raise ValueError("Each ligand selection must contain exactly one residue.")
    by_name = {a.name: a for a in atoms}
    if len(by_name) != len(atoms):
        raise ValueError("Atom names are ambiguous. Select one alternate conformer first.")
    return atoms, by_name


def ligand_align(mobile, reference, pairs="", output="ligand_fitted", scope="object", state=1):
    """Fit a copy using name-pairs; no bond optimisation or inferred chemistry."""
    if cmd is None:
        raise RuntimeError("Run this command inside PyMOL.")
    state = int(state)
    scope = str(scope).strip()
    if scope not in ("object", "ligand"):
        raise ValueError("scope must be object or ligand.")
    if not output or not str(output).replace("_", "").isalnum():
        raise ValueError("Use a simple, nonempty output object name.")
    if output in cmd.get_names("all"):
        raise ValueError(f"Output already exists: {output}; choose a new name.")
    objects = cmd.get_object_list(f"({mobile})")
    if len(objects) != 1:
        raise ValueError("The mobile selection must belong to exactly one object.")
    _, ma = _ligand(mobile, state)
    _, ra = _ligand(reference, state)
    pairs = "" if pairs is None else str(pairs).strip()
    if pairs in ("None", "''", '""'):
        pairs = ""
    if len(pairs) >= 2 and pairs[0] == pairs[-1] and pairs[0] in ("'", '"'):
        pairs = pairs[1:-1]
    if pairs:
        mapping = []
        for token in pairs.replace("|", ";").split(";"):
            pieces = token.strip().split(":")
            if len(pieces) != 2:
                raise ValueError("Atom pairs use mobile:reference|mobile:reference syntax.")
            mapping.append(tuple(piece.strip() for piece in pieces))
    else:
        if set(ma) != set(ra) or {a.resn for a in ma.values()} != {a.resn for a in ra.values()}:
            raise ValueError("Different ligands or naming: provide a chemically justified explicit atom map.")
        mapping = [(name, name) for name in sorted(ma)]
    if len({m for m, _ in mapping}) != len(mapping) or len({r for _, r in mapping}) != len(mapping):
        raise ValueError("Atom mapping must be one-to-one.")
    for m, r in mapping:
        if m not in ma or r not in ra:
            raise ValueError(f"Unknown atom name in pair {m}:{r}")
        if ma[m].symbol != ra[r].symbol:
            raise ValueError(f"Element mismatch in pair {m}:{r}")
    x = np.array([ma[m].coord for m, _ in mapping])
    y = np.array([ra[r].coord for _, r in mapping])
    rotation, translation, rmsd = rigid_fit(x, y)
    source = objects[0] if scope == "object" else f"({mobile})"
    cmd.create(output, source, source_state=state, target_state=1)
    coordinates = cmd.get_coords(output, state=1)
    cmd.load_coords(coordinates @ rotation + translation, output, state=1)
    cmd.group("class_fits", output)
    result = {"output": output, "scope": scope, "atom_pairs": mapping, "n_pairs": len(mapping),
              "mapped_atom_rmsd_A": rmsd, "rotation": rotation.tolist(),
              "translation": translation.tolist()}
    print(f"{output}: {len(mapping)} mapped heavy atoms; rigid-fit RMSD = {rmsd:.4f} A.")
    print("Inputs preserved. Atom-name agreement is not proof of chemical equivalence or binding.")
    return result


if cmd is not None:
    cmd.extend("ligand_align", ligand_align)
