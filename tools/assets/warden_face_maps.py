"""The Ford-Warden's face data map (face_data.png) from his Face Forge head's own geometry, for warden_wet.gdshader's
face pass (WardenLook key "face", material warden_face / warden_face_lod).

The head (tools/assets/warden_face.py) carries a portrait projected into its texture: the photo's own front light is
baked in, so in a night shot the face read as a lit photo pasted on. This map gives the shader:
  R  de-light: the factor that takes the portrait's low-frequency shading out. The texture's luminance, low-passed over
     the surface, is fitted as a + c.n (an ambient term and one directional light along c); R = (mean / fit)^DELIGHT,
     stored /2 (0..2).
  G  wet sheen, 0..0.8: a thin line on the lower lids' rims, and the lips (Warden 7 r3: nothing else);
     0.8..1: the eyes (glassy).
  B  creases: concavity (the sockets' rims, nasolabial folds, the lids' fold, under the brow), 0..1.
  A  hair zones: scalp (the buzz cut) and beard/stubble, where the texture's dark specks are made the beard's grey.
Regions are set in a face frame from the eyes (manifest head.eyes, Head-bone local, through the Head joint's inverse
bind matrix): origin between the eyes, x across, y up, z forward, in units of the eye distance.

  python tools/assets/warden_face_maps.py [PKG] [--size 1024] [--debug DIR]
PKG defaults to godot/art/npc/ford_warden; writes PKG/face_data.png (rerun whenever warden_face.py rebuilds the head).
"""
import io, json, os, struct, sys
import numpy as np
from PIL import Image
from scipy import sparse
from scipy.ndimage import distance_transform_edt

CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}
DELIGHT = 0.85      # how much of the fitted shading is taken out
LOWPASS = 60        # smoothing iterations of the surface low-pass


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


class Glb:
    def __init__(self, path):
        b = open(path, "rb").read()
        n = struct.unpack("<I", b[12:16])[0]
        self.j = json.loads(b[20:20 + n])
        o = 20 + n
        m = struct.unpack("<I", b[o:o + 4])[0]
        self.bin = bytes(b[o + 8:o + 8 + m])

    def acc(self, i):
        a = self.j["accessors"][i]
        bv = self.j["bufferViews"][a["bufferView"]]
        dt = np.dtype(CT[a["componentType"]]); nc = NC[a["type"]]
        off = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        stride = bv.get("byteStride", 0) or dt.itemsize * nc
        raw = np.frombuffer(self.bin, dtype=np.uint8, count=stride * (a["count"] - 1) + dt.itemsize * nc, offset=off)
        out = np.lib.stride_tricks.as_strided(raw, shape=(a["count"], dt.itemsize * nc), strides=(stride, 1)).copy()
        out = out.view(dt).reshape(a["count"], nc).astype(np.float64)
        if a.get("normalized"): out /= np.iinfo(dt).max
        return out if nc > 1 else out[:, 0]

    def image(self, i):
        im = self.j["images"][i]; bv = self.j["bufferViews"][im["bufferView"]]
        o = bv.get("byteOffset", 0)
        return Image.open(io.BytesIO(self.bin[o:o + bv["byteLength"]]))


def head_prim(g, mat="warden_face"):
    mi = next(i for i, m in enumerate(g.j["materials"]) if m.get("name") == mat)
    for me in g.j["meshes"]:
        for p in me["primitives"]:
            if p.get("material") == mi:
                at = p["attributes"]
                return (g.acc(at["POSITION"]), g.acc(at["NORMAL"]), g.acc(at["TEXCOORD_0"]),
                        g.acc(p["indices"]).astype(np.int64).reshape(-1, 3), g.j["materials"][mi])
    raise SystemExit("no " + mat)


def head_bind(g):
    sk = g.j["skins"][0]
    names = [g.j["nodes"][n].get("name", "") for n in sk["joints"]]
    k = next(i for i, n in enumerate(names) if n.lower() == "head")
    ibm = g.acc(sk["inverseBindMatrices"])[k].reshape(4, 4).T   # column-major
    return np.linalg.inv(ibm)


def adjacency(F, n):
    e = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    e = np.concatenate([e, e[:, ::-1]])
    A = sparse.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)).tocsr()
    A.data[:] = 1
    return A


