"""Give the Ford-Warden's as-generated package a Face Forge head in place of its generated hood, face and rope beard.

The Meshy body's head region read as a black alien mask with a rope trunk for a beard (judges, Warden 5). It is cut away
and replaced by a man's head built on its own by Marionette's Face Forge (faceforge.js buildHeadAlone: a reference
portrait -> Pixal3D bust, the picture projected into its texture, MediaPipe landmarks on the surface):

  1. the body (the 'generated' surface): the hood (everything above the mantle's rim RIM) and the rope beard (neutral
     grey texels in front of the chest, grown over the mesh) are dropped. The kept body's vertices, UVs and atlas are
     untouched (only its index list changes). Holes the ropes leave in the chest are filled by a smooth membrane
     (material warden_patch: a small texture of the hole's own edge colours, eased across it);
  2. the head: placed by its eyes (IPD apart, level, facing +Z) with its chin at CHIN_Y and its neck centred over the
     neck bone; cut at CUT_Y (inside the mantle); its shoulders tucked inside the mantle where they would show through;
     reduced to HEAD_TRIS, a fresh unwrap, colour and normal baked from the Pixal bust (material warden_face, TEX);
  3. the collar: the mantle's rim joined to the neck by a strip (warden_patch, the rim's colours darkened), so no gap
     shows into the hollow body;
  4. skinned: the skull and face above the jaw to Head, the neck to neck_01, the shoulders the mantle's weights;
  5. lod.glb gets the same cut (labels moved over from LOD0), a ~LOD_TRIS head and a coarse shadow head;
  6. manifest.json: head (source, tris, maps, bones) and head.eyes (the two iris centres, Head-bone local, metres).

Run (Blender 4.5, a blender turn; pyfqmr and xatlas in Blender's python, as warden_head.py):
  blender -b --python-exit-code 1 -P tools/assets/warden_face.py -- PKG_IN PKG_OUT HEAD.glb HEAD.json
        [--ipd 0.064] [--chin 1.545] [--work DIR]
HEAD.glb / HEAD.json: Marionette exportHead(cand) and { marks3D } of buildHeadAlone (Pixal frame, glTF axes).
"""
import bpy, bmesh, io, json, math, os, sys
import numpy as np
import mathutils
from mathutils.bvhtree import BVHTree
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from warden_head import Glb, b2g, g2b, imp, world_pts, kd, simplified, bake, smoothstep, add_prim, select_only  # noqa: E402

# ---- constants (package frame, glTF: Y up, metres, front +Z) ----
RIM = 1.515                      # the hood is everything above this (the mantle's top)
ROPE = dict(band=(-0.06, 0.105), y0=1.07, L_seed=0.24, L_grow=0.17, sat=0.035, z_min=0.10)
MID_X, NECK_Z = 0.0165, -0.030   # the neck's centre line (the neck_01 / Head bones: x 1.3-1.7 cm, z -3.6 cm)
CUT_Y = 1.40                     # the head is kept above this (its shoulders inside the mantle)
TUCK = 0.005
HEAD_TRIS, LOD_TRIS, SHADOW_TRIS = 18000, 2500, 600
TEX, PATCH_TEX = 4096, 512
MAT, PATCH = "warden_face", "warden_patch"
SKIN_ROUGH = 0.55
COLLAR_DARK = 0.55


def log(*a):
    print("[warden_face]", *a, flush=True)


# ================= the body: what goes =================
def glb_image(g, tex):
    im = g.j["images"][g.j["textures"][tex]["source"]]
    bv = g.j["bufferViews"][im["bufferView"]]
    o = bv.get("byteOffset", 0)
    return np.asarray(Image.open(io.BytesIO(bytes(g.bin[o:o + bv["byteLength"]]))).convert("RGB"), np.float32) / 255


def tri_colours(img, uv, F):
    s = img.shape[0]

    def col(u):
        return img[np.clip((u[:, 1] * s).astype(int), 0, s - 1), np.clip((u[:, 0] * s).astype(int), 0, s - 1)]
    return (col(uv[F[:, 0]]) + col(uv[F[:, 1]]) + col(uv[F[:, 2]]) + col(uv[F].mean(1))) / 4


def welded(P):
    _, wid = np.unique(np.round(P * 1e5).astype(np.int64), axis=0, return_inverse=True)
    wid = wid.ravel()
    Pw = np.zeros((wid.max() + 1, 3))
    Pw[wid] = P
    return wid, Pw


