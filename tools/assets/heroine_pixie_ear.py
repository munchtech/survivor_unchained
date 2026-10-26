"""The pixie kept off her ear, on her ear as it is (face 41, 26 Oct).

    python tools/assets/heroine_pixie_ear.py godot/art/people [--dry] [--style pixie,braid,ponytail]

Face 42 (26 Oct): the braid and ponytail take it too (--style; default pixie). The braid had the same dark tuft of
blunt card ends over her lit helix root at the Look turned 40, and their cap (laid for the old ear) showed on the
ear's front and inside its top: their cap also fades within CAP_TIP of the flap. Their tie (hair_tie) is left alone; mark <style>_ear.

heroine_hair.py builds the pixie from the built blend, whose ear is the old one (before heroine_ear_shape set it in
toward her skull), and heroine_ear_shape.py --follow-only then carries it onto the new ear. Its build-time ear rules
(pixie_ear_hug, pixie_rim_hidden, the cap's clearing) saw the old ear, which stood 3 mm prouder: on the new one, seen
from 25-35 degrees round (the Look turned -40), the hair just in front of her ear's top hid its upper front helix and
its top read pointed, and card tips ended on its top-front corner (a dark tuft). So, on the installed files, the
pixie only, nothing moved: each hair point's vertex alpha (the cards' and fine strands' cover, the cap's fade, the
hair shader's COLOR.a) is eased to none

  1. within CLEAR (perpendicular, m) of a sight line from her helix rim (the upper half of the flap's side-view
     outline, its outer 60%, over RIM_UP) toward VIEWS (degrees round from her front, and up), the ones her head does not cut,
     nearer the eye than the rim: the hair's edge drawn back round the helix with a skin gap under it;
  2. within TIP of her ear's flap (3D): no card or strand end lies on it.

Face 42 r2b (pixie): its cap is first refined round her ears (refine_cap: edges over SUB_EDGE split within SUB_R of
the flap; its 4-10 mm triangles held their cover across the fade); the sight lines also run PIXIE_BACK behind the rim
(hair on her scalp behind the rim's top met it in the picture), and lines from the ear's front (FRONT_H stand-off,
FRONT_Y) keep her sideburn PIXIE_FRONT off it. Then

    python tools/assets/heroine_pixie_ear.py godot/art/people --shade

writes head_tex/heroine_shadow_pixie.png (heroine_shadow.png's scalp shade off the same zone, SHADE_*; People.HerScalp
lays heroine_shadow_<style>.png where there is one); run it after body post 7c (and again whenever heroine_shadow.png
changes: its done-mark, the PNG's text chunk pixie_shade, carries that file's checksum).

Run after heroine_ear_shape.py --follow-only (and heroine_shape_falloff.py) on each pixie build. Done-mark: the
gltf's asset extras pixie_ear; the .bin rewritten with the gltf's data checksum (Godot reimports on the .gltf).
"""
import os
import sys

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_ear_shape as es  # noqa: E402
from heroine_neck import _Gl, _CT, _NC, _dense, _top4  # noqa: E402

MARK = "pixie_ear"
VIEWS = [(az, el) for az in (25, 30, 35, 40, 45, 50, 55, 65) for el in (-5, 0, 5, 10)]
CLEAR = (0.0010, 0.0035)        # m from a sight line: no hair within the first, as it was past the second
RIM_UP = 0.008                  # m over the flap's middle (side on): the rim kept in sight (its top and upper front;
                                # below, her sideburn lies in front of it, as a real one does)
TIP = (0.0008, 0.0035)          # m from her ear's flap: the same (cards and strands, not the cap)
CAP_TIP = (0.0015, 0.0040)      # m from her ear's flap: the braid's and ponytail's cap the same (face 42: their cap,
                                # laid for the old ear, showed as a dark band down the helix's front at the Look turned
                                # 40 and a stroke inside its top at -40; the pixie's cap is as j5 passed it)
PIXIE_CLEAR = (0.0015, 0.0045)  # m from a sight line: the pixie's (a skin margin seen round the rim, not only off it)
PIXIE_BACK = 0.020              # m: the pixie's lines also run this far back past the rim (face 42 r2b: her hair and
                                # cap on her scalp behind the rim's top, which no line in front of it reached, met the
                                # rim's top in the picture at the Look turned 40, with no skin between)
