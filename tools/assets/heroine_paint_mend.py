"""Her body paint mended where faces read the texture's unused fill (Body 12, 26 Oct: the "cut" dashes).

    python tools/assets/heroine_paint_mend.py IN.glb OUT.glb [--report]

The baked body paint (Material_0.001's base colour, 2048) leaves its unused texels a dark red (about 84,14,12 to
150,91,85), not dilated. A few faces have UVs squeezed to a texel or two that sit in, or bilinear-tap into, that fill:
on the body of record since Body 8, 16 faces on her LEFT upper arm and elbow (three short strips: mid upper arm front,
above the elbow, the elbow's outer side) and ~325 elsewhere. In game they draw as short dark red-brown dashes (the town
close-up's "cut", luminance 77 against 158; the Look's streak by her breast). Neither the geometry, the normals, the
tone map nor the freckles cause them (dbg shots: paint alone keeps them, flat paint removes them).

Mend: (1) every face's paint is sampled (bilinear, 15 points: vertices, edge midpoints, interior); a face is BAD when a
sample is 25+ levels darker or redder than the median of its two-ring 3D neighbours AND a sample's taps touch texels no
face covers. (2) Each bad face's taps (and a 1-texel ring) take its neighbours' median colour, never over a texel a good
face covers. (3) Every texel no face covers takes its nearest covered texel's colour (a full dilation, so no mip or
filter can reach the dark fill again). Covered texels of good faces are never changed. Other textures untouched.
"""
import io
import os
import struct
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from heroine_arm_tone import _read, _write  # noqa: E402

DARK = 25.0


def _get(g, binc, ai):
    a = g["accessors"][ai]
    bv = g["bufferViews"][a["bufferView"]]
    n = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[a["type"]]
    dt = np.dtype({5121: "u1", 5123: "u2", 5125: "u4", 5126: "f4"}[a["componentType"]])
    o = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    return np.frombuffer(bytes(binc[o:o + dt.itemsize * n * a["count"]]), dt).reshape(a["count"], n)


def _raster(UV, F, W, H):
    from PIL import Image, ImageDraw
    im = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(im)
    for t in F:
        d.polygon([(UV[i, 0] * W - 0.5, UV[i, 1] * H - 0.5) for i in t], fill=255, outline=255)
    return np.array(im) > 0


def _taps(U, W, H):
    """The 4 texels each UV sample's bilinear filter reads (x, y int arrays, shape (..., 4))."""
    x = U[..., 0] * W - 0.5
    y = U[..., 1] * H - 0.5
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    xs = np.stack([x0, x0 + 1, x0, x0 + 1], -1).clip(0, W - 1)
    ys = np.stack([y0, y0, y0 + 1, y0 + 1], -1).clip(0, H - 1)
    return xs, ys


