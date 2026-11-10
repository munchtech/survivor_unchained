"""deform_audit: her body's deformation by number, every major joint, body B (body_p1) against body A (heroine.glb),
through the clips and through pure range-of-motion sweeps, with B's layers switched off one at a time.

    python tools/body/deform_audit.py [--only clips,p4,rom,md,sheets] [--procs 5] [--step 1] [--out tools/body/out/audit]
    (--step N samples every Nth frame of the 33 dumps; A1's p4 clips are always read at every frame)

Bodies:  B = body_p1/body.glb + rig.json (lbs poser + rig_drive), layers full | nocorr (blend shapes off) |
         nolaws (girdle and hand_clear only: helpers ride their parents at rest local, no shapes);
         Bplay = play.glb + play_rig.json, full;  A = heroine.glb by the game poser (skin.py), full | nocorr.
Regions: triangles by REST centroid on each body's own mesh (welded by place) and skeleton: shoulder ball 0.12 m
         (.deltoid = above the joint or lateral, .axilla = below and medial), clav (the neck-base slope), elbow 0.08,
         forearm, wrist 0.06, hip 0.14 (.front/.glute/.groin), knee 0.10 (.front/.back), ankle 0.07, neck, trunk (.waist).
Metrics per region and posed frame, against the rest pose (the poser's own pose with no turns):
  st50/st99  |l/l0 - 1| over the region's edges, p50 / p99 % (st99 = P3's kneeloc/walk measure); ext99 p99 of the
             stretch alone, cp99 of the compression alone (%)
  bad/flip   % of triangles with area < 0.5x or > 2x rest; % whose posed normal is against the rest normal turned by
             the vertex-blended skin rotation (P3's per_tri)
  kink99/kinkmax  the dihedral angle's change over the region's inner edges, p99 / max deg
  ins_n/ins_mm    region points inside the posed surface (3-ray parity in the body's frame; points inside at rest
             dropped) deeper than 2 mm / the deepest, mm: exact distance to the posed triangles whose rest centroid is
             over 12 mm from the point's rest place (bends.true_depth's rule, among the 64 nearest)
  at_n/at_mm (axilla only) upper-arm points (first 40%) under the torso skin: count / depth mm (clipcheck's measure)
  slide50/95/max  the residual after the best rigid fit (Kabsch) of the region rest -> posed, mm: what a rigid plate sees
  sb50/95/max     (deltoid and clav = the trap slope only) slide_bone: each point against where the region's reference
             bone ALONE would carry it rigidly (deltoid: upperarm_share_{s}, else the upper arm; clav: clavicle_{s}), mm:
             what a rigid pauldron riding that bone sees (the Kabsch slide over the whole ball includes the bend itself)
  pop99/popmax    (clips) per point second difference across frames in the region's rigid-fit frame, mm / frame^2
  ROM only: girth and area ratio at bends' stations (elbow, knee, shoulder abd/flex, hip flex).
Out (git-ignored): audit.json, audit.md, sheet_<joint>.png (+ _half.jpg): B | A, clay and flagged (orange bad, red flipped).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bends  # noqa: E402
import ray  # noqa: E402
from bends import rot, unit  # noqa: E402
from posers import make_poser  # noqa: E402

REPO = HERE.parent.parent
P1 = REPO / "godot/art/people/body_p1"
DUMP = HERE / "out/clips"
P4 = REPO.parent / "motion-a1/godot/art/people/body_p1/p4"
OUT = HERE / "out/audit"
BODIES = {"B": (P1 / "body.glb", P1 / "rig.json", "lbs", ("full", "nocorr", "nolaws")),
          "Bplay": (P1 / "play.glb", P1 / "play_rig.json", "lbs", ("full",)),
          "A": (REPO / "godot/art/people/heroine.glb", None, "game", ("full", "nocorr"))}
COLS = ["B.full", "B.nocorr", "B.nolaws", "Bplay.full", "A.full", "A.nocorr"]
MET = ["st50", "st99", "ext99", "cp99", "bad", "flip", "kink99", "kinkmax", "ins_n", "ins_mm", "slide50", "slide95",
       "slidemax", "at_n", "at_mm", "sb50", "sb95", "sbmax"]
CLIPMET = MET + ["pop99", "popmax"]
JOINTS = {"shoulder": ["shoulder_{s}", "shoulder_{s}.deltoid", "shoulder_{s}.axilla", "clav_{s}"], "elbow": ["elbow_{s}"],
          "forearm": ["forearm_{s}"], "wrist": ["wrist_{s}"], "hip": ["hip_{s}", "hip_{s}.front", "hip_{s}.glute", "hip_{s}.groin"],
          "knee": ["knee_{s}", "knee_{s}.front", "knee_{s}.back"], "ankle": ["ankle_{s}"], "neck": ["neck"],
          "trunk": ["trunk", "trunk.waist", "trunk.core"]}
P4_TWIN = {"walk": "Jog_Fwd", "run": "run_warden", "idle": "idle_warden_town", "p4_proof_walk": "Jog_Fwd",
           "p4_proof_idle": "idle_warden_town"}
CAM = {"shoulder": (0.5, 0.2, 0.8), "elbow": (0.6, 0.0, -0.8), "forearm": (0.7, 0, 0.7), "wrist": (0.7, 0, 0.7),
       "hip": (0.4, 0.0, 0.9), "knee": (0.9, 0.0, 0.4), "ankle": (0.9, 0.1, 0.4), "neck": (0.5, 0.1, 0.85), "trunk": (0.3, 0, 0.95)}
DIRS = np.array([[0.5774, 0.5774, 0.5774], [-0.7071, 0.1, 0.7], [0.1, -0.9, -0.42]])
DIRS = DIRS / np.linalg.norm(DIRS, axis=1, keepdims=True)


def mats(a):
    a = np.asarray(a, float).reshape(-1, 3, 4)
    m = np.zeros((len(a), 4, 4))
    m[:, :3] = a
    m[:, 3, 3] = 1
    return m


def kabsch(P, Q):
    """R, t with Q ~ P @ R.T + t."""
    cp, cq = P.mean(0), Q.mean(0)
    U, _, Vt = np.linalg.svd((P - cp).T @ (Q - cq))
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1, 1, d]) @ U.T
    return R, cq - R @ cp


def ortho(R):
    U, _, Vt = np.linalg.svd(R)
    return U @ Vt


class Shim:
    """B's driver with a layer switched off (rig_drive stays the one implementation)."""

    def __init__(self, rd, layer):
        self.rd, self.layer = rd, layer

    def drive(self, p, G, rig):
        rd = self.rd
        if self.layer == "nolaws":
            G = G.copy()
            for fn, key in ((rd.girdle, "girdle"), (rd.hand_clear, "hand_clear")):
                if key in rig:
                    for s in "lr":
                        fn(p, G, rig, s)
            return G, {}
        G, _ = rd.drive_helpers(p, G, rig)
        return G, ({} if self.layer == "nocorr" else rd.corrective_weights(p, G, rig))