FRONT_H = 0.0012                # m: the ear's front taken where it stands this far off her skull
FRONT_Z = 0.5                   # the ear's front outline: its outline points this share of the way from its middle to its front
FRONT_Y = (-0.006, 0.030)       # m about the flap's middle (side on), up: from her sideburn's tip to the rim's top front
PIXIE_FRONT = (0.0005, 0.0025)  # m from a sight line by the ear's front (pixie): her sideburn's tip kept ~2 mm off it
                                # (face 42 r2b: it lay on the ear's front at the Look turned 40, its shade with it)
PIXIE_TIP = (0.0030, 0.0050)    # m from her ear's flap: the pixie's cards AND cap (face 42 j1, max: its side hair still lay
                                # on the helix's top at the Look turned 40, the owner's "hair still goes over the ear":
                                # 3-4 mm of skin over the ear's top, ~2 mm between the sideburn's tip and its front)
SUB_R = 0.007                   # m from her ear's flap (3D): the pixie's cap refined here, before its fade
SUB_EDGE = 0.0010               # m: its edges split (midpoints) until none here is longer (face 42 r2b: its 4-10 mm
                                # triangles at the rim's top held their far corners' cover across the fade, so vertex
                                # alpha could not draw the margin)
SHADE_CLEAR = (0.0020, 0.0040)  # m: her scalp shade under the pixie (head_tex/heroine_shadow_pixie.png) off the same sight
SHADE_TIP = (0.0030, 0.0050)    # lines and her ear's flap as its hair, so the skin round the rim is skin, not the shade
                                # read as hair (face 42 r2b: with no hair on, the shade ran dark to the helix's top)
SHADE_BLUR = 1.2                # texels (of 1024): the clearing's edge softened
GRAIN_KEEP = 0.2                # her skin's shader grain kept over the bared scalp and her ear's top (the shade's alpha)
GRAIN_T = (0.50, 0.65)          # her ear from this height up (none under the first, in full past the second)
SHADE_FRONT = PIXIE_FRONT       # m: and the same off the ear's front
REACH = 0.045                   # m from the ear's middle (3D): the points looked at


def _ss(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def _normals(P, F):
    N = np.zeros_like(P)
    fn = np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]])
    for k in range(3):
        np.add.at(N, F[:, k], fn)
    return N / (np.linalg.norm(N, axis=1)[:, None] + 1e-12)


def _read(G, ai):
    """An accessor, dense (sparse and bufferView-less ones too)."""
    a = G.g["accessors"][ai]
    n, dt = _NC[a["type"]], np.dtype(_CT[a["componentType"]])
    X = G.get(ai) if "bufferView" in a else np.zeros((a["count"], n), dt)
    sp = a.get("sparse")
    if sp:
        def raw(v, t, c):
            bv = G.g["bufferViews"][v["bufferView"]]
            off = G.b0 + bv.get("byteOffset", 0) + v.get("byteOffset", 0)
            return np.frombuffer(bytes(G.buf[off:off + np.dtype(t).itemsize * c]), t)
        idx = raw(sp["indices"], _CT[sp["indices"]["componentType"]], sp["count"]).astype(int)
        X = X.copy()
        X[idx] = raw(sp["values"], dt, sp["count"] * n).reshape(-1, n)
    return X


def _append(G, x, target=None):
    """New data at the .bin's end; its bufferView's index."""
    while len(G.buf) % 4:
        G.buf.append(0)
    b = np.ascontiguousarray(x).tobytes()
    bv = {"buffer": 0, "byteOffset": len(G.buf), "byteLength": len(b)}
    if target:
        bv["target"] = target
    G.buf.extend(b)
    G.g["bufferViews"].append(bv)
    G.g["buffers"][0]["byteLength"] = len(G.buf)
    return len(G.g["bufferViews"]) - 1


def _accessor(G, x, like, target=34962):
    a = {k: v for k, v in G.g["accessors"][like].items() if k in ("componentType", "type", "normalized")}
    x = np.ascontiguousarray(x, dtype=_CT[a["componentType"]])
    a.update(bufferView=_append(G, x, target), count=len(x))
    if a["type"] == "VEC3" and a["componentType"] == 5126:
        a.update(min=x.min(0).tolist(), max=x.max(0).tolist())
    G.g["accessors"].append(a)
    return len(G.g["accessors"]) - 1


