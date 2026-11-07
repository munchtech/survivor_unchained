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
                  glb carries; glTF convention, +Y = up the texture), so B lights as A does over B's own shape where
                  A's form is a correction of ours; A's map detail alone where A's form is another shape (carry_normal)
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
VERSION = "bake2"
# A's point for each of ours: a ray along our normal reaches REACH both ways (derivation: (c) the fit's own residual,
# measured: our close body to the fit's target p99 25 mm on the LOOSE arms, the template hands and feet; 4 mm on the
# TIGHT trunk) and takes a face of A's that looks our way (cos > FACING: no hit through to the inner thigh or a finger
# behind); the rest take the closest point on A
REACH = 0.03
FACING = 0.5


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

    def __init__(self, build_glb, pose=None, a_rest=None, a_normals=None):
        import her_target
        # (pose: the fit's posed bones (forms/her_topo_target_bones.json): A on the surface our points were wrapped
        # onto. The built body's own skeleton (landmarks on the fitted points) poses A up to 4 cm off it: the bake read
        # 53% of its texels by the closest-point fallback, p95 33 mm)
        want = None
        if pose:
            with open(pose if os.path.isabs(pose) else os.path.join(REPO, pose)) as f:
                want = {k: (np.asarray(v[0], float), np.asarray(v[1], float)) for k, v in json.load(f)["bones"].items()}
            # (a_rest: these chain bones at A's own rest turn, as her_a_target's "a_rest" lays B's girdle and upper arm)
            for b in a_rest or ():
                for sd in "lr":
                    want[f"{b}_{sd}"] = None
        A = Glb(A_PATH)
        m = A.mesh("Heroine")
        # (a_normals "file", P1 R1 round 15: A's form is the normals A's file stores, posed as Godot skins them, which is
        # what the game shades A with; None: the welded mesh's area-weighted normals (rounds 10-14). A's file normals
        # are not its mesh's: over the upper chest and breasts they lie p50 2 deg, p90 15-20 deg off the area-weighted
        # ones (y 1.30-1.40 m), a smooth slope over a faceted mesh (edges 6-10 mm); B carried the faceted field there
        # (form_near: A's whole form), lumps 20-40 mm across between the collarbone and the breast's top that A never shows)
        assert a_normals in (None, "file"), a_normals
        t = her_target.target(build_glb, A_PATH, world=True, want=want,
                              normals=m.N.astype(np.float64) if a_normals == "file" else None)
        first, inv = her_target.weld(m.P.astype(np.float64))   # (float64 as skin.Body reads it: a float32 P / tol rounds 183 tris' keys apart)
        Tw = inv[m.T]
        Tw = Tw[(Tw[:, 0] != Tw[:, 1]) & (Tw[:, 1] != Tw[:, 2]) & (Tw[:, 0] != Tw[:, 2])]
        assert len(Tw) == len(t["T"]) and (Tw == t["T"]).all(), "A's welded order differs from her_target's"
        self.P = t["P"][inv].astype(np.float64)
        self.T = m.T
        self.UV = m.UV.astype(np.float64)
        self.prim = m.prim_of
        fn = np.cross(self.P[self.T[:, 1]] - self.P[self.T[:, 0]], self.P[self.T[:, 2]] - self.P[self.T[:, 0]])
        if a_normals == "file":
            assert np.abs(t["P_file"] - m.P).max() < 1e-5, "A's file points are not her_target's body order"
            self.N = t["N_file"]                        # per file vertex, as A's file splits them
        else:
            self.N = t["N"][inv]                        # welded (smooth across A's UV seams)
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

    def project(self, X, Nx, reach=REACH):
        """(tri, bary, dist, fallback) of each point on A: the nearer hit of the rays along +/-N within `reach` whose
        face agrees with our normal (cos > FACING), else the closest point."""
        n = len(X)
        best_t = np.full(n, -1, np.int64)
        best_d = np.full(n, np.inf)
        best_q = np.zeros_like(X)
        fn = U(np.cross(self.P[self.T[:, 1]] - self.P[self.T[:, 0]], self.P[self.T[:, 2]] - self.P[self.T[:, 0]]))
        for sgn in (1.0, -1.0):
            org = X - sgn * Nx * reach
            pid, tf = ray.hits(self.scene, org, sgn * Nx)
            d = np.abs(tf - reach)
            ok = (pid >= 0) & (tf <= 2 * reach) & (d < best_d)
            ok[ok] &= (fn[pid[ok]] * Nx[ok]).sum(1) > FACING
            best_t[ok], best_d[ok] = pid[ok], d[ok]
            best_q[ok] = org[ok] + sgn * Nx[ok] * tf[ok, None]
        miss = best_t < 0
        if miss.any():
            q, _, t, d = self.surf.closest(X[miss], k=16)
            best_t[miss], best_d[miss], best_q[miss] = t, d, q
        a, b, c = (self.P[self.T[best_t, k]] for k in range(3))
        w = tu.bary(best_q, a, b, c)
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
        # off the graft: as the game reads a part with no map (hint_default_black: 0,0,0 and ALPHA 1). Alpha is 1 less her
        # sky mask (heroine_skin.gdshader sky_w): 0 here gave the whole torso her neck's sky share under the Look's rig, so
        # it lost the sky's cool light and read pinker than her head (P1 R1 round 10), with a step at the graft's edge
        fr = np.zeros((len(t), 4))
        fr[:, 3] = 1.0
        if self.freckles is not None:
            g = pr == 1
            fr[g] = bilinear(self.freckles, uv[g])
        return {"albedo": alb, "normal": Ns, "form": Ng, "rough": rough, "freckles": fr, "graft": pr == 1}