def grow(seed, ok, W):
    out = seed.copy()
    vt = {}
    for t in np.nonzero(ok)[0]:
        for v in W[t]:
            vt.setdefault(v, []).append(t)
    front = list(np.nonzero(seed)[0])
    while front:
        nxt = []
        for t in front:
            for v in W[t]:
                for u in vt.get(v, ()):
                    if not out[u]:
                        out[u] = True
                        nxt.append(u)
        front = nxt
    return out


def classify(P, F, col, W):
    """drop: the hood (above RIM) and the rope beard (neutral grey texels in front of the chest, grown, closed)."""
    C = P[F].mean(1)
    x, y, z = C.T
    hood = y > RIM
    L = col.mean(1)
    sat = col.max(1) - col.min(1)
    c = ROPE
    band = (x > c["band"][0]) & (x < c["band"][1]) & (y > c["y0"]) & ~hood & (z > c["z_min"])
    rope = grow(band & (sat < c["sat"]) & (L > c["L_seed"]), band & (sat < c["sat"] + 0.01) & (L > c["L_grow"]), W)
    touch = np.zeros(W.max() + 1, bool)
    for _ in range(2):
        touch[W[rope].ravel()] = True
        rope |= band & touch[W].all(1)
    log(f"dropped: hood {int(hood.sum())} tris, rope beard {int(rope.sum())} tris")
    return hood, rope


def boundary_loops(W, keep):
    E = np.concatenate([W[keep][:, [0, 1]], W[keep][:, [1, 2]], W[keep][:, [2, 0]]])
    k = np.sort(E, 1)
    _, inv, cnt = np.unique(k, axis=0, return_inverse=True, return_counts=True)
    b = E[cnt[inv.ravel()] == 1]
    nxt = {}
    for a, c in b:
        nxt.setdefault(a, []).append(c)
    seen, out = set(), []
    for a in list(nxt):
        if a in seen:
            continue
        lp, cur = [a], a
        seen.add(a)
        while True:
            n = [v for v in nxt.get(cur, []) if v not in seen]
            if not n:
                break
            cur = n[0]
            lp.append(cur)
            seen.add(cur)
        out.append(np.array(lp))
    return out


# ================= patches (holes and the collar) =================
class Patches:
    """New surface pieces in one primitive with one small texture: positions, colours (eased from their edges), weights."""

    def __init__(self, nb):
        self.pos, self.col, self.W, self.tri, self.cell = [], [], [], [], []
        self.nb = nb

    def add(self, pos, col, W, tri):
        o = sum(len(p) for p in self.pos)
        self.pos.append(pos)
        self.col.append(col)
        self.W.append(W)
        self.tri.append(tri + o)
        self.cell.append(len(self.pos) - 1)

    def arrays(self):
        """UVs: each piece projected on its own best plane into its own cell of a PATCH_TEX map, colours rastered there."""
        n = len(self.pos)
        g = max(1, math.ceil(math.sqrt(n)))
        cs = 1.0 / g
        uvs, img = [], np.zeros((PATCH_TEX, PATCH_TEX, 3), np.float32)
        have = np.zeros((PATCH_TEX, PATCH_TEX), bool)
        for k, (p, c) in enumerate(zip(self.pos, self.col)):
            m = p.mean(0)
            _, _, vt = np.linalg.svd(p - m)
            q = (p - m) @ vt[:2].T
            q = (q - q.min(0)) / max(np.ptp(q, 0).max(), 1e-6)
            cx, cy = (k % g) * cs, (k // g) * cs
            uvs.append(np.c_[cx + cs * (0.06 + 0.88 * q[:, 0]), cy + cs * (0.06 + 0.88 * q[:, 1])])
        uv = np.vstack(uvs)
        col = np.vstack(self.col)
        tri = np.vstack(self.tri)
        px = uv * PATCH_TEX - 0.5
        for t in tri:
            a, b, c = px[t[0]], px[t[1]], px[t[2]]
            x0, y0 = np.floor(np.minimum(np.minimum(a, b), c)).astype(int)
            x1, y1 = np.ceil(np.maximum(np.maximum(a, b), c)).astype(int)
            x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, PATCH_TEX - 1), min(y1, PATCH_TEX - 1)
            X, Y = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
            den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
            if abs(den) < 1e-12:
                continue
            w0 = ((b[1] - c[1]) * (X - c[0]) + (c[0] - b[0]) * (Y - c[1])) / den
            w1 = ((c[1] - a[1]) * (X - c[0]) + (a[0] - c[0]) * (Y - c[1])) / den
            w2 = 1 - w0 - w1
            m = (w0 >= -0.05) & (w1 >= -0.05) & (w2 >= -0.05)
            img[Y[m], X[m]] = w0[m, None] * col[t[0]] + w1[m, None] * col[t[1]] + w2[m, None] * col[t[2]]
            have[Y[m], X[m]] = True
        from scipy import ndimage
        _, (iy, ix) = ndimage.distance_transform_edt(~have, return_indices=True)
        img = img[iy, ix]
        pos = np.vstack(self.pos).astype(np.float32)
        Wd = np.vstack(self.W)
        J = np.argsort(-Wd, 1)[:, :4]
        Wt = np.take_along_axis(Wd, J, 1)
        Wt /= np.maximum(Wt.sum(1, keepdims=True), 1e-9)
        nrm = vertex_normals(pos, tri)
        return dict(pos=pos, nrm=nrm, uv=uv.astype(np.float32), idx=tri.astype(np.uint32).ravel()), J.astype(np.uint16), \
            Wt.astype(np.float32), Image.fromarray((np.clip(img, 0, 1) ** (1 / 2.2) * 255 + 0.5).astype(np.uint8))


