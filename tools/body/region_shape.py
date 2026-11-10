"""region_shape: the SHAPE half of the shoulder target's gate (WIP, T2 solver for lead 14): does a surface keep her shape?

    python tools/body/region_shape.py shift --provider pub|target|lbs_base|a [--poses a,b | --only train,held,extreme | --clip NAME]
    python tools/body/region_shape.py pops  --provider ... --clips run_warden,sword_heavy,p4:bladestorm_loop
  NOT BUILT YET (context cap): silhouette, sheets.

Pose names: rest[:s] | x:<extreme>[:s] | <clip>@<frame>[:s] (p4:<clip>@f too); side l by default. Out: tools/body/out/shoulder.
Providers (pose -> whole-body B vertices): pub = published B; target = region_target live (full_target), or target.npz +
  region.npz when the pose is in it; lbs_base = the target's base LBS blended by beta; a = A's own surface (test: 0).
A in the same pose: library clips = A's own dump frame; extremes and p4 clips = A posed by B's driven bone turns from rest
  (A spine_01/02/03 <- B spine_02/03/05, the rest by name).
shift: per band point, the signed distance (mm, + outward) to A's posed surface along A's interpolated normal, minus the
  same at rest. A is brought to B per band by the band's ANCHOR bone (D_B D_A^-1, D = posed global x rest^-1), so a skeleton
  difference (B's girdle law against A's keyed clavicle) is not read as shape. The closest point is searched only on the A
  triangles within RAD 50 mm of the point at rest whose rest normal faces the same way (no jump across the armpit).
Bands (B rest, left topology points inside the region; the right = the twins; disjoint, in this priority):
  fold_front / fold_back  within 3 rows of the seam between the arm class and the torso class (region_target's armv), more
                          than 20 mm below the joint, not on the arm's outer side (lateral < 20 mm), 10 mm in front of /
                          behind the joint: the pectoral edge and the lat edge
  deltoid_cap             within 0.12 m of the shoulder joint, lateral of it, rest normal not facing down (n.up > -0.3)
  trap_line               outside that ball, 30 mm from the midline to the joint, above the joint - 30 mm, n.up > 0.6
  breast_edge             region points within 7 rows (the border ring 3 + blend 4) of the left breast part
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import deform_audit as da  # noqa: E402
import region_target as rt  # noqa: E402
from surfdist import closest_on_tris  # noqa: E402

OUT = rt.OUT
BANDS = ["fold_front", "fold_back", "deltoid_cap", "trap_line", "breast_edge"]
ANCHOR = {"fold_front": "chest", "fold_back": "chest", "deltoid_cap": "upperarm", "trap_line": "clavicle", "breast_edge": "chest"}
RAD, K = 0.05, 64
SPINE = {"spine_01": "spine_02", "spine_02": "spine_03", "spine_03": "spine_05"}
turn = lambda G, R0, j: da.ortho(G[j][:3, :3] @ np.linalg.inv(R0[j][:3, :3]))


class Near:
    """Signed distance of points to a posed mesh, each point against the triangles near it at rest."""

    def __init__(self, P0, N0, bd):
        self.bd, T = bd, bd.T
        c = bd.V0[T].mean(1)
        fn = da.unit(np.cross(bd.V0[T[:, 1]] - bd.V0[T[:, 0]], bd.V0[T[:, 2]] - bd.V0[T[:, 0]]))
        d, i = cKDTree(c).query(P0, k=K, distance_upper_bound=RAD)
        ok = np.isfinite(d)
        i = np.where(ok, i, 0)
        self.ok = ok & (np.einsum("nkj,nj->nk", fn[i], N0) > 0)
        self.tri = T[i]

    def signed(self, P, V):
        """(signed distance [n] m, closest point [n, 3]) of P against the mesh at V."""
        n, k = self.ok.shape
        a, b, c = (V[self.tri[..., j]].reshape(-1, 3) for j in range(3))
        p = np.repeat(P, k, 0)
        q = closest_on_tris(p, a, b, c)
        d = np.where(self.ok.ravel(), np.linalg.norm(p - q, axis=1), np.inf).reshape(n, k)
        j = d.argmin(1) + np.arange(n) * k
        q, t = q[j], self.tri.reshape(-1, 3)[j]
        A_, B_, C_ = V[t[:, 0]], V[t[:, 1]], V[t[:, 2]]
        nt = np.cross(B_ - A_, C_ - A_)
        ar = np.maximum((nt ** 2).sum(1), 1e-30)
        bw = np.stack([np.einsum("ij,ij->i", np.cross(C_ - B_, q - B_), nt), np.einsum("ij,ij->i", np.cross(A_ - C_, q - C_), nt),
                       np.einsum("ij,ij->i", np.cross(B_ - A_, q - A_), nt)], 1) / ar[:, None]
        N = self.bd._normals(V)
        nq = (np.clip(bw, 0, 1)[:, :, None] * N[t]).sum(1)
        nq /= np.maximum(np.linalg.norm(nq, axis=1, keepdims=True), 1e-12)
        sd = np.einsum("ij,ij->i", P - q, nq)
        sd[~self.ok.any(1)] = np.nan
        return sd, q


class Ctx:
    def __init__(self):
        self.B, self.A = da.body("B"), da.body("A")
        self.B.set_layer("full")
        self.A.set_layer("full")
        self.md = md = rt.Model(self.B.p)
        B, A = self.B, self.A
        self.sg = {"l": 1, "r": -1}
        cl = lambda bd, s: bd.p.names[bd.p.parent[bd.p.index[bd.role("upperarm", s)]]]
        self.anch = {s: {"upperarm": (B.role("upperarm", s), A.role("upperarm", s)), "clavicle": (cl(B, s), cl(A, s)),
                         "chest": tuple(bd.p.names[bd.p.parent[bd.p.index[cl(bd, s)]]] for bd in (B, A))} for s in "lr"}
        self.bands = self._bands()
        N0 = B._normals(B.V0)
        self.near, self.sd0, self.q0 = {}, {}, {}
        for s in "lr":
            for b in BANDS:
                v = md.first[self.bands[b][s]]
                nr = self.near[b, s] = Near(B.V0[v], N0[v], A)
                self.sd0[b, s], self.q0[b, s] = nr.signed(B.V0[v], A.V0)
        self._tz = None

    def _bands(self):
        B, md = self.B, self.md
        fr, sd = B.frame, md.S["l"]
        ids, n = sd["ids"], md.n
        H = B.head("upperarm_l")
        r = md.V0 - H
        N = B._normals(B.V0)[md.first]
        inr = np.zeros(n, bool)
        inr[ids] = True
        arm = np.zeros(n, bool)
        arm[ids[sd["armv"]]] = True

        def grow(m, rows):
            for _ in range(rows):
                m = m | (md.adj @ m > 0)
            return m
        seam = grow(arm, 1) & grow(inr & ~arm, 1) & inr
        fold = grow(seam, 3) & inr & (r @ fr.up < -0.02) & (r @ fr.lat < 0.02)
        ball = np.linalg.norm(r, axis=1) < 0.12
        topo = np.load(rt.HERE / "out/topo/close.npz", allow_pickle=True)
        breast = (topo["part"] == list(topo["parts"]).index("breast")) & (topo["side"] == 1)
        m = {"fold_front": fold & (r @ fr.front > 0.01), "fold_back": fold & (r @ fr.front < -0.01),
             "deltoid_cap": inr & ball & (r @ fr.lat > 0) & (N @ fr.up > -0.3),
             "trap_line": inr & ~ball & (md.V0 @ fr.lat > 0.03) & (r @ fr.lat < 0) & (r @ fr.up > -0.03) & (N @ fr.up > 0.6),
             "breast_edge": inr & grow(breast, 7)}
        used, out = np.zeros(n, bool), {}
        for b in BANDS:
            l = np.nonzero(m[b] & ~used)[0]
            used[l] = True
            out[b] = {"l": l, "r": md.tw[l]}
        OUT.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(OUT / "bands.npz", **{f"{b}_{s}": v[s] for b, v in out.items() for s in "lr"},
                            **{f"{b}_v{s}": md.first[v[s]] for b, v in out.items() for s in "lr"})
        return out

    # ------------------------------------------------------------------ poses --
    def a_from_B(self, G):
        """A posed by B's driven bone turns from rest."""
        B, A = self.B, self.A
        want = ["pelvis", "spine_01", "spine_02", "spine_03", "neck_01"] + [f"{b}_{s}" for s in "lr" for b in ("clavicle", "upperarm", "lowerarm", "hand")]
        turns, done = [], {}
        for an in want:
            bn = SPINE.get(an, an)
            if an not in A.p.index or bn not in B.p.index:
                continue
            Rb = turn(G, B.p.rest, B.p.index[bn])
            k, Rp = A.p.parent[A.p.index[an]], np.eye(3)
            while k >= 0 and k not in done:
                k = A.p.parent[k]
            if k >= 0:
                Rp = done[k]
            turns.append((an, Rb @ Rp.T))
            done[A.p.index[an]] = Rb
        return A.pose_turns(turns)

    def poses(self, names):
        """Yield {name, side, G, A: (V, G)} for pose names (grouped by clip)."""
        B, A, by = self.B, self.A, {}
        for nm in names:
            core, s = (nm[:-2], nm[-1]) if nm[-2:] in (":l", ":r") else (nm, "l")
            if core == "rest":
                yield {"name": nm, "side": s, "G": B.G0, "A": (A.V0, A.G0)}
            elif core.startswith("x:"):
                G = rt.extreme_G(B, core[2:])[0]
                G = G if s == "l" else B.rd.drive(B.p, self.md.mirror_G(G), B.rig)[0]
                yield {"name": nm, "side": s, "G": G, "A": self.a_from_B(G)}
            else:
                c, f = core.rsplit("@", 1)
                by.setdefault(c, {}).setdefault(int(f), []).append((nm, s))
        for c, fs in by.items():
            Gs = {f: G for f, _, G in B.clip_frames(da.load_clip(c), 1) if f in fs}
            Af = {} if c.startswith("p4:") else rt.a_frames(A, c, set(fs))
            for f, lst in fs.items():
                for nm, s in lst:
                    yield {"name": nm, "side": s, "G": Gs[f], "A": Af[f] if f in Af else self.a_from_B(Gs[f])}

    # -------------------------------------------------------------- providers --
    def surface(self, kind, pose):
        B, md, G, s = self.B, self.md, pose["G"], pose["side"]
        Vp = rt.published(B, G)
        if kind == "pub":
            return Vp
        sd = md.S[s]
        nr = len(sd["ids"])
        if kind == "lbs_base":
            X = md.beta[:, None] * md._lbs(sd, G)[:nr] + (1 - md.beta[:, None]) * Vp[md.first[sd["ids"]]]
        elif kind == "target":
            if self._tz is None:
                self._tz = dict(np.load(OUT / "target.npz")) if (OUT / "target.npz").exists() else {}
                self._ti = {str(n): i for i, n in enumerate(self._tz.get("name", []))}
            i = self._ti.get(pose["name"] if pose["name"][-2:] in (":l", ":r") else pose["name"] + ":l")
            X = self._tz["X"][i] if i is not None and self._tz["X"].shape[1] == nr else md.target(G, Vp[md.first], s)
        else:
            raise KeyError(kind)
        g = np.nonzero(sd["loc"][md.src] >= 0)[0]
        g = g[sd["loc"][md.src[g]] < nr]
        V = Vp.copy()
        V[g] = X[sd["loc"][md.src[g]]]
        return V

    def align(self, pose, anchor):
        """4x4 taking A's posed surface onto B's by the anchor bone."""
        bn, an = self.anch[pose["side"]][anchor]
        jb, ja = self.B.p.index[bn], self.A.p.index[an]
        Ga = np.asarray(pose["A"][1])
        M = pose["G"][jb] @ np.linalg.inv(self.B.p.rest[jb]) @ np.asarray(self.A.G0)[ja] @ np.linalg.inv(Ga[ja])
        M[:3, :3] = da.ortho(M[:3, :3])
        return M

    def shift(self, kind, pose, V=None):
        """{band: per-point shift (m)} of a provider's surface against A, the rest offset removed."""
        s, out = pose["side"], {}
        Va = pose["A"][0]
        if V is None and kind != "a":
            V = self.surface(kind, pose)
        for b in BANDS:
            nr, M = self.near[b, s], self.align(pose, ANCHOR[b])
            if kind == "a":
                P, d0 = self._carry(nr, self.q0[b, s], Va), 0.0         # A's own points, carried by A
            else:
                P, d0 = (V[self.md.first[self.bands[b][s]]] - M[:3, 3]) @ M[:3, :3], self.sd0[b, s]
            out[b] = nr.signed(P, Va)[0] - d0
        return out

    def _carry(self, nr, q0, Va):
        """Points on A's rest surface (q0) carried to A's posed surface by their triangle's barycentrics."""
        A0 = self.A.V0
        n, k = nr.ok.shape
        tri = nr.tri.reshape(-1, 3)
        a, b, c = (A0[tri[:, j]] for j in range(3))
        p = np.repeat(q0, k, 0)
        d = np.where(nr.ok.ravel(), np.linalg.norm(p - closest_on_tris(p, a, b, c), axis=1), np.inf).reshape(n, k)
        t = tri[d.argmin(1) + np.arange(n) * k]
        w = np.linalg.solve(np.swapaxes(A0[t], 1, 2) + 1e-12 * np.eye(3), q0[:, :, None])[:, :, 0]
        return np.einsum("nk,nkj->nj", w / w.sum(1, keepdims=True), Va[t])


