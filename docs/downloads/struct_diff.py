# struct_diff.py: colour two superimposed structures by local structural deviation (stored in
# the B-factors). Paulo Martel, 2026. Usage: help struct_diff; manual: docs/struct_diff.md
from pymol import cmd
import math

_struct_diff_unmatched = -1.0


# ----------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------
def _struct_diff_keys(sel):
    _sd_keys = set()
    cmd.iterate(sel, "_sd_keys.add((model, index))", space={"_sd_keys": _sd_keys})
    return _sd_keys


def _struct_diff_xyz(sel, state):
    _sd_xyz = {}
    cmd.iterate_state(state, sel, "_sd_xyz[(model, index)] = (x, y, z)",
                      space={"_sd_xyz": _sd_xyz})
    return _sd_xyz


def _struct_diff_resinfo(sel):
    """(model, index) -> residue key (model, segi, chain, resi, resn)"""
    _sd_res = {}
    cmd.iterate(sel, "_sd_res[(model, index)] = (model, segi, chain, resi, resn)",
                space={"_sd_res": _sd_res})
    return _sd_res


def _struct_diff_atomsel(key):
    return f"(model {key[0]} and index {key[1]})"


def _struct_diff_reslabel(rk):
    model, segi, chain, resi, resn = rk
    return f"{model}/{chain or '-'}/{resn}`{resi}"


# ----------------------------------------------------------------------------
# pairing: PyMOL aligners
# ----------------------------------------------------------------------------
def _struct_diff_aligner_pairs(method, msel, tsel, mstate, tstate):
    aln = cmd.get_unused_name("_sdiff_aln")
    try:
        if method == "align":
            cmd.align(msel, tsel, cycles=0, transform=0, object=aln,
                      mobile_state=mstate, target_state=tstate, quiet=1)
        elif method == "super":
            cmd.super(msel, tsel, cycles=0, transform=0, object=aln,
                      mobile_state=mstate, target_state=tstate, quiet=1)
        elif method == "cealign":
            # cealign argument order is (target, mobile)
            cmd.cealign(tsel, msel, target_state=tstate, mobile_state=mstate,
                        transform=0, object=aln, quiet=1)
        else:
            raise ValueError(method)
        raw = cmd.get_raw_alignment(aln)
    finally:
        cmd.delete(aln)

    mk, tk = _struct_diff_keys(msel), _struct_diff_keys(tsel)
    pairs = []
    for p in raw:
        p = [tuple(a) for a in p]
        m = [a for a in p if a in mk]
        t = [a for a in p if a in tk]
        if len(m) == 1 and len(t) == 1:
            pairs.append((m[0], t[0]))
    return pairs


# ----------------------------------------------------------------------------
# pairing: spatial (mutual nearest CA within radius)
# ----------------------------------------------------------------------------
def _struct_diff_load_atoms(sel, state):
    _sd_atoms = []
    cmd.iterate_state(
        state, sel,
        "_sd_atoms.append((model, index, segi, chain, resi, resn, name, x, y, z))",
        space={"_sd_atoms": _sd_atoms})
    return _sd_atoms


def _struct_diff_grid(atoms, h):
    g = {}
    for i, a in enumerate(atoms):
        c = (math.floor(a[7] / h), math.floor(a[8] / h), math.floor(a[9] / h))
        g.setdefault(c, []).append(i)
    return g


def _struct_diff_nearest_within(p, atoms, g, h, r):
    cx, cy, cz = math.floor(p[0] / h), math.floor(p[1] / h), math.floor(p[2] / h)
    best, bd = None, r
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for j in g.get((cx + dx, cy + dy, cz + dz), ()):
                    d = math.dist(p, atoms[j][7:10])
                    if d <= bd:
                        best, bd = j, d
    return best