def refine_cap(G, prim, near, report=True):
    """The cap's triangles split (conforming: 1, 2 or 3 edge midpoints each) where an edge is over SUB_EDGE and its
    middle near (a callable on points -> bool); every attribute and morph target taken to the midpoints (normals and
    tangents renormalised, skin weights merged to the top 4). Written as new accessors at the .bin's end."""
    at = prim["attributes"]
    A = {k: _read(G, v).astype(float) for k, v in at.items()}
    T = [_read(G, t["POSITION"]).astype(float) for t in prim["targets"]]
    F = _read(G, prim["indices"]).reshape(-1, 3).astype(int)
    n0, f0 = len(A["POSITION"]), len(F)
    nj = int(A["JOINTS_0"].max()) + 1
    for _ in range(8):
        V = A["POSITION"]
        E = np.sort(np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), 1)
        E = np.unique(E, axis=0)
        L = np.linalg.norm(V[E[:, 0]] - V[E[:, 1]], axis=1)
        sp = E[(L > SUB_EDGE) & near((V[E[:, 0]] + V[E[:, 1]]) / 2)]
        if not len(sp):
            break
        a_, b_ = sp[:, 0], sp[:, 1]
        mid = {(int(i), int(j)): len(V) + k for k, (i, j) in enumerate(sp)}
        for k in A:
            if k == "JOINTS_0" or k == "WEIGHTS_0":
                continue
            m = (A[k][a_] + A[k][b_]) / 2
            if k == "NORMAL":
                m /= np.linalg.norm(m, axis=1, keepdims=True) + 1e-12
            if k == "TANGENT":
                m[:, :3] /= np.linalg.norm(m[:, :3], axis=1, keepdims=True) + 1e-12
                m[:, 3] = A[k][a_, 3]
            A[k] = np.vstack([A[k], m])
        M = _dense(A["JOINTS_0"], A["WEIGHTS_0"], nj)
        j4, w4 = _top4((M[a_] + M[b_]) / 2)
        A["JOINTS_0"] = np.vstack([A["JOINTS_0"], j4])
        A["WEIGHTS_0"] = np.vstack([A["WEIGHTS_0"], w4])
        T = [np.vstack([t, (t[a_] + t[b_]) / 2]) for t in T]
        out = []
        for f in F:
            ms = [mid.get((min(f[i], f[(i + 1) % 3]), max(f[i], f[(i + 1) % 3]))) for i in range(3)]
            c = sum(m is not None for m in ms)
            if c == 0:
                out.append(f)
                continue
            if c == 3:
                (x, y, z), (mx, my, mz) = f, ms
                out += [(x, mx, mz), (mx, y, my), (mz, my, z), (mx, my, mz)]
                continue
            r = next(i for i in range(3) if (ms[i] is not None) and (c == 1 or ms[(i + 1) % 3] is not None))
            x, y, z = f[r], f[(r + 1) % 3], f[(r + 2) % 3]
            if c == 1:
                m = ms[r]
                out += [(x, m, z), (m, y, z)]
            else:
                m1, m2 = ms[r], ms[(r + 1) % 3]        # on x-y and y-z
                out.append((m1, y, m2))
                if np.linalg.norm(A["POSITION"][x] - A["POSITION"][m2]) < np.linalg.norm(A["POSITION"][m1] - A["POSITION"][z]):
                    out += [(x, m1, m2), (x, m2, z)]
                else:
                    out += [(x, m1, z), (m1, m2, z)]
        F = np.array(out, int)
    for k, ai in list(at.items()):
        x = A[k]
        if k in ("JOINTS_0", "COLOR_0"):
            x = np.round(x)
        at[k] = _accessor(G, x, ai)
    for t in prim["targets"]:
        t["POSITION"] = _accessor(G, T.pop(0), t["POSITION"])
    ix = F.astype(np.uint32 if len(A["POSITION"]) > 65535 else np.uint16).reshape(-1)
    ia = {"componentType": 5125 if ix.dtype == np.uint32 else 5123, "type": "SCALAR"}
    ia.update(bufferView=_append(G, ix, 34963), count=len(ix))
    G.g["accessors"].append(ia)
    prim["indices"] = len(G.g["accessors"]) - 1
    if report:
        print("PIXIE_EAR: cap refined round her ears: %d -> %d points, %d -> %d triangles" % (n0, len(A["POSITION"]), f0, len(F)))


