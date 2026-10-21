"""
ligalign.py -- symmetry-aware superposition and RMSD of small molecules in PyMOL
================================================================================

Superimposes two small molecules and reports the RMSD, without relying on atom
names or atom order. The atom correspondence is derived from the molecular
graphs (element + connectivity), and every symmetry-equivalent correspondence
is evaluated so the reported RMSD is the minimum over molecular symmetry
(e.g. flipped phenyl rings, carboxylate oxygens, sulfonyl oxygens).

Matching strategies, tried in order when method=auto:

  1. iso   exact graph isomorphism on heavy atoms (pure Python, no extra deps).
           Insensitive to names, order, and to differences in explicit H.
           If the bonds stored in PyMOL are not isomorphic (e.g. a PDB file
           with incomplete CONECT records), it is retried once with
           connectivity re-derived from interatomic distances.
  2. mcs   maximum common substructure via RDKit (only if RDKit is importable
           inside PyMOL's Python). Used when the heavy-atom graphs differ
           (missing atoms, analogues, different ligands sharing a scaffold).
           The RMSD is then over the common subset only, and this is reported.
  3. name  atoms paired by identical atom name (and element).
  4. order atoms paired by order of appearance (same element required).

Usage in PyMOL
--------------
    run ligalign.py
    ligalign mobile, target
    ligalign lig_pose, lig_xtal, fit=0             # docking-style RMSD, no move
    ligalign poses, ref, mobile_state=0, fit=0     # every state of 'poses'
    ligalign lig1, lig2, hydrogens=1, show_pairs=1, verbose=2

Arguments
---------
    mobile        selection/object that is moved (its whole object is moved)
    target        reference selection/object (never moved)
    method        auto | iso | mcs | name | order        (default: auto)
    fit           1 = superimpose, mapping chosen to minimise fitted RMSD
                  0 = do not move; mapping chosen to minimise in-place RMSD
                      (the usual definition for docking pose RMSD)
    hydrogens     0 = heavy atoms only (default). H atoms are ignored entirely,
                      also for matching, so the two oxygens of COOH/COO-, NO2,
                      etc. are treated as equivalent (on the molecules I
                      tested this reproduces RDKit's CalcRMS/GetBestRMS
                      with default options).
                  1 = H-aware matching (attached-H counts used in the atom
                      labels, falling back to H-blind if that fails); H atoms
                      are paired per matched heavy atom (iterated with the
                      fit) and included in the fit/RMSD
    bond_order    1 = require identical PyMOL bond orders in iso/mcs matching.
                      Off by default: bond orders from PDB files are unreliable,
                      and Kekule bond patterns would forbid phenyl ring flips.
    mobile_state  state of mobile (default -1 = current; 0 = loop over all
                  states, reporting one RMSD per state)
    target_state  state of target (default -1 = current)
                  With -1, single-state objects are always read from state 1.
    transform     1 = actually move the mobile object when fit=1 (default 1)
    max_matches   cap on symmetry-equivalent mappings enumerated (default 20000)
    mcs_timeout   seconds allowed for RDKit FindMCS (default 10)
    complete_rings  1 = MCS may not break rings (default 1)
    show_pairs    1 = create distance object '<name>' linking paired atoms
    name          name of the distance object (default 'ligalign_pairs')
    verbose       0 quiet, 1 summary (default), 2 summary + atom pair table

Return value (API): RMSD as float (fit=1: fitted; fit=0: in-place), or a list
of floats when mobile_state=0.

Python API:  cmd.ligalign("mobile", "target", fit=1)

Notes
-----
* Alternate locations: only '' and 'A' altlocs are used.
* The RMSD after fit equals what PyMOL's pair_fit would report for the same
  atom pairs (Kabsch, unweighted, no outlier rejection, no cycles).
"""

import importlib.util
import itertools

import numpy as np
from pymol import cmd, CmdException

