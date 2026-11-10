"""region_target: stage T of the shoulder region rebuild: the pose set and the offline TARGET surface (WIP, lead 14).

    python tools/body/region_target.py region | poses | target | gate [--base rule_main|rule|pub] [--only train,held,extreme]

Out (git-ignored, tools/body/out/shoulder): poses.npz, region.npz, target.npz, gate.json, base_rule.npz (cache).
  `region` writes region.npz alone and prints the region's size, its depth around each armpit apex and what bounds it.
Region (topology points, left; the right is its twin by mirror_of, same order): core = left points of the neck, trunk,
  shoulder and arm parts whose girdle weight (clavicle, scap, upper arm chain, share, delt, trap, pec, lat; published or
  base) is over CORE_W 0.02 and whose station along the upper arm is under T_ARM 0.50 (arm ring 11: the ball's 0.12 m
  ends at 0.475); grown RING 3 + BLEND 4 rows into the rigid trunk and arm (never the breast part, the midline or the
  head seam). The head seam is the mesh's OPEN BORDER (an edge of one quad). POLES true (the default) keeps the
  poles (points of 3 or 5 quads) in the region like any other point; false is the old test "four quads at a point",
  which caught the seam and also punched every pole out as a one-point hole with its own border rows: two 5-poles
  sit 30 mm from the armpit apex, so the fixed border ran through the armpit. depth = rows from outside; beta 0 on
  rows 1-3 (the fixed border ring = the published skinned surface), smoothstep over rows 4-7, 1 inside.
  Target = beta X + (1 - beta) published.
Method (own numpy; every number below is PARAMS):
  base   LBS of the rule weights with the A roles off (weights_topo.body on the build's weights body), the muscle
         helpers merged into their parents (MERGE: delt, trap, pec, lat, scap): the twist chain and the share stay
         (they are the arm's own kinematics). "pub" = the published weights, "rule" = unmerged.
  mush   delta mush: Taubin smoothing (lam 0.5, mu -0.53, DM_ITERS pairs: a low pass that does not shrink; plain
         Laplace smoothing flattens the cap) of the base over the region, its outer neighbours held at the base;
         each point's rest delta re-added in its local frame = the polar rotation of its smoothed one-ring + normal.
  contact arm class (base arm share >= 0.5) against torso class, both directions, point against triangle, pairs over
         REST_SEP 12 mm apart at rest (the audit's own rule), GAP 1 mm (the audit tests 0.3 mm off the skin); the
         overlap is split by beta (both sides give; a fixed side gives nothing), SKIRT rows drag the neighbours.
  guard  the closed cap's volume (region + a fan over each border loop) brought back inside +-VOL_DEAD of the rest's
         by a normal offset over the free points, then one more contact pass.
Poses: descriptor (left; the right mirrored) = upper arm direction and twist in spine_05's frame, clavicle, spine_05
  in spine_04, neck_01; distance (deg) = sqrt(swing^2 + (.5 twist)^2 + clav^2 + (.5 spine)^2 + (.25 neck)^2).
  A clip that keys no clavicle (unkeyed) is posed with the girdle LAW driving the clavicle (the rig without
  "clavicle_by", as the extremes are), which is what the game shows at runtime; a clip that keys one stays as keyed.
  poses.npz `law` marks the law-driven poses.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import scipy.sparse as sp
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation as Rot

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import deform_audit as da  # noqa: E402
import ray  # noqa: E402
from surfdist import closest_on_tris  # noqa: E402

ROUND, OUT = HERE / "out/round_36", HERE / "out/shoulder"
M4 = np.diag([-1.0, 1, 1, 1])
PARAMS = {"base": "rule_main", "core_w": 0.02, "t_arm": 0.50, "ring": 3, "blend": 4, "dm_iters": 8, "lam": 0.5,
          "mu": -0.53, "gap": 0.001, "reach": 0.04, "cap": 0.012, "rest_sep": 0.012, "contact_iters": 8, "skirt": 3, "fall": 0.6,
          "vol_dead": 0.025, "guard_arm": 0.0, "w_desc": [1, 0.5, 1, 0.5, 0.25], "n_train": 64, "n_held": 64,
          "poles": True,                        # the region keeps poles; only the open border is the seam (see Region)
          "unkeyed_deg": 0.1,                   # a track within this of the bone's rest all clip long counts as unkeyed
          "apex": [0.154, 1.418, -0.03]}        # report only: her left armpit apex at rest, m (the right is its mirror)
APEX_R = (0.03, 0.06)                           # the report's radii round the apex, m
CLAVICLES = {"clavicle": ("clavicle_l", "clavicle_r")}      # her names of the bones the girdle law drives when unkeyed
MERGE = {"delt_{s}": "upperarm_twist_01_{s}", "trap_{s}": "clavicle_{s}", "pec_{s}": "spine_05", "lat_{s}": "spine_04",
         "scap_{s}": "clavicle_{s}"}
GIRDLE = ["clavicle", "scap", "upperarm", "upperarm_twist_01", "upperarm_twist_02", "upperarm_twist_03",
          "upperarm_twist_04", "upperarm_share", "delt", "trap", "pec", "lat"]
EXTREMES = {"abd120": (120, 0, 0), "abd150": (150, 0, 0), "abd170": (170, 0, 0), "flex120": (120, 90, 0),
            "flex150": (150, 90, 0), "flex170": (170, 90, 0), "hadd40": (90, 130, 0), "ext40": (40, -90, 0),
            "add0": (0, 0, 0), "add0_int60": (0, 0, 60), "add0_ext60": (0, 0, -60), "abd90_int60": (90, 0, 60),
            "abd90_ext60": (90, 0, -60)}        # (elevation from down, azimuth from out toward front, twist) deg
unit = lambda v: v / max(np.linalg.norm(v), 1e-12)
unit_rows = lambda v: v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-15)
s01 = lambda x: np.clip(x, 0, 1) ** 2 * (3 - 2 * np.clip(x, 0, 1))


def rows(adj, seed):
    """Rows (edge steps) from the seed points, [n]: 0 on the seed; a point no row reaches keeps n."""
    d, cur, k = np.where(seed, 0, adj.shape[0]), seed.copy(), 0
    while True:
        k += 1
        nb = (adj @ cur > 0) & ~cur
        if not nb.any():
            return d
        d[nb], cur = k, cur | nb


def rule_weights():
    """The rule weights with the A roles off, dense [n, bones] (cached: the build's stages 1-3 + weights_topo.body)."""
    cache = OUT / "base_rule.npz"
    if cache.exists():
        return np.load(cache)["W"]
    import os
    import build_topo as bt
    spec = bt.with_defaults(bt.load_spec(str(HERE / "specs/her_b.json")))
    g = bt.ground_offset(spec)
    if g:
        spec["_ground_m"] = g
    A = bt.Glb(os.path.join(bt.REPO, spec["ref"]))
    baked = bt.headbake.bake(A, bt.HEADS)
    hm = np.asarray(bt.sliders_head_move(spec.get("sliders", {})), float) + np.asarray(g or [0.0, 0, 0], float)
    for h in baked:
        baked[h]["P"] = baked[h]["P"] + hm[None]
    rep = {"timings_s": {}}
    z, V = bt.stage_base(spec, "close", rep)
    V, ring, _ = bt.stage_place(spec, z, V, A, baked, rep)
    V = bt.stage_forms(spec, "close", z, V, ring, rep)
    err = float(np.abs(V - np.load(ROUND / "stage/close.npz")["V"]).max())
    assert err < 1e-5, f"the rebuilt body is not round_36's ({err})"
    sk = json.loads((ROUND / "stage/close_skeleton.json").read_text())
    sk["worlds"] = np.asarray(sk["worlds"], float)
    sk["ends"] = {k: tuple(np.asarray(x, float) for x in v) for k, v in sk["ends"].items()}
    rules = {k: v for k, v in (spec.get("weights") or {}).items() if not k.startswith("a_")}
    J, W, _ = bt.wtp.body(bt.weights_body(spec, "close", z, V, A, baked, rep), z, sk, rules)
    D = np.zeros((len(V), len(sk["names"])))
    np.put_along_axis(D, J, W, 1)
    OUT.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cache, W=D)
    return D


