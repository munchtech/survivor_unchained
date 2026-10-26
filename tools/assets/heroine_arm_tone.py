"""Her arms' and shoulders' muscle tone: a soft relief laid in her skin's normal maps (body 9, 24 October 2026; the owner:
"not toned or sexy"; the max judge on the shoulder sculpt's round 2: "tone needs a detail normal map for the arm and
shoulder, not deeper geometry": a 2 mm groove in her 6-15 mm mesh does not show at the game's cameras).

The relief is a height field on her rest skin (mm), drawn left-canonical and mirrored, so her two arms match by
construction: the deltoid as one proud mass, its anterior border down the front of her shoulder (the deltopectoral
groove, a soft hollow below her clavicle at its top) and its posterior border meeting at the insertion's V about 45%
down her upper arm, three soft bellies on it (front, middle, rear heads); on her upper arm the biceps, the triceps' long
and lateral heads and the brachialis between them, so the biceps/triceps separation runs down the underside as a soft
valley; on her forearm a hint of the brachioradialis. Each muscle is a plateau with a rounded border band (DOMES, DELT),
in a chart round her upper arm's own axis (the line through its cross-sections' centres; s mm down from her shoulder
joint's level, phi deg round it: 0 front, 90 out, 180 back) and her forearm's; it is laid only on her arm's own surface
(not on her breast or side where they lie near it: her arm's radius per (s, phi) measured from her mesh), and fades to
nothing over her shoulder's top (the trapezius-deltoid join stays the geometry's).

Each texel's slope is the field's gradient at its 3D rest place (central differences), in the tangent frame Godot draws
it in (per-vertex tangents from her UVs and normals, angle-weighted as MikkTSpace; binormal toward the image's top, as
heroine_neck_relief.py and the hero's baked relief), 2x2 samples a texel on her body's sheet (2.2 mm a texel on her arms
at 2048), the islands padded. Her body's material (Material_0.001) takes it as a new normal texture (it had none); her
graft (skin_graft, her shoulder caps and chest) takes it added, slope for slope, to her collar's relief already there.
Godot hands a glb material's normal texture to the skin shader as its `relief` (People.Skin), so it is one map for every
skin tone; her pores go on over it; her paint, freckles and tattoo are not touched.

    ARM_TONE=1 python tools/assets/heroine_arm_tone.py <heroine.glb in> <heroine.glb out> [--strength K] [--png DIR]
    python tools/assets/heroine_arm_tone.py --remove <heroine.glb>     (takes it off again: before a re-run)

Gate: ARM_TONE=1 (without it the tool says so and changes nothing). Done-mark `heroine_arm_tone` (its parameters and
what it replaced, so --remove can put the graft's own relief back). A final pass: run it on a built body after every
geometry step (it reads her rest skin), then reimport. --strength scales every height (1: as drawn).
"""
import io
import json
import os
import shutil
import struct
import sys

import numpy as np
from scipy import ndimage
from scipy.ndimage import distance_transform_edt, map_coordinates

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

MARK = "heroine_arm_tone"
GATE = "ARM_TONE"
XM = 0.0010                       # her midline (m), as heroine_neck_shape
R0 = 45.0                         # mm a radian's arc is taken at in the arm chart (her upper arm's radius)
BODY_SIZE = 2048                  # her body sheet's relief (as its paint: 2.2 mm a texel on her arms)
GRAFT_SIZE = 2048                 # her graft's (as her collar relief: 0.29 mm a texel)
SUPER = {"Material_0.001": 2, "skin_graft": 1}    # samples a texel per side
PAD = 8                           # texels the islands are padded by
GREEN = 1                         # (binormal toward the image's top: glTF / Blender / Godot's OpenGL convention)
# the deltoid's outline in the arm chart (s mm, phi deg), from its top at the front, down the anterior border to the
# insertion's V (112 mm: ~45% of her upper arm from the acromion), up the posterior border
DELT = ((-80, 38), (-45, 16), (-15, -4), (15, -12), (45, 8), (78, 44), (112, 84),
        (78, 124), (45, 165), (15, 198), (-15, 204), (-45, 178), (-80, 152))
