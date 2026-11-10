"""Gear motion check on any body built on the base (P2 gear): wearcheck's measures (tools/armor/wearcheck.py, A's
checker), run from a built gear folder (tools/armor/gear_fit.py build) on that folder's body, through that body's own
clips. Numbers only; it fixes nothing.

Posing: the body by its own poser (tools/body/posers.py "lbs": the glb's skin, rig.json "poser" = tools.body.rig_drive),
from the clip dumps (tools/body/out/clips/<clip>.json, the body's baked globals per key frame, Godot skeleton space),
as tools/body/clipcheck.py Body.pose does it: bones the dump lacks, and unkeyed rig helpers, at their rest local; then
the rig's laws (girdle, hand_clear, helper rows) and its correctives (rig.json "correctives": arm_hang rbf, elbow /
knee flex, hip arc). The pieces ride the SAME bone matrices with their own weights (8 a vertex) and inverse binds,
and the same blend-shape weights by name: the correctives they carry (arm_hang_*: a piece built over her takes her
shapes), and form_support_lift / _press / _fill, set as HerWear does from the worn top's hold (ArmorHold: support, else
clamp((1 - amount) / 0.45, 0, 1); lift/press/fill each default to it; no top, or a top with no hold: 0).
NOT driven: B's springs (P1Jiggle's breast and glute bones) beyond what the dump carries (the bake's own globals for
those bones; no live spring swing is simulated here), the face (HeroineHead's face/expression shapes stay at 0), and
cloth (no row simulates).

Measures (per clip and per test; B's close tier):
  skin    her skin under each piece, tucked by the piece's armor_tuck record as heroine_skin.gdshader draws it on B
          (tuck_channel -2, a float tuck_map, so no 8-bit step: pushed in along her posed normal by 10 mm x the mark,
          all of it past 0.973; a point marked 0.995 and over not drawn), against the piece's posed faces: wearcheck's
          signed gap (to the piece's inner face; OUT: past its OUTER face, what shows).
  control the sets as worn: each calling's own pieces (same outfit: no garment tuck), and the plate proof set (pieces of
          different outfits: the garment tuck as the game lays it between them).
  mixed   every piece of one proof set (reaver revealing, ranger leather, the plate set) under / over every piece of
          another, in the slot order (tools/armor/slot_map.json "order"), with the garment tuck as HerWear lays it
          (Rpg/GarmentTuck.cs Over / Field / Lay: the inner piece laid onto her under the outer piece's footprint,
          max(armor_tuck, armor_cover) spread 20 mm, its faces all past 0.995 removed, and its laid vertices' weights
          blended toward the outer piece's nearest vertex by the lay amount, top 8, normalised: GarmentTuck.Weights).
          Never the same slot, nor a pair where one's covers hide the other, nor a skirt from another source's belt
          (Wear.Look); a rigid inner piece is never laid.
  show    every slot shows: for the three proof sets as worn and each mixed look (one set with one piece of another set
          put on, the rest filled by Wear.Look's rules: the put-on piece's covers hide the set's pieces there, a set piece
          whose covers would hide the put-on piece is dropped, a skirt never hangs from another source's belt), at rest
          with each piece laid under the pieces over it: each worn piece's visible area (its kept faces, thinned on a
          4 mm grid; a sample is visible when any of 5 rays (her outward normal and four 50 deg off it) runs 8 cm clear of
          every other worn piece). A piece under 5% visible fails; a piece Look drops is listed with its reason. Slots no
          proof set fills are listed.

Counts read as area: a skin sample is her vertex (a third of its triangles' area), a piece sample a GRID voxel (at
least GRID^2). OUT>2: area of samples ever past the outer face by more than 2 mm in the clip.

    python tools/armor/gear_wear.py [--gear godot/art/gear/out/body_p1] [--body <dir>] [--clips <dir> | a,b,.. | a.json,..]
        [--pieces a,b,..] [--tests skin,control,mixed,show] [--step 2] [--grid 2.5] [--jobs N] [--out <dir>]
        [--out-mm <depth>]
Where it shows ("views" per test, mm^2): close = through over 2 mm in the town / idle / look / talk clips, play = over
6 mm in every other clip, "*_ex" without the known broken clips (VIEWS, CLOSE_WORDS, BROKEN). --out-mm D adds
"outd_mm2": the 2 mm count again at depth D.
What the eye gets ("frames" per test, "frame_mm2" per clip): the WORST SINGLE FRAME's through area deeper than each of
FRAME_MM (the views above are unions over every frame of every clip, which no frame shows at once). --samples adds
<out>/samples_<piece>.npz per skin test (each sample's rest position, area and deepest out per clip) for a breakdown.
Writes <out>/gear_wear.json (everything) and <out>/gear_wear.md (worst 20 and per-test totals).
"""
import json
import os
import struct
import sys
import time

import numpy as np
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "tools", "body"))
sys.path.insert(0, os.path.join(REPO, "tools", "anim"))
import wearcheck as wc  # noqa: E402  (cast, signed_gap, SkinPts: the measuring core and the garment tuck's port)

GEAR = os.path.join(REPO, "godot", "art", "gear", "out", "body_p1")
CLIPS = os.path.join(REPO, "tools", "body", "out", "clips")
OUT = os.path.join(REPO, "godot", ".shots", "gear_p2", "wear")
SKIP_SLOTS = ("ink", "cloak")
PLATE_SET = ("plate_cuirass_plain", "plate_gstring_plain", "plate_pauldrons_plain", "warden.greaves", "warden.boots",
             "warden.bracers")
PROOF = ("reaver", "ranger", "plate")
CALLINGS = ("warden", "arcanist", "reaver", "ranger")
VISUAL_SLOTS = ("top", "bottom", "legwear", "gloves", "skirt", "belt", "collar", "bracers", "greaves", "boots",
                "pauldrons", "cloak", "head")
HANGS = {"skirt": "belt"}
TUCK_DEPTH, T_FULL, T_GONE = 0.010, 0.973, 0.995           # heroine_skin.gdshader
G_SPREAD = 0.020                                           # GarmentTuck.Spread
REACH, REACH_POSED, K, K0, REFINE, DRIFT = wc.REACH, wc.REACH_POSED, wc.K, wc.K0, wc.REFINE, wc.DRIFT
SHOW_GRID, SHOW_RAY, SHOW_TILT, SHOW_MIN = 0.004, 0.08, 50.0, 0.05
# WHERE IT SHOWS: the depth (mm past the outer face) a through must reach to show under each camera. close: the town,
# idle, look and talk clips (close cameras, about 1 mm a pixel); play: every other clip (the play camera, 13 mm a pixel
# at 23 m). A clip's view is read from the words of its name (clip_view). BROKEN: clips known bad, left out of "*_ex".
VIEWS = {"close": 2.0, "play": 6.0}
CLOSE_WORDS = ("town", "idle", "look", "talk")
BROKEN = ("Jog_Fwd",)
FRAME_MM = (2.0, 3.0, 6.0)      # the depths the worst single frame's through area is counted at (frame_mm2, frames)


# ------------------------------------------------------------------ helpers --
def amount(t):
    return np.where(t > T_FULL, 1.0, np.clip(t, 0, 1))


def support_of(row):
    """HerWear: the worn top's hold drives B's form_support shapes ({} when none)."""
    h = (row or {}).get("hold") if (row or {}).get("slot") == "top" else None
    if not h:
        return (0.0, 0.0, 0.0)
    s = h.get("support")
    s = float(np.clip((1 - float(h.get("amount", 1))) / 0.45, 0, 1)) if s is None else float(s)
    return tuple(float(h[k]) if h.get(k) is not None else s for k in ("lift", "press", "fill"))


def support_weights(sup):
    return {"form_support_lift": sup[0], "form_support_press": sup[1], "form_support_fill": sup[2]}


def read_records(path):
    if not os.path.isfile(path):
        return {}
    raw = open(path, "rb").read()
    n = struct.unpack("<I", raw[:4])[0]
    rec = np.frombuffer(raw[4:4 + 16 * n], dtype=[("x", "<i4"), ("y", "<i4"), ("z", "<i4"), ("t", "<f4")])
    return {(int(r["x"]), int(r["y"]), int(r["z"])): float(r["t"]) for r in rec}


def keys_of(P):
    return [tuple(k) for k in np.round(np.asarray(P, np.float64) * 1e5).astype(np.int64)]