def ear_lines(P, F, hy, report=True):
    """Per side: its flap's points, its rim, and the rim's sight lines (points, directions) her head does not cut."""
    from scipy.spatial import ConvexHull
    N = _normals(P, F)
    out = {}
    for sg in (-1, 1):
        f = es.ear_frame(P, sg, hy)
        E = P[f["ear"]]
        eq = ConvexHull(E[:, 1:]).equations
        dist = -(E[:, 1:] @ eq[:, :2].T + eq[:, 2]).max(1)
        yc = (E[:, 1].min() + E[:, 1].max()) / 2
        rim = E[(dist < 0.0025) & (E[:, 1] > yc) & (np.abs(E[:, 0]) > np.percentile(np.abs(E[:, 0]), 40))]
        flap = f["near"] & (f["h"] > 0.001) & (f["r"] < es.EAR_R[1])
        body = ~flap
        T = cKDTree(P[body])
        Pb, Nb = P[body], N[body]
        rim_c = rim[rim[:, 1] > E[:, 1].mean() + RIM_UP]
        # (the front from the flap where it stands FRONT_H off her skull, not the flap's 3 mm: there her ear rises from
        # her cheek 5-7 mm ahead of that, and that is the edge seen)
        Ef = P[f["near"] & (f["h"] > FRONT_H) & (f["r"] < es.EAR_R[1])]
        eqf = ConvexHull(Ef[:, 1:]).equations
        df = -(Ef[:, 1:] @ eqf[:, :2].T + eqf[:, 2]).max(1)
        zm = Ef[:, 2].mean()
        front = Ef[(df < 0.0025) & (Ef[:, 2] > zm + FRONT_Z * (Ef[:, 2].max() - zm)) & (Ef[:, 1] > E[:, 1].mean() + FRONT_Y[0])
                   & (Ef[:, 1] < E[:, 1].mean() + FRONT_Y[1])]

        def lines(pts, dense=0):
            # (the front's points and the midpoints of its neighbours within 3 mm, twice: 2-3 mm apart, the union
            # of their lines drew a sawtooth edge on the shade)
            for _ in range(dense):
                pr = cKDTree(pts).query_pairs(0.003, output_type="ndarray")
                pts = np.unique(np.vstack([pts, (pts[pr[:, 0]] + pts[pr[:, 1]]) / 2]), axis=0)
            R, D = [], []
            for az, el in VIEWS:
                a, b = np.radians(az), np.radians(el)
                d = np.array([sg * np.sin(a) * np.cos(b), np.sin(b), np.cos(a) * np.cos(b)])    # (glb: x side, y up, z front)
                S = pts[:, None, :] + np.arange(0.002, 0.061, 0.001)[None, :, None] * d
                _, ix = T.query(S.reshape(-1, 3))
                inside = (((S.reshape(-1, 3) - Pb[ix]) * Nb[ix]).sum(1) < 0).reshape(S.shape[:2]).any(1)
                R.append(pts[~inside])
                D.append(np.repeat(d[None], (~inside).sum(), 0))
            return np.vstack(R), np.vstack(D)
        R, D = lines(rim_c)
        RF, DF = lines(front, 2)
        out[sg] = dict(c=E.mean(0), flap=P[f["ear"]], rim=rim, R=R, D=D, RF=RF, DF=DF)
        if report:
            print("PIXIE_EAR: side %+d: %d rim points, %d sight lines kept clear (%d front points, %d lines)"
                  % (sg, len(rim), len(R), len(front), len(RF)))
    return out


def line_gap(Q, R, D, back=0.0):
    """Each point's least distance from a sight line (R, D), over the lines it is in front of (nearer the eye), and
    those it is up to back (m) behind the rim on (seen just beside the rim, past it)."""
    g = np.full(len(Q), np.inf)
    for i0 in range(0, len(Q), 1024):
        X = Q[i0:i0 + 1024, None, :] - R[None]
        t = (X * D[None]).sum(-1)
        perp = np.linalg.norm(X - t[..., None] * D[None], axis=-1)
        perp[(t < 0.001) & ~((back > 0) & (t > -back))] = np.inf
        g[i0:i0 + 1024] = perp.min(1)
    return g