def stats(x):
    x = x[np.isfinite(x)] * 1000
    return [round(float(v), 2) for v in (np.median(x), max(-np.percentile(x, 5), 0), max(-x.min(), 0), max(x.max(), 0))]


def cmd_shift(cx, a):
    if a.poses:
        names = a.poses.split(",")
    elif a.clip:
        n = da.load_clip(a.clip)["frames"]
        names = [f"{a.clip}@{f}:{s}" for f in range(n) for s in "lr"]
    else:
        z = np.load(OUT / "poses.npz")
        names = [str(n) for n, k in zip(z["name"], z["kind"]) if str(k) in a.only.split(",")]
    print("bands:", {b: len(v["l"]) for b, v in cx.bands.items()}, "| cols per band: p50 / in95 / inmax / outmax mm (+ outward)")
    rows = {}
    for pose in cx.poses(names):
        rows[pose["name"]] = r = {b: stats(v) for b, v in cx.shift(a.provider, pose).items()}
        if len(names) <= 40:
            print(f"{pose['name']:28s}" + "  ".join(f"{b[:6]} {'/'.join(f'{x:.1f}' for x in r[b])}" for b in BANDS), flush=True)
    (OUT / f"shift_{a.provider}.json").write_text(json.dumps(rows))
    print(f"{a.provider}: {len(rows)} poses. band: worst in95 / worst inmax (pose) / worst outmax | median p50 / in95 / inmax")
    for b in BANDS:
        v = np.array([r[b] for r in rows.values()])
        w = list(rows)[int(v[:, 2].argmax())]
        print(f"  {b:12s} {v[:, 1].max():.1f} / {v[:, 2].max():.1f} ({w}) / {v[:, 3].max():.1f} | "
              f"{np.median(v[:, 0]):.1f} / {np.median(v[:, 1]):.1f} / {np.median(v[:, 2]):.1f}")