class Body:
    def __init__(self, key):
        glb, rigp, kind, self.layers = BODIES[key]
        self.key, self.kind = key, kind
        self.rig = json.loads(Path(rigp).read_text()) if rigp else {}
        self.p = p = make_poser(kind, str(glb), self.rig)
        if kind == "lbs":
            self.rd = p.driver
            self.J, self.W = p.J, p.W
            par, self.order, seen = p.parent, [], set()

            def visit(k):
                if k in seen:
                    return
                if par[k] >= 0:
                    visit(par[k])
                seen.add(k)
                self.order.append(k)
            for k in range(len(p.names)):
                visit(k)
            self.rl = [np.linalg.inv(p.rest[par[k]]) @ p.rest[k] if par[k] >= 0 else p.rest[k].copy() for k in range(len(par))]
            self.helpers = {h["name"].replace("{s}", s) for h in self.rig.get("helpers", []) for s in "lr"}
        else:
            self.J, self.W, self.corr = p.body.Jv, p.body.W, p.body.corr
        self.T, self.piece = p.T, p.piece
        self.layer = None
        self.set_layer("full")
        self.V0, self.G0 = self.pose_turns([])
        self.frame = bends.Frame(p, self.rig)
        self.L0i = np.linalg.inv(self._blend(self.G0))
        self._topology()
        self._regions()
        self.ins0 = np.zeros(len(self.V0), bool)
        self.at0 = {s: 0 for s in "lr"}
        self.ins0 = self._inside(self.V0, self.G0)[0] > -1
        self.at0 = {s: self._armtorso(self.V0, self._normals(self.V0), s)[2] for s in "lr"}

    # ------------------------------------------------------------------ posing --
    def set_layer(self, layer):
        self.layer = layer
        if self.kind == "lbs":
            self.p.driver = Shim(self.rd, layer)
        else:
            self.p.body.corr = self.corr if layer == "full" else {}

    def pose_turns(self, turns):
        V, G, _ = self.p.pose(turns)
        return V, G

    def _blend(self, G):
        if self.kind == "lbs":
            S = (G @ self.p.skel.ibm)[:, :3, :3]
        else:
            S = self.p.body.skin_mats(G)[:, :3, :3]
        L = np.zeros((len(self.J), 3, 3))
        for k in range(self.J.shape[1]):
            L += self.W[:, k, None, None] * S[self.J[:, k]]
        return L

    def clip_frames(self, d, step=1):
        """(frame, V, G) of a clip: a keys dump (tools/body/out/clips) or one of A1's p4 clips (B only)."""
        p = self.p
        if "bones" in d:                                            # p4: B local rotations (x, y, z, w) by bone
            n = d["frames"]
            for f in range(0, n, step):
                G = p.rest.copy()
                for k in self.order:
                    L = self.rl[k].copy()
                    nm = p.names[k]
                    if nm in d["rot"]:
                        L[:3, :3] = Rotation.from_quat(d["rot"][nm][f]).as_matrix()
                    if nm in d.get("pos", {}):
                        L[:3, 3] = d["pos"][nm][f]
                    G[k] = G[p.parent[k]] @ L if p.parent[k] >= 0 else L
                G, w = p.driver.drive(p, G, self.rig)
                yield f, p._skin(G, w), G
        elif self.kind == "lbs":                                    # the dump's B globals (clipcheck.Body.pose)
            names, keyed = d["b_names"], set(d["keyed"])
            Gb = mats(d["B"]).reshape(d["frames"], len(names), 4, 4)
            X = p.rest[p.index["pelvis"]] @ np.linalg.inv(mats(d["b_rest"])[names.index("pelvis")])
            mp = [p.index.get(n, -1) for n in names]
            for f in range(0, d["frames"], step):
                G = p.rest.copy()
                got = np.zeros(len(G), bool)
                for a, k in enumerate(mp):
                    if k >= 0:
                        G[k] = X @ Gb[f, a]
                        got[k] = True
                for k in self.order:
                    pk, n = p.parent[k], p.names[k]
                    if pk >= 0 and (not got[k] or n in self.helpers and n not in keyed):
                        G[k] = G[pk] @ self.rl[k]
                G, w = p.driver.drive(p, G, self.rig)
                yield f, p._skin(G, w), G
        else:                                                       # A: the dump's globals -> local turns -> the game poser
            import skin
            b = p.body
            sk = b.sk
            names = d["a_names"]
            Ga = mats(d["A"]).reshape(d["frames"], len(names), 4, 4)[:, :, :3, :3]
            Ga = Ga / np.linalg.norm(Ga, axis=2, keepdims=True)
            R0 = mats(d["a_rest"])[:, :3, :3]
            R0 = R0 / np.linalg.norm(R0, axis=1, keepdims=True)
            ia = {n: i for i, n in enumerate(names)}
            rotq = np.broadcast_to(sk.rest_rot, (d["frames"],) + sk.rest_rot.shape).copy()
            g0 = Rotation.from_quat(sk.rest_globals()[0][0]).as_matrix()
            for j, n in enumerate(sk.names):
                if n not in ia:
                    continue
                pj = sk.parent[j]
                if pj < 0:
                    R = (g0[j] @ R0[ia[n]].T) @ Ga[:, ia[n]]
                elif sk.names[pj] in ia:
                    R = np.swapaxes(Ga[:, ia[sk.names[pj]]], 1, 2) @ Ga[:, ia[n]]
                else:
                    continue
                rotq[:, j] = Rotation.from_matrix(R).as_quat()
            pos = np.broadcast_to(sk.rest_pos, (d["frames"],) + sk.rest_pos.shape).copy()
            clip = skin.Clip(d["name"], d["fps"], rotq, pos, False)
            st = {}
            for f in range(0, d["frames"], step):
                G = b.globals(clip, f, st, step / d["fps"])
                yield f, b.pose(G), G

    # ---------------------------------------------------------------- topology --
    def _topology(self):
        V0, T = self.V0, self.T
        _, inv = np.unique(np.round(V0, 5), axis=0, return_inverse=True)
        self.wid = inv = inv.reshape(-1)
        nw = inv.max() + 1
        self.rep = np.zeros(nw, np.int64)
        self.rep[inv[::-1]] = np.arange(len(V0))[::-1]
        self.Tw = Tw = inv[T]
        Vw = V0[self.rep]
        self.n0 = np.cross(V0[T[:, 1]] - V0[T[:, 0]], V0[T[:, 2]] - V0[T[:, 0]])
        self.a0 = np.linalg.norm(self.n0, axis=1)
        self.ok = (Tw[:, 0] != Tw[:, 1]) & (Tw[:, 1] != Tw[:, 2]) & (Tw[:, 0] != Tw[:, 2]) & (self.a0 > 1e-12)
        nt = len(Tw)
        e = np.sort(np.concatenate([Tw[:, [0, 1]], Tw[:, [1, 2]], Tw[:, [2, 0]]]), 1)
        key = e[:, 0] * nw + e[:, 1]
        key[np.tile(~self.ok, 3)] = -1 - np.arange(int((~self.ok).sum()) * 3)       # degenerate: edges of their own
        uq, einv, cnt = np.unique(key, return_inverse=True, return_counts=True)
        self.tri_e = einv.reshape(3, nt).T
        self.E = np.stack([np.abs(uq) // nw, np.abs(uq) % nw], 1)
        self.el0 = np.maximum(np.linalg.norm(Vw[self.E[:, 1]] - Vw[self.E[:, 0]], axis=1), 1e-9)
        order = np.argsort(einv, kind="stable")
        start = np.concatenate([[0], np.cumsum(cnt)[:-1]])
        two = np.nonzero((cnt == 2) & (uq >= 0))[0]
        self.ie = two
        self.it = np.stack([order[start[two]] % nt, order[start[two] + 1] % nt], 1)
        self.dih0 = self._dihedral(Vw, self.n0)

    def _dihedral(self, Vw, fn):
        fn = fn / np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-20)
        n1, n2 = fn[self.it[:, 0]], fn[self.it[:, 1]]
        e = Vw[self.E[self.ie, 1]] - Vw[self.E[self.ie, 0]]
        e = e / np.maximum(np.linalg.norm(e, axis=1, keepdims=True), 1e-20)
        return np.arctan2(np.einsum("ij,ij->i", np.cross(n1, n2), e), np.einsum("ij,ij->i", n1, n2))

    def _normals(self, V):
        fn = np.cross(V[self.T[:, 1]] - V[self.T[:, 0]], V[self.T[:, 2]] - V[self.T[:, 0]])
        nw = self.wid.max() + 1
        N = np.stack([sum(np.bincount(self.Tw[:, k], fn[:, a], nw) for k in range(3)) for a in range(3)], 1)[self.wid]
        return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)

    def head(self, n):
        return self.G0[self.p.index[n]][:3, 3]

    def role(self, r, s):
        return bends.bone(self.p, self.rig, r, s)

    def chain(self, prefix):
        nm = sorted(n for n in self.p.names if n.startswith(prefix) and n[len(prefix):].isdigit())
        return nm

    def head_bone(self):
        return "Head" if "Head" in self.p.index else "head"

    def _regions(self):
        p, V0, T = self.p, self.V0, self.T
        c = V0[T].mean(1)
        body = (self.piece[T[:, 0]] == "body") & self.ok
        fr = self.frame
        up, lat, front = fr.up, fr.lat, fr.front
        M = {}
        nk = self.chain("neck_") + [self.head_bone()]
        Hn, Hd = self.head(nk[0]), self.head(nk[-1])
        sub = lambda n: p.D[:, p.subtree(p.index[n])].sum(1)
        self.armv, self.torso = {}, None
        armw = np.zeros(len(V0))
        for s, sg in (("l", 1), ("r", -1)):
            o = lat * sg
            ua, la, hd, th, cf, ft = (self.role(r, s) for r in ("upperarm", "lowerarm", "hand", "thigh", "calf", "foot"))
            H = self.head(ua)
            r = c - H
            ball = body & (np.linalg.norm(r, axis=1) < 0.12)
            ax = (r @ up < 0) & (r @ o < 0)
            M[f"shoulder_{s}"], M[f"shoulder_{s}.deltoid"], M[f"shoulder_{s}.axilla"] = ball, ball & ~ax, ball & ax
            x = (c - Hn) @ o
            M[f"clav_{s}"] = body & ~ball & (x > 0.02) & (x < (H - Hn) @ o) & (r @ up > -0.03) & ((c - Hd) @ up < 0)
            He, Hw = self.head(la), self.head(hd)
            M[f"elbow_{s}"] = body & (np.linalg.norm(c - He, axis=1) < 0.08)
            a, Lf = unit(Hw - He), np.linalg.norm(Hw - He)
            t = (c - He) @ a
            dist = np.linalg.norm((c - He) - t[:, None] * a, axis=1)
            M[f"forearm_{s}"] = body & (t > 0.12 * Lf) & (t < 0.88 * Lf) & (dist < 0.07)
            M[f"wrist_{s}"] = body & (np.linalg.norm(c - Hw, axis=1) < 0.06)
            Hh = self.head(th)
            r = c - Hh
            ball = body & (np.linalg.norm(r, axis=1) < 0.14) & ((c - fr.center) @ o > 0)
            groin = (r @ o < -0.03) & (r @ up < 0)
            fm = (r @ front > 0) & ~groin
            M[f"hip_{s}"], M[f"hip_{s}.front"], M[f"hip_{s}.glute"], M[f"hip_{s}.groin"] = ball, ball & fm, ball & ~fm & ~groin, ball & groin
            r = c - self.head(cf)
            ball = body & (np.linalg.norm(r, axis=1) < 0.10)
            M[f"knee_{s}"], M[f"knee_{s}.front"], M[f"knee_{s}.back"] = ball, ball & (r @ front > 0), ball & (r @ front <= 0)
            M[f"ankle_{s}"] = body & (np.linalg.norm(c - self.head(ft), axis=1) < 0.07)
            w = sub(ua)
            armw += w
            u, Lu = unit(He - H), np.linalg.norm(He - H)
            self.armv[s] = np.nonzero((self.piece == "body") & (w >= 0.5) & ((V0 - H) @ u < 0.4 * Lu))[0]
        a, Ln = unit(Hd - Hn), np.linalg.norm(Hd - Hn)
        t = (c - Hn) @ a
        dist = np.linalg.norm((c - Hn) - t[:, None] * a, axis=1)
        M["neck"] = self.ok & (t > -0.01) & (t < Ln + 0.03) & (dist < 0.09)
        Hp, Ht = self.head("pelvis"), self.head(self.chain("spine_")[-1])
        h, hh = (c - Hp) @ up, (Ht - Hp) @ up
        M["trunk"] = body & (h > 0) & (h < hh) & (armw[T].mean(1) < 0.5) & (np.abs((c - Hp) @ lat) < 0.22)
        M["trunk.waist"] = M["trunk"] & (np.abs(h - 0.45 * hh) < 0.06)
        # the trunk away from the shoulder girdle: no triangle within 0.17 m of either shoulder joint (the armpit wall out)
        M["trunk.core"] = M["trunk"] & np.all([np.linalg.norm(c - self.head(self.role("upperarm", s)), axis=1) > 0.17 for s in "lr"], 0)
        gi = [k for k, n in enumerate(p.names) if n.startswith(("clavicle", "scap", "trap", "delt", "upperarm"))]
        legs = sub(self.role("calf", "l")) + sub(self.role("calf", "r"))
        self.torso = np.nonzero((self.piece == "body") & (armw + p.D[:, gi].sum(1) < 1 / 3) & (legs < 0.5)
                                & ((V0 - Hd) @ up < 0))[0]
        self.reg = {}
        im = {}
        for name, m in M.items():
            tr = np.nonzero(m)[0]
            if not len(tr):
                continue
            vw = np.unique(self.Tw[tr])
            di = np.nonzero(m[self.it[:, 0]] & m[self.it[:, 1]])[0]
            self.reg[name] = {"tris": tr, "edges": np.unique(self.tri_e[tr]), "dih": di, "vw": vw, "v": self.rep[vw]}
            ref = None                                              # slide_bone's reference bone
            if name.endswith(".deltoid"):
                s = name[9]
                ref = f"upperarm_share_{s}" if f"upperarm_share_{s}" in p.index else self.role("upperarm", s)
            elif name.startswith("clav_"):
                s = name[5]
                ref = f"clavicle_{s}" if f"clavicle_{s}" in p.index else p.names[p.parent[p.index[self.role("upperarm", s)]]]
            if ref is not None:
                self.reg[name]["ref"] = p.index[ref]
            im[name] = m
        self.mask = im
        allv = np.unique(np.concatenate([r["v"] for r in self.reg.values()]))
        self.testv = allv[self.piece[allv] == "body"]

    # ----------------------------------------------------------------- measures --
    def _inside(self, V, G, N=None):
        """Depth (mm) of each test point inside the posed surface, -1 where not inside (0: inside, no far skin near)."""
        dep = np.full(len(V), -1.0)
        idx = self.testv[~self.ins0[self.testv]]
        if not len(idx):
            return dep, idx
        Rb = ortho(G[self.p.index["pelvis"]][:3, :3] @ np.linalg.inv(self.G0[self.p.index["pelvis"]][:3, :3]))
        N = self._normals(V) if N is None else N
        ins = ray.inside(ray.scene(V, self.T), V[idx] + 3e-4 * N[idx], dirs=DIRS @ Rb.T)
        q = idx[ins]
        if len(q):
            from surfdist import closest_on_tris
            T = self.T[self.ok]
            cen, cen0 = V[T].mean(1), self.V0[T].mean(1)
            _, nn = cKDTree(cen).query(V[q], k=64)
            far = np.linalg.norm(cen0[nn] - self.V0[q][:, None], axis=2) > 0.012
            qi, ki = np.nonzero(far)
            t = T[nn[qi, ki]]
            x = closest_on_tris(V[q][qi], V[t[:, 0]], V[t[:, 1]], V[t[:, 2]])
            d = np.full(len(q), np.inf)
            np.minimum.at(d, qi, np.linalg.norm(V[q][qi] - x, axis=1))
            dep[q] = np.where(np.isfinite(d), d * 1000, 0.0)
        return dep, idx

    def _armtorso(self, V, N, s):
        a = self.armv[s]
        d, i = cKDTree(V[self.torso]).query(V[a])
        q = self.torso[i]
        sd = np.einsum("ij,ij->i", V[a] - V[q], N[q])
        ins = (sd < 0) & (d < 0.03)
        if isinstance(self.at0[s], np.ndarray):
            ins &= ~self.at0[s]
        return int(ins.sum()), float((-sd[ins]).max() * 1000) if ins.any() else 0.0, ins

    def measure(self, V, G, inside=True, flags=False):
        """{region: [MET values]}, and (with `flags`) per triangle 0 / 1 bad / 2 flipped; plus the rigid fits."""
        Vw = V[self.rep]
        es = np.linalg.norm(Vw[self.E[:, 1]] - Vw[self.E[:, 0]], axis=1) / self.el0 - 1
        T = self.T
        fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
        ar = np.linalg.norm(fn, axis=1) / np.maximum(self.a0, 1e-20)
        L = self._blend(G) @ self.L0i
        m = sum(np.einsum("vij,vj->vi", L[T[:, k]], self.n0) for k in range(3))
        flip = np.einsum("ij,ij->i", m, fn) < 0
        bad = (ar < 0.5) | (ar > 2)
        dd = np.degrees(np.abs((self._dihedral(Vw, fn) - self.dih0 + np.pi) % (2 * np.pi) - np.pi))
        N = self._normals(V) if inside else None
        dep = self._inside(V, G, N)[0] if inside else None
        out, fits = {}, {}
        for name, r in self.reg.items():
            e = es[r["edges"]]
            ae = np.abs(e)
            R, t = kabsch(self.V0[r["v"]], V[r["v"]])
            res = np.linalg.norm(V[r["v"]] - (self.V0[r["v"]] @ R.T + t), axis=1) * 1000
            fits[name] = (R, t)
            k = dd[r["dih"]] if len(r["dih"]) else np.zeros(1)
            row = [np.percentile(ae, 50) * 100, np.percentile(ae, 99) * 100, max(np.percentile(e, 99), 0) * 100,
                   max(np.percentile(-e, 99), 0) * 100, bad[r["tris"]].mean() * 100, flip[r["tris"]].mean() * 100,
                   np.percentile(k, 99), k.max(), 0, 0, np.percentile(res, 50), np.percentile(res, 95), res.max(), 0, 0, 0, 0, 0]
            if "ref" in r:                                          # slide_bone: the reference bone's own rigid carry
                j = r["ref"]
                Rj = ortho(G[j][:3, :3] @ np.linalg.inv(self.G0[j][:3, :3]))
                sb = np.linalg.norm(V[r["v"]] - ((self.V0[r["v"]] - self.G0[j][:3, 3]) @ Rj.T + G[j][:3, 3]), axis=1) * 1000
                row[15:18] = [np.percentile(sb, 50), np.percentile(sb, 95), sb.max()]
            if inside:
                dv = dep[r["v"]]
                row[8], row[9] = int((dv > 2).sum()), float(max(dv.max(), 0))
                if name.endswith(".axilla"):
                    row[13], row[14] = self._armtorso(V, N, name[9])[:2]
            out[name] = [round(float(x), 3) for x in row]
        if flags:
            return out, fits, np.where(flip, 2, np.where(bad, 1, 0)) * self.ok
        return out, fits