def vertex_normals(pos, tri):
    fn = np.cross(pos[tri[:, 1]] - pos[tri[:, 0]], pos[tri[:, 2]] - pos[tri[:, 0]])
    n = np.zeros_like(pos)
    for k in range(3):
        np.add.at(n, tri[:, k], fn)
    return (n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)).astype(np.float32)


def membrane(loop_pos, loop_col, loop_W, outward, h=0.010, iters=80):
    """A smooth surface over a closed boundary loop: Blender's triangle fill, interior edges split to ~h, the inside
    relaxed (positions, colours, weights eased from the edge). Faces turned to face `outward` (a function of a point)."""
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in loop_pos.tolist()]
    for i in range(len(vs)):
        bm.edges.new((vs[i], vs[(i + 1) % len(vs)]))
    bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=bm.edges[:])
    nb = len(vs)
    for _ in range(6):
        bm.verts.index_update()
        long_ = [e for e in bm.edges if not e.is_boundary and e.calc_length() > h]
        if not long_:
            break
        bmesh.ops.subdivide_edges(bm, edges=long_, cuts=1, use_grid_fill=False)
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        bmesh.ops.beautify_fill(bm, faces=bm.faces[:], edges=[e for e in bm.edges if not e.is_boundary])
    bm.verts.index_update()
    n = len(bm.verts)
    pos = np.array([v.co[:] for v in bm.verts])
    nbrs = [[e.other_vert(v).index for e in v.link_edges] for v in bm.verts]
    tri = np.array([[v.index for v in f.verts] for f in bm.faces if len(f.verts) == 3])
    # the loop's own vertices keep their first indices (bmesh keeps creation order)
    fixed = np.zeros(n, bool)
    fixed[:nb] = True
    col = np.zeros((n, loop_col.shape[1]))
    col[:nb] = loop_col
    W = np.zeros((n, loop_W.shape[1]))
    W[:nb] = loop_W
    free = np.nonzero(~fixed)[0]
    for it in range(iters if len(free) else 0):
        for arr in (pos, col, W):
            new = np.array([arr[nbrs[i]].mean(0) for i in free])
            arr[free] = new
    bm.free()
    # orientation
    fc = pos[tri].mean(1)
    fn = np.cross(pos[tri[:, 1]] - pos[tri[:, 0]], pos[tri[:, 2]] - pos[tri[:, 0]])
    if (np.einsum("ij,ij->i", fn, np.array([outward(c) for c in fc])) < 0).mean() > 0.5:
        tri = tri[:, ::-1]
    return pos, col, W, tri


# ================= the head =================
def rot_to(a, b):
    a, b = a / np.linalg.norm(a), b / np.linalg.norm(b)
    v = np.cross(a, b)
    c = float(a @ b)
    if np.linalg.norm(v) < 1e-9:
        return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K / (1 + c)


def set_points(o, pts_g):
    o.data.vertices.foreach_set("co", g2b(pts_g).astype(np.float64).ravel())
    o.data.update()