FORM_DEG = (8.0, 16.0)
# A's normal on ours: A's shading normal Ns (its map in its own frame) turned by the rotation that takes A's geometric
# normal Ng onto ours, by the part of that angle A's form does not carry: below FORM_DEG[0] none (A's form is a
# correction of ours: B lights as A), above FORM_DEG[1] all of it (only A's map detail, on our shape), smooth between.
# Derivation: (c) the fit's TIGHT tolerance (measured on bake1: the trunk, pelvis and thighs' form angle p99 5-11 deg);
# (a) beyond it A's form is another shape (the LOOSE arms p95 40 deg: girth only, no roll; the template hands and feet
# 90+ deg), whose lighting on ours inverted 7% of the hands' and 6% of the feet's texels.


def carry_normal(Ns, Ng, Nn, deg=FORM_DEG):
    ax = np.cross(Ng, Nn)
    sn = np.linalg.norm(ax, axis=1)
    th = np.arctan2(sn, (Ng * Nn).sum(1))
    t = np.clip((np.degrees(th) - deg[0]) / (deg[1] - deg[0]), 0, 1)
    a = th * t * t * (3 - 2 * t)
    k = ax / np.maximum(sn, 1e-12)[:, None]
    c, s_ = np.cos(a)[:, None], np.sin(a)[:, None]
    return U(Ns * c + np.cross(k, Ns) * s_ + k * (k * Ns).sum(1, keepdims=True) * (1 - c))


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
SOURCE_MAPS = ("albedo", "normal", "form_normal", "roughness", "freckles")