def _struct_diff_spatial_pairs(msel, tsel, mstate, tstate, radius):
    ma, ta = _struct_diff_load_atoms(msel, mstate), _struct_diff_load_atoms(tsel, tstate)
    rkey = lambda a: (a[0], a[2], a[3], a[4], a[5])   # model, segi, chain, resi, resn
    mca = [a for a in ma if a[6] == "CA"]
    tca = [a for a in ta if a[6] == "CA"]
    if not mca or not tca:
        raise RuntimeError("method=spatial needs CA atoms in both selections "
                           "(check the 'atoms' argument).")

    h = max(radius, 1.0)
    gm, gt = _struct_diff_grid(mca, h), _struct_diff_grid(tca, h)

    res_pairs = []
    for i, a in enumerate(mca):
        j = _struct_diff_nearest_within(a[7:10], tca, gt, h, radius)
        if j is None:
            continue
        if _struct_diff_nearest_within(tca[j][7:10], mca, gm, h, radius) == i:
            res_pairs.append((rkey(a), rkey(tca[j])))

    def by_res(atoms):
        d = {}
        for a in atoms:
            d.setdefault(rkey(a), {}).setdefault(a[6], (a[0], a[1]))  # first altloc
        return d

    mby, tby = by_res(ma), by_res(ta)
    pairs = []
    for mr, tr in res_pairs:
        for name in sorted(mby[mr].keys() & tby[tr].keys()):
            pairs.append((mby[mr][name], tby[tr][name]))
    return pairs


# ----------------------------------------------------------------------------
# shared pairing entry point
# ----------------------------------------------------------------------------
def _struct_diff_get_pairs(mobile, target, atoms, method, radius, cutoff, mstate, tstate):
    msel = f"({mobile}) and ({atoms})"
    tsel = f"({target}) and ({atoms})"
    if cmd.count_atoms(msel) == 0:
        raise RuntimeError(f"Empty mobile selection: {msel}")
    if cmd.count_atoms(tsel) == 0:
        raise RuntimeError(f"Empty target selection: {tsel}")
    if cmd.count_atoms(f"({msel}) and ({tsel})") > 0:
        raise RuntimeError("mobile and target selections overlap.")

    if method == "spatial":
        pairs = _struct_diff_spatial_pairs(msel, tsel, mstate, tstate, radius)
    elif method in ("align", "super", "cealign"):
        pairs = _struct_diff_aligner_pairs(method, msel, tsel, mstate, tstate)
    else:
        raise ValueError("method must be spatial, align, super or cealign")
    if not pairs:
        raise RuntimeError("No atom pairs found.")

    mxyz, txyz = _struct_diff_xyz(msel, mstate), _struct_diff_xyz(tsel, tstate)

    # sanity check: iterate_state coordinates vs. PyMOL's own distance
    if mstate == tstate:
        m0, t0 = pairs[0]
        d_iter = math.dist(mxyz[m0], txyz[t0])
        d_view = cmd.get_distance(_struct_diff_atomsel(m0), _struct_diff_atomsel(t0), state=mstate)
        if abs(d_iter - d_view) > 1e-2:
            raise RuntimeError(
                f"Coordinate check failed ({d_iter:.3f} vs {d_view:.3f} A): object "
                "matrices are probably not applied. Flatten with cmd.create first.")

    disp = {}
    kept = []
    for mk, tk in pairs:
        d = math.dist(mxyz[mk], txyz[tk])
        if cutoff > 0 and d > cutoff:
            continue
        kept.append((mk, tk))
        disp[mk] = d
        disp[tk] = d
    return msel, tsel, pairs, kept, disp, mxyz, txyz