def placement(H, marks, ipd, chin_y):
    """Pixal frame -> package: scale by the eyes, level them, chin at chin_y, the neck centred on the neck bone."""
    m = {k: np.array(v) for k, v in marks.items()}
    eR = m.get("irisR", (m["eyeOutR"] + m["eyeInR"]) / 2)
    eL = m.get("irisL", (m["eyeOutL"] + m["eyeInL"]) / 2)
    s = ipd / np.linalg.norm(eL - eR)
    d = eL - eR
    R = rot_to(np.array([d[0], d[1], 0.0]), np.array([1.0, 0, 0]))  # level the eyes (roll), keep the Pixal facing
    Q = (s * (H @ R.T))
    chin = s * (R @ m["chin"])
    ty = chin_y - chin[1]
    # neck: the bust's section 4 cm under the chin, centred on (MID_X, NECK_Z)
    yl = chin[1] - 0.04
    sl = Q[np.abs(Q[:, 1] - yl) < 0.004]
    sl = sl[np.abs(sl[:, 0] - np.median(sl[:, 0])) < 0.09]
    cx, cz = (sl[:, 0].min() + sl[:, 0].max()) / 2, (sl[:, 2].min() + sl[:, 2].max()) / 2
    t = np.array([MID_X - cx, ty, NECK_Z - cz])
    log(f"placed: scale {s:.4f}, roll {math.degrees(math.atan2(d[1], d[0])):.2f} deg, neck {np.ptp(sl[:, 0])*100:.1f} x {np.ptp(sl[:, 2])*100:.1f} cm")

    def f(p):
        return s * (np.asarray(p) @ R.T) + t
    return f


def head_weights(pos, marks_p, body_pos, body_W, names):
    """Head above the jaw (a plane through the chin and the two jaw angles, eased 3 cm under it), the mantle's weights
    at the shoulders (below 1.47, eased to 1.53), neck_01 between."""
    nb = len(names)
    hi, nk = names.index("Head"), names.index("neck_01")
    c, jr, jl = marks_p["chin"], marks_p["jawR"], marks_p["jawL"]
    n = np.cross(jl - c, jr - c)
    n /= np.linalg.norm(n)
    if n[1] < 0:
        n = -n
    above = (pos - (c - np.array([0, 0.012, 0]))) @ n
    f_head = smoothstep(-0.03, 0.0, above)
    f_body = 1 - smoothstep(1.47, 1.53, pos[:, 1])
    f_body = np.minimum(f_body, 1 - f_head)
    t = kd(body_pos)
    dense = np.zeros((len(pos), nb), np.float32)
    for i, q in enumerate(pos):
        if f_body[i] <= 0:
            continue
        hits = t.find_n(q, 4)
        ws = np.array([1 / max(h[2], 1e-4) for h in hits])
        ws /= ws.sum()
        for (_, k, _), w in zip(hits, ws):
            dense[i] += body_W[k] * w
    dense *= f_body[:, None]
    dense[:, hi] += f_head
    dense[:, nk] += np.clip(1 - f_body - f_head, 0, 1)
    J = np.argsort(-dense, 1)[:, :4]
    Wt = np.take_along_axis(dense, J, 1)
    Wt /= Wt.sum(1, keepdims=True)
    return J.astype(np.uint16), Wt.astype(np.float32)


def dense_weights(g, p, nb):
    J = g.acc(p["attributes"]["JOINTS_0"]).astype(int)
    W = g.acc(p["attributes"]["WEIGHTS_0"]).astype(np.float32)
    D = np.zeros((len(J), nb), np.float32)
    for k in range(4):
        np.add.at(D, (np.arange(len(J)), J[:, k]), W[:, k])
    return D


def head_arrays(o):
    """o (Blender mesh, package frame) -> per-loop-split glTF arrays: pos, nrm, uv, idx."""
    me = o.data
    me.calc_loop_triangles()
    uvl = me.uv_layers.active.data
    key, out_pos, out_nrm, out_uv, idx = {}, [], [], [], []
    M = o.matrix_world
    for lt in me.loop_triangles:
        for li, vi in zip(lt.loops, lt.vertices):
            uv = tuple(round(c, 6) for c in uvl[li].uv)
            k = (vi, uv)
            if k not in key:
                key[k] = len(out_pos)
                out_pos.append(M @ me.vertices[vi].co)
                out_nrm.append((M.to_3x3() @ me.vertices[vi].normal).normalized())
                out_uv.append((uv[0], 1 - uv[1]))
            idx.append(key[k])
    pos = b2g(np.array(out_pos))
    nrm = b2g(np.array(out_nrm))
    return dict(pos=pos.astype(np.float32), nrm=nrm.astype(np.float32), uv=np.array(out_uv, np.float32), idx=np.array(idx, np.uint32))


