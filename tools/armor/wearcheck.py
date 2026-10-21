"""Mixed-look clipping (armor 7): every pair of her slot pieces from different sources worn together (an inner piece A
under an outer piece B, Rpg/Wear.cs Look), and each piece over her tucked skin, through her core clips, posed as the
game poses them (tools/anim/skin.py: Godot's skinning with her helpers and correctives, her springs at the worn top's
hold, else amount 1 squash 1 as HerWear.Apply).

A is sampled on a GRID mm voxel grid (one vertex per voxel, so counts read as area: n x GRID^2 mm^2). Each sample casts
a ray out along her posed surface normal (the nearest point of her body or head). B's faces are oriented (her pieces are
closed shells): a face whose normal opposes the ray is an entry (inner) face. The signed gap is the distance out to B's
inner face; negative when A is past it (inside B's shell or out through it): A shows through B.

Footprint: A's samples whose ray meets B within REACH mm at rest (either side); pairs with none are pruned (never
touch). Per frame the gap is tracked on B's face hit at rest (its posed plane, while that hit stays within 4 mm of the
ray) and, where that reads under 3 mm or has drifted,
re-cast against the K B faces nearest the rest hit (or, where that misses because B slid, B's faces over the whole
footprint nearest the sample; none within reach: B is off it, no contact). Her body is posed once per frame for every pair (cached per hold).

Pairs: layer(A) < layer(B), or equal layers in the order whose rest median gap is larger; never the same slot, nor a
pair one of whose covers hides the other (Wear.cs Look). Pieces of one source (an outfit, or one new piece) are not mixed
pairs: --same adds them as a control. Skin: her skin tucked by the piece's own armor_tuck record (10 mm x the mark, all
of it past 0.973, eight bits, and none of her drawn where marked 0.995 and over, as her shader reads it) vs the piece,
per piece (a control).

Garment tuck (--garment-tuck, as HerWear draws it: Rpg/GarmentTuck.cs, docs/armor/PIECE_SCHEMA.md "Garment tuck"):
a mixed pair's inner piece is the earlier in the slot order (tools/armor/slot_map.json "order", or --order a,b,..),
laid down onto her skin under the outer piece's footprint (max of its armor_tuck and armor_cover records, tools/armor/
cover.py), spread past its edge over --tuck-r mm (falling off to 0); its triangles all past 0.995 removed (their samples dropped). --tuck-off: that pairing
without the tuck (the baseline).

    python tools/armor/wearcheck.py [--pieces a,b,..] [--clips c1,c2,..] [--step 2] [--same] [--grid 2.5]
                                    [--out <dir>] [--no-skin] [--garment-tuck [--tuck-r 20] [--tuck-off] [--order ..]]
Writes <out>/matrix.json and <out>/table.txt (worst first).
"""
import json
import os
import struct
import sys
import time

import numpy as np
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
MAIN = os.path.abspath(os.path.join(ROOT, "..", "..", ".."))     # (the main checkout: the built clips, tools/anim/out)
sys.path.insert(0, os.path.join(ROOT, "tools", "anim"))
os.environ.setdefault("ANIM_OUT", os.path.join(MAIN if os.path.isdir(os.path.join(MAIN, "tools", "anim", "out")) else ROOT, "tools", "anim", "out"))
import skin  # noqa: E402

CLIPS = ("idle_warden", "idle_warden_town", "run_warden", "run_warden_town", "sword_heavy", "sword_fore", "idle_reaver",
         "run_reaver_axes", "axe_heavy", "idle_arcanist", "run_arcanist_wand", "cast_flick", "idle_stalker", "run_stalker",
         "crossbow_shoot", "daggers_heavy")
INDEXES = (os.path.join(ROOT, "godot", "art", "people", "armor_index.json"),
           os.path.join(ROOT, "godot", "art", "armor", "armor_index.json"))
SKIP_SLOTS = ("ink", "cloak")
REACH = 0.025      # rest footprint, m
REACH_POSED = 0.030
K = 48             # B faces kept per sample for the posed re-cast
K0 = 160           # B faces tried per sample at rest
REFINE = 0.003     # tracked gap under this: re-cast
DRIFT = 0.004      # the rest hit this far off the ray: re-cast
DEFAULT_HOLD = {"amount": 1, "squash": 1}