def run(art, dry=False, report=True, style="pixie"):
    path = os.path.join(art, "heroine_hair_%s.gltf" % style)
    mark = MARK if style == "pixie" else "%s_ear" % style
    G = _Gl(path)
    if mark in G.g["asset"].get("extras", {}):
        print("PIXIE_EAR: %s has had it" % os.path.basename(path))
        return
    P, UV, F, hy = es._head(os.path.join(art, "heroine.glb"))
    L = ear_lines(P, F, hy, report)
    if style == "pixie":
        flaps = cKDTree(np.vstack([e["flap"] for e in L.values()]))
        for p in G.g["meshes"][0]["primitives"]:
            if G.g["materials"][p["material"]].get("name") == "hair_cap":
                refine_cap(G, p, lambda X: flaps.query(X)[0] < SUB_R, report)
    for p in G.g["meshes"][0]["primitives"]:
        name = G.g["materials"][p["material"]].get("name")
        if name == "hair_tie":
            continue
        a = p["attributes"]
        V = G.get(a["POSITION"]).astype(float)
        C = G.get(a["COLOR_0"]).astype(float) / 65535.0
        assert G.g["accessors"][a["COLOR_0"]]["componentType"] == 5123
        k = np.ones(len(V))
        for sg, e in L.items():
            m = (np.sign(V[:, 0]) == sg) & (np.linalg.norm(V - e["c"], axis=1) < REACH)
            if not m.any():
                continue
            g = line_gap(V[m], e["R"], e["D"], PIXIE_BACK if style == "pixie" else 0.0)
            cl = PIXIE_CLEAR if style == "pixie" else CLEAR
            w = _ss((g - cl[0]) / (cl[1] - cl[0]))
            if style == "pixie":
                gf = line_gap(V[m], e["RF"], e["DF"], PIXIE_BACK)
                w = np.minimum(w, _ss((gf - PIXIE_FRONT[0]) / (PIXIE_FRONT[1] - PIXIE_FRONT[0])))
                dt = cKDTree(e["flap"]).query(V[m])[0]
                w = np.minimum(w, _ss((dt - PIXIE_TIP[0]) / (PIXIE_TIP[1] - PIXIE_TIP[0])))
            elif name != "hair_cap":
                dt = cKDTree(e["flap"]).query(V[m])[0]
                w = np.minimum(w, _ss((dt - TIP[0]) / (TIP[1] - TIP[0])))
            else:
                dt = cKDTree(e["flap"]).query(V[m])[0]
                w = np.minimum(w, _ss((dt - CAP_TIP[0]) / (CAP_TIP[1] - CAP_TIP[0])))
            k[m] = np.minimum(k[m], w)
        a0 = C[:, 3].copy()
        C[:, 3] = C[:, 3] * k
        if report:
            ch = a0 - C[:, 3] > 0.02
            print("PIXIE_EAR: %s: %d of %d points eased (%d to under 0.1)" % (name, int(ch.sum()), len(V), int((ch & (C[:, 3] < 0.1)).sum())))
        G.put(a["COLOR_0"], np.clip(np.round(C * 65535.0), 0, 65535).astype(np.uint16))
    tip = PIXIE_TIP if style == "pixie" else TIP
    G.g["asset"].setdefault("extras", {})[mark] = "clear %.1f-%.1f mm, tip %.1f-%.1f mm, %d views%s" % (
        (PIXIE_CLEAR if style == "pixie" else CLEAR)[0] * 1e3, (PIXIE_CLEAR if style == "pixie" else CLEAR)[1] * 1e3, tip[0] * 1e3, tip[1] * 1e3, len(VIEWS),
        ", cap refined to %.1f mm within %.0f mm" % (SUB_EDGE * 1e3, SUB_R * 1e3) if style == "pixie" else "")
    if not dry:
        G.save()
        print("PIXIE_EAR: %s written" % path)


def clear_field(X, L, wid=0.0):
    """The pixie's skin clearing at points X on her skin: 0 bare, 1 shade (or hair) in full (SHADE_*, each range
    pushed out by wid)."""
    k = np.ones(len(X))
    for sg, e in L.items():
        m = (np.sign(X[:, 0]) == sg) & (np.linalg.norm(X - e["c"], axis=1) < REACH)
        g = line_gap(X[m], e["R"], e["D"], PIXIE_BACK)
        gf = line_gap(X[m], e["RF"], e["DF"], PIXIE_BACK)
        dt = cKDTree(e["flap"]).query(X[m])[0]
        r = lambda x, a: _ss((x - a[0]) / (a[1] + wid - a[0]))
        k[m] = np.minimum(np.minimum(r(g, SHADE_CLEAR), r(gf, SHADE_FRONT)), r(dt, SHADE_TIP))
    return k