# ------------------------------------------------------------------- runs --
_B = {}


def body(key):
    if key not in _B:
        _B[key] = Body(key)
    return _B[key]


def load_clip(name):
    if name.startswith("p4:"):
        return json.loads((P4 / (name[3:] + ".json")).read_text())
    return json.loads((DUMP / (name + ".json")).read_text())


def run_clip(task):
    key, layer, name, step = task
    bd = body(key)
    bd.set_layer(layer)
    d = load_clip(name)
    best = {r: [[0.0, -1] for _ in CLIPMET] for r in bd.reg}
    hist = {r: [] for r in bd.reg}
    nf = 0
    for f, V, G in bd.clip_frames(d, step):
        nf += 1
        out, fits = bd.measure(V, G)
        for r, row in out.items():
            R, t = fits[r]
            h = hist[r]
            h.append((V[bd.reg[r]["v"]] - t) @ R)
            if len(h) == 3:
                a = np.linalg.norm(h[2] - 2 * h[1] + h[0], axis=1) * 1000 / step ** 2
                row = row + [round(float(np.percentile(a, 99)), 3), round(float(a.max()), 3)]
                h.pop(0)
            for i, x in enumerate(row):
                if x > best[r][i][0]:
                    best[r][i] = [x, f - step if i >= len(MET) else f]
    return f"{key}.{layer}", name, {"frames": nf, "regions": best}


