#!/usr/bin/env python
"""P1 E: her body's maps on OUR UVs (topo_uv.py), baked from the built body and A's shipped body, as a build step
(build_topo.py stage 7; numpy + embree rays, no Blender: the build stays one command without a Blender turn, the
same transfer runs for any body on our topology, and every texel's source is a ray we can count and check).

    python tools/body/topo_bake.py <build_out> <maps_dir> [--size 2048]    (build_topo runs it when the spec asks)

Carried from A (godot/art/people/heroine.glb, node Heroine: primitive 0 "Material_0.001" paint + normal, rough 0.8;
primitive 1 "skin_graft" its own paint + normal, rough 0.5; and the graft's freckles layer People.cs puts on it,
godot/art/people/head_tex/heroine_freckles_graft.png), A posed into our build's rest (her_target.target, world=True:
the surface her fit was made to, B within ~1.7 mm of it):
  albedo.png      A's paint at the point each texel's body point lands on (a ray along our normal, both ways, 6 mm;
                  else the closest point); the left and right halves averaged (the UVs mirror: one texel, two points)
  normal.png      A's SHADING normal (its map decoded in its own tangent frame) re-expressed in OURS (the TANGENT the
                  glb carries; glTF convention, +Y = up the texture), so B lights as A does over B's own shape
  roughness.png   glTF metallicRoughness (G = A's roughness, B = 0 metal)
  freckles.png    the graft's freckles layer (RGBA as People.cs reads it), 0 off the graft
L1's data maps (B3's inputs, docs/design/look/her_paint_regions.json via base/her_paint_regions.json):
  region_id.png   8-bit: the region id (1-13; 0 off the islands, the gutters filled from the nearest island)
  ao.png          ambient occlusion on our built body with her head (32 cosine rays, 25 cm), white = open
  curvature.png   mean curvature of our surface, 0.5 + H * 1 cm (H in 1/m; convex brighter), clamped
  thickness.png   how thin she is there: 1 - d / 6 cm (d the mean distance through her body along 8 rays inside a
                  30 degree cone against the normal), white = thin
  form_normal.png A's GEOMETRIC normal (no map) in our tangent frame: A's big forms against ours
  zones.png       R warm, G cool (her_paint_regions.json's zones for regions 4-13; none of them cool), smooth masks
  zones.json      each zone: region, its centre (our vertex), radius, rule
Gutters: every map's empty texels take the nearest island texel (no seam bleeds at any mip).
"""
import argparse
import json
import os
import sys
import time

import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import ray  # noqa: E402
import topo_uv as tu  # noqa: E402
from gl import Glb, weld  # noqa: E402

A_PATH = os.path.join(REPO, "godot", "art", "people", "heroine.glb")
FRECKLES = os.path.join(REPO, "godot", "art", "people", "head_tex", "heroine_freckles_graft.png")
ROUGH = {0: 0.8, 1: 0.5}          # A's primitives' roughnessFactor (no roughness texture)
MIRROR = np.array([-1.0, 1, 1])
VERSION = "bake1"


def U(v):
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-20)


# --------------------------------------------------------------------------------------------- frames --
def tangent_frames(P, N, UV, T):
    """Per vertex (tangent xyz, w) from the UVs (glTF: v down): T along +u, the bitangent up the texture (-v); w the
    handedness so that cross(N, T) * w is that bitangent (glTF's TANGENT rule). Per-face gradients summed by area."""
    e1, e2 = P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]
    d1, d2 = UV[T[:, 1]] - UV[T[:, 0]], UV[T[:, 2]] - UV[T[:, 0]]
    det = d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]
    r = 1.0 / np.where(np.abs(det) < 1e-20, 1e-20, det)
    dPu = (e1 * d2[:, 1:2] - e2 * d1[:, 1:2]) * r[:, None]
    dPv = (e2 * d1[:, 0:1] - e1 * d2[:, 0:1]) * r[:, None]
    area = 0.5 * np.linalg.norm(np.cross(e1, e2), axis=1)[:, None]
    Tu = np.zeros_like(P)
    Bv = np.zeros_like(P)
    for k in range(3):
        np.add.at(Tu, T[:, k], U(dPu) * area)
        np.add.at(Bv, T[:, k], U(-dPv) * area)
    Tt = U(Tu - N * (Tu * N).sum(1, keepdims=True))
    w = np.where((np.cross(N, Tt) * Bv).sum(1) < 0, -1.0, 1.0)
    return Tt, w