def run(build_out, maps_dir, size=2048, tier="close", z=None, uvd=None, sk=None, pose=None, carrier=None, carry=None,
        source_maps=None, form_deg=FORM_DEG, mirror="avg", dump=None, a_rest=None, form_near=None, a_normals=None,
        mirror_normal=None):
    """source_maps (P1 round 10): a directory of SOURCE_MAPS on our UVs, already carried once (her_a_target.py, its own
    bake.json holds the carry's gates): copied as they are, so the build reads neither A nor a carrier for the skin; only
    this body's own maps (AO, thickness, curvature, zones) are computed.
    carry (None = A's paint, relief and roughness as carried; {"mode": "neutral", "band_m": [a, b],
    "keep_regions": [names]}: a neutral placeholder skin, A's carried maps kept only within a of the open neck ring
    (eased out to 0 at b: the head seam) and on the keep_regions' texels (hands, feet: the nails); see neutral_keep).
    carrier (slider route, 5 Nov): a build of the SAME topology whose surface lies on A (her_topo.json's fit,
    built): A's paint, relief, roughness and freckles are read at each texel's point on the CARRIER, so every texel
    keeps the anatomical point it was painted at whatever shape the sliders give this body (our UVs are shared; the
    maps are a per-UV asset); B's own maps (AO, thickness, curvature, zones) are this build's surface. Without it a
    body far from A (the sliders: up to 5 cm at the bust and glutes) read A's paint by a 3 cm ray and the closest
    point: a shifted throat mask and lost arm paint."""
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
    keep_fn, A, Vc, Nvc, alb = None, None, Vb, Nv, None
    if source_maps:
        # the paint as stored source maps (made once, by the target's generator): no read of A or of a carrier at build
        sm = source_maps if os.path.isabs(source_maps) else os.path.join(REPO, source_maps)
        import shutil
        for k in SOURCE_MAPS:
            shutil.copy2(os.path.join(sm, f"{k}.png"), os.path.join(maps_dir, f"{k}.png"))
        with open(os.path.join(sm, "bake.json")) as f:
            made = json.load(f)
        rep["source_maps"] = source_maps.replace("\\", "/")
        rep["projection"] = made.get("projection")
    else:
        src_out, Vc, Nvc, Tan_c, wsg_c = build_out, Vb, Nv, Tan, wsg
        if carrier:
            src_out = carrier if os.path.isabs(carrier) else os.path.join(REPO, carrier)
            Vc = np.load(os.path.join(src_out, "stage", f"{tier}.npz"))["V"].astype(np.float64)
            assert Vc.shape == Vb.shape, "the carrier is not this topology"
            _, mc, _ = body_of(src_out, tier)
            assert len(mc.P) == len(src), "the carrier's glb is not this UV split"
            Nvc = np.zeros_like(Vc)
            Nvc[src] = mc.N.astype(np.float64)
            Tan_c, wsg_c = tangent_frames(mc.P.astype(np.float64), mc.N.astype(np.float64), uvd["UV"], Tg)
            rep["carrier"] = os.path.relpath(src_out, REPO).replace("\\", "/")
        Cl = (w[:, :, None] * Vc[vl]).sum(1)
        Cr = (w[:, :, None] * Vc[vr]).sum(1)
        CNl = U((w[:, :, None] * Nvc[vl]).sum(1))
        CNr = U((w[:, :, None] * Nvc[vr]).sum(1))
        gl_ = Tl[tri]
        Tt = U((w[:, :, None] * Tan_c[gl_]).sum(1))
        Tt = U(Tt - CNl * (Tt * CNl).sum(1, keepdims=True))
        wl = np.sign((w * wsg_c[gl_]).sum(1))
        Bt = np.cross(CNl, Tt) * wl[:, None]
        # (the right half's frame is the left's mirrored: x flipped, so its tangent-space values equal the left's; made
        # normal to the right's OWN normal, the handedness flipped (a mirror turns cross(N, T) w into cross(N', T') (-w)),
        # as the glb's TANGENT is there (tangent_frames on that half). The same as Tt, Bt mirrored when CNr is CNl
        # mirrored; skewed by their difference otherwise (P1 R1 bake round 2: B's halves carry A's own normals, which
        # are not mirror images: p90 4-7 deg apart on the trunk)
        TtR = U(Tt * MIRROR - CNr * ((Tt * MIRROR) * CNr).sum(1, keepdims=True))
        BtR = np.cross(CNr, TtR) * (-wl)[:, None]
        print("BAKE texels", len(tix), round(time.time() - t0, 1), flush=True)
        A = Source(os.path.join(src_out, "body.glb"), pose, a_rest, a_normals)
        rep["a_normals"] = a_normals or "area"
        res = {}
        covered0 = np.zeros(size * size, bool)
        covered0[tix] = True
        covered0 = covered0.reshape(size, size)
        for side, X, Nn, Tf, Bf in (("l", Cl, CNl, Tt, Bt), ("r", Cr, CNr, TtR, BtR)):
            t, bw, d, miss = A.project(X, Nn)
            s = A.sample(t, bw)
            ts = lambda v: np.stack([(v * Tf).sum(1), (v * Bf).sum(1), (v * Nn).sum(1)], 1)     # noqa: E731
            deg = form_deg
            if form_near is not None:
                # (P1 R1 round 13: where our surface lies ON A (the her_a target: within near_mm[0] of A along the ray,
                # smoothed over ~2 texels so the rule has no texel noise), A's form is carried whole up to wide_deg: A's
                # navel (walls to 77 deg on A's own mesh, a dip of ours) and its folds are A's geometry, which the
                # 8-16 deg rule dropped; off A (hands, feet: 7-25 mm) the old rule)
                lo_mm, hi_mm = form_near["near_mm"]
                dimg = np.zeros(size * size)
                dimg[tix] = d * 1e3
                dimg = ndimage.gaussian_filter(fill_gutters(dimg.reshape(size, size, 1), covered0)[:, :, 0], 2.0).ravel()[tix]
                k = 1 - np.clip((dimg - lo_mm) / (hi_mm - lo_mm), 0, 1)
                k = k * k * (3 - 2 * k)
                w0, w1 = form_near["wide_deg"]
                deg = (form_deg[0] + k * (w0 - form_deg[0]), form_deg[1] + k * (w1 - form_deg[1]))
            res[side] = {"albedo": s["albedo"], "normal": U(ts(carry_normal(s["normal"], s["form"], Nn, deg))),
                         "form": U(ts(s["form"])),
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
    files = {}
    rq = tu.region_of_quads(z, uvd["isl"])
    nq = len(z["Q"])
    tri_q = np.nonzero(~uvd["is_right"][uvd["T"]].all(1))[0][tri] % nq
    if not source_maps:
        if dump:
            np.savez_compressed(dump, tix=tix, Xl=Cl, Xr=Cr, **{f"{k}_{sd}": res[sd][k] for sd in ("l", "r")
                                                             for k in ("albedo", "normal", "form", "dist")})
        # (mirror "left", P1 R1 round 13: one texel serves both halves; the two halves' carries averaged halved A's
        # detail where A is not symmetric to the texel (torso: the L-R shading normals p50 2.4 deg apart against a
        # detail of 1.8: the abs' slopes p50 1.84 -> 1.08 deg, the sternum 3.26 -> 2.09): "left" takes A's left half
        # for both, its detail whole and mirrored)
        avg = ((lambda k: 0.5 * (res["l"][k] + res["r"][k])) if mirror == "avg" else (lambda k: res["l"][k]))   # noqa: E731
        rep["mirror"] = mirror
        a_alb, a_nrm, a_rgh, a_frk = avg("albedo"), avg("normal"), avg("rough"), avg("freckles")
        if mirror_normal is not None:
            # (mirror_normal, P1 R1 bake round 2: the normal map's own rule. Once B's vertex normals are A's, each half
            # its own (her_a "normals"), a texel's two halves need values apart only by what B's interpolation misses of
            # A's field (p90 1.6-3.1 deg, each half its own) and A's detail's asymmetry (p90 0.5-0.9): "avg" splits that
            # between the halves (each p90 1.0-1.6) where "left" gave the right half all of it; the paint stays mirror's)
            a_nrm = 0.5 * (res["l"]["normal"] + res["r"]["normal"]) if mirror_normal == "avg" else res["l"]["normal"]
            rep["mirror_normal"] = mirror_normal
        keep_fn = None
        if carry:
            assert carry.get("mode") == "neutral", carry
            keep_fn = neutral_keep(z, Vb, rq, carry)
            k_ring, k = keep_fn(Xl, tri_q)
            mid = (k_ring >= 0.5) & (k_ring < 1)
            assert mid.any(), "no texel in the neck band"
            n_alb = np.median(a_alb[mid], axis=0)
            n_rgh = float(np.median(a_rgh))
            a_alb = k[:, None] * a_alb + (1 - k[:, None]) * n_alb
            a_rgh = k * a_rgh + (1 - k) * n_rgh
            a_nrm = k[:, None] * a_nrm + (1 - k[:, None]) * np.array([0.0, 0.0, 1.0])
            a_frk = k[:, None] * a_frk
            rep["carry"] = {"mode": "neutral", "band_m": list(carry["band_m"]), "keep_regions": list(carry["keep_regions"]),
                            "albedo_rgb": [round(float(x), 5) for x in n_alb], "roughness": round(n_rgh, 5),
                            "kept_fraction": round(float((k > 0.5).mean()), 4)}
        alb = img(a_alb, 3)
        save(os.path.join(maps_dir, "albedo.png"), alb, "RGB")
        nrm = U(a_nrm)
        rep["normal_inverted_texels"] = int((nrm[:, 2] <= 0).sum())
        rep["normal_form"] = {"full_below_deg": form_deg[0], "detail_only_above_deg": form_deg[1],
                              **({"near_a": form_near} if form_near is not None else {})}
        save(os.path.join(maps_dir, "normal.png"), img(nrm * 0.5 + 0.5, 3), "RGB")
        fnm = U(avg("form"))
        save(os.path.join(maps_dir, "form_normal.png"), img(fnm * 0.5 + 0.5, 3), "RGB")
        rgh = np.stack([np.zeros(len(tix)), a_rgh, np.zeros(len(tix))], 1)
        save(os.path.join(maps_dir, "roughness.png"), img(rgh, 3), "RGB")
        save(os.path.join(maps_dir, "freckles.png"), img(a_frk, 4), "RGBA")
    # regions
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
    if source_maps:
        rep["gates"] = {**made["gates"], "from": "the source maps' own bake.json (the carry's gates)"}
        rep["gates"]["frame_mismatch"] = rep["frames"]["tangent_w_mismatch"]
        rep["gates"]["pass"] = bool(made["gates"]["pass"]) and rep["frames"]["tangent_w_mismatch"] == 0
    else:
        rep["gates"] = gates(z, uvd, Vc, Nvc, A, alb, covered, keep_fn=keep_fn, Vown=Vb, rq=rq)
    print("BAKE gates", rep["gates"]["pass"], round(time.time() - t0, 1), flush=True)
    rep["sheet"] = os.path.relpath(uv_sheet(maps_dir, uvd, os.path.join(build_out, "uv_sheet.png")), REPO).replace("\\", "/")
    rep["s"] = round(time.time() - t0, 1)
    return rep, {"alb": alb, "covered": covered, "A": A, "Vb": Vb}


def neutral_keep(z, Vb, rq, carry):
    """(carry neutral) f(X, q) -> (k_ring, k): X the points on B, q their quads. k_ring: 1 within band_m[0] of B's open
    neck ring (the boundary vertices of the topology, build_topo.boundary_ring: the baked head's ring), smoothstep to 0
    at band_m[1]; k: max(k_ring, 1 on the keep_regions' quads, regions named in base/her_paint_regions.json)."""
    Q = z["Q"]
    e = np.sort(np.concatenate([Q[:, [0, 1]], Q[:, [1, 2]], Q[:, [2, 3]], Q[:, [3, 0]]]), 1)
    u, c = np.unique(e, axis=0, return_counts=True)
    ring = np.unique(u[c == 1])
    tree = cKDTree(Vb[ring])
    a, b = carry["band_m"]
    ids = {r["name"]: r["id"] for r in tu.regions_json()["regions"]}
    keep_ids = [ids[n] for n in carry["keep_regions"]]

    def f(X, q):
        d, _ = tree.query(X)
        t = np.clip((b - d) / (b - a), 0, 1)
        kr = t * t * (3 - 2 * t)
        return kr, np.where(np.isin(rq[q], keep_ids), 1.0, kr)
    return f


def frame_mismatch(UV, T, w):
    """Triangles whose UV winding disagrees with a vertex's tangent handedness (an inverted tangent frame)."""
    d1, d2 = UV[T[:, 1]] - UV[T[:, 0]], UV[T[:, 2]] - UV[T[:, 0]]
    det = d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]
    sgn = np.where(det < 0, 1.0, -1.0)          # glTF v down: a counter-clockwise face in math UV has det < 0 here
    return int((w[T] != sgn[:, None]).any(1).sum())