def mend(P, UV, F, img):
    from scipy import ndimage, sparse
    H, W = img.shape[:2]
    im = img[..., :3].astype(float)
    lum = im @ [0.2126, 0.7152, 0.0722]
    red = im[..., 0] - im[..., 1]
    bc = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1], [.5, .5, 0], [0, .5, .5], [.5, 0, .5], [1 / 3, 1 / 3, 1 / 3],
                   [.6, .2, .2], [.2, .6, .2], [.2, .2, .6], [.45, .45, .1], [.1, .45, .45], [.45, .1, .45],
                   [.8, .1, .1], [.1, .8, .1]])
    U = np.einsum("sk,fkd->fsd", bc, UV[F])                       # (nF, 15, 2)
    xs, ys = _taps(U, W, H)
    cov = _raster(UV, F, W, H)
    tl, tr = lum[ys, xs].mean(-1), red[ys, xs].mean(-1)         # per sample (tap mean ~ bilinear)
    fcol = im[ys, xs].mean((1, 2))                               # per face colour
    # two-ring 3D neighbours (welded by position)
    key = np.round(P * 2e4).astype(np.int64)
    _, inv = np.unique(key, axis=0, return_inverse=True)
    Fw = inv.ravel()[F]
    nV = Fw.max() + 1
    rows = np.repeat(np.arange(len(F)), 3)
    A = sparse.coo_matrix((np.ones(len(rows)), (rows, Fw.ravel())), shape=(len(F), nV)).tocsr()
    N1 = (A @ A.T).tocsr()
    N2 = (N1 @ N1).tocsr()
    flum = fcol @ [0.2126, 0.7152, 0.0722]
    fred = fcol[:, 0] - fcol[:, 1]

    def ring_median(vals, ok):
        out = np.empty((len(F),) + vals.shape[1:])
        ip, ix = N2.indptr, N2.indices
        for f in range(len(F)):
            nb = ix[ip[f]:ip[f + 1]]
            nb = nb[ok[nb] & (nb != f)]
            out[f] = np.median(vals[nb], 0) if len(nb) else vals[f]
        return out

    ok0 = np.ones(len(F), bool)
    ref_l = ring_median(flum, ok0)
    ref_r = ring_median(fred, ok0)
    off = (tl < ref_l[:, None] - DARK) | (tr > ref_r[:, None] + DARK)  # (nF, 15)
    unc = ~cov[ys, xs].all(-1)                                         # sample's taps touch uncovered texels
    bad = (off & unc).any(1)
    ref = ring_median(fcol, ~bad)
    cov_good = _raster(UV, F[~bad], W, H)
    out = im.copy()
    fixed = np.zeros((H, W), bool)
    for f in np.nonzero(bad)[0]:
        x0, x1 = max(xs[f].min() - 1, 0), min(xs[f].max() + 2, W)
        y0, y1 = max(ys[f].min() - 1, 0), min(ys[f].max() + 2, H)
        win = ~cov_good[y0:y1, x0:x1]
        out[y0:y1, x0:x1][win] = ref[f]
        fixed[y0:y1, x0:x1] |= win
    have = cov_good | fixed
    _, (iy, ix) = ndimage.distance_transform_edt(~have, return_indices=True)
    fill = ~have
    out[fill] = out[iy[fill], ix[fill]]
    return np.clip(np.round(out), 0, 255).astype(np.uint8), bad, int(fixed.sum()), int(fill.sum())


def run(path_in, path_out, report=False):
    from PIL import Image
    g, binc = _read(path_in)
    me = [m for m in g["meshes"] if m["name"] == "Mesh_0"][0]
    p = me["primitives"][0]
    mat = g["materials"][p["material"]]
    ti = mat["pbrMetallicRoughness"]["baseColorTexture"]["index"]
    users = [q for q in me["primitives"] if g["materials"][q["material"]]["pbrMetallicRoughness"]
             .get("baseColorTexture", {}).get("index") == ti]
    assert len(users) == 1, "the body paint is shared; mend it per primitive first"
    imd = g["images"][g["textures"][ti]["source"]]
    bv = g["bufferViews"][imd["bufferView"]]
    o = bv.get("byteOffset", 0)
    img = np.array(Image.open(io.BytesIO(bytes(binc[o:o + bv["byteLength"]]))).convert("RGB"))
    P = _get(g, binc, p["attributes"]["POSITION"]).astype(float)
    UV = _get(g, binc, p["attributes"]["TEXCOORD_0"]).astype(float)
    F = _get(g, binc, p["indices"]).reshape(-1, 3).astype(int)
    new, bad, nfix, nfill = mend(P, UV, F, img)
    c = P[F].mean(1)
    larm = bad & (c[:, 0] > 0.15) & (c[:, 1] > 1.1)
    rarm = bad & (c[:, 0] < -0.15) & (c[:, 1] > 1.1)
    print("MEND faces bad %d (left arm %d, right arm %d); texels set %d; fill texels %d" % (
        bad.sum(), larm.sum(), rarm.sum(), nfix, nfill))
    if report:
        for f in np.nonzero(larm | rarm)[0]:
            print("   f%d rest %s uv %s" % (f, c[f].round(3), UV[F[f]].mean(0).round(4)))
    buf = io.BytesIO()
    Image.fromarray(new).save(buf, "PNG", optimize=False)
    png = buf.getvalue()
    while len(binc) % 4:
        binc.append(0)
    g["bufferViews"].append({"buffer": 0, "byteOffset": len(binc), "byteLength": len(png)})
    binc.extend(png)
    imd["bufferView"] = len(g["bufferViews"]) - 1
    imd["mimeType"] = "image/png"
    g.setdefault("extras", {})["paint_mend"] = {"bad_faces": int(bad.sum()), "fill_texels": nfill}
    _write(path_out, g, binc)
    return bad


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    run(a[0], a[1], "--report" in sys.argv)
