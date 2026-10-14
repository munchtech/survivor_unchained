"""Her smile's upper lip without a trough at its border, in her exported glb (heroine.glb).

The smile seam (solver seam1, 14 October 2026; judge j2: in smile .8 and smile with her mouth open, a dashed seam just
above the Cupid's bow on Highborn, Vixen, Doe, Moonlit, Hard-won and Fey, a dark liner along own's upper lip, a
doubled line on Sunborn, Saffron and Wildling). The cause is her smile key's shape (MakeHuman's mouth-corner-puller
as fitted to her head): it draws her upper lip's red back 2.3-2.9 mm and leaves the skin over it where it is, and
the whole change happens across the one or two rows of points at her vermilion border (at her mouth's middle: 2.66 mm
back 0.4 mm under the border, 0.3 mm at it, 0.1 mm 0.4 mm over it). Her sculpt's border is a shelf facing up (her
upper lip's red juts 1.8 mm out of the philtrum's plane); drawn back so, the shelf turns to face down and a groove
1.3-1.8 mm deep opens between the skin and the lip's front, in shade from the lamps over her: the dark line. On her
own face it lies on the border (a liner); on the other faces, whose keys put the paint's red and the border
elsewhere on the same points, it lies over the bow (a dashed seam, by the mesh's rows) or beside the paint's own
edge (a doubled line). Every face shares the one smile key, so it is mended there, once for all of them.

Her open mouth's key (MakeHuman's mouth-open) has the same cliff at the same rows: it draws her face over the border
(her philtrum and her nose's foot) down 2.5-3.8 mm at full and her upper lip's red not at all (up 0.2 mm), so at
mouth_open .6 the border's rows turn over (the lip's top row 1.1 mm over the skin's lowest), and with a smile (smo) the
fold is the seam's other half. So both keys (KEYS) are mended alike.

So: in a band across her upper lip's border (B_LO under it to B_HI over it, as the smile key's own move finds it
in each column: where its draw-back falls to half the lip's), each key's move is made the smoothest that meets the
key's own moves round the band (harmonic: the band's points each the cotangent-weighted mean of their neighbours'),
so her upper lip's red moves as before and the change eases off up her philtrum; the band stops under her nose
(no point whose rest normal faces further down than NOSE_NY), and none of it past X_OUT off her mouth's middle
(eased in from X_IN). Each key's normals turn with its new shape. Her rest pose and every other key are untouched.

    python tools/assets/heroine_smile_lip.py [GLB [OUT]]

heroine_outfits.py runs it on the body it exports, after heroine_mouth.seat. On one done already (her head's
extras say smile_lip) it does nothing. Numpy and scipy (it runs in Blender's Python too).
"""
import os
import sys

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_seam as hs  # noqa: E402
import heroine_mouth as hmo  # noqa: E402

GLB = hmo.GLB
KEYS = tuple(os.environ.get("SMILE_LIP_KEYS", "smile,mouth_open").split(","))
FIND = "smile"                 # (the key whose draw-back finds her border)
# (m: the band across her border, under it and over it)
B_LO = float(os.environ.get("SMILE_LIP_LO_MM", "2.0")) / 1000
B_HI = float(os.environ.get("SMILE_LIP_HI_MM", "5.0")) / 1000
NOSE_NY = -0.55                # (the band stops under her nose: no point whose rest normal faces further down)
X_FIND = 0.018                 # (m off her mouth's middle: the border looked for out to here; out past it, its last)
X_IN, X_OUT = float(os.environ.get("SMILE_LIP_XIN_MM", "16")) / 1000, float(os.environ.get("SMILE_LIP_XOUT_MM", "21")) / 1000
COL_W = 0.0006                 # (m: a column's half width, as the border is looked for)


def _weld(P):
    """Her head's points as one per place (the exporter splits them along UV seams): (first index, inverse)."""
    _, first, inv = np.unique(np.round(P / 1e-6).astype(np.int64), axis=0, return_index=True, return_inverse=True)
    return first, inv.ravel()