def rim_radius(neck_pos, nbin=48):
    """The mantle's opening: its radius about the neck's axis by angle (binned, gaps filled round the circle)."""
    a = np.arctan2(neck_pos[:, 0] - MID_X, neck_pos[:, 2] - NECK_Z)
    r = np.hypot(neck_pos[:, 0] - MID_X, neck_pos[:, 2] - NECK_Z)
    b = ((a + np.pi) / (2 * np.pi) * nbin).astype(int) % nbin
    R = np.full(nbin, np.nan)
    for k in range(nbin):
        if (b == k).any():
            R[k] = r[b == k].min()
    ok = ~np.isnan(R)
    idx = np.arange(nbin)
    R = np.interp(idx, np.r_[idx[ok] - nbin, idx[ok], idx[ok] + nbin], np.r_[R[ok], R[ok], R[ok]])

    def at(p):
        aa = np.arctan2(p[..., 0] - MID_X, p[..., 2] - NECK_Z)
        return R[((aa + np.pi) / (2 * np.pi) * nbin).astype(int) % nbin]
    return at


def tuck_inside(pos, kept_P, kept_F, below, rim_at):
    """Head vertices under `below` and outside the mantle's opening (under the mantle) that show outside the kept body:
    moved TUCK inside it (nearest surface). The neck inside the opening is left alone."""
    bvh = BVHTree.FromPolygons([tuple(v) for v in kept_P.tolist()], [tuple(t) for t in kept_F.tolist()])
    out = pos.copy()
    moved = 0
    worst = 0.0
    r = np.hypot(pos[:, 0] - MID_X, pos[:, 2] - NECK_Z)
    for i in np.nonzero((pos[:, 1] < below) & (r > rim_at(pos) - 0.01))[0]:
        q = mathutils.Vector(pos[i].tolist())
        hit = bvh.find_nearest(q, 0.08)
        if hit[0] is None:
            continue
        p, n = hit[0], hit[1]
        d = (q - p).dot(n)
        if d > -TUCK:
            worst = max(worst, d)
            out[i] = np.array(p - n * TUCK)
            moved += 1
    return out, moved, worst


def add_material(g, name, color, normal=None, rough=SKIN_ROUGH, size=None):
    def enc(im, fmt, q=92):
        b = io.BytesIO()
        im.save(b, fmt, quality=q) if fmt == "JPEG" else im.save(b, fmt, optimize=True)
        return b.getvalue()
    if size and color.size[0] != size:
        color = color.resize((size, size), Image.LANCZOS)
    tc = g.add_image(enc(color, "JPEG", 92), "image/jpeg", name + "_color")
    mr = Image.new("RGB", (64, 64), (0, int(rough * 255), 0))
    tmr = g.add_image(enc(mr, "PNG"), "image/png", name + "_mr")
    mat = {"name": name, "pbrMetallicRoughness": {"baseColorTexture": {"index": tc}, "metallicRoughnessTexture": {"index": tmr},
                                                  "metallicFactor": 1.0, "roughnessFactor": 1.0}}
    if normal is not None:
        if size and normal.size[0] != size:
            normal = normal.resize((size, size), Image.LANCZOS)
        mat["normalTexture"] = {"index": g.add_image(enc(normal, "JPEG", 95), "image/jpeg", name + "_normal")}
    g.j["materials"].append(mat)
    return len(g.j["materials"]) - 1


def arr_img(a):
    return Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8))


# ================= one glb (body or lod) =================
def cut_and_patch(g, prim, drop, nb, names, col_img=None, collar=None, dark=COLLAR_DARK):
    """Drop the triangles, fill the holes left in the chest (not the neck), optionally the collar strip.
    Returns (Patches, keep, the neck loop (welded ids), welded positions, their colours, their dense weights)."""
    P = g.acc(prim["attributes"]["POSITION"]).astype(float)
    F = g.acc(prim["indices"]).reshape(-1, 3).astype(np.int64)
    uv = g.acc(prim["attributes"]["TEXCOORD_0"]) if "TEXCOORD_0" in prim["attributes"] else None
    D = dense_weights(g, prim, nb)
    wid, Pw = welded(P)
    W = wid[F]
    keep = ~drop
    prim["indices"] = g.add_acc(F[keep].astype(np.uint32).ravel(), "SCALAR", target=34963)
    # per welded vertex: a colour and dense weights (from any of its split copies)
    rep = np.zeros(len(Pw), np.int64)
    rep[wid] = np.arange(len(P))
    if col_img is not None and uv is not None:
        s = col_img.shape[0]
        vc = col_img[np.clip((uv[rep, 1] * s).astype(int), 0, s - 1), np.clip((uv[rep, 0] * s).astype(int), 0, s - 1)]
    else:
        vc = np.full((len(Pw), 3), 0.15)
    vW = D[rep]
    loops = boundary_loops(W, keep)
    neck = max(loops, key=lambda lp: (Pw[lp][:, 1].max() > RIM - 0.03) * len(lp))
    pat = Patches(nb)
    filled = []
    for lp in loops:
        if lp is neck or len(lp) < 3:
            continue

        def outward(c):
            v = np.array([c[0] - MID_X, 0, c[2] - NECK_Z])
            return v / max(np.linalg.norm(v), 1e-9)
        pos, col, Wl, tri = membrane(Pw[lp], vc[lp] ** 2.2, vW[lp], outward)
        pat.add(pos, col, Wl, tri)
        filled.append(len(lp))
    log(f"holes filled: {len(filled)} (edge verts {sorted(filled)[::-1][:6]}...), neck loop {len(neck)} verts")
    return pat, keep, neck, Pw, vc, vW


