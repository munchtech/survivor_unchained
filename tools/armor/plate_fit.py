"""Rigid plate fit (Body 14 fit2, 26 October 2026): each plate of a shell piece (a pauldron's shell, a lame) skinned
by ONE weight set, fitted to her posed body over her clips.

A rigid plate's posed point is its rest point through one blended matrix, sum_k w_k S_k, so every gap wearcheck
measures from a point of her (her tucked skin under the piece, a top's surface under it) out to the plate's inner face
is linear in the plate's weights w (the face's normal held from the last round). Per piece, a small LP over its
plates' weights (tools/armor/plate_fit.json: candidate bones per side, plus those the plate carries now):

  minimise  sum_i a_i t_i + reg * |w - w0|_1
  s.t.      t_i >= c - g_if(w)   (each sample i's worst frames f: her tucked skin, a top of another source, the lame
                                  under it; c the clearance, a_i its kind's weight)
            |swim_f(w)| <= max(swim_f(w0), floor)  (each plate point vs her nearest skin point, over her idles:
                                  no more slide than the follow's weights give)
            w >= 0, sum w = 1, at most max_infl bones

w0 is the plate's mean weight set now (the follow's). The rows are re-chosen and re-linearised each round from a full
wearcheck-like measure (the tracked rest-hit face, re-cast where near; tools/armor/wearcheck.py's rules), which also
gives the before/after counts (OUT>2: past the outer face by 2 mm, as wearcheck's table).

Plates (plate_fit.json "group"): 'side' = a side's rigid parts all one plate (a shell with its trims and studs);
'sets' = rigid parts clustered by their original weight set (--orig id=<gltf>: the export's, by mesh and point;
else the file's), one plate a cluster (lames). Small and non-rigid parts within attach_mm of a plate ride it (ties:
the nearest original set); LOD and shadow meshes ride their nearest plate point. Her shoulder shapes on the piece
(body_follow_post's) are kept ("shapes": "keep", measured: the fit with them is far better, warden.pauldrons skin
OUT>2 on cast_raise/leap/idle_warden 1847 -> 1099 kept vs 1647 dropped); "drop" takes them off the plates' points.

    python tools/armor/plate_fit.py [--pieces a,b,..] [--clips c1,..] [--step 2] [--out <dir>] [--orig id=<gltf>,..]
                                    [--write] [--shapes keep|drop]

WC_ART / ANIM_PEOPLE as wearcheck (the stage's art). --write puts the fitted weights into the piece files (mark
plate_fit). Prints PLATE_FIT lines (the chain's numbers); writes <out>/plate_fit.json (per plate: its set, w0, counts).
"""
import json
import os
import sys
import time

import numpy as np
from scipy import sparse
from scipy.optimize import linprog
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools", "assets"))
import wearcheck as wc  # noqa: E402
skin = wc.skin
from heroine_neck import _Gl  # noqa: E402
from body_follow_post import _weights, _add_acc, _append, _sparse_g, RIGID_MATS  # noqa: E402

CONF = json.load(open(os.path.join(HERE, "plate_fit.json"), encoding="utf-8"))
MARK = "plate_fit"


def say(*a):
    print("PLATE_FIT", *a, flush=True)


def is_rigid(mat):
    return mat in RIGID_MATS or mat.startswith("gem_")


def weld_components(X, F):
    from scipy.sparse.csgraph import connected_components
    q = np.round(X * 1e5).astype(np.int64)
    _, inv = np.unique(q, axis=0, return_inverse=True)
    inv = inv.ravel()
    if not len(F):
        return inv
    e = np.r_[F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]
    nv = inv.max() + 1
    A = sparse.coo_matrix((np.ones(len(e)), (inv[e[:, 0]], inv[e[:, 1]])), (nv, nv))
    return connected_components(A, directed=False)[1][inv]


def sparse_read(G, ai):
    """A (maybe sparse) VEC3 accessor of a _Gl file: [count, 3]."""
    a = G.g["accessors"][ai]
    if "bufferView" in a:
        out = G.get(ai).astype(float)
    else:
        out = np.zeros((a["count"], 3))
    sp = a.get("sparse")
    if sp:
        bvi, bvv = G.g["bufferViews"][sp["indices"]["bufferView"]], G.g["bufferViews"][sp["values"]["bufferView"]]
        it = {5125: "<u4", 5123: "<u2", 5121: "u1"}[sp["indices"]["componentType"]]
        o = G.b0 + bvi.get("byteOffset", 0) + sp["indices"].get("byteOffset", 0)
        ix = np.frombuffer(bytes(G.buf[o:o + np.dtype(it).itemsize * sp["count"]]), it).astype(np.int64)
        o = G.b0 + bvv.get("byteOffset", 0) + sp["values"].get("byteOffset", 0)
        out[ix] = np.frombuffer(bytes(G.buf[o:o + 12 * sp["count"]]), "<f4").reshape(-1, 3)
    return out