def shade(art, report=True):
    """head_tex/heroine_shadow_pixie.png: heroine_shadow.png (body post 7c's) with its green (the scalp shade) off her
    skin within SHADE_CLEAR of the pixie's sight lines (PIXIE_BACK behind the rim too) and SHADE_TIP of her ear's flap,
    faded back in past them; People.HerScalp lays heroine_shadow_<style>.png where there is one. Done-mark: the PNG's
    text chunk pixie_shade, with heroine_shadow.png's checksum (rewritten when that changes)."""
    import hashlib
    from PIL import Image, PngImagePlugin
    from scipy import ndimage
    src = os.path.join(art, "head_tex", "heroine_shadow.png")
    dst = os.path.join(art, "head_tex", "heroine_shadow_pixie.png")
    md5 = hashlib.md5(open(src, "rb").read()).hexdigest()
    tag = "clear %.1f-%.1f mm, front %.1f-%.1f mm (h %.1f, y %.0f-%.0f mm, dense, blur %.1f), tip %.1f-%.1f mm, back %.0f mm, src %s" % (
        SHADE_CLEAR[0] * 1e3, SHADE_CLEAR[1] * 1e3, SHADE_FRONT[0] * 1e3, SHADE_FRONT[1] * 1e3, FRONT_H * 1e3, FRONT_Y[0] * 1e3, FRONT_Y[1] * 1e3, SHADE_BLUR, SHADE_TIP[0] * 1e3,
                                                                         SHADE_TIP[1] * 1e3, PIXIE_BACK * 1e3, md5) + ", grain %.2f from t %.2f-%.2f, skin wid %.1f mm, ear %.0f mm" % (GRAIN_KEEP, GRAIN_T[0], GRAIN_T[1], SKIN_WID * 1e3, TOP_DE * 1e3)
    if os.path.exists(dst) and Image.open(dst).info.get("pixie_shade") == tag:
        print("PIXIE_EAR: %s has had it" % os.path.basename(dst))
        return
    im = Image.open(src)
    A = np.array(im.convert("RGBA"))
    size = A.shape[0]
    P, UV, F, hy = es._head(os.path.join(art, "heroine.glb"))
    L = ear_lines(P, F, hy, False)
    # (each texel at its own point on her skin, not her head's points' values drawn across its triangles: its 3-5 mm
    # triangles round the ear left a sawtooth edge on a 2 mm fade)
    T = F[(np.linalg.norm(P[F] - np.vstack([e["c"] for e in L.values()])[:, None, None], axis=-1) < REACH).all(-1).any(0)]
    iy, ix, X = es._raster(UV, T, P, size)
    k = clear_field(X, L)
    M = np.ones((size, size), np.float32)
    M[iy, ix] = k
    M = ndimage.gaussian_filter(M, SHADE_BLUR)     # (what teeth the lines' union still left, softened)
    cov = np.zeros((size, size), bool)
    ci, cj, _ = es._raster(UV, F, np.zeros((len(P), 1)), size)
    cov[ci, cj] = True
    dist, (ny, nx) = ndimage.distance_transform_edt(~cov, return_indices=True)
    gut = ~cov & (dist <= 4) & (M[ny, nx] < 1)
    M[gut] = M[ny[gut], nx[gut]]
    g0 = A[..., 1].astype(np.float32)
    A[..., 1] = np.clip(np.floor(g0 * M + 0.5), 0, 255).astype(np.uint8)
    # (its alpha: her skin's shader grain kept GRAIN_KEEP there (heroine_skin.gdshader, under scalp_shadow): bared, the
    # scalp's grain (x3 off her face, none on it) read as a pale mottle on her ear's top and the margin round it)
    Z = _zone(art, size)
    gw = np.maximum((1 - Z["kw"]) * Z["sc"], (1 - Z["sc"]) * _ss((Z["t"] - GRAIN_T[0]) / (GRAIN_T[1] - GRAIN_T[0])) * (Z["de"] < TOP_DE))
    Gm = np.zeros((size, size), np.float32)
    Gm[Z["iy"], Z["ix"]] = gw
    Gm = ndimage.gaussian_filter(Gm, SHADE_BLUR)
    gut = ~cov & (dist <= 4)
    Gm[gut] = Gm[ny[gut], nx[gut]]
    A[..., 3] = np.clip(np.floor(255 * (1 - (1 - GRAIN_KEEP) * Gm) + 0.5), 0, 255).astype(np.uint8)
    info = PngImagePlugin.PngInfo()
    info.add_text("pixie_shade", tag)
    Image.fromarray(A, "RGBA").save(dst, pnginfo=info)
    if report:
        print("PIXIE_EAR: %s: %d texels eased" % (dst, int((A[..., 1] != g0).sum())))