def solve(axis, u0, meas, target):
    ts = np.arange(-179.5, 180, 0.5)
    f = np.array([meas(rot(axis, t) @ u0) - target for t in ts])
    k = np.nonzero((f[:-1] * f[1:] <= 0) & (np.abs(f[:-1] - f[1:]) < 90))[0]
    if not len(k):
        raise ValueError("no turn reaches the target")
    i = k[np.argmin(np.abs(ts[k]))]
    return float(ts[i] - f[i] * 0.5 / (f[i + 1] - f[i])) if f[i + 1] != f[i] else float(ts[i])


def rom_list(bd):
    """[(pose, joints, side, strip or None, deg, extra(R1) -> turns)]"""
    p, fr = bd.p, bd.frame
    up, lat, front = fr.up, fr.lat, fr.front
    out = []
    for s, sg in (("l", 1), ("r", -1)):
        o = lat * sg
        ua, la, hd, th, cf, ft = (bd.role(r, s) for r in ("upperarm", "lowerarm", "hand", "thigh", "calf", "foot"))
        st = {m: bends.Strip(p, bd.rig, fr, m, s) for m in ("elbow", "knee", "shoulder_abd", "shoulder_flex", "hip_flex")}
        H = bd.head
        for a in (45, 90, 135, 170):
            out.append((f"sh_abd{a}", ["shoulder"], s, st["shoulder_abd"], a, None))
        for a in (45, 90, 135, 170):
            out.append((f"sh_flex{a}", ["shoulder"], s, st["shoulder_flex"], a, None))
        out.append(("sh_ext40", ["shoulder"], s, st["shoulder_flex"], -40, None))
        out.append(("sh_hadd40", ["shoulder"], s, st["shoulder_flex"], 90, lambda R1, ua=ua, sg=sg: [(ua, rot(up, -40 * sg))]))
        u0 = st["shoulder_abd"].u_d0
        for a in (60, -60):
            out.append((f"sh_twist{a:+d}", ["shoulder"], s, st["shoulder_abd"], 10,
                        lambda R1, ua=ua, a=a, u0=u0: [(ua, rot(R1 @ u0, a))]))
        for a in (45, 90, 135, 150):
            out.append((f"elbow{a}", ["elbow"], s, st["elbow"], a, None))
        fa = unit(H(hd) - H(la))
        for a in (80, -80):
            out.append((f"pronate{a:+d}", ["forearm", "wrist", "elbow"], s, None, 0, lambda R1, hd=hd, fa=fa, a=a: [(hd, rot(fa, a))]))
        kid = lambda w: [n for n in p.names if w in n.lower() and p.index[n] in p.subtree(p.index[hd])]
        if kid("index") and kid("pinky"):
            kn = bends.perp(H(kid("index")[0]) - H(kid("pinky")[0]), fa)
        else:
            kn = st["elbow"].axis
        for a in (70, -70):
            out.append((f"wrist_flex{a:+d}", ["wrist"], s, None, 0, lambda R1, hd=hd, kn=kn, a=a: [(hd, rot(kn, a))]))
        for a in (25, -25):
            out.append((f"wrist_dev{a:+d}", ["wrist"], s, None, 0, lambda R1, hd=hd, ax=np.cross(fa, kn), a=a: [(hd, rot(ax, a))]))
        for a in (45, 90, 120):
            out.append((f"hip_flex{a}", ["hip"], s, st["hip_flex"], a, None))
        out.append(("hip_ext25", ["hip"], s, st["hip_flex"], -25, None))
        td = unit(H(cf) - H(th))
        t = solve(front, td, lambda d, o=o: math.degrees(math.atan2(d @ o, -(d @ up))), 45)
        out.append(("hip_abd45", ["hip"], s, None, 0, lambda R1, th=th, t=t: [(th, rot(front, t))]))
        for a in (40, -40):
            out.append((f"hip_rot{a:+d}", ["hip"], s, None, 0, lambda R1, th=th, td=td, a=a: [(th, rot(td, a))]))
        for a in (45, 90, 135, 150):
            out.append((f"knee{a}", ["knee"], s, st["knee"], a, None))
        for nm, ax, a in (("ankle_dorsi25", lat, -25), ("ankle_plantar50", lat, 50), ("ankle_inv+20", front, 20), ("ankle_inv-20", front, -20)):
            out.append((nm, ["ankle"], s, None, 0, lambda R1, ft=ft, ax=ax, a=a: [(ft, rot(ax, a))]))
    nk = bd.chain("neck_") + [bd.head_bone()]
    sp = bd.chain("spine_")
    spread = lambda ch, ax, a: (lambda R1: [(b, rot(ax, a / len(ch))) for b in ch])
    for nm, ax, a in (("head_yaw+70", up, 70), ("head_yaw-70", up, -70), ("head_pitch+40", lat, 40), ("head_pitch-40", lat, -40),
                      ("head_tilt+30", front, 30), ("head_tilt-30", front, -30)):
        out.append((nm, ["neck"], "", None, 0, spread(nk, ax, a)))
    for nm, ax, a in (("spine_twist45", up, 45), ("spine_side30", front, 30), ("spine_flex45", lat, 45), ("spine_ext25", lat, -25)):
        out.append((nm, ["trunk"], "", None, 0, spread(sp, ax, a)))
    return out