# ----------------------------------------------------------------- the parts --
class Piece:
    """A piece's file: its meshes' primitives (points, faces, weights by bone name, material), welded parts, plates."""

    def __init__(self, row, names, cfg, orig=None):
        self.row, self.id, self.cfg = row, row["id"], cfg
        self.path = row["path"]
        G = _Gl(self.path)
        g = G.g
        self.prims = []      # (node name, mesh index, prim index, X, dense W [n, len(names)], F, mat, lod0, shadow)
        lod0 = set(row["meshes"])
        Go = _Gl(orig) if orig else None
        oprims = {}
        if Go:
            for n in Go.g["nodes"]:
                if "mesh" in n and "skin" in n:
                    m = Go.g["meshes"][n["mesh"]]
                    jn = [Go.g["nodes"][j]["name"] for j in Go.g["skins"][n["skin"]]["joints"]]
                    for pi, p in enumerate(m["primitives"]):
                        oprims[(n["name"], pi)] = (Go, p, jn)
        col = {nm: i for i, nm in enumerate(names)}
        for n in g["nodes"]:
            if "mesh" not in n or "skin" not in n:
                continue
            m = g["meshes"][n["mesh"]]
            if not m.get("name", "").startswith(self.id + "."):
                continue
            jn = [g["nodes"][j]["name"] for j in g["skins"][n["skin"]]["joints"]]
            for pi, p in enumerate(m["primitives"]):
                a = p["attributes"]
                X = G.get(a["POSITION"]).astype(float)
                J, W = _weights(G, a)
                D = np.zeros((len(X), len(names)))
                for k in range(J.shape[1]):
                    c = np.array([col.get(jn[j], -1) for j in J[:, k]])
                    ok = c >= 0
                    np.add.at(D, (np.nonzero(ok)[0], c[ok]), W[ok, k])
                Do = D
                if (n["name"], pi) in oprims:
                    Go_, po, jno = oprims[(n["name"], pi)]
                    Jo, Wo = _weights(Go_, po["attributes"])
                    if len(Jo) == len(X):
                        Do = np.zeros_like(D)
                        for k in range(Jo.shape[1]):
                            c = np.array([col.get(jno[j], -1) for j in Jo[:, k]])
                            ok = c >= 0
                            np.add.at(Do, (np.nonzero(ok)[0], c[ok]), Wo[ok, k])
                F = G.get(p["indices"]).reshape(-1, 3).astype(int) if "indices" in p else np.arange(len(X)).reshape(-1, 3)
                mat = g["materials"][p["material"]]["name"] if "material" in p else ""
                self.prims.append({"node": n["name"], "mesh": n["mesh"], "pi": pi, "X": X, "W": D, "Wo": Do, "F": F,
                                   "mat": mat, "lod0": n["name"] in lod0,
                                   "shadow": "shadow" in m.get("name", "") or mat == "lod_shadow"})
        self.plates = []

    def make_plates(self, side_of):
        """Units (welded parts) to plates; each prim's per-point plate label (-1: rides its own weights)."""
        cfg = self.cfg
        units = []
        for k, pr in enumerate(self.prims):
            pr["lab"] = np.full(len(pr["X"]), -1)
            if not pr["lod0"]:
                continue
            comp = weld_components(pr["X"], pr["F"])
            for c in np.unique(comp):
                idx = np.nonzero(comp == c)[0]
                units.append({"prim": k, "idx": idx, "n": len(idx), "rigid": is_rigid(pr["mat"]),
                              "side": side_of(pr["X"][idx].mean(0)), "wo": pr["Wo"][idx].mean(0)})
        # plates
        cand = [u for u in units if u["rigid"] and (cfg["group"] == "side" or u["n"] >= cfg["plate_min"])]
        # (big soft parts, a leather lining, keep their own weights)
        for u in units:
            if not u["rigid"] and u["n"] >= cfg["plate_min"]:
                u["plate"] = -1
        plates = []
        for u in sorted(cand, key=lambda u: -u["n"]):
            hit = None
            for pi_, p in enumerate(plates):
                if p["side"] != u["side"]:
                    continue
                if cfg["group"] == "side" or np.abs(p["wo"] - u["wo"]).sum() < cfg["tol"]:
                    hit = pi_
                    break
            if hit is None:
                plates.append({"side": u["side"], "units": [], "wo": u["wo"]})
                hit = len(plates) - 1
            plates[hit]["units"].append(u)
            u["plate"] = hit
        # the rest ride the nearest plate within attach_mm (ties within 1 mm: the closest original set)
        pts = [np.vstack([self.prims[u["prim"]]["X"][u["idx"]] for u in p["units"]]) for p in plates]
        trees = [cKDTree(x) for x in pts]
        for u in units:
            if "plate" in u:
                continue
            X = self.prims[u["prim"]]["X"][u["idx"]]
            d = np.array([t.query(X)[0].min() for t in trees])
            ok = np.nonzero(d <= max(d.min() + 0.001, 0))[0]
            if d.min() > cfg["attach_mm"] / 1000:
                u["plate"] = -1
                continue
            u["plate"] = int(ok[np.argmin([np.abs(plates[i]["wo"] - u["wo"]).sum() for i in ok])])
            plates[u["plate"]]["units"].append(u)
        for u in units:
            self.prims[u["prim"]]["lab"][u["idx"]] = u["plate"]
        # LOD and shadow meshes: their nearest LOD0 plate point (LOD parts: a part's majority)
        lp = np.vstack([pr["X"][pr["lab"] >= 0] for pr in self.prims if pr["lod0"]]) if plates else np.zeros((0, 3))
        ll = np.concatenate([pr["lab"][pr["lab"] >= 0] for pr in self.prims if pr["lod0"]]) if plates else np.zeros(0, int)
        if len(lp):
            tl = cKDTree(lp)
            for pr in self.prims:
                if pr["lod0"]:
                    continue
                d, j = tl.query(pr["X"])
                lab = np.where(d < 0.01, ll[j], -1)
                if not pr["shadow"]:
                    comp = weld_components(pr["X"], pr["F"])
                    for c in np.unique(comp):
                        s = comp == c
                        v = lab[s][lab[s] >= 0]
                        lab[s] = np.bincount(v).argmax() if len(v) else -1
                pr["lab"] = lab
        self.plates = plates
        for i, p in enumerate(plates):
            sel = [(pr, pr["lab"] == i) for pr in self.prims if pr["lod0"]]
            p["n"] = int(sum(s.sum() for _, s in sel))
            p["w0"] = sum(pr["W"][s].sum(0) for pr, s in sel) / max(p["n"], 1)
            p["sets0"] = len({tuple(np.round(w, 3)) for pr, s in sel for w in pr["W"][s]})
        return plates


