"""Her face paint's colour eased into her neck's under her jaw, in each head's paint (Face 35, 21 October 2026).

Since the 10 October jaw cut (heroine_jaw_cut.py) her neck under the jaw is her head's own skin, but the face
paint above the cut stays the portrait's: 8 to 12 Oklab L lighter and a little greyer, so every face showed a pale
line along the jaw over a darker neck (the owner: "a stark change in color from top of neck / face into the rest
of the body ... a clearly visible line"). This removes that step in low-frequency colour only, by a smooth gain
field over her neck, and leaves every pore and freckle as it was:

  1. her head's points welded (UV seams joined), the paint padded outside its islands and low-passed (2 mm) and
     read at each point, as log linear RGB;
  2. on the mesh, a correction d is solved (least squares over edges, Poisson): zero on her face (the face paint's
     alpha full, so her face keeps its look) and at SPLIT and below (her neck stays her body's there), and
     elsewhere following her paint's own changes except across the face paint's edge under her jaw (its alpha's
     ramp, on her neck's side, to ear height), where the change is asked to be none. So her neck is lifted to her
     face's edge colour right under the jaw and eased back to its own colour over the whole neck down to SPLIT
     (several cm), around the sides as far as the cut goes;
  3. exp(d), laid per texel through the mesh's triangles (continuous in 3D, so no line along UV island edges, and
     texels outside the islands take the nearest inside's), multiplies the full-resolution paint in linear light.

    python tools/assets/heroine_jaw_blend.py [face ...]       (no faces: all ten paints in godot/art/people/head_tex)
    python tools/assets/heroine_jaw_blend.py --out DIR face   (written to DIR instead, for a try with --head-paint)

Run-once: heroine_face/jaw_blend_done.json keeps each written paint's sha1; a paint that still has it is skipped.
A paint laid again (heroine_face.py, heroine_jaw_cut.py, a relay) has another hash and is blended again.
"""
import hashlib
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage, sparse
from scipy.sparse.csgraph import dijkstra
from scipy.sparse.linalg import spsolve

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_seam as hs  # noqa: E402
from heroine_ao_seam import split_gl  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEX = os.path.join(ROOT, "godot", "art", "people", "head_tex")
HF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "heroine_face")
GLB = os.path.join(ROOT, "godot", "art", "people", "heroine.glb")
DONE = os.path.join(HF, "jaw_blend_done.json")
FACES = ("own", "doe", "fey", "hardwon", "highborn", "moonlit", "saffron", "sunborn", "vixen", "wildling")
LOW = 4            # (the paint read at a quarter of its size, low-passed by SIGMA of those texels: about 2 mm)
SIGMA = 4.0
CORE = 0.9         # (face paint alpha from which it's her face, kept as is)
SPLIT_KEEP = 0.004 # (metres above SPLIT held unchanged, so nothing moves against her body)
EAR_Y = (1.725, 1.75)  # (the jaw's step eased out between these heights, glTF y: her temples and hairline untouched)
LEAN = float(os.environ.get("JAW_LEAN", 0.4))  # (phi ** LEAN: under 1 her neck holds her face's colour longer below the jaw)
FACE_IN = float(os.environ.get("JAW_FACE_IN", 0.004))  # (metres of her face's edge taken into the ease)
LEVEL = float(os.environ.get("JAW_LEVEL", 0.1))  # (weight of level distance against height in phi)
MOUTH = (0.035, 1.675, 0.06)  # (|x| under, y over, z over: her mouth, never her neck)
TOP_Y = 1.78       # (above this nothing changes)
ZONE_R = (0.03, 0.05)  # (metres over her skin from the jaw cut's zone (jaw_zone.png) within which the step is taken)
EAR = (0.076, 1.735, -0.018)  # (her ears' middle, as heroine_ears.py: her ears left out)
EAR_R = (0.03, 0.045)