SKIN_MARK = "pixie_skin"
SKIN_WID = 0.003                 # m: the skin's lift runs this far under the hair past the shade's clearing (its edge
                                 # under hair, not at the hair's fading edge)
SKIN_EAR = (0.0008, 0.0015)      # m of stand-off off her skull: in full under the first, none past the second (the ear's
                                 # own paint left; its front is heroine_ear_shape's front_tone)
SKIN_Q = (1.69, 1.72, 1.77)      # linear: the bared scalp's paint over her face's beside it (features' blue), per channel
                                 # (face 42 r2c: bared, it rendered 0.057 OKLab L under her cheek, greyer and yellower at
                                 # the Look turned 40 in copper; her face takes face_tone and its fits, her scalp none)
SKIN_C = 1.2                     # its OKLab chroma raised by this share (at the same lift it rendered 0.85x her cheek's: a
                                 # grey strip behind the rim in blonde)
SKIN_DETAIL = 0.5                # the paint's fine detail (over its blur, SKIN_SIGMA texels of 4096) kept: the scalp's
SKIN_SIGMA = 10.0                # stipple of follicles eased toward her cheek's finer grain
TOP_T = (0.70, 0.82)             # her ear's own top (its height up the ear: none under the first, in full past the second),
TOP_REF = (0.40, 0.65)           # which the pixie bares (its hair lay on it): its blur taken to the ear's paint between
TOP_DETAIL = 0.35                # these heights, TOP_DETAIL of its detail kept (face 42 r2c: its paint, never seen
                                 # before, rendered a pale mottle on the helix's top front and a mauve-grey patch behind)
TOP_DE = 0.006                   # m from the ear's points (its flap standing 3 mm off her skull): its rim's outer 1.5-3 mm too


def _zone(art, n=1024):
    """The pixie's bared zone round her ears at her head's texels (n x n): each texel's clearing (k0; kw, SKIN_WID
    further under the hair), stand-off off her skull (h), height up the ear (t), distance to its points (de), the
    features' blue, and the weights: w her bared scalp's (off her face and ear), we her ear's own top's."""
    from PIL import Image
    from scipy import ndimage
    P, UV, F, hy = es._head(os.path.join(art, "heroine.glb"))
    L = ear_lines(P, F, hy, False)
    T = F[(np.linalg.norm(P[F] - np.vstack([e["c"] for e in L.values()])[:, None, None], axis=-1) < REACH).all(-1).any(0)]
    iy, ix, X = es._raster(UV, T, P, n)
    k0, kw = clear_field(X, L), clear_field(X, L, SKIN_WID)
    h, t, de = np.zeros(len(X)), np.zeros(len(X)), np.full(len(X), np.inf)
    for sg in (-1, 1):
        m = np.sign(X[:, 0]) == sg
        f = es.ear_frame(P, sg, hy)
        h[m] = np.abs(X[m, 0]) - f["sk"](X[m][:, 1:3])
        t[m] = (X[m, 1] - f["y"][0]) / (f["y"][1] - f["y"][0])
        de[m] = cKDTree(P[f["ear"]]).query(X[m])[0]
    fe = np.asarray(Image.open(os.path.join(art, "head_tex", "heroine_features.png")).convert("RGBA"), np.float32)[..., 2] / 255
    fe = ndimage.zoom(fe, n / fe.shape[0], order=1) if fe.shape[0] != n else fe
    blue = fe[iy, ix]
    sc = _ss((SKIN_EAR[1] - h) / (SKIN_EAR[1] - SKIN_EAR[0]))
    w = (1 - kw) * sc * (1 - blue)
    we = (1 - sc) * _ss((t - TOP_T[0]) / (TOP_T[1] - TOP_T[0])) * (de < TOP_DE)
    return dict(iy=iy, ix=ix, X=X, k0=k0, kw=kw, h=h, t=t, de=de, blue=blue, sc=sc, w=w, we=we)