def rom_pose(bd, row):
    nm, joints, s, strip, deg, extra = row
    turns, R1 = [], np.eye(3)
    if strip is not None:
        aim = deg
        for _ in range(8):
            t = strip.turn(aim)
            V, G = bd.pose_turns(strip.turns_at(t))
            err = strip.achieved(G) - deg
            if abs(err) < 0.1:
                break
            aim -= err
        turns, R1 = strip.turns_at(t), rot(strip.axis, t)
    if extra is not None:
        turns = turns + extra(R1)
    return bd.pose_turns(turns) if (extra is not None or strip is None) else (V, G)


def run_rom(task):
    key, layer = task
    bd = body(key)
    bd.set_layer(layer)
    res = {}
    for row in rom_list(bd):
        nm, joints, s, strip, deg, extra = row
        V, G = rom_pose(bd, row)
        out, _ = bd.measure(V, G)
        want = [r.replace("{s}", s) for j in joints for r in JOINTS[j]]
        e = {"joints": joints, "regions": {r: out[r] for r in want if r in out}}
        if strip is not None and extra is None:
            s0, s1 = strip.sections(bd.V0, bd.G0), strip.sections(V, G)
            g = [s1[k][0] / s0[k][0] for k in s0 if s0[k][0] == s0[k][0] and s1[k][0] == s1[k][0]]
            a = [s1[k][1] / s0[k][1] for k in s0 if s0[k][1] == s0[k][1] and s1[k][1] == s1[k][1]]
            e["girth"] = [round(min(g), 3), round(max(g), 3)] if g else None
            e["area"] = [round(min(a), 3), round(max(a), 3)] if a else None
        res[f"{nm}|{s}"] = e
    return f"{key}.{layer}", res