def vnormals(V, T):
    """Corner-angle-weighted vertex normals (as Blender's) of the welded mesh (V, T)."""
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    fn = np.cross(b - a, c - a)
    fn /= np.linalg.norm(fn, axis=1)[:, None] + 1e-20
    acc = np.zeros_like(V)
    for k, (p, q, r) in enumerate(((a, b, c), (b, c, a), (c, a, b))):
        u, v = q - p, r - p
        ang = np.arccos(np.clip((u * v).sum(1) / (np.linalg.norm(u, axis=1) * np.linalg.norm(v, axis=1) + 1e-20), -1, 1))
        np.add.at(acc, T[:, k], fn * ang[:, None])
    return acc / (np.linalg.norm(acc, axis=1)[:, None] + 1e-20)


def cot_laplacian(V, T):
    """The cotangent weights of the mesh (V, T) as a sparse symmetric matrix W (W[i, j] the weight of edge ij, the
    weights clamped at zero from under)."""
    n = len(V)
    rows, cols, vals = [], [], []
    for i, j, k in ((0, 1, 2), (1, 2, 0), (2, 0, 1)):
        u, v = V[T[:, i]] - V[T[:, k]], V[T[:, j]] - V[T[:, k]]
        cot = (u * v).sum(1) / (np.linalg.norm(np.cross(u, v), axis=1) + 1e-20)
        rows += [T[:, i], T[:, j]]
        cols += [T[:, j], T[:, i]]
        vals += [0.5 * cot, 0.5 * cot]
    W = sparse.coo_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(n, n)).tocsr()
    W.data = np.maximum(W.data, 1e-6)
    return W


def border(V, D, line, mid):
    """Her upper lip's border per column as the smile key's move finds it (where its draw-back, going up from her
    lip, falls to half the lip's), at x = mid + every 0.5 mm out to X_FIND: (xs, ys), NaN where no lip is found."""
    xs = mid + np.arange(-X_FIND, X_FIND + 1e-6, 0.0005)
    ys = np.full(len(xs), np.nan)
    r = -D[:, 2]
    for k, x in enumerate(xs):
        s = np.where((np.abs(V[:, 0] - x) < COL_W) & (V[:, 1] > line - 0.002) & (V[:, 1] < line + 0.014) & (V[:, 2] > 0.075))[0]
        if len(s) < 4:
            continue
        s = s[np.argsort(-V[s, 1])]
        lip = (V[s, 1] < line + 0.010)
        if not lip.any():
            continue
        rl = r[s][lip].max()
        if rl < 0.0004:
            continue
        # (the first point, coming down, drawn back more than half the lip's; the border between it and the one over)
        i = int(np.argmax(r[s] >= 0.5 * rl))
        if i == 0:
            continue
        a, b = s[i - 1], s[i]
        t = (0.5 * rl - r[a]) / max(r[b] - r[a], 1e-9)
        ys[k] = V[a, 1] + t * (V[b, 1] - V[a, 1])
    return xs, ys


