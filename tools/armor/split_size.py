"""Sizing an ARTICULATED (split) spaulder from measurement: which (s, theta) pieces can a rigid plate ride?

Reads P1's skin-travel tool, body-p1b tools/body/ride_travel.py (worktree .claude/worktrees/body-p1b, branch body-p1b
@61244c52f), imported as a module (its body model, surfaces, clips and rides; nothing copied). Its patch is extended
in s from the cop's box (-88..+36 mm) to the lames' reach (+154 mm), theta 21..172 on the shoulder frame (upperarm ->
lowerarm), and its sphere turn sampled t = 0..1 step 0.1. Surfaces: `new` (the carried target P1's fit aims at) and
`pub` (today's game skin); both sides; its four clips (91 frames); measured from rest and from each clip's first frame
(the stance, Prowl).

Per candidate piece (a rectangle in the patch's own s, theta), per surface / side / ref, over all frames:
    FLOOR      per-frame Kabsch fit of the piece's points (no rigid plate does better)
    bones      the game's ride (native_travel.ride: sum share * bone motion / sum shares) over clavicle, upperarm,
               upperarm_share, delt, scap; shares >= 0 chosen by a linear program minimising sink+ max (+0.05 gap max)
    bones+sph  the same blend with one sphere turn (clavicle -> upperarm about the shoulder joint) as a sixth member,
               best t of 0..1 step 0.1
    numbers    sink+ max / p95 (skin up into the plate, mm), gap max (the plate lifting off: most negative sink), travel max
With ref first the rides are each bone's motion FROM the clip's first frame (the plate seated in the stance).

    python tools/armor/split_size.py                      (first run builds a cache of the tracks, about 5 minutes)
    python tools/armor/split_size.py --out DIR --sph-surfaces new
    python tools/armor/split_size.py --partition          the skin-fitted pieces: FLOOR vs the game's rigid-part form
                                                          (mean_ride, + carried shapes) on PUB, and edge openings

Outputs (--out, default godot/.shots/gear_p2/split_size): tracks.npz (cache), sweep.json, table.txt, partition.json.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

ROOT = Path(__file__).resolve().parents[2]
P1 = ROOT.parent / "body-p1b" if (ROOT.parent / "body-p1b").exists() else Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\body-p1b")
SIDES, KINDS = ("l", "r"), ("new", "pub")
BONES = ("clavicle", "upperarm", "share", "delt", "scap")                     # the brief's set
EXTRA = {"trap": "trap_{s}", "tw1": "upperarm_twist_01_{s}", "tw2": "upperarm_twist_02_{s}", "tw3": "upperarm_twist_03_{s}",
         "tw4": "upperarm_twist_04_{s}"}                                     # body B's other helpers about the arm ("all")
TS = tuple(round(0.1 * i, 1) for i in range(11))
S_EXT = (-0.088, 0.154)
LIMIT_SINK, LIMIT_GAP = 5.0, 8.0


# ------------------------------------------------------------------------------------------- the tracks (P1's tool)

def build_cache(path):
    sys.path.insert(0, str(P1 / "tools" / "body"))
    import ride_travel as rtv
    cfg = dict(rtv.HER)
    cfg["patch"] = dict(cfg["patch"], s=S_EXT)
    cfg["sphere"] = dict(cfg["sphere"], t=TS)
    cfg["rides"] = dict(cfg["rides"], **EXTRA)
    tracks, frames, pat = rtv.her_tracks(cfg, SIDES, list(KINDS), list(cfg["clips"]))
    out = {"frames": np.array([f"{c}@{f}" for c, f in frames])}
    for s in SIDES:
        out[f"s_{s}"], out[f"th_{s}"] = pat[s]["s"], pat[s]["th"]
    for (k, s), tr in tracks.items():
        p = f"{k}_{s}_"
        out[p + "P0"], out[p + "N0"], out[p + "P"], out[p + "N"], out[p + "area"] = tr.P0, tr.N0, tr.P, tr.N, tr.area
        for b in list(BONES) + list(EXTRA):
            if b in tr.rides:
                out[p + "R_" + b] = tr.rides[b]
        for t in TS:
            out[p + f"R_sph{t:g}"] = tr.rides[f"sphere {t:g}"]
    np.savez_compressed(path, **out)


def rigid_fit(X0, X, w):
    w = w / w.sum()
    c0, c = w @ X0, w @ X
    H = ((X0 - c0) * w[:, None]).T @ (X - c)
    U, _, Vt = np.linalg.svd(H)
    D = np.diag([1.0, 1.0, np.sign(np.linalg.det(Vt.T @ U.T))])
    R = Vt.T @ D @ U.T
    return R, c - R @ c0


class Case:
    """One surface / side / ref: X0 [F, n, 3] (each frame's reference point), P, N [F, n, 3], rides {m: [F, 4, 4]}."""

    def __init__(self, z, k, s, ref):
        p = f"{k}_{s}_"
        fr = [x.split("@")[0] for x in z["frames"]]
        P, N, P0 = z[p + "P"], z[p + "N"], z[p + "P0"]
        F = len(P)
        first = np.array([fr.index(c) for c in fr])
        names = list(BONES) + [b for b in EXTRA if p + "R_" + b in z] + [f"sph{t:g}" for t in TS]
        self.extra = [b for b in EXTRA if p + "R_" + b in z]
        R = {m: z[p + "R_" + m] for m in names}
        if ref == "first":
            self.X0 = P[first]
            R = {m: M @ np.linalg.inv(M[first]) for m, M in R.items()}
        else:
            self.X0 = np.broadcast_to(P0, P.shape)
        self.P, self.N, self.area, self.R, self.names = P, N, z[p + "area"], R, names
        self.s, self.th = z[f"s_{s}"] * 1e3, z[f"th_{s}"]
        self.first, self.F = first, F
        # each member's carried points and their sink coefficient b = Q . N; a = P . N
        self.Q = {m: np.einsum("fij,fnj->fni", M[:, :3, :3], self.X0) + M[:, None, :3, 3] for m, M in R.items()}
        self.a = (P * N).sum(2)
        self.b = {m: (Q * N).sum(2) for m, Q in self.Q.items()}

    def mask(self, s0, s1, t0, t1):
        return (self.s >= s0) & (self.s <= s1) & (self.th >= t0) & (self.th <= t1)

    def nums(self, sel, Q):
        d = self.P[:, sel] - Q
        sink = (d * self.N[:, sel]).sum(2) * 1e3
        sp = sink.max(0)
        return {"sink": round(float(max(sp.max(), 0)), 2), "sink_p95": round(float(max(np.percentile(sp, 95), 0)), 2),
                "gap": round(float(max(-sink.min(), 0)), 2), "travel": round(float(np.linalg.norm(d, axis=2).max() * 1e3), 2),
                "spread": round(float(sink.max() - sink.min()), 2)}      # sink + gap: what no seat height (standoff) changes

    def floor(self, sel):
        Q = np.empty((self.F, sel.sum(), 3))
        for f in range(self.F):
            R, t = rigid_fit(self.X0[f][sel], self.P[f][sel], self.area[sel])
            Q[f] = self.X0[f][sel] @ R.T + t
        return self.nums(sel, Q)

    def blend(self, sel, members):
        """The LP: shares w >= 0, sum 1, minimise the spread z + g (a free seat height trades sink for gap) with sink <= z, -sink <= g (m; rows added as violated)."""
        a = self.a[:, sel].ravel()
        B = np.stack([self.b[m][:, sel].ravel() for m in members], 1)       # sink = a - B w
        K = len(members)
        act = np.unique(np.r_[np.argsort(-(a - B.mean(1)))[:400], np.argsort(a - B.mean(1))[:400]])
        w = np.full(K, 1.0 / K)
        for _ in range(12):
            nA = len(act)
            A_ub = np.zeros((2 * nA, K + 2))
            A_ub[:nA, :K], A_ub[:nA, K] = -B[act], -1.0
            A_ub[nA:, :K], A_ub[nA:, K + 1] = B[act], -1.0
            b_ub = np.r_[-a[act], a[act]]
            r = linprog(np.r_[np.zeros(K), 1.0, 0.98], A_ub=A_ub, b_ub=b_ub, A_eq=np.r_[np.ones(K), 0, 0][None], b_eq=[1.0],
                        bounds=[(0, None)] * K + [(None, None)] * 2, method="highs")
            if r.status != 0:
                break
            w, z, g = r.x[:K], r.x[K], r.x[K + 1]
            sk = a - B @ w
            viol = np.where((sk > z + 1e-6) | (-sk > g + 1e-6))[0]
            if not len(viol):
                break
            new = np.setdiff1d(np.r_[viol[np.argsort(-sk[viol])[:300]], viol[np.argsort(sk[viol])[:300]]], act)
            if not len(new):
                break
            act = np.r_[act, new]
        Q = sum(wi * self.Q[m][:, sel] for wi, m in zip(w, members))
        return self.nums(sel, Q), {m: round(float(wi), 3) for m, wi in zip(members, w) if wi > 1e-3}

    def best(self, sel, sph=True):
        nb, wb = self.blend(sel, list(BONES))
        out = {"bones": {**nb, "shares": wb}}
        if sph:
            cand = []
            for t in TS:
                n, w = self.blend(sel, list(BONES) + [f"sph{t:g}"])
                cand.append((n["spread"], t, n, w))
            _, t, n, w = min(cand, key=lambda c: c[0])
            out["bones+sph"] = {**n, "t": t, "shares": w}
            n, w = self.blend(sel, list(BONES) + self.extra + [f"sph{t:g}"])
            out["all"] = {**n, "t": t, "shares": w}
        return out

    def opening(self, sel_edge, ma, mb):
        """Max |ride A x - ride B x| over the frames at the shared-edge points (rides as share dicts), mm."""
        def q(rule):
            return sum(v * self.Q[m][:, sel_edge] for m, v in rule.items()) / sum(rule.values())
        d = q(ma) - q(mb)
        dn = np.abs((d * self.N[:, sel_edge]).sum(2))
        return round(float(np.linalg.norm(d, axis=2).max() * 1e3), 2), round(float(dn.max() * 1e3), 2)


def candidates():
    cs = [("check", -45, 36, 60.0, 130.0)]          # P1's cap_top zone of the cop box: the floor should match P1's
    for s0 in (-60, -45, -30, -15, 0, 15):
        for ln in (25, 35, 50, 70):
            for c in (80, 96, 110):
                for wd in (50, 80, 110, 150):
                    cs.append(("cap", s0, s0 + ln, max(21.0, c - wd / 2), min(172.0, c + wd / 2)))
    for a in range(-30, 151, 10):
        for wd in (10, 20, 30, 40, 60):
            if a + wd <= 164:
                cs.append(("lame", a, min(a + wd, 154), 21.0, 172.0))
    return cs


# ------------------------------------------------------------- the game's rigid-part form (gear_native.part_blends)

PIECES = {"A": (-45, -10, 35, 172), "B": (-10, 10, 70, 150), "C": (10, 30, 70, 150), "D": (30, 50, 70, 150),
          "L1": (50, 70, 21, 172), "L2": (70, 90, 21, 172), "L3": (90, 110, 21, 172), "L4": (110, 130, 21, 172),
          "L5": (130, 154, 21, 172)}                                       # the skin-fitted partition (facts.md section 2)
CARRY_SHAPES = ("arm_hang_", "elbow_")                                    # gear_native.CARRY_SHAPES


def build_game_cache(path):
    """Per frame (her_tracks' order): her bone skinning matrices S = G @ ibm and her corrective shapes' weights (the
    `pub` surface's own: region_target.published = poser._skin(G, rig_drive.corrective_weights)); per side the patch
    vertices' rest points, skin weights, areas and the shapes' deltas on them."""
    sys.path.insert(0, str(P1 / "tools" / "body"))
    import carried_target as ct
    import deform_audit as da
    import ride_travel as rtv
    cfg = dict(rtv.HER)
    cfg["patch"] = dict(cfg["patch"], s=S_EXT)
    h = ct.Her(verbose=False)
    B, pz = h.bd, h.bd.p
    T = np.asarray(B.T, np.int64)
    frs = rtv.shoulder_frames(B.V0, T, B.head, cfg)
    area = rtv.vertex_area(B.V0, T)
    S, CW = [], []
    for c in cfg["clips"]:
        for f, _, G in B.clip_frames(da.load_clip(c), 1):
            S.append(np.array(G) @ pz.skel.ibm)
            CW.append(B.rd.corrective_weights(pz, np.array(G), B.rig))
    names = sorted(pz.targets)
    out = {"S": np.array(S), "cw": np.array([[float(w.get(k, 0.0) or 0.0) for k in names] for w in CW]), "shapes": np.array(names)}
    inv = {v: k for k, v in pz.index.items()} if hasattr(pz, "index") else {}
    out["joints"] = np.array([inv.get(i, str(i)) for i in range(out["S"].shape[1])])
    for s in SIDES:
        ids = rtv.footprint(B.V0, T, frs[s], *cfg["patch"]["s"], *cfg["patch"]["theta"], cfg["patch"]["rmax"])
        out[f"{s}_X"], out[f"{s}_J"], out[f"{s}_W"], out[f"{s}_A"] = pz.Pb[ids], pz.J[ids], pz.W[ids], area[ids]
        out[f"{s}_dP"] = np.array([pz.targets[k][ids] for k in names])
    np.savez_compressed(path, **out)


def game_ride(g, s, sel, shapes, top=8):
    """([F, 4, 4] the part's ride from rest, shapes carried, {bone: share}): native_spaulder.mean_ride (the area-
    weighted mean of her skin weights over its points, top 8 bones) of S, after her shapes each as ONE rigid motion (the
    rigid fit of its delta over the points) scaled by its weight in the frame. shapes: "none", "carry" (CARRY_SHAPES),
    "all" (every shape non-zero on the points)."""
    X, J, W, A = g[f"{s}_X"][sel], g[f"{s}_J"][sel], g[f"{s}_W"][sel], g[f"{s}_A"][sel]
    D = np.zeros(g["S"].shape[1])
    np.add.at(D, J.reshape(-1), (W * A[:, None]).reshape(-1))
    j = [int(a) for a in np.argsort(-D)[:top] if D[a] > 0]
    sh = D[j] / D[j].sum()
    M = np.einsum("j,fjab->fab", sh, g["S"][:, j])
    Aff, nf = np.tile(np.eye(4), (len(M), 1, 1)), 0
    for k, nm in enumerate(g["shapes"]):
        dP = g[f"{s}_dP"][k][sel]
        if shapes == "none" or np.abs(dP).max() <= 1e-5 or not (shapes == "all" or str(nm).startswith(CARRY_SHAPES)):
            continue
        R, t = rigid_fit(X, X + dP, A)
        Af = np.zeros((4, 4))
        Af[:3, :3], Af[:3, 3] = R - np.eye(3), t
        Aff = Aff + g["cw"][:, k, None, None] * Af           # X + sum w (X R^T + t - X): one affine map per frame
        nf += 1
    return M @ Aff, nf, {str(g["joints"][a]): round(float(v), 3) for a, v in zip(j, sh)}


def floor_Q(c, sel, X):
    Q = np.empty((c.F, X.sum(), 3))
    for f in range(c.F):
        R, t = rigid_fit(c.X0[f][sel], c.P[f][sel], c.area[sel])
        Q[f] = c.X0[f][X] @ R.T + t
    return Q


def partition(z, out, refs, pieces=None, tag=""):
    """The skin-fitted partition (PIECES): per piece the FLOOR, the game's form (mean_ride; + CARRY_SHAPES; + all her
    shapes) on PUB, and the neighbours' opening at each shared s edge (both skin-fitted, points within 6 mm). pieces:
    {name: (s0, s1, t0, t1)} in order along the arm (PIECES when None); tag: the output files' suffix. The line's
    NEW column is the FLOOR on the `new` surface (P1's carried target)."""
    pieces = pieces or PIECES
    gp = out / "game.npz"
    if not gp.exists():
        build_game_cache(gp)
    g = dict(np.load(gp))
    res, lines = [], ["piece box | ref side | FLOOR sink/gap/spread | mean_ride | +carry(n) | +all(n)  (PUB; mm)"]
    for ref in refs:
        for s in SIDES:
            cs = Case(z, "pub", s, ref)
            chk = float(np.abs(g[f"{s}_X"] - z[f"pub_{s}_P0"]).max()) * 1e3
            M, _, _ = game_ride(g, s, np.ones(len(cs.s), bool), "none")
            lines.append(f"check {ref} {s}: rest points vs tracks {chk:.4f} mm")
            cn = Case(z, "new", s, ref)
            for nm, bx in pieces.items():
                sel = cs.mask(*bx)
                r = {"ref": ref, "side": s, "piece": nm, "box": bx, "n": int(sel.sum()), "floor": cs.floor(sel),
                     "floor_new": cn.floor(cn.mask(*bx))}
                for v in ("none", "carry", "all"):
                    M, nf, sh = game_ride(g, s, sel, v)
                    if ref == "first":
                        M = M @ np.linalg.inv(M[cs.first])
                    Q = np.einsum("fij,fnj->fni", M[:, :3, :3], cs.X0[:, sel]) + M[:, None, :3, 3]
                    r[v] = {**cs.nums(sel, Q), "shapes": nf, "ride": sh if v == "none" else None}
                res.append(r)
                f = r["floor"]
                lines.append(f"{nm:3s} {bx} | {ref:5s} {s} | {f['sink']:5.1f}/{f['gap']:5.1f}/{f['spread']:5.1f} | " +
                             " | ".join(f"{r[v]['sink']:5.1f}/{r[v]['gap']:5.1f}/{r[v]['spread']:5.1f}" + (f"({r[v]['shapes']})" if v != "none" else "")
                                        for v in ("none", "carry", "all")) + f" | NEW floor {r['floor_new']['spread']:5.1f}")
            for k in KINDS:
                c2 = Case(z, k, s, ref)
                ks = list(pieces)
                for a_, b_ in zip(ks, ks[1:]):
                    A_, B_ = pieces[a_], pieces[b_]
                    e = A_[1]
                    ed = c2.mask(e - 6, e + 6, max(A_[2], B_[2]), min(A_[3], B_[3]))
                    if not ed.any():
                        continue
                    d = floor_Q(c2, c2.mask(*A_), ed) - floor_Q(c2, c2.mask(*B_), ed)
                    o = (round(float(np.linalg.norm(d, axis=2).max() * 1e3), 1), round(float(np.abs((d * c2.N[:, ed]).sum(2)).max() * 1e3), 1))
                    res.append({"ref": ref, "side": s, "surface": k, "edge": f"{a_}|{b_}", "s": e, "n": int(ed.sum()), "open_mm": o})
                    if k == "pub":                   # the game's form: the two parts' own rides (mean_ride + carry) at the edge
                        def gq(bx):
                            M = game_ride(g, s, cs.mask(*bx), "carry")[0]
                            if ref == "first":
                                M = M @ np.linalg.inv(M[cs.first])
                            return np.einsum("fij,fnj->fni", M[:, :3, :3], cs.X0[:, ed]) + M[:, None, :3, 3]
                        d = gq(A_) - gq(B_)
                        og = (round(float(np.linalg.norm(d, axis=2).max() * 1e3), 1), round(float(np.abs((d * c2.N[:, ed]).sum(2)).max() * 1e3), 1))
                        dn = (d * c2.N[:, ed]).sum(2)    # (+: the upper part off the lower, -: the lower up into it)
                        cl = (round(float(max(-dn.min(), 0) * 1e3), 1), round(float(max(dn.max(), 0) * 1e3), 1))
                        res[-1]["open_game_mm"], res[-1]["close_lift_mm"] = og, cl
                        lines.append(f"edge game {ref} {s} {a_}|{b_} s{e}: n{int(ed.sum())} open {og[0]} / normal {og[1]}"
                                     f" (lower into upper {cl[0]}, upper off {cl[1]})")
                    lines.append(f"edge {k} {ref} {s} {a_}|{b_} s{e}: n{int(ed.sum())} open {o[0]} / normal {o[1]}")
    (out / f"partition_game{tag}.json").write_text(json.dumps(res, indent=1, default=list))
    (out / f"partition_game{tag}.txt").write_text("\n".join(lines))
    print("\n".join(lines))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=str(ROOT / "godot" / ".shots" / "gear_p2" / "split_size"))
    ap.add_argument("--sph-surfaces", nargs="+", default=list(KINDS), help="surfaces the sphere-turn scan runs on (11 LPs each)")
    ap.add_argument("--refs", nargs="+", default=["first", "rest"])
    ap.add_argument("--partition", action="store_true", help="only the skin-fitted partition: floor vs the game's form, edges")
    ap.add_argument("--pieces", help='candidate boxes for --partition, JSON {"name": [s0, s1, t0, t1], ..} in order along the arm')
    ap.add_argument("--tag", default="", help="--partition's output files' suffix")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    if not (out / "tracks.npz").exists():
        build_cache(out / "tracks.npz")
    z = dict(np.load(out / "tracks.npz"))
    print(f"tracks: {len(z['frames'])} frames, patch l {len(z['s_l'])} / r {len(z['s_r'])} points, s {z['s_l'].min()*1e3:.0f}..{z['s_l'].max()*1e3:.0f} mm ({time.time()-t0:.0f} s)")
    if a.partition:
        partition(z, out, a.refs, {k: tuple(v) for k, v in json.loads(a.pieces).items()} if a.pieces else None, a.tag)
        print(f"wrote {out} ({time.time()-t0:.0f} s)")
        return
    rows = []
    for ref in a.refs:
        for k in KINDS:
            for s in SIDES:
                cs = Case(z, k, s, ref)
                for kind, s0, s1, t0_, t1 in candidates():
                    sel = cs.mask(s0, s1, t0_, t1)
                    if sel.sum() < 12:
                        continue
                    r = {"ref": ref, "surface": k, "side": s, "kind": kind, "box": [s0, s1, t0_, t1], "n": int(sel.sum()),
                         "floor": cs.floor(sel), **cs.best(sel, k in a.sph_surfaces)}
                    rows.append(r)
                print(f"  {ref} {k} {s}: done ({time.time()-t0:.0f} s)", flush=True)
    (out / "sweep.json").write_text(json.dumps(rows))
    # the table: per box, NEW L/R from first, the realistic ride (best of bones / bones+sph) and the floor
    def real(r):
        best = r["bones"]
        for fam in ("bones+sph", "all"):
            if fam in r and r[fam]["spread"] < best["spread"] - 0.5:
                best = dict(r[fam], family=fam)
        return best
    idx = {(r["ref"], r["surface"], r["side"], tuple(r["box"])): r for r in rows}
    lines = ["box s0 s1 theta0 theta1 | per ref/surface/side: n  FLOOR sink/p95/gap/trav  REAL sink/p95/gap/trav ride (mm)"]
    boxes = list(dict.fromkeys(tuple(r["box"]) for r in rows))
    for bx in boxes:
        lines.append(f"{bx[0]:4.0f} {bx[1]:4.0f} {bx[2]:5.0f} {bx[3]:5.0f}")
        for ref in a.refs:
            for k in KINDS:
                for s in SIDES:
                    r = idx.get((ref, k, s, bx))
                    if not r:
                        continue
                    f, re = r["floor"], real(r)
                    tag = ("sph%g " % re["t"] if "t" in re else "") + ",".join(f"{m}{v:.2f}" for m, v in re["shares"].items())
                    lines.append(f"   {ref:5s} {k} {s} n{r['n']:4d}  F {f['sink']:5.1f}/{f['sink_p95']:5.1f}/{f['gap']:5.1f}/{f['travel']:5.1f}"
                                 f"  R {re['sink']:5.1f}/{re['sink_p95']:5.1f}/{re['gap']:5.1f}/{re['travel']:5.1f} {tag}")
    (out / "table.txt").write_text("\n".join(lines))
    # the partition: the largest cap piece passing on NEW from first, both sides; then lames to +154 greedily
    def ok(bx, ref="first", k="new"):
        rs = [idx.get((ref, k, s, bx)) for s in SIDES]
        return all(r and real(r)["spread"] <= LIMIT_SINK + LIMIT_GAP for r in rs)     # some seat height meets both
    def size(bx):
        return min(idx[("first", "new", s, bx)]["n"] for s in SIDES)
    caps = [bx for bx in boxes if idx.get(("first", "new", "l", bx), {}).get("kind") == "cap" and ok(bx)]
    part = {"cap": None, "lames": [], "edges": []}
    if caps:
        cap = max(caps, key=size)
        part["cap"] = cap
        cur = cap[1]
        lames = [bx for bx in boxes if idx.get(("first", "new", "l", bx), {}).get("kind") == "lame"]
        while cur < 154:
            nxt = [bx for bx in lames if abs(bx[0] - cur) <= 5 and ok(bx)]
            if not nxt:
                part["stuck_at"] = cur
                break
            bx = max(nxt, key=lambda b: b[1])
            part["lames"].append(bx)
            cur = bx[1]
        # shared-edge openings (NEW and PUB, both refs): points within 6 mm of the shared s edge, the edge's theta span
        chain = [cap] + part["lames"]
        for ref in a.refs:
            for k in KINDS:
                for s in SIDES:
                    cs = Case(z, k, s, ref)
                    for A_, B_ in zip(chain, chain[1:]):
                        e = 0.5 * (A_[1] + B_[0])
                        sel = cs.mask(e - 6, e + 6, max(A_[2], B_[2]), min(A_[3], B_[3]))
                        ra, rb = real(idx[(ref, k, s, A_)])["shares"], real(idx[(ref, k, s, B_)])["shares"]
                        ra = {(f"sph{real(idx[(ref, k, s, A_)])['t']:g}" if m.startswith("sph") else m): v for m, v in ra.items()}
                        rb = {(f"sph{real(idx[(ref, k, s, B_)])['t']:g}" if m.startswith("sph") else m): v for m, v in rb.items()}
                        if sel.sum():
                            part["edges"].append({"ref": ref, "surface": k, "side": s, "edge_s": e, "n": int(sel.sum()),
                                                  "open_mm": cs.opening(sel, ra, rb)})
    (out / "partition.json").write_text(json.dumps(part, indent=1, default=list))
    print(json.dumps(part, default=list)[:3000])
    print(f"wrote {out} ({time.time()-t0:.0f} s)")


if __name__ == "__main__":
    main()