# ----------------------------------------------------------------- report --
def score(row):
    return row[MET.index("flip")] * 10 + row[MET.index("bad")] + row[MET.index("st99")] / 100


def worst_clip(A, col, joint, names=None, top=True):
    """(score, clip, frame, region) of the joint's worst frame in a column (by flip, bad, then st99 of the ball)."""
    best = (-1, None, 0, None)
    for clip, e in A["clips"].get(col, {}).items():
        if names is not None and clip not in names:
            continue
        for s in "lr":
            r = JOINTS[joint][0].replace("{s}", s)
            if r not in e["regions"]:
                continue
            b = e["regions"][r]
            i = "flip" if b[MET.index("flip")][0] > 0 else "bad" if b[MET.index("bad")][0] > 0 else "st99"
            sc = score([x[0] for x in b[:len(MET)]])
            if sc > best[0]:
                best = (sc, clip, b[MET.index(i)][1], r)
    return best


def write_md(A, out):
    L = ["# Deformation audit: B (body_p1) vs A (heroine.glb)", "",
         "Cells: the worst over both sides and all frames. Clips = the 33 library dumps (every column poses the same clips);",
         "p4 = A1's rebuilt clips (B only). st/ext/cp %, bad/flip % of triangles, kink deg, ins/at/slide mm, pop mm/frame^2.", ""]
    dumps = sorted(c for c in A["clips"].get("B.full", {}) if not c.startswith("p4:"))
    p4 = sorted(c for c in A["clips"].get("B.full", {}) if c.startswith("p4:"))

    def cell(col, regs, i, names):
        best = (None, "", 0)
        for clip in names:
            e = A["clips"].get(col, {}).get(clip)
            if not e:
                continue
            for r in regs:
                if r in e["regions"] and (best[0] is None or e["regions"][r][i][0] > best[0]):
                    best = (e["regions"][r][i][0], clip, e["regions"][r][i][1])
        return best

    for joint, regs in JOINTS.items():
        L += [f"## {joint}", ""]
        for rg in regs:
            rs = sorted({rg.replace("{s}", s) for s in "lr"})
            L += [f"**{rg}** (clips)", "", "| metric | " + " | ".join(COLS) + " | B.full worst | A.full worst | B p4 | p4 worst |",
                  "|" + "---|" * (len(COLS) + 5)]
            for i, mname in enumerate(CLIPMET):
                if mname.startswith("at_") and not rg.endswith("axilla"):
                    continue
                if mname.startswith("sb") and not (rg.endswith("deltoid") or rg.startswith("clav")):
                    continue
                cs = [cell(c, rs, i, dumps) for c in COLS]
                pc = cell("B.full", rs, i, p4)
                f = lambda b: "-" if b[0] is None else f"{b[0]:.4g}"
                w = lambda b: "-" if not b[0] else f"{b[1].replace('p4:', '')}@{b[2]}"
                L.append(f"| {mname} | " + " | ".join(f(b) for b in cs) + f" | {w(cs[0])} | {w(cs[4])} | {f(pc)} | {w(pc)} |")
            if rs[0] in A.get("lr", {}):
                L += ["", "L/R (B.full clips, st99 / bad / slide95): " + A["lr"][rs[0]]]
            L.append("")
        L += [f"**{joint} ROM** (worst side; st99 / bad / flip / kinkmax / ins_mm / slide95" + (" / at_mm" if joint == "shoulder" else "")
              + "; girth min-max where bends has stations)", "", "| pose | region | " + " | ".join(COLS) + " |", "|" + "---|" * (len(COLS) + 2)]
        poses = sorted({k.split("|")[0] for k, e in A["rom"].get("B.full", {}).items() if joint in e["joints"]},
                       key=lambda n: [k.split("|")[0] for k in A["rom"]["B.full"]].index(n))
        ix = [MET.index(m) for m in ("st99", "bad", "flip", "kinkmax", "ins_mm", "slide95")]
        for ps in poses:
            for rg in regs:
                cells = []
                for c in COLS:
                    rows = [e["regions"][rg.replace("{s}", k.split("|")[1])] for k, e in A["rom"].get(c, {}).items()
                            if k.split("|")[0] == ps and rg.replace("{s}", k.split("|")[1]) in e["regions"]]
                    if not rows:
                        cells.append("-")
                        continue
                    b = max(rows, key=score)
                    txt = "/".join(f"{b[i]:.3g}" for i in ix) + (f"/{b[MET.index('at_mm')]:.3g}" if rg.endswith("axilla") else "")
                    if rg.endswith("deltoid") or rg.startswith("clav"):
                        txt += f" sb{b[MET.index('sb95')]:.3g}"
                    if rg == regs[0]:
                        g = [e.get("girth") for k, e in A["rom"][c].items() if k.split("|")[0] == ps and e.get("girth")]
                        if g:
                            txt += f" g{min(x[0] for x in g):.2f}-{max(x[1] for x in g):.2f}"
                    cells.append(txt)
                L.append(f"| {ps} | {rg.replace('_{s}', '')} | " + " | ".join(cells) + " |")
        L.append("")
    (out / "audit.md").write_text("\n".join(L), encoding="utf-8")