def collar_strip(pat, neck_pos, neck_col, neck_W, head_bvh, head_W_at, dark=COLLAR_DARK):
    """Join the mantle's rim to the neck: each rim point to where a level ray toward the neck's axis meets the head."""
    inner, ok = [], []
    for p in neck_pos:
        d = np.array([MID_X - p[0], 0, NECK_Z - p[2]])
        L = np.linalg.norm(d)
        hit = head_bvh.ray_cast(mathutils.Vector(p.tolist()), mathutils.Vector((d / max(L, 1e-9)).tolist()), L + 0.02)
        if hit[0] is None:
            inner.append(p)
            ok.append(False)
        else:
            inner.append(np.array(hit[0][:]) - (d / max(L, 1e-9)) * -0.0005)
            ok.append(True)
    inner = np.array(inner)
    gap = np.linalg.norm(inner - neck_pos, axis=1)
    n = len(neck_pos)
    pos = np.vstack([neck_pos, inner])
    col = np.vstack([neck_col, neck_col * dark])
    Wd = np.vstack([neck_W, np.array([head_W_at(q) for q in inner])])
    tri = []
    for i in range(n):
        j = (i + 1) % n
        tri += [[i, j, n + j], [i, n + j, n + i]]
    tri = np.array(tri)
    fc = pos[tri].mean(1)
    fn = np.cross(pos[tri[:, 1]] - pos[tri[:, 0]], pos[tri[:, 2]] - pos[tri[:, 0]])
    if (fn[:, 1] < 0).mean() > 0.5:  # the strip faces up (seen from above, into the collar)
        tri = tri[:, ::-1]
    pat.add(pos, col, Wd, tri)
    return gap, np.array(ok)