# --------------------------------------------------------------- the fitter --
class Fit:
    def __init__(self, argv):
        def opt(name, default):
            return argv[argv.index(name) + 1] if name in argv else default
        self.ids = opt("--pieces", ",".join(CONF["pieces"])).split(",")
        self.clips = opt("--clips", ",".join(wc.CLIPS)).split(",")
        self.step = int(opt("--step", "2"))
        self.out = opt("--out", os.path.join(os.environ.get("TEMP", "."), "plate_fit"))
        self.write = "--write" in argv
        self.shapes = opt("--shapes", None)
        self.orig = dict(kv.split("=", 1) for kv in opt("--orig", "").split(",") if "=" in kv)
        os.makedirs(self.out, exist_ok=True)

    def cfg(self, pid):
        c = dict(CONF["defaults"])
        c.update(CONF["pieces"].get(pid, {}))
        if self.shapes:
            c["shapes"] = self.shapes
        return c

    # ---- setup: her body, the pieces, the tests (as wearcheck makes them)
    def setup(self):
        t0 = time.time()
        rows = wc.catalogue(None)
        byid = {r["id"]: r for r in rows}
        self.byid = byid
        targets = [byid[i] for i in self.ids if i in byid]
        unders = [r for r in rows if r["slot"] in CONF["under_slots"]]
        sk = skin.Skeleton.load(skin.SKELETONS / "heroine_skeleton.json")
        files = [(skin.PEOPLE / "heroine.glb", lambda n: n == "Heroine", "skin"),
                 (skin.PEOPLE / "heroine.glb", lambda n: n == "HeroineHead", "head")]
        owner = {}
        use = targets + [r for r in unders if r not in targets]
        for path in sorted({r["path"] for r in use}):
            names = {m: r["id"] for r in use if r["path"] == path for m in r["meshes"]}
            owner.update(names)
            files.append((skin.Path(path), lambda n, s=frozenset(names): n in s, "garment"))
        body = skin.Body(sk, files, skin.Jiggle(sk, 1, 1), label="her", helpers=True)
        self.body, self.sk = body, body.sk
        names = list(body.sk.names)
        self.names = names
        pid = np.array([owner.get(p, "") for p in body.piece])
        P0 = body.P
        isk = np.nonzero(body.kind == "skin")[0]
        ish = np.nonzero(body.kind != "garment")[0]
        loc = np.full(len(P0), -1)
        loc[ish] = np.arange(len(ish))
        self.TS = loc[body.T[(body.kind[body.T] != "garment").all(1)]]
        N0 = np.zeros_like(P0)
        N0[ish] = skin._normals(P0[ish], self.TS)
        self.P0, self.N0, self.isk, self.ish = P0, N0, isk, ish
        kd_sh = cKDTree(P0[ish])
        tri_piece = pid[body.T[:, 0]]
        grid = 0.0025
        # (the body's vertex index of each piece prim's points: a node's points are contiguous, its prims in order)
        first = {}
        for i, nm in enumerate(body.piece):
            first.setdefault(nm, i)
        side_of = lambda c: "l" if c[0] > 0 else "r"
        self.pieces = {}
        for r in targets:
            pc = Piece(r, names, self.cfg(r["id"]), self.orig.get(r["id"]))
            pc.make_plates(side_of)
            off = {}
            for pr in pc.prims:
                if pr["lod0"]:
                    o = off.get(pr["node"], first[pr["node"]])
                    pr["bidx"] = np.arange(o, o + len(pr["X"]))
                    off[pr["node"]] = o + len(pr["X"])
                    assert np.abs(P0[pr["bidx"]] - pr["X"]).max() < 1e-5, pr["node"]
            lab = np.full(len(P0), -1)
            for pr in pc.prims:
                if pr["lod0"]:
                    lab[pr["bidx"]] = pr["lab"]
            pc.lab = lab
            pc.v = np.nonzero(pid == r["id"])[0]
            pc.T = body.T[tri_piece == r["id"]]
            pc.Tlab = lab[pc.T[:, 0]]
            self.pieces[r["id"]] = pc
            for i, p in enumerate(pc.plates):
                bones = [b.replace("{s}", p["side"]) for b in CONF["bones"]]
                bones = [b for b in bones if b in body.sk.index]
                bones += [names[j] for j in np.nonzero(p["w0"] >= 0.02)[0] if names[j] not in bones]
                p["cand"] = np.array([body.sk.index[b] for b in bones])
                say("%s plate %d: side %s, %d pts (%d parts, %d weight sets now), w0 %s" % (
                    r["id"], i, p["side"], p["n"], len(p["units"]), p["sets0"],
                    " ".join("%s:%.2f" % (names[j], p["w0"][j]) for j in np.argsort(-p["w0"])[:6] if p["w0"][j] > 0.005)))
            nfree = sum(int((pr["lab"] < 0).sum()) for pr in pc.prims if pr["lod0"])
            say("%s: %d plates, %d LOD0 points ride their own weights" % (r["id"], len(pc.plates), nfree))

        # the tests
        self.tests = []

        def footprint(O, D, T):
            kd = cKDTree(P0[T].mean(1))
            kdv = cKDTree(P0[np.unique(T)])
            d0, _ = kdv.query(O, distance_upper_bound=wc.REACH + 0.01)
            keep = np.nonzero(np.isfinite(d0))[0]
            res = {"idx": [], "gap": [], "out": [], "hit": [], "bary": [], "cand": []}
            for a in range(0, len(keep), 1500):
                ii = keep[a:a + 1500]
                _, ci = kd.query(O[ii], k=min(wc.K0, len(T)))
                ci = ci.reshape(len(ii), -1)
                t, fa, u, v = wc.cast(O[ii], D[ii], P0[T[ci]])
                gg, j, go = wc.signed_gap(t, fa, wc.REACH)
                ok = np.isfinite(gg)
                if not ok.any():
                    continue
                rr = np.nonzero(ok)[0]
                hit = ci[rr, j[rr]]
                hp = O[ii[rr]] + D[ii[rr]] * gg[rr, None]
                _, cand = kd.query(hp, k=min(wc.K, len(T)))
                res["idx"].append(ii[rr])
                res["gap"].append(gg[rr])
                res["out"].append(go[rr])
                res["hit"].append(hit)
                res["bary"].append(np.c_[1 - u[rr, j[rr]] - v[rr, j[rr]], u[rr, j[rr]], v[rr, j[rr]]])
                res["cand"].append(cand.reshape(len(rr), -1))
            if not res["idx"]:
                return None
            return {k: np.concatenate(v) for k, v in res.items()}

        def add(kind, A, pc, O, D, pts, dirs, T, Tlab, hold, extra=None):
            fp = footprint(O, D, T)
            if fp is None:
                return
            x = {"kind": kind, "A": A, "B": pc.id, "pc": pc, "fp": fp, "pts": pts[fp["idx"]], "dir": dirs[fp["idx"]],
                 "T": T, "Tlab": Tlab, "hold": hold, "hitv": T[fp["hit"]], "candv": T[fp["cand"]],
                 "Sv": T[np.unique(fp["cand"])], "rest_gap": fp["gap"]}
            if extra:
                x.update({k: v[fp["idx"]] for k, v in extra.items()})
            self.tests.append(x)

        for r in targets:
            pc = self.pieces[r["id"]]
            # her skin, tucked by the piece's record
            tk = np.zeros(len(P0))
            tk[isk], gone = wc.tuck_of(r["tuck_path"], P0[isk])
            sv = isk[~gone]
            O = P0[sv] - N0[sv] * tk[sv, None]
            add("skin", "skin", pc, O + N0[sv] * 1e-5, N0[sv], sv, sv, pc.T, pc.Tlab, wc.hold_key(r),
                {"tuck": tk[sv]})
            # the tops of other sources under it
            for a in unders:
                if a["source"] == r["source"] or a["slot"] == r["slot"] or r["slot"] in a["covers"] or a["slot"] in r["covers"]:
                    continue
                if not a["layer"] < r["layer"]:
                    continue
                v = np.nonzero(pid == a["id"])[0]
                if not len(v):
                    continue
                _, fi = np.unique(np.floor(P0[v] / grid).astype(np.int64), axis=0, return_index=True)
                smp = v[np.sort(fi)]
                _, near = kd_sh.query(P0[smp])
                add("top", a["id"], pc, P0[smp], N0[ish[near]], smp, ish[near], pc.T, pc.Tlab, wc.hold_key(a, r))
            # each plate's points under its neighbour plates (a lame under the one above)
            for j in range(len(pc.plates)):
                v = pc.v[pc.lab[pc.v] == j]
                _, fi = np.unique(np.floor(P0[v] / grid).astype(np.int64), axis=0, return_index=True)
                smp = v[np.sort(fi)]
                _, near = kd_sh.query(P0[smp])
                m = (pc.Tlab >= 0) & (pc.Tlab != j)
                if not m.any():
                    continue
                n0 = len(self.tests)
                add("lame", "plate%d" % j, pc, P0[smp], N0[ish[near]], smp, ish[near], pc.T[m], pc.Tlab[m],
                    wc.hold_key(r))
                if len(self.tests) > n0:
                    x = self.tests[-1]
                    ok = (x["rest_gap"] > -0.0005) & (x["rest_gap"] < 0.008)    # (under it at rest, in its overlap)
                    if not ok.any():
                        self.tests.pop()
                        continue
                    for k in ("pts", "dir", "rest_gap", "hitv", "candv"):
                        x[k] = x[k][ok]
                    for k in list(x["fp"]):
                        x["fp"][k] = x["fp"][k][ok]
                    x["Sv"] = x["T"][np.unique(x["fp"]["cand"])]
                    x["plate_a"] = j
        for x in self.tests:
            x["clear"] = {"skin": x["pc"].cfg["clear_skin_mm"], "top": x["pc"].cfg["clear_top_mm"],
                          "lame": x["pc"].cfg["clear_lame_mm"]}[x["kind"]] / 1000
            if x["kind"] == "lame":
                x["clear_i"] = np.minimum(x["rest_gap"], x["clear"])
            else:
                x["clear_i"] = np.full(len(x["pts"]), x["clear"])
            x["a"] = {"skin": x["pc"].cfg["w_skin"], "top": x["pc"].cfg["w_top"], "lame": x["pc"].cfg["w_lame"]}[x["kind"]]
        say("setup: %d tests (%s) in %.0f s" % (len(self.tests), ", ".join("%s>%s %d" % (x["A"], x["B"], len(x["pts"])) for x in self.tests), time.time() - t0))

    # ---- her bone globals per frame (per hold), cached
    def frames(self):
        self.F = {}
        holds = sorted({x["hold"] for x in self.tests})
        for h in holds:
            path = os.path.join(self.out, "globals_%g_%g_s%d.npz" % (h[0], h[1], self.step))
            key = "|".join(self.clips)
            if os.path.isfile(path):
                z = np.load(path, allow_pickle=True)
                if str(z["key"]) == key:
                    self.F[h] = list(zip(z["clip"], z["frame"], z["G"]))
                    continue
            self.body.jiggle = skin.Jiggle(self.sk, amount=h[0], squash=h[1])
            out = []
            t0 = time.time()
            for c in self.clips:
                fr = self.body.frames(self.body.clip(c))
                for f in range(0, len(fr), self.step):
                    out.append((c, f, fr[f]))
            np.savez(path, key=key, clip=np.array([o[0] for o in out]), frame=np.array([o[1] for o in out]),
                     G=np.array([o[2] for o in out]))
            say("hold %s: %d frames in %.0f s" % (h, len(out), time.time() - t0))
            self.F[h] = out

    # ---- a frame's posed data
    def rest_with_shapes(self, sw, idx, plates_drop):
        P = self.P0[idx].copy()
        for k, w in sw.items():
            d = self.body.corr[k][idx]
            if plates_drop is not None:
                d = np.where(plates_drop[:, None], 0, d)
            P += w * d
        return P

    def eval(self, Wp, collect=False, M=None):
        """Every test over every frame with plate weights Wp {piece: [plates, nS]} (None: the file's own weights):
        min gap and min outer gap per sample; collect: each sample's M worst rows (frame, face, bary, O, D)."""
        body = self.body
        M = M or 6
        for x in self.tests:
            n = len(x["pts"])
            x["min"] = np.full(n, np.inf)
            x["min_out"] = np.full(n, np.inf)
            x["at"] = np.full(n, -1)
            if collect:
                x["rows"] = {"g": np.full((n, M), np.inf), "fr": np.full((n, M), -1), "face": np.zeros((n, M, 3), int),
                             "bary": np.zeros((n, M, 3)), "O": np.zeros((n, M, 3)), "D": np.zeros((n, M, 3))}
        self.frame_S = {}
        self.frame_sw = {}
        for h, frames in self.F.items():
            group = [x for x in self.tests if x["hold"] == h]
            if not group:
                continue
            need = np.unique(np.concatenate([self.ish] + [np.r_[x["pts"], x["hitv"].ravel(), x["candv"].ravel(), x["Sv"].ravel()] for x in group]))
            at = np.full(len(self.P0), -1)
            at[need] = np.arange(len(need))
            sh_local = at[self.ish]
            for fi, (c, f, G) in enumerate(frames):
                S = body.skin_mats(G)
                sw = body.shape_weights(G)
                self.frame_S[(h, fi)] = S
                self.frame_sw[(h, fi)] = sw
                Pp = body.pose(G, need)
                # (plate points through their plate's one matrix)
                for pc in {x["pc"] for x in group}:
                    if Wp is None or pc.id not in Wp:
                        continue
                    v = need[pc.lab[need] >= 0]
                    drop = None
                    if pc.cfg["shapes"] == "drop":
                        drop = np.ones(len(v), bool)
                    X = self.rest_with_shapes(sw, v, drop)
                    Mx = np.einsum("pk,kij->pij", Wp[pc.id], S)       # [plates, 4, 4]
                    L = pc.lab[v]
                    Pp[at[v]] = np.einsum("nij,nj->ni", Mx[L][:, :3, :], np.c_[X, np.ones(len(X))])
                Np = np.zeros_like(Pp)
                Np[sh_local] = skin._normals(Pp[sh_local], self.TS)
                for x in group:
                    O = Pp[at[x["pts"]]]
                    D = Np[at[x["dir"]]]
                    if x["kind"] == "skin":
                        O = O - D * x["tuck"][:, None] + D * 1e-5
                    H = Pp[at[x["hitv"]]]
                    hp = (H * x["fp"]["bary"][:, :, None]).sum(1)
                    fn = np.cross(H[:, 1] - H[:, 0], H[:, 2] - H[:, 0])
                    den = (fn * D).sum(1)
                    g = np.where(np.abs(den) > 1e-14, ((hp - O) * fn).sum(1) / np.where(np.abs(den) > 1e-14, den, 1), np.nan)
                    lat = np.linalg.norm(np.cross(hp - O, D), axis=1)
                    g = np.where((np.abs(g) < wc.REACH_POSED) & (lat < wc.DRIFT), g, np.nan)
                    go = g.copy()
                    face = x["fp"]["hit"].copy()          # (index into x["T"])
                    bary = x["fp"]["bary"].copy()
                    r = np.nonzero(~(g > wc.REFINE))[0]
                    if len(r):
                        t, fa, u, vv = wc.cast(O[r], D[r], Pp[at[x["candv"][r]]])
                        gr, jr, gor = wc.signed_gap(t, fa, wc.REACH_POSED)
                        ok = np.isfinite(gr)
                        rr = r[ok]
                        face[rr] = x["fp"]["cand"][r[ok], jr[ok]]
                        uu, vq = u[ok, jr[ok]], vv[ok, jr[ok]]
                        bary[rr] = np.c_[1 - uu - vq, uu, vq]
                        lost = np.nonzero(~ok)[0]
                        if len(lost):
                            Sv = x["Sv"]
                            kd = cKDTree(Pp[at[Sv]].mean(1))
                            _, ii = kd.query(O[r[lost]], k=min(wc.K0, len(Sv)))
                            ii = ii.reshape(len(lost), -1)
                            t, fa, u, vv = wc.cast(O[r[lost]], D[r[lost]], Pp[at[Sv[ii]]])
                            gl, jl, gol = wc.signed_gap(t, fa, wc.REACH_POSED)
                            gr[lost], gor[lost] = gl, gol
                            okl = np.isfinite(gl)
                            if okl.any() and collect:
                                # (the face in x["T"] terms: Sv rows are T rows)
                                Tix = {tuple(t_): i_ for i_, t_ in enumerate(map(tuple, x["T"]))} if "Tix" not in x else x["Tix"]
                                x["Tix"] = Tix
                                for q in np.nonzero(okl)[0]:
                                    face[r[lost[q]]] = Tix[tuple(Sv[ii[q, jl[q]]])]
                                    uu, vq = u[q, jl[q]], vv[q, jl[q]]
                                    bary[r[lost[q]]] = (1 - uu - vq, uu, vq)
                        g[r], go[r] = gr, gor
                    x["min_out"] = np.minimum(x["min_out"], np.where(np.isfinite(go), go, np.inf))
                    gg = np.where(np.isfinite(g), g, np.inf)
                    nw = gg < x["min"]
                    x["at"][nw] = fi
                    x["min"] = np.minimum(x["min"], gg)
                    if collect:
                        R = x["rows"]
                        # (keep the M lowest gaps per sample, within the row margin of its clearance)
                        cand = np.isfinite(gg) & (gg < x["clear_i"] + x["pc"].cfg["row_margin_mm"] / 1000)
                        worst = R["g"].argmax(1)
                        repl = cand & (gg < R["g"][np.arange(len(gg)), worst])
                        q = np.nonzero(repl)[0]
                        if len(q):
                            w_ = worst[q]
                            R["g"][q, w_] = gg[q]
                            R["fr"][q, w_] = fi
                            R["face"][q, w_] = x["T"][face[q]]
                            R["bary"][q, w_] = bary[q]
                            R["O"][q, w_] = O[q] if x["kind"] != "lame" else self.P0[x["pts"][q]]
                            R["D"][q, w_] = D[q]
                            R.setdefault("h", h)

    def counts(self):
        out = {}
        for x in self.tests:
            k = (x["A"], x["B"])
            out[k] = {"out2": int((x["min_out"] < -0.002).sum()), "in2": int((x["min"] < -0.002).sum()),
                      "in05": int((x["min"] < -0.0005).sum()),
                      "under_clear": int((x["min"] < x["clear_i"]).sum()), "n": len(x["pts"]),
                      "worst_mm": float(-x["min_out"][np.isfinite(x["min_out"])].min() * 1000) if np.isfinite(x["min_out"]).any() else 0}
        return out

    # ---- swim: each plate's points against her nearest skin over her idles
    def swim_data(self):
        self.swim = {}
        body = self.body
        idles = [c for c in CONF["swim_clips"] if c in self.clips]
        h = wc.hold_key({"slot": "pauldrons"})
        frames = [(fi, c) for fi, (c, f, G) in enumerate(self.F[h]) if c in idles]
        kd = cKDTree(self.P0[self.isk])
        for pid, pc in self.pieces.items():
            for i, p in enumerate(pc.plates):
                v = pc.v[pc.lab[pc.v] == i]
                if not len(v):
                    continue
                # (up to 16 points spread over the plate: farthest-point picks)
                pick = [v[np.argmin(np.abs(self.P0[v, 1] - self.P0[v, 1].max()))]]
                d = np.linalg.norm(self.P0[v] - self.P0[pick[0]], axis=1)
                for _ in range(15):
                    pick.append(v[d.argmax()])
                    d = np.minimum(d, np.linalg.norm(self.P0[v] - self.P0[pick[-1]], axis=1))
                pick = np.array(pick)
                _, an = kd.query(self.P0[pick])
                anc = self.isk[an]
                rec = {"pts": pick, "anc": anc, "fr": [], "clip": [], "A": [], "own": []}
                for fi, c in frames:
                    G = self.F[h][fi][2]
                    Pp = body.pose(G, np.r_[anc, pick])
                    rec["fr"].append(fi)
                    rec["clip"].append(c)
                    rec["A"].append(Pp[:len(anc)])
                    rec["own"].append(Pp[len(anc):])
                for k in ("A", "own"):
                    rec[k] = np.array(rec[k])
                rec["clip"] = np.array(rec["clip"])
                dev0 = self.devs(rec["own"] - rec["A"], rec["clip"])
                rec["dev0"] = dev0
                rec["bound"] = np.maximum(np.abs(dev0).max(0), pc.cfg["swim_floor_mm"] / 1000)     # [pts, 3]
                self.swim[(pid, i)] = rec
        self.swim_h = h

    @staticmethod
    def devs(o, clip):
        """o [frames, pts, 3] offsets: each frame's off its clip's mean."""
        d = np.zeros_like(o)
        for c in np.unique(clip):
            s = clip == c
            d[s] = o[s] - o[s].mean(0)
        return d

    def swim_of(self, pid, i, w):
        rec = self.swim[(pid, i)]
        h = self.swim_h
        drop = self.pieces[pid].cfg["shapes"] == "drop"
        own = []
        for fi in rec["fr"]:
            S = self.frame_S[(h, fi)]
            X = self.P0[rec["pts"]] if drop else self.rest_with_shapes(self.frame_sw[(h, fi)], rec["pts"], None)
            Mx = np.einsum("k,kij->ij", w, S)
            own.append(np.c_[X, np.ones(len(X))] @ Mx[:3].T)
        return self.devs(np.array(own) - rec["A"], rec["clip"])

    # ---- the LP
    def solve_piece(self, pid, W_now):
        pc = self.pieces[pid]
        cfg = pc.cfg
        plates = pc.plates
        drop = cfg["shapes"] == "drop"
        # variables: each plate's candidate weights | t per sample with rows | |w - w0| aux | swim slack per plate
        var = [(i, int(k)) for i, p in enumerate(plates) for k in p["cand"]]
        vix = {v: j for j, v in enumerate(var)}
        nW = len(var)
        rows, cols, vals, rhs = [], [], [], []
        cost_t = []
        nt = 0
        Mpl = {}
        for x in self.tests:
            if x["B"] != pid or "rows" not in x or x["rows"].get("h") is None:
                continue
            R = x["rows"]
            h = R["h"]
            ok = R["fr"] >= 0
            samp = np.nonzero(ok.any(1))[0]
            if not len(samp):
                continue
            si, mi = np.nonzero(ok[samp])
            fr = R["fr"][samp][si, mi]
            face = R["face"][samp][si, mi]
            bary = R["bary"][samp][si, mi]
            O = R["O"][samp][si, mi]
            Dv = R["D"][samp][si, mi]
            lab = pc.lab[face[:, 0]]
            Xf = self.P0[face].copy()                                              # [r, 3, 3]
            if not drop:
                for j_, f_ in enumerate(fr):
                    for k, w in self.frame_sw[(h, f_)].items():
                        Xf[j_] += w * self.body.corr[k][face[j_]]
            Xh = np.concatenate([Xf, np.ones((len(fr), 3, 1))], 2)                 # [r, 3, 4]
            for f_ in np.unique(fr):
                if (h, f_) not in Mpl:
                    Mpl[(h, f_)] = np.einsum("pk,kij->pij", W_now, self.frame_S[(h, f_)])
            Mr = np.array([Mpl[(h, f_)][max(l_, 0)] for f_, l_ in zip(fr, lab)])     # [r, 4, 4]
            Hp = np.einsum("rij,rvj->rvi", Mr[:, :3], Xh)
            nrm = np.cross(Hp[:, 1] - Hp[:, 0], Hp[:, 2] - Hp[:, 0])
            nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-12)
            den = (nrm * Dv).sum(1)
            good = (np.abs(den) > 0.2) & (lab >= 0)
            if x["kind"] == "lame":
                good &= lab != x["plate_a"]
            xh = (Xh * bary[:, :, None]).sum(1)                                    # [r, 4]
            tix = np.full(len(samp), -1)
            used = np.unique(si[good])
            tix[used] = nt + np.arange(len(used))
            nt += len(used)
            cost_t.append(np.full(len(used), x["a"]))
            for q in np.nonzero(good)[0]:
                p = lab[q]
                K = plates[p]["cand"]
                S = self.frame_S[(h, fr[q])]
                a_k = (S[K][:, :3] @ xh[q]) @ nrm[q] / den[q] * 1000
                r_ = len(rhs)
                rows += [r_] * (len(K) + 1)
                cols += [vix[(p, int(k))] for k in K] + [nW + tix[si[q]]]
                vals += list(-a_k) + [-1.0]
                if x["kind"] == "lame":
                    pa = x["plate_a"]
                    Ka = plates[pa]["cand"]
                    b_k = -(S[Ka][:, :3] @ np.r_[O[q], 1.0]) @ nrm[q] / den[q] * 1000
                    rows += [r_] * len(Ka)
                    cols += [vix[(pa, int(k))] for k in Ka]
                    vals += list(-b_k)
                    const = 0.0
                else:
                    const = -(O[q] @ nrm[q]) / den[q] * 1000
                rhs.append(const - x["clear_i"][samp[si[q]]] * 1000)
        nrow_gap = len(rhs)
        nU = nW
        nP = len(plates)
        # swim: |dev_f(w)| <= bound + slack_p per plate point, coordinate, frame (her idles)
        h = self.swim_h
        for i, p in enumerate(plates):
            rec = self.swim.get((pid, i))
            if rec is None:
                continue
            K = p["cand"]
            Xh = np.c_[self.P0[rec["pts"]], np.ones(len(rec["pts"]))]
            SX = np.array([np.einsum("kij,nj->kni", self.frame_S[(h, fi)][K][:, :3], Xh) for fi in rec["fr"]])  # [F, K, n, 3]
            Ad = self.devs(rec["A"], rec["clip"])
            SXd = np.zeros_like(SX)
            for c in np.unique(rec["clip"]):
                s = rec["clip"] == c
                SXd[s] = SX[s] - SX[s].mean(0)
            bnd = rec["bound"] * 1000
            for f_ in range(0, len(rec["fr"]), 2):
                co = SXd[f_] * 1000                                   # [K, n, 3]
                a0 = Ad[f_] * 1000                                    # [n, 3]
                for n_ in range(co.shape[1]):
                    for d_ in range(3):
                        for sgn in (1, -1):
                            r_ = len(rhs)
                            rows += [r_] * (len(K) + 1)
                            cols += [vix[(i, int(k))] for k in K] + [nW + nt + nU + i]
                            vals += list(sgn * co[:, n_, d_]) + [-1.0]
                            rhs.append(bnd[n_, d_] + sgn * a0[n_, d_])
        nrow_swim = len(rhs) - nrow_gap
        for j, (i, k) in enumerate(var):
            w0 = plates[i]["w0"][k]
            for sgn in (1, -1):
                r_ = len(rhs)
                rows += [r_, r_]
                cols += [j, nW + nt + j]
                vals += [sgn, -1.0]
                rhs.append(sgn * w0)
        nV = nW + nt + nU + nP
        A = sparse.csr_matrix((vals, (rows, cols)), shape=(len(rhs), nV))
        Aeq = sparse.csr_matrix((np.ones(nW), ([i for i, _ in var], np.arange(nW))), shape=(nP, nV))
        c = np.zeros(nV)
        if cost_t:
            c[nW:nW + nt] = np.concatenate(cost_t)
        c[nW + nt:nW + nt + nU] = cfg["reg_mm"] * np.array([plates[i]["n"] for i, _ in var]) / 100.0
        c[nW + nt + nU:] = cfg["swim_cost"] * np.array([p["n"] for p in plates]) / 100.0
        bounds = [(0, 0) if k in plates[i].get("banned", ()) else (0, 1) for i, k in var] + [(0, None)] * (nt + nU + nP)
        t0 = time.time()
        res = linprog(c, A_ub=A, b_ub=np.array(rhs), A_eq=Aeq, b_eq=np.ones(nP), bounds=bounds, method="highs")
        if res.status != 0:
            say("%s LP: %s (%d gap rows, %d swim rows); the last weights kept" % (pid, res.message, nrow_gap, nrow_swim))
            return W_now
        Wn = np.zeros_like(W_now)
        for j, (i, k) in enumerate(var):
            Wn[i, k] = max(res.x[j], 0)
        Wn[Wn < 1e-4] = 0
        Wn /= Wn.sum(1, keepdims=True)
        say("%s LP: %d vars, %d gap rows, %d swim rows, objective %.1f, swim slack %s mm (%.1f s)" % (
            pid, nV, nrow_gap, nrow_swim, res.fun, np.round(res.x[nW + nt + nU:], 2).tolist(), time.time() - t0))
        return Wn

    def run(self):
        self.setup()
        self.frames()
        nS = None
        # the file's own weights: the baseline counts and rows
        self.eval(None, collect=True, M=max(self.cfg(p)["rows_per_sample"] for p in self.pieces))
        base = self.counts()
        nS = len(next(iter(self.frame_S.values())))
        self.swim_data()
        W = {pid: np.array([p["w0"][:nS] if len(p["w0"]) >= nS else np.r_[p["w0"], np.zeros(nS - len(p["w0"]))] for p in pc.plates])
             for pid, pc in self.pieces.items()}
        # (w0 as one set: the plate's mean, its own count)
        self.eval(W, collect=True)
        mean0 = self.counts()
        hist = [("file", base), ("w0", mean0)]
        best = {pid: (W[pid].copy(), self.score(mean0, pid)) for pid in self.pieces}
        rounds = max(self.cfg(p)["rounds"] for p in self.pieces)
        for rd in range(rounds):
            for pid in self.pieces:
                Wn = self.solve_piece(pid, W[pid])
                W[pid] = self.cap(pid, Wn)
            self.eval(W, collect=True)
            cn = self.counts()
            hist.append(("round%d" % (rd + 1), cn))
            for pid in self.pieces:
                s = self.score(cn, pid)
                if s < best[pid][1]:
                    best[pid] = (W[pid].copy(), s)
            self.report(cn, base, "round %d" % (rd + 1))
        Wb = {pid: best[pid][0] for pid in self.pieces}
        self.eval(Wb)
        fin = self.counts()
        self.report(fin, base, "best")
        self.swim_report(Wb)
        json.dump({"pieces": {pid: [{"side": p["side"], "n": p["n"], "parts": len(p["units"]), "sets_before": p["sets0"],
                                    "w0": {self.names[j]: round(float(p["w0"][j]), 4) for j in np.nonzero(p["w0"] > 1e-3)[0]},
                                    "w": {self.names[j]: round(float(Wb[pid][i][j]), 4) for j in np.nonzero(Wb[pid][i] > 1e-4)[0]}}
                                   for i, p in enumerate(pc.plates)] for pid, pc in self.pieces.items()},
                   "counts": {name: {"%s>%s" % k: v for k, v in c.items()} for name, c in hist + [("best", fin)]}},
                  open(os.path.join(self.out, "plate_fit.json"), "w"), indent=1)
        if self.write:
            for pid, pc in self.pieces.items():
                self.write_piece(pc, Wb[pid])
        return Wb

    def score(self, cn, pid):
        """OUT>2 over the piece's skin and top tests, plus the lame poke-throughs past 0.5 mm."""
        s = 0
        for x in self.tests:
            if x["B"] != pid:
                continue
            if x["kind"] == "lame":
                s += int((x["min"] < -0.0005).sum())
            else:
                s += int((x["min_out"] < -0.002).sum())
        return s

    def cap(self, pid, Wn):
        pc = self.pieces[pid]
        mx = pc.cfg["max_infl"]
        for i, p in enumerate(pc.plates):
            nz = np.nonzero(Wn[i] > 0)[0]
            if len(nz) > mx:
                keep = nz[np.argsort(-Wn[i][nz])[:mx]]
                p["banned"] = set(p.get("banned", set())) | set(int(k) for k in nz if k not in keep)
                Wn[i][[k for k in nz if k not in keep]] = 0
                Wn[i] /= Wn[i].sum()
        return Wn

    def report(self, cn, base, label):
        for x in self.tests:
            k = (x["A"], x["B"])
            if x["kind"] == "lame":
                say("%-6s %-24s lame %-7s under its neighbours: %d of %d past 0.5 mm (file %d)" % (
                    label, x["B"], x["A"], cn[k]["in05"], len(x["pts"]), base[k]["in05"]))
            else:
                say("%-6s %-24s <- %-22s OUT>2 %5d (file %5d), inside clearance %5d of %5d" % (
                    label, x["B"], x["A"], cn[k]["out2"], base[k]["out2"], cn[k]["under_clear"], cn[k]["n"]))

    def swim_report(self, Wb):
        for (pid, i), rec in self.swim.items():
            d0 = np.linalg.norm(rec["dev0"], axis=2)
            d1 = np.linalg.norm(self.swim_of(pid, i, Wb[pid][i]), axis=2)
            say("swim %s plate %d: idle slide vs her skin max %.2f mm p95 %.2f (the file's weights: max %.2f p95 %.2f)" % (
                pid, i, d1.max() * 1000, np.percentile(d1, 95) * 1000, d0.max() * 1000, np.percentile(d0, 95) * 1000))

    # ---- writing
    def write_piece(self, pc, Wb):
        G = _Gl(pc.path)
        g = G.g
        names = self.names
        drop = pc.cfg["shapes"] == "drop"
        nmeshes = set()
        for pr in pc.prims:
            lab = pr["lab"]
            if not (lab >= 0).any():
                continue
            node = next(n for n in g["nodes"] if n.get("name") == pr["node"] and "mesh" in n)
            m = g["meshes"][node["mesh"]]
            p = m["primitives"][pr["pi"]]
            a = p["attributes"]
            sk = g["skins"][node["skin"]]
            jn = [g["nodes"][j]["name"] for j in sk["joints"]]
            jm = {nm: k for k, nm in enumerate(jn)}
            J, W = _weights(G, a)
            nw = 8 if "JOINTS_1" in a else 4
            J = np.pad(J, ((0, 0), (0, nw - J.shape[1])))[:, :nw]
            W = np.pad(W, ((0, 0), (0, nw - W.shape[1])))[:, :nw]
            for i in np.unique(lab[lab >= 0]):
                nz = np.nonzero(Wb[i] > 0)[0]
                nz = nz[np.argsort(-Wb[i][nz])]
                if len(nz) > nw:
                    raise RuntimeError("%s plate %d: %d bones, the file carries %d a point" % (pc.id, i, len(nz), nw))
                miss = [names[k] for k in nz if names[k] not in jm]
                if miss:
                    raise RuntimeError("%s: the skin lacks %s" % (pc.id, miss))
                s = lab == i
                J[s] = 0
                W[s] = 0
                J[s, :len(nz)] = [jm[names[k]] for k in nz]
                W[s, :len(nz)] = Wb[i][nz]
            jt = g["accessors"][a["JOINTS_0"]]["componentType"]
            jd = np.uint8 if jt == 5121 else np.uint16
            a["JOINTS_0"] = _add_acc(G, J[:, :4].astype(jd), jt, "VEC4")
            a["WEIGHTS_0"] = _add_acc(G, W[:, :4].astype(np.float32), 5126, "VEC4")
            if nw == 8:
                a["JOINTS_1"] = _add_acc(G, J[:, 4:].astype(jd), jt, "VEC4")
                a["WEIGHTS_1"] = _add_acc(G, W[:, 4:].astype(np.float32), 5126, "VEC4")
            if drop and p.get("targets"):
                for t in p["targets"]:
                    for key in ("POSITION", "NORMAL"):
                        if key not in t:
                            continue
                        Dv = sparse_read(G, t[key])
                        Dv[lab >= 0] = 0
                        ip = np.nonzero(np.abs(Dv).max(1) > 0)[0]
                        t[key] = _sparse_g(G, len(Dv), ip, Dv[ip])
            nmeshes.add(m.get("name"))
        ex = g.setdefault("asset", {}).setdefault("extras", {})
        bsha = __import__("hashlib").sha1(open(skin.PEOPLE / "heroine.glb", "rb").read()).hexdigest()
        ex[MARK] = {"body": bsha, "plates": len(pc.plates), "shapes": pc.cfg["shapes"]}
        g["buffers"][0]["byteLength"] = len(G.buf) - G.b0
        G.save()
        say("%s written: %d plates over %s" % (pc.id, len(pc.plates), ", ".join(sorted(nmeshes))))


def main(argv):
    Fit(argv).run()


if __name__ == "__main__":
    main(sys.argv[1:])
