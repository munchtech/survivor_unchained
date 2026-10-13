"""Her upper lids' crease made a soft fold, never a second brow, in her exported glb (heroine.glb).

Her head has no normal map: its shading is its mesh's normals. Under each brow her head's sculpt folds sharply into
the upper lid's crease (its normals turn down 50-60 degrees within 3-4 mm, right under the painted brow), so under
the Look's high key light, her chin lifted 12 degrees and seen a little from below, the crease drew a dark band just
under her brow, about as wide as the brow and parallel to it (the owner, 12 October 2026: "double eyebrow"; on Doe at
the Look the band was 94-97 against 150 on her lid with a flat paint, no AO and no lashes).

This turns her head's normals only (her shape is untouched), over a band from just above each upper lid's lash line
to the brow's lower edge, toward a smooth field across it: the harmonic fill of the normals round the band (the
smoothest field that meets the lid's and the brow's own), so the crease reads as a soft fold. The band is eased in
over the lid, eased out into the brow (where the brow's paint hides the ease) and at the eye's corners. It is found
on the mesh and its UVs, not on screen: the lid's edge is the seam between her face's UV island and her eye socket's;
the brow is where her face's own paint (head_tex/heroine_head[_ID].jpg) is darker than the skin round it, over the
lid. Every face gets it on its own shaped head (face_ID at 1) with its own paint's brows; every other key (the
sliders, the expressions) gets her own face's band on its own normals. Each key's normal deltas are written anew so
that her head's normals under it are the folded ones.

    python tools/assets/heroine_browfold.py godot/art/people/heroine.glb [OUT.glb]
    python tools/assets/heroine_browfold.py --measure [GLB]     (per face: the band, how far its normals turn)

On one already done (its head's extras say brow_fold) it does nothing.
"""
import os
import sys

import numpy as np
from scipy.ndimage import map_coordinates
from scipy.sparse import coo_matrix, csr_matrix
from scipy.sparse.csgraph import connected_components, dijkstra
from scipy.sparse.linalg import splu

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_seam as hs  # noqa: E402  (the glb's reader and writer)

GLB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "godot", "art", "people", "heroine.glb")
MARGIN_NY = -0.5         # (her lid's margin, rolled under from the socket's seam to the lash line, faces down this far)
MARGIN_MAX = 0.0065      # (m: and is no deeper than this from the seam, along her skin)
LID_START = 0.0025       # (m: the band starts this far above the lash line, along her skin, over the lid's front)
LID_EASE = 0.0010        # (and is eased in over this)
KEEP = (0.003, -0.5)     # (points this near the lash line whose normals face down this far keep them)
BROW_EASE = 0.0030       # (eased out over this into the brow, and off the band's sides)
CORNER = 0.0030          # (eased in over this along the lid from each eye's corners)
GAP = (0.009, 0.012)     # (m: the brow's lower edge is held this far over the lash line, along her skin: its crease reaches 9-12 mm)
STRENGTH = 1.0           # (how far toward the smooth field, in the band's middle)
ZONE = (0.0025, 0.025)   # (a brow is looked for this far over the lid's edge)
BROW_DARK = 0.045        # (her paint this much darker than the skin round it, there, is brow)
BLUR, ROUND = 5.0, 24.0  # (texels: the paint's own blur, and the skin round it)


def head(js):
    mats = [m.get("name") for m in js.get("materials", [])]
    for m in js["meshes"]:
        for p in m["primitives"]:
            if "material" in p and mats[p["material"]] == "skin_head":
                return m, p, m.get("extras", {}).get("targetNames", [])
    raise SystemExit("BROWFOLD: no skin_head in the glb")