class Model:
    """Everything fixed: the topology, both sides' region, the base weights, the rest's smoothed surface and deltas."""

    def __init__(self, p, params=None):
        self.P = P = {**PARAMS, **(params or {})}
        self.p, self.I = p, p.index
        st = np.load(ROUND / "stage/close.npz")
        topo = np.load(HERE / "out/topo/close.npz", allow_pickle=True)
        self.src = src = st["src"]
        n = self.n = int(src.max()) + 1
        self.first = np.zeros(n, np.int64)
        self.first[src[::-1]] = np.arange(len(src))[::-1]
        self.Pb, self.V0 = p.Pb[self.first], p.P0[self.first]
        self.Rinv = np.linalg.inv(p.rest)
        nm = list(p.names)
        self.sw = np.array([self.I.get(x[:-1] + ("r" if x[-1] == "l" else "l"), i) if x[-2:] in ("_l", "_r") else i
                            for i, x in enumerate(nm)])
        Q = self.Q = topo["Q"]
        mo = topo["mirror_of"]
        self.tw = tw = np.arange(n)
        r = np.nonzero(mo >= 0)[0]
        tw[r], tw[mo[r]] = mo[r], r
        e, ec = np.unique(np.sort(np.concatenate([Q[:, [0, 1]], Q[:, [1, 2]], Q[:, [2, 3]], Q[:, [3, 0]]]), 1), axis=0,
                          return_counts=True)
        self.adj = sp.coo_matrix((np.ones(2 * len(e)), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), (n, n)).tocsr()
        self.T = np.concatenate([Q[:, [0, 1, 2]], Q[:, [0, 2, 3]]])
        Wp = np.zeros((n, len(nm)))
        np.put_along_axis(Wp, st["J"], st["W"], 1)
        if P["base"] == "pub":
            Wb = Wp
        else:
            Wb = rule_weights().copy()
            if P["base"] == "rule_main":
                for a, b in MERGE.items():
                    for s in "lr":
                        ia, ib = self.I[a.replace("{s}", s)], self.I[b.replace("{s}", s)]
                        Wb[:, ib] += Wb[:, ia]
                        Wb[:, ia] = 0
        self.Wb = Wb
        parts = list(topo["parts"])
        part, side = topo["part"], topo["side"]
        H, E = p.rest[self.I["upperarm_l"]][:3, 3], p.rest[self.I["lowerarm_l"]][:3, 3]
        t = (self.V0 - H) @ unit(E - H) / np.linalg.norm(E - H)
        gi = [self.I[f"{b}_l"] for b in GIRDLE]
        cnt = np.bincount(Q.ravel(), minlength=n)
        seam = np.zeros(n, bool)
        seam[e[ec == 1].ravel()] = True                             # the open border (the head seam)
        own = np.isin(part, [parts.index(x) for x in ("neck", "trunk", "shoulder", "arm")])
        ok = (side == 1) & own & (~seam if P["poles"] else cnt == 4)
        reg = ok & (np.maximum(Wp[:, gi].sum(1), Wb[:, gi].sum(1)) > P["core_w"]) & (t < P["t_arm"])
        for _ in range(P["ring"] + P["blend"]):
            reg = ok & (reg | (self.adj @ reg > 0))
        ids = np.nonzero(reg)[0]
        self.depth = rows(self.adj, ~reg)[ids]
        # what each outside point is (the report's "bounded by"): -1 inside the region
        self.why_names = ["midline", "breast part", "other part", "open seam", "pole", "rigid trunk / arm"]
        self.why = np.where(reg, -1, np.select([side != 1, part == parts.index("breast"), ~own, seam, ~ok], [0, 1, 2, 3, 4], 5))
        self.part, self.parts = part, [str(x) for x in parts]
        self.beta = s01((self.depth - P["ring"]) / P["blend"])
        ai = [k for b in ("upperarm_l", "delt_l") for k in p.subtree(self.I[b])]
        arm_l = Wb[:, ai].sum(1) + 0.5 * Wb[:, self.I["upperarm_share_l"]]
        self.t_l, self.rad_l = t[ids], np.linalg.norm(self.V0[ids] - H, axis=1)
        self.rings = {k: np.nonzero((side == 1) & (part == parts.index("arm")) & (topo["ring"] == r_))[0]
                      for k, r_ in (("mid_deltoid", 2), ("insertion", 10))}
        self.S = {}
        for s in "lr":
            m = (lambda x: x) if s == "l" else (lambda x: tw[x])
            sid = m(ids)
            inr = np.zeros(n, bool)
            inr[sid] = True
            ext = np.r_[sid, np.nonzero((self.adj @ inr > 0) & ~inr)[0]]
            loc = -np.ones(n, np.int64)
            loc[ext] = np.arange(len(ext))
            Aloc = self.adj[sid][:, ext].tocsr()
            N = sp.diags(1.0 / np.asarray(Aloc.sum(1)).ravel()) @ Aloc
            ei, ej = Aloc.nonzero()
            tr = self.T[(loc[self.T] >= 0).all(1)]                  # the topology's own winding (outward) on both sides
            q = m(Q[reg[Q].all(1)]) if s == "l" else m(Q[reg[Q].all(1)])[:, ::-1]
            # the cap: the region's quads + a fan over each border loop (edges of one region quad)
            de = np.concatenate([q[:, [0, 1]], q[:, [1, 2]], q[:, [2, 3]], q[:, [3, 0]]])
            key = np.sort(de, 1) @ np.array([n, 1])
            _, inv, c = np.unique(key, return_inverse=True, return_counts=True)
            be = de[c[inv] == 1]
            _, lab = sp.csgraph.connected_components(sp.coo_matrix((np.ones(len(be)), (be[:, 0], be[:, 1])), (n, n)), False)
            armc = (arm_l if s == "l" else arm_l[tw]) >= 0.5
            near = np.linalg.norm(self.V0 - (H if s == "l" else H * [-1, 1, 1]), axis=1) < 0.35
            T = self.T
            sd = {"ids": sid, "ext": ext, "loc": loc, "N": N, "ei": ei, "ej": ej, "tr": loc[tr], "quads": q,
                  "be": be, "lab": lab[be[:, 0]], "armv": armc[sid], "arm": np.clip(arm_l[ids], 0, 1),
                  "vcls": armc.astype(int), "tcls": np.where(~near[T].all(1), -1, np.where(armc[T].all(1), 1, np.where((~armc[T]).all(1), 0, -1))),
                  "rings": {k: m(v) for k, v in self.rings.items()}}
            self.S[s] = sd
            x0 = self._lbs(sd, p.rest)
            sd["s0"] = s0 = self._smooth(sd, x0)
            sd["d"] = self.V0[sid] - s0[:len(sid)]
            sd["e0"] = s0[ej] - s0[ei]
            sd["n0"] = self._normals(s0, sd["tr"])[:len(sid)]
            sd["wn"] = np.bincount(ei, (sd["e0"] ** 2).sum(1), len(sid)) / np.bincount(ei, minlength=len(sid))
            sd["vol0"] = self.volume(sd, self.V0)
            N0 = np.zeros((n, 3))
            N0[ext] = self._normals(self.V0[ext], sd["tr"])
            sd["free"] = ~np.any([self._inside(self.V0, sid, N0, np.eye(3), k * P["gap"]) for k in (0.3, 1, 2)], 0)
        self.betaN = np.zeros(n)


    def blend(self, G, side):
        """The share of the target against the published surface per region point for the pose G of `side`, [points]:
        today the rest-built beta whatever the pose; rows whose share follows the pose (the breast part's upper and
        lateral rows, by the arm's elevation) answer here."""
        return self.beta

    def _lbs(self, sd, G):
        S = (G @ self.p.skel.ibm)[:, :3]
        W, Ph = self.Wb[sd["ext"]], np.c_[self.Pb[sd["ext"]], np.ones(len(sd["ext"]))]
        out = np.zeros((len(Ph), 3))
        for j in np.nonzero(W.max(0) > 0)[0]:
            out += W[:, j:j + 1] * (Ph @ S[j].T)
        return out

    def _smooth(self, sd, X):
        X, nr = X.copy(), len(sd["ids"])
        for _ in range(self.P["dm_iters"]):
            for lam in (self.P["lam"], self.P["mu"]):
                if lam:
                    X[:nr] += lam * (sd["N"] @ X - X[:nr])
        return X

    @staticmethod
    def _normals(X, tr):
        fn = np.cross(X[tr[:, 1]] - X[tr[:, 0]], X[tr[:, 2]] - X[tr[:, 0]])
        N = np.stack([sum(np.bincount(tr[:, k], fn[:, a], len(X)) for k in range(3)) for a in range(3)], 1)
        return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)

    def volume(self, sd, Vt):
        """The closed cap's volume on whole-topology positions Vt."""
        q, be = sd["quads"], sd["be"]
        tri = np.concatenate([q[:, [0, 1, 2]], q[:, [0, 2, 3]]])
        v = np.einsum("ij,ij->i", Vt[tri[:, 0]], np.cross(Vt[tri[:, 1]], Vt[tri[:, 2]])).sum()
        for k in np.unique(sd["lab"]):
            b = be[sd["lab"] == k]
            c = Vt[np.unique(b)].mean(0)
            v += np.einsum("ij,ij->i", Vt[b[:, 1]], np.cross(Vt[b[:, 0]], c[None])).sum()
        return float(v / 6)

    def girth(self, sd, Vt):
        out = {}
        for k, v in sd["rings"].items():
            A = self.adj[v][:, v].tocoo()
            out[k] = float(np.linalg.norm(Vt[v[A.row]] - Vt[v[A.col]], axis=1).sum() / 2)
        return out

    def mirror_G(self, G):
        return M4 @ G[self.sw] @ self.Rinv[self.sw] @ M4 @ self.p.rest

    def _inside(self, Y, pv, Nv, Rb, off):
        """Which of the points pv, lifted `off` along their normals, are inside the surface Y (the audit's 3-ray parity,
        the rays turned with the chest so a rigid turn changes nothing)."""
        return ray.inside(ray.scene(Y, self.T), Y[pv] + off * Nv[pv], dirs=da.DIRS @ Rb.T)

    def _contact(self, sd, Y, beta, iters, Rb, Y0=None):
        """Arm against torso: a free point is in contact when it is INSIDE the posed surface by parity, 0.3 mm off its
        skin (the audit's test: two sheets under one another are also what a thin fold's two walls are, so nothing
        local can tell) and was not at rest. It backs out along its own normal: the ray down its normal meets the
        other class's skin (far at rest) t under it, and the two give t + GAP between them by their betas (a fixed
        side gives nothing); no point leaves its place before contact (Y0) by over CAP (a deep cross-body press is
        eased, not undone)."""
        P, ids, n = self.P, sd["ids"], self.n
        bN = np.zeros(n)
        bN[ids] = beta
        free, tc, vc = ids[sd["free"]], sd["tcls"], sd["vcls"]
        hit = np.zeros(len(ids), bool)
        Y0 = Y[ids].copy() if Y0 is None else Y0
        for _ in range(iters):
            Nv = np.zeros((n, 3))
            Nv[sd["ext"]] = self._normals(Y[sd["ext"]], sd["tr"])
            scn = ray.scene(Y, self.T)
            pv = free[ray.inside(scn, Y[free] + 3e-4 * Nv[free], dirs=da.DIRS @ Rb.T)]
            if not len(pv):
                break
            pr, t = ray.hits(scn, Y[pv] - 1e-4 * Nv[pv], -Nv[pv])
            ok = (pr >= 0) & (t < P["reach"])
            pr = np.where(ok, pr, 0)
            tri = self.T[pr]
            mp, mf = bN[pv], bN[tri].mean(1)
            ok &= (tc[pr] == 1 - vc[pv]) & (np.linalg.norm(self.V0[tri].mean(1) - self.V0[pv], axis=1) > P["rest_sep"]) & (mp + mf > 1e-9)
            if not ok.any():
                break
            pv, tri, mp, mf = pv[ok], tri[ok], mp[ok], mf[ok]
            amt = np.minimum(t[ok] + P["gap"], P["cap"])
            fp = mp / (mp + mf)
            disp, ws = np.zeros((n, 3)), np.zeros(n)
            np.add.at(disp, pv, -(fp * amt)[:, None] * Nv[pv])
            np.add.at(ws, pv, 1.0)
            for k in range(3):
                np.add.at(disp, tri[:, k], ((1 - fp) * amt)[:, None] * Nv[pv])
                np.add.at(ws, tri[:, k], 1.0)
            got = ws[ids] > 1e-9
            hit |= got
            u = np.zeros((len(ids), 3))
            u[got] = disp[ids][got] / ws[ids][got, None]
            A = sd["N"][:, :len(ids)] > 0
            for _ in range(P["skirt"]):
                cn = np.asarray(A @ got.astype(float)).ravel()
                new = ~got & (cn > 0)
                u[new] = P["fall"] * (A @ u)[new] / cn[new, None] * beta[new, None]
                got = got | new
            d = Y[ids] + u * (bN[ids] > 0)[:, None] - Y0
            Y[ids] = Y0 + d * np.minimum(1, P["cap"] / np.maximum(np.linalg.norm(d, axis=1), 1e-12))[:, None]
        return Y, hit

    def target(self, G, Vp, side="l", info=None):
        """The target positions of the side's region points [nr, 3]: G the posed globals (helpers driven), Vp the
        published skinned surface on the topology's points [n, 3]."""
        sd, P = self.S[side], self.P
        ids, nr, beta = sd["ids"], len(sd["ids"]), self.beta
        s = self._smooth(sd, self._lbs(sd, G))
        C = np.zeros((nr, 3, 3))
        np.add.at(C, sd["ei"], (s[sd["ej"]] - s[sd["ei"]])[:, :, None] * sd["e0"][:, None, :])
        C += sd["wn"][:, None, None] * self._normals(s, sd["tr"])[:nr, :, None] * sd["n0"][:, None, :]
        U, _, Vt = np.linalg.svd(C)
        U[:, :, 2] *= np.sign(np.linalg.det(U @ Vt))[:, None]
        X = s[:nr] + np.einsum("nij,nj->ni", U @ Vt, sd["d"])
        Y = Vp.copy()
        Y[ids] = beta[:, None] * X + (1 - beta[:, None]) * Vp[ids]
        v_dm, g_dm = self.volume(sd, Y) / sd["vol0"], self.girth(sd, Y)
        Yc = Y[ids].copy()
        Rb = da.ortho(G[self.I["spine_05"]][:3, :3] @ self.Rinv[self.I["spine_05"]][:3, :3])
        Y, hit = self._contact(sd, Y, beta, P["contact_iters"], Rb)
        for _ in range(2):
            r = self.volume(sd, Y) / sd["vol0"]
            want = np.clip(r, 1 - P["vol_dead"], 1 + P["vol_dead"])
            if want == r:
                break
            Nv = self._normals(Y[sd["ext"]], sd["tr"])[:nr]
            fn = np.cross(Y[sd["quads"][:, 1]] - Y[sd["quads"][:, 0]], Y[sd["quads"][:, 3]] - Y[sd["quads"][:, 0]])
            area = np.bincount(sd["loc"][sd["quads"]].ravel(), np.repeat(np.linalg.norm(fn, axis=1) / 4, 4), len(sd["ext"]))[:nr]
            phi = beta * ~hit * (1 - (1 - P["guard_arm"]) * sd["arm"])
            Y[ids] += ((want - r) * sd["vol0"] / max(float((phi * area).sum()), 1e-12)) * phi[:, None] * Nv
        Y, hit2 = self._contact(sd, Y, beta, 3, Rb, Yc)
        if info is not None:
            g0, g1 = self.girth(sd, self.V0), self.girth(sd, Y)
            info.update(vol_dm=round(v_dm, 4), **{f"girth_dm_{k}": round(g_dm[k] / g0[k], 4) for k in g0}, vol=round(self.volume(sd, Y) / sd["vol0"], 4), contact=int((hit | hit2).sum()),
                        **{f"girth_{k}": round(g1[k] / g0[k], 4) for k in g0})
        return Y[ids]