# ------------------------------------------------------------------------------------------------ gates --
GATES = {"albedo_dE_p95": 3.0, "seam_step_dE_p95": 4.0, "frame_mismatch": 0}
# (derivation: (a) the game's need: dE00 about 2-3 is the just-noticeable step on skin at the close camera, 1:1; the
# bake must carry A's paint unseen (3), an island's edge must not read as a line (4: a seam pair is two texels side by
# side, seen together); an inverted tangent frame lights a triangle inside out (0))
AWAY_PX = 4          # "away from seams": the point's texel more than 4 texels from its island's edge (bilinear + mips)


def srgb_lab(c):
    c = np.clip(c, 0, 1)
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    M = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750],
                  [0.0193339, 0.1191920, 0.9503041]])
    xyz = lin @ M.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > (6 / 29) ** 3, np.cbrt(xyz), xyz / (3 * (6 / 29) ** 2) + 4 / 29)
    return np.stack([116 * f[:, 1] - 16, 500 * (f[:, 0] - f[:, 1]), 200 * (f[:, 1] - f[:, 2])], 1)


def de2000(a, b):
    """CIEDE2000 between Lab arrays (Sharma, Wu, Dalal 2005)."""
    L1, a1, b1 = a.T
    L2, a2, b2 = b.T
    C1, C2 = np.hypot(a1, b1), np.hypot(a2, b2)
    Cm = 0.5 * (C1 + C2)
    G = 0.5 * (1 - np.sqrt(Cm ** 7 / (Cm ** 7 + 25.0 ** 7)))
    a1p, a2p = a1 * (1 + G), a2 * (1 + G)
    C1p, C2p = np.hypot(a1p, b1), np.hypot(a2p, b2)
    h1p, h2p = np.degrees(np.arctan2(b1, a1p)) % 360, np.degrees(np.arctan2(b2, a2p)) % 360
    dLp, dCp = L2 - L1, C2p - C1p
    dh = h2p - h1p
    dh = np.where(C1p * C2p == 0, 0, np.where(dh > 180, dh - 360, np.where(dh < -180, dh + 360, dh)))
    dHp = 2 * np.sqrt(C1p * C2p) * np.sin(np.radians(dh / 2))
    Lm, Cmp = 0.5 * (L1 + L2), 0.5 * (C1p + C2p)
    hs = h1p + h2p
    hm = np.where(C1p * C2p == 0, hs, np.where(np.abs(h1p - h2p) <= 180, hs / 2,
                                               np.where(hs < 360, (hs + 360) / 2, (hs - 360) / 2)))
    Tt = (1 - 0.17 * np.cos(np.radians(hm - 30)) + 0.24 * np.cos(np.radians(2 * hm))
          + 0.32 * np.cos(np.radians(3 * hm + 6)) - 0.20 * np.cos(np.radians(4 * hm - 63)))
    dth = 30 * np.exp(-(((hm - 275) / 25) ** 2))
    Rc = 2 * np.sqrt(Cmp ** 7 / (Cmp ** 7 + 25.0 ** 7))
    Sl = 1 + 0.015 * (Lm - 50) ** 2 / np.sqrt(20 + (Lm - 50) ** 2)
    Sc, Sh = 1 + 0.045 * Cmp, 1 + 0.015 * Cmp * Tt
    Rt = -np.sin(np.radians(2 * dth)) * Rc
    return np.sqrt((dLp / Sl) ** 2 + (dCp / Sc) ** 2 + (dHp / Sh) ** 2 + Rt * (dCp / Sc) * (dHp / Sh))