def lr_notes(A):
    out = {}
    e = A["clips"].get("B.full", {})
    for joint, regs in JOINTS.items():
        for rg in regs:
            if "{s}" not in rg:
                continue
            v = {}
            for s in "lr":
                r = rg.replace("{s}", s)
                v[s] = [max((c["regions"][r][MET.index(m)][0] for n, c in e.items() if r in c["regions"] and not n.startswith("p4:")), default=0)
                        for m in ("st99", "bad", "slide95")]
            out[rg.replace("{s}", "l")] = "L " + " / ".join(f"{x:.3g}" for x in v["l"]) + "; R " + " / ".join(f"{x:.3g}" for x in v["r"])
    return out


# ----------------------------------------------------------------- sheets --
def frame_of(bd, clip, f):
    for g, V, G in bd.clip_frames(load_clip(clip), 1):
        if g == f:
            return V, G
    raise KeyError((clip, f))


def panel(bd, V, G, region, cam, half=0.19):
    """Clay and flagged clay of a posed body about a region: (two [h, w, 3] uint8, the camera in body coords)."""
    out, fits, flag = bd.measure(V, G, inside=False, flags=True)
    R, _ = fits[region]
    fr = bd.frame
    B = np.stack([fr.lat, fr.up, fr.front], 1)
    if cam is None:
        tr = bd.reg[region]["tris"]
        n = bd.n0[tr[flag[tr] > 0]]
        n = n.sum(0) / max(np.linalg.norm(n, axis=1).sum(), 1e-12) if len(n) else np.zeros(3)
        cam = tuple(B.T @ unit(n)) if np.linalg.norm(n) > 0.3 else None
    if cam is None:
        j = region.split("_")[0].split(".")[0]
        j = "shoulder" if j == "clav" else j
        c = CAM[j]
        cam = (c[0] * (-1 if region.split(".")[0].endswith("_r") else 1), c[1], c[2])
    cw = R @ (B @ unit(np.array(cam)))
    ey = bends.perp(R @ fr.up, cw) if abs((R @ fr.up) @ cw) < 0.95 else bends.perp(R @ fr.front, cw)
    view = ray.View(V[bd.reg[region]["v"]].mean(0), np.cross(ey, cw), ey, cw, bends.PX_CLOSE, -half, half, -half, half)
    img, m = bends.clay(V, bd.T, view)
    g = np.repeat((np.clip(img, 0, 1) * 255).astype(np.uint8)[..., None], 3, 2)
    pid, _ = view.cast(ray.scene(V, bd.T))
    fl = np.where(pid >= 0, flag[np.maximum(pid, 0)], 0)
    mk = g.copy()
    mk[fl == 1] = (0.45 * mk[fl == 1] + 0.55 * np.array([255, 150, 0])).astype(np.uint8)
    mk[fl == 2] = (0.35 * mk[fl == 2] + 0.65 * np.array([230, 0, 0])).astype(np.uint8)
    return g, mk, cam, out[region]