# ----------------------------------------------------------------------------------------------- A side --
class Source:
    """A's body posed into our build's rest, unwelded (its UVs), with its textures and frames."""

    def __init__(self, build_glb):
        import her_target
        t = her_target.target(build_glb, A_PATH, world=True)
        A = Glb(A_PATH)
        m = A.mesh("Heroine")
        first, inv = her_target.weld(m.P)
        Tw = inv[m.T]
        Tw = Tw[(Tw[:, 0] != Tw[:, 1]) & (Tw[:, 1] != Tw[:, 2]) & (Tw[:, 0] != Tw[:, 2])]
        assert len(Tw) == len(t["T"]) and (Tw == t["T"]).all(), "A's welded order differs from her_target's"
        self.P = t["P"][inv].astype(np.float64)
        self.T = m.T
        self.UV = m.UV.astype(np.float64)
        self.prim = m.prim_of
        fn = np.cross(self.P[self.T[:, 1]] - self.P[self.T[:, 0]], self.P[self.T[:, 2]] - self.P[self.T[:, 0]])
        self.N = t["N"][inv]                            # welded (smooth across A's UV seams)
        self.Tan, self.w = tangent_frames(self.P, self.N, self.UV, self.T)
        self.scene = ray.scene(self.P, self.T)
        import surfdist
        self.surf = surfdist.Surface(self.P, self.T)
        imgs = {}
        b = A.g.buffers[0]
        import io
        for i, im in enumerate(A.js["images"]):
            v = A.js["bufferViews"][im["bufferView"]]
            o = v.get("byteOffset", 0)
            imgs[i] = np.asarray(Image.open(io.BytesIO(b[o:o + v["byteLength"]])).convert("RGB"), np.float64) / 255
        mats = A.js["materials"]
        prims = A.js["meshes"][A.js["nodes"][[n.get("name") for n in A.js["nodes"]].index("Heroine")]["mesh"]]["primitives"]
        self.tex = {}
        for pi, pr in enumerate(prims):
            mt = mats[pr["material"]]
            src = lambda key: A.js["textures"][key["index"]]["source"]          # noqa: E731
            self.tex[pi] = {"albedo": imgs[src(mt["pbrMetallicRoughness"]["baseColorTexture"])],
                            "normal": imgs[src(mt["normalTexture"])] if "normalTexture" in mt else None,
                            "rough": float(mt["pbrMetallicRoughness"].get("roughnessFactor", 1.0)),
                            "name": mt.get("name")}
        self.freckles = (np.asarray(Image.open(FRECKLES).convert("RGBA"), np.float64) / 255
                         if os.path.exists(FRECKLES) else None)
        self.fit_note = {"surface": "her_target.target(world=True)", "points": int(len(self.P)),
                         "materials": [self.tex[k]["name"] for k in sorted(self.tex)]}

    def project(self, X, Nx, reach=0.006):
        """(tri, bary, dist) of each point on A: the nearer of the rays along +/-N within `reach`, else the closest."""
        n = len(X)
        best_t = np.full(n, -1, np.int64)
        best_d = np.full(n, np.inf)
        for sgn in (1.0, -1.0):
            org = X - sgn * Nx * reach
            pid, tf = ray.hits(self.scene, org, sgn * Nx)
            d = np.abs(tf - reach)
            ok = (pid >= 0) & (tf <= 2 * reach) & (d < best_d)
            best_t[ok], best_d[ok] = pid[ok], d[ok]
        miss = best_t < 0
        if miss.any():
            _, _, t, d = self.surf.closest(X[miss], k=16)
            best_t[miss], best_d[miss] = t, d
        a, b, c = (self.P[self.T[best_t, k]] for k in range(3))
        Xp = X if True else None
        w = tu.bary(Xp, a, b, c)
        w = np.clip(w, 0, None)
        w /= w.sum(1, keepdims=True)
        return best_t, w, best_d, miss

    def sample(self, t, w):
        """A's albedo, shading normal (object space), geometric normal, roughness and freckles at (tri, bary)."""
        Tv = self.T[t]
        uv = (w[:, :, None] * self.UV[Tv]).sum(1)
        pr = self.prim[t]
        alb = np.zeros((len(t), 3))
        nts = np.zeros((len(t), 3))
        nts[:, 2] = 1
        rough = np.zeros(len(t))
        for pi, tx in self.tex.items():
            m = pr == pi
            if not m.any():
                continue
            alb[m] = bilinear(tx["albedo"], uv[m])
            if tx["normal"] is not None:
                nts[m] = bilinear(tx["normal"], uv[m]) * 2 - 1
            rough[m] = tx["rough"]
        Ng = U((w[:, :, None] * self.N[Tv]).sum(1))
        Ta = (w[:, :, None] * self.Tan[Tv]).sum(1)
        Ta = U(Ta - Ng * (Ta * Ng).sum(1, keepdims=True))
        wa = np.sign((w * self.w[Tv]).sum(1))
        Ba = np.cross(Ng, Ta) * wa[:, None]
        nts = U(nts)
        Ns = U(nts[:, :1] * Ta + nts[:, 1:2] * Ba + nts[:, 2:] * Ng)
        fr = np.zeros((len(t), 4))
        if self.freckles is not None:
            g = pr == 1
            fr[g] = bilinear(self.freckles, uv[g])
        return {"albedo": alb, "normal": Ns, "form": Ng, "rough": rough, "freckles": fr, "graft": pr == 1}