# ------------------------------------------------------------------- poses --
def arc(a, b):
    ax, c = np.cross(a, b), float(a @ b)
    s = np.linalg.norm(ax)
    if s < 1e-9:
        return np.eye(3) if c > 0 else Rot.from_rotvec(np.pi * unit(np.cross(a, [1.0, 0, 0]))).as_matrix()
    return Rot.from_rotvec(ax / s * np.arctan2(s, c)).as_matrix()


def describe(md, G):
    """The left shoulder's state of globals G: swing [3], twist deg, clavicle / spine / neck quaternions."""
    I, R0 = md.I, md.p.rest
    turn = lambda b: da.ortho(G[I[b]][:3, :3] @ np.linalg.inv(R0[I[b]][:3, :3]))
    Rt = turn("spine_05")
    d = Rt.T @ unit(G[I["lowerarm_l"]][:3, 3] - G[I["upperarm_l"]][:3, 3])
    d0 = unit(R0[I["lowerarm_l"]][:3, 3] - R0[I["upperarm_l"]][:3, 3])
    tw = np.degrees(Rot.from_matrix(arc(d0, d).T @ Rt.T @ turn("upperarm_l")).as_rotvec() @ d0)
    q = lambda M: Rot.from_matrix(M).as_quat()
    return np.r_[d, tw, q(Rt.T @ turn("clavicle_l")), q(turn("spine_04").T @ Rt), q(Rt.T @ turn("neck_01"))]