def skin_tuck(recs, keys):
    """The shader's tuck of her skin under one piece: depth (m) and not drawn, per point."""
    t = np.array([recs.get(k, 0.0) for k in keys])
    return TUCK_DEPTH * amount(t), t >= T_GONE



ENCLOSE_SLOTS = ("boots", "gloves", "greaves", "bracers", "head")   # mirrors gear_tuck.ENCLOSE_SLOTS


def full_cast(O, D, V, reach, chunk=48, cull=0.20):
    """Rays O, D [n, 3] against ALL of one piece's faces V [m, 3, 3]: g, j (face index in V), go, u, v as cast/signed_gap
    give them. A sample in a boot's toe box finds its inner face ahead, which the K0 nearest faces miss. Samples go in
    spatially sorted chunks, each against the faces within `cull` m of the chunk (a ray only matters to `reach`, and the
    forward face of a toe box is a few cm on), so cost and memory stay small."""
    n = len(O)
    g, go = np.full(n, np.nan), np.full(n, np.nan)
    j, u, v = np.zeros(n, int), np.zeros(n), np.zeros(n)
    if n == 0:
        return g, j, go, u, v
    cen = V.mean(1)
    kd = cKDTree(cen)
    order = np.lexsort(np.floor(O.T[::-1] / 0.05).astype(int))
    for a in range(0, n, chunk):
        sl = order[a:a + chunk]
        rad = cull + float(np.linalg.norm(O[sl] - O[sl].mean(0), axis=1).max())
        fi = np.asarray(kd.query_ball_point(O[sl].mean(0), rad), dtype=int)
        if len(fi) == 0:
            continue
        k = len(sl)
        t, fa, uu, vv = wc.cast(O[sl], D[sl], np.broadcast_to(V[fi], (k, len(fi), 3, 3)))
        gg, jj, gg2 = wc.signed_gap(t, fa, reach)
        r = np.arange(k)
        g[sl], go[sl], j[sl] = gg, gg2, fi[jj]
        u[sl], v[sl] = uu[r, jj], vv[r, jj]
    return g, j, go, u, v

class Welded:
    """Point normals of a fixed topology, welded by rest place (computed once)."""

    def __init__(self, P0, T):
        _, inv = np.unique(np.round(P0, 6), axis=0, return_inverse=True)
        self.inv, self.T, self.n = np.asarray(inv).ravel(), T, int(np.max(inv)) + 1
        self.on = np.zeros(len(P0), bool)
        self.on[T.ravel()] = True

    def __call__(self, P):
        T = self.T
        fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
        N = np.zeros((self.n, 3))
        for k in range(3):
            np.add.at(N, self.inv[T[:, k]], fn)
        N = N[self.inv]
        return np.where(self.on[:, None], N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12), 0.0)


def blend_weights(Ja, Wa, Jb, Wb, s, keep=8):
    """GarmentTuck.BlendWeights, rows at once: (1 - s) A + s B by bone, the largest `keep`, normalised."""
    n = len(Ja)
    J = np.concatenate([Ja, Jb], 1)
    W = np.concatenate([Wa * (1 - s)[:, None], Wb * s[:, None]], 1)
    W = np.where(W > 0, W, 0)
    # (equal bones merged: sorted by bone, each run summed into its last column)
    o = np.argsort(J, 1, kind="stable")
    J = np.take_along_axis(J, o, 1)
    W = np.take_along_axis(W, o, 1)
    for c in range(1, J.shape[1]):
        same = J[:, c] == J[:, c - 1]
        W[:, c] = np.where(same, W[:, c] + W[:, c - 1], W[:, c])
        W[:, c - 1] = np.where(same, 0, W[:, c - 1])
    o = np.argsort(-W, 1, kind="stable")[:, :keep]
    J = np.take_along_axis(J, o, 1)
    W = np.take_along_axis(W, o, 1)
    sw = W.sum(1, keepdims=True)
    return np.where(W > 0, J, 0), np.where(sw > 0, W / np.maximum(sw, 1e-30), 0)


# -------------------------------------------------------------------- scene --
class Scene:
    """The body and every piece as one point set on one skeleton: rest points, triangles, 8 bone weights a point,
    blend-shape deltas by name (sparse), and the skinning (S [B, 4, 4] = G @ inverse binds)."""

    def __init__(self, P0, T, kind, owner, J, W, targets, keys=None):
        self.P0 = np.asarray(P0, np.float64)
        self.T = np.asarray(T, np.int64)
        self.kind = np.asarray(kind)
        self.owner = np.asarray(owner)
        self.J = np.asarray(J, np.int64)
        self.W = np.asarray(W, np.float64)
        self.targets = targets            # {name: (idx [n], delta [n, 3])}
        self.keys = keys
        self.tri_owner = self.owner[self.T[:, 0]]
        self.isk = np.nonzero(self.kind == "skin")[0]
        self.ish = np.nonzero(self.kind != "piece")[0]
        loc = np.full(len(self.P0), -1)
        loc[self.ish] = np.arange(len(self.ish))
        self.TS = loc[self.T[(self.kind[self.T] != "piece").all(1)]]
        self.normals_sh = Welded(self.P0[self.ish], self.TS)

    def restrict(self, idx):
        """The blend shapes' deltas over the points idx (local rows): {name: (rows, delta)}."""
        at = np.full(len(self.P0), -1)
        at[idx] = np.arange(len(idx))
        sub = {}
        for k, (ti, d) in self.targets.items():
            a = at[ti]
            ok = a >= 0
            if ok.any():
                sub[k] = (a[ok], d[ok])
        return sub

    def rest(self, idx, weights=None, sub=None):
        P = self.P0[idx].copy()
        if weights and any(weights.values()):
            sub = self.restrict(idx) if sub is None else sub
            for k, w in weights.items():
                if w and k in sub:
                    a, d = sub[k]
                    P[a] += w * d
        return P

    @staticmethod
    def lbs(S, P, J, W):
        Ph = np.c_[P, np.ones(len(P))]
        out = np.zeros((len(P), 3))
        for k in range(J.shape[1]):
            w = W[:, k]
            if not w.any():
                continue
            out += w[:, None] * np.einsum("nij,nj->ni", S[J[:, k], :3, :], Ph)
        return out

    def pose(self, S, weights, idx):
        return self.lbs(S, self.rest(idx, weights), self.J[idx], self.W[idx])


def load_rows(gear):
    ix = json.load(open(os.path.join(gear, "gear_index.json"), encoding="utf-8"))
    rows = []
    for r in ix["rows"]:
        if r.get("lod") or r.get("slot") in (None, *SKIP_SLOTS) or not r.get("file"):
            continue
        r = dict(r)
        r["covers"] = r.get("covers") or [r["slot"]]
        r["source"] = r.get("outfit") or r["id"]
        r["path"] = os.path.join(gear, os.path.basename(r["file"]))
        r["tuck_path"] = os.path.join(gear, r["tuck"]) if r.get("tuck") else ""
        r["cover_path"] = os.path.join(gear, "armor_cover", f"{r['id']}.bin")
        rows.append(r)
    return ix, rows