# ----------------------------------------------------------------- geometry --
def _cross(a, b):
    """np.cross over the last axis, without its axis shuffling (the hot loop)."""
    a0, a1, a2 = a[..., 0], a[..., 1], a[..., 2]
    b0, b1, b2 = b[..., 0], b[..., 1], b[..., 2]
    return np.stack((a1 * b2 - a2 * b1, a2 * b0 - a0 * b2, a0 * b1 - a1 * b0), -1)


def cast(O, D, V):
    """Rays O, D [n, 3] against per-ray triangle sets V [n, k, 3, 3] (nan rows: none): t [n, k] (nan: miss) and each
    face's facing, sign(n_face . d) (-1: an entry face)."""
    v0, e1, e2 = V[:, :, 0], V[:, :, 1] - V[:, :, 0], V[:, :, 2] - V[:, :, 0]
    d = D[:, None]
    p = _cross(np.broadcast_to(d, e2.shape), e2)
    det = (e1 * p).sum(2)
    ok = np.abs(det) > 1e-14
    inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0)
    s = O[:, None] - v0
    u = (s * p).sum(2) * inv
    q = _cross(s, e1)
    v = (d * q).sum(2) * inv
    t = (e2 * q).sum(2) * inv
    hit = ok & (u >= -1e-6) & (v >= -1e-6) & (u + v <= 1 + 1e-6)
    facing = np.sign((_cross(e1, e2) * d).sum(2))
    return np.where(hit, t, np.nan), facing, u, v


def signed_gap(t, facing, reach):
    """Per ray: the gap out to B's inner face (negative: past it), the column used, and the gap out to B's outer face
    (negative: A out through B where it shows; inside B's shell it is hidden), nan if none within reach."""
    t = np.where(np.abs(t) < reach, t, np.nan)
    n = len(t)
    rows = np.arange(n)
    fw = np.where(t >= 0, t, np.inf)
    jf = fw.argmin(1)
    tf = fw[rows, jf]
    sf = facing[rows, jf]
    bi = np.where((t < 0) & (facing < 0), t, -np.inf)
    jbi = bi.argmax(1)
    tbi = bi[rows, jbi]
    ba = np.where(t < 0, t, -np.inf)
    jba = ba.argmax(1)
    tba = ba[rows, jba]
    hf, hbi, hba = np.isfinite(tf), np.isfinite(tbi), np.isfinite(tba)
    g = np.full(n, np.nan)
    j = np.zeros(n, int)
    c1 = hf & (sf < 0)
    c2 = ~c1 & hbi
    c3 = ~c1 & ~c2 & hf
    c4 = ~c1 & ~c2 & ~c3 & hba
    for c, gg, jj in ((c1, tf, jf), (c2, tbi, jbi), (c3, tf, jf), (c4, tba, jba)):
        g[c], j[c] = gg[c], jj[c]
    fx = np.where((t >= 0) & (facing > 0), t, np.inf).min(1)
    bx = np.where((t < 0) & (facing > 0), t, -np.inf).max(1)
    gout = np.where(np.isfinite(fx), fx, np.where(np.isfinite(bx), bx, np.nan))
    # (B's outer face is never nearer than its inner one: overlapping shells read as their inner face)
    gout = np.where(np.isfinite(g), np.where(np.isfinite(gout), np.maximum(gout, g), g), np.nan)
    return g, j, gout


# ------------------------------------------------------------------ catalogue --
def catalogue(only=None):
    rows = []
    for path in INDEXES:
        base = os.path.dirname(path)
        for r in json.load(open(path, encoding="utf-8")):
            if r["slot"] in SKIP_SLOTS or (only and r["id"] not in only):
                continue
            r = dict(r)
            r["covers"] = r.get("covers") or [r["slot"]]
            r["source"] = r.get("outfit") or r["id"]
            if r.get("file"):
                r["path"] = os.path.join(base, r["file"].replace("res://art/armor/", ""))
            else:
                r["path"] = os.path.join(base, f"heroine_outfit_{r['outfit']}.gltf")
            r["tuck_path"] = os.path.join(base, r["tuck"])
            rows.append(r)
    return rows


