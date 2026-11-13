"""Corrective shapes relaxed where they fold the posed skin (P1 posed folds, 13 Nov), a build step after each tier's
correctives (build_topo.run_tier; correctives.run writes the shapes, this rewrites the ones it touches).

    python tools/body/shape_relax.py <out_dir> [--tier close|play]     (again on a built round: reads the joint's
                                                                         "fold_relax" from the spec's correctives data)

Why: a key laid on another surface (her_b's "arm_hang": seven game keys, correctives.game_a_key, B's points put on old
body A's posed surface in game shots) carries that surface's own creases and the point-by-point validity mask into
the shape. At its key the shape is A's surface; OFF its key the RBF mixes several such shapes over a skin the bones
turn differently, and the creases fold (round_39b close, foldcheck full mode, shoulder inverted: rom 26/23, walk
119/43, fight 23/80 a side, with the laws mode, no shapes, at 0). Smoothing every key's move (game_a "smooth") clears
most of it but flattens the shape everywhere (Look's moved p95 8.3 -> 5.5 mm); this smooths only where it folds.

What: the tier's export (out/<glb> with its shapes, out/<rig>) posed by foldcheck.py's own poses (cfg "sets": rom and
the R&D clips "rnd") in its "full" mode (helpers and shapes driven, as the game). Each round, every triangle inverted in
cfg "regions" (foldcheck's fault boxes, degenerate slivers excepted as foldcheck counts them) on any pose marks its
points for each of the joint's shapes worn there (weight > cfg "w_min") on that triangle's side; a right side's points
are taken to the left shape by the topology's own mirror (correctives.topo_mirror: 0 unmatched; a positional mirror
leaves 14k of her points unmatched, her trunk is not symmetric to 0.1 mm, and the right keys plateaued on it). The marks
grow `rows` rings; the left shape's delta is relaxed `iters` times there (each point half to its ring's mean, the ring
weighted by 1/edge length, as weights_topo.fold_relax), the right shape rebuilt as its mirror, until none folds or
`rounds`. Everything outside the marks is the shape as solved, so each key keeps its form where it does not fold
(report "fidelity": each shape's posed move at its own key, p95 and max mm, before and after). The tier's glb targets
and stage/<shapes>.npz are rewritten (correctives.write_targets, the normals' deltas made again from the new shapes).
Vertex count, order and UVs unchanged.
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
import scipy.sparse as sp

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
for _p in (HERE, REPO):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import correctives  # noqa: E402
import foldcheck as fc  # noqa: E402
from posers import LbsPoser, make_poser  # noqa: E402


def _key_moves(p, rig, jc, names):
    """Each game key's shape's posed move at its own key (the key's pose, that shape alone at weight 1): p95 (points
    moved over 0.1 mm) and max, mm."""
    ga = jc.get("game_a")
    if not ga:
        return {}
    kps = json.load(open(os.path.join(REPO, ga["poses"])))["keys"]
    out = {}
    for key, nm in zip(jc["keys"], names):
        if key[0] != "game":
            continue
        s_ = key[2] if len(key) > 2 else ga.get("side", "r")
        G = correctives.game_pose(p, kps[key[1]])
        n = nm.replace("{s}", s_)
        mv = np.linalg.norm(p._skin(G, {n: 1.0}) - p._skin(G, {}), axis=1)
        v = mv[mv > 1e-4]
        out[n] = [round(float(np.percentile(v, 95) * 1e3), 2), round(float(mv.max() * 1e3), 2)] if len(v) else [0.0, 0.0]
    return out


def relax(out, tier, jname, cfg, turn_normals=True, ns=0, write=True):
    """Relax the joint `jname`'s shapes on a built tier (see the module's doc). Returns the report."""
    t0 = time.time()
    f_glb, f_rig, f_base, f_shapes, _ = correctives.TIERS[tier]
    rig = json.load(open(os.path.join(out, f_rig)))
    p = make_poser("lbs", os.path.join(out, f_glb), rig)
    sk, md = fc.Skin(p), fc.Modes(p, rig)
    nb = sk.nb
    jcr = next(c for c in rig["correctives"] if c.get("joint") == jname)
    names = [n for n in jcr["shapes"] if n]
    conf_names = names
    sets = cfg.get("sets", ["rom", "rnd"])
    src = (list(fc.rom_poses(p)) if "rom" in sets else []) + \
          (list(fc.rnd_poses(p, cfg.get("rnd", ["walk", "fight"]))) if "rnd" in sets else [])
    regs = cfg.get("regions", ["shoulder_l", "shoulder_r"])
    side_reg = {s: np.zeros(len(sk.Tw), bool) for s in "lr"}
    for r in regs:
        side_reg[r[-1]] |= sk.reg_tw[r]
    for s in "lr":
        side_reg[s] &= ~sk.degen
    # the topology's mirror, on the body's points, then on the welded points
    Pb = p.Pb[:nb]
    tp = os.path.join(HERE, "out", "topo", f"{tier}.npz")
    mir = correctives.topo_mirror(np.load(tp)["mirror_of"], Pb, os.path.join(out, "stage", f"{tier}.npz"))
    assert (mir >= 0).all()
    mw = sk.rep[mir[sk.first]]
    E, nw, X = sk.Ew, sk.nw, sk.Xw0
    w = 1.0 / np.maximum(np.linalg.norm(X[E[:, 0]] - X[E[:, 1]], axis=1), 1e-4)
    A = sp.coo_matrix((np.r_[w, w], (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), (nw, nw)).tocsr()
    L = sp.diags(1.0 / np.asarray(A.sum(1)).ravel()) @ A
    Ab = (A > 0).astype(float)
    left = X[:, 0] > 1e-6                       # (a left shape lives on the left: correctives zero x < 0)
    mx = np.array([-1.0, 1, 1])
    Dw = {n: p.targets[n.replace("{s}", "l")][:nb][sk.first].copy() for n in names}
    fid0 = _key_moves(p, rig, cfg.get("_jc", {}), conf_names) if cfg.get("_jc") else {}

    def put():
        for n in names:
            Dl = np.zeros_like(p.Pb)
            Dl[:nb] = Dw[n][sk.rep]
            Dr = np.zeros_like(p.Pb)
            Dr[:nb] = Dl[:nb][mir] * mx
            p.targets[n.replace("{s}", "l")], p.targets[n.replace("{s}", "r")] = Dl, Dr

    hist, touched, wmin = [], {n: np.zeros(nw, bool) for n in names}, float(cfg.get("w_min", 0.02))
    for _ in range(int(cfg.get("rounds", 10))):
        marks, cnt = {}, 0
        for lab, G, kd in src:
            Gd, wt = md.drv.drive(p, md.hold(G, kd), rig)
            V = p._skin(Gd, wt)[:nb][sk.first]
            nb_, _ = fc.inverted(sk.Xw0, V, sk.Tw, sk.Aw, sk.EPw)
            for s in "lr":
                m = nb_ & side_reg[s]
                if not m.any():
                    continue
                cnt += int(m.sum())
                vs = np.zeros(nw, bool)
                vs[sk.Tw[m].ravel()] = True
                if s == "r":
                    vl = np.zeros(nw, bool)
                    vl[mw[vs]] = True
                    vs = vl
                for n in names:
                    if wt.get(n.replace("{s}", s), 0.0) > wmin:
                        marks[n] = marks.get(n, np.zeros(nw, bool)) | vs
        hist.append(cnt)
        if cnt == 0 or not marks:
            break
        for n, mk in marks.items():
            for _ in range(int(cfg.get("rows", 3))):
                mk = mk | ((Ab @ mk.astype(float)) > 0)
            mk &= left
            touched[n] |= mk
            D = Dw[n]
            for _ in range(int(cfg.get("iters", 10))):
                Dn = 0.5 * D + 0.5 * (L @ D)
                D[mk] = Dn[mk]
            D[~left] = 0.0
        put()
    fid1 = _key_moves(p, rig, cfg.get("_jc", {}), conf_names) if cfg.get("_jc") else {}
    rep = {"inverted_per_round": hist, "points": {n: int(v.sum()) for n, v in touched.items() if v.any()},
           "fidelity_p95_max_mm": {k: [fid0[k], fid1[k]] for k in fid0}}
    if write:
        z = np.load(os.path.join(out, "stage", f_shapes))
        shapes = {k: z[k] for k in z.files}
        for n in names:
            for s in "lr":
                shapes[n.replace("{s}", s)] = p.targets[n.replace("{s}", s)][:nb].copy()
        base = LbsPoser(os.path.join(out, "stage", f_base), dict(rig, correctives=[]))
        body = np.nonzero(base.piece == "body")[0]
        Pbb, Tbb = base.Pb[body], base.T[(base.piece[base.T] == "body").all(1)]
        assert len(Pbb) == nb and np.abs(Pbb - Pb).max() < 1e-6
        correctives.write_targets(out, tier, rig, shapes, base, Pbb, Tbb, turn_normals, ns)
    rep["seconds"] = round(time.time() - t0, 1)
    return rep


def run(out, tier="close", conf_path=None, turn_normals=True):
    """Every joint of the correctives data with a "fold_relax" block whose "tiers" (default both) hold this tier."""
    conf = correctives.load_conf(conf_path)
    ns = int(conf["solve"].get("normal_smooth", 0))
    rep = {}
    for jc in conf["joints"]:
        fr = jc.get("fold_relax")
        if jc.get("held") or not fr or tier not in fr.get("tiers", ["close", "play"]):
            continue
        rep[jc["name"]] = relax(out, tier, jc["name"], dict(fr, _jc=jc), turn_normals, ns)
        print("SHAPE_RELAX", tier, jc["name"], rep[jc["name"]], flush=True)
    return rep


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    tier = sys.argv[sys.argv.index("--tier") + 1] if "--tier" in sys.argv else "close"
    a = [x for x in a if x != tier]
    spec = json.load(open(os.path.join(REPO, "tools/body/specs/her_b.json")))
    run(os.path.abspath(a[0]), tier, spec.get("correctives_conf"))
