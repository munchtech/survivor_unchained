"""foldcheck: the posed skin's folds, by region and side, on the game's poser (P1 posed folds, 13 Nov).

    python tools/body/foldcheck.py [--p1 DIR] [--sets rom,rnd,game] [--modes plain,laws,full] [--step N]
                                   [--whole-x] [--out FILE]

Poses the body as the game does (posers.LbsPoser + rig.json's driver: the helper laws AND the corrective shapes,
mode "full"), and in the R&D's two modes for like-for-like numbers (Marionette rig lead 18): "plain" (bare LBS, no
laws) and "laws" (the helper laws, no shapes; what fitgates' "driven" rows were). Pose sets:
  rom   fitgates' ROM (21 bends: elbow, knee, shoulder abd/flex, hip flex/abd, spine_flex), restated below;
  rnd   the R&D clips (Marionette x14/r11 p1_top_folk_f_walk "walk", p1_top_dw_strike_f "fight"), every key;
  game  her 33 game clips from the keys dumps (tools/body/out/clips, P1BakeRun; git-ignored), every --step'th key,
        posed as clipcheck.Body does (unkeyed helpers at their rest local, then the laws); mode full only.
Per pose and mode, on the body's own triangles (head pieces left out, as the R&D did):
  inv / sharp   a triangle against the area-weighted mean normal of its vertex ring (c > 0.2 at rest, < 0 posed),
                and triangles on an edge whose dihedral turns past 120 deg (new against rest): foldlib.inverted's rule.
                "_rd" = on the glb's UV-split triangles exactly as the R&D ran it; the plain names = WELDED by position
                first (a UV seam is not a crease: the split copies are one point).
  x             self-crossing: posed edges that pass through a posed triangle they share no (welded) point with,
                counted as edges, new against rest (at rest only the toes cross, 380 edges a side).
The four routed faults per side (rest centroid boxes, mm; her left is +x):
  shoulder_{s}  x 60..280, y 1380..1600 (the deltoid-trapezius seam, shoulder_flex);
  strap_{s}     within 35 mm of the fitted top's open edges (x14/r19 p1_top_rest.glb; the strike's keys 18-21);
  lumbar_{s}    y 1080..1130, |x| < 60, z < -40 (walk:10's lumbar midline);
  belly_{s}     front torso self-crossing: edges with rest y 950..1250, z > 20, |x| < 170 through triangles of that
                band (spine_flex: the upper belly through the lower).
Whole-body totals (inv, sharp, and x with --whole-x) are the "no new folds elsewhere" baseline.
Writes --out (default tools/body/out/foldcheck.json) and prints one line per pose with any fault.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
from scipy.sparse import coo_matrix
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from gl import Glb, weld, boundary_edges  # noqa: E402
from posers import make_poser  # noqa: E402

REPO = HERE.parent.parent
P1 = REPO / "godot/art/people/body_p1"
DUMP = HERE / "out/clips"
MARIONETTE = Path(r"C:\Users\munch\Desktop\Marionette")
RND = MARIONETTE / "generated/rnd/x14"
RND_CLIPS = {"walk": RND / "r11/p1_top_folk_f_walk.glb", "fight": RND / "r11/p1_top_dw_strike_f.glb"}
TOP = RND / "r19/p1_top_rest.glb"
SIDES = (("l", 1.0), ("r", -1.0))
HELPER = ("twist", "share", "point", "corrective")
# fitgates.ROM restated (Marionette tools/npc/attach/fitgates.py; rig.mjs setupPose)
ROM = ([{"id": f"elbow_{s}_{d}", "joint": f"lowerarm_{s}", "toward": (0, 0, 1), "deg": d} for s, _ in SIDES for d in (90, 130)]
       + [{"id": f"knee_{s}_{d}", "joint": f"calf_{s}", "toward": (0, 0, -1), "deg": d} for s, _ in SIDES for d in (90, 130)]
       + [{"id": f"shoulder_abd_{s}", "joint": f"upperarm_{s}", "toward": (0, 1, 0), "deg": 60} for s, _ in SIDES]
       + [{"id": f"shoulder_flex_{s}", "joint": f"upperarm_{s}", "toward": (0, 0, 1), "deg": 90} for s, _ in SIDES]
       + [{"id": f"hip_flex_{s}", "joint": f"thigh_{s}", "toward": (0, 0, 1), "deg": 90} for s, _ in SIDES]
       + [{"id": f"hip_abd_{s}", "joint": f"thigh_{s}", "toward": (g, 0, 0), "deg": 45} for s, g in SIDES]
       + [{"id": "spine_flex", "joint": "spine_01", "toward": (0, 0, 1), "deg": 45}])
FAULTS = ("shoulder", "strap", "lumbar", "belly")


def U(x):
    return x / np.maximum(np.linalg.norm(x, axis=-1, keepdims=True), 1e-12)


def tri_normals(V, T):
    return np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])


def vt_adj(T, n):
    return coo_matrix((np.ones(T.size), (np.repeat(np.arange(len(T)), 3), T.ravel())), shape=(len(T), n)).tocsr()


def edge_pairs(T):
    """Triangle pairs sharing an edge."""
    e = np.sort(np.r_[T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]], 1)
    t = np.tile(np.arange(len(T)), 3)
    key = e[:, 0].astype(np.int64) * (int(T.max()) + 1) + e[:, 1]
    o = np.argsort(key, kind="stable")
    k, t = key[o], t[o]
    same = k[1:] == k[:-1]
    return np.c_[t[:-1][same], t[1:][same]]


def inverted(X0, X1, T, A, EP):
    """foldlib.inverted (Marionette rig18): (against the ring, sharp dihedral) per triangle, new against rest."""
    def ring(X):
        N = tri_normals(X, T)
        return N, (A @ (A.T @ N)) - 3 * N
    N0, M0 = ring(X0)
    N1, M1 = ring(X1)
    c0 = np.einsum("ij,ij->i", U(N0), U(M0))
    c1 = np.einsum("ij,ij->i", U(N1), U(M1))
    ok = (np.linalg.norm(N1, axis=1) > 1e-14) & (np.linalg.norm(N0, axis=1) > 1e-14)
    nb = ok & (c0 > 0.2) & (c1 < 0)
    d0 = np.einsum("ij,ij->i", U(N0[EP[:, 0]]), U(N0[EP[:, 1]]))
    d1 = np.einsum("ij,ij->i", U(N1[EP[:, 0]]), U(N1[EP[:, 1]]))
    sh = np.zeros(len(T), bool)
    sh[EP[(d1 < -0.5) & (d0 > -0.5)].ravel()] = True
    return nb, sh & ok


def crossings(V, T, E, emask=None, tmask=None, chunk=20000):
    """Edges (rows of E, welded indices into V) that pass through a triangle of T sharing no point with them:
    -> (bool per edge, bool per triangle). A grid of cells the size of the longest edge / triangle bounds the pairs."""
    ei = np.flatnonzero(emask) if emask is not None else np.arange(len(E))
    ti = np.flatnonzero(tmask) if tmask is not None else np.arange(len(T))
    he, ht = np.zeros(len(E), bool), np.zeros(len(T), bool)
    if not len(ei) or not len(ti):
        return he, ht
    Tt = T[ti]
    A, B, C = V[Tt[:, 0]], V[Tt[:, 1]], V[Tt[:, 2]]
    cen = (A + B + C) / 3
    rad = np.max(np.linalg.norm(np.stack([A, B, C], 1) - cen[:, None], axis=2), 1)
    Ee = E[ei]
    P0, P1 = V[Ee[:, 0]], V[Ee[:, 1]]
    mid, half = 0.5 * (P0 + P1), 0.5 * np.linalg.norm(P1 - P0, axis=1)
    tree = cKDTree(cen)
    # candidate triangles within (half + the largest triangle radius) of the edge's middle, then exact per pair
    R = float(rad.max())
    for s in range(0, len(ei), chunk):
        sl = slice(s, s + chunk)
        lists = tree.query_ball_point(mid[sl], half[sl] + R)
        ne = np.fromiter((len(x) for x in lists), int, len(lists))
        if not ne.sum():
            continue
        pe = np.repeat(np.arange(s, min(s + chunk, len(ei))), ne)
        pt = np.fromiter((t for x in lists for t in x), int, int(ne.sum()))
        # drop pairs farther than both radii, and pairs sharing a point
        k = np.linalg.norm(mid[pe] - cen[pt], axis=1) <= half[pe] + rad[pt] + 1e-9
        pe, pt = pe[k], pt[k]
        sh = (Ee[pe][:, :, None] == Tt[pt][:, None, :]).any((1, 2))
        pe, pt = pe[~sh], pt[~sh]
        if not len(pe):
            continue
        O, D = P0[pe], P1[pe] - P0[pe]
        a, e1, e2 = A[pt], B[pt] - A[pt], C[pt] - A[pt]
        p = np.cross(D, e2)
        det = np.einsum("ij,ij->i", e1, p)
        ok = np.abs(det) > 1e-18
        inv = np.where(ok, 1 / np.where(ok, det, 1), 0)
        tv = O - a
        u = np.einsum("ij,ij->i", tv, p) * inv
        q = np.cross(tv, e1)
        v = np.einsum("ij,ij->i", D, q) * inv
        t = np.einsum("ij,ij->i", e2, q) * inv
        h = ok & (u > 0) & (v > 0) & (u + v < 1) & (t > 0) & (t < 1)
        he[ei[pe[h]]] = True
        ht[ti[pt[h]]] = True
    return he, ht


class Skin:
    """The body's own triangles, raw (UV-split, the R&D's) and welded, with the fault regions on rest centroids."""

    def __init__(self, poser, top=TOP):
        p = self.p = poser
        nb = int((p.piece == "body").sum())
        self.nb = nb
        T = p.T[(p.T < nb).all(1)]
        self.T = T
        X0 = p.P0[:nb]
        self.X0 = X0
        self.A, self.EP = vt_adj(T, nb), edge_pairs(T)
        rep = weld(X0, 1e-6)
        self.rep = rep
        Tw = rep[T]
        keep = (Tw[:, 0] != Tw[:, 1]) & (Tw[:, 1] != Tw[:, 2]) & (Tw[:, 0] != Tw[:, 2])
        self.Tw, self.kw = Tw[keep], keep
        nw = int(rep.max()) + 1
        self.nw = nw
        first = np.full(nw, -1)
        first[rep[::-1]] = np.arange(nb)[::-1]
        self.first = first                       # a raw point per welded point
        self.Aw, self.EPw = vt_adj(self.Tw, nw), edge_pairs(self.Tw)
        self.Ew = np.unique(np.sort(np.r_[self.Tw[:, [0, 1]], self.Tw[:, [1, 2]], self.Tw[:, [2, 0]]], 1), axis=0)
        Xw = X0[first]
        self.Xw0 = Xw
        c = X0[T].mean(1) * 1e3                   # raw triangles' rest centroids, mm
        cw = Xw[self.Tw].mean(1) * 1e3
        em = Xw[self.Ew].mean(1) * 1e3
        self.reg_t, self.reg_tw = {}, {}
        strap = None
        if top is not None and Path(top).exists():
            g = Glb(str(top))
            m = next(m for m in g.meshes if m.node.startswith("piece_"))
            r = weld(m.P.astype(float), 1e-6)
            be = boundary_edges(r[m.T])
            fp = np.zeros(len(m.P), int)
            fp[r[::-1]] = np.arange(len(m.P))[::-1]
            pts = m.P.astype(float)[fp[np.unique(be.ravel())]] * 1e3
            strap = cKDTree(pts)
        for s, sg in SIDES:
            for tag, cc, out in (("raw", c, self.reg_t), ("w", cw, self.reg_tw)):
                x, y, z = cc[:, 0] * sg, cc[:, 1], cc[:, 2]
                out[f"shoulder_{s}"] = (x >= 60) & (x <= 280) & (y >= 1380) & (y <= 1600)
                out[f"lumbar_{s}"] = (x >= 0) & (x < 60) & (y >= 1080) & (y <= 1130) & (z < -40)
                if strap is not None:
                    out[f"strap_{s}"] = (x >= 0) & np.isfinite(strap.query(cc, distance_upper_bound=35.0)[0])
        band = lambda q: (q[:, 1] >= 950) & (q[:, 1] <= 1250) & (q[:, 2] > 20) & (np.abs(q[:, 0]) < 170)  # noqa: E731
        self.belly_t = band(cw)
        self.belly_e = {s: band(em) & (em[:, 0] * sg >= 0) for s, sg in SIDES}
        self.belly_ea = band(em)
        self.rest_x = crossings(self.Xw0, self.Tw, self.Ew)[0]     # the toes cross themselves at rest (380 a side)

    def measure(self, Vfull, whole_x=False):
        V = Vfull[:self.nb]
        Vw = V[self.first]
        r = {}
        nb, sh = inverted(self.X0, V, self.T, self.A, self.EP)
        nbw, shw = inverted(self.Xw0, Vw, self.Tw, self.Aw, self.EPw)
        r["whole"] = {"inv": int(nbw.sum()), "sharp": int(shw.sum()), "inv_rd": int(nb.sum()), "sharp_rd": int(sh.sum())}
        for k, m in self.reg_tw.items():
            mr = self.reg_t[k]
            r[k] = {"inv": int((nbw & m).sum()), "sharp": int((shw & m).sum()),
                    "inv_rd": int((nb & mr).sum()), "sharp_rd": int((sh & mr).sum())}
        he, ht = crossings(Vw, self.Tw, self.Ew, self.belly_ea, self.belly_t)
        for s, _ in SIDES:
            r[f"belly_{s}"] = {"x": int((he & self.belly_e[s]).sum()), "x_tris": int(ht.sum()),
                               "x_mm": None}
            if (he & self.belly_e[s]).any():
                r[f"belly_{s}"]["x_rest_y"] = [round(float(v)) for v in np.percentile(
                    self.Xw0[self.Ew[he & self.belly_e[s]]].mean(1)[:, 1] * 1e3, [5, 50, 95])]
        if whole_x:
            he, _ = crossings(Vw, self.Tw, self.Ew)
            r["whole"]["x"] = int((he & ~self.rest_x).sum())          # new against rest
        return r


# ---- poses: each yields (label, worlds G of the poser's bones, keyed bone names or None)
def rodrigues(axis, deg):
    a = U(np.asarray(axis, float))
    t = math.radians(deg)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + math.sin(t) * K + (1 - math.cos(t)) * K @ K


def rom_poses(p):
    kids = {}
    for k, pk in enumerate(p.parent):
        kids.setdefault(int(pk), []).append(k)
    for pose in ROM:
        ji = p.index.get(pose["joint"])
        if ji is None or not kids.get(ji):
            continue
        ch = kids[ji]
        c = next((i for i in ch if not any(h in p.names[i].lower() for h in HELPER)), ch[0])
        a, b = p.rest[ji][:3, 3], p.rest[c][:3, 3]
        du = U(b - a)
        axis = np.cross(du, U(np.asarray(pose["toward"], float)))
        if np.linalg.norm(axis) < math.sin(math.radians(5)):
            axis = np.cross(du, [1, 0, 0])
        R = rodrigues(axis, pose["deg"])
        M = np.eye(4)
        M[:3, :3], M[:3, 3] = R, a - R @ a
        G = p.rest.copy()
        sub = p.subtree(ji)
        G[sub] = M @ G[sub]
        yield pose["id"], G, None


def rnd_poses(p, which):
    sys.path.insert(0, str(MARIONETTE / "tools/npc/attach"))
    import glbx  # noqa: E402
    for tag in which:
        j, b = glbx.read(str(RND_CLIPS[tag]))
        an = j["animations"][0]
        keyed = {j["nodes"][ch["target"]["node"]].get("name") for ch in an["channels"] if "node" in ch["target"]}
        sk = j["skins"][0]
        ibm = glbx.accessor(j, b, sk["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
        jn = [j["nodes"][n]["name"] for n in sk["joints"]]
        times = glbx.clip_times(j, b, 0)
        loc = glbx.clip_locals(j, b, 0, times)
        my_ibm = np.linalg.inv(p.rest)
        for k in range(len(times)):
            Wd = glbx.worlds(j, loc[k])
            G = p.rest.copy()
            for i, n in enumerate(sk["joints"]):
                q = p.index.get(jn[i])
                if q is not None:
                    G[q] = (Wd[n] @ ibm[i]) @ np.linalg.inv(my_ibm[q])
            yield f"{tag}:{k}", G, keyed


def game_poses(p, clips, step, dump=DUMP):
    import clipcheck as cc
    for name in clips:
        f = Path(dump) / f"{name}.json"
        if not f.exists():
            print(f"  (no keys dump {f.name})", flush=True)
            continue
        d = json.loads(f.read_text())
        Gb = np.stack([cc.mats(x) for x in d["B"]])
        bn = d["b_names"]
        j = bn.index("pelvis")
        X = p.rest[p.index["pelvis"]] @ np.linalg.inv(cc.mats(d["b_rest"])[j])
        mp = [p.index.get(n, -1) for n in bn]
        for fr in range(0, len(Gb), step):
            G = p.rest.copy()
            got = np.zeros(len(G), bool)
            for a, k in enumerate(mp):
                if k >= 0:
                    G[k] = X @ Gb[fr][a]
                    got[k] = True
            yield f"{name}:{fr}", G, (set(d["keyed"]), got)


class Modes:
    def __init__(self, p, rig):
        self.p, self.rig, self.drv = p, rig, p.driver
        self.helpers = set()
        for h in rig.get("helpers", []):
            for s in ("l", "r") if "{s}" in h["name"] else ("",):
                self.helpers.add(h["name"].replace("{s}", s))
        par = p.parent
        self.order, seen = [], set()

        def visit(k):
            if k in seen:
                return
            if par[k] >= 0:
                visit(par[k])
            seen.add(k)
            self.order.append(k)
        for k in range(len(p.names)):
            visit(k)

    def hold(self, G, keyed):
        """Unkeyed helpers (and bones a dump lacks) at their rest local, as P1Laws / clipcheck.Body."""
        if keyed is None:
            return G
        got = None
        if isinstance(keyed, tuple):
            keyed, got = keyed
        p = self.p
        G = G.copy()
        for k in self.order:
            pk = p.parent[k]
            n = p.names[k]
            if pk >= 0 and ((got is not None and not got[k]) or (n in self.helpers and n not in keyed)):
                G[k] = G[pk] @ (np.linalg.inv(p.rest[pk]) @ p.rest[k])
        return G

    def pose(self, G, keyed, mode):
        p = self.p
        if mode == "plain":
            if isinstance(keyed, tuple):          # a game dump: bones it lacks at rest local only
                G = self.hold(G, (set(p.names), keyed[1]))
            return p._skin(G, {})
        G = self.hold(G, keyed)
        if mode == "laws":
            G, _ = self.drv.drive_helpers(p, G, self.rig)
            return p._skin(G, {})
        G, w = self.drv.drive(p, G, self.rig)
        return p._skin(G, w)


_W = {}


def _init(p1):
    rig = json.loads((Path(p1) / "rig.json").read_text())
    p = make_poser("lbs", str(Path(p1) / "body.glb"), rig)
    _W.update(p=p, sk=Skin(p), md=Modes(p, rig))


def _one(job):
    st, mode, lab, G, keyed, whole_x = job
    return _W["sk"].measure(_W["md"].pose(G, keyed, mode), whole_x)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--p1", default=str(P1))
    ap.add_argument("--sets", default="rom,rnd,game")
    ap.add_argument("--modes", default="plain,laws,full")
    ap.add_argument("--rnd", default="walk,fight")
    ap.add_argument("--clips", default=None, help="game clips (default: every keys dump)")
    ap.add_argument("--rom", default=None, help="ROM ids (default: all)")
    ap.add_argument("--step", type=int, default=2, help="game clips: every Nth key")
    ap.add_argument("--whole-x", action="store_true", help="whole-body self-crossing per pose (slower)")
    ap.add_argument("--dump", default=str(DUMP))
    ap.add_argument("--jobs", type=int, default=12)
    ap.add_argument("--out", default=str(HERE / "out/foldcheck.json"))
    a = ap.parse_args(argv)
    t0 = time.time()
    rig = json.loads((Path(a.p1) / "rig.json").read_text())
    p = make_poser("lbs", str(Path(a.p1) / "body.glb"), rig)
    sk = Skin(p)
    modes = a.modes.split(",")
    rest = sk.measure(p.P0, a.whole_x)
    out = {"p1": str(a.p1), "rest": rest, "poses": {}}
    sets = a.sets.split(",")
    src = []
    if "rom" in sets:
        want = set(a.rom.split(",")) if a.rom else None
        src += [("rom", m, x) for x in rom_poses(p) if want is None or x[0] in want for m in modes]
    if "rnd" in sets:
        src += [("rnd", m, x) for x in rnd_poses(p, a.rnd.split(",")) for m in modes]
    if "game" in sets:
        clips = a.clips.split(",") if a.clips else sorted(f.stem for f in Path(a.dump).glob("*.json"))
        src += [("game", "full", x) for x in game_poses(p, clips, a.step, a.dump)]
    from multiprocessing import Pool
    jobs = [(st, mode, lab, G, keyed, a.whole_x) for st, mode, (lab, G, keyed) in src]
    with Pool(a.jobs, initializer=_init, initargs=(a.p1,)) as pool:
        res = pool.map(_one, jobs, chunksize=4)
    for (st, mode, lab, _, _, _), r in zip(jobs, res):
        out["poses"].setdefault(f"{st}:{lab}", {})[mode] = r
        f = {k: v for k, v in r.items() if k != "whole" and (v.get("inv") or v.get("sharp") or v.get("x"))}
        w = r["whole"]
        if f or st != "game":
            print(f"{st}:{lab:22s} {mode:5s} whole inv {w['inv']:4d} sharp {w['sharp']:4d} (rd {w['inv_rd']}/{w['sharp_rd']})"
                  + (f" x {w['x']}" if "x" in w else "") + " | "
                  + " ".join(f"{k} {v.get('inv', v.get('x'))}/{v.get('sharp', v.get('x_tris'))}" for k, v in f.items()), flush=True)
    tot = {}
    for lab, mm in out["poses"].items():
        for mode, r in mm.items():
            key = lab.split(":")[0] + ":" + lab.split(":")[1] + ":" + mode
            t = tot.setdefault(key, {})
            for k, v in r.items():
                for q, n in v.items():
                    if isinstance(n, int):
                        t[f"{k}.{q}"] = t.get(f"{k}.{q}", 0) + n
    out["totals"] = tot
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=1))
    print(f"wrote {a.out} ({len(out['poses'])} poses, {time.time() - t0:.0f}s)")


if __name__ == "__main__":
    main()