def tuck_of(path, P):
    """Her skin's tuck under a piece, m, and whether it is not drawn at all (a mark of 0.995 and over)."""
    if not os.path.isfile(path):
        return np.zeros(len(P)), np.zeros(len(P), bool)
    raw = open(path, "rb").read()
    n = struct.unpack("<I", raw[:4])[0]
    rec = np.frombuffer(raw[4:4 + 16 * n], dtype=[("x", "<i4"), ("y", "<i4"), ("z", "<i4"), ("t", "<f4")])
    d = {(int(r["x"]), int(r["y"]), int(r["z"])): float(r["t"]) for r in rec}
    q = np.round(P.astype(np.float64) * 1e5).astype(np.int64)
    t = np.array([d.get(tuple(k), 0.0) for k in q])
    t = np.round(np.clip(t, 0, 1) * 255) / 255
    return 0.010 * np.where(t > 0.973, 1.0, t), t >= 0.995


# ------------------------------------------------------------ garment tuck --
G_OFFSET, G_FULL, G_GONE, G_SMOOTH, G_REACH = 0.0003, 0.973, 0.995, 0.010, 0.08   # (Rpg/GarmentTuck.cs)


def records(path):
    """A tuck-format record file: {(x, y, z): value}."""
    if not os.path.isfile(path):
        return {}
    raw = open(path, "rb").read()
    n = struct.unpack("<I", raw[:4])[0]
    rec = np.frombuffer(raw[4:4 + 16 * n], dtype=[("x", "<i4"), ("y", "<i4"), ("z", "<i4"), ("t", "<f4")])
    return {(int(r["x"]), int(r["y"]), int(r["z"])): float(r["t"]) for r in rec}


def footprint_records(r):
    """A piece's footprint on her body: the larger of its tuck and its cover a point."""
    d = records(r["tuck_path"])
    for k, t in records(os.path.join(os.path.dirname(r["tuck_path"]), "..", "armor_cover", f"{r['id']}.bin")).items():
        if t > d.get(k, 0):
            d[k] = t
    return d


class SkinPts:
    """Her body's points one a key (split copies merged, normals averaged), as GarmentTuck.SkinPoints."""

    def __init__(self, P, N):
        q = np.round(P.astype(np.float64) * 1e5).astype(np.int64)
        uq, first, inv = np.unique(q, axis=0, return_index=True, return_inverse=True)
        inv = np.asarray(inv).ravel()
        self.P = P[first]
        n = np.zeros((len(uq), 3))
        np.add.at(n, inv, N)
        self.N = n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
        self.key = {tuple(int(c) for c in k): i for i, k in enumerate(uq)}
        self.kd = cKDTree(self.P)

    def field(self, recs, spread):
        f = np.zeros(len(self.P))
        for d in recs:
            for k, t in d.items():
                i = self.key.get(k)
                if i is not None and t > f[i]:
                    f[i] = t
        if spread > 0 and (f > 0).any():
            nz = np.nonzero(f > 0)[0]
            g = f.copy()
            for i, js in zip(nz, self.kd.query_ball_point(self.P[nz], spread)):
                js = np.asarray(js, int)
                fall = 1 - np.linalg.norm(self.P[js] - self.P[i], axis=1) / spread
                g[js] = np.maximum(g[js], f[i] * fall)
            f = g
        return f

    def lay(self, PA, f):
        """GarmentTuck.Lay: each point's displacement [n, 3] and value."""
        disp = np.zeros_like(PA)
        t = np.zeros(len(PA))
        nz = np.nonzero(f > 0)[0]
        if not len(nz):
            return disp, t
        d, a = self.kd.query(PA, distance_upper_bound=G_REACH)
        ok = np.isfinite(d)
        # (only points near her footprint)
        dn, _ = cKDTree(self.P[nz]).query(PA, distance_upper_bound=G_REACH + 2 * G_SMOOTH)
        idx = np.nonzero(ok & np.isfinite(dn))[0]
        if not len(idx):
            return disp, t
        a = a[idx]
        ha = ((PA[idx] - self.P[a]) * self.N[a]).sum(1)
        F = PA[idx] - self.N[a] * ha[:, None]
        lists = self.kd.query_ball_point(F, G_SMOOTH)
        cnt = np.array([len(l) for l in lists])
        lists = [l if len(l) else [int(a[i])] for i, l in enumerate(lists)]
        cnt1 = np.array([len(l) for l in lists])
        row = np.repeat(np.arange(len(idx)), cnt1)
        col = np.concatenate([np.asarray(l, int) for l in lists])
        q = 1 - ((self.P[col] - F[row]) ** 2).sum(1) / G_SMOOTH ** 2
        w = np.where(cnt[row] == 0, 1.0, np.maximum(q, 0) ** 2 + 1e-9)
        sw = np.bincount(row, w, len(idx))
        tt = np.bincount(row, w * f[col], len(idx)) / sw
        Pm = np.stack([np.bincount(row, w * self.P[col, c], len(idx)) for c in range(3)], 1) / sw[:, None]
        Nm = np.stack([np.bincount(row, w * self.N[col, c], len(idx)) for c in range(3)], 1)
        Nm = Nm / np.maximum(np.linalg.norm(Nm, axis=1, keepdims=True), 1e-12)
        h = ((PA[idx] - Pm) * Nm).sum(1)
        amt = np.where(tt > G_FULL, 1.0, np.clip(tt, 0, 1))
        dd = np.where((tt > 0) & (h > G_OFFSET), (h - G_OFFSET) * amt, 0)
        disp[idx] = -Nm * dd[:, None]
        t[idx] = tt
        return disp, t