def _smooth01(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


class Topo:
    """Her head's points welded along its UV seams, its face's island, and each eye's lid edges."""

    def __init__(self, V, F, UV):
        self.V, self.F, self.UV = V, F, UV
        _, self.rep = np.unique(np.round(V / 1e-7).astype(np.int64), axis=0, return_inverse=True)
        self.rep = self.rep.ravel()
        self.n = self.rep.max() + 1
        nv = len(V)
        E = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
        k, lab = connected_components(coo_matrix((np.ones(len(E)), (E[:, 0], E[:, 1])), shape=(nv, nv)), directed=False)
        main = np.bincount(lab).argmax()
        self.main_v = lab == main                       # (original points on her face's island)
        inmain = np.zeros(self.n, bool)
        inmain[self.rep[self.main_v]] = True
        self.inmain = inmain                            # (welded points on it)
        # (one original point per welded point, on her face's island where it has one: its UV)
        self.pick = np.zeros(self.n, np.int64)
        self.pick[self.rep[::-1]] = np.arange(nv)[::-1]
        self.pick[self.rep[self.main_v]] = np.where(self.main_v)[0]
        # (the welded edges of her face's island)
        fm = self.main_v[F[:, 0]]
        Em = np.concatenate([F[fm][:, [0, 1]], F[fm][:, [1, 2]], F[fm][:, [2, 0]]])
        Em = self.rep[Em]
        Em = np.unique(np.sort(Em, 1), axis=0)
        self.E = Em[Em[:, 0] != Em[:, 1]]
        # Each eye's socket: an island of its own, beside her face's, sharing her lid's edges with it.
        self.upper, self.lower, self.s_in, self.s_out = [], [], {}, {}
        for c in range(k):
            if c == main:
                continue
            m = lab == c
            cen = V[m].mean(0)
            if m.sum() < 200 or abs(cen[0]) < 0.01:
                continue
            w = np.zeros(self.n, bool)
            w[self.rep[m]] = True
            edge = np.where(w & inmain)[0]
            P = V[self.pick[edge]]
            a, b = edge[np.argmin(np.abs(P[:, 0]))], edge[np.argmax(np.abs(P[:, 0]))]   # (inner, outer corners)
            pa, pb = V[self.pick[a]], V[self.pick[b]]
            line = pa[1] + (P[:, 0] - pa[0]) / (pb[0] - pa[0]) * (pb[1] - pa[1])
            up = edge[P[:, 1] >= line - 1e-9]
            lo = edge[P[:, 1] <= line + 1e-9]
            # (her upper lid's edge in order from the inner corner, and how far along it each point is from each corner)
            o = up[np.argsort(np.abs(V[self.pick[up], 0]))]
            seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(V[self.pick[o]], axis=0), axis=1))]
            for i, s in zip(o, seg):
                self.s_in[i], self.s_out[i] = s, seg[-1] - s
            self.upper.append(o)
            self.lower.append(lo)
        assert len(self.upper) == 2, "found %d eye sockets" % len(self.upper)

    def graph(self, P):
        """Her face's island as a graph, its edges as long as they are on the shape P (welded points)."""
        d = np.linalg.norm(P[self.E[:, 0]] - P[self.E[:, 1]], axis=1) + 1e-9
        return csr_matrix((np.r_[d, d], (np.r_[self.E[:, 0], self.E[:, 1]], np.r_[self.E[:, 1], self.E[:, 0]])),
                          shape=(self.n, self.n))


