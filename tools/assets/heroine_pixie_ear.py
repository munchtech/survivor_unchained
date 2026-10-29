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

Run after heroine_ear_shape.py --follow-only (and heroine_shape_falloff.py) on each pixie build. Done-mark: the
gltf's asset extras pixie_ear; the .bin rewritten with the gltf's data checksum (Godot reimports on the .gltf).
"""
import os
import sys

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_ear_shape as es  # noqa: E402
from heroine_neck import _Gl  # noqa: E402

MARK = "pixie_ear"
VIEWS = [(az, el) for az in (25, 30, 35, 40, 45, 50, 55, 65) for el in (-5, 0, 5, 10)]
CLEAR = (0.0010, 0.0035)        # m from a sight line: no hair within the first, as it was past the second
RIM_UP = 0.008                  # m over the flap's middle (side on): the rim kept in sight (its top and upper front;
                                # below, her sideburn lies in front of it, as a real one does)
TIP = (0.0008, 0.0035)          # m from her ear's flap: the same (cards and strands, not the cap)
CAP_TIP = (0.0015, 0.0040)      # m from her ear's flap: the braid's and ponytail's cap the same (face 42: their cap,
                                # laid for the old ear, showed as a dark band down the helix's front at the Look turned
                                # 40 and a stroke inside its top at -40; the pixie's cap is as j5 passed it)
PIXIE_CLEAR = (0.0025, 0.0045)  # m from a sight line: the pixie's (a skin margin seen round the rim, not only off it)
PIXIE_TIP = (0.0030, 0.0050)    # m from her ear's flap: the pixie's cards AND cap (face 42 j1, max: its side hair still lay
                                # on the helix's top at the Look turned 40, the owner's "hair still goes over the ear":
                                # 3-4 mm of skin over the ear's top, ~2 mm between the sideburn's tip and its front)
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
        R, D = [], []
        for az, el in VIEWS:
            a, b = np.radians(az), np.radians(el)
            d = np.array([sg * np.sin(a) * np.cos(b), np.sin(b), np.cos(a) * np.cos(b)])    # (glb: x side, y up, z front)
            S = rim_c[:, None, :] + np.arange(0.002, 0.061, 0.001)[None, :, None] * d
            _, ix = T.query(S.reshape(-1, 3))
            inside = (((S.reshape(-1, 3) - Pb[ix]) * Nb[ix]).sum(1) < 0).reshape(S.shape[:2]).any(1)
            R.append(rim_c[~inside])
            D.append(np.repeat(d[None], (~inside).sum(), 0))
        out[sg] = dict(c=E.mean(0), flap=P[f["ear"]], rim=rim, R=np.vstack(R), D=np.vstack(D))
        if report:
            print("PIXIE_EAR: side %+d: %d rim points, %d sight lines kept clear" % (sg, len(rim), len(out[sg]["R"])))
    return out


def line_gap(Q, R, D):
    """Each point's least distance from a sight line (R, D), over the lines it is in front of (nearer the eye)."""
    g = np.full(len(Q), np.inf)
    for i0 in range(0, len(Q), 1024):
        X = Q[i0:i0 + 1024, None, :] - R[None]
        t = (X * D[None]).sum(-1)
        perp = np.linalg.norm(X - t[..., None] * D[None], axis=-1)
        perp[t < 0.001] = np.inf
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
            g = line_gap(V[m], e["R"], e["D"])
            cl = PIXIE_CLEAR if style == "pixie" else CLEAR
            w = _ss((g - cl[0]) / (cl[1] - cl[0]))
            if style == "pixie":
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
    G.g["asset"].setdefault("extras", {})[mark] = "clear %.1f-%.1f mm, tip %.1f-%.1f mm, %d views" % (
        (PIXIE_CLEAR if style == "pixie" else CLEAR)[0] * 1e3, (PIXIE_CLEAR if style == "pixie" else CLEAR)[1] * 1e3, tip[0] * 1e3, tip[1] * 1e3, len(VIEWS))
    if not dry:
        G.save()
        print("PIXIE_EAR: %s written" % path)


if __name__ == "__main__":
    a = sys.argv[1:]
    st = a[a.index("--style") + 1].split(",") if "--style" in a else ["pixie"]
    pos = [x for i, x in enumerate(a) if not x.startswith("--") and (i == 0 or a[i - 1] != "--style")]
    for s_ in st:
        run(pos[0] if pos else "godot/art/people", dry="--dry" in a, style=s_)