def _pct(x, q=95):
    return round(float(np.percentile(x, q)), 3) if len(x) else 0.0


def uv_seams(T, src, n, left):
    """Each UV seam edge's two copies: (a1, b1, a2, b2) glb vertices, a* at the lower topology end. A seam: a topology
    edge whose two triangles hold it through different glb vertices (one of them a left triangle)."""
    e = np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
    et = np.tile(np.arange(len(T)), 3)
    sw = src[e[:, 0]] > src[e[:, 1]]
    lo, hi = np.where(sw, e[:, 1], e[:, 0]), np.where(sw, e[:, 0], e[:, 1])
    key = src[lo] * n + src[hi]
    o = np.argsort(key, kind="stable")
    ks = key[o]
    same = np.nonzero(ks[1:] == ks[:-1])[0]
    i1, i2 = o[same], o[same + 1]
    keep = ((lo[i1] != lo[i2]) | (hi[i1] != hi[i2])) & (left[et[i1]] | left[et[i2]])
    i1, i2 = i1[keep], i2[keep]
    return lo[i1], hi[i1], lo[i2], hi[i2]


def gates(z, uvd, Vb, Nv, A, alb, covered, n=400_000, seed=11, keep_fn=None, Vown=None, rq=None):
    """The bake's three gate numbers, measured on the SAVED albedo (8-bit, gutters filled, as the game reads it):
    albedo: random points on our left triangles (area-weighted on our body) and their mirrors; ours = the albedo at
      the point's UV (bilinear), A's = A's paint at the point's own projection (Source.project); dE00 per side (the
      UVs mirror, so one texel carries both sides: A's own left/right difference is in it, reported apart as
      mirror_part), on points away from seams (AWAY_PX).
    seam: every UV seam edge (uv_seams), 8 points along it, the albedo at the edge's UV on each side: dE00 between.
    frames: the export's triangles whose tangent handedness disagrees with their UV winding (frame_mismatch)."""
    size = alb.shape[0]
    q8 = np.round(np.clip(alb, 0, 1) * 255) / 255
    T, src, UV = uvd["T"], uvd["src"], uvd["UV"]
    left = ~uvd["is_right"][T].all(1)
    Tl = T[left]
    rng = np.random.default_rng(seed)
    P3 = Vb[src]
    ar = 0.5 * np.linalg.norm(np.cross(P3[Tl[:, 1]] - P3[Tl[:, 0]], P3[Tl[:, 2]] - P3[Tl[:, 0]]), axis=1)
    ti = rng.choice(len(Tl), n, p=ar / ar.sum())
    r1, r2 = rng.random(n), rng.random(n)
    s1 = np.sqrt(r1)
    w = np.stack([1 - s1, s1 * (1 - r2), s1 * r2], 1)
    uv = (w[:, :, None] * UV[Tl[ti]]).sum(1)
    ours = srgb_lab(bilinear(q8, uv))
    inv_m = np.arange(len(Vb))
    mo = z["mirror_of"]
    inv_m[mo[mo >= 0]] = np.nonzero(mo >= 0)[0]
    vl = src[Tl[ti]]
    edge = ndimage.distance_transform_edt(covered)
    px = np.clip((uv * size).astype(int), 0, size - 1)
    away = edge[px[:, 1], px[:, 0]] > AWAY_PX
    sides = {}
    for nm, vv in (("l", vl), ("r", inv_m[vl])):
        X = (w[:, :, None] * Vb[vv]).sum(1)
        Nn = U((w[:, :, None] * Nv[vv]).sum(1))
        t, bw, _, _ = A.project(X, Nn)
        sides[nm] = srgb_lab(A.sample(t, bw)["albedo"])
    dl, dr = de2000(ours, sides["l"]), de2000(ours, sides["r"])
    kept = np.ones(n, bool)
    if keep_fn is not None:           # carry neutral: A's paint is kept (and must match A) only where k == 1
        qi = np.nonzero(left)[0][ti] % len(z["Q"])
        _, k = keep_fn((w[:, :, None] * Vown[vl]).sum(1), qi)
        kept = k >= 1.0
    away = away & kept
    de = np.r_[dl[away], dr[away]]
    mirror_part = de2000(sides["l"], sides["r"])[away]
    a1, b1, a2, b2 = uv_seams(T, src, len(Vb), left)
    tt = (np.arange(8) + 0.5) / 8
    u1 = (UV[a1][:, None] * (1 - tt[None, :, None]) + UV[b1][:, None] * tt[None, :, None]).reshape(-1, 2)
    u2 = (UV[a2][:, None] * (1 - tt[None, :, None]) + UV[b2][:, None] * tt[None, :, None]).reshape(-1, 2)
    step = de2000(srgb_lab(bilinear(q8, u1)), srgb_lab(bilinear(q8, u2)))
    moved = (np.abs(u1 - u2).max(1) * size) > 0.5          # (the mirror line's copies share their UV: no step to see)
    _, wsg = tangent_frames(P3, Nv[src], UV, T)
    fm = int(frame_mismatch(UV, T, wsg))
    res = {"what": "dE = CIEDE2000 on the saved 8-bit albedo (sRGB -> Lab D65)",
           "albedo_dE_p95": _pct(de), "albedo_dE_p50": _pct(de, 50), "albedo_dE_p99": _pct(de, 99),
           "albedo_points_away": int(len(de)), "away_px": AWAY_PX,
           "albedo_dE_p95_near_seams": _pct(np.r_[dl[~away], dr[~away]]),
           "mirror_part_dE_p95": _pct(mirror_part), "mirror_part_dE_p50": _pct(mirror_part, 50),
           "seam_step_dE_p95": _pct(step[moved]), "seam_step_dE_p99": _pct(step[moved], 99),
           "seam_step_dE_max": round(float(step[moved].max()), 3) if moved.any() else 0.0,
           "seam_edges": int(len(a1)), "seam_samples": int(moved.sum()), "frame_mismatch": fm, "limits": GATES}
    if keep_fn is not None:
        res["albedo_dE_scope"] = "kept"
    res["pass"] = bool(res["albedo_dE_p95"] <= GATES["albedo_dE_p95"]
                       and res["seam_step_dE_p95"] <= GATES["seam_step_dE_p95"] and fm <= GATES["frame_mismatch"])
    return res