_HYDROGENS = ("H", "D")


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def _boolarg(x):
    if isinstance(x, str):
        return x.strip().lower() in ("1", "true", "yes", "on")
    return bool(x)


def _element(atom):
    sym = (atom.symbol or "").strip()
    if not sym:  # fall back on the atom name
        sym = "".join(c for c in atom.name if c.isalpha())[:1]
    return sym.capitalize()


def _kabsch(P, Q):
    """Best rotation R and translation t such that P @ R.T + t ~ Q.
    Returns (rmsd_after_fit, R, t)."""
    pc, qc = P.mean(0), Q.mean(0)
    P0, Q0 = P - pc, Q - qc
    H = P0.T @ Q0
    U, S, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    D = np.diag([1.0, 1.0, d])
    R = Vt.T @ D @ U.T
    t = qc - pc @ R.T
    diff = P0 @ R.T - Q0
    rmsd = np.sqrt((diff * diff).sum() / len(P))
    return rmsd, R, t


def _apply_transform(obj, R, t, state):
    """x' = R x + t on all atoms of obj in one state."""
    M = np.eye(4)
    M[:3, :3], M[:3, 3] = R, t
    try:
        cmd.transform_selection(obj, M.flatten().tolist(), state=state,
                                homogenous=1)
    except TypeError:  # very old PyMOL without the homogenous argument
        Rl, tl = R.tolist(), t.tolist()
        cmd.alter_state(state, obj,
                        "(x, y, z) = (r[0][0]*x + r[0][1]*y + r[0][2]*z + t[0],"
                        " r[1][0]*x + r[1][1]*y + r[1][2]*z + t[1],"
                        " r[2][0]*x + r[2][1]*y + r[2][2]*z + t[2])",
                        space={"r": Rl, "t": tl})


def _rmsd(P, Q):
    d = P - Q
    return float(np.sqrt((d * d).sum() / len(P)))


# --------------------------------------------------------------------------
# molecule container
# --------------------------------------------------------------------------
# single-bond covalent radii (A), Cordero et al., Dalton Trans. 2008, 2832
_COVRAD = {"H": 0.31, "D": 0.31, "B": 0.84, "C": 0.76, "N": 0.71, "O": 0.66,
           "F": 0.57, "Si": 1.11, "P": 1.07, "S": 1.05, "Cl": 1.02,
           "Se": 1.20, "Br": 1.20, "I": 1.39}


def _distance_bonds(atoms, tol=0.45):
    """Bonds from interatomic distances (bond order unknown -> 1).
    Each H is attached only to its nearest bonded partner."""
    X = np.array([a.coord for a in atoms], float)
    el = [_element(a) for a in atoms]
    r = np.array([_COVRAD.get(e, 1.5) for e in el])
    D = np.linalg.norm(X[:, None] - X[None], axis=2)
    B = (D < r[:, None] + r[None] + tol) & (D > 0.4)
    isH = np.array([e in _HYDROGENS for e in el])
    bonds = set()
    for i in range(len(atoms)):
        for j in np.nonzero(B[i])[0]:
            if j <= i or (isH[i] and isH[j]):
                continue
            if isH[i] or isH[j]:
                h = i if isH[i] else j
                cand = np.nonzero(B[h] & ~isH)[0]
                if not len(cand) or cand[np.argmin(D[h, cand])] != (j if h == i
                                                                     else i):
                    continue
            bonds.add((i, j, 1))
    return sorted(bonds)


def _resolve_state(selection, state):
    """state -1 -> the current state, except that single-state objects are
    always read from state 1 (as displayed with static_singletons)."""
    state = int(state)
    if state != -1:
        return state
    objs = cmd.get_object_list("(%s)" % selection) or []
    n = max([cmd.count_states(o) for o in objs] or [1])
    if n <= 1:
        return 1
    cur = cmd.get_state()
    if cur > n:
        raise CmdException("ligalign: current state %d does not exist in '%s' "
                           "(%d states); pass an explicit state" %
                           (cur, selection, n))
    return cur