def paint_dark(tex):
    """Her paint's darkness against the skin round it (0 where lighter), per texel."""
    if not os.path.exists(tex):
        raise SystemExit("BROWFOLD: no paint " + tex)
    try:
        import cv2
        im = cv2.imread(tex, cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255
        return cv2.GaussianBlur(im, (0, 0), ROUND) - cv2.GaussianBlur(im, (0, 0), BLUR)
    except ImportError:  # (Blender's Python, in heroine_outfits.py: the same blurs, near enough)
        from scipy.ndimage import gaussian_filter
        try:
            from PIL import Image
            im = np.asarray(Image.open(tex).convert("L")).astype(np.float32) / 255
        except ImportError:
            import bpy
            img = bpy.data.images.load(tex, check_existing=False)
            w, h = img.size
            px = np.empty(w * h * 4, np.float32)
            img.pixels.foreach_get(px)
            bpy.data.images.remove(img)
            px = px.reshape(h, w, 4)[::-1]  # (Blender's rows run bottom up; its jpg reads as sRGB values)
            im = px[..., 0] * 0.299 + px[..., 1] * 0.587 + px[..., 2] * 0.114
        return gaussian_filter(im, ROUND, truncate=3.0) - gaussian_filter(im, BLUR, truncate=3.0)


def margin(T, G, N, d_seam, d_lo):
    """Her upper lids' margins (welded points): the skin rolled under from the socket's seam to the lash line, facing
    down (N: her normals, welded, unit), grown from the seam; and the lash line, its edge on the lid's front."""
    up = np.concatenate(T.upper)
    side = T.inmain & (d_seam < d_lo)
    ok = side & (N[:, 1] < MARGIN_NY) & (d_seam < MARGIN_MAX)
    ok[up] = True
    E = T.E[ok[T.E[:, 0]] & ok[T.E[:, 1]]]
    _, lab = connected_components(coo_matrix((np.ones(len(E)), (E[:, 0], E[:, 1])), shape=(T.n, T.n)), directed=False)
    marg = ok & np.isin(lab, np.unique(lab[up]))
    a, b = T.E[:, 0], T.E[:, 1]
    line = np.zeros(T.n, bool)
    line[a[marg[a] & side[b] & ~marg[b]]] = True
    line[b[marg[b] & side[a] & ~marg[a]]] = True
    return marg, line


def band(T, P, N, dark):
    """The band's weights (0-1) per welded point on the shape P (welded) with its normals N (welded, unit), its brows
    from the paint's darkness map."""
    G = T.graph(P)
    up = np.concatenate(T.upper)
    lo = np.concatenate(T.lower)
    d_seam, _, src = dijkstra(G, indices=up, min_only=True, return_predecessors=True)
    d_lo = dijkstra(G, indices=lo, min_only=True)
    # (her lid's edge is rolled under it, 3-6 mm from the socket's seam to the lash line, facing down: the band is
    # measured from the lash line, that margin's edge on the lid's front, and only off the margin. Not from the
    # lashes: their tips lie on her skin up in the crease, so the points nearest them are no lash line)
    marg, line = margin(T, G, N, d_seam, d_lo)
    d_up = dijkstra(G, indices=np.where(line)[0], min_only=True)
    beyond = ~marg
    uv = T.UV[T.pick]
    H, W = dark.shape
    dk = map_coordinates(dark, [uv[:, 1] * H - 0.5, uv[:, 0] * W - 0.5], order=1, mode="nearest")
    zone = T.inmain & beyond & (d_up > ZONE[0]) & (d_up < ZONE[1]) & (d_seam < d_lo)
    brow = zone & (dk > BROW_DARK)
    # (only its big pieces: each brow is one, specks of dark skin are not)
    Eb = T.E[brow[T.E[:, 0]] & brow[T.E[:, 1]]]
    k, lab = connected_components(coo_matrix((np.ones(len(Eb)), (Eb[:, 0], Eb[:, 1])), shape=(T.n, T.n)), directed=False)
    cnt = np.bincount(lab[brow], minlength=k)
    big = np.where(cnt >= max(30, 0.15 * cnt.max()))[0]
    brow &= np.isin(lab, big)
    d_br = dijkstra(G, indices=np.where(brow)[0], min_only=True)
    # (the brow's lower edge over the lid: the paint's brows are found point by point only roughly (hairs, freckles,
    # a painted lash line), so each face takes the median over the middle half of its lids, held to GAP)
    ln = np.where(line)[0]
    sm = src[ln].clip(0)
    mid = ln[[min(T.s_in.get(i, 0), T.s_out.get(i, 0)) > 0.25 * (T.s_in.get(i, 0) + T.s_out.get(i, 0)) for i in sm]]
    g = d_br[mid]
    gap = float(np.clip(np.median(g[np.isfinite(g)]) if np.isfinite(g).any() else GAP[1], *GAP))
    excess = d_up - gap
    s = np.array([min(T.s_in.get(i, 0), T.s_out.get(i, 0)) for i in src.clip(0)])
    w = _smooth01((d_up - LID_START) / LID_EASE) * (1 - _smooth01(excess / BROW_EASE)) * _smooth01(s / CORNER)
    w[~(T.inmain & beyond & (d_seam < d_lo) & (d_up < ZONE[1]) & np.isfinite(d_up))] = 0
    # (near the lash line, skin that faces down is the lid's edge rolling under: it keeps its own normals)
    keep = (d_up < KEEP[0]) & (N[:, 1] < KEEP[1])
    w[keep] = 0
    return np.clip(w * STRENGTH, 0, 1), dict(brow=brow, d_up=d_up, gap=gap, raw_gap=g, dark=dk, marg=marg, line=line,
                                             keep=keep, d_seam=d_seam, s=s, src=src)


class Fill:
    """The harmonic fill over a band's points (weights > 0), from the normals round it, on the shape P (welded)."""

    def __init__(self, T, P, w):
        self.T, self.w = T, w
        self.free = np.where(w > 1e-4)[0]
        idx = -np.ones(T.n, np.int64)
        idx[self.free] = np.arange(len(self.free))
        self.idx = idx
        a, b = T.E[:, 0], T.E[:, 1]
        c = 1 / (np.linalg.norm(P[a] - P[b], axis=1) + 1e-6)
        i, j, cc = np.r_[a, b], np.r_[b, a], np.r_[c, c]
        keep = idx[i] >= 0
        i, j, cc = i[keep], j[keep], cc[keep]
        nf = len(self.free)
        diag = np.bincount(idx[i], weights=cc, minlength=nf)
        inner = idx[j] >= 0
        A = coo_matrix((np.r_[diag, -cc[inner]], (np.r_[np.arange(nf), idx[i][inner]], np.r_[np.arange(nf), idx[j][inner]])),
                       shape=(nf, nf)).tocsc()
        self.lu = splu(A)
        self.bi, self.bj, self.bc = idx[i][~inner], j[~inner], cc[~inner]

    def __call__(self, N):
        """N (welded, unit) folded: toward the fill by the band's weights."""
        rhs = np.zeros((len(self.free), 3))
        np.add.at(rhs, self.bi, self.bc[:, None] * N[self.bj])
        S = N.copy()
        S[self.free] = self.lu.solve(rhs)
        out = N.copy()
        w = self.w[self.free, None]
        f = (1 - w) * N[self.free] + w * S[self.free]
        out[self.free] = f / (np.linalg.norm(f, axis=1)[:, None] + 1e-12)
        return out


def _unit(v):
    return v / (np.linalg.norm(v, axis=1)[:, None] + 1e-12)


def plan(js, binc, glb_path, faces=None):
    """Every face's band and fill. Returns (T, hm, hp, names, bands {face: (w, info, fill)})."""
    hm, hp, names = head(js)
    V = hs._read(js, binc, hp["attributes"]["POSITION"])
    UV = hs._read(js, binc, hp["attributes"]["TEXCOORD_0"])
    F = hs._read(js, binc, hp["indices"]).reshape(-1, 3)
    T = Topo(V, F, UV)
    tex = os.path.join(os.path.dirname(os.path.abspath(glb_path)), "head_tex")
    if not os.path.isdir(tex):  # (a glb written elsewhere: the paints in the repo)
        tex = os.path.join(os.path.dirname(os.path.abspath(GLB)), "head_tex")
    keys = {n: i for i, n in enumerate(names)}
    hn = hs._read(js, binc, hp["attributes"]["NORMAL"])
    bands = {}
    for face in faces or ["own"] + sorted(n[5:] for n in names if n.startswith("face_") and n[-1] not in "+-"):
        P, N = V.copy(), hn.copy()
        if face != "own":
            t = hp["targets"][keys["face_" + face]]
            P = P + hs._read(js, binc, t["POSITION"])
            if "NORMAL" in t:
                N = N + hs._read(js, binc, t["NORMAL"])
        Pw, Nw = P[T.pick], _unit(N[T.pick])
        w, info = band(T, Pw, Nw, paint_dark(os.path.join(tex, "heroine_head%s.jpg" % ("" if face == "own" else "_" + face))))
        bands[face] = (w, info, Fill(T, Pw, w), Pw)
    return T, hm, hp, names, bands


def fold(path, out=None):
    js, binc = hs._load(path)
    hm, hp, names = head(js)
    if "brow_fold" in hm.get("extras", {}):
        print("BROWFOLD: already done in", path, "- nothing done")
        return
    chunks = {i: binc[bv.get("byteOffset", 0):bv.get("byteOffset", 0) + bv["byteLength"]] for i, bv in enumerate(js["bufferViews"])}
    T, hm, hp, names, bands = plan(js, binc, path)
    hn = hs._read(js, binc, hp["attributes"]["NORMAL"])
    rep = T.rep
    w0, _, fill0, _ = bands["own"]
    hn_w = _unit(hn[T.pick])
    hn2_w = fill0(hn_w)
    ch0 = w0 > 1e-4
    hn2 = hn.copy()
    m0 = ch0[rep]
    hn2[m0] = hn2_w[rep[m0]]
    # (her duplicates along seams in the band: how far apart their normals were)
    ang = lambda a, b: np.degrees(np.arccos(np.clip((_unit(a) * _unit(b)).sum(1), -1, 1)))
    print("BROWFOLD: own band %d points (%d at full), normals turned up to %.1f deg (mean %.1f over the band)" % (
        ch0.sum(), (w0 > 0.99).sum(), ang(hn_w[ch0], hn2_w[ch0]).max(), ang(hn_w[ch0], hn2_w[ch0]).mean()))
    region = (bands["own"][1]["d_up"] < ZONE[1] + 0.01)
    report = []
    for k, t in enumerate(hp["targets"]):
        if "NORMAL" not in t:
            continue
        name = names[k] if k < len(names) else str(k)
        face = name[5:] if name.startswith("face_") and name[-1] not in "+-" else "own"
        wk, _, fillk, _ = bands[face]
        dn = hs._read(js, binc, t["NORMAL"])
        dp = hs._read(js, binc, t["POSITION"]) if "POSITION" in t else np.zeros_like(dn)
        chk = wk > 1e-4
        touched = (np.abs(dn).max(1) > 0) | (np.abs(dp).max(1) > 0)
        if not (touched & region[rep]).any() and face == "own":
            # (a key that moves nothing near her eyes: under it her base's fold holds as it is)
            if np.abs(dn[m0]).max() == 0:
                continue
        nk_w = _unit(hn[T.pick] + dn[T.pick])
        nk2_w = fillk(nk_w)
        mk = (chk | ch0)[rep]
        dn2 = dn.copy()
        dn2[mk] = nk2_w[rep[mk]] - hn2[mk]
        if np.abs(dn2 - dn).max() > 1e-7:
            hs._set(js, chunks, t["NORMAL"], dn2)
            if face != "own":
                a = ang(nk_w[chk], nk2_w[chk])
                report.append("%s %d pts, up to %.1f deg (mean %.1f)" % (face, chk.sum(), a.max(), a.mean()))
    hs._set(js, chunks, hp["attributes"]["NORMAL"], hn2)
    hm.setdefault("extras", {})["brow_fold"] = {"margin_ny": MARGIN_NY, "margin_max": MARGIN_MAX, "lid_start": LID_START,
                                                "lid_ease": LID_EASE, "keep": list(KEEP), "brow_ease": BROW_EASE,
                                                "corner": CORNER, "strength": STRENGTH}
    hs._save(out or path, js, chunks)
    print("BROWFOLD: faces " + "; ".join(report))
    print("BROWFOLD: written", out or path)


def measure(path):
    js, binc = hs._load(path)
    T, hm, hp, names, bands = plan(js, binc, path)
    for face, (w, info, fill, P) in bands.items():
        g = info["raw_gap"][np.isfinite(info["raw_gap"])]
        print("%-9s band %4d pts (%4d full), brow %4d pts; lid to brow over the lids' middles %.1f-%.1f mm, "
              "median %.1f, held %.1f" % (face, (w > 1e-4).sum(), (w > 0.99).sum(), info["brow"].sum(),
                                          1000 * g.min(), 1000 * g.max(), 1000 * np.median(g), 1000 * info["gap"]))


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--measure":
        measure(a[1] if len(a) > 1 else GLB)
    else:
        fold(a[0] if a else GLB, a[1] if len(a) > 1 else None)