def build_scene(body_dir, rows, only=None):
    """B's body (lbs poser: Heroine + its close head) and the rows' meshes from their gltfs, on B's skeleton."""
    from posers import make_poser
    from gl import Glb
    rig = json.load(open(os.path.join(body_dir, "rig.json"), encoding="utf-8"))
    p = make_poser("lbs", os.path.join(body_dir, "body.glb"), rig)
    nb = len(p.names)
    pad = lambda a: np.pad(a, ((0, 0), (0, 8 - a.shape[1]))) if a.shape[1] < 8 else a[:, :8]  # noqa: E731
    P, T, kind, owner, J, W = [p.Pb], [p.T], [np.where(p.piece == "body", "skin", "head")], [np.full(len(p.Pb), "")], \
        [pad(p.J)], [pad(p.W)]
    tg = {k: [(np.nonzero(np.abs(d).sum(1) > 0)[0], d[np.abs(d).sum(1) > 0])] for k, d in p.targets.items()}
    base = len(p.Pb)
    ibm_body = p.skel.ibm
    for r in rows:
        if only and r["id"] not in only:
            continue
        g = Glb(r["path"])
        names = [g.nodes[j]["name"] for j in g.js["skins"][0]["joints"]]
        remap = np.array([p.index[n] for n in names])
        ibm = g.skeleton(0).ibm
        if np.abs(ibm - ibm_body[remap]).max() > 1e-5:
            raise SystemExit(f"gear_wear: {r['id']}: its inverse binds are not the body's")
        got = 0
        for m in g.meshes:
            if m.node not in r["meshes"] or m.J is None:
                continue
            Wm = pad(m.W.astype(np.float64))
            Wm = Wm / np.maximum(Wm.sum(1, keepdims=True), 1e-12)
            P.append(m.P.astype(np.float64))
            T.append(m.T + base)
            kind.append(np.full(len(m.P), "piece"))
            owner.append(np.full(len(m.P), r["id"], dtype=object))
            J.append(remap[pad(m.J)])
            W.append(Wm)
            for k, d in m.targets.items():
                d = d["POSITION"].astype(np.float64)
                nz = np.nonzero(np.abs(d).sum(1) > 0)[0]
                if len(nz):
                    tg.setdefault(k, []).append((nz + base, d[nz]))
            base += len(m.P)
            got += 1
        if not got:
            print(f"gear_wear: {r['id']}: no skinned mesh of {r['meshes']} in {r['path']}")
    targets = {k: (np.concatenate([a for a, _ in v]), np.concatenate([b for _, b in v])) for k, v in tg.items()}
    sc = Scene(np.concatenate(P), np.concatenate(T), np.concatenate(kind), np.concatenate(owner).astype(str),
               np.concatenate(J), np.concatenate(W), targets)
    sc.keys = keys_of(p.Pb[p.piece == "body"])      # (the tuck format's keys: B's close body's bind points)
    sc.ibm = ibm_body
    sc.poser, sc.rig = p, rig
    return sc


class ClipPoser:
    """B's skinning matrices and shape weights per key frame of a clip dump (clipcheck.Body.pose's globals)."""

    def __init__(self, sc, dump):
        p = sc.poser
        self.sc, self.p, self.d = sc, p, dump
        names = dump["b_names"]
        self.map = [p.index.get(n, -1) for n in names]
        rest_dump = mats(dump["b_rest"])
        j = names.index("pelvis")
        self.X = p.rest[p.index["pelvis"]] @ np.linalg.inv(rest_dump[j])
        self.keyed = set(dump["keyed"])
        self.helpers = set()
        for h in sc.rig.get("helpers", []):
            for s in ("l", "r") if "{s}" in h["name"] else ("",):
                self.helpers.add(h["name"].replace("{s}", s))
        self.order, seen = [], set()

        def visit(k):
            if k in seen:
                return
            if p.parent[k] >= 0:
                visit(p.parent[k])
            seen.add(k)
            self.order.append(k)
        for k in range(len(p.names)):
            visit(k)
        self.n = len(dump["B"])

    def frame(self, f):
        p = self.p
        Gd = mats(self.d["B"][f])
        G = p.rest.copy()
        got = np.zeros(len(G), bool)
        for a, k in enumerate(self.map):
            if k >= 0:
                G[k] = self.X @ Gd[a]
                got[k] = True
        for k in self.order:
            pk = p.parent[k]
            if pk >= 0 and (not got[k] or p.names[k] in self.helpers and p.names[k] not in self.keyed):
                G[k] = G[pk] @ (np.linalg.inv(p.rest[pk]) @ p.rest[k])
        G, w = p.driver.drive(p, G, self.sc.rig)
        return G @ self.sc.ibm, dict(w)


def dump_sources(sc, paths, step):
    """The clip dumps as run() sources: B posed at every `step`th key frame."""
    out = []
    for cp in paths:
        name = os.path.splitext(os.path.basename(cp))[0]

        def frames(cp=cp):
            cpz = ClipPoser(sc, json.load(open(cp, encoding="utf-8")))
            for f in range(0, cpz.n, step):
                S, w = cpz.frame(f)
                yield f, S, w
        out.append((name, frames))
    return out


def mats(a):
    a = np.asarray(a, float).reshape(-1, 3, 4)
    m = np.zeros((len(a), 4, 4))
    m[:, :3] = a
    m[:, 3, 3] = 1
    return m


def clip_view(name):
    """"close" or "play" (VIEWS) by the words of a clip's name: idle_stalker_town is close (idle, town), not by the
    "talk" inside "stalker"."""
    words = os.path.splitext(os.path.basename(name))[0].lower().replace("-", "_").split("_")
    return "close" if any(w in CLOSE_WORDS for w in words) else "play"


def view_sets(per_clip_out, n):
    """{view key: sample indices} of one test: per view (VIEWS), the samples ever past the outer face by more than the
    view's depth over that view's clips; "<view>_ex" leaves the BROKEN clips out. per_clip_out: {clip: min out (m)}."""
    out = {}
    for v, d in VIEWS.items():
        for ex in ("", "_ex"):
            mo = np.full(n, np.inf)
            for c, o in per_clip_out.items():
                if clip_view(c) == v and not (ex and c in BROKEN):
                    mo = np.minimum(mo, o)
            out[v + ex] = np.nonzero(mo < -d / 1000.0)[0].tolist()
    return out


def frame_views(per_clip):
    """{view key: {depth: {"mm2", "clip", "frame"}}} of one test: per view (and "<view>_ex"), the worst SINGLE FRAME's
    through area at each of FRAME_MM over that view's clips. per_clip: the report's rows (frame_mm2, frame_at)."""
    out = {}
    for v in VIEWS:
        for ex in ("", "_ex"):
            best = {f"{d:g}": {"mm2": 0.0, "clip": "", "frame": -1} for d in FRAME_MM}
            for c, row in per_clip.items():
                if clip_view(c) != v or (ex and c in BROKEN) or "frame_mm2" not in row:
                    continue
                for k, a in row["frame_mm2"].items():
                    if a > best[k]["mm2"]:
                        best[k] = {"mm2": a, "clip": c, "frame": row["frame_at"][k]}
            out[v + ex] = best
    return out


def clip_files(spec):
    """--clips: a folder (every dump in it), or a list of names or .json paths (names read from the default folder)."""
    if os.path.isdir(spec):
        return sorted(os.path.join(spec, f) for f in os.listdir(spec) if f.endswith(".json"))
    out = []
    for c in spec.split(","):
        c = c.strip()
        if c:
            out.append(c if c.endswith(".json") else os.path.join(CLIPS, c + ".json"))
    return out


# -------------------------------------------------------------------- sets --
def proof_sets(byid):
    return {"reaver": [i for i, r in byid.items() if r.get("outfit") == "reaver"],
            "ranger": [i for i, r in byid.items() if r.get("outfit") == "ranger"],
            "plate": [i for i in PLATE_SET if i in byid]}


def over(outer, inner, order):
    """GarmentTuck.Over: outer later in the order, not of inner's outfit, inner not rigid."""
    if outer["slot"] not in order or inner["slot"] not in order:
        return False
    o, i = order.index(outer["slot"]), order.index(inner["slot"])
    if o <= i or outer["id"] == inner["id"] or inner.get("rigid"):
        return False
    return not (outer.get("outfit") and outer.get("outfit") == inner.get("outfit"))


def look_of(base, put, byid):
    """Wear.Look for one set's pieces (fills) with one other piece put on: (look {slot: id}, dropped [(id, why)])."""
    pr = byid[put]
    look, dropped = {pr["slot"]: put}, []
    hidden = {c for c in pr["covers"] if c != pr["slot"]}
    for i in base:
        r = byid[i]
        if r["slot"] == pr["slot"]:
            dropped.append((i, f"its slot holds {put}"))
        elif r["slot"] in hidden:
            dropped.append((i, f"{put} covers {r['slot']}"))
        elif HANGS.get(r["slot"]) == pr["slot"] and r["source"] != pr["source"]:
            dropped.append((i, f"hangs from {pr['slot']}, which holds {put}"))
        elif any(c != r["slot"] and c == pr["slot"] for c in r["covers"]):
            dropped.append((i, f"its covers would hide {put}"))
        else:
            look[r["slot"]] = i
    # (what the fills kept hide, of the other fills)
    for s, i in list(look.items()):
        if i == put:
            continue
        for c in byid[i]["covers"]:
            if c != s and c in look and look[c] != put:
                dropped.append((look.pop(c), f"{i} covers {c}"))
    return look, dropped