def _get_atoms(selection, state):
    """Atoms, bonds and (object, index) identifiers of a selection.

    Uses only long-standing chempy attributes (symbol, name, coord,
    bond.index, bond.order). The object name and atom index come from
    cmd.iterate, done one object at a time, and are cross-checked against the
    get_model atom list so a different ordering cannot go unnoticed."""
    objs = cmd.get_object_list("(%s)" % selection) or []
    atoms, bonds, ident = [], [], []
    for obj in objs:
        osel = "(%s) and (%s)" % (selection, obj)
        model = cmd.get_model(osel, state=state)
        if not model.atom:
            continue
        info = []
        cmd.iterate(osel, "info.append((index, name))", space={"info": info})
        if (len(info) != len(model.atom) or
                any(n != a.name for (_, n), a in zip(info, model.atom))):
            raise CmdException("ligalign: atom order from get_model and "
                               "iterate differ for '%s'; please report your "
                               "PyMOL version" % obj)
        off = len(atoms)
        atoms.extend(model.atom)
        ident.extend((obj, idx) for idx, _ in info)
        bonds.extend((b.index[0] + off, b.index[1] + off, b.order)
                     for b in model.bond)
    return atoms, bonds, ident, objs


class _Mol:
    def __init__(self, selection, state, geom=False):
        sel = "(%s) and (alt ''+A)" % selection
        atoms, file_bonds, ident, objs = _get_atoms(sel, state)
        if not atoms:
            raise CmdException("ligalign: selection '%s' (state %s) is empty"
                               % (selection, state))
        self.objects = sorted({o for o, _ in ident})
        heavy = [i for i, a in enumerate(atoms) if _element(a) not in _HYDROGENS]
        if not heavy:
            raise CmdException("ligalign: no heavy atoms in '%s'" % selection)
        remap = {old: new for new, old in enumerate(heavy)}
        self.n = len(heavy)
        self.elem = [_element(atoms[i]) for i in heavy]
        self.name = [atoms[i].name for i in heavy]
        self.ident = [ident[i] for i in heavy]
        self.xyz = np.array([atoms[i].coord for i in heavy], float)
        self.adj = [dict() for _ in range(self.n)]   # heavy-atom graph
        self.hyd = [[] for _ in range(self.n)]      # attached H: (ident, name, xyz)
        bonds = (_distance_bonds(atoms) if geom else
                 file_bonds)
        self.geom = geom
        for i, j, order in bonds:
            hi, hj = i in remap, j in remap
            if hi and hj:
                self.adj[remap[i]][remap[j]] = order
                self.adj[remap[j]][remap[i]] = order
            elif hi != hj:
                h, p = (j, i) if hi else (i, j)
                a = atoms[h]
                self.hyd[remap[p]].append((ident[h], a.name,
                                           np.array(a.coord, float)))
        self.nbonds = sum(len(x) for x in self.adj) // 2


# --------------------------------------------------------------------------
# strategy 1: graph isomorphism (all symmetry-equivalent mappings)
# --------------------------------------------------------------------------
def _refined_labels(mols, bond_order, hcount):
    """Joint colour refinement (1-WL) so labels are comparable across mols."""
    labels = [[(m.elem[i], len(m.adj[i]), len(m.hyd[i]) if hcount else 0)
               for i in range(m.n)] for m in mols]
    table = {}
    labels = [[table.setdefault(l, len(table)) for l in L] for L in labels]
    nclass = len(table)
    for _ in range(max(m.n for m in mols)):
        table = {}
        new = []
        for m, L in zip(mols, labels):
            row = []
            for i in range(m.n):
                nb = sorted((L[j], o if bond_order else 0)
                            for j, o in m.adj[i].items())
                row.append(table.setdefault((L[i], tuple(nb)), len(table)))
            new.append(row)
        labels = new
        if len(table) == nclass:
            break
        nclass = len(table)
    return labels