DELT_A = 2.2                      # mm proud of her arm round it
DELT_W = float(os.environ.get("TONE_DELT_W", 7.0))   # mm: its border band is twice this (round 4: 10, soft at strength 2.75)
DELT_FADE = (-60.0, -20.0)        # s: none above the first (her shoulder's top), whole below the second
# bellies: (chart, s0, phi0, half-length mm, half-width deg, height mm, plateau share)
HEADS = (("up", 30, 15, 60, 32, 0.6, 0.35),      # deltoid front head
         ("up", 35, 95, 62, 34, 0.72, 0.35),     # middle head
         ("up", 30, 168, 58, 32, 0.6, 0.35))     # rear head
# (round 4) TONE_SPLIT deg widens the biceps' and the triceps long head's half-widths so their split on the underside
# is a shallow valley, not a groove line (the owner wants the pit-to-elbow underside line straight)
_SPL = float(os.environ.get("TONE_SPLIT", 0.0))
DOMES = (("up", 150, -15, 85, 50 + _SPL, 1.8, 0.5),     # biceps
         ("up", 105, -150, 80, 42 + _SPL, 1.6, 0.5),    # triceps, long head (the underside)
         ("up", 120, 140, 55, 30, 1.2, 0.45),    # triceps, lateral head
         ("up", 200, 62, 42, 22, 0.7, 0.4),      # brachialis, between them on the outside
         ("fore", 35, 55, 80, 34, 1.3, 0.45))    # brachioradialis (forearm chart: s from the elbow, phi 0 front)
FOSSA = (-50, 10, 14, 16, -0.6)   # the hollow below her clavicle at the groove's top: s, phi, sigma mm, sigma deg, mm
ON_ARM = (5.0, 14.0)              # mm outside her arm's own radius: whole within the first, none past the second
RG_S = np.arange(-100, 281, 5.0)  # her arm's radius grid: s (mm) by phi (deg)
RG_P = np.arange(-180, 181, 5.0)
STRENGTH = 1.0