# ---------------------------------------------------------------- the check --
class Check:
    def __init__(self, sc, rows, order, grid=0.0025, confirm=True):
        self.sc, self.rows, self.order, self.grid, self.confirm = sc, rows, order, grid, confirm
        self.byid = {r["id"]: r for r in rows}
        P0 = sc.P0
        self.N0 = np.zeros_like(P0)
        self.N0[sc.ish] = sc.normals_sh(P0[sc.ish])
        self.kd_sh = cKDTree(P0[sc.ish])
        self.pc = {}
        for r in rows:
            v = np.nonzero(sc.owner == r["id"])[0]
            if not len(v):
                continue
            _, first = np.unique(np.floor(P0[v] / grid).astype(np.int64), axis=0, return_index=True)
            smp = v[np.sort(first)]
            dist, near = self.kd_sh.query(P0[smp])
            T = sc.T[sc.tri_owner == r["id"]]
            self.pc[r["id"]] = {"samples": smp, "near": sc.ish[near], "skin_mm": dist * 1000, "T": T, "v": v,
                                "kd": cKDTree(P0[T].mean(1)), "kdv": cKDTree(P0[v])}
        T = sc.T
        ta = np.linalg.norm(np.cross(P0[T[:, 1]] - P0[T[:, 0]], P0[T[:, 2]] - P0[T[:, 0]]), axis=1) / 2
        self.VA = np.zeros(len(P0))
        np.add.at(self.VA, T.ravel(), np.repeat(ta / 3, 3))
        self.recs = {r["id"]: read_records(r["tuck_path"]) if r["tuck_path"] else {} for r in rows}
        self.foot = {}
        for r in rows:
            d = dict(self.recs[r["id"]])
            for k, t in read_records(r["cover_path"]).items():
                if t > d.get(k, 0):
                    d[k] = t
            self.foot[r["id"]] = d
        if sc.keys is not None and len(sc.keys) == len(sc.isk):
            self.sp = wc.SkinPts(P0[sc.isk], self.N0[sc.isk])
        self.lay_cache = {}
        self.tests = []

    # ---- the garment tuck --
    def laid(self, A, outers):
        """A laid under `outers` (GarmentTuck.Field + Lay at rest), over A's vertices v (sorted): displacement D [v],
        alive [v] (on a kept face), kept faces (global), and the laid weights J, W [v] (blended toward the nearest outer
        vertex by the lay amount: GarmentTuck.Weights)."""
        key = (A, tuple(sorted(outers)))
        if key in self.lay_cache:
            return self.lay_cache[key]
        sc, P0 = self.sc, self.sc.P0
        v = self.pc[A]["v"]
        f = self.sp.field([self.foot[b] for b in outers], G_SPREAD)
        disp, t = self.sp.lay(P0[v], f)
        TA = self.pc[A]["T"]
        tl = t[np.searchsorted(v, TA)]
        kept = TA[~(tl >= T_GONE).all(1)]
        alive = np.zeros(len(v), bool)
        alive[np.searchsorted(v, kept.ravel())] = True
        s = amount(t)
        Jl, Wl = sc.J[v].copy(), sc.W[v].copy()
        mv = np.nonzero(s > 0)[0]
        if len(mv):
            ov = np.concatenate([self.pc[b]["v"] for b in outers])
            d, nb = cKDTree(P0[ov]).query(P0[v[mv]] + disp[mv], distance_upper_bound=wc.G_REACH)
            ok = np.isfinite(d)
            mv, nb = mv[ok], ov[nb[ok]]
            Jl[mv], Wl[mv] = blend_weights(sc.J[v[mv]], sc.W[v[mv]], sc.J[nb], sc.W[nb], s[mv])
        out = {"v": v, "D": disp, "alive": alive, "kept": kept, "J": Jl, "W": Wl,
               "moved": int((np.abs(disp).sum(1) > 0).sum()), "culled": int(len(TA) - len(kept))}
        self.lay_cache[key] = out
        return out

    def rest_footprint(self, O, D, Bid, skin=False):
        B, P0 = self.pc[Bid], self.sc.P0
        d0, _ = B["kdv"].query(O, distance_upper_bound=REACH + 0.01)
        keep = np.nonzero(np.isfinite(d0))[0]
        res = {"idx": [], "gap": [], "out": [], "hit": [], "bary": [], "cand": []}
        for a in range(0, len(keep), 1500):
            ii = keep[a:a + 1500]
            _, ci = B["kd"].query(O[ii], k=min(K0, len(B["T"])))
            ci = ci.reshape(len(ii), -1)
            t, fa, u, v = wc.cast(O[ii], D[ii], P0[B["T"][ci]])
            g, j, go = wc.signed_gap(t, fa, REACH)
            hit_f = ci[np.arange(len(ii)), j]
            u, v = u[np.arange(len(ii)), j], v[np.arange(len(ii)), j]
            if skin and self.byid[Bid]["slot"] in ENCLOSE_SLOTS:
                fl = np.nonzero((g < 0) | (go < 0))[0]
                if len(fl):
                    g2, j2, go2, u2, v2 = full_cast(O[ii[fl]], D[ii[fl]], P0[B["T"]], REACH)
                    g, go, hit_f, u, v = g.copy(), go.copy(), hit_f.copy(), u.copy(), v.copy()
                    g[fl], go[fl], hit_f[fl], u[fl], v[fl] = g2, go2, j2, u2, v2
            ok = np.isfinite(g)
            if not ok.any():
                continue
            rr = np.nonzero(ok)[0]
            hit = hit_f[rr]
            hp = O[ii[rr]] + D[ii[rr]] * g[rr, None]
            _, cand = B["kd"].query(hp, k=min(K, len(B["T"])))
            res["idx"].append(ii[rr])
            res["gap"].append(g[rr])
            res["out"].append(go[rr])
            res["hit"].append(hit)
            res["bary"].append(np.c_[1 - u[rr] - v[rr], u[rr], v[rr]])
            res["cand"].append(cand.reshape(len(rr), -1))
        if not res["idx"]:
            return None
        return {k: np.concatenate(v) for k, v in res.items()}

    # ---- tests --
    def add_skin(self, ids):
        sc, P0 = self.sc, self.sc.P0
        for i in ids:
            if i not in self.pc:
                continue
            tk, gone = skin_tuck(self.recs[i], sc.keys)
            sv = sc.isk[~gone]
            tsv = tk[~gone]
            O = P0[sv] - self.N0[sv] * tsv[:, None]
            fp = self.rest_footprint(O + self.N0[sv] * 1e-5, self.N0[sv], i, skin=True)
            if fp is None:
                continue
            x = {"A": "skin", "B": i, "kind": "skin", "fp": fp, "sup": support_of(self.byid[i]),
                 "tuck": tsv[fp["idx"]], "pts": sv[fp["idx"]], "dir": sv[fp["idx"]]}
            if self.confirm:
                # (wearcheck --confirm, armor 10 c2: a gap past the piece checked by its nearest face; a ray running along
                # a plate (her normal at the underbust crease, the arm's inner skin beside a cuirass) reads 15-30 mm past
                # it where the sample stands clear of every face)
                TB = self.pc[i]["T"]
                O0 = O[fp["idx"]]
                F0 = P0[TB[fp["cand"]]]
                n0 = np.cross(F0[:, :, 1] - F0[:, :, 0], F0[:, :, 2] - F0[:, :, 0])
                # (inner: a face whose normal opposes her outward normal at rest, the signed gap's entry face; wearcheck
                # took the faces the sample stood in front of at rest, which reads a point already through at rest as clear)
                x["inner0"] = (n0 * self.N0[sv[fp["idx"]]][:, None]).sum(2) < 0
                x["thick"] = float(np.median(fp["out"] - fp["gap"]))
                x["raw_min_out"] = np.full(len(fp["idx"]), np.inf)
                rr0 = np.nonzero(fp["gap"] < -0.0005)[0]
                if len(rr0):
                    g0, go0 = wc.confirm_gap(O0[rr0], F0[rr0], x["inner0"][rr0], x["thick"])
                    fp["gap"], fp["out"] = fp["gap"].copy(), fp["out"].copy()
                    fp["gap"][rr0], fp["out"][rr0] = g0, go0
            self._add(x)

    def add_pair(self, a, b, kind, tuck_ok=True):
        ra, rb = self.byid[a], self.byid[b]
        if a not in self.pc or b not in self.pc:
            return
        if ra["slot"] == rb["slot"] or rb["slot"] in ra["covers"] or ra["slot"] in rb["covers"]:
            return
        if ra["source"] != rb["source"] and (HANGS.get(ra["slot"]) == rb["slot"] or HANGS.get(rb["slot"]) == ra["slot"]):
            return
        order = self.order
        in_order = ra["slot"] in order and rb["slot"] in order
        diff = not (ra.get("outfit") and ra.get("outfit") == rb.get("outfit"))
        if tuck_ok and diff and in_order:
            orders = [(a, b)] if order.index(ra["slot"]) < order.index(rb["slot"]) else [(b, a)]
        else:
            orders = [(a, b)] if ra["layer"] < rb["layer"] else [(b, a)] if rb["layer"] < ra["layer"] else [(a, b), (b, a)]
        P0 = self.sc.P0
        found = []
        for A, B in orders:
            sA = self.pc[A]
            O = P0[sA["samples"]]
            D = self.N0[sA["near"]]
            lay = None
            if tuck_ok and over(self.byid[B], self.byid[A], order):
                lay = self.laid(A, [B])
                ls = np.searchsorted(lay["v"], sA["samples"])
                O = O + lay["D"][ls]
                O = np.where(lay["alive"][ls][:, None], O, 1e3)
            fp = self.rest_footprint(O, D, B)
            if fp is not None:
                found.append((A, B, fp, lay))
        if len(found) == 2:
            found = [max(found, key=lambda f: np.median(f[2]["gap"]))]
        for A, B, fp, lay in found:
            sup = next((support_of(self.byid[x]) for x in (A, B) if self.byid[x]["slot"] == "top"), (0.0, 0.0, 0.0))
            x = {"A": A, "B": B, "kind": kind, "fp": fp, "sup": sup, "pts": self.pc[A]["samples"][fp["idx"]],
                 "dir": self.pc[A]["near"][fp["idx"]], "laid": None, "rigid_inner": bool(self.byid[A].get("rigid"))}
            if lay is not None:
                loc = np.searchsorted(lay["v"], x["pts"])
                x["dA"] = lay["D"][loc]
                x["lJ"], x["lW"] = lay["J"][loc], lay["W"][loc]
                x["laid"] = {"moved": lay["moved"], "culled": lay["culled"]}
            self._add(x)

    def _add(self, x):
        if any(t["A"] == x["A"] and t["B"] == x["B"] for t in self.tests):
            return      # (warden's greaves, boots, bracers: in the warden set and the plate set alike)
        TB = self.pc[x["B"]]["T"]
        fp = x["fp"]
        x["hitv"] = TB[fp["hit"]]
        x["candv"] = TB[fp["cand"]]
        x["Sv"] = TB[np.unique(fp["cand"])]
        x["rest_out2"] = int((fp["out"] < -0.002).sum())
        x["rest_min_mm"] = float(fp["gap"].min() * 1000)
        x["per_clip"] = {}
        x["min"] = np.full(len(fp["idx"]), np.inf)
        x["min_out"] = np.full(len(fp["idx"]), np.inf)
        x["lost"] = x["seen"] = 0
        A = x["A"]
        x["area"] = self.VA[x["pts"]] if A == "skin" else np.maximum(self.VA[x["pts"]], self.grid ** 2)
        self.tests.append(x)

    # ---- the motion --
    def run(self, sources, log=print):
        """sources: [(clip name, frames())], frames() yielding (key frame, S [B, 4, 4], shape weights)."""
        sc = self.sc
        t0 = time.time()
        groups = sorted({x["sup"] for x in self.tests})
        for sup in groups:
            group = [x for x in self.tests if x["sup"] == sup]
            need = np.unique(np.concatenate([sc.ish] + [np.r_[x["pts"], x["hitv"].ravel(), x["candv"].ravel()] for x in group]))
            at = np.full(len(sc.P0), -1)
            at[need] = np.arange(len(need))
            sh_local = at[sc.ish]
            SvB = {B: np.unique(np.concatenate([x["Sv"] for x in group if x["B"] == B]), axis=0) for B in {x["B"] for x in group}}
            sub = sc.restrict(need)
            Jn, Wn = sc.J[need], sc.W[need]
            for x in group:     # (a laid test's points: their own shapes, then the lay)
                if "dA" in x:
                    x["_sub"] = sc.restrict(x["pts"])
            for cname, frames in sources:
                for f, S, w in frames():
                    w = dict(w)
                    w.update(support_weights(sup))
                    Pn = sc.rest(need, w, sub)
                    Pp = sc.lbs(S, Pn, Jn, Wn)
                    Np = np.zeros_like(Pp)
                    Np[sh_local] = sc.normals_sh(Pp[sh_local])
                    kd_frame = {}
                    for x in group:
                        self._measure(x, Pp, Np, at, S, w, SvB, kd_frame, cname, f)
                log(f"gear_wear: support {sup} {cname} ({time.time() - t0:.0f} s)")
        return time.time() - t0

    def _measure(self, x, Pp, Np, at, S, w, SvB, kd_frame, cname, f):
        sc = self.sc
        O = Pp[at[x["pts"]]]
        D = Np[at[x["dir"]]]
        if x["A"] == "skin":
            O = O - D * x["tuck"][:, None] + D * 1e-5
        elif "dA" in x:
            R = sc.rest(x["pts"], w, x["_sub"]) + x["dA"]
            O = sc.lbs(S, R, x["lJ"], x["lW"])
        H = Pp[at[x["hitv"]]]
        hp = (H * x["fp"]["bary"][:, :, None]).sum(1)
        fn = np.cross(H[:, 1] - H[:, 0], H[:, 2] - H[:, 0])
        den = (fn * D).sum(1)
        okd = np.abs(den) > 1e-14
        g = np.where(okd, ((hp - O) * fn).sum(1) / np.where(okd, den, 1), np.nan)
        lat = np.linalg.norm(np.cross(hp - O, D), axis=1)
        g = np.where((np.abs(g) < REACH_POSED) & (lat < DRIFT), g, np.nan)
        go = g.copy()
        r = np.nonzero(~(g > REFINE))[0]
        if len(r):
            t, fa, _, _ = wc.cast(O[r], D[r], Pp[at[x["candv"][r]]])
            gr, _, gor = wc.signed_gap(t, fa, REACH_POSED)
            lost = np.nonzero(~np.isfinite(gr))[0]
            if len(lost):
                if x["B"] not in kd_frame:
                    kd_frame[x["B"]] = cKDTree(Pp[at[SvB[x["B"]]]].mean(1))
                Sv = SvB[x["B"]]
                _, ii = kd_frame[x["B"]].query(O[r[lost]], k=min(K0, len(Sv)))
                t, fa, _, _ = wc.cast(O[r[lost]], D[r[lost]], Pp[at[Sv[ii.reshape(len(lost), -1)]]])
                gl, _, gol = wc.signed_gap(t, fa, REACH_POSED)
                gr[lost], gor[lost] = gl, gol
                x["lost"] += int((~np.isfinite(gl)).sum())
            if x["A"] == "skin" and self.byid[x["B"]]["slot"] in ENCLOSE_SLOTS:
                fl = np.nonzero((gr < 0) | (gor < 0))[0]
                if len(fl):
                    Sv = SvB[x["B"]]
                    g2, _, go2, _, _ = full_cast(O[r[fl]], D[r[fl]], Pp[at[Sv]], REACH_POSED)
                    gr, gor = gr.copy(), gor.copy()
                    gr[fl], gor[fl] = g2, go2
            g[r], go[r] = gr, gor
        if "inner0" in x:
            x["raw_min_out"] = np.minimum(x["raw_min_out"], np.where(np.isfinite(go), go, np.inf))
            rc = np.nonzero(g < -0.0005)[0]
            if len(rc):
                g[rc], go[rc] = wc.confirm_gap(O[rc], Pp[at[x["candv"][rc]]], x["inner0"][rc], x["thick"])
        x["seen"] += len(g)
        gg = np.where(np.isfinite(g), g, np.inf)
        go_ = np.where(np.isfinite(go), go, np.inf)
        x["min"] = np.minimum(x["min"], gg)
        x["min_out"] = np.minimum(x["min_out"], go_)
        pc = x["per_clip"].setdefault(cname, {"out": np.full(len(gg), np.inf), "worst": np.inf, "frame": -1, "pt": -1,
                                               "worst_in": np.inf})
        pc["out"] = np.minimum(pc["out"], go_)
        k = int(go_.argmin())
        if go_[k] < pc["worst"]:
            pc["worst"], pc["frame"], pc["pt"] = float(go_[k]), f, k
        pc["worst_in"] = min(pc["worst_in"], float(gg.min()))
        fr = pc.setdefault("fr", {d: [0.0, -1] for d in FRAME_MM})      # (the worst single frame: area past each depth)
        for d in FRAME_MM:
            a_ = float(x["area"][go_ < -d / 1000.0].sum())
            if a_ > fr[d][0]:
                fr[d] = [a_, f]

    # ---- every slot shows --
    def show(self, look):
        """At rest, each piece of `look` laid under the look's pieces over it; its visible area share."""
        sc, P0 = self.sc, self.sc.P0
        ids = [i for i in look.values() if i in self.pc]
        pos, kept = {}, {}
        for i in ids:
            outs = [o for o in ids if over(self.byid[o], self.byid[i], self.order)]
            if outs:
                lay = self.laid(i, outs)
                kept[i] = lay["kept"]
                pos[i] = P0[kept[i]] + lay["D"][np.searchsorted(lay["v"], kept[i])]
            else:
                kept[i] = self.pc[i]["T"]
                pos[i] = P0[kept[i]]
        res = {}
        for i in ids:
            others = [o for o in ids if o != i]
            Fo = np.concatenate([pos[o] for o in others]) if others else np.zeros((0, 3, 3))
            Tm = kept[i]
            if not len(Tm):
                res[i] = {"area_mm2": 0.0, "visible_mm2": 0.0, "share": 0.0, "fail": True, "why": "every face removed by the lay"}
                continue
            Fi = pos[i]
            c = Fi.mean(1)
            a = np.linalg.norm(np.cross(Fi[:, 1] - Fi[:, 0], Fi[:, 2] - Fi[:, 0]), axis=1) / 2
            _, first, inv = np.unique(np.floor(c / SHOW_GRID).astype(np.int64), axis=0, return_index=True, return_inverse=True)
            area = np.bincount(np.asarray(inv).ravel(), a)
            O = c[first]
            _, nn = self.kd_sh.query(O)
            Nn = self.N0[sc.ish[nn]]
            vis = np.ones(len(O), bool)
            if len(Fo):
                vis = self._visible(O, Nn, Fo)
            tot, sv = float(area.sum() * 1e6), float(area[vis].sum() * 1e6)
            res[i] = {"area_mm2": round(tot, 1), "visible_mm2": round(sv, 1), "share": round(sv / max(tot, 1e-9), 4),
                      "fail": bool(sv / max(tot, 1e-9) < SHOW_MIN)}
        return res

    @staticmethod
    def _visible(O, N, Fo, kq=40):
        kd = cKDTree(Fo.mean(1))
        # (directions: her normal, and four SHOW_TILT off it)
        tA = np.cross(N, np.where(np.abs(N[:, :1]) < 0.9, [[1.0, 0, 0]], [[0, 1.0, 0]]))
        tA /= np.linalg.norm(tA, axis=1, keepdims=True)
        tB = np.cross(N, tA)
        c, s = np.cos(np.radians(SHOW_TILT)), np.sin(np.radians(SHOW_TILT))
        dirs = [N] + [c * N + s * sg * tt for tt in (tA, tB) for sg in (1, -1)]
        # (a sample with no other piece's face within the ray's length is seen outright)
        d, _ = kd.query(O, distance_upper_bound=SHOW_RAY + 0.01)
        vis = ~np.isfinite(d)
        k = min(kq, len(Fo))
        for D in dirs:
            todo = np.nonzero(~vis)[0]
            for a0 in range(0, len(todo), 2000):
                ii = todo[a0:a0 + 2000]
                Oi, Di = O[ii] + D[ii] * 5e-4, D[ii]
                cand = [kd.query(Oi + Di * h, k=k)[1].reshape(len(ii), -1) for h in (0.0, 0.02, 0.045, 0.07)]
                cand = np.concatenate(cand, 1)
                t, _, _, _ = wc.cast(Oi, Di, Fo[cand])
                blocked = ((t > 0) & (t < SHOW_RAY)).any(1)
                vis[ii[~blocked]] = True
        return vis

    # ---- report --
    def report(self, clips, region_of, out_mm=0.0, samples=False):
        """out_mm > 0 adds "outd_mm2" (per test and per clip): as out2 with that depth in place of 2 mm. samples: each
        skin test carries "_samples" (rest position mm, deepest out per clip mm; 999 = never measured)."""
        out, worst = [], []
        for x in self.tests:
            A, B = x["A"], x["B"]
            m, mo, ar = x["min"], x["min_out"], x["area"]
            fin = np.isfinite(m)
            e = {"A": A, "B": B, "kind": x["kind"],
                 "slots": f"{'skin' if A == 'skin' else self.byid[A]['slot']}->{self.byid[B]['slot']}",
                 "support": list(x["sup"]), "footprint_mm2": round(float(ar.sum() * 1e6), 1),
                 "worst_in_mm": round(float(-m[fin].min() * 1000), 2) if fin.any() else None,
                 "out_worst_mm": round(float(-mo[np.isfinite(mo)].min() * 1000), 2) if np.isfinite(mo).any() else None,
                 "out2_n": int((mo < -0.002).sum()), "out2_mm2": round(float(ar[mo < -0.002].sum() * 1e6), 1),
                 "in2_mm2": round(float(ar[m < -0.002].sum() * 1e6), 1),
                 "rest_out2_n": x["rest_out2"], "rest_gap_min_mm": round(x["rest_min_mm"], 2),
                 "lost_share": round(x["lost"] / max(x["seen"], 1), 4), "laid": x.get("laid"),
                 "rigid_inner": x.get("rigid_inner", False), "per_clip": {}, "confirm": "inner0" in x,
                 "_o2": np.nonzero(mo < -0.002)[0].tolist(), "_i2": np.nonzero(m < -0.002)[0].tolist(),
                 "_area": (ar * 1e6).round(3).tolist()}
            if "raw_min_out" in x:
                rm = x["raw_min_out"]
                e["raw_out2_mm2"] = round(float(ar[rm < -0.002].sum() * 1e6), 1)
                e["raw_out_worst_mm"] = round(float(-rm[np.isfinite(rm)].min() * 1000), 2) if np.isfinite(rm).any() else None
            e["_vw"] = view_sets({c: pc["out"] for c, pc in x["per_clip"].items()}, len(mo))
            e["views"] = {k: round(float(ar[v].sum() * 1e6), 1) for k, v in e["_vw"].items()}
            if out_mm > 0:
                e["outd_mm"], e["_od"] = out_mm, np.nonzero(mo < -out_mm / 1000.0)[0].tolist()
                e["outd_mm2"] = round(float(ar[e["_od"]].sum() * 1e6), 1)
            for c, pc in x["per_clip"].items():
                o2 = pc["out"] < -0.002
                pt = x["pts"][pc["pt"]] if pc["pt"] >= 0 else -1
                row = {"out2_n": int(o2.sum()), "out2_mm2": round(float(ar[o2].sum() * 1e6), 1),
                       "out_worst_mm": round(float(-pc["worst"] * 1000), 2) if np.isfinite(pc["worst"]) else None,
                       "in_worst_mm": round(float(-pc["worst_in"] * 1000), 2) if np.isfinite(pc["worst_in"]) else None,
                       "frame": pc["frame"], "region": region_of(pt) if pt >= 0 else "",
                       "frame_mm2": {f"{d:g}": round(pc["fr"][d][0] * 1e6, 1) for d in FRAME_MM},
                       "frame_at": {f"{d:g}": pc["fr"][d][1] for d in FRAME_MM}}
                if out_mm > 0:
                    row["outd_mm2"] = round(float(ar[pc["out"] < -out_mm / 1000.0].sum() * 1e6), 1)
                e["per_clip"][c] = row
                if samples and A == "skin":
                    sm = e.setdefault("_samples", {"pos": (self.sc.P0[x["pts"]] * 1000).round(2).tolist(), "clips": {}})
                    sm["clips"][c] = np.where(np.isfinite(pc["out"]), pc["out"] * 1000, 999.0).round(2).tolist()
                if row["out2_n"]:
                    worst.append({"clip": c, "test": f"{A} under {B}" if A != "skin" else f"skin under {B}",
                                  "kind": x["kind"], **{k: row[k] for k in ("out2_mm2", "out2_n", "out_worst_mm", "frame", "region")}})
            e["frames"] = frame_views(e["per_clip"])
            out.append(e)
        out.sort(key=lambda e: (-e["out2_mm2"], -(e["out_worst_mm"] or -99)))
        worst.sort(key=lambda r: (-r["out2_mm2"], -(r["out_worst_mm"] or 0)))
        return out, worst