def bilinear(img, uv):
    h, w = img.shape[:2]
    x = np.clip(uv[:, 0] * w - 0.5, 0, w - 1.001)
    y = np.clip(uv[:, 1] * h - 0.5, 0, h - 1.001)
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    fx, fy = (x - x0)[:, None], (y - y0)[:, None]
    x1, y1 = np.minimum(x0 + 1, w - 1), np.minimum(y0 + 1, h - 1)
    return (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x1] * fx * (1 - fy) + img[y1, x0] * (1 - fx) * fy +
            img[y1, x1] * fx * fy)


# ------------------------------------------------------------------------------------------------ texels --
def texels(uvd, size):
    """Every texel centre's left triangle (index into uvd's left triangles) and barycentrics: embree on the UV
    triangles laid flat (glTF UV, v down = image rows)."""
    T = uvd["T"]
    left = ~uvd["is_right"][T].all(1)
    Tl = T[left]
    UV = uvd["UV"]
    P2 = np.c_[UV, np.zeros(len(UV))]
    s = ray.scene(P2, Tl)
    ys, xs = np.mgrid[0:size, 0:size]
    org = np.c_[(xs.ravel() + 0.5) / size, (ys.ravel() + 0.5) / size, np.ones(size * size)]
    dirs = np.broadcast_to(np.array([0.0, 0, -1]), org.shape)
    pid = np.full(len(org), -1, np.int64)
    bu = np.zeros(len(org))
    bv = np.zeros(len(org))
    for a in range(0, len(org), 2_000_000):
        r = s.run(org[a:a + 2_000_000].astype(np.float32), np.ascontiguousarray(dirs[a:a + 2_000_000], np.float32), output=1)
        pid[a:a + 2_000_000] = np.asarray(r["primID"])
        bu[a:a + 2_000_000] = np.asarray(r["u"])
        bv[a:a + 2_000_000] = np.asarray(r["v"])
    hit = pid >= 0
    w = np.stack([1 - bu - bv, bu, bv], 1)
    return Tl, np.nonzero(hit)[0], pid[hit], w[hit]


def fill_gutters(img, covered):
    """Each uncovered texel takes its nearest covered texel's value."""
    _, (iy, ix) = ndimage.distance_transform_edt(~covered, return_indices=True)
    return img[iy, ix]