def _isomorphisms(target, mobile, bond_order, max_matches, hcount=False):
    """Yield dicts target_index -> mobile_index for every graph isomorphism."""
    if target.n != mobile.n or target.nbonds != mobile.nbonds:
        return
    lt, lm = _refined_labels([target, mobile], bond_order, hcount)
    if sorted(lt) != sorted(lm):
        return
    by_label = {}
    for j, l in enumerate(lm):
        by_label.setdefault(l, []).append(j)
    freq = {l: len(v) for l, v in by_label.items()}

    # matching order: BFS, each component started from its rarest label
    order, seen = [], set()
    while len(order) < target.n:
        start = min((i for i in range(target.n) if i not in seen),
                    key=lambda i: (freq[lt[i]], -len(target.adj[i])))
        queue = [start]
        seen.add(start)
        while queue:
            i = queue.pop(0)
            order.append(i)
            for j in sorted(target.adj[i], key=lambda j: freq[lt[j]]):
                if j not in seen:
                    seen.add(j)
                    queue.append(j)

    t2m, used = {}, set()
    count = [0]

    def feasible(t, c):
        tn, cn = target.adj[t], mobile.adj[c]
        nmapped = 0
        for u, o in tn.items():
            if u in t2m:
                nmapped += 1
                v = t2m[u]
                if v not in cn or (bond_order and cn[v] != o):
                    return False
        return nmapped == sum(1 for v in cn if v in used)

    def recurse(k):
        if count[0] >= max_matches:
            return
        if k == len(order):
            count[0] += 1
            yield dict(t2m)
            return
        t = order[k]
        # candidates: neighbours of an already-mapped neighbour, if any
        anchor = next((u for u in target.adj[t] if u in t2m), None)
        pool = (mobile.adj[t2m[anchor]].keys() if anchor is not None
                else by_label[lt[t]])
        for c in pool:
            if c in used or lm[c] != lt[t] or not feasible(t, c):
                continue
            t2m[t] = c
            used.add(c)
            yield from recurse(k + 1)
            del t2m[t]
            used.discard(c)

    yield from recurse(0)


# --------------------------------------------------------------------------
# strategy 2: RDKit maximum common substructure
# --------------------------------------------------------------------------
def _to_rdkit(m, bond_order):
    from rdkit import Chem
    rw = Chem.RWMol()
    for e in m.elem:
        a = Chem.Atom(e if Chem.GetPeriodicTable().GetAtomicNumber(e) else "C")
        a.SetNoImplicit(True)
        rw.AddAtom(a)
    btype = {1: Chem.BondType.SINGLE, 2: Chem.BondType.DOUBLE,
             3: Chem.BondType.TRIPLE, 4: Chem.BondType.AROMATIC}
    for i in range(m.n):
        for j, o in m.adj[i].items():
            if i < j:
                rw.AddBond(i, j, btype.get(o, Chem.BondType.SINGLE)
                           if bond_order else Chem.BondType.SINGLE)
    mol = rw.GetMol()
    mol.UpdatePropertyCache(strict=False)
    Chem.FastFindRings(mol)
    return mol


def _mcs_mappings(target, mobile, bond_order, complete_rings, timeout,
                  max_matches):
    from rdkit import Chem
    from rdkit.Chem import rdFMCS
    mt, mm = _to_rdkit(target, bond_order), _to_rdkit(mobile, bond_order)
    res = rdFMCS.FindMCS(
        [mt, mm],
        atomCompare=rdFMCS.AtomCompare.CompareElements,
        bondCompare=(rdFMCS.BondCompare.CompareOrderExact if bond_order
                     else rdFMCS.BondCompare.CompareAny),
        ringMatchesRingOnly=True,
        completeRingsOnly=complete_rings,
        timeout=int(timeout))
    if res.numAtoms < 3:
        return [], res
    patt = Chem.MolFromSmarts(res.smartsString)
    tmatches = mt.GetSubstructMatches(patt, uniquify=True, useChirality=False,
                                      maxMatches=max_matches)
    mmatches = mm.GetSubstructMatches(patt, uniquify=False, useChirality=False,
                                      maxMatches=max_matches)
    maps = []
    for tm in tmatches:
        for mmt in mmatches:
            maps.append(dict(zip(tm, mmt)))
            if len(maps) >= max_matches:
                return maps, res
    return maps, res