def hold_key(*rows):
    top = next((r for r in rows if r["slot"] == "top"), None)
    h = (top or {}).get("hold") or DEFAULT_HOLD
    return (float(h["amount"]), float(h["squash"]))


# ---------------------------------------------------------------------- main --
def main(argv):
    def opt(name, default):
        return argv[argv.index(name) + 1] if name in argv else default
    only = set(opt("--pieces", "").split(",")) - {""} or None
    clips = opt("--clips", ",".join(CLIPS)).split(",")
    step = int(opt("--step", "2"))
    grid = float(opt("--grid", "2.5")) / 1000
    same = "--same" in argv
    gt = "--garment-tuck" in argv
    gt_off = "--tuck-off" in argv
    gt_r = float(opt("--tuck-r", "20")) / 1000
    gt_w = "--tuck-weights" in argv     # (a prototype: the laid part of A skinned toward B's weights by its value)
    order = opt("--order", "").split(",") if "--order" in argv else \
        json.load(open(os.path.join(HERE, "slot_map.json"), encoding="utf-8"))["order"]
    out_dir = opt("--out", os.path.join(os.environ.get("TEMP", "."), "wearcheck"))
    os.makedirs(out_dir, exist_ok=True)
    t_start = time.time()

    rows = catalogue(only)
    byid = {r["id"]: r for r in rows}
    sk = skin.Skeleton.load(skin.SKELETONS / "heroine_skeleton.json")
    files = [(skin.PEOPLE / "heroine.glb", lambda n: n == "Heroine", "skin"),
             (skin.PEOPLE / "heroine.glb", lambda n: n == "HeroineHead", "head")]
    owner = {}
    for path in sorted({r["path"] for r in rows}):
        names = {m: r["id"] for r in rows if r["path"] == path for m in r["meshes"]}
        owner.update(names)
        files.append((skin.Path(path), lambda n, s=frozenset(names): n in s, "garment"))
    body = skin.Body(sk, files, skin.Jiggle(sk, 1, 1), label="her", helpers=True)
    pid = np.array([owner.get(p, "") for p in body.piece])
    P0 = body.P
    isk = np.nonzero(body.kind == "skin")[0]
    ish = np.nonzero(body.kind != "garment")[0]                      # her skin and head: her surface's normals
    loc = np.full(len(P0), -1)
    loc[ish] = np.arange(len(ish))
    TS = loc[body.T[(body.kind[body.T] != "garment").all(1)]]
    N0 = np.zeros_like(P0)
    N0[ish] = skin._normals(P0[ish], TS)
    kd_sh = cKDTree(P0[ish])
    tri_piece = pid[body.T[:, 0]]

    # Each piece: its samples (one vertex per voxel), their nearest point of her surface, its faces.
    pc = {}
    for r in rows:
        v = np.nonzero(pid == r["id"])[0]
        if not len(v):
            print("wearcheck: no mesh for", r["id"])
            continue
        _, first = np.unique(np.floor(P0[v] / grid).astype(np.int64), axis=0, return_index=True)
        smp = v[np.sort(first)]
        dist, near = kd_sh.query(P0[smp])
        T = body.T[tri_piece == r["id"]]
        pc[r["id"]] = {"samples": smp, "near": ish[near], "skin_mm": dist * 1000, "T": T,
                       "kd": cKDTree(P0[T].mean(1)), "kdv": cKDTree(P0[v])}

    if gt:
        sp = SkinPts(P0[isk], N0[isk])
        foot = {r["id"]: footprint_records(r) for r in rows}
        lay_cache = {}

        def laid(A, B):
            """A laid under B: its vertices' rest displacement (by vertex index), which of them a kept face has, and
            how many moved and how many faces were removed."""
            if (A, B) not in lay_cache:
                v = np.nonzero(pid == A)[0]
                disp, t = sp.lay(P0[v], sp.field([foot[B]], gt_r))
                Dd = np.zeros_like(P0)
                Dd[v] = disp
                tv = np.zeros(len(P0))
                tv[v] = t
                T = pc[A]["T"]
                kept = T[~(tv[T] >= G_GONE).all(1)]
                alive = np.zeros(len(P0), bool)
                alive[kept.ravel()] = True
                lay_cache[(A, B)] = (Dd, alive, int((np.abs(disp).sum(1) > 0).sum()), int(len(T) - len(kept)),
                                     np.where(tv > G_FULL, 1.0, np.clip(tv, 0, 1)))
            return lay_cache[(A, B)]

    def rest_footprint(O, D, Bid):
        """Rest: which samples meet B within REACH, the gap, the hit face and its K neighbours."""
        B = pc[Bid]
        d0, _ = B["kdv"].query(O, distance_upper_bound=REACH + 0.01)
        keep = np.nonzero(np.isfinite(d0))[0]
        res = {"idx": [], "gap": [], "out": [], "hit": [], "bary": [], "cand": []}
        for a in range(0, len(keep), 1500):
            ii = keep[a:a + 1500]
            _, ci = B["kd"].query(O[ii], k=min(K0, len(B["T"])))
            ci = ci.reshape(len(ii), -1)
            t, fa, u, v = cast(O[ii], D[ii], P0[B["T"][ci]])
            g, j, go = signed_gap(t, fa, REACH)
            ok = np.isfinite(g)
            if not ok.any():
                continue
            rr = np.nonzero(ok)[0]
            hit = ci[rr, j[rr]]
            hp = O[ii[rr]] + D[ii[rr]] * g[rr, None]
            _, cand = B["kd"].query(hp, k=min(K, len(B["T"])))
            res["idx"].append(ii[rr])
            res["gap"].append(g[rr])
            res["out"].append(go[rr])
            res["hit"].append(hit)
            res["bary"].append(np.c_[1 - u[rr, j[rr]] - v[rr, j[rr]], u[rr, j[rr]], v[rr, j[rr]]])
            res["cand"].append(cand.reshape(len(rr), -1))
        if not res["idx"]:
            return None
        return {k: np.concatenate(v) for k, v in res.items()}

    # The pairs, and their rest footprints.
    tests = []
    ids = [r["id"] for r in rows if r["id"] in pc]
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            ra, rb = byid[a], byid[b]
            if ra["slot"] == rb["slot"] or rb["slot"] in ra["covers"] or ra["slot"] in rb["covers"]:
                continue
            ctrl = ra["source"] == rb["source"]
            if ctrl and not same:
                continue
            orders = [(a, b)] if ra["layer"] < rb["layer"] else [(b, a)] if rb["layer"] < ra["layer"] else [(a, b), (b, a)]
            tuck = gt and not ctrl and ra["slot"] in order and rb["slot"] in order
            if tuck:
                orders = [(a, b)] if order.index(ra["slot"]) < order.index(rb["slot"]) else [(b, a)]
            found = []
            for A, B in orders:
                sA = pc[A]
                O = P0[sA["samples"]]
                D = N0[sA["near"]]
                info = None
                if tuck and not gt_off:
                    Dd, alive, nmoved, ncull, _ = laid(A, B)
                    O = O + Dd[sA["samples"]]
                    O = np.where(alive[sA["samples"]][:, None], O, 1e3)
                    info = (nmoved, ncull)
                fp = rest_footprint(O, D, B)
                if fp is not None:
                    found.append((A, B, fp, info))
            if len(found) == 2:
                found = [max(found, key=lambda f: np.median(f[2]["gap"]))]
            for A, B, fp, info in found:
                tests.append({"A": A, "B": B, "kind": "control" if ctrl else "mixed", "fp": fp, "laid": info,
                              "hold": hold_key(byid[A], byid[B]),
                              "reversed": bool(byid[A]["layer"] < byid[B]["layer"] and np.median(fp["gap"]) < 0)})
    # Her skin under each piece (tucked by the piece's record).
    if "--no-skin" not in argv:
        tk_all = {}
        for r in rows:
            if r["id"] not in pc:
                continue
            tk = np.zeros(len(P0))
            tk[isk], gone = tuck_of(r["tuck_path"], P0[isk])
            sv = isk[~gone]
            O = P0[sv] - N0[sv] * tk[sv, None]
            fp = rest_footprint(O + N0[sv] * 1e-5, N0[sv], r["id"])
            if fp is None:
                continue
            tk_all[r["id"]] = tk
            tests.append({"A": "skin", "B": r["id"], "kind": "skin", "fp": fp, "hold": hold_key(r), "reversed": False,
                          "tuck": tk[sv[fp["idx"]]], "sv": sv})
    t_rest = time.time() - t_start
    print(f"wearcheck: {len(rows)} pieces, {len(tests)} tests with a footprint ({t_rest:.0f} s at rest)")

    # Each test's points into the posed set.
    for x in tests:
        fp = x["fp"]
        if x["A"] == "skin":
            x["pts"] = x["sv"][fp["idx"]]
            x["dir"] = x["pts"]
        else:
            x["pts"] = pc[x["A"]]["samples"][fp["idx"]]
            x["dir"] = pc[x["A"]]["near"][fp["idx"]]
            if x.get("laid"):
                x["dA"] = laid(x["A"], x["B"])[0][x["pts"]]
                if gt_w:
                    vB = np.nonzero(pid == x["B"])[0]
                    _, nb = pc[x["B"]]["kdv"].query(P0[x["pts"]] + x["dA"])
                    x["wsh"] = laid(x["A"], x["B"])[4][x["pts"]]
                    x["nB"] = vB[nb]
        TB = pc[x["B"]]["T"]
        x["hitv"] = TB[fp["hit"]]
        x["candv"] = TB[fp["cand"]]
        x["Sv"] = TB[np.unique(fp["cand"])]
        n = len(fp["idx"])
        x["min"] = np.full(n, np.inf)
        x["min_out"] = np.full(n, np.inf)
        x["worst"] = (np.inf, None, None)
        x["rest_min_mm"] = float(fp["gap"].min() * 1000)
        x["rest_med_mm"] = float(np.median(fp["gap"]) * 1000)
        x["rest_through2"] = int((fp["gap"] < -0.002).sum())
        x["rest_out2"] = int((fp["out"] < -0.002).sum())
        x["lost"] = 0
        x["per_clip"] = {}
        x["seen"] = 0

    holds = sorted({x["hold"] for x in tests})
    for h in holds:
        group = [x for x in tests if x["hold"] == h]
        need = np.unique(np.concatenate([ish] + [np.r_[x["pts"], x["hitv"].ravel(), x["candv"].ravel()] for x in group]))
        at = np.full(len(P0), -1)
        at[need] = np.arange(len(need))
        sh_local = at[ish]
        SvB = {B: np.unique(np.concatenate([x["Sv"] for x in group if x["B"] == B]), axis=0) for B in {x["B"] for x in group}}
        body.jiggle = skin.Jiggle(sk, amount=h[0], squash=h[1])
        for c in clips:
            clip = body.clip(c)
            frames = body.frames(clip)
            for f in range(0, len(frames), step):
                Pp = body.pose(frames[f], need)
                S = body.skin_mats(frames[f]) if any("dA" in x for x in group) else None
                Np = np.zeros_like(Pp)
                Np[sh_local] = skin._normals(Pp[sh_local], TS)
                kd_frame = {}
                for x in group:
                    O = Pp[at[x["pts"]]]
                    D = Np[at[x["dir"]]]
                    if x["A"] == "skin":
                        O = O - D * x["tuck"][:, None] + D * 1e-5
                    elif "dA" in x:
                        # (skinning is linear in the rest point: the displacement goes through its blend of bones)
                        Jp, Wp = body.J[x["pts"]], body.W[x["pts"]]
                        M = sum(Wp[:, k, None, None] * S[Jp[:, k], :3, :3] for k in range(Jp.shape[1]))
                        O = O + np.einsum("nij,nj->ni", M, x["dA"])
                        if "nB" in x:
                            Jb, Wb = body.J[x["nB"]], body.W[x["nB"]]
                            Mb = sum(Wb[:, k, None, None] * S[Jb[:, k]] for k in range(Jb.shape[1]))
                            pr = np.c_[P0[x["pts"]] + x["dA"], np.ones(len(x["pts"]))]
                            Ob = np.einsum("nij,nj->ni", Mb[:, :3, :], pr)
                            O = O + x["wsh"][:, None] * (Ob - O)
                    # (tracked: B's rest hit face's posed plane)
                    H = Pp[at[x["hitv"]]]
                    hp = (H * x["fp"]["bary"][:, :, None]).sum(1)
                    fn = np.cross(H[:, 1] - H[:, 0], H[:, 2] - H[:, 0])
                    den = (fn * D).sum(1)
                    g = np.where(np.abs(den) > 1e-14, ((hp - O) * fn).sum(1) / np.where(np.abs(den) > 1e-14, den, 1), np.nan)
                    # (trusted only while B's rest hit stays on the ray: else re-cast)
                    lat = np.linalg.norm(np.cross(hp - O, D), axis=1)
                    g = np.where((np.abs(g) < REACH_POSED) & (lat < DRIFT), g, np.nan)
                    go = g.copy()
                    r = np.nonzero(~(g > REFINE))[0]
                    if len(r):
                        t, fa, _, _ = cast(O[r], D[r], Pp[at[x["candv"][r]]])
                        gr, _, gor = signed_gap(t, fa, REACH_POSED)
                        lost = np.nonzero(~np.isfinite(gr))[0]
                        if len(lost):
                            # (B slid off its rest hit: B's faces over every footprint of B, nearest the sample)
                            if x["B"] not in kd_frame:
                                kd_frame[x["B"]] = cKDTree(Pp[at[SvB[x["B"]]]].mean(1))
                            Sv = SvB[x["B"]]
                            _, ii = kd_frame[x["B"]].query(O[r[lost]], k=min(K0, len(Sv)))
                            t, fa, _, _ = cast(O[r[lost]], D[r[lost]], Pp[at[Sv[ii.reshape(len(lost), -1)]]])
                            gl, _, gol = signed_gap(t, fa, REACH_POSED)
                            gr[lost], gor[lost] = gl, gol
                            x["lost"] += int((~np.isfinite(gl)).sum())
                        g[r], go[r] = gr, gor
                    x["min_out"] = np.minimum(x["min_out"], np.where(np.isfinite(go), go, np.inf))
                    x["seen"] += len(g)
                    gg = np.where(np.isfinite(g), g, np.inf)
                    x["min"] = np.minimum(x["min"], gg)
                    k = int(gg.argmin())
                    pc_ = x["per_clip"].setdefault(c, [np.inf, np.zeros(len(gg), bool)])
                    pc_[0] = min(pc_[0], float(gg[k]))
                    pc_[1] |= gg < -0.002
                    if gg[k] < x["worst"][0]:
                        x["worst"] = (float(gg[k]), c, f)
            print(f"wearcheck: hold {h} {c} ({time.time() - t_start:.0f} s)", flush=True)
        print(f"wearcheck: hold {h} done ({time.time() - t_start:.0f} s)")

    # Report.
    bone = np.array(sk.names)
    out = []
    for x in tests:
        m = x["min"]
        mo = x["min_out"]
        fin = np.isfinite(m)
        pen = -m[fin] * 1000
        A, B = x["A"], x["B"]
        wi = int(np.argmin(np.where(fin, m, np.inf)))
        pt = x["pts"][wi]
        e = {"A": A, "B": B, "kind": x["kind"],
             "slots": f"{'skin' if A == 'skin' else byid[A]['slot']}->{byid[B]['slot']}",
             "layers": [0 if A == "skin" else byid[A]["layer"], byid[B]["layer"]],
             "hold": list(x["hold"]), "footprint": int(len(m)),
             "worst_mm": round(float(pen.max()), 2) if len(pen) else None,
             "p99_mm": round(float(np.percentile(pen, 99)), 2) if len(pen) else None,
             "n_over_0_5": int((pen > 0.5).sum()), "n_over_2": int((pen > 2).sum()),
             "rest_n_over_2": x["rest_through2"],
             "out_worst_mm": round(float(-mo[np.isfinite(mo)].min() * 1000), 2) if np.isfinite(mo).any() else None,
             "out_n_over_0_5": int((mo < -0.0005).sum()), "out_n_over_2": int((mo < -0.002).sum()),
             "rest_out_n_over_2": x["rest_out2"],
             "B_shell_mm_median": round(float(np.median(x["fp"]["out"] - x["fp"]["gap"]) * 1000), 2),
             "worst_clip": x["worst"][1], "worst_frame": x["worst"][2],
             "worst_bone": str(bone[body.J[pt, int(body.W[pt].argmax())]]),
             "rest_gap_min_mm": round(x["rest_min_mm"], 2), "rest_gap_median_mm": round(x["rest_med_mm"], 2),
             "per_clip": {c: [round(-v[0] * 1000, 1), int(v[1].sum())] for c, v in x["per_clip"].items()},
             "laid": x.get("laid"), "reversed": x["reversed"], "lost_share": round(x["lost"] / max(x["seen"], 1), 4)}
        if A != "skin":
            fi = x["fp"]["idx"]
            e["A_skin_mm_median"] = round(float(np.median(pc[A]["skin_mm"][fi])), 2)
            e["B_skin_mm_median"] = round(float(np.median(pc[A]["skin_mm"][fi] + x["fp"]["gap"] * 1000)), 2)
            e["A_skin_mm_at_worst"] = round(float(pc[A]["skin_mm"][fi][wi]), 2)
        out.append(e)
    out.sort(key=lambda e: (-e["out_n_over_2"], -(e["worst_mm"] if e["worst_mm"] is not None else -99)))
    took = time.time() - t_start
    meta = {"garment_tuck": gt and not gt_off, "tuck_r_mm": gt_r * 1000, "order": order, "clips": clips, "step": step, "grid_mm": grid * 1000, "reach_mm": REACH * 1000, "K": K, "seconds": round(took),
            "pieces": [r["id"] for r in rows], "note": "worst_mm/p99_mm: penetration of A past B's inner face (negative: "
            "the least clearance); n_*: A samples (grid voxels) ever past by more than 0.5 / 2 mm; rest_n_over_2 at rest; "
            "per_clip: [worst mm, samples past 2 mm]; out_*: the same past B's OUTER face (what shows; inside B's shell "
            "is hidden); table sorted by out_n_over_2 then worst_mm"}
    json.dump({"meta": meta, "pairs": out}, open(os.path.join(out_dir, "matrix.json"), "w"), indent=1)
    with open(os.path.join(out_dir, "table.txt"), "w") as fh:
        fh.write(f"{'A':18} {'B':18} {'slots':18} {'kind':7} {'worst':>6} {'p99':>6} {'>0.5':>5} {'>2':>5} {'rest>2':>6} "
                 f"{'rmin':>6} {'rmed':>6} {'foot':>5} {'Askin':>5} {'Bskin':>5} {'Bshl':>4} {'OUT':>5} {'OUT>2':>5} {'rOUT>2':>6} worst_clip@frame bone\n")
        for e in out:
            fh.write(f"{e['A']:18} {e['B']:18} {e['slots']:18} {e['kind']:7} {e['worst_mm']:6.1f} {e['p99_mm']:6.1f} "
                     f"{e['n_over_0_5']:5d} {e['n_over_2']:5d} {e['rest_n_over_2']:6d} {e['rest_gap_min_mm']:6.1f} "
                     f"{e['rest_gap_median_mm']:6.1f} {e['footprint']:5d} {e.get('A_skin_mm_median', 0):5.1f} "
                     f"{e.get('B_skin_mm_median', 0):5.1f} {e['B_shell_mm_median']:4.1f} {e['out_worst_mm'] or 0:5.1f} {e['out_n_over_2']:5d} "
                     f"{e['rest_out_n_over_2']:6d} {e['worst_clip']}@{e['worst_frame']} {e['worst_bone']}"
                     f"{' REVERSED' if e['reversed'] else ''}\n")
    print(f"wearcheck: {len(out)} tests in {took:.0f} s -> {out_dir}")


if __name__ == "__main__":
    main(sys.argv[1:])