def _smooth_nan(ys, sig=2.0):
    """ys (NaN where missing) filled across its gaps and out to its ends by the nearest, and smoothed (sig samples)."""
    ok = np.isfinite(ys)
    x = np.arange(len(ys))
    y = np.interp(x, x[ok], ys[ok])
    k = np.arange(-int(3 * sig), int(3 * sig) + 1)
    g = np.exp(-0.5 * (k / sig) ** 2)
    pad = np.r_[np.full(len(k) // 2, y[0]), y, np.full(len(k) // 2, y[-1])]
    return np.convolve(pad, g / g.sum(), mode="valid")


def band_of(V, N, D, line, mid):
    """The band across her upper lip's border (welded points V, their rest normals N, the finding key's move D):
    (a mask of its points, the border (xs, ys), each point's share of the mend (1 to X_IN, none past X_OUT))."""
    xs, ys = border(V, D, line, mid)
    if np.isfinite(ys).sum() < 0.5 * len(ys):
        raise SystemExit("SMILE_LIP: her upper lip's border found in only %d of %d columns" % (np.isfinite(ys).sum(), len(ys)))
    ys = _smooth_nan(ys)
    yb = np.interp(V[:, 0], xs, ys)
    ax = np.abs(V[:, 0] - mid)
    band = ((V[:, 1] > yb - B_LO) & (V[:, 1] < yb + B_HI) & (N[:, 1] > NOSE_NY) & (ax < X_OUT) & (V[:, 2] > 0.075))
    share = 1 - hmo._s01((ax - X_IN) / (X_OUT - X_IN))
    return band, (xs, ys), share


def harmonic(V, T, D, band):
    """D on the band's points replaced by the smoothest field that meets D round it (each band point the
    cotangent-weighted mean of its neighbours')."""
    W = cot_laplacian(V, T)
    L = sparse.diags(np.asarray(W.sum(1)).ravel()) - W
    free, fixed = np.where(band)[0], np.where(~band)[0]
    Lff = L[free][:, free].tocsc()
    Lfb = L[free][:, fixed]
    H = D.copy()
    for c in range(3):
        H[free, c] = spsolve(Lff, -Lfb @ D[fixed, c])
    return H


def ease(js, binc, chunks, hm, hp, keys=KEYS):
    names = hm.get("extras", {}).get("targetNames", [])
    if "smile_lip" in hm.get("extras", {}):
        print("SMILE_LIP: already done - nothing done")
        return False
    P = hs._read(js, binc, hp["attributes"]["POSITION"])
    N = hs._read(js, binc, hp["attributes"]["NORMAL"])
    T = hs._read(js, binc, hp["indices"]).astype(np.int64).reshape(-1, 3)
    line = hmo.lips_line(P, hs._read(js, binc, hp["targets"][names.index("mouth_open")]["POSITION"]))
    first, inv = _weld(P)
    n = len(first)
    Tw = inv[T]
    Tw = Tw[(Tw[:, 0] != Tw[:, 1]) & (Tw[:, 1] != Tw[:, 2]) & (Tw[:, 2] != Tw[:, 0])]
    Vw, Nw = P[first], N[first]
    cnt = np.bincount(inv, minlength=n)[:, None]

    def welded(D):
        out = np.zeros((n, 3))
        np.add.at(out, inv, D)
        return out / cnt

    mid = float(np.median(Vw[(np.abs(Vw[:, 1] - line - 0.004) < 0.008) & (np.abs(Vw[:, 0]) < 0.03) & (Vw[:, 2] > 0.085), 0]))
    band, (xs, ys), share = band_of(Vw, Nw, welded(hs._read(js, binc, hp["targets"][names.index(FIND)]["POSITION"])), line, mid)
    done = {}
    for key in keys:
        tgt = hp["targets"][names.index(key)]
        D = hs._read(js, binc, tgt["POSITION"])
        Dw = welded(D)
        D2w = Dw + share[:, None] * (harmonic(Vw, Tw, Dw, band) - Dw)
        D2 = D2w[inv]
        if "NORMAL" in tgt:
            dN = hs._read(js, binc, tgt["NORMAL"])
            turn = (vnormals(Vw + D2w, Tw) - vnormals(Vw + Dw, Tw))[inv]
            rows = np.abs(turn).max(1) > 1e-7
            a = N[rows] + dN[rows] + turn[rows]
            dN2 = dN.copy()
            dN2[rows] = a / np.linalg.norm(a, axis=1)[:, None] - N[rows]
            hs._set(js, chunks, tgt["NORMAL"], dN2)
        hs._set(js, chunks, tgt["POSITION"], D2, minmax=True)
        done[key] = round(1000 * float(np.linalg.norm(D2 - D, axis=1).max()), 2)
    hm.setdefault("extras", {})["smile_lip"] = {"band_mm": [B_LO * 1000, B_HI * 1000], "points": int(band.sum()),
                                                "most_mm": done}
    print("SMILE_LIP: %s eased across her upper lip's border on %d points (moved at most %s mm); the border %.1f..%.1f mm "
          "over her lips' line (y %.4f), her mouth's middle x %.1f mm" % (
              ", ".join(keys), int(band.sum()), done, 1000 * (np.min(ys) - line), 1000 * (np.max(ys) - line), line, 1000 * mid))
    return True


def run(path, out=None):
    js, binc = hs._load(path)
    chunks = {i: binc[bv.get("byteOffset", 0):bv.get("byteOffset", 0) + bv["byteLength"]] for i, bv in enumerate(js["bufferViews"])}
    hm, hp = hmo._prim(js, "skin_head")
    if ease(js, binc, chunks, hm, hp):
        hs._save(out or path, js, chunks)
    elif out and out != path:
        open(out, "wb").write(open(path, "rb").read())


if __name__ == "__main__":
    a = sys.argv[1:]
    run(a[0] if a else GLB, a[1] if len(a) > 1 else None)