def desc_dist(A, B, w=PARAMS["w_desc"]):
    """[na, nb] deg between descriptor rows."""
    ang = lambda X, Y, f=1.0: np.degrees(f * np.arccos(np.clip(X @ Y.T, -1, 1)))
    qa = lambda a: ang(A[:, a:a + 4], B[:, a:a + 4]) * 0 + np.degrees(2 * np.arccos(np.clip(np.abs(A[:, a:a + 4] @ B[:, a:a + 4].T), 0, 1)))
    tw = np.abs((A[:, 3:4] - B[:, 3][None] + 180) % 360 - 180)
    return np.sqrt(ang(A[:, :3], B[:, :3]) ** 2 + (w[1] * tw) ** 2 + (w[2] * qa(4)) ** 2 + (w[3] * qa(8)) ** 2 + (w[4] * qa(12)) ** 2)


def extreme_G(bd, name):
    """A named extreme on the left arm: the upper arm turned from rest, clavicle and scapula by the girdle law."""
    p = bd.p
    el, az, tw = np.radians(EXTREMES[name])
    d = np.array([np.sin(el) * np.cos(az), -np.cos(el), np.sin(el) * np.sin(az)])
    j, k = p.index["upperarm_l"], p.index["lowerarm_l"]
    R = Rot.from_rotvec(d * tw).as_matrix() @ arc(unit(p.rest[k][:3, 3] - p.rest[j][:3, 3]), d)
    G = p.rest.copy()
    D = np.eye(4)
    D[:3, :3], D[:3, 3] = R, G[j][:3, 3] - R @ G[j][:3, 3]
    for c in p.subtree(j):
        G[c] = D @ G[c]
    return bd.rd.drive(p, G, law_rig(bd))[0], R