def smooth(A, x, it):
    deg = np.asarray(A.sum(1)).ravel()
    d = deg[:, None] if x.ndim == 2 else deg
    for _ in range(it):
        x = 0.5 * x + 0.5 * (A @ x) / d
    return x


def raster(uv, F, vals, size):
    """Per-texel barycentric interpolation of per-vertex vals (N, C) over the UV triangles; returns (img, covered)."""
    C = vals.shape[1]
    out = np.zeros((size, size, C)); cov = np.zeros((size, size), bool)
    P = np.c_[uv[:, 0] * size - 0.5, uv[:, 1] * size - 0.5]   # glTF uv: v from the image's top
    for t in F:
        a, b, c = P[t]
        x0, x1 = int(np.floor(min(a[0], b[0], c[0]))), int(np.ceil(max(a[0], b[0], c[0])))
        y0, y1 = int(np.floor(min(a[1], b[1], c[1]))), int(np.ceil(max(a[1], b[1], c[1])))
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, size - 1), min(y1, size - 1)
        if x1 < x0 or y1 < y0: continue
        d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(d) < 1e-12: continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        l0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / d
        l1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / d
        l2 = 1 - l0 - l1
        m = (l0 >= -0.02) & (l1 >= -0.02) & (l2 >= -0.02)
        if not m.any(): continue
        out[ys[m], xs[m]] = l0[m, None] * vals[t[0]] + l1[m, None] * vals[t[1]] + l2[m, None] * vals[t[2]]
        cov[ys[m], xs[m]] = True
    # pad the islands (nearest covered texel) so filtering and mips don't pull in the empty space
    idx = distance_transform_edt(~cov, return_distances=False, return_indices=True)
    return out[idx[0], idx[1]], cov


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    opt = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
    a = [x for x in a if x not in (opt("--size", None), opt("--debug", None))]
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    pkg = a[0] if a else os.path.join(root, "godot", "art", "npc", "ford_warden")
    size = int(opt("--size", 1024)); dbg = opt("--debug", None)
    g = Glb(os.path.join(pkg, "body.glb"))
    man = json.load(open(os.path.join(pkg, "manifest.json")))
    P, N, UV, F, mat = head_prim(g)
    nv = len(P)
    # (some vertices carry a zero normal: those get their faces' area-weighted one)
    fn = np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]])
    vn = np.zeros_like(P)
    for k in range(3): np.add.at(vn, F[:, k], fn)
    bad = np.linalg.norm(N, axis=1) < 0.5
    N[bad] = vn[bad]; N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    print(f"[face_maps] head: {nv} verts, {len(F)} tris")
    # the face frame from the eyes
    B = head_bind(g)
    el, er = [(B @ np.r_[man["head"]["eyes"][k], 1.0])[:3] for k in ("l", "r")]
    o = (el + er) / 2; ipd = np.linalg.norm(el - er)
    ex = (el - er) / ipd; ez = np.array([0, 0, 1.0]); ez -= ex * (ez @ ex); ez /= np.linalg.norm(ez)
    ey = np.cross(ez, ex)
    R = np.stack([ex, ey, ez], 1)
    Q = (P - o) @ R / ipd       # x across (to his left), y up, z forward; eye-distance units
    Nf = N @ R
    print(f"[face_maps] eyes at {o.round(4)}, ipd {ipd:.4f}; face frame y {Q[:, 1].min():.2f}..{Q[:, 1].max():.2f}, "
          f"z {Q[:, 2].min():.2f}..{Q[:, 2].max():.2f}")
    # (the unwrap splits vertices at its seams: smoothing runs on the welded surface, then back to the split vertices)
    _, wid = np.unique(np.round(P / 1e-5).astype(np.int64), axis=0, return_inverse=True)
    wid = wid.ravel(); nw = wid.max() + 1
    Aw = adjacency(wid[F], nw)
    cnt = np.bincount(wid, minlength=nw).astype(float)

    class _A:  # smooth(A, x) on split vertices: average twins, smooth on the weld, scatter back
        def sum(self, _):
            return np.ones((nv, 1))

        def __matmul__(self, x):
            xw = np.zeros((nw,) + x.shape[1:]); np.add.at(xw, wid, x)
            xw /= cnt.reshape((-1,) + (1,) * (x.ndim - 1))
            deg = np.asarray(Aw.sum(1)).reshape((-1,) + (1,) * (x.ndim - 1))
            return ((Aw @ xw) / np.maximum(deg, 1))[wid]
    A = _A()
    # the texture at each vertex (a box-filtered copy, so pores don't decide it)
    col = g.image(mat["pbrMetallicRoughness"]["baseColorTexture"]["index"]).convert("RGB")
    lin = (np.asarray(col.resize((512, 512), Image.BOX), np.float64) / 255.0) ** 2.2
    ui = np.clip((UV[:, 0] * 512).astype(int), 0, 511); vi = np.clip((UV[:, 1] * 512).astype(int), 0, 511)
    lum = lin[vi, ui] @ [0.2126, 0.7152, 0.0722]
    # regions (soft), in eye-distance units
    x, y, z = Q.T; ax = np.abs(x)
    front = smoothstep(-0.2, 0.4, Nf[:, 2])
    eye_d = np.minimum(np.linalg.norm(Q - [0.5, 0, 0], axis=1), np.linalg.norm(Q - [-0.5, 0, 0], axis=1))
    eyes = 1 - smoothstep(0.17, 0.21, eye_d)
    eyes *= smoothstep(-0.3, -0.1, z)    # the eyeballs' front only
    brow = smoothstep(0.12, 0.25, y) * (1 - smoothstep(0.55, 0.75, y)) * (1 - smoothstep(0.85, 1.05, ax))
    nose = (1 - smoothstep(0.18, 0.3, ax)) * smoothstep(-1.15, -1.0, y) * (1 - smoothstep(0.0, 0.2, y)) * smoothstep(0.0, 0.3, z)
    cheek = smoothstep(0.35, 0.5, ax) * (1 - smoothstep(0.95, 1.15, ax)) * smoothstep(-0.95, -0.75, y) * (1 - smoothstep(-0.3, -0.18, y))
    lids = smoothstep(0.15, 0.2, eye_d) * (1 - smoothstep(0.26, 0.34, eye_d)) * (1 - smoothstep(-0.08, 0.0, y))
    lips = (1 - smoothstep(0.38, 0.5, ax)) * smoothstep(-1.85, -1.72, y) * (1 - smoothstep(-1.45, -1.35, y))
    # curvature: + convex (ridges), - concave (creases): the vertex against its neighbours' mean, along the normal
    Ns = smooth(A, N, 2); Ns /= np.linalg.norm(Ns, axis=1, keepdims=True)
    curv = smooth(A, np.einsum("ij,ij->i", P - smooth(A, P, 4), Ns), 2)
    cs_ = np.percentile(np.abs(curv), 95)
    convex = np.clip(curv / cs_, 0, 1); concave = np.clip(-curv / cs_, 0, 1)
    # (Warden 7 r3 judge: the face read as glossy black rubber with white dots on the nose: the wet sheen only a thin
    #  line on the lower lids' rims and the lips now; the brow, nose, cheekbones and the convex rest are matte skin)
    rim = smoothstep(0.16, 0.19, eye_d) * (1 - smoothstep(0.22, 0.26, eye_d)) * (1 - smoothstep(-0.08, 0.0, y))
    wet = np.clip(np.maximum(rim, lips * 0.85), 0, 1) * front
    G = 0.8 * wet * (1 - eyes) + eyes
    crease = np.clip(concave * 1.4, 0, 1) * (1 - eyes)
    # hair zones: the scalp (above the brow, round the back, the temples) and the beard (below the nose line, the jaw, the
    # neck, and up the cheek sides to a beard line under the cheekbone: Warden 6 r3, the jaw's and cheeks' dark specks
    # read as scab or mould where the old zone, starting below the nose line, missed them)
    scalp = np.maximum.reduce([smoothstep(0.75, 1.0, y), (1 - smoothstep(-0.9, -0.5, z)) * smoothstep(-0.6, -0.2, y),
                               smoothstep(0.85, 1.0, ax) * smoothstep(-0.1, 0.25, y)])
    line = -1.0 + 0.55 * smoothstep(0.35, 1.0, ax)    # the beard line: the mouth's corner up to the sideburn
    cheeks = (1 - smoothstep(line - 0.12, line + 0.12, y)) * smoothstep(0.28, 0.42, ax)
    sides = smoothstep(0.8, 1.0, ax) * (1 - smoothstep(-0.1, 0.25, y))   # the sideburns, into the scalp's temples
    beard = np.maximum.reduce([(1 - smoothstep(-1.15, -0.95, y)), cheeks, sides]) * (1 - lips * 0.9) * (1 - nose)
    hair = np.clip(np.maximum(scalp, beard), 0, 1) * (1 - eyes)
    # de-light: low-passed luminance fitted as a + c.n over the skin (not the eyes, the hair zones, the lips)
    low = smooth(A, lum, LOWPASS)
    Nl = smooth(A, N, LOWPASS // 3); Nl /= np.linalg.norm(Nl, axis=1, keepdims=True)
    skin = (eyes < 0.01) & (hair < 0.3) & (lips < 0.1)
    coef, *_ = np.linalg.lstsq(np.c_[np.ones(skin.sum()), Nl[skin]], low[skin], rcond=None)
    fit = np.c_[np.ones(nv), Nl] @ coef
    mean = low[skin].mean()
    fac = np.clip((mean / np.maximum(fit, 0.02)) ** DELIGHT, 0.4, 1.9)
    cdir = coef[1:] / np.linalg.norm(coef[1:])
    r2 = 1 - ((low[skin] - fit[skin]) ** 2).sum() / ((low[skin] - mean) ** 2).sum()
    print(f"[face_maps] shading fit: ambient {coef[0]:.3f}, light {np.linalg.norm(coef[1:]):.3f} along {(cdir @ R).round(2)} "
          f"(face frame); skin r^2 {r2:.2f}; factor {fac.min():.2f}..{fac.max():.2f}; skin lum mean {mean:.3f}")
    vals = np.c_[fac / 2, G, crease, hair]
    img, cov = raster(UV, F, vals, size)
    Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA").save(os.path.join(pkg, "face_data.png"))
    print(f"[face_maps] wrote face_data.png {size}; covered {cov.mean():.1%}; verts wet>0.3 {np.mean(G > 0.3):.1%}, "
          f"eyes {np.mean(eyes > 0.5):.1%}, hair {np.mean(hair > 0.5):.1%}, crease>0.3 {np.mean(crease > 0.3):.1%}")
    if dbg:
        os.makedirs(dbg, exist_ok=True)
        c = np.asarray(col.resize((size, size)), np.float64) / 255
        for k, nm in enumerate("RGBA"):
            ch = img[:, :, k] / max(img[:, :, k].max(), 1e-6)
            ov = c * 0.45 + 0.55 * ch[:, :, None] * [1, 0.55, 0.15]
            Image.fromarray((np.clip(ov, 0, 1) * 255).astype(np.uint8)).save(os.path.join(dbg, f"face_{nm}.jpg"), quality=85)
        # the masks splatted on the head, front and side views (orthographic, nearest wins)
        vcol = lin[vi, ui] ** (1 / 2.2)
        views = []
        for view in ("front", "side"):
            u, v, dep = (Q[:, 0], Q[:, 1], Q[:, 2]) if view == "front" else (-Q[:, 2], Q[:, 1], Q[:, 0])
            tiles = []
            for k in range(5):
                im = np.zeros((300, 300, 3)); zb = np.full((300, 300), -1e9)
                if k == 4: ch = (lin[vi, ui] * fac[:, None]) ** (1 / 2.2)
                else:
                    m = np.clip((vals[:, 0] * 2 - 0.7) / 0.7, 0, 1) if k == 0 else vals[:, k]
                    ch = vcol * 0.5 + 0.5 * m[:, None] * np.array([1, 0.55, 0.15])
                px = np.clip(((u + 2.2) / 4.4 * 300).astype(int), 0, 299); py = np.clip(((1.9 - v) / 4.4 * 300).astype(int), 0, 299)
                for i in np.argsort(dep):
                    for dx in (0, 1):
                        for dy in (0, 1):
                            im[min(py[i] + dy, 299), min(px[i] + dx, 299)] = ch[i]
                tiles.append(im)
            views.append(np.concatenate(tiles, 1))
        Image.fromarray((np.clip(np.concatenate(views, 0), 0, 1) * 255).astype(np.uint8)).save(os.path.join(dbg, "masks_3d.jpg"), quality=88)
        dl = np.clip(c ** 2.2 * img[:, :, :1] * 2, 0, 1) ** (1 / 2.2)
        Image.fromarray((np.concatenate([c, dl], 1) * 255).astype(np.uint8)).save(os.path.join(dbg, "delight_ab.jpg"), quality=85)


if __name__ == "__main__":
    main()