def save(path, arr, mode):
    a = np.clip(np.round(arr * 255), 0, 255).astype(np.uint8)
    Image.fromarray(a, mode).save(path, optimize=True)


# ------------------------------------------------------------------------------------------------ B side --
def body_of(build_out, tier="close"):
    """Our built body (stage/<tier>.npz V, the glb's split, normals and head) for the bake."""
    g = Glb(os.path.join(build_out, "body.glb" if tier == "close" else "play.glb"))
    m = g.mesh("Heroine")
    heads = [mm for mm in g.meshes if mm.node != "Heroine"]
    return g, m, heads


def mean_curvature(P, T, N):
    """Per vertex H (1/m), sign by the normal (convex > 0), from the cotan Laplacian over the mixed area."""
    import scipy.sparse as sp
    n = len(P)
    L = np.zeros((n, 3))
    A = np.zeros(n)
    for i in range(3):
        a, b, c = T[:, i], T[:, (i + 1) % 3], T[:, (i + 2) % 3]
        u, v = P[a] - P[c], P[b] - P[c]
        cot = (u * v).sum(1) / np.maximum(np.linalg.norm(np.cross(u, v), axis=1), 1e-20)
        d = (P[b] - P[a]) * cot[:, None] * 0.5
        np.add.at(L, a, d)
        np.add.at(L, b, -d)
    ar = 0.5 * np.linalg.norm(np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]), axis=1)
    for i in range(3):
        np.add.at(A, T[:, i], ar / 3)
    Hn = L / np.maximum(A, 1e-12)[:, None]
    return -0.5 * (Hn * N).sum(1)


def hemisphere(n, seed=7):
    rng = np.random.default_rng(seed)
    u1, u2 = (np.arange(n) + rng.random(n)) / n, rng.random(n)
    r = np.sqrt(u1)
    th = 2 * np.pi * u2
    return np.stack([r * np.cos(th), r * np.sin(th), np.sqrt(1 - u1)], 1)


def frame_of(Nn):
    a = np.where(np.abs(Nn[:, :1]) < 0.9, np.array([[1.0, 0, 0]]), np.array([[0, 1.0, 0]]))
    t = U(np.cross(Nn, a))
    return t, np.cross(Nn, t)


def occlusion(scene, X, Nn, dirs, dist):
    """Fraction of `dirs` (local, z = the normal) that leave within `dist` unblocked."""
    t1, t2 = frame_of(Nn)
    open_ = np.zeros(len(X))
    for d in dirs:
        D = d[0] * t1 + d[1] * t2 + d[2] * Nn
        pid, tf = ray.hits(scene, X + Nn * 5e-4, D)
        open_ += (pid < 0) | (tf > dist)
    return open_ / len(dirs)


def through(scene, X, Nn, dirs, cap):
    t1, t2 = frame_of(Nn)
    acc = np.zeros(len(X))
    for d in dirs:
        D = -(d[0] * t1 + d[1] * t2 + d[2] * Nn)
        pid, tf = ray.hits(scene, X - Nn * 5e-4, D)
        acc += np.where(pid >= 0, np.minimum(tf, cap), cap)
    return acc / len(dirs)