# --------------------------------------------------------------------------
# strategies 3 and 4: names / order
# --------------------------------------------------------------------------
def _name_mapping(target, mobile):
    idx = {}
    for j, (nm, e) in enumerate(zip(mobile.name, mobile.elem)):
        idx.setdefault((nm, e), []).append(j)
    mp = {}
    for i, (nm, e) in enumerate(zip(target.name, target.elem)):
        js = idx.get((nm, e))
        if js and len(js) == 1:
            mp[i] = js[0]
    return mp if len(mp) >= 3 else None


def _order_mapping(target, mobile):
    if target.n != mobile.n or target.elem != mobile.elem:
        return None
    return {i: i for i in range(target.n)}


# --------------------------------------------------------------------------
# scoring
# --------------------------------------------------------------------------
def _score(mapping, target, mobile, fit):
    ti = np.fromiter(mapping.keys(), int)
    mi = np.fromiter(mapping.values(), int)
    P, Q = mobile.xyz[mi], target.xyz[ti]
    if fit:
        return _kabsch(P, Q)[0]
    return _rmsd(P, Q)


def _best(mappings, target, mobile, fit, keep=200):
    """Score all mappings; return (best `keep` mappings sorted by score, n)."""
    scored, n = [], 0
    for mp in mappings:
        n += 1
        scored.append((_score(mp, target, mobile, fit), n, mp))
        if len(scored) > 4 * keep:
            scored = sorted(scored, key=lambda x: x[:2])[:keep]
    scored.sort(key=lambda x: x[:2])
    return [mp for _, _, mp in scored[:keep]], n


def _pairs_with_h(mapping, target, mobile, R, t):
    """Pair hydrogens per matched heavy atom using mobile coords after (R, t)."""
    hpairs = []
    for ti, mi in mapping.items():
        Ht, Hm = target.hyd[ti], mobile.hyd[mi]
        if not Ht or not Hm:
            continue
        T = np.array([h[2] for h in Ht])
        M = np.array([h[2] for h in Hm]) @ R.T + t
        D = np.linalg.norm(T[:, None, :] - M[None, :, :], axis=2)
        k = min(len(Ht), len(Hm))
        best, best_c = None, np.inf
        if max(len(Ht), len(Hm)) <= 6:
            for rows in itertools.permutations(range(len(Ht)), k):
                for cols in itertools.permutations(range(len(Hm)), k):
                    c = D[list(rows), list(cols)].sum()
                    if c < best_c:
                        best, best_c = list(zip(rows, cols)), c
        else:  # greedy for pathological cases
            best, Dw = [], D.copy()
            for _ in range(k):
                r, c = np.unravel_index(np.argmin(Dw), Dw.shape)
                best.append((r, c))
                Dw[r, :] = np.inf
                Dw[:, c] = np.inf
        hpairs.append((Ht, Hm, best))
    return hpairs


def _flat(groups):
    return [(Ht[r], Hm[c]) for Ht, Hm, asg in groups for r, c in asg]