# ----------------------------------------------------------------------------
# main command
# ----------------------------------------------------------------------------
def struct_diff(mobile, target, mode="residue", atoms="not hydro",
                method="spatial", radius=3.0, cutoff=0.0,
                palette="blue_red", maximum=0.0, unmatched="green",
                mobile_state=1, target_state=1, top=10, report="", quiet=0):
    """
DESCRIPTION

    Colour two superimposed structures by local structural deviation:
    per-residue RMSD (or per-atom displacement) of paired atoms, in the
    current superposition (nothing is moved). The values are written to
    the B-factors of both structures (-1 = unmatched).

USAGE

    struct_diff mobile, target [, mode [, atoms [, method [, radius
        [, cutoff [, palette [, maximum [, unmatched [, mobile_state
        [, target_state [, top [, report [, quiet ]]]]]]]]]]]]]

ARGUMENTS

    mobile, target = string: the two structures; may be chains of one
    object, but must not overlap

    mode = residue or atom: residue RMSD over its matched atoms, or each
    atom's displacement {default: residue}

    atoms = string: atoms used for pairing and values, e.g. name CA,
    backbone {default: not hydro}

    method = spatial, align, super or cealign: how atoms are paired;
    spatial = mutual nearest CA within radius in the current
    superposition, then atoms by name {default: spatial}

    radius = float: CA pairing radius (A) for method=spatial {default: 3.0}

    cutoff = float: drop atom pairs farther apart than this (A)
    {default: 0, off}

    palette = string: spectrum palette {default: blue_red}

    maximum = float: top of the colour ramp (A) {default: 0, the largest
    value found}

    unmatched = string: colour of unmatched atoms, or hide {default: green}

    mobile_state, target_state = integer: states compared {default: 1}

    top = integer: number of worst residue pairs printed {default: 10}

    report = string: file for a table (TSV) of all residue pairs

    quiet = 0/1 {default: 0}

EXAMPLES

    struct_diff objA, objB
    struct_diff objA, objB, method=align, atoms=backbone, cutoff=3.5, maximum=3.0
    struct_diff obj and chain A, obj and chain B

NOTES

    Overwrites the B-factors of both structures. method=spatial cannot pair
    residues displaced by more than radius (they appear as unmatched):
    check the pairing with struct_diff_pairs. Manual: docs/struct_diff.md
    in the pymol repository.

SEE ALSO

    struct_diff_pairs, align_view, bcolor

AUTHOR

    Paulo Martel, 2026
    """
    mstate, tstate = int(mobile_state), int(target_state)
    radius, cutoff, maximum = float(radius), float(cutoff), float(maximum)
    top, quiet = int(top), int(quiet)

    msel, tsel, pairs_all, pairs, disp, _, _ = _struct_diff_get_pairs(
        mobile, target, atoms, method, radius, cutoff, mstate, tstate)
    if not pairs:
        raise RuntimeError("No pairs left after cutoff.")

    both = f"({mobile}) or ({target})"
    info = _struct_diff_resinfo(both)

    # residue-level sums and partner map
    sq, n, partner = {}, {}, {}
    for mk, tk in pairs:
        d2 = disp[mk] ** 2
        rm, rt = info[mk], info[tk]
        partner.setdefault(rm, rt)
        for key in (rm, rt):
            sq[key] = sq.get(key, 0.0) + d2
            n[key] = n.get(key, 0) + 1
    res_rmsd = {k: math.sqrt(sq[k] / n[k]) for k in sq}

    if mode == "atom":
        vals = disp
        label = "atom displacement"
    elif mode == "residue":
        vals = {ak: res_rmsd.get(rk, _struct_diff_unmatched) for ak, rk in info.items()}
        label = "residue RMSD"
    else:
        raise ValueError("mode must be 'residue' or 'atom'")

    cmd.alter(both, "b = _sd_vals.get((model, index), %r)" % _struct_diff_unmatched,
              space={"_sd_vals": vals})

    good = [v for v in vals.values() if v >= 0]
    vmax = maximum if maximum > 0 else (max(good) if good else 1.0)
    if vmax <= 0:
        vmax = 1.0
    cmd.spectrum("b", palette, f"({both}) and b > -0.5", minimum=0.0, maximum=vmax)
    if unmatched == "hide":
        cmd.hide("everything", f"({both}) and b < -0.5")
    else:
        cmd.color(unmatched, f"({both}) and b < -0.5")

    if report:
        with open(report, "w") as fh:
            fh.write("mobile_residue\ttarget_residue\tn_atoms\trmsd_A\n")
            for rm, rt in sorted(partner.items(),
                                 key=lambda kv: (kv[0][2], kv[0][1], kv[0][3])):
                fh.write(f"{_struct_diff_reslabel(rm)}\t{_struct_diff_reslabel(rt)}\t{n[rm]}\t{res_rmsd[rm]:.3f}\n")

    if not quiet:
        overall = math.sqrt(sum(disp[mk] ** 2 for mk, _ in pairs) / len(pairs))
        n_unm_m = cmd.count_atoms(f"({mobile}) and b < -0.5")
        n_unm_t = cmd.count_atoms(f"({target}) and b < -0.5")
        print(f"struct_diff: method={method}, {len(pairs)} atom pairs "
              f"({len(pairs_all) - len(pairs)} removed by cutoff), "
              f"{len(partner)} residue pairs")
        print(f"  overall RMSD (current superposition) = {overall:.3f} A; "
              f"ramp 0-{vmax:.2f} A ({label})")
        print(f"  unmatched atoms: mobile {n_unm_m}, target {n_unm_t}")
        if top > 0:
            worst = sorted(((res_rmsd[rm], rm, rt) for rm, rt in partner.items()),
                           reverse=True)[:top]
            print(f"  top {len(worst)} residue pairs:")
            for v, rm, rt in worst:
                print(f"    {_struct_diff_reslabel(rm):28s} <-> {_struct_diff_reslabel(rt):28s} {v:6.2f} A")
    return vals