REGIONS = (("breast", "breast"), ("pec", "chest"), ("spine_0", "torso"), ("pelvis", "hips"), ("glute", "buttock"),
           ("thigh", "thigh"), ("calf", "calf"), ("knee", "knee"), ("foot", "foot"), ("ball", "toes"),
           ("clavicle", "shoulder"), ("delt", "shoulder"), ("scap", "shoulder blade"), ("trap", "neck/trap"),
           ("upperarm", "upper arm"), ("lowerarm", "forearm"), ("elbow", "elbow"), ("hand", "hand"), ("neck", "neck"),
           ("Head", "head"), ("lat", "flank"), ("belly", "belly"))


def region_name(bone):
    side = " L" if bone.endswith("_l") else " R" if bone.endswith("_r") else ""
    for k, nm in REGIONS:
        if bone.startswith(k):
            return f"{nm}{side} ({bone})"
    return bone


# ---------------------------------------------------------------------- main --
def plan(ck, tests, only=None):
    byid = ck.byid
    ps = proof_sets(byid)
    sel = lambda ids: [i for i in ids if (not only or i in only) and i in ck.pc]  # noqa: E731
    looks = []
    if "skin" in tests:
        ck.add_skin(sel(list(byid)))
    if "control" in tests:
        for cal in CALLINGS:
            ids = sel([i for i, r in byid.items() if r.get("outfit") == cal])
            for a in range(len(ids)):
                for b in ids[a + 1:]:
                    ck.add_pair(ids[a], b, "control", tuck_ok=False)
        ids = sel(ps["plate"])
        for a in range(len(ids)):
            for b in ids[a + 1:]:
                ck.add_pair(ids[a], b, "control")
    if "mixed" in tests:
        names = [s for s in PROOF]
        for si in range(len(names)):
            for sj in range(si + 1, len(names)):
                for a in sel(ps[names[si]]):
                    for b in sel(ps[names[sj]]):
                        if a != b:
                            ck.add_pair(a, b, "mixed")
    if "show" in tests:
        for s in PROOF:
            looks.append({"name": f"{s} set", "look": {byid[i]["slot"]: i for i in ps[s] if i in ck.pc}, "dropped": []})
        for s in PROOF:
            for t in PROOF:
                if s == t:
                    continue
                for p in ps[t]:
                    if p not in ck.pc:
                        continue
                    lk, dr = look_of(ps[s], p, byid)
                    looks.append({"name": f"{s} set + {p}", "look": lk, "dropped": dr})
    return looks


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--gear", default=GEAR)
    ap.add_argument("--body", default=None, help="the body folder (default: godot/art/people/<gear_index body>)")
    ap.add_argument("--clips", default=CLIPS)
    ap.add_argument("--pieces", default="")
    ap.add_argument("--tests", default="skin,control,mixed,show")
    ap.add_argument("--step", type=int, default=2)
    ap.add_argument("--grid", type=float, default=2.5)
    ap.add_argument("--no-confirm", action="store_true", help="skin tests: the raw ray gap only (no nearest-face check)")
    ap.add_argument("--jobs", type=int, default=1, help="clips split over this many processes")
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--out-mm", type=float, default=0.0, help="also count the through deeper than this many mm "
                    "(outd_mm2, per test and per clip); 0: only the 2 mm count and the views")
    ap.add_argument("--samples", action="store_true", help="also write <out>/samples_<piece>.npz per skin test: pos "
                    "(rest, mm), area (mm^2), clips, out (clip x sample: deepest out, mm; 999 = never measured)")
    ap.add_argument("--part", default="", help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    t_start = time.time()
    clips = clip_files(a.clips)
    if a.jobs > 1 and not a.part:
        return fan_out(a, argv if argv is not None else sys.argv[1:], clips, t_start)
    ix, rows = load_rows(a.gear)
    body_dir = a.body or os.path.join(REPO, "godot", "art", "people", ix["body"])
    only = set(a.pieces.split(",")) - {""} or None
    tests = set(a.tests.split(","))
    order = json.load(open(os.path.join(HERE, "slot_map.json"), encoding="utf-8"))["order"]
    sc = build_scene(body_dir, rows, only)
    ck = Check(sc, rows, order, a.grid / 1000, not a.no_confirm)
    looks = plan(ck, tests, only)
    t_rest = time.time() - t_start
    print(f"gear_wear: {len(rows)} rows, {len(ck.tests)} tests, {len(looks)} looks, {len(clips)} clips ({t_rest:.0f} s to set up)")
    shows = []
    if not a.part:
        for lk in looks:
            r = ck.show(lk["look"])
            shows.append({**lk, "pieces": r, "fails": [i for i, v in r.items() if v["fail"]]})
    t_motion = ck.run(dump_sources(sc, clips, a.step))
    names = sc.poser.names
    dom = np.array([names[j] for j in sc.J[np.arange(len(sc.P0)), sc.W.argmax(1)]])
    pairs, worst = ck.report([os.path.basename(c) for c in clips], lambda pt: region_name(dom[pt]), a.out_mm, a.samples)
    if a.part:
        json.dump({"pairs": pairs, "worst": worst}, open(a.part, "w"))
        return
    write(a, clips, pairs, worst, shows, ck, time.time() - t_start, t_motion)


def fan_out(a, argv, clips, t_start):
    """--jobs N: the clips dealt to N processes (each sets up the same tests), their numbers merged."""
    import subprocess
    import shutil
    tmp = os.path.join(a.out, "_parts")     # (each part's numbers and log; removed after a clean merge)
    os.makedirs(tmp, exist_ok=True)
    base = [x for i, x in enumerate(argv) if not (x == "--jobs" or (i and argv[i - 1] == "--jobs") or x == "--clips"
                                                     or (i and argv[i - 1] == "--clips"))]
    deal = [clips[k::a.jobs] for k in range(a.jobs)]
    procs = []
    for k, cs in enumerate(deal):
        if not cs:
            continue
        part = os.path.join(tmp, f"part{k}.json")
        cmd = [sys.executable, "-u", os.path.abspath(__file__), *base, "--clips", ",".join(cs), "--part", part]
        procs.append((part, subprocess.Popen(cmd, stdout=open(part + ".log", "w"), stderr=subprocess.STDOUT)))
    # (the show test once, here, while the parts run)
    ix, rows = load_rows(a.gear)
    body_dir = a.body or os.path.join(REPO, "godot", "art", "people", ix["body"])
    only = set(a.pieces.split(",")) - {""} or None
    order = json.load(open(os.path.join(HERE, "slot_map.json"), encoding="utf-8"))["order"]
    shows = []
    ck = None
    if "show" in a.tests.split(","):
        sc = build_scene(body_dir, rows, only)
        ck = Check(sc, rows, order, a.grid / 1000, not a.no_confirm)
        looks = plan(ck, {"show"}, only)
        for lk in looks:
            r = ck.show(lk["look"])
            shows.append({**lk, "pieces": r, "fails": [i for i, v in r.items() if v["fail"]]})
        print(f"gear_wear: {len(shows)} looks shown ({time.time() - t_start:.0f} s)", flush=True)
    for part, pr in procs:
        if pr.wait() != 0:
            raise SystemExit(f"gear_wear: a part failed: {open(part + '.log').read()[-3000:]}")
    parts = [json.load(open(p)) for p, _ in procs]
    shutil.rmtree(tmp, ignore_errors=True)
    pairs = merge(parts)
    worst = sorted([w for p in parts for w in p["worst"]], key=lambda r: (-r["out2_mm2"], -(r["out_worst_mm"] or 0)))
    write(a, clips, pairs, worst, shows, ck, time.time() - t_start, None)


def merge(parts):
    """Tests' numbers over the parts' clips: per clip as each part had it; out2 over all clips the union of the parts'
    samples (every part set up the same tests, so sample rows agree)."""
    by = {}
    for p in parts:
        for e in p["pairs"]:
            k = (e["A"], e["B"])
            if k not in by:
                by[k] = dict(e)
                by[k]["per_clip"] = dict(e["per_clip"])
                by[k]["_parts"] = [e]
            else:
                b = by[k]
                b["per_clip"].update(e["per_clip"])
                b["_parts"].append(e)
                if "_samples" in e:
                    b["_samples"] = {"pos": e["_samples"]["pos"], "clips": {**b["_samples"]["clips"], **e["_samples"]["clips"]}}
                for f in ("worst_in_mm", "out_worst_mm", "raw_out_worst_mm", "raw_out2_mm2"):
                    if e.get(f) is not None and (b.get(f) is None or e[f] > b[f]):
                        b[f] = e[f]
    out = []
    for b in by.values():
        ps = b.pop("_parts")
        ar = np.array(ps[0]["_area"])
        o2 = sorted(set().union(*[e["_o2"] for e in ps]))
        i2 = sorted(set().union(*[e["_i2"] for e in ps]))
        b["out2_n"], b["out2_mm2"] = len(o2), round(float(ar[o2].sum()), 1)
        b["in2_mm2"] = round(float(ar[i2].sum()), 1)
        if "_vw" in ps[0]:
            b["views"] = {k: round(float(ar[sorted(set().union(*[e["_vw"][k] for e in ps]))].sum()), 1) for k in ps[0]["_vw"]}
        if "_od" in ps[0]:
            b["outd_mm2"] = round(float(ar[sorted(set().union(*[e["_od"] for e in ps]))].sum()), 1)
        b["lost_share"] = round(float(np.mean([e["lost_share"] for e in ps])), 4)
        b["frames"] = frame_views(b["per_clip"])
        out.append(b)
    out.sort(key=lambda e: (-e["out2_mm2"], -(e["out_worst_mm"] or -99)))
    return out


def write(a, clips, pairs, worst, shows, ck, took, t_motion):
    os.makedirs(a.out, exist_ok=True)
    for e in pairs:
        sm = e.pop("_samples", None)
        if sm:
            cs = sorted(sm["clips"])
            np.savez_compressed(os.path.join(a.out, f"samples_{e['B']}.npz"), pos=np.array(sm["pos"]),
                                area=np.array(e["_area"]), clips=np.array(cs), out=np.array([sm["clips"][c] for c in cs]))
        for k in ("_o2", "_i2", "_area", "_vw", "_od"):
            e.pop(k, None)
    slots_filled = set()
    if ck is not None:
        ps = proof_sets(ck.byid)
        for s in PROOF:
            for i in ps[s]:
                slots_filled.update(ck.byid[i]["covers"])
    empty = [s for s in VISUAL_SLOTS if s not in slots_filled] if ck is not None else None
    cn = [os.path.splitext(os.path.basename(c))[0] for c in clips]
    meta = {"gear": os.path.relpath(a.gear, REPO), "clips": [os.path.basename(c) for c in clips], "step": a.step,
            "views": {"depth_mm": VIEWS, "broken": [c for c in cn if c in BROKEN],
                      **{v: [c for c in cn if clip_view(c) == v] for v in VIEWS}},
            "grid_mm": a.grid, "seconds": round(took), "motion_seconds": round(t_motion) if t_motion else None,
            "jobs": a.jobs, "tests": a.tests, "pieces": a.pieces or "all",
            "note": "out_*: past the piece's OUTER face (what shows); in_*: past its inner face. out2: samples ever "
                    "past by more than 2 mm, as area (mm^2). per_clip: that clip alone. Garment tuck as HerWear lays it "
                    "(mixed, and the plate set's own pairs). Not driven: live springs, face shapes, cloth."}
    totals = {}
    for e in pairs:
        t = totals.setdefault(e["kind"], {"tests": 0, "out2_mm2": 0.0, "with_out2": 0})
        t["tests"] += 1
        t["out2_mm2"] = round(t["out2_mm2"] + e["out2_mm2"], 1)
        t["with_out2"] += int(e["out2_mm2"] > 0)
    json.dump({"meta": meta, "totals": totals, "tests": pairs, "worst": worst, "show": shows, "empty_slots": empty},
              open(os.path.join(a.out, "gear_wear.json"), "w"), indent=1)
    L = [f"# gear_wear: {meta['gear']}", "",
         f"{len(clips)} clips, step {a.step}, grid {a.grid} mm, {len(pairs)} tests, {took:.0f} s. Garment tuck as "
         "HerWear lays it. OUT>2: her skin / the inner piece past the outer face by more than 2 mm (what shows), as area.", "",
         "| kind | tests | with OUT>2 | OUT>2 mm^2 (all clips) |", "|---|---:|---:|---:|"]
    for k, t in sorted(totals.items()):
        L.append(f"| {k} | {t['tests']} | {t['with_out2']} | {t['out2_mm2']:.0f} |")
    L += ["", "## Worst 20 (clip, test)", "", "| clip | test | kind | OUT>2 mm^2 | worst mm | frame | region |",
          "|---|---|---|---:|---:|---:|---|"]
    for w in worst[:20]:
        L.append(f"| {w['clip']} | {w['test']} | {w['kind']} | {w['out2_mm2']:.0f} | {w['out_worst_mm']} | {w['frame']} | {w['region']} |")
    L += ["", "## Where it shows", "",
          "close: through over " + f"{VIEWS['close']:g} mm in the town / idle / look / talk clips ({len(meta['views']['close'])}); "
          f"play: over {VIEWS['play']:g} mm in the others ({len(meta['views']['play'])}); ex: without {', '.join(BROKEN)}. mm^2.", "",
          "| test | close | play | play ex |", "|---|---:|---:|---:|"]
    for e in sorted(pairs, key=lambda e: -(e["views"]["close"] + e["views"]["play"]))[:20]:
        if e["views"]["close"] + e["views"]["play"] > 0:
            L.append(f"| {e['A']} under {e['B']} | {e['views']['close']:.0f} | {e['views']['play']:.0f} | {e['views']['play_ex']:.0f} |")
    L += ["", "## What one frame shows", "",
          "The worst single frame's through area (mm^2) past each depth, its clip and frame: close views at "
          f"{VIEWS['close']:g} mm, play (ex) at 3 and {VIEWS['play']:g} mm. One play pixel is 169 mm^2.", "",
          "| test | close 2 mm | play 3 mm | play 6 mm |", "|---|---|---|---|"]
    cell = lambda r: f"{r['mm2']:.0f} ({r['clip']} f{r['frame']})" if r["mm2"] > 0 else "0"
    for e in sorted(pairs, key=lambda e: -e.get("frames", {}).get("play_ex", {}).get("6", {}).get("mm2", 0))[:20]:
        fv = e.get("frames")
        if fv and (fv["close_ex"]["2"]["mm2"] + fv["play_ex"]["3"]["mm2"]) > 0:
            L.append(f"| {e['A']} under {e['B']} | {cell(fv['close_ex']['2'])} | {cell(fv['play_ex']['3'])} | {cell(fv['play_ex']['6'])} |")
    if shows:
        L += ["", "## Every slot shows (at rest)", ""]
        fails = [(s["name"], i, s["pieces"][i]) for s in shows for i in s["fails"]]
        L.append(f"{len(shows)} looks; {len(fails)} piece(s) under {SHOW_MIN:.0%} visible." + (" Slots no proof set fills: " + ", ".join(empty) + "." if empty else ""))
        for nm, i, v in fails:
            L.append(f"- FAIL {nm}: {i} {v['share']:.1%} visible ({v['visible_mm2']:.0f} of {v['area_mm2']:.0f} mm^2)")
        drops = [(s["name"], d) for s in shows for d in s["dropped"]]
        if drops:
            L += ["", "Dropped by Look's rules (hidden by a cover or a hang):", ""]
            L += [f"- {nm}: {i} ({why})" for nm, (i, why) in drops]
    open(os.path.join(a.out, "gear_wear.md"), "w").write("\n".join(L) + "\n")
    print(f"gear_wear: {len(pairs)} tests in {took:.0f} s -> {a.out}")


if __name__ == "__main__":
    main()