def _refine_h(groups, P0, Q0):
    """Local search over H permutations per parent atom, scoring each trial
    with a full Kabsch fit (fixes local minima of assign/fit alternation)."""
    def score(gr):
        hp = _flat(gr)
        P = np.vstack([P0] + [h[1][2] for h in hp])
        Q = np.vstack([Q0] + [h[0][2] for h in hp])
        return _kabsch(P, Q)[0]
    cur = score(groups)
    improved = True
    while improved:
        improved = False
        for g, (Ht, Hm, asg) in enumerate(groups):
            if len(asg) < 2 or max(len(Ht), len(Hm)) > 6:
                continue
            k = len(asg)
            for rows in itertools.permutations(range(len(Ht)), k):
                for cols in itertools.permutations(range(len(Hm)), k):
                    trial = list(zip(rows, cols))
                    if sorted(trial) == sorted(groups[g][2]):
                        continue
                    gr = groups[:g] + [(Ht, Hm, trial)] + groups[g + 1:]
                    sc = score(gr)
                    if sc < cur - 1e-9:
                        groups, cur, improved = gr, sc, True
    return groups


def _evaluate(mapping, target, mobile, fit, hydrogens):
    """Coordinates, atom pairs and RMSDs for one heavy-atom mapping."""
    ti = list(mapping.keys())
    mi = [mapping[i] for i in ti]
    P, Q = mobile.xyz[mi], target.xyz[ti]
    pairs = [(target.ident[a], target.name[a], mobile.ident[b], mobile.name[b])
             for a, b in zip(ti, mi)]
    rms_before = _rmsd(P, Q)
    _, R, t = _kabsch(P, Q)
    if not fit:
        R, t = np.eye(3), np.zeros(3)
    if hydrogens:
        # assign H per matched heavy atom, refit, repeat until stable
        P0, Q0, pairs0, prev = P, Q, pairs, None
        for _it in range(10):
            groups = _pairs_with_h(mapping, target, mobile, R, t)
            if fit and groups:
                groups = _refine_h(groups, P0, Q0)
            hp = _flat(groups)
            key = [(h[0][0], h[1][0]) for h in hp]
            if not hp or key == prev:
                break
            prev = key
            P = np.vstack([P0] + [h[1][2] for h in hp])
            Q = np.vstack([Q0] + [h[0][2] for h in hp])
            pairs = pairs0 + [(h[0][0], h[0][1], h[1][0], h[1][1]) for h in hp]
            rms_before = _rmsd(P, Q)
            if not fit:
                break
            _, R, t = _kabsch(P, Q)
    return dict(mapping=mapping, P=P, Q=Q, pairs=pairs, R=R, t=t,
                rms_before=rms_before, rms_final=_rmsd(P @ R.T + t, Q))