def _ss(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def _step(a, b, x):
    return _ss((x - a) / (b - a))


def _wrap(d):
    return (d + 180) % 360 - 180


def _vn(X, F):
    q = np.cross(X[F[:, 1]] - X[F[:, 0]], X[F[:, 2]] - X[F[:, 0]])
    n = np.zeros_like(X)
    for k in range(3):
        np.add.at(n, F[:, k], q)
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


def _chart(Q, O, ax, f, l):
    d = Q - O
    s = d @ ax
    q = d - s[:, None] * ax
    return s * 1000, np.degrees(np.arctan2(q @ l, q @ f)), np.linalg.norm(q, axis=1) * 1000


def _poly_sd(x, y, V):
    """signed distance (positive inside) from points (x, y) to the closed polygon V (k, 2)."""
    d = np.full(len(x), np.inf)
    inside = np.zeros(len(x), bool)
    for i in range(len(V)):
        (ax_, ay), (bx, by) = V[i], V[(i + 1) % len(V)]
        ex, ey = bx - ax_, by - ay
        t = np.clip(((x - ax_) * ex + (y - ay) * ey) / (ex * ex + ey * ey), 0, 1)
        d = np.minimum(d, np.hypot(x - ax_ - t * ex, y - ay - t * ey))
        inside ^= ((ay > y) != (by > y)) & (x < ex * (y - ay) / (ey + 1e-12) + ax_)
    return np.where(inside, d, -d)


def _dome(s, phi, s0, p0, hs, hp, A, flat):
    rho = np.sqrt(((s - s0) / hs) ** 2 + (_wrap(phi - p0) / hp) ** 2)
    return A * _step(1.0, flat, rho)


def frames(b):
    """Per side, her left-canonical charts (the right's points mirrored to her left): the upper arm's axis through its
    cross-sections' centres at 5-7 and 19-21 cm down, the forearm's at 3-5 and 15-17 cm, and her arm's radius grid."""
    J = {n: np.linalg.inv(b.ibm[i])[:3, 3] for i, n in enumerate(b.names)}
    Nv = _vn(b.U, b.F)
    out = {}
    for side, sg in (("l", 1), ("r", -1)):
        mir = np.array([sg, 1, 1.0])
        off = np.array([XM * (1 - sg), 0, 0])
        S0, E, Hd = (J[n + "_" + side] * mir + off for n in ("upperarm", "lowerarm", "hand"))
        U, N = b.U * mir + off, Nv * mir
        arm = [b.I[n] for n in b.names if (n.startswith("upperarm") or n.startswith("delt")) and n.endswith("_" + side)]
        fore = [b.I[n] for n in b.names if n.startswith("lowerarm") and n.endswith("_" + side)]
        wa, wf = b.Wd[:, arm].sum(1), b.Wd[:, fore].sum(1)

        def axis(A0, A1, levels, w, xmin):
            a = (A1 - A0) / np.linalg.norm(A1 - A0)
            s = (U - A0) @ a
            c = [U[(np.abs(s - lv) < 0.006) & (w > 0.6) & (U[:, 0] > xmin)].mean(0) for lv in levels]
            C1, C2 = np.mean(c[:3], 0), np.mean(c[3:], 0)
            ax = (C2 - C1) / np.linalg.norm(C2 - C1)
            f = np.array([0, 0, 1.0]) - ax[2] * ax
            f /= np.linalg.norm(f)
            return C1 + ((A0 - C1) @ ax) * ax, ax, f, np.cross(f, ax)

        O, ax, f, l = axis(S0, E, (0.05, 0.06, 0.07, 0.19, 0.20, 0.21), wa + wf, 0.12)
        O2, ax2, f2, l2 = axis(E, Hd, (0.03, 0.04, 0.05, 0.15, 0.16, 0.17), wf, 0.25)
        # her arm's own radius R(s, phi): per cell the innermost outward-facing point the arm's bones carry
        s, phi, r = _chart(U, O, ax, f, l)
        q = (U - O) - ((U - O) @ ax)[:, None] * ax
        outward = (N * q).sum(1) / np.maximum(np.linalg.norm(q, axis=1), 1e-9)
        m = (outward > 0.3) & (wa > 0.3) & (s > RG_S[0]) & (s < RG_S[-1]) & (U[:, 0] > 0.08)
        i = np.clip(np.round((s[m] - RG_S[0]) / 5).astype(int), 0, len(RG_S) - 1)
        j = np.clip(np.round((phi[m] - RG_P[0]) / 5).astype(int), 0, len(RG_P) - 1)
        G = np.full((len(RG_S), len(RG_P)), np.inf)
        np.minimum.at(G, (i, j), r[m])
        have = np.isfinite(G)
        G[~have] = 0
        _, (ii, jj) = distance_transform_edt(~have, return_indices=True)
        G = np.concatenate([G[ii, jj][:, -8:-1], G[ii, jj], G[ii, jj][:, 1:8]], 1)
        G = ndimage.gaussian_filter(G, 1.2)[:, 7:-7]
        out[side] = dict(sg=sg, mir=mir, off=off, up=(O, ax, f, l), fore=(O2, ax2, f2, l2), Rg=G)
    return out


def _side(Q, fr):
    s, phi, r = _chart(Q, *fr["up"])
    s2, phi2, r2 = _chart(Q, *fr["fore"])
    R = map_coordinates(fr["Rg"], [(np.clip(s, RG_S[0], RG_S[-1]) - RG_S[0]) / 5, (phi - RG_P[0]) / 5],
                        order=1, mode="nearest")
    on = _step(ON_ARM[1], ON_ARM[0], r - R) * _step(270, 240, s)
    k = R0 * np.pi / 180
    V = np.array(DELT, float)
    m = _step(-DELT_W, DELT_W, _poly_sd(s, ((phi + 90) % 360 - 90) * k, np.c_[V[:, 0], V[:, 1] * k]))
    top = _step(DELT_FADE[0], DELT_FADE[1], s)
    up = DELT_A * m * top
    for _, s0, p0, hs, hp, A, fl in HEADS:
        up += _dome(s, phi, s0, p0, hs, hp, A, fl) * m * top
    fo = np.zeros_like(s)
    for c, s0, p0, hs, hp, A, fl in DOMES:
        if c == "up":
            up += _dome(s, phi, s0, p0, hs, hp, A, fl)
        else:
            fo += _dome(s2, phi2, s0, p0, hs, hp, A, fl)
    fs, fp, gs, gp, fA = FOSSA
    up += fA * np.exp(-((s - fs) / gs) ** 2 - (_wrap(phi - fp) / gp) ** 2)
    fo *= _step(70, 55, r2) * _step(-60, -30, s2) * _step(200, 160, s2)
    return (up * on + fo) * 1e-3 * STRENGTH


def field(P, FR):
    """Her relief's height (m) at rest points P (n, 3)."""
    h = np.zeros(len(P))
    for fr in FR.values():
        Q = P * fr["mir"] + fr["off"]
        on = Q[:, 0] > 0.06
        if on.any():
            h[on] += _side(Q[on], fr)
    return h


def gradient(P, FR, eps=3e-4):
    g = np.zeros_like(P)
    for k in range(3):
        e = np.zeros(3)
        e[k] = eps
        g[:, k] = (field(P + e, FR) - field(P - e, FR)) / (2 * eps)
    return g


def vertex_tangents(X, N, uv, F):
    """Per-vertex tangent (toward +u, unit, in the vertex's plane) and handedness w (binormal = w N x T points toward
    the image's top, -v), from the faces' dP/du angle-weighted, as MikkTSpace gives Godot's import."""
    e1, e2 = X[F[:, 1]] - X[F[:, 0]], X[F[:, 2]] - X[F[:, 0]]
    d1, d2 = uv[F[:, 1]] - uv[F[:, 0]], uv[F[:, 2]] - uv[F[:, 0]]
    det = d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]
    det = np.where(np.abs(det) < 1e-14, 1e-14, det)
    Pu = (e1 * d2[:, 1:2] - e2 * d1[:, 1:2]) / det[:, None]
    Pv = (e2 * d1[:, 0:1] - e1 * d2[:, 0:1]) / det[:, None]
    T = np.zeros_like(X)
    Bv = np.zeros_like(X)
    for k in range(3):
        a, b_, c = F[:, k], F[:, (k + 1) % 3], F[:, (k + 2) % 3]
        u1, u2 = X[b_] - X[a], X[c] - X[a]
        ang = np.arccos(np.clip((u1 * u2).sum(1) / np.maximum(np.linalg.norm(u1, axis=1) * np.linalg.norm(u2, axis=1),
                                                             1e-18), -1, 1))
        tu = Pu / np.maximum(np.linalg.norm(Pu, axis=1, keepdims=True), 1e-18)
        tv = Pv / np.maximum(np.linalg.norm(Pv, axis=1, keepdims=True), 1e-18)
        np.add.at(T, a, tu * ang[:, None])
        np.add.at(Bv, a, tv * ang[:, None])
    T -= (T * N).sum(1, keepdims=True) * N
    T /= np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-18)
    w = np.sign((np.cross(N, T) * -Bv).sum(1)) * GREEN
    w[w == 0] = 1
    return T, w