def sheets(A, out):
    from PIL import Image, ImageDraw
    B, Ab = body("B"), body("A")
    B.set_layer("full")
    Ab.set_layer("full")
    dumps = {c for c in A["clips"]["A.full"]}
    for joint in JOINTS:
        rows = []
        sc, clip, f, region = worst_clip(A, "B.full", joint)
        if clip:
            Vb, Gb = frame_of(B, clip, f)
            if clip in dumps:
                ac, af = clip, f
            else:
                twin = next((v for k, v in P4_TWIN.items() if clip[3:].startswith(k)), "sword_heavy")
                e = A["clips"]["A.full"][twin]["regions"].get(region)
                ac, af = twin, (e[MET.index("st99")][1] if e else 0)
            Va, Ga = frame_of(Ab, ac, af)
            rows.append((f"clip {clip}@{f}", f"clip {ac}@{af}", Vb, Gb, Va, Ga, region))
        best = (-1, None)
        for k, e in A["rom"]["B.full"].items():
            if joint in e["joints"]:
                r = JOINTS[joint][0].replace("{s}", k.split("|")[1])
                if r in e["regions"] and score(e["regions"][r]) > best[0]:
                    best = (score(e["regions"][r]), k, r)
        if best[1]:
            nm, s = best[1].split("|")
            Vb, Gb = rom_pose(B, next(r for r in rom_list(B) if r[0] == nm and r[2] == s))
            Va, Ga = rom_pose(Ab, next(r for r in rom_list(Ab) if r[0] == nm and r[2] == s))
            rows.append((f"ROM {nm} {s}", f"ROM {nm} {s}", Vb, Gb, Va, Ga, best[2]))
        tiles = []
        for tb, ta, Vb, Gb, Va, Ga, region in rows:
            if region not in Ab.reg:
                continue
            g1, m1, cam, rb = panel(B, Vb, Gb, region, None)
            g2, m2, _, ra = panel(Ab, Va, Ga, region, cam)
            cap = lambda t, r: f"{t} {region}: st99 {r[1]:.0f}% bad {r[4]:.1f}% flip {r[5]:.2f}% kink {r[7]:.0f} slide95 {r[11]:.1f}mm"
            tiles.append(([g1, m1, g2, m2], "B " + cap(tb, rb), "A " + cap(ta, ra)))
        if not tiles:
            continue
        h, w = tiles[0][0][0].shape[:2]
        im = Image.new("RGB", (4 * w, len(tiles) * (h + 28)), (255, 255, 255))
        dr = ImageDraw.Draw(im)
        for i, (ims, cb, ca) in enumerate(tiles):
            for k, g in enumerate(ims):
                im.paste(Image.fromarray(g), (k * w, i * (h + 28) + 28))
            dr.text((4, i * (h + 28) + 2), cb, fill=(0, 0, 0))
            dr.text((2 * w + 4, i * (h + 28) + 2), ca, fill=(0, 0, 0))
            dr.text((4, i * (h + 28) + 14), "clay | flagged: orange bad area, red flipped", fill=(90, 90, 90))
        im.save(out / f"sheet_{joint}.png")
        im.resize((im.width // 2, im.height // 2), Image.LANCZOS).save(out / f"sheet_{joint}_half.jpg", quality=88)
        print("sheet", joint, [t[1] for t in tiles], flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="clips,p4,rom,md,sheets")
    ap.add_argument("--procs", type=int, default=5)
    ap.add_argument("--step", type=int, default=1)
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--clips", default="")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    only = a.only.split(",")
    jp = out / "audit.json"
    A = json.loads(jp.read_text()) if jp.exists() else {"clips": {}, "rom": {}}
    from multiprocessing import Pool
    tasks = []
    names = a.clips.split(",") if a.clips else sorted(p.stem for p in DUMP.glob("*.json"))
    if "clips" in only:
        tasks += [(k, l, n, a.step) for n in names for k in BODIES for l in BODIES[k][3]]
    if "p4" in only and P4.exists():
        tasks += [(k, l, "p4:" + p.stem, 1) for p in sorted(P4.glob("*.json")) for k in ("B", "Bplay") for l in BODIES[k][3]]
    rt = [(k, l) for k in BODIES for l in BODIES[k][3]] if "rom" in only else []
    if tasks or rt:
        with Pool(a.procs) as pool:
            rr = pool.imap_unordered(run_rom, rt)
            for i, (col, name, res) in enumerate(pool.imap_unordered(run_clip, tasks)):
                A["clips"].setdefault(col, {})[name] = res
                if i % 20 == 0:
                    print(f"clips {i + 1}/{len(tasks)}", flush=True)
                    jp.write_text(json.dumps(A, separators=(",", ":")))
            for col, res in rr:
                A["rom"][col] = res
                print("rom", col, flush=True)
        A["lr"] = lr_notes(A)
        jp.write_text(json.dumps(A, separators=(",", ":")))
    if "md" in only:
        A["lr"] = lr_notes(A)
        write_md(A, out)
    if "sheets" in only:
        sheets(A, out)


if __name__ == "__main__":
    main()