# --------------------------------------------------------------------------
# main command
# --------------------------------------------------------------------------
def _find_mapping(target, mobile, method, fit, bond_order, max_matches,
                  mcs_timeout, complete_rings, quiet, hydrogens=False,
                  geom_pair=None):
    """Return (method, candidate mappings best-first, note, target, mobile).
    The returned molecules may be the distance-bonded versions."""
    tried = []
    order = (["iso", "iso_geom", "mcs", "name", "order"] if method == "auto"
             else ["iso", "iso_geom"] if method == "iso" else [method])
    for meth in order:
        if meth == "iso_geom":
            if geom_pair is None:
                continue
            gt, gm = geom_pair()
            if (gt.adj == target.adj and gm.adj == mobile.adj):
                continue  # identical connectivity, nothing new to try
            try:
                r = _find_mapping(gt, gm, "iso", fit, False, max_matches,
                                  mcs_timeout, complete_rings, quiet,
                                  hydrogens)
            except CmdException:
                tried.append("iso: not isomorphic with distance-derived "
                             "bonds either")
                continue
            return ("iso", r[1], r[2] + "; connectivity re-derived from "
                    "distances (file bonds were not isomorphic)", gt, gm)
        if meth == "iso":
            # hydrogens=1: first with attached-H counts in the atom labels
            # (distinguishes e.g. the two C(=O)OH oxygens), then H-blind.
            # hydrogens=0: H-blind only, so terminal groups such as COOH/COO-
            # or NO2 oxygens are treated as equivalent and protonation /
            # missing-H differences between the molecules do not matter.
            levels = [True, False] if (hydrogens and any(target.hyd) and
                                       any(mobile.hyd)) else [False]
            for hc in levels:
                mp, n = _best(_isomorphisms(target, mobile, bond_order,
                                            max_matches, hc),
                              target, mobile, fit)
                if mp:
                    note = ("%s, %d symmetry-equivalent mapping(s) evaluated"
                            % ("H-count aware" if hc else "H-blind", n))
                    if n >= max_matches:
                        note += " (CAP REACHED: raise max_matches)"
                    return meth, mp, note, target, mobile
            tried.append("iso: heavy-atom graphs are not isomorphic")
        elif meth == "mcs":
            if importlib.util.find_spec("rdkit") is None:
                tried.append("mcs: RDKit not importable in PyMOL's Python")
                continue
            maps, res = _mcs_mappings(target, mobile, bond_order,
                                      complete_rings, mcs_timeout, max_matches)
            if maps:
                mp, n = _best(maps, target, mobile, fit)
                note = ("MCS %d atoms (%s), %d mapping(s) evaluated"
                        % (res.numAtoms, res.smartsString if not quiet
                           and len(res.smartsString) < 120 else "...", n))
                if res.canceled:
                    note += " (MCS TIMED OUT: may be non-maximal)"
                return meth, mp, note, target, mobile
            tried.append("mcs: common substructure < 3 atoms")
        elif meth == "name":
            mp = _name_mapping(target, mobile)
            if mp:
                return (meth, [mp], "paired by unique atom name + element",
                        target, mobile)
            tried.append("name: < 3 shared unique atom names")
        elif meth == "order":
            mp = _order_mapping(target, mobile)
            if mp:
                return (meth, [mp], "paired by atom order (UNVERIFIED chemically)",
                        target, mobile)
            tried.append("order: element sequences differ")
        else:
            raise CmdException("ligalign: unknown method '%s'" % meth)
    raise CmdException("ligalign: no atom correspondence found.\n  "
                       + "\n  ".join(tried))