def bake(G, b, FR, k, size, base=None):
    """(tone slopes x, y as float images, how many texels carry them) for her prim k (0 body, 1 graft)."""
    from heroine_neck import _Gl  # noqa: F401  (G is one)
    g = G.g
    hb = [n for n in g["nodes"] if n.get("name") == "Heroine"][0]
    prims = [p for p in g["meshes"][hb["mesh"]]["primitives"] if g["materials"][p["material"]].get("name") != "skin_head"]
    off = np.cumsum([0] + [g["accessors"][p["attributes"]["POSITION"]]["count"] for p in prims])
    p = prims[k]
    name = g["materials"][p["material"]]["name"]
    uv = G.get(p["attributes"]["TEXCOORD_0"]).astype(float)
    F = G.get(p["indices"]).reshape(-1, 3).astype(int)
    X = b.U[b.wid[off[k]:off[k + 1]]]
    N = G.get(p["attributes"]["NORMAL"]).astype(float)
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    T, w = vertex_tangents(X, N, uv, F)
    hv = np.abs(field(X, FR)) > 1e-9
    live = hv[F].any(1)
    # (and two rings of faces round them: a feature may sit inside a face whose corners have none)
    for _ in range(2):
        vv = np.zeros(len(X), bool)
        vv[F[live].ravel()] = True
        live = vv[F].any(1)
    cov = np.zeros((size, size), bool)
    sx = np.zeros((size, size))
    sy = np.zeros((size, size))
    n_sub = SUPER.get(name, 1)
    subs = [((i + 0.5) / n_sub - 0.5, (j + 0.5) / n_sub - 0.5) for i in range(n_sub) for j in range(n_sub)]
    allL, allf, allpix = [], [], []
    for fi, f in enumerate(F):
        t = uv[f] * size - 0.5
        lo, hi = np.floor(t.min(0)).astype(int), np.ceil(t.max(0)).astype(int)
        xs, ys = np.meshgrid(np.arange(max(lo[0], 0), min(hi[0], size - 1) + 1),
                             np.arange(max(lo[1], 0), min(hi[1], size - 1) + 1))
        q = np.stack([xs.ravel(), ys.ravel()], 1).astype(float)
        if not len(q):
            continue
        a, b_, c = t
        den = (b_[1] - c[1]) * (a[0] - c[0]) + (c[0] - b_[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        hit = np.zeros(len(q), bool)
        for ox, oy in subs if live[fi] else [(0.0, 0.0)]:
            qx, qy = q[:, 0] + ox, q[:, 1] + oy
            l1 = ((b_[1] - c[1]) * (qx - c[0]) + (c[0] - b_[0]) * (qy - c[1])) / den
            l2 = ((c[1] - a[1]) * (qx - c[0]) + (a[0] - c[0]) * (qy - c[1])) / den
            l3 = 1 - l1 - l2
            m = (l1 > -1e-4) & (l2 > -1e-4) & (l3 > -1e-4)
            hit |= m
            if live[fi] and m.any():
                allL.append(np.stack([l1[m], l2[m], l3[m]], 1))
                allf.append(np.full(m.sum(), fi))
                allpix.append(q[m].astype(int))
        cov[q[hit, 1].astype(int), q[hit, 0].astype(int)] = True
    if allL:
        L = np.concatenate(allL)
        fi = np.concatenate(allf)
        pix = np.concatenate(allpix)
        ff = F[fi]
        P = (X[ff] * L[..., None]).sum(1)
        Nn = (N[ff] * L[..., None]).sum(1)
        Nn /= np.linalg.norm(Nn, axis=1, keepdims=True)
        Tt = (T[ff] * L[..., None]).sum(1)
        Tt -= (Tt * Nn).sum(1, keepdims=True) * Nn
        Tt /= np.maximum(np.linalg.norm(Tt, axis=1, keepdims=True), 1e-18)
        Bb = np.cross(Nn, Tt) * w[ff[:, 0]][:, None]
        gr = gradient(P, FR)
        gr -= (gr * Nn).sum(1, keepdims=True) * Nn
        cnt = np.zeros((size, size))
        np.add.at(sx, (pix[:, 1], pix[:, 0]), -(gr * Tt).sum(1))
        np.add.at(sy, (pix[:, 1], pix[:, 0]), -(gr * Bb).sum(1))
        np.add.at(cnt, (pix[:, 1], pix[:, 0]), 1)
        sx = np.where(cnt > 0, sx / np.maximum(cnt, 1), 0)
        sy = np.where(cnt > 0, sy / np.maximum(cnt, 1), 0)
    d, (iy, ix) = distance_transform_edt(~cov, return_indices=True)
    pad = (~cov) & (d <= PAD)
    sx[pad], sy[pad] = sx[iy[pad], ix[pad]], sy[iy[pad], ix[pad]]
    return name, sx, sy


def _encode(sx, sy, base=None):
    """slopes (and a base normal map's, added) to an 8-bit tangent-space normal map."""
    if base is not None:
        n0 = base[..., :3].astype(float) / 255 * 2 - 1
        z = np.maximum(n0[..., 2], 0.2)
        sx, sy = sx + n0[..., 0] / z, sy + n0[..., 1] / z
    n = np.stack([sx, sy, np.ones_like(sx)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return np.clip(np.round((n * 0.5 + 0.5) * 255), 0, 255).astype(np.uint8)


def _read(path):
    d = open(path, "rb").read()
    jl = struct.unpack("<I", d[12:16])[0]
    g = json.loads(d[20:20 + jl])
    b0 = 20 + jl
    bl = struct.unpack("<I", d[b0:b0 + 4])[0]
    return g, bytearray(d[b0 + 8:b0 + 8 + bl])


def _write(path, g, binc):
    while len(binc) % 4:
        binc.append(0)
    g["buffers"][0]["byteLength"] = len(binc)
    js = json.dumps(g, separators=(",", ":")).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    body = struct.pack("<I", len(js)) + b"JSON" + js + struct.pack("<I", len(binc)) + b"BIN\x00" + bytes(binc)
    open(path, "wb").write(b"glTF" + struct.pack("<II", 2, 12 + len(body)) + body)


def _image(g, binc, ti):
    from PIL import Image
    im = g["images"][g["textures"][ti]["source"]]
    bv = g["bufferViews"][im["bufferView"]]
    o = bv.get("byteOffset", 0)
    return np.array(Image.open(io.BytesIO(bytes(binc[o:o + bv["byteLength"]]))).convert("RGB"))


def run(path_in, path_out, png_dir=None):
    from heroine_neck import _Gl
    import pit_hollow_post as ph
    from PIL import Image
    if os.path.abspath(path_in) != os.path.abspath(path_out):
        shutil.copyfile(path_in, path_out)
    G = _Gl(path_out)
    if (G.g.get("asset", {}).get("extras") or {}).get(MARK):
        print("ARM_TONE: %s has had it (--remove first to lay it again)" % path_out)
        return
    b = ph.Body(G)
    FR = frames(b)
    g, binc = _read(path_out)
    was = {}
    for k in (0, 1):
        size = BODY_SIZE if k == 0 else GRAFT_SIZE
        name, sx, sy = bake(G, b, FR, k, size)
        mat = [m for m in g["materials"] if m.get("name") == name][0]
        old = mat.get("normalTexture", {}).get("index")
        base = _image(g, binc, old) if old is not None else None
        if base is not None and base.shape[0] != size:
            base = np.array(Image.fromarray(base).resize((size, size), Image.BILINEAR))
        img = _encode(sx, sy, base)
        live = int((np.hypot(sx, sy) > 0.01).sum())
        tilt = float(np.degrees(np.arctan(np.hypot(sx, sy).max())))
        buf = io.BytesIO()
        Image.fromarray(img).save(buf, "PNG", optimize=True)
        png = buf.getvalue()
        if png_dir:
            os.makedirs(png_dir, exist_ok=True)
            open(os.path.join(png_dir, "arm_tone_%s.png" % name), "wb").write(png)
        while len(binc) % 4:
            binc.append(0)
        o = len(binc)
        binc += png
        g["bufferViews"].append({"buffer": 0, "byteOffset": o, "byteLength": len(png)})
        g["images"].append({"name": "heroine_arm_tone_" + name, "mimeType": "image/png",
                            "bufferView": len(g["bufferViews"]) - 1})
        g["textures"].append({"sampler": 0, "source": len(g["images"]) - 1})
        mat["normalTexture"] = {"index": len(g["textures"]) - 1}
        was[name] = old
        print("ARM_TONE: %s: %d texels carry tone, steepest %.1f deg; %d KB png%s"
              % (name, live, tilt, len(png) // 1024, " (added to its relief)" if base is not None else ""))
    g.setdefault("asset", {}).setdefault("extras", {})[MARK] = {
        "strength": STRENGTH, "body_size": BODY_SIZE, "graft_size": GRAFT_SIZE, "was": was,
        "delt_w": DELT_W, "split": _SPL}
    _write(path_out, g, binc)


def remove(path):
    """The tone taken off: each material's normal texture back to what it was (none on her body, her collar's relief on
    her graft); the tone's images stay in the file unused (a fresh build drops them)."""
    g, binc = _read(path)
    ex = g.setdefault("asset", {}).setdefault("extras", {})
    rec = ex.pop(MARK, None)
    if not rec:
        print("ARM_TONE: no tone on %s" % path)
        return
    for name, old in rec["was"].items():
        mat = [m for m in g["materials"] if m.get("name") == name][0]
        if old is None:
            mat.pop("normalTexture", None)
        else:
            mat["normalTexture"] = {"index": old}
    ex[MARK + "_removed"] = True
    _write(path, g, binc)
    print("ARM_TONE: removed from %s" % path)


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--remove" in a:
        remove(a[a.index("--remove") + 1])
        sys.exit(0)
    if os.environ.get(GATE) != "1":
        print("ARM_TONE: gated off (set %s=1 to lay her arms' tone); nothing changed" % GATE)
        sys.exit(0)
    if "--strength" in a:
        STRENGTH = float(a[a.index("--strength") + 1])
    png = a[a.index("--png") + 1] if "--png" in a else None
    files = [x for i, x in enumerate(a) if not x.startswith("--") and (i == 0 or a[i - 1] not in ("--strength", "--png"))]
    run(files[0], files[1], png)