# ---------------------------------------------------------------------------------------------------- zones --
def zones(z, Vb, sk, region_q):
    """L1's warm zones on the body regions as soft masks per our vertex (0..1) and their table. Centres from our
    skeleton (placed from our vertices) and our topology; radii by the zone's size."""
    names, worlds = sk["names"], sk["worlds"]
    J = lambda n: np.asarray(worlds[names.index(n)][:3, 3], float)     # noqa: E731
    n = len(Vb)
    left = z["side"] >= 0
    part = z["part"]
    P = list(z["parts"])
    out, table = np.zeros(n), []

    def add(name, region, c_idx, r, rule):
        nonlocal out
        for ci in np.atleast_1d(c_idx):
            for cc in (ci, mirror_vertex(z, ci)):
                d = np.linalg.norm(Vb - Vb[cc], axis=1)
                out = np.maximum(out, 1 - tu_smooth(d / r))
            table.append({"zone": name, "region": region, "warm": True, "centre_vertex": int(ci), "radius_m": r,
                          "rule": rule})

    def pick(mask, score):
        i = np.nonzero(mask)[0]
        return int(i[np.argmax(score[i])])
    ctr = np.nonzero(z["side"] == 0)[0]
    nk = ctr[(part[ctr] == P.index("neck")) & (Vb[ctr, 2] > np.median(Vb[ctr, 2]))]
    add("throat notch", 4, int(nk[np.argmin(Vb[nk, 1])]), 0.03, "the neck's lowest front center vertex")
    e = J("lowerarm_l")
    add("elbows", 7, pick(left & np.isin(part, [P.index("elbow")]) & (np.linalg.norm(Vb - e, axis=1) < 0.06), -Vb[:, 2]),
        0.04, "the elbow part's rearmost vertex within 6 cm of lowerarm_l's head")
    k_ = J("calf_l")
    add("knees", 12, pick(left & np.isin(part, [P.index("knee")]) & (np.linalg.norm(Vb - k_, axis=1) < 0.08), Vb[:, 2]),
        0.05, "the knee part's frontmost vertex within 8 cm of calf_l's head")
    hand = left & (part == P.index("hand"))
    dors = U(J("middle_01_l") - J("hand_l"))
    for f in ("index", "middle", "ring", "pinky"):
        j = J(f"{f}_01_l")
        near = hand & (np.linalg.norm(Vb - j, axis=1) < 0.015)
        nrm = Vb - j
        add("knuckles", 9, pick(near, nrm[:, 0]), 0.012, f"{f}_01_l's head, its outermost (+x: the back of the hand) vertex within 1.5 cm")
    for f in ("index", "middle", "ring", "pinky", "thumb"):
        j = J(f"{f}_04_leaf_l") if f"{f}_04_leaf_l" in names else J(f"{f}_03_l")
        add("fingertips", 9, int(np.argmin(np.where(hand, np.linalg.norm(Vb - j, axis=1), np.inf))), 0.012,
            f"the hand vertex nearest {f}'s tip joint")
    foot = left & (part == P.index("foot"))
    b, fwd = J("ball_l"), U((J("ball_l") - J("foot_l")) * [1, 0, 1])
    ahead = foot & ((Vb - b) @ fwd > 0)
    add("toes", 13, int(np.nonzero(ahead)[0][np.argmax(((Vb - b) @ fwd)[ahead])]), 0.04,
        "the foot vertex farthest ahead of ball_l (its toes, 4 cm)")
    add("heels", 13, pick(foot & (Vb[:, 1] < J("foot_l")[1] - 0.03), -((Vb - b) @ fwd)), 0.035,
        "the foot vertex farthest behind ball_l, 3 cm under foot_l")
    return out, table


def tu_smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def mirror_vertex(z, i):
    mo = z["mirror_of"]
    if z["side"][i] == 0:
        return i
    j = np.nonzero(mo == i)[0]
    return int(j[0]) if len(j) else i