# ----------------------------------------------------------------------------
# diagnostic command
# ----------------------------------------------------------------------------
def struct_diff_pairs(mobile, target, show="all", atoms="not hydro",
                      method="spatial", radius=3.0, cutoff=0.0,
                      mobile_state=1, target_state=1):
    """
DESCRIPTION

    Show how struct_diff pairs the residues: for each residue of mobile in
    show, its partner in target, the CA-CA distance, the atom pairs
    proposed and kept, the value struct_diff would write, and whether it
    is matched, rejected by the cutoff or unmatched. Changes nothing.

USAGE

    struct_diff_pairs mobile, target [, show [, atoms [, method [, radius
        [, cutoff [, mobile_state [, target_state ]]]]]]]

ARGUMENTS

    show = string: residues of mobile to list {default: all}

    the others as for struct_diff

EXAMPLES

    struct_diff_pairs objA, objB, show=resi 30-45
    struct_diff_pairs objA, objB, method=align, atoms=backbone, cutoff=3.5, show=resi 30-45

NOTES

    Lists residues of mobile only: swap the arguments to see residues of
    target that are unmatched (the aligners may then pair differently).

SEE ALSO

    struct_diff

AUTHOR

    Paulo Martel, 2026
    """
    mstate, tstate = int(mobile_state), int(target_state)
    radius, cutoff = float(radius), float(cutoff)

    msel, tsel, pairs_all, pairs, disp, mxyz, txyz = _struct_diff_get_pairs(
        mobile, target, atoms, method, radius, cutoff, mstate, tstate)
    info = _struct_diff_resinfo(f"({mobile}) or ({target})")

    kept = set(pairs)
    # mobile residue -> [target residue, n_all, n_kept, CA dist, sum d^2 over kept]
    res = {}
    for mk, tk in pairs_all:
        rm, rt = info[mk], info[tk]
        e = res.setdefault(rm, [rt, 0, 0, None, 0.0])
        e[1] += 1
        d = math.dist(mxyz[mk], txyz[tk])
        if (mk, tk) in kept:
            e[2] += 1
            e[4] += d * d
        if cmd.count_atoms(f"{_struct_diff_atomsel(mk)} and name CA"):
            e[3] = d

    shown = []
    cmd.iterate(f"({mobile}) and ({show}) and name CA",
                "_sd_shown.append((model, segi, chain, resi, resn))",
                space={"_sd_shown": shown})
    print(f"struct_diff_pairs: method={method}, atoms='{atoms}', cutoff={cutoff}")
    print("  'pairs' = atom pairs proposed by the pairing method; 'kept' = after cutoff.")
    print("  'b' = residue-mode value struct_diff writes with the same arguments "
          "(-1 = unmatched).")
    print(f"  {'mobile':28s}    {'proposed target':28s} {'CA dist':>8s} "
          f"{'pairs':>6s} {'kept':>5s} {'b':>6s}  status")
    for rm in shown:
        if rm not in res:
            print(f"  {_struct_diff_reslabel(rm):28s}    {'-':28s} {'':>8s} {0:6d} {0:5d} "
                  f"{_struct_diff_unmatched:6.2f}  _struct_diff_unmatched (no pair proposed)")
            continue
        rt, na, nk, dca, sq = res[rm]
        ds = f"{dca:8.2f}" if dca is not None else "     n/a"
        if nk == 0:
            bval, status = _struct_diff_unmatched, "REJECTED (all pairs > cutoff)"
        else:
            bval = math.sqrt(sq / nk)
            status = "matched" if nk == na else f"matched ({na - nk} atom pairs > cutoff)"
        print(f"  {_struct_diff_reslabel(rm):28s} -> {_struct_diff_reslabel(rt):28s} {ds} {na:6d} {nk:5d} "
              f"{bval:6.2f}  {status}")


cmd.extend("struct_diff", struct_diff)
cmd.extend("struct_diff_pairs", struct_diff_pairs)
for _c in ("struct_diff", "struct_diff_pairs"):
    try:
        cmd.auto_arg[0][_c] = cmd.auto_arg[0]["align"]
        cmd.auto_arg[1][_c] = cmd.auto_arg[1]["align"]
    except (KeyError, AttributeError, IndexError):
        pass