def skin(art, faces=None, report=True):
    """The scalp the pixie bares round her ears (clear_field, SKIN_WID further under the hair) laid in her face's
    colour in each head paint (head_tex/heroine_head*.jpg): its blur taken to her face's paint beside it times SKIN_Q,
    SKIN_DETAIL of its fine detail kept; off her face (the features' blue, which has face_tone) and her ear. Face 42
    r2c: bared, it read a grey-brown crescent round the rim. Done-mark: each paint's JPEG comment pixie_skin."""
    from PIL import Image
    from scipy import ndimage
    import heroine_brow_strokes as bs
    import heroine_ears as he
    tex = os.path.join(art, "head_tex")
    paints = [fn for fn in sorted(os.listdir(tex)) if fn.startswith("heroine_head") and fn.endswith(".jpg")]
    if faces:
        paints = [fn for fn in paints if fn[len("heroine_head"):-4].lstrip("_") in faces or (fn == "heroine_head.jpg" and "own" in faces)]
    paints = [fn for fn in paints if SKIN_MARK not in bs.comment(os.path.join(tex, fn)) or print("PIXIE_EAR: %s has had it" % fn)]
    if not paints:
        return
    n = 1024
    Z = _zone(art)
    iy, ix, k0, h, t, de, blue, w, we = (Z[k] for k in ("iy", "ix", "k0", "h", "t", "de", "blue", "w", "we"))
    bare = (k0 < 0.2) & (h < SKIN_EAR[0]) & (blue < 0.1)
    face = (blue > 0.9) & (h < SKIN_EAR[0]) & (k0 > 0.99)
    top = (h > SKIN_EAR[1]) & (t > TOP_T[1]) & (de < 0.001)
    mid = (h > SKIN_EAR[1]) & (t > TOP_REF[0]) & (t < TOP_REF[1]) & (de < 0.001)
    Wn, We = np.zeros((n, n), np.float32), np.zeros((n, n), np.float32)
    Wn[iy, ix], We[iy, ix] = w, we
    for fn in paints:
        path = os.path.join(tex, fn)
        img = Image.open(path).convert("RGB")
        size = img.size[0]
        A = es._lin(np.asarray(img, np.float32) / 255)
        a = es._lin(np.asarray(img.resize((n, n), Image.BOX), np.float32) / 255)
        G = a[iy[face], ix[face]].mean(0) * np.array(SKIN_Q) / a[iy[bare], ix[bare]].mean(0)
        Ge = a[iy[mid], ix[mid]].mean(0) / a[iy[top], ix[top]].mean(0)
        Wt = np.clip(ndimage.zoom(Wn, size / n, order=1), 0, 1) if size != n else Wn
        Et = np.clip(ndimage.zoom(We, size / n, order=1), 0, 1) if size != n else We
        Et = np.minimum(Et, 1 - Wt)
        ys, xs = np.nonzero((Wt > 0.002) | (Et > 0.002))
        y0, y1, x0, x1 = max(ys.min() - 64, 0), min(ys.max() + 65, size), max(xs.min() - 64, 0), min(xs.max() + 65, size)
        sub = A[y0:y1, x0:x1]
        low = np.stack([ndimage.gaussian_filter(sub[..., c], SKIN_SIGMA * size / 4096) for c in range(3)], -1)
        new = he.oklab(np.clip((low + SKIN_DETAIL * (sub - low)) * G, 0, 1).astype(np.float64))
        new[..., 1:] *= SKIN_C
        new = np.clip(he.unoklab(new), 0, 1).astype(np.float32)
        ear = np.clip((low + TOP_DETAIL * (sub - low)) * Ge, 0, 1)
        wt, et = Wt[y0:y1, x0:x1, None], Et[y0:y1, x0:x1, None]
        A[y0:y1, x0:x1] = sub * (1 - wt - et) + new * wt + ear * et
        out = np.clip(es._srgb(A) * 255 + 0.5, 0, 255).astype(np.uint8)
        Image.fromarray(out).save(path, quality=95, subsampling=0, comment=(bs.comment(path) + " " + SKIN_MARK).strip().encode("latin-1"))
        if report:
            print("PIXIE_EAR: %s: bared scalp's paint x %s (linear), %d texels; ear's top x %s, %d texels" % (
                fn, np.round(G, 3), int((Wt > 0.5).sum()), np.round(Ge, 3), int((Et > 0.5).sum())))


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--skin" in a:
        pos = [x for x in a if not x.startswith("--")]
        skin(pos[0] if pos else "godot/art/people", pos[1:] or None)
        sys.exit(0)
    if "--shade" in a:
        shade(next((x for x in a if not x.startswith("--")), "godot/art/people"))
        sys.exit(0)
    st = a[a.index("--style") + 1].split(",") if "--style" in a else ["pixie"]
    pos = [x for i, x in enumerate(a) if not x.startswith("--") and (i == 0 or a[i - 1] != "--style")]
    for s_ in st:
        run(pos[0] if pos else "godot/art/people", dry="--dry" in a, style=s_)