def ligalign(mobile, target, method="auto", fit=1, hydrogens=0, bond_order=0,
             mobile_state=-1, target_state=-1, transform=1, max_matches=20000,
             mcs_timeout=10, complete_rings=1, show_pairs=0,
             name="ligalign_pairs", verbose=1, _self=cmd):
    """
DESCRIPTION

    Symmetry-aware superposition and RMSD of two small molecules, independent
    of atom names and atom order. See the header of ligalign.py for details.

USAGE

    ligalign mobile, target [, method [, fit [, hydrogens [, bond_order
        [, mobile_state [, target_state [, transform [, max_matches
        [, mcs_timeout [, complete_rings [, show_pairs [, name
        [, verbose ]]]]]]]]]]]]]

    method: auto | iso | mcs | name | order   (default auto)
    fit=0 : no superposition; minimum in-place (docking-style) RMSD
    mobile_state=0 : evaluate every state of mobile
    """
    method = str(method).strip().lower()
    fit, hydrogens, bond_order = map(_boolarg, (fit, hydrogens, bond_order))
    transform, complete_rings, show_pairs = map(
        _boolarg, (transform, complete_rings, show_pairs))
    mobile_state = int(mobile_state)
    target_state = _resolve_state(target, target_state)
    max_matches, mcs_timeout, verbose = (int(max_matches), float(mcs_timeout),
                                         int(verbose))

    tgt = _Mol(target, target_state)
    if mobile_state == 0:
        objs = cmd.get_object_list("(%s)" % mobile) or []
        if not objs:
            raise CmdException("ligalign: selection '%s' is empty" % mobile)
        nstates = max(cmd.count_states(o) for o in objs)
        states = list(range(1, nstates + 1))
    else:
        states = [_resolve_state(mobile, mobile_state)]

    results = []
    meth = note = None
    for st in states:
        mob = _Mol(mobile, st)
        if set(mob.objects) & set(tgt.objects) and fit and transform:
            raise CmdException("ligalign: mobile and target share an object; "
                               "cannot move one without the other")
        geom_pair = (lambda: (_Mol(target, target_state, geom=True),
                              _Mol(mobile, st, geom=True)))
        if meth in ("iso", "mcs") and st != states[0]:
            # re-evaluate the symmetry-equivalent mappings for every state
            _, cands, _, tg, mb = _find_mapping(
                tgt, mob, meth, fit, bond_order, max_matches, mcs_timeout,
                complete_rings, True, hydrogens, geom_pair)
        else:
            meth, cands, note, tg, mb = _find_mapping(
                tgt, mob, method, fit, bond_order, max_matches, mcs_timeout,
                complete_rings, verbose < 1, hydrogens, geom_pair)
        # heavy-only: best candidate by heavy-atom score. With H: the heavy
        # mapping that is best for heavy atoms need not be best once H are
        # included (e.g. equivalent methyls), so the top candidates are all
        # evaluated with their H assignment.
        evals = [_evaluate(mp, tg, mb, fit, hydrogens)
                 for mp in (cands if hydrogens else cands[:1])]
        ev = min(evals, key=lambda e: e["rms_final"])
        mapping, P, Q, pairs = ev["mapping"], ev["P"], ev["Q"], ev["pairs"]
        R, t, rms_before, rms_final = ev["R"], ev["t"], ev["rms_before"], \
            ev["rms_final"]
        Pfin = P @ R.T + t

        if fit and transform:
            for obj in mob.objects:
                _apply_transform(obj, R, t, st)

        results.append(rms_final)

        if verbose >= 1:
            print(" ligalign: %s -> %s (mobile state %d, target state %d)"
                  % (mobile, target, st, target_state))
            if st == states[0]:
                print("   method      : %s  [%s]" % (meth, note))
            print("   atoms paired: %d  (mobile heavy %d, target heavy %d)"
                  % (len(pairs), mb.n, tg.n))
            if hydrogens:
                nh = len(pairs) - len(mapping)
                print("   H paired    : %d  (mobile H %d, target H %d)"
                      % (nh, sum(map(len, mb.hyd)), sum(map(len, tg.hyd))))
            if len(mapping) < max(mb.n, tg.n):
                print("   WARNING     : partial match, RMSD is over the "
                      "common substructure only")
            print("   RMSD in place (before fit): %.4f A" % rms_before)
            if fit:
                print("   RMSD after superposition  : %.4f A%s"
                      % (rms_final, "" if transform
                         else "  (mobile NOT moved, transform=0)"))
        if verbose >= 2:
            print("   %-22s %-22s %8s" % ("target atom", "mobile atom", "d/A"))
            for k, (tid, tn, mid, mn) in enumerate(pairs):
                d = np.linalg.norm(Pfin[k] - Q[k])
                print("   %-22s %-22s %8.3f" % ("%s`%d/%s" % (tid[0], tid[1], tn),
                                               "%s`%d/%s" % (mid[0], mid[1], mn),
                                               d))

        if show_pairs and st == states[-1]:
            cmd.delete(name)
            for tid, _, mid, _ in pairs:
                cmd.distance(name, "%s and index %d" % tid,
                             "%s and index %d" % mid, state=st)
            cmd.hide("labels", name)

    if len(results) > 1 and verbose >= 1:
        print(" ligalign summary (%s per state): min %.4f  max %.4f  mean %.4f"
              % ("fitted RMSD" if fit else "in-place RMSD",
                 min(results), max(results), float(np.mean(results))))
    return results if mobile_state == 0 else results[0]


cmd.extend("ligalign", ligalign)
cmd.auto_arg[0]["ligalign"] = cmd.auto_arg[0]["align"]
cmd.auto_arg[1]["ligalign"] = cmd.auto_arg[1]["align"]