# ------------------------------------------------------------------------------------------------ sheet --
SHEET = ["albedo", "normal", "roughness", "freckles", "ao", "curvature", "thickness", "region_id"]


def uv_sheet(maps_dir, uvd, out_png, panel=1024):
    """One sheet: each map (SHEET, 4 x 2 panels) at `panel` px with the UV layout over it (the left triangles' edges
    faint, the UV seams bright), the gate numbers in bake.json beside it."""
    from PIL import ImageDraw
    T, UV, src = uvd["T"], uvd["UV"], uvd["src"]
    left = ~uvd["is_right"][T].all(1)
    a1, b1, a2, b2 = uv_seams(T, src, int(src.max()) + 1, left)
    Tl = T[left]
    e = np.unique(np.sort(np.concatenate([Tl[:, [0, 1]], Tl[:, [1, 2]], Tl[:, [2, 0]]]), 1), axis=0)
    seam = np.unique(np.sort(np.r_[np.c_[a1, b1], np.c_[a2, b2]], 1), axis=0)
    pal = np.random.default_rng(5).integers(40, 255, (256, 3))
    pal[0] = 0
    W = np.zeros((panel * 2, panel * 4, 3), np.uint8)
    for i, k in enumerate(SHEET):
        im = Image.open(os.path.join(maps_dir, f"{k}.png"))
        if k == "region_id":
            im = Image.fromarray(pal[np.asarray(im)].astype(np.uint8), "RGB")
        elif k == "roughness":
            im = Image.fromarray(np.repeat(np.asarray(im.convert("RGB"))[:, :, 1:2], 3, 2), "RGB")
        elif k == "freckles":
            a = np.asarray(im.convert("RGBA"), np.float64) / 255
            im = Image.fromarray(np.round(255 * (a[:, :, :3] * a[:, :, 3:] + 0.5 * (1 - a[:, :, 3:]))).astype(np.uint8))
        im = im.convert("RGB").resize((panel, panel), Image.LANCZOS)
        d = ImageDraw.Draw(im, "RGBA")
        xy = UV * panel
        for (p, q) in e:
            d.line([tuple(xy[p]), tuple(xy[q])], fill=(255, 255, 255, 28))
        for (p, q) in seam:
            d.line([tuple(xy[p]), tuple(xy[q])], fill=(255, 40, 200, 255))
        d.text((8, 8), k, fill=(255, 255, 0, 255))
        r, c = divmod(i, 4)
        W[r * panel:(r + 1) * panel, c * panel:(c + 1) * panel] = np.asarray(im)
    Image.fromarray(W).save(out_png, optimize=True)
    return out_png


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("build_out")
    ap.add_argument("maps_dir")
    ap.add_argument("--size", type=int, default=2048)
    ap.add_argument("--pose", default="tools/body/forms/her_topo_target_bones.json")
    ap.add_argument("--carrier", default=None, help="a build on A of the same topology: the paint's points (run's doc)")
    a = ap.parse_args()
    rep, _ = run(a.build_out, a.maps_dir, a.size, pose=a.pose, carrier=a.carrier)
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