def lin(c): return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def srgb(c): return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(np.clip(c, 0, None), 1 / 2.4) - 0.055)


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def head_mesh():
    js, binc = hs._load(GLB)
    mats = [m.get("name") for m in js["materials"]]
    prim = next(p for m in js["meshes"] for p in m["primitives"] if mats[p["material"]] == "skin_head")
    P = hs._read(js, binc, prim["attributes"]["POSITION"]).astype(np.float64)
    UV = hs._read(js, binc, prim["attributes"]["TEXCOORD_0"]).astype(np.float64)
    T = hs._read(js, binc, prim["indices"]).astype(np.int64).reshape(-1, 3)
    inside = hs._read(js, binc, prim["attributes"]["COLOR_0"])[:, 3] < 0.9  # (her mouth's inside: heroine_mouth_inner)
    return P, UV, T, inside


def tri_map(UV, T, n):
    """Per texel: its triangle (-1: none) and barycentrics (rows from the top, glTF's UV)."""
    tri = np.full((n, n), -1, np.int32)
    bar = np.zeros((n, n, 2), np.float32)
    U = UV * n
    for k, t in enumerate(U[T]):
        x0, y0 = np.maximum(np.floor(t.min(0)).astype(int), 0)
        x1, y1 = np.minimum(np.ceil(t.max(0)).astype(int), n - 1)
        if x1 < x0 or y1 < y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        xs, ys = xs.ravel(), ys.ravel()
        a, b, c = t
        v0, v1 = b - a, c - a
        den = v0[0] * v1[1] - v1[0] * v0[1]
        if abs(den) < 1e-12:
            continue
        qx, qy = xs + 0.5 - a[0], ys + 0.5 - a[1]
        vv = (qx * v1[1] - v1[0] * qy) / den
        ww = (v0[0] * qy - qx * v0[1]) / den
        m = (vv > -1e-3) & (ww > -1e-3) & (1 - vv - ww > -1e-3)
        tri[ys[m], xs[m]] = k
        bar[ys[m], xs[m], 0] = vv[m]
        bar[ys[m], xs[m], 1] = ww[m]
    return tri, bar