def cmd_pops(cx, a):
    """The audit's pop (run_clip): the second difference in time of each shoulder region in its own rigid fit, mm."""
    B, A, res = cx.B, cx.A, {}
    regs = [r.replace("{s}", s) for s in "lr" for r in da.JOINTS["shoulder"]]
    for c in a.clips.split(","):
        d = da.load_clip(c)
        hist, best = {}, {}
        ait = None if c.startswith("p4:") else A.clip_frames(d, 1)
        for f, Vb, G in B.clip_frames(d, 1):
            cols = {"B": (B, Vb), "A": (A, cx.a_from_B(G)[0] if ait is None else next(ait)[1])}
            if a.provider != "pub":
                V = Vb
                for s in "lr":
                    Vs = cx.surface(a.provider, {"name": f"{c}@{f}:{s}", "side": s, "G": G})
                    g = np.abs(Vs - Vb).max(1) > 0
                    V = np.where(g[:, None], Vs, V)
                cols["P"] = (B, V)
            for col, (bd, V) in cols.items():
                for r in regs:
                    v = bd.reg[r]["v"]
                    R, t = da.kabsch(bd.V0[v], V[v])
                    h = hist.setdefault((col, r), [])
                    h.append((V[v] - t) @ R)
                    if len(h) == 3:
                        x = np.linalg.norm(h[2] - 2 * h[1] + h[0], axis=1) * 1000
                        e = best.setdefault((col, r), [0.0, 0.0, -1])
                        if x.max() > e[1]:
                            e[2] = f - 1
                        e[0], e[1] = max(e[0], float(np.percentile(x, 99))), max(e[1], float(x.max()))
                        h.pop(0)
        res[c] = {f"{col}.{r}": [round(e[0], 2), round(e[1], 2), e[2]] for (col, r), e in best.items()}
        print(f"{c}: pop99 / popmax mm @frame, " + " | ".join(sorted({k[0] for k in best})))
        for r in regs:
            print(f"  {r:20s}" + " | ".join("{:.2f} / {:.2f} @{}".format(*best[col, r]) for col in sorted({k[0] for k in best})), flush=True)
    (OUT / f"pops_{a.provider}.json").write_text(json.dumps(res))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["shift", "pops"])
    ap.add_argument("--provider", default="pub")
    ap.add_argument("--poses", default="")
    ap.add_argument("--only", default="train,held,extreme")
    ap.add_argument("--clip", default="")
    ap.add_argument("--clips", default="run_warden,sword_heavy,p4:bladestorm_loop")
    a = ap.parse_args()
    {"shift": cmd_shift, "pops": cmd_pops}[a.cmd](Ctx(), a)


if __name__ == "__main__":
    main()
