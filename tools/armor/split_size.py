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


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=str(ROOT / "godot" / ".shots" / "gear_p2" / "split_size"))
    ap.add_argument("--sph-surfaces", nargs="+", default=list(KINDS), help="surfaces the sphere-turn scan runs on (11 LPs each)")
    ap.add_argument("--refs", nargs="+", default=["first", "rest"])
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    if not (out / "tracks.npz").exists():
        build_cache(out / "tracks.npz")
    z = dict(np.load(out / "tracks.npz"))
    print(f"tracks: {len(z['frames'])} frames, patch l {len(z['s_l'])} / r {len(z['s_r'])} points, s {z['s_l'].min()*1e3:.0f}..{z['s_l'].max()*1e3:.0f} mm ({time.time()-t0:.0f} s)")
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