# ------------------------------------------------------------------------------------------------------ run --
def run(build_out, maps_dir, size=2048, tier="close", z=None, uvd=None, sk=None):
    t0 = time.time()
    os.makedirs(maps_dir, exist_ok=True)
    z = z or dict(np.load(os.path.join(HERE, "out", "topo", f"{tier}.npz")))
    uvd = uvd or tu.load(tier, z)[0]
    st = np.load(os.path.join(build_out, "stage", f"{tier}.npz"))
    Vb = st["V"].astype(np.float64)                  # our built body, topology order
    g, m, heads = body_of(build_out, tier)
    src = uvd["src"]
    assert len(m.P) == len(src), "the glb is not this UV split"
    Ng = m.N.astype(np.float64)                      # the export's normals (per glb vertex)
    Tg = uvd["T"]
    Tan, wsg = tangent_frames(m.P.astype(np.float64), Ng, uvd["UV"], Tg)
    Tl, tix, tri, w = texels(uvd, size)
    rep = {"version": VERSION, "size": size, "covered": round(len(tix) / size ** 2, 4)}
    # each texel: its left point and its mirror (the same barycentrics on the mirrored triangle's vertices)
    vl = src[Tl[tri]]                               # [k,3] topology vertices
    inv_m = np.arange(len(Vb))
    mo = z["mirror_of"]
    inv_m[mo[mo >= 0]] = np.nonzero(mo >= 0)[0]      # left -> right (center: itself)
    vr = inv_m[vl]
    Pv = Vb
    Nv = np.zeros_like(Vb)
    Nv[src] = Ng                                     # (a topology vertex's normal: its copies share it)
    Xl = (w[:, :, None] * Pv[vl]).sum(1)
    Xr = (w[:, :, None] * Pv[vr]).sum(1)
    Nl = U((w[:, :, None] * Nv[vl]).sum(1))
    Nr = U((w[:, :, None] * Nv[vr]).sum(1))
    gl_ = Tl[tri]
    Tt = U((w[:, :, None] * Tan[gl_]).sum(1))
    Tt = U(Tt - Nl * (Tt * Nl).sum(1, keepdims=True))
    wl = np.sign((w * wsg[gl_]).sum(1))
    Bt = np.cross(Nl, Tt) * wl[:, None]
    # (the right half's frame is the left's mirrored: x flipped, so its tangent-space values equal the left's)
    TtR, BtR = Tt * MIRROR, Bt * MIRROR
    print("BAKE texels", len(tix), round(time.time() - t0, 1), flush=True)
    A = Source(os.path.join(build_out, "body.glb"))
    res = {}
    for side, X, Nn, Tf, Bf in (("l", Xl, Nl, Tt, Bt), ("r", Xr, Nr, TtR, BtR)):
        t, bw, d, miss = A.project(X, Nn)
        s = A.sample(t, bw)
        ts = lambda v: np.stack([(v * Tf).sum(1), (v * Bf).sum(1), (v * Nn).sum(1)], 1)     # noqa: E731
        res[side] = {"albedo": s["albedo"], "normal": U(ts(s["normal"])), "form": U(ts(s["form"])),
                     "rough": s["rough"], "freckles": s["freckles"], "dist": d, "miss": miss}
    print("BAKE carried", round(time.time() - t0, 1), flush=True)
    rep["projection"] = {"dist_p95_mm": round(float(np.percentile(np.r_[res["l"]["dist"], res["r"]["dist"]], 95)) * 1e3, 2),
                         "dist_max_mm": round(float(max(res["l"]["dist"].max(), res["r"]["dist"].max())) * 1e3, 2),
                         "closest_point_fallback": int(res["l"]["miss"].sum() + res["r"]["miss"].sum())}
    covered = np.zeros(size * size, bool)
    covered[tix] = True
    covered = covered.reshape(size, size)

    def img(vals, ch):
        a = np.zeros((size * size, ch))
        a[tix] = vals.reshape(len(tix), ch)
        return fill_gutters(a.reshape(size, size, ch), covered)
    avg = lambda k: 0.5 * (res["l"][k] + res["r"][k])          # noqa: E731
    files = {}
    alb = img(avg("albedo"), 3)
    save(os.path.join(maps_dir, "albedo.png"), alb, "RGB")
    nrm = U(avg("normal"))
    rep["normal_inverted_texels"] = int((nrm[:, 2] <= 0).sum())
    save(os.path.join(maps_dir, "normal.png"), img(nrm * 0.5 + 0.5, 3), "RGB")
    fnm = U(avg("form"))
    save(os.path.join(maps_dir, "form_normal.png"), img(fnm * 0.5 + 0.5, 3), "RGB")
    rgh = np.stack([np.zeros(len(tix)), avg("rough"), np.zeros(len(tix))], 1)
    save(os.path.join(maps_dir, "roughness.png"), img(rgh, 3), "RGB")
    save(os.path.join(maps_dir, "freckles.png"), img(avg("freckles"), 4), "RGBA")
    # regions
    rq = tu.region_of_quads(z, uvd["isl"])
    nq = len(z["Q"])
    tri_q = np.nonzero(~uvd["is_right"][uvd["T"]].all(1))[0][tri] % nq
    rid = np.zeros((size * size, 1))
    rid[tix, 0] = rq[tri_q]
    rid = fill_gutters(rid.reshape(size, size, 1), covered)[:, :, 0]
    Image.fromarray(rid.astype(np.uint8), "L").save(os.path.join(maps_dir, "region_id.png"), optimize=True)
    # B's own: AO, thickness, curvature (both halves, averaged)
    Pall = [m.P.astype(np.float64)] + [h.P.astype(np.float64) for h in heads if h.node == "HeroineHead"]
    Tall = [m.T] + [h.T for h in heads if h.node == "HeroineHead"]
    off = np.cumsum([0] + [len(p) for p in Pall])[:-1]
    scene = ray.scene(np.concatenate(Pall), np.concatenate([t_ + o for t_, o in zip(Tall, off)]))
    hd = hemisphere(32)
    cone = hemisphere(8, seed=3) * [np.sin(np.radians(30)), np.sin(np.radians(30)), 1]
    cone = U(cone)
    ao = 0.5 * (occlusion(scene, Xl, Nl, hd, 0.25) + occlusion(scene, Xr, Nr, hd, 0.25))
    save(os.path.join(maps_dir, "ao.png"), img(ao, 1)[:, :, 0], "L")
    th = 0.5 * (through(scene, Xl, Nl, cone, 0.06) + through(scene, Xr, Nr, cone, 0.06))
    save(os.path.join(maps_dir, "thickness.png"), img(1 - th / 0.06, 1)[:, :, 0], "L")
    Tq = np.concatenate([z["Q"][:, [0, 1, 2]], z["Q"][:, [0, 2, 3]]])
    H = mean_curvature(Vb, Tq, Nv)
    Ht = 0.5 * ((w * H[vl]).sum(1) + (w * H[vr]).sum(1))
    save(os.path.join(maps_dir, "curvature.png"), img(np.clip(0.5 + Ht * 0.01, 0, 1), 1)[:, :, 0], "L")
    print("BAKE own maps", round(time.time() - t0, 1), flush=True)
    # zones
    if sk is not None:
        zm, ztab = zones(z, Vb, sk, rq)
        zt = 0.5 * ((w * zm[vl]).sum(1) + (w * zm[vr]).sum(1))
        save(os.path.join(maps_dir, "zones.png"), img(np.stack([zt, np.zeros_like(zt), np.zeros_like(zt)], 1), 3), "RGB")
        with open(os.path.join(maps_dir, "zones.json"), "w") as f:
            json.dump({"what": "her warm/cool zones on the body regions (tools/body/topo_bake.py zones(); L1's "
                               "her_paint_regions.json zones_warm/zones_cool for regions 4-13)",
                       "map": "zones.png: R warm, G cool (0..1, smoothstep over the radius), B unused",
                       "zones": ztab}, f, indent=1)
    for k in ("albedo", "normal", "roughness", "freckles", "region_id", "ao", "thickness", "curvature", "form_normal",
              "zones"):
        files[k] = os.path.relpath(os.path.join(maps_dir, f"{k}.png"), REPO).replace("\\", "/")
    rep["files"] = files
    rep["frames"] = {"tangent_w_mismatch": int(frame_mismatch(uvd["UV"], Tg, wsg))}
    rep["s"] = round(time.time() - t0, 1)
    return rep, {"alb": alb, "covered": covered, "A": A, "Vb": Vb}


def frame_mismatch(UV, T, w):
    """Triangles whose UV winding disagrees with a vertex's tangent handedness (an inverted tangent frame)."""
    d1, d2 = UV[T[:, 1]] - UV[T[:, 0]], UV[T[:, 2]] - UV[T[:, 0]]
    det = d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]
    sgn = np.where(det < 0, 1.0, -1.0)          # glTF v down: a counter-clockwise face in math UV has det < 0 here
    return int((w[T] != sgn[:, None]).any(1).sum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("build_out")
    ap.add_argument("maps_dir")
    ap.add_argument("--size", type=int, default=2048)
    a = ap.parse_args()
    rep, _ = run(a.build_out, a.maps_dir, a.size)
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