def clip_names():
    return sorted(q.stem for q in da.DUMP.glob("*.json")) + da.p4_clips()


law_rig = da.law_rig


def clav_deg(D):
    """The clavicle's turn from rest in spine_05's frame, deg, of descriptor rows."""
    return np.degrees(2 * np.arccos(np.clip(np.abs(D[:, 7]), 0, 1)))


def cmd_poses(bd, md):
    names, sides, Gs, D, law = [], [], [], [], {}
    rig = bd.rig
    for c in clip_names():
        d = da.load_clip(c)
        law[c] = da.unkeyed(d, CLAVICLES["clavicle"], bd.p, bd.rl, PARAMS["unkeyed_deg"])
        try:
            if law[c]:
                bd.rig = law_rig(bd)
            for f, _, G in bd.clip_frames(d, 1):
                for s in "lr":
                    names.append((c, f))
                    sides.append(s)
                    D.append(describe(md, G if s == "l" else md.mirror_G(G)))
                Gs.append(G)
        finally:
            bd.rig = rig
    D = np.array(D)
    nt, nh = md.P["n_train"], md.P["n_held"]
    pick = [int(np.argmin(desc_dist(D, describe(md, bd.p.rest)[None])[:, 0]))]
    dmin = desc_dist(D, D[pick])[:, 0]
    while len(pick) < nt + nh:
        if len(pick) == nt:
            cover = dmin.copy()                                     # every frame's distance to the train set
        pick.append(int(np.argmax(dmin)))
        dmin = np.minimum(dmin, desc_dist(D, D[pick[-1:]])[:, 0])
    ex = {k: extreme_G(bd, k)[0] for k in EXTREMES}
    name = [f"{names[i][0]}@{names[i][1]}:{sides[i]}" for i in pick] + [f"x:{k}:l" for k in ex]
    kind = ["train"] * nt + ["held"] * nh + ["extreme"] * len(ex)
    G = np.array([Gs[i // 2] for i in pick] + list(ex.values()))
    Dx = np.array([describe(md, g) for g in ex.values()])
    cl = np.array([x[0] for x in names])
    worst = {c: round(float(cover[cl == c].max()), 1) for c in np.unique(cl)}
    OUT.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(OUT / "poses.npz", name=name, kind=kind, side=[x.split(":")[-1] for x in name], G=G,
                        desc=np.r_[D[pick], Dx], bones=list(bd.p.names), cover_all=cover, clip_worst=json.dumps(worst),
                        law=np.array([law[names[i][0]] for i in pick] + [True] * len(ex)))
    print("clavicle unkeyed, posed by the girdle law:", [c for c in law if law[c]])
    print("clavicle keyed, posed as keyed:", [c for c in law if not law[c]])
    p4, pk = np.char.startswith(cl, "p4:"), np.array(pick)
    q = lambda v: "p50/p95/max " + "/".join(f"{x:.1f}" for x in (np.median(v), np.percentile(v, 95), v.max())) if len(v) else "none"
    for k, m in (("p4", p4), ("dump", ~p4)):
        sel = pk[m[pk]]
        print(f"clavicle turn deg from rest, {k}: picked poses ({len(sel)}, law-driven {sum(law[names[i][0]] for i in sel)}) "
              f"{q(clav_deg(D[sel]))}; all candidates ({int(m.sum())}) {q(clav_deg(D[m]))}")
    print(f"poses: {len(D)} candidates (frames x sides), train {nt}, held {nh}, extremes {len(ex)}")
    print(f"coverage deg to nearest train: held p50/max {np.median(cover[pick[nt:]]):.1f}/{cover[pick[nt:]].max():.1f}; "
          f"all frames p50/p95/max {np.median(cover):.1f}/{np.percentile(cover, 95):.1f}/{cover.max():.1f}; "
          f"extremes {dict(zip(ex, np.round(desc_dist(Dx, D[pick[:nt]]).min(1), 0)))}")
    print("clip worst frame:", worst)


def published(bd, G):
    return bd.p._skin(G, bd.rd.corrective_weights(bd.p, G, bd.rig))


def full_target(bd, md, G, side, info=None):
    """(V target, V published) on the body's own vertices for one pose and side."""
    Vp = published(bd, G)
    X = md.target(G, Vp[md.first], side, info)
    sd = md.S[side]
    g = np.nonzero(sd["loc"][md.src] >= 0)[0]
    g = g[sd["loc"][md.src[g]] < len(sd["ids"])]
    V = Vp.copy()
    V[g] = X[sd["loc"][md.src[g]]]
    return V, Vp


def cmd_target(bd, md):
    z = np.load(OUT / "poses.npz")
    X, infos = [], []
    for G, s in zip(z["G"], z["side"]):
        i = {}
        Vp = published(bd, G)[md.first]
        X.append(md.target(G, Vp, str(s), i))
        infos.append(i)
    np.savez_compressed(OUT / "target.npz", X=np.array(X), name=z["name"], side=z["side"], kind=z["kind"],
                        info=json.dumps(infos), params=json.dumps(md.P))
    save_region(md)
    for k in ("vol_dm", "vol", "girth_mid_deltoid", "girth_insertion", "contact"):
        v = np.array([i[k] for i in infos])
        print(f"{k}: min {v.min():.3f} median {np.median(v):.3f} max {v.max():.3f}")
    print("region points", len(md.S["l"]["ids"]), "pure (beta 1)", int((md.beta == 1).sum()), "ring", int((md.beta == 0).sum()))


def save_region(md):
    OUT.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(OUT / "region.npz", ids_l=md.S["l"]["ids"], ids_r=md.S["r"]["ids"], depth=md.depth, beta=md.beta,
                        src=md.src, first=md.first, params=json.dumps(md.P))


def cmd_region(bd, md):
    """Write region.npz alone and say how deep the region holds each armpit apex and what bounds it there."""
    save_region(md)
    ids, pure = md.S["l"]["ids"], md.P["ring"] + md.P["blend"] + 1
    print("region points a side", len(ids), "pure (beta 1)", int((md.beta == 1).sum()), "ring (beta 0)", int((md.beta == 0).sum()),
          "(poles kept)" if md.P["poles"] else "(poles punched out)")
    near = {k: rows(md.adj, md.why == i)[ids] for i, k in enumerate(md.why_names) if (md.why == i).any()}
    for s, sx in (("l", 1), ("r", -1)):
        d = np.linalg.norm(md.V0[md.S[s]["ids"]] - np.array(md.P["apex"]) * [sx, 1, 1], axis=1)
        for r in APEX_R:
            m = d < r
            lo = m & (md.depth < pure)
            by = {k: int((v[lo] == md.depth[lo]).sum()) for k, v in near.items() if (v[lo] == md.depth[lo]).any()}
            print(f"apex {s} within {r * 1000:.0f} mm: {int(m.sum())} points, depth min / median / max {md.depth[m].min()} / "
                  f"{np.median(md.depth[m]):.0f} / {md.depth[m].max()}; under row {pure}: {int(lo.sum())}" + (f", bounded by {by}" if by else ""))
        i = int(np.argmin(d))
        print(f"apex {s}: nearest point {int(md.S[s]['ids'][i])} at {d[i] * 1000:.1f} mm, depth {md.depth[i]}; rows from it to:",
              {k: int(v[i]) for k, v in near.items()})
    print("region points by part:", {md.parts[k]: int(c) for k, c in zip(*np.unique(md.part[ids], return_counts=True))})
    inr = np.zeros(md.n, bool)
    inr[ids] = True
    out = np.nonzero((md.adj @ inr > 0) & ~inr)[0]
    print("its outer neighbours:", {md.why_names[k]: int(c) for k, c in zip(*np.unique(md.why[out], return_counts=True))},
          "| by part:", {md.parts[k]: int(c) for k, c in zip(*np.unique(md.part[out], return_counts=True))})


GM = ["st99", "bad", "flip", "kink99", "ins_mm"]
TOL = {"st99": 1.0, "bad": 0.1, "flip": 0.05, "kink99": 1.0, "ins_mm": 0.5}


def a_frames(Ab, clip, frames):
    return {f: (V, G) for f, V, G in Ab.clip_frames(da.load_clip(clip), 1) if f in frames}


def cmd_gate(bd, md, only):
    """Gate T: the target against A.full and B.full on the audit's own shoulder metrics, every pose."""
    z = np.load(OUT / "poses.npz")
    Ab = da.body("A")
    mi = [da.MET.index(m) for m in GM]
    by = {}
    for i, nm in enumerate(z["name"]):
        if str(z["kind"][i]) in only:
            by.setdefault(str(nm).rsplit("@", 1)[0] if "@" in str(nm) else str(nm), []).append(i)
    rows = {}
    for key, idx in by.items():
        A = {}
        if key.startswith("x:"):
            R = extreme_G(bd, key.split(":")[1])[1]
            A[None] = Ab.pose_turns([("upperarm_l", R)])
        elif not key.startswith("p4:"):
            A = a_frames(Ab, key, {int(str(z["name"][i]).split("@")[1].split(":")[0]) for i in idx})
        for i in idx:
            s, G = str(z["side"][i]), z["G"][i]
            info = {}
            Vt, Vp = full_target(bd, md, G, s, info)
            f = None if key.startswith("x:") else int(str(z["name"][i]).split("@")[1].split(":")[0])
            row = {"kind": str(z["kind"][i]), **info}
            cols = {"T": (bd, Vt, G), "B": (bd, Vp, G)}
            if f in A:
                cols["A"] = (Ab,) + tuple(A[f])
            for col, (b, V, g) in cols.items():
                out = b.measure(V, g)[0]
                row[col] = {r: [out[r.replace("{s}", s)][k] for k in mi] for r in da.JOINTS["shoulder"]}
            rows[str(z["name"][i])] = row
            print(str(z["name"][i]), {c: row[c]["shoulder_{s}"] for c in "TBA" if c in row}, flush=True)
    (OUT / "gate.json").write_text(json.dumps(rows))
    report(rows)


def report(rows):
    fails = []
    print("GATE T  region metric: worst T/A/B | median T/A/B")
    for r in da.JOINTS["shoulder"]:
        for k, m in enumerate(GM):
            v = {c: np.array([row[c][r][k] for row in rows.values() if "A" in row]) for c in "TAB"}
            vb = {c: np.array([row[c][r][k] for row in rows.values()]) for c in "TB"}
            print(f"  {r:22s}{m:7s} " + "/".join(f"{v[c].max():.1f}" for c in "TAB") + " | " + "/".join(f"{np.median(v[c]):.1f}" for c in "TAB")
                  + f"   (all poses T/B worst {vb['T'].max():.1f}/{vb['B'].max():.1f})")
            for nm, row in rows.items():
                t = row["T"][r][k]
                if t > row["B"][r][k] + TOL[m] or ("A" in row and t > row["A"][r][k] + TOL[m]):
                    fails.append((nm, r, m, t, row.get("A", {}).get(r, [None] * 5)[k], row["B"][r][k]))
    bad = sorted({f[0] for f in fails})
    print(f"poses {len(rows)} (with A {sum('A' in r for r in rows.values())}); failing any line: {len(bad)}; lines failed {len(fails)}")
    by = {}
    for f in fails:
        by.setdefault((f[1], f[2]), []).append(f)
    for k, v in by.items():
        w = max(v, key=lambda f: f[3] - min(x for x in (f[4], f[5]) if x is not None))
        print(f"  FAIL {k[0]} {k[1]}: {len(v)} poses; worst {w[0]} T {w[3]} A {w[4]} B {w[5]}")
    for k in ("vol_dm", "vol", "girth_mid_deltoid", "girth_insertion"):
        v = np.array([row[k] for row in rows.values()])
        print(f"  {k}: min {v.min():.3f} median {np.median(v):.3f} max {v.max():.3f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["region", "poses", "target", "gate", "report"])
    ap.add_argument("--base", default=PARAMS["base"])
    ap.add_argument("--only", default="train,held,extreme")
    ap.add_argument("--set", default="{}", help="JSON overrides of PARAMS")
    a = ap.parse_args()
    if a.cmd == "report":
        return report(json.loads((OUT / "gate.json").read_text()))
    bd = da.body("B")
    bd.set_layer("full")
    md = Model(bd.p, {"base": a.base, **json.loads(a.set)})
    {"region": cmd_region, "poses": cmd_poses, "target": cmd_target}.get(a.cmd, lambda b, m: cmd_gate(b, m, a.only.split(",")))(bd, md)


if __name__ == "__main__":
    main()