# ================= main =================
def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    pos_args = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or not argv[i - 1].startswith("--"))]
    opt = {argv[i][2:]: argv[i + 1] for i in range(len(argv) - 1) if argv[i].startswith("--")}
    pkg_in, pkg_out, head_glb, head_json = pos_args[:4]
    ipd, chin_y = float(opt.get("ipd", 0.064)), float(opt.get("chin", 1.545))
    work = opt.get("work", os.path.join(pkg_out, "..", "_check_face"))
    os.makedirs(pkg_out, exist_ok=True)
    os.makedirs(work, exist_ok=True)
    marks = json.load(open(head_json))["marks3D"]

    # ---- body: what goes ----
    g = Glb(os.path.join(pkg_in, "body.glb"))
    skin = g.j["skins"][0]
    names = [g.j["nodes"][n]["name"] for n in skin["joints"]]
    nb = len(names)
    bm_ = g.j["meshes"][0]
    gp = next(p for p in bm_["primitives"] if g.j["materials"][p["material"]]["name"] == "generated")
    P = g.acc(gp["attributes"]["POSITION"]).astype(float)
    F = g.acc(gp["indices"]).reshape(-1, 3).astype(np.int64)
    uv = g.acc(gp["attributes"]["TEXCOORD_0"])
    atlas = glb_image(g, g.j["materials"][gp["material"]]["pbrMetallicRoughness"]["baseColorTexture"]["index"])
    wid, _ = welded(P)
    hood, rope = classify(P, F, tri_colours(atlas, uv, F), wid[F])
    drop = hood | rope
    pat, keep, neck, Pw, vc, vW = cut_and_patch(g, gp, drop, nb, names, col_img=atlas)
    kept_P, kept_F = P, F[keep]

    # ---- the head ----
    hi_objs = imp(head_glb)
    select_only(*hi_objs)
    if len(hi_objs) > 1:
        bpy.ops.object.join()
    hi = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    H = b2g(world_pts(hi))
    place = placement(H, marks, ipd, chin_y)
    set_points(hi, place(H))
    mk = {k: place(np.array(v)[None])[0] for k, v in marks.items()}
    # cut at CUT_Y
    bpy.ops.object.mode_set(mode="EDIT")
    bmh = bmesh.from_edit_mesh(hi.data)
    gone = [v for v in bmh.verts if v.co.z < CUT_Y]
    bmesh.ops.delete(bmh, geom=gone, context="VERTS")
    # (the GLB comes split at every UV seam: welded, or the decimator keeps every seam as a border and xatlas
    #  gets the whole 400k bust: a 30-minute hang)
    bmesh.ops.remove_doubles(bmh, verts=bmh.verts[:], dist=1e-6)
    bmesh.update_edit_mesh(hi.data)
    bpy.ops.object.mode_set(mode="OBJECT")
    for p_ in hi.data.polygons:
        p_.use_smooth = True
    lo = simplified(hi, HEAD_TRIS, MAT, TEX)
    baked = bake(hi, lo, TEX, MAT)
    colour, normal = arr_img(baked["DIFFUSE"]), arr_img(baked["NORMAL"])
    colour.save(os.path.join(work, "face_color.png"))
    ga = head_arrays(lo)
    # shoulders inside the mantle
    rim_at = rim_radius(Pw[neck])
    ga["pos"], moved, worst = tuck_inside(ga["pos"].astype(float), kept_P, kept_F, RIM - 0.004, rim_at)
    ga["pos"] = ga["pos"].astype(np.float32)
    log(f"head: {len(ga['idx'])//3} tris; shoulders tucked inside the mantle: {moved} verts (most outside before: {worst*1000:.1f} mm)")
    bodyD = dense_weights(g, gp, nb)
    sel = (P[:, 1] > 1.30) & (P[:, 1] < RIM) & np.isin(np.arange(len(P)), np.unique(kept_F))
    J, Wt = head_weights(ga["pos"].astype(float), mk, P[sel], bodyD[sel], names)

    # ---- the collar strip ----
    hbvh = BVHTree.FromPolygons([tuple(v) for v in ga["pos"].astype(float).tolist()], [tuple(t) for t in ga["idx"].reshape(-1, 3).tolist()])
    hk = kd(ga["pos"].astype(float))

    def head_W_at(q):
        i = hk.find(q)[1]
        d = np.zeros(nb, np.float32)
        d[J[i]] = Wt[i]
        return d
    gap, ok = collar_strip(pat, Pw[neck], vc[neck] ** 2.2, vW[neck], hbvh, head_W_at)
    log(f"collar: rim {len(neck)} verts, rim->neck gap mm p50 {np.median(gap)*1000:.1f} p95 {np.percentile(gap, 95)*1000:.1f} max {gap.max()*1000:.1f}; rays that missed the neck {int((~ok).sum())}")

    # ---- write body.glb ----
    hm = add_material(g, MAT, colour, normal)
    add_prim(g, bm_, ga, J, Wt, hm, ["NORMAL", "TEXCOORD_0"])
    parr, pJ, pW, pimg = pat.arrays()
    pimg.save(os.path.join(work, "patch_color.png"))
    pm = add_material(g, PATCH, pimg, None, rough=0.8)
    add_prim(g, bm_, parr, pJ, pW, pm, ["NORMAL", "TEXCOORD_0"])
    gm = g.global_mats()
    Ghead = gm[g.node_index("Head")]
    g.save(os.path.join(pkg_out, "body.glb"))
    log(f"body.glb: kept {int(keep.sum())} of {len(F)} generated tris; head {len(ga['idx'])//3}; patches {len(parr['idx'])//3}")

    # ---- lod.glb ----
    gL = Glb(os.path.join(pkg_in, "lod.glb"))
    namesL = [gL.j["nodes"][n]["name"] for n in gL.j["skins"][0]["joints"]]
    remapL = np.array([namesL.index(n) for n in names], np.uint16)
    lmesh = gL.j["meshes"][next(gL.j["nodes"][i]["mesh"] for i, n in enumerate(gL.j["nodes"]) if n.get("name") == "lod")]
    smesh = gL.j["meshes"][next(gL.j["nodes"][i]["mesh"] for i, n in enumerate(gL.j["nodes"]) if n.get("name") == "lod_shadow")]
    lp = lmesh["primitives"][0]
    LP = gL.acc(lp["attributes"]["POSITION"]).astype(float)
    LF = gL.acc(lp["indices"]).reshape(-1, 3).astype(np.int64)
    tk = kd(P[F].mean(1))
    ldrop = np.array([drop[tk.find(c)[1]] for c in LP[LF].mean(1)]) | (LP[LF].mean(1)[:, 1] > RIM)
    lpat, *_ = cut_and_patch(gL, lp, ldrop, len(namesL), namesL)
    mid = simplified(lo, LOD_TRIS, MAT + "_lod", 1024)
    lb = bake(hi, mid, 1024, MAT + "_lod")
    gl = head_arrays(mid)
    gl["pos"], _, _ = tuck_inside(gl["pos"].astype(float), kept_P, kept_F, RIM - 0.004, rim_at)
    gl["pos"] = gl["pos"].astype(np.float32)
    JL, WL = head_weights(gl["pos"].astype(float), mk, P[sel], bodyD[sel], names)
    add_prim(gL, lmesh, gl, remapL[JL], WL, add_material(gL, MAT + "_lod", arr_img(lb["DIFFUSE"]), arr_img(lb["NORMAL"])), ["NORMAL", "TEXCOORD_0"])
    if lpat.pos:
        la, lJ, lW, limg = lpat.arrays()
        add_prim(gL, lmesh, la, remapL[lJ], lW, add_material(gL, PATCH + "_lod", limg, None, rough=0.8), ["NORMAL", "TEXCOORD_0"])
    sp = smesh["primitives"][0]
    SP = gL.acc(sp["attributes"]["POSITION"]).astype(float)
    SF = gL.acc(sp["indices"]).reshape(-1, 3)
    sk = SP[SF].mean(1)[:, 1] < RIM
    sp["indices"] = gL.add_acc(SF[sk].astype(np.uint32).ravel(), "SCALAR", target=34963)
    sh = simplified(lo, SHADOW_TRIS, "shadow_head", 256)
    gs = head_arrays(sh)
    JS, WS = head_weights(gs["pos"].astype(float), mk, P[sel], bodyD[sel], names)
    add_prim(gL, smesh, gs, remapL[JS], WS, sp["material"], ["NORMAL"])
    gL.save(os.path.join(pkg_out, "lod.glb"))
    log(f"lod.glb: kept {int((~ldrop).sum())} of {len(LF)}; head {len(gl['idx'])//3}, shadow head {len(gs['idx'])//3}")

    # ---- eyes and manifest ----
    eyes = {}
    for side, k in (("l", "irisL"), ("r", "irisR")):
        if k not in mk:
            continue
        p = mk[k] + np.array([0, 0, 0.004])
        eyes[side] = [round(float(v), 4) for v in (np.linalg.inv(Ghead) @ np.r_[p, 1])[:3]]
    m = json.load(open(os.path.join(pkg_in, "manifest.json")))
    m["head"] = {
        "source": os.path.basename(head_glb) + " (Marionette Face Forge buildHeadAlone: Pixal3D bust from a Krea portrait), grafted by tools/assets/warden_face.py",
        "material": MAT, "patchMaterial": PATCH, "tris": len(ga["idx"]) // 3, "lodTris": len(gl["idx"]) // 3, "shadowTris": len(gs["idx"]) // 3,
        "maps": TEX, "bones": sorted({names[j] for j in np.unique(J[Wt > 0.01])}),
        "dropped": {"hood": int(hood.sum()), "ropeBeard": int(rope.sum())}, "ipd": ipd, "chinY": chin_y,
        "eyes": eyes, "eyesFrame": "Head bone local, metres (glTF/Godot): the iris centres, 4 mm proud",
        "collarGapMm": {"p50": round(float(np.median(gap)) * 1000, 1), "max": round(float(gap.max()) * 1000, 1)},
    }
    t = m.get("tris")
    if isinstance(t, dict):
        t.setdefault("surfaces", {})
        t["surfaces"]["generated"] = int(keep.sum())
        t["surfaces"][MAT] = len(ga["idx"]) // 3
        t["surfaces"][PATCH] = len(parr["idx"]) // 3
        t["total"] = t["drawn"] = sum(t["surfaces"].values())
        t["note"] = "generated after the head cut, plus the Face Forge head and the patches"
    json.dump(m, open(os.path.join(pkg_out, "manifest.json"), "w"), indent=1)
    log("eyes (Head local):", eyes, "Head bone at", np.round(Ghead[:3, 3], 4).tolist())
    log("marks (package):", {k: np.round(v, 4).tolist() for k, v in mk.items() if k in ("chin", "noseTip", "irisL", "irisR", "top")})
    log("done:", pkg_out)


if __name__ == "__main__":
    main()