class Head:
    def __init__(self, n):
        P, UV, T, inside = head_mesh()
        key = np.round(P / 1e-5).astype(np.int64)
        _, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
        self.P, self.UV, self.T, self.inv = P, UV, T, inv.ravel()
        self.Pw = P[first]
        self.inside = np.zeros(len(first), bool)
        np.logical_or.at(self.inside, self.inv.ravel(), inside)
        # (and her lips' inner rims, turned up or back into her mouth: a face's lips may be laid below CORE)
        Q = self.Pw
        Tw0 = self.inv[T]
        fn = np.cross(Q[Tw0[:, 1]] - Q[Tw0[:, 0]], Q[Tw0[:, 2]] - Q[Tw0[:, 0]])
        nrm = np.zeros_like(Q)
        for k in range(3):
            np.add.at(nrm, Tw0[:, k], fn)
        nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-12)
        self.inside |= ((np.abs(Q[:, 0]) < MOUTH[0]) & (Q[:, 1] > MOUTH[1]) & (Q[:, 2] > MOUTH[2])
                        & ((nrm[:, 1] > 0.2) | (nrm[:, 2] < 0.2)))
        nv = len(first)
        Tw = self.inv[T]
        e = np.sort(np.concatenate([Tw[:, [0, 1]], Tw[:, [1, 2]], Tw[:, [2, 0]]]), 1)
        e = np.unique(e[e[:, 0] != e[:, 1]], axis=0)
        self.E = e
        ln = np.linalg.norm(self.Pw[e[:, 1]] - self.Pw[e[:, 0]], axis=1)
        self.w = 1.0 / np.maximum(ln, 1e-5)
        ne = len(e)
        self.B = sparse.csr_matrix((np.r_[-np.ones(ne), np.ones(ne)], (np.r_[np.arange(ne), np.arange(ne)],
                                    np.r_[e[:, 0], e[:, 1]])), shape=(ne, nv))
        self.nv = nv
        self.tri, self.bar = tri_map(UV, T, n)
        cov = self.tri >= 0
        _, (self.iy, self.ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
        self.n = n

    def per_point(self, img_low):
        """A low image (n/LOW square) read at each welded point (mean of its UV copies)."""
        m = img_low.shape[0]
        x = np.clip(self.UV[:, 0] * m - 0.5, 0, m - 1)
        y = np.clip(self.UV[:, 1] * m - 0.5, 0, m - 1)
        ch = [ndimage.map_coordinates(img_low[..., c], [y, x], order=1, mode="nearest") for c in range(img_low.shape[2])]
        v = np.stack(ch, 1)
        acc = np.zeros((self.nv, v.shape[1]))
        np.add.at(acc, self.inv, v)
        cnt = np.bincount(self.inv, minlength=self.nv)[:, None]
        return acc / cnt

    def to_texels(self, d):
        """A per-welded-point field laid per texel through the triangles, padded outside the islands."""
        dv = d[self.inv]
        t = np.maximum(self.tri, 0)
        Tv = self.T[t]
        b1, b2 = self.bar[..., 0:1], self.bar[..., 1:2]
        out = dv[Tv[..., 0]] * (1 - b1 - b2) + dv[Tv[..., 1]] * b1 + dv[Tv[..., 2]] * b2
        return out[self.iy, self.ix]


def low(h, img):
    """img (n square, padded outside the islands) shrunk by LOW and low-passed."""
    n = img.shape[0]
    m = n // LOW
    s = img[h.iy, h.ix].reshape(m, LOW, m, LOW, -1).mean((1, 3))
    return np.stack([ndimage.gaussian_filter(s[..., c], SIGMA, mode="nearest") for c in range(s.shape[2])], -1)


DEBUG = {}


def harmonic(h, dom, held, V):
    """V on the held points carried smoothly over dom (a membrane); free (no flow) at dom's other edges."""
    e = h.E
    use = (dom | held)[e[:, 0]] & (dom | held)[e[:, 1]] & (dom[e[:, 0]] | dom[e[:, 1]])
    B = h.B[use]
    A = (B.T @ sparse.diags(h.w[use]) @ B).tocsr()
    eps = 1e-3  # (a part of dom that reaches no held point keeps V: L, or 0 for phi)
    Aff = (A[dom][:, dom] + eps * sparse.identity(int(dom.sum()))).tocsc()
    out = V.copy()
    for c in range(V.shape[1]):
        out[dom, c] = spsolve(Aff, eps * V[dom, c] - (A[dom][:, held] @ V[held, c]))
    return out


def solve(h, L, a, zone):
    """The log-gain per point (3 channels): see the module's note."""
    P = h.Pw
    y = P[:, 1]
    s = split_gl(P)
    fixed = (a >= CORE) | (s <= SPLIT_KEEP) | (y >= TOP_Y)
    e = h.E
    # not her face, reached from the jaw cut's zone without crossing her face (so not her mouth or eyes)
    q = (a < CORE) & ~h.inside
    eq = q[e[:, 0]] & q[e[:, 1]]
    gd = sparse.coo_matrix((1 / h.w[eq], (e[eq, 0], e[eq, 1])), shape=(h.nv, h.nv)).tocsr()
    src = np.where((zone > 0.05) & q)[0]
    dist = dijkstra(gd, directed=False, indices=src, min_only=True, limit=ZONE_R[1] * 1.5)
    de = np.linalg.norm(np.c_[np.abs(P[:, 0]), P[:, 1:]] - np.array(EAR), axis=1)
    w = (1 - smooth(EAR_Y[0], EAR_Y[1], y)) * (1 - smooth(ZONE_R[0], ZONE_R[1], dist)) * smooth(*EAR_R, de)
    w = np.where(q, w, 0)
    # and her face's last few mm above her neck there, so the ease starts inside her face's edge
    gall = sparse.coo_matrix((1 / h.w, (e[:, 0], e[:, 1])), shape=(h.nv, h.nv)).tocsr()
    nb = np.where(q & (w > 0))[0]
    db, _, sb = dijkstra(gall, directed=False, indices=nb, min_only=True, limit=FACE_IN * 1.5,
                         return_predecessors=True)
    band = (~q) & (db < FACE_IN) & ~h.inside
    w = np.where(band, w[np.maximum(sb, 0)], w)
    fixed &= ~band
    # over her neck under the jaw (dom) the paint's low colour is laid anew: G, her face's edge colour carried
    # down (her face's points held, free elsewhere), H, her neck's own colour at SPLIT and at the zone's sides
    # carried up (free at her face), eased from one to the other by S(phi), phi running 1 at her face to 0 at
    # SPLIT evenly over the distance between (over her skin); so it leaves her face and arrives at SPLIT flat, with no kink at either end. w eases it in sideways.
    dom = (w > 0) & ~fixed
    face = (a >= CORE) & ~dom & ~h.inside
    low_ = ~dom & ~face & ~h.inside
    G = harmonic(h, dom, face, L)
    H = harmonic(h, dom, low_, L)
    use = (dom[e[:, 0]] | dom[e[:, 1]])
    # (phi's distances mostly in height: under her chin her skin runs level and is seen edge on from the front,
    # so it keeps her face's colour and the ease is spread down the front and sides of her neck as they're seen)
    dv = P[e[:, 1]] - P[e[:, 0]]
    cost = np.sqrt(dv[:, 1] ** 2 + LEVEL ** 2 * (dv[:, 0] ** 2 + dv[:, 2] ** 2)) + 1e-7
    gdom = sparse.coo_matrix((cost[use], (e[use, 0], e[use, 1])), shape=(h.nv, h.nv)).tocsr()
    df = dijkstra(gdom, directed=False, indices=np.where(face)[0], min_only=True)
    dl = dijkstra(gdom, directed=False, indices=np.where(low_)[0], min_only=True)
    phi = np.where(np.isfinite(df), dl / np.maximum(dl + df, 1e-9), 0)
    S = smooth(0, 1, phi ** LEAN)[:, None]
    d = np.where(dom[:, None], (H + (G - H) * S - L) * w[:, None], 0)
    DEBUG.update(w=w, phi=phi, G=G, H=H, dom=dom, face=face, low=low_, d=d)
    return d, w > 0.5


def face_alpha(face):
    sfx = "" if face == "own" else "_" + face
    return np.asarray(Image.open(os.path.join(HF, "face_paint%s.png" % sfx)).convert("RGBA"))[..., 3].astype(np.float32) / 255


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main(faces, out_dir=None):
    done = json.load(open(DONE)) if os.path.exists(DONE) else {}
    todo = []
    for face in faces or FACES:
        path = os.path.join(TEX, "heroine_head.jpg" if face == "own" else "heroine_head_%s.jpg" % face)
        if not out_dir and done.get(face) == sha1(path):
            print("JAW BLEND %-9s already done" % face)
            continue
        todo.append((face, path))
    if not todo:
        return
    h = zone = None
    for face, path in todo:
        im = np.asarray(Image.open(path).convert("RGB")).astype(np.float32) / 255
        n = im.shape[0]
        if h is None or h.n != n:
            h, zone = Head(n), None
        li = lin(im)
        L = np.log(np.maximum(h.per_point(low(h, li)), 1e-4))
        al = face_alpha(face)
        if al.shape[0] != n:
            al = np.asarray(Image.fromarray((al * 255).astype(np.uint8)).resize((n, n), Image.BILINEAR)) / 255.0
        a = h.per_point(low(h, al[..., None].astype(np.float32)))[:, 0]
        if zone is None:
            zi = np.asarray(Image.open(os.path.join(HF, "jaw_zone.png")).convert("L").resize((n, n), Image.BILINEAR))
            zone = h.per_point(low(h, zi[..., None].astype(np.float32) / 255))[:, 0]
        d, neck = solve(h, L, a, zone)
        gain = np.exp(h.to_texels(d).astype(np.float32))
        out = srgb(li * gain)
        q = os.path.join(out_dir, os.path.basename(path)) if out_dir else path
        Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(q, quality=95, subsampling=0)
        top = d[neck].max(0)
        print("JAW BLEND %-9s neck lifted by up to x%.3f %.3f %.3f (linear), %d points moved -> %s"
              % (face, *np.exp(top), int((np.abs(d).max(1) > 1e-3).sum()), q))
        if not out_dir:
            done[face] = sha1(q)
            with open(DONE, "w") as fh:
                json.dump(done, fh, indent=1)


if __name__ == "__main__":
    args = sys.argv[1:]
    od = None
    if args[:1] == ["--out"]:
        od, args = args[1], args[2:]
        os.makedirs(od, exist_ok=True)
    main(args, od)
