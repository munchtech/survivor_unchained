"""The Ford-Warden's hood and ragged wool capelet: one package piece (armor/hood.glb), draped by a cloth simulation.

Concept A, the Drowned Watchman: a deep heavy wool hood with a short torn soaked capelet over the shoulders, all
dark charcoal-navy. The face judge's spec (Warden 6): the front edge a finger above the brows at the centre, dropping
over the brow ends and the temples; the sides ~2 cm outside the outer eye corners (ears, side stubble and the
projection line hidden); the brim well forward of the brow so moonlight leaves the forehead and upper sockets dark;
the capelet over the collar filler. About a third of the face shows (lower brow, eyes, nose, cheekbone fronts).

  1. the shape: rings (PROFILE) round the head and shoulders, closed, voxel-remeshed to an even cloth grid; the face
     opening (OPENING, a front-view outline) and the hem cut out; pushed clear of the body;
  2. cloth grain UVs from the rest shape (u = arc length round each ring, v = arc length down the meridian), two
     islands (left, right: seams at the back and front centre lines, the hood's own centre seam);
  3. a cloth simulation (Blender cloth, self collision) drapes it on the body and the head under gravity: the brim
     band pinned (the opening stays where the spec puts it), the hood held softly, the capelet free;
  4. the hem torn (a ragged line with V tears), reduced to the budget, the fine sim's folds baked into a normal map
     with a 2/2 twill on top; wool colour and roughness, darker and wetter toward the hem;
  5. thickness (an inner shell, dark, and a rim), an alpha-tested frayed fringe on the face edge and the hem;
  6. skinned: the hood to Head, the neck band eased to neck_01, the capelet the body's own weights there (spine_03,
     clavicles, the shoulder share bones), smoothed;
  7. lod1 (~2.4k) and a shadow mesh (~600); armor/hood.glb on body.glb's skeleton (meshes hood.wool, hood.lod1.wool,
     hood.shadow); renders and the spec numbers in --work.

Run (Blender 4.5, a blender turn; pyfqmr in Blender's python):
  blender -b --python-exit-code 1 -P tools/assets/warden_hood.py -- PKG_DIR [--work DIR] [--stage shell|all]
"""
import bpy, bmesh, json, math, os, sys, time
import numpy as np
import mathutils
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from warden_head import Glb, b2g, g2b, select_only, smoothstep  # noqa: E402

# ---- the shape (package frame, glTF: Y up, metres, front +Z) ----
X0 = 0.0204                     # the head's centre line (between the irises)
EYE_Y, EYE_Z = 1.659, 0.106     # the iris centres (manifest head.eyes in Head space, to the package frame)
BROW_Y, BROW_Z = 1.685, 0.124   # the brow ridge at the centre
# y, half width a, centre z, front depth, back depth (rings round the head, then the shoulders)
PROFILE = [
    (1.858, 0.000, -0.050, 0.000, 0.000),
    (1.850, 0.030, -0.045, 0.030, 0.030),
    (1.835, 0.058, -0.035, 0.070, 0.062),
    (1.810, 0.088, -0.020, 0.118, 0.098),
    (1.780, 0.110, -0.008, 0.155, 0.122),
    (1.745, 0.125, -0.003, 0.178, 0.136),
    (1.705, 0.132, 0.000, 0.186, 0.142),
    (1.660, 0.136, 0.000, 0.180, 0.144),
    (1.620, 0.137, 0.000, 0.168, 0.142),
    (1.580, 0.136, -0.004, 0.156, 0.138),
    (1.545, 0.145, -0.010, 0.150, 0.138),
    (1.515, 0.200, -0.015, 0.158, 0.160),
    (1.490, 0.285, -0.020, 0.178, 0.195),
    (1.460, 0.345, -0.025, 0.195, 0.222),
    (1.410, 0.372, -0.030, 0.212, 0.243),
    (1.340, 0.392, -0.032, 0.226, 0.262),
    (1.250, 0.410, -0.032, 0.236, 0.276),
    (1.200, 0.418, -0.032, 0.240, 0.282),
]
SUPER = 2.5                      # ring squareness (2 = ellipse)
BLEND = (1.500, 1.540)           # the hood rings blend into the capelet tent over these heights
TENT_FLARE = 0.22                # the tent widens by this much per metre down from 1.47 (the folds' cloth)
PIN_BAND = (0.015, 0.05)         # the brim band pinned (full to the first, eased to none at the second, metres)
HOOD_HOLD = 1.0                  # the hood above the neck held to its built (folded) shape: wet heavy wool keeps its volume
BEND = 1.5                       # wool's bending stiffness
FRAMES = 60
SELF_COLLIDE = os.environ.get("HOOD_SELF", "0") == "1"   # (on, the capelet crumples: 28 Oct w8)
POSE_DEG = 40.0                  # the upper arms lowered from the bind pose for the drape (then unposed)
# the face opening, front view (x from X0, y), the left half from the top centre round to the bottom centre
OPENING = [(0.000, 1.703), (0.022, 1.701), (0.040, 1.695), (0.051, 1.686), (0.058, 1.674), (0.062, 1.660),
           (0.064, 1.640), (0.065, 1.615), (0.067, 1.590), (0.070, 1.565), (0.072, 1.545), (0.068, 1.528),
           (0.052, 1.518), (0.028, 1.513), (0.000, 1.512)]
HEM_Y = 1.215                    # the straight hem before the tear (front lower, back and sides a little higher)
VOXEL = 0.0085                   # the sim's cloth grid
LO_TRIS = 4300                   # the outer surface's budget (x2 with the inner shell, + rim and fringe)
LOD_TRIS, SHADOW_TRIS = 2400, 600
TEX = 4096
WOOL = (0.13, 0.145, 0.19)       # sRGB
MAT_WOOL, MAT_INNER, MAT_FRINGE = "warden_hood_wool", "warden_hood_inner", "warden_hood_fringe"
THICK = 0.0045


def log(*a):
    print("[warden_hood]", *a, flush=True)


def prof(y):
    t = np.array(PROFILE)
    return [np.interp(y, t[::-1, 0], t[::-1, k]) for k in range(1, 5)]


TENT = None   # (rows y, sectors theta, radius): the capelet's starting tent over the posed shoulders (tent())


def r_hood(y, th):
    """The hood's ring at y (a squarish ellipse round (X0, zc)) as a radius at polar angles th."""
    a, zc, bf, bb = prof(y)
    ph = np.linspace(0, 2 * np.pi, 1024, endpoint=False)
    s, c = np.sin(ph), np.cos(ph)
    e = 2.0 / SUPER
    x = a * np.sign(s) * np.abs(s) ** e
    z = np.where(c > 0, bf, bb) * np.sign(c) * np.abs(c) ** e
    t = np.arctan2(x, z) % (2 * np.pi)
    r = np.hypot(x, z)
    o = np.argsort(t)
    t, r = t[o], r[o]
    return np.interp(th % (2 * np.pi), np.concatenate([t - 2 * np.pi, t, t + 2 * np.pi]), np.concatenate([r, r, r]))


def r_tent(y, th):
    ys, ths, R = TENT
    i = np.interp(y, ys, np.arange(len(ys)))
    i0 = int(np.clip(np.floor(i), 0, len(ys) - 2))
    f = i - i0
    row = R[i0] * (1 - f) + R[i0 + 1] * f
    tt = np.concatenate([ths - 2 * np.pi, ths, ths + 2 * np.pi])
    return np.interp(th % (2 * np.pi), tt, np.concatenate([row, row, row]))


def ring_r(y, th):
    w = smoothstep(BLEND[0], BLEND[1], y)
    if TENT is None or w >= 1:
        return r_hood(y, th)
    return r_hood(y, th) * w + r_tent(y, th) * (1 - w)


def ring(y, n):
    th = np.linspace(0, 2 * np.pi, n, endpoint=False)
    r = ring_r(y, th)
    zc = prof(y)[1]
    return np.stack([X0 + r * np.sin(th), np.full(n, y), zc + r * np.cos(th)], 1)


def tent(Vb):
    """The capelet's start: round the posed body's shoulders, arms and chest, the widest point at or above each height
    (a tent that falls straight from the shoulders), plus a gap that grows toward the hem (cloth to fold)."""
    global TENT
    ys = np.arange(HEM_Y - 0.03, BLEND[1] + 0.011, 0.01)
    ths = np.linspace(0, 2 * np.pi, 120, endpoint=False)
    sel = Vb[(Vb[:, 1] > HEM_Y - 0.05) & (Vb[:, 1] < 1.535)]
    zc = np.array([prof(y)[1] for y in sel[:, 1]])
    t = np.arctan2(sel[:, 0] - X0, sel[:, 2] - zc) % (2 * np.pi)
    r = np.hypot(sel[:, 0] - X0, sel[:, 2] - zc)
    k = (t / (2 * np.pi) * len(ths)).astype(int) % len(ths)
    R = np.zeros((len(ys), len(ths)))
    for i, y in enumerate(ys):
        m = sel[:, 1] >= y - 0.005
        row = np.zeros(len(ths))
        np.maximum.at(row, k[m], r[m])
        R[i] = row
    # sectors smoothed (a max over 3, then a mean over 5), the gap added
    R = np.maximum(np.maximum(R, np.roll(R, 1, 1)), np.roll(R, -1, 1))
    R = sum(np.roll(R, d, 1) for d in range(-2, 3)) / 5
    gap = 0.022 + TENT_FLARE * np.clip(1.47 - ys, 0, None)
    TENT = (ys, ths, R + gap[:, None])
    log(f"tent: {len(sel)} body points; hem radius {R[0].min() + gap[0]:.3f}-{R[0].max() + gap[0]:.3f} m")


def opening_poly():
    L = np.array(OPENING)
    R = L[::-1].copy()
    R[:, 0] *= -1
    return np.concatenate([L, R[1:-1]])  # (x rel, y), closed


def inside_poly(pts, poly):
    x, y = pts[:, 0], pts[:, 1]
    ins = np.zeros(len(pts), bool)
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        c = ((y1 > y) != (y2 > y)) & (x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1)
        ins ^= c
    return ins


def nearest_on_poly(p, poly):
    best, bd = None, 1e9
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        ab = b - a
        t = np.clip(np.dot(p - a, ab) / (np.dot(ab, ab) + 1e-12), 0, 1)
        q = a + t * ab
        d = np.sum((q - p) ** 2)
        if d < bd:
            bd, best = d, q
    return best


def mk(name, V, F, coll=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in V], [], [tuple(f) for f in F])
    me.update()
    ob = bpy.data.objects.new(name, me)
    (coll or bpy.context.scene.collection).objects.link(ob)
    return ob


def verts(ob):
    a = np.zeros(len(ob.data.vertices) * 3)
    ob.data.vertices.foreach_get("co", a)
    return a.reshape(-1, 3)


def set_verts(ob, V):
    ob.data.vertices.foreach_set("co", np.asarray(V, np.float64).ravel())
    ob.data.update()


def apply_mods(ob):
    select_only(ob)
    for m in list(ob.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)


# ================= the body (collider and weight donor) =================
def load_body(pkg):
    g = Glb(os.path.join(pkg, "body.glb"))
    skin = g.j["skins"][0]
    names = [g.j["nodes"][n]["name"] for n in skin["joints"]]
    out = {"g": g, "names": names, "prims": {}}
    for p in g.j["meshes"][0]["primitives"]:
        mat = g.j["materials"][p["material"]]["name"]
        P = g.acc(p["attributes"]["POSITION"]).astype(float)
        F = g.acc(p["indices"]).reshape(-1, 3).astype(np.int64)
        J = g.acc(p["attributes"]["JOINTS_0"]).astype(np.int64)
        W = g.acc(p["attributes"]["WEIGHTS_0"]).astype(float)
        out["prims"][mat] = dict(P=P, F=F, J=J, W=W, prim=p)
    return out


def collider(body):
    Vs, Fs, o = [], [], 0
    for mat in ("generated", "warden_face", "warden_patch"):
        d = body["prims"][mat]
        keep = d["P"][d["F"]].mean(1)[:, 1] > 1.0
        Vs.append(d["P"])
        Fs.append(d["F"][keep] + o)
        o += len(d["P"])
    V, F = np.concatenate(Vs), np.concatenate(Fs)
    used = np.unique(F)
    remap = -np.ones(len(V), np.int64)
    remap[used] = np.arange(len(used))
    ob = mk("collider", g2b(V[used]), remap[F])
    return ob


# ================= 1. the shape =================
def shell():
    ys = np.arange(PROFILE[0][0] - 0.004, PROFILE[-1][0] - 1e-6, -0.004)
    n = 220
    rings = [ring(y, n) for y in ys]
    V = [np.array([[X0, PROFILE[0][0], PROFILE[0][2]]])] + rings
    bot = np.array([[X0, ys[-1], -0.03]])
    V = np.concatenate(V + [bot])
    F = []
    for i in range(n):
        F.append((0, 1 + (i + 1) % n, 1 + i))
    for r in range(len(rings) - 1):
        a, b = 1 + r * n, 1 + (r + 1) * n
        for i in range(n):
            j = (i + 1) % n
            F.append((a + i, a + j, b + j, b + i))
    last = 1 + (len(rings) - 1) * n
    for i in range(n):
        F.append((last + i, last + (i + 1) % n, len(V) - 1))
    ob = mk("hood_shape", g2b(V), F)
    m = ob.modifiers.new("vox", "REMESH")
    m.mode = "VOXEL"
    m.voxel_size = VOXEL
    m.use_smooth_shade = True
    apply_mods(ob)
    # the hem's cap and the face opening out
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    poly = opening_poly()
    gone = []
    for f in bm.faces:
        c = b2g(np.array([f.calc_center_median()]))[0]
        nrm = b2g(np.array([f.normal]))[0]
        if c[1] < HEM_Y or (c[1] < ys[-1] + 0.01 and nrm[1] < -0.6):
            gone.append(f)
            continue
        a, zc, bf, bb = prof(c[1])
        if c[2] > zc + 0.25 * bf and inside_poly(np.array([[c[0] - X0, c[1]]]), poly)[0]:
            gone.append(f)
    bmesh.ops.delete(bm, geom=gone, context="FACES")
    # loose bits
    bm.verts.ensure_lookup_table()
    bm.to_mesh(ob.data)
    bm.free()
    keep_largest(ob)
    # the opening's edge onto the outline (front view), the hem level
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    for v in bm.verts:
        if not v.is_boundary:
            continue
        p = b2g(np.array([v.co]))[0]
        if p[1] > HEM_Y + 0.05:
            q = nearest_on_poly(np.array([p[0] - X0, p[1]]), poly)
            p[0], p[1] = q[0] + X0, q[1]
        else:
            p[1] = HEM_Y
        v.co = Vector(g2b(np.array([p]))[0])
    # (snapping can stack boundary verts: zero-length edges make the cloth's springs blow up)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0025)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=0.0008)
    bm.to_mesh(ob.data)
    bm.free()
    log(f"shell: {len(ob.data.vertices)} verts, {len(ob.data.polygons)} faces")
    return ob


def hood_folds(ob, seed=21):
    """The hood's own folds (it keeps its shape; only the capelet is draped): soft vertical folds down the back and the
    sides that deepen toward the neck, a few ripples gathered behind the brim, a slow lumpiness, the peak slumped a
    little to one side. Displaced along the normal."""
    rng = np.random.default_rng(seed)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.normal_update()
    edge = [b2g(np.array([v.co]))[0] for v in bm.verts if v.is_boundary and b2g(np.array([v.co]))[0][1] > HEM_Y + 0.08]
    t = KDTree(len(edge))
    for i, p in enumerate(edge):
        t.insert(p, i)
    t.balance()
    ph = rng.uniform(0, 2 * np.pi, 4)
    for v in bm.verts:
        p = b2g(np.array([v.co]))[0]
        y = p[1]
        if y < 1.50:
            continue
        th = math.atan2(p[0] - X0, p[2] - prof(y)[1])
        back = smoothstep(-0.5, 0.3, -math.cos(th))
        # vertical folds: 9 round the head, wandering with height, sharp valleys and round ridges
        s1 = math.sin(9 * th + 2.2 * math.sin(7 * y + ph[0]) + ph[1])
        f1 = (abs(s1) ** 0.6 * (1 if s1 > 0 else -1.6)) * 0.018 * smoothstep(1.84, 1.62, y) * (0.35 + 0.65 * back)
        s2 = math.sin(5 * th + ph[2] + 3.0 * y)
        f2 = s2 * 0.010 * smoothstep(1.86, 1.70, y)
        de = t.find(p)[2]
        front_top = smoothstep(0.2, 0.7, math.cos(th)) * smoothstep(1.62, 1.68, y)
        f3 = math.sin(2 * math.pi * de / 0.024 + ph[3]) * 0.006 * math.exp(-de / 0.05) * front_top
        f4 = 0.007 * math.sin(3 * th + 11 * y + ph[0]) * math.sin(2 * th - 7 * y + ph[2])
        w = smoothstep(1.50, 1.56, y)
        v.co = v.co + v.normal * (f1 + f2 + f3 + f4) * w
        v.co.x += 0.012 * smoothstep(1.79, 1.86, y)
    bm.to_mesh(ob.data)
    bm.free()
    log("hood folds laid")


def clean(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0025)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=0.0008)
    bm.to_mesh(ob.data)
    bm.free()
    E = np.array([e.vertices[:] for e in ob.data.edges])
    V = verts(ob)
    L = np.linalg.norm(V[E[:, 0]] - V[E[:, 1]], axis=1)
    log(f"cleaned: {len(V)} verts; edges min {L.min() * 1000:.2f} mm, median {np.median(L) * 1000:.1f} mm")


def keep_largest(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    seen, parts = set(), []
    for f in bm.faces:
        if f.index in seen:
            continue
        stack, part = [f], []
        seen.add(f.index)
        while stack:
            x = stack.pop()
            part.append(x)
            for e in x.edges:
                for y in e.link_faces:
                    if y.index not in seen:
                        seen.add(y.index)
                        stack.append(y)
        parts.append(part)
    parts.sort(key=len)
    dead = [f for p in parts[:-1] for f in p]
    if dead:
        bmesh.ops.delete(bm, geom=dead, context="FACES")
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context="VERTS")
    bm.to_mesh(ob.data)
    bm.free()


def push_clear(ob, col, gap=0.010, iters=6):
    """Shell vertices inside the body (or nearer than gap) moved out along the body's normal, then smoothed."""
    bvh = eval_mesh_bvh(col)[0]
    V = verts(ob)
    adj = adjacency(ob)
    moved = 0
    for it in range(iters):
        for i, v in enumerate(V):
            if b2g(v[None])[0][1] > 1.56:
                continue   # (the hood is built clear of the head; a nearest point inside the face's mouth or sockets would pull it in)
            hit = bvh.find_nearest(Vector(v), 0.04)
            if hit[0] is None:
                continue
            d = np.dot(v - np.array(hit[0]), np.array(hit[1]))
            if d < gap:
                V[i] = np.array(hit[0]) + np.array(hit[1]) * gap
                moved += it == 0
        V = 0.5 * V + 0.5 * np.array([V[a].mean(0) if len(a) else V[i] for i, a in enumerate(adj)]) if it < iters - 1 else V
    set_verts(ob, V)
    log(f"pushed clear of the body: {moved} verts")


def adjacency(ob):
    adj = [[] for _ in ob.data.vertices]
    for e in ob.data.edges:
        a, b = e.vertices
        adj[a].append(b)
        adj[b].append(a)
    return adj


# ================= 2. grain UVs =================
def grain_uv(ob):
    """Per loop, from the rest shape: u = arc length round the ring from the front centre line (both islands 0 at the
    front, C/2 at the back seam), v = arc length down the meridian from the peak; the right island packed above the
    left one in 0..1. Returns the metres the map spans."""
    yy = np.linspace(HEM_Y - 0.02, PROFILE[0][0], 300)
    n = 2048
    arc = []
    for y in yy:
        R = ring(y, n)
        seg = np.linalg.norm(np.diff(np.vstack([R, R[:1]]), axis=0), axis=1)
        arc.append(np.concatenate([[0], np.cumsum(seg)]))
    arc = np.array(arc)  # [row, phi index 0..n]: arc from the front centre, arc[:, n] = the ring's length
    nm = 64
    mer = np.zeros((len(yy), nm))
    for k, ph in enumerate(np.linspace(0, 2 * np.pi, nm, endpoint=False)):
        pts = np.array([ring_pt(y, ph) for y in yy[::-1]])
        s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
        mer[:, k] = s[::-1]
    V = b2g(verts(ob))
    rr = np.interp(V[:, 1], yy, np.arange(len(yy)))
    r0 = np.clip(np.floor(rr).astype(int), 0, len(yy) - 2)
    fr = rr - r0
    ph = np.array([phi_of(p) for p in V])
    k = ph / (2 * np.pi) * n
    k0 = np.clip(k.astype(int), 0, n - 1)
    kf = k - k0
    A = lambda r: arc[r, k0] * (1 - kf) + arc[r, k0 + 1] * kf
    a_v = A(r0) * (1 - fr) + A(r0 + 1) * fr
    C = arc[r0, n] * (1 - fr) + arc[r0 + 1, n] * fr
    km = ph / (2 * np.pi) * nm
    m0 = km.astype(int) % nm
    m1 = (m0 + 1) % nm
    mf = km - np.floor(km)
    vm = lambda m: mer[r0, m] * (1 - fr) + mer[r0 + 1, m] * fr
    v_v = vm(m0) * (1 - mf) + vm(m1) * mf
    me = ob.data
    li_v = np.zeros(len(me.loops), np.int64)
    me.loops.foreach_get("vertex_index", li_v)
    side = np.zeros(len(me.loops), bool)  # left
    for poly in me.polygons:
        side[poly.loop_start:poly.loop_start + poly.loop_total] = V[list(poly.vertices)].mean(0)[0] < X0
    a, c = a_v[li_v], C[li_v]
    u = np.where(side, np.where(a < 0.25 * c, -a, c - a), np.where(a > 0.75 * c, a - c, a))
    v = v_v[li_v]
    span_u = u.max() - u.min()
    span_v = v.max()
    scale = 1.0 / max(span_u * 1.02, 2 * span_v * 1.04)
    global GRAIN
    GRAIN = (scale, float(u.min()))
    U = (u - u.min()) * scale + 0.005
    Vv = v * scale + 0.005 + np.where(side, 0.5, 0.0)
    uvl = me.uv_layers.new(name="UVMap")
    uvl.data.foreach_set("uv", np.stack([U, 1 - Vv], 1).astype(np.float32).ravel())
    log(f"grain UVs: {span_u:.2f} x {span_v:.2f} m an island, {1 / scale / TEX * 1000:.2f} mm a texel at {TEX}")
    return 1.0 / scale


def ring_pt(y, th):
    r = ring_r(y, np.array([th]))[0]
    return np.array([X0 + r * math.sin(th), y, prof(y)[1] + r * math.cos(th)])


def phi_of(p):
    return math.atan2(p[0] - X0, p[2] - prof(p[1])[1]) % (2 * math.pi)


# ================= the drape pose =================
def armature():
    return next(o for o in bpy.data.objects if o.type == "ARMATURE")


def pose_arms(deg):
    """The upper arms lowered by deg about the body's forward axis (from the bind pose's wide A), for the drape."""
    arm = armature()
    bpy.context.view_layer.update()
    Mw = arm.matrix_world
    fwd = Vector(g2b(np.array([[0, 0, 1.0]]))[0])
    for name, sgn in (("upperarm_l", -1), ("upperarm_r", 1)):
        pb = arm.pose.bones[name]
        head_w = Mw @ pb.head
        R = mathutils.Matrix.Translation(head_w) @ mathutils.Matrix.Rotation(math.radians(deg * sgn), 4, fwd) @ mathutils.Matrix.Translation(-head_w)
        pb.matrix = Mw.inverted() @ R @ Mw @ pb.matrix
        bpy.context.view_layer.update()
    log(f"drape pose: upper arms lowered {deg} deg")


def skin_mats(names):
    """Per joint: the posed-from-bind matrix (Blender world), the joint order of the glb's skin."""
    arm = armature()
    Mw = arm.matrix_world
    out = []
    for n in names:
        pb = arm.pose.bones.get(n)
        if pb is None:
            out.append(np.eye(4))
            continue
        out.append(np.array((Mw @ pb.matrix) @ (Mw @ pb.bone.matrix_local).inverted()))
    return np.array(out)


def posed_body(bobs):
    _, V, F = eval_mesh_bvh(bobs)
    return b2g(V), V, F


# ================= 3. the drape =================
def pin_group(ob):
    """Pinned: the brim band (1 at the opening's edge, eased to 0 by PIN_BAND), the hood held softly above the neck."""
    me = ob.data
    V = b2g(verts(ob))
    bnd = set()
    for e in me.edges:
        pass
    bm = bmesh.new()
    bm.from_mesh(me)
    edge_pts = np.array([b2g(np.array([v.co]))[0] for v in bm.verts if v.is_boundary and b2g(np.array([v.co]))[0][1] > HEM_Y + 0.05])
    bm.free()
    t = KDTree(len(edge_pts))
    for i, p in enumerate(edge_pts):
        t.insert(p, i)
    t.balance()
    d = np.array([t.find(p)[2] for p in V])
    w = np.maximum(1 - smoothstep(PIN_BAND[0], PIN_BAND[1], d), HOOD_HOLD * smoothstep(1.525, 1.585, V[:, 1]))
    g = ob.vertex_groups.new(name="pin")
    for i, x in enumerate(w):
        if x > 0.001:
            g.add([i], float(x), "REPLACE")
    log(f"pins: {(w > 0.99).sum()} held, {((w > 0.001) & (w <= 0.99)).sum()} eased")


def drape(ob, bobs, frames):
    sc = bpy.context.scene
    for b in bobs:
        c = b.modifiers.new("collide", "COLLISION")
        b.collision.thickness_outer = 0.006
        b.collision.thickness_inner = 0.01
        b.collision.cloth_friction = 8.0
        b.collision.damping = 0.5
    m = ob.modifiers.new("cloth", "CLOTH")
    cs = m.settings
    cs.quality = 10
    cs.mass = 0.35
    cs.air_damping = 2.0
    cs.tension_stiffness = 30
    cs.compression_stiffness = 30
    cs.shear_stiffness = 12
    cs.bending_stiffness = BEND
    cs.tension_damping = 8
    cs.compression_damping = 8
    cs.bending_damping = 0.8
    cs.vertex_group_mass = "pin"
    cs.pin_stiffness = 4.0
    cc = m.collision_settings
    cc.collision_quality = 4
    cc.distance_min = 0.006
    cc.use_self_collision = SELF_COLLIDE
    cc.self_distance_min = 0.003
    cc.self_friction = 8
    m.point_cache.frame_start = 1
    m.point_cache.frame_end = frames
    sc.frame_start, sc.frame_end = 1, frames
    t0 = time.time()
    for f in range(1, frames + 1):
        sc.frame_set(f)
        if f % 5 == 0 or f < 4:
            e = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
            P = np.array([v.co[:] for v in e.data.vertices])
            log(f"  drape frame {f}/{frames} ({time.time() - t0:.0f} s): box {np.round(P.min(0), 2).tolist()} {np.round(P.max(0), 2).tolist()}")
    select_only(ob)
    bpy.ops.object.modifier_apply(modifier=m.name)
    for b in bobs:
        b.modifiers.remove(b.modifiers["collide"])
    log(f"draped: {frames} frames in {time.time() - t0:.0f} s")


def smooth_edge(ob, reach=0.04, iters=12):
    """The cut opening's ragged voxel edge eased: verts near the boundary relaxed (the boundary itself held)."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    B = [v for v in bm.verts if v.is_boundary]
    if not B:
        bm.free()
        return
    t = KDTree(len(B))
    for i, v in enumerate(B):
        t.insert(v.co, i)
    t.balance()
    near = [v for v in bm.verts if not v.is_boundary and t.find(v.co)[2] < reach]
    for _ in range(iters):
        new = {v: sum((e.other_vert(v).co for e in v.link_edges), Vector()) / len(v.link_edges) for v in near}
        for v, c in new.items():
            v.co = v.co * 0.4 + c * 0.6
    # the boundary itself, along the edge only (a 1D smooth keeps it on the outline)
    for _ in range(4):
        new = {}
        for v in B:
            nb = [e.other_vert(v) for e in v.link_edges if e.is_boundary]
            if len(nb) == 2:
                new[v] = (nb[0].co + nb[1].co) * 0.5
        for v, c in new.items():
            v.co = v.co * 0.5 + c * 0.5
    bm.to_mesh(ob.data)
    bm.free()


# ================= 4. the tear, the budget, the maps =================
def loop_uv(ob):
    me = ob.data
    uv = np.zeros(len(me.loops) * 2)
    me.uv_layers.active.data.foreach_get("uv", uv)
    return uv.reshape(-1, 2)


def uv_metres(uv):
    """Loop UVs back to the grain's metres: (u from the front centre line, v down from the peak, left island?)."""
    scale, umin = GRAIN
    V = 1 - uv[:, 1]
    left = V > 0.5
    return (uv[:, 0] - 0.005) / scale + umin, (V - 0.005 - left * 0.5) / scale, left


def vnoise1(x, scale, seed):
    rng = np.random.default_rng(seed)
    k = rng.random(4096)
    t = x / scale
    i = np.floor(t).astype(int)
    f = t - i
    f = f * f * (3 - 2 * f)
    return k[i % 4096] * (1 - f) + k[(i + 1) % 4096] * f


def tear_hem(ob, seed=7):
    """The capelet's hem torn: faces within a ragged depth of the hem (by the grain's v, per u along the hem) go:
    a wavering line (1-3 cm) and a few V tears (4-10 cm deep, 3-6 cm wide)."""
    me = ob.data
    uv = loop_uv(ob)
    u, v, left = uv_metres(uv)
    fu = np.zeros(len(me.polygons))
    fv = np.zeros(len(me.polygons))
    fl = np.zeros(len(me.polygons), bool)
    for p in me.polygons:
        s = slice(p.loop_start, p.loop_start + p.loop_total)
        fu[p.index], fv[p.index], fl[p.index] = u[s].mean(), v[s].mean(), left[s].mean() > 0.5
    # one coordinate round the hem: right island u, left island -u
    t = np.where(fl, -fu, fu)
    bins = np.round(t / 0.01).astype(int)
    vmax = {}
    for b, x in zip(bins, fv):
        vmax[b] = max(vmax.get(b, 0), x)
    hem = np.array([max(vmax.get(b + d, 0) for d in (-1, 0, 1)) for b in bins])
    depth = 0.008 + 0.022 * vnoise1(t + 5, 0.06, seed) ** 1.5 + 0.008 * vnoise1(t + 5, 0.017, seed + 1)
    rng = np.random.default_rng(seed)
    span = t.max() - t.min()
    for c in t.min() + span * np.sort(rng.random(9)):
        w, dp = rng.uniform(0.03, 0.06), rng.uniform(0.04, 0.10)
        depth = np.maximum(depth, dp * np.clip(1 - np.abs(t - c) / (w / 2), 0, None) ** 1.3)
    near_hem = fv > 0.30   # (the capelet only: the hood's opening is far above)
    gone = near_hem & (fv > hem - depth)
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.faces[i] for i in np.nonzero(gone)[0]], context="FACES")
    bm.to_mesh(me)
    bm.free()
    keep_largest(ob)
    log(f"hem torn: {int(gone.sum())} faces")


def decimated(ob, tris, name):
    lo = ob.copy()
    lo.data = ob.data.copy()
    lo.name = name
    bpy.context.scene.collection.objects.link(lo)
    lo.modifiers.clear()
    n = sum(len(p.vertices) - 2 for p in lo.data.polygons)
    m = lo.modifiers.new("dec", "DECIMATE")
    m.decimate_type = "COLLAPSE"
    m.ratio = min(1.0, tris / max(n, 1))
    m.use_collapse_triangulate = True
    apply_mods(lo)
    log(f"{name}: {sum(len(p.vertices) - 2 for p in lo.data.polygons)} tris (from {n})")
    return lo


def bake_lo(hi, lo, size, ao_objs):
    """The fine drape's normals onto the reduced surface (tangent space, Blender's = glTF's), and its ambient occlusion
    among the body (the hood's inside, the folds' valleys)."""
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    mat = bpy.data.materials.new("bake_target")
    mat.use_nodes = True
    lo.data.materials.clear()
    lo.data.materials.append(mat)
    tn = mat.node_tree.nodes.new("ShaderNodeTexImage")
    mat.node_tree.nodes.active = tn
    bk = sc.render.bake
    bk.margin = 16
    out = {}
    img = bpy.data.images.new("hood_n", size, size, alpha=False, float_buffer=True)
    img.colorspace_settings.name = "Non-Color"
    tn.image = img
    sc.cycles.samples = 4
    bk.use_selected_to_active = True
    bk.cage_extrusion = 0.012
    bk.max_ray_distance = 0.03
    select_only(hi, lo)
    t0 = time.time()
    bpy.ops.object.bake(type="NORMAL")
    out["normal"] = np.array(img.pixels[:]).reshape(size, size, 4)[::-1, :, :3].copy()
    log(f"baked the drape's normals at {size} ({time.time() - t0:.0f} s)")
    img2 = bpy.data.images.new("hood_ao", size // 2, size // 2, alpha=False, float_buffer=True)
    img2.colorspace_settings.name = "Non-Color"
    tn.image = img2
    sc.cycles.samples = 48
    bk.use_selected_to_active = False
    hide = [o for o in bpy.data.objects if o.type == "MESH" and o not in ao_objs and o is not lo]
    for o in hide:
        o.hide_render = True
    select_only(lo)
    t0 = time.time()
    bpy.ops.object.bake(type="AO")
    for o in hide:
        o.hide_render = False
    out["ao"] = np.array(img2.pixels[:]).reshape(size // 2, size // 2, 4)[::-1, :, 0].copy()
    log(f"baked AO at {size // 2} ({time.time() - t0:.0f} s)")
    return out


def blur(a, r):
    from scipy import ndimage
    return ndimage.gaussian_filter(a, r)


def vnoise2(shape, cell, seed):
    rng = np.random.default_rng(seed)
    gh, gw = shape[0] // cell + 2, shape[1] // cell + 2
    g = rng.random((gh, gw))
    from scipy import ndimage
    return ndimage.zoom(g, (shape[0] / (gh - 1), shape[1] / (gw - 1)), order=3)[:shape[0], :shape[1]]


def wool_maps(bk, size):
    """Albedo, roughness and normal in the grain UVs: the WOOL charcoal-navy with felted mottling and a fibre fuzz,
    darker and wetter toward the hem (by the grain's v, the soak line wandering), the drape's AO in the valleys; a 2/2
    twill normal on top of the baked drape (UDN)."""
    scale, umin = GRAIN
    px = 1.0 / scale / size                      # metres a texel
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    Vimg = (yy + 0.5) / size                       # (row 0 = top = V 1 in UV terms: image row = 1 - V)
    left = Vimg > 0.5
    vm = (Vimg - 0.005 - left * 0.5) / scale       # metres down from the peak
    um = (xx + 0.5) / size / scale                 # metres along the ring (from the island's start)
    # the soak: from ~0.22 m down (the shoulders) to the hem (~0.75 m), with a wandering line
    wander = (vnoise2((size, size), size // 24, 3) - 0.5) * 0.10
    wet = smoothstep(0.24, 0.62, vm + wander)
    wet = np.clip(wet + 0.18 * smoothstep(0.55, 0.75, vm), 0, 1)
    mott = vnoise2((size, size), size // 40, 5) * 0.6 + vnoise2((size, size), size // 140, 6) * 0.4
    fuzz = np.random.default_rng(9).random((size, size)).astype(np.float32)
    fuzz = blur(fuzz, 0.7)
    ao = np.asarray(Image.fromarray((np.clip(bk["ao"], 0, 1) * 255).astype(np.uint8)).resize((size, size), Image.BILINEAR), np.float32) / 255
    ao = blur(ao, 1.2)
    lin = lambda c: np.where(np.asarray(c) <= 0.04045, np.asarray(c) / 12.92, ((np.asarray(c) + 0.055) / 1.055) ** 2.4)
    base = lin(np.array(WOOL))
    k = (0.86 + 0.28 * mott + 0.10 * (fuzz - 0.5)) * (1 - 0.42 * wet) * (0.50 + 0.50 * ao)
    col = base[None, None, :] * k[..., None]
    # a faint greenish river stain in the soaked hem (the river's silt), and the dry top a touch greyer (felted fibres)
    col = col * (1 + wet[..., None] * np.array([-0.06, 0.04, -0.02]) * (mott[..., None] > 0.45))
    srgb = np.where(col <= 0.0031308, col * 12.92, 1.055 * np.power(np.clip(col, 0, None), 1 / 2.4) - 0.055)
    albedo = Image.fromarray((np.clip(srgb, 0, 1) * 255 + 0.5).astype(np.uint8))
    rough = np.clip(0.88 - 0.30 * wet + 0.05 * (mott - 0.5) + 0.04 * (fuzz - 0.5), 0.4, 1.0)
    mr = np.zeros((size, size, 3), np.uint8)
    mr[..., 1] = (rough * 255 + 0.5).astype(np.uint8)
    mr_img = Image.fromarray(mr).resize((size // 2, size // 2), Image.LANCZOS)
    # 2/2 twill: warp threads along v (pitch P), weft along u; a warp float rises where (i + j) mod 4 < 2
    P = 0.0011
    i = np.floor(um / P)
    j = np.floor(vm / P)
    fu, fv = um / P - i, vm / P - j
    up = ((i + j) % 4) < 2
    yarn_u = np.sin(np.pi * fu) ** 0.7     # across a warp thread
    yarn_v = np.sin(np.pi * fv) ** 0.7
    h = np.where(up, yarn_u, yarn_v) * 0.6 + 0.4 * blur(fuzz, 1.5)
    h = blur(h.astype(np.float32), 0.6) * (1 - 0.5 * wet)    # (wet wool lies flatter)
    gy, gx = np.gradient(h)
    s = 1.4
    nd = np.stack([-gx * s, gy * s, np.ones_like(h)], -1)
    nb = bk["normal"] * 2 - 1
    n = np.stack([nb[..., 0] + nd[..., 0], nb[..., 1] + nd[..., 1], nb[..., 2]], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-8
    nimg = Image.fromarray((np.clip(n * 0.5 + 0.5, 0, 1) * 255 + 0.5).astype(np.uint8))
    log(f"wool maps: {px * 1000:.2f} mm a texel, twill pitch {P * 1000:.1f} mm")
    return {"color": albedo, "mr": mr_img, "normal": nimg}


def fringe_map(w=1024, h=256, seed=11):
    """The frayed edge's strands (RGBA): a felted root band that splits into loose yarn ends of mixed length, a few
    longer strays; colour the wet wool's, a touch lighter at the tips. v 0 = the cloth's edge, 1 = the strip's end."""
    rng = np.random.default_rng(seed)
    a = np.zeros((h, w), np.float32)
    lit = np.zeros((h, w), np.float32)
    yy = np.arange(h)[:, None] / h
    root = np.clip(1 - yy / 0.22, 0, 1) ** 0.6 * np.ones((1, w))
    a = np.maximum(a, root * (0.75 + 0.25 * rng.random((1, w))))
    xs = np.arange(w)[None, :]
    for _ in range(170):
        x0 = rng.uniform(0, w)
        L = rng.uniform(0.25, 0.75) if rng.random() > 0.1 else rng.uniform(0.75, 0.98)
        wd = rng.uniform(1.5, 4.0)
        bend = rng.uniform(-30, 30)
        cx = x0 + bend * yy ** 2 + 3 * np.sin(yy * rng.uniform(6, 14) + rng.uniform(0, 6))
        d = np.abs(((xs - cx) + w / 2) % w - w / 2)
        taper = np.clip(1 - yy / L, 0, 1) ** 0.35
        s = np.clip(1 - d / (wd * (0.4 + 0.6 * taper)), 0, 1) * (yy < L)
        a = np.maximum(a, s)
        lit = np.maximum(lit, s * yy / L)
    rgb = np.array(WOOL)[None, None, :] * (0.75 + 0.35 * lit[..., None])
    img = np.concatenate([np.clip(rgb, 0, 1), np.clip(a, 0, 1)[..., None]], -1)
    return Image.fromarray((img * 255 + 0.5).astype(np.uint8), "RGBA")


# ================= 5. thickness and the fringe =================
def thicken(lo):
    m = lo.modifiers.new("solid", "SOLIDIFY")
    m.thickness = THICK
    m.offset = -1.0
    m.use_rim = True
    m.use_even_offset = False   # (even thickness throws spikes where the reduced cloth folds back)
    m.use_quality_normals = True
    m.material_offset = 1
    m.material_offset_rim = 0
    apply_mods(lo)
    log(f"thickened: {sum(len(p.vertices) - 2 for p in lo.data.polygons)} tris")


def fringe(lo, src):
    """Strips along the outer boundary of src (the opening and the hem), in the cloth's plane, away from the cloth:
    hem 2.6 cm, opening 1.1 cm; u along the edge (10 cm a repeat), v across."""
    bm = bmesh.new()
    bm.from_mesh(src.data)
    bm.normal_update()
    V, F, UV = [], [], []
    for e in bm.edges:
        if not e.is_boundary:
            continue
        f = e.link_faces[0]
        a, b = e.verts
        mid = (a.co + b.co) / 2
        t = (b.co - a.co)
        out = t.cross(f.normal).normalized()
        if out.dot(mid - f.calc_center_median()) < 0:
            out = -out
        y = b2g(np.array([mid]))[0][1]
        L = 0.011 if y > HEM_Y + 0.12 else 0.026
        out = (out * 0.75 + Vector(g2b(np.array([[0, -1.0, 0]]))[0]) * (0.25 if L > 0.02 else 0.0)).normalized()
        k = len(V)
        rng_l = 0.8 + 0.4 * ((hash((round(mid.x, 3), round(mid.y, 3))) % 1000) / 1000)
        for p in (a.co, b.co):
            V.append(p - f.normal * 0.0005)
            V.append(p + out * L * rng_l - f.normal * 0.002)
        ua = (a.co.x * 7.3 + a.co.y * 5.1 + a.co.z * 6.7)
        ub = ua + t.length / 0.10
        UV += [(ua, 1.0), (ua, 0.0), (ub, 1.0), (ub, 0.0)]   # (texture v 0 at the edge: image top = UV 1)
        F.append((k, k + 2, k + 3, k + 1))
    bm.free()
    ob = mk("fringe", V, F)
    uvl = ob.data.uv_layers.new(name="UVMap")
    lu = np.zeros((len(ob.data.loops), 2))
    for p in ob.data.polygons:
        for li in p.loop_indices:
            lu[li] = UV[ob.data.loops[li].vertex_index]
    uvl.data.foreach_set("uv", lu.astype(np.float32).ravel())
    log(f"fringe: {len(F)} strips")
    return ob


# ================= 6. skinning =================
def body_posed_donors(body, mats):
    """The body's points (generated, the collar patch, the head's neck) at the drape pose, with their weights."""
    P, J, W = [], [], []
    for mat in ("generated", "warden_patch", "warden_face"):
        d = body["prims"][mat]
        keep = d["P"][:, 1] > 1.05
        Pb = g2b(d["P"][keep])
        Jk, Wk = d["J"][keep], d["W"][keep]
        M = np.einsum("nk,nkij->nij", Wk, mats[Jk])
        pp = np.einsum("nij,nj->ni", M[:, :3, :3], Pb) + M[:, :3, 3]
        P.append(pp)
        J.append(Jk)
        W.append(Wk)
    return np.concatenate(P), np.concatenate(J), np.concatenate(W)


def hood_weights(Vb, adj, donors, names, nb):
    """Per vertex (Blender frame, drape pose): the body's weights near it (6 nearest, by 1/d), minus the forearms and
    hands; the hood above the jaw to Head (eased in over 1.535-1.590), smoothed, the 4 largest kept."""
    P, J, W = donors
    no = {names.index(n) for n in names if any(k in n for k in ("lowerarm", "hand", "index", "middle", "ring", "pinky", "thumb"))}
    t = KDTree(len(P))
    for i, p in enumerate(P):
        t.insert(p, i)
    t.balance()
    A = np.zeros((len(Vb), nb))
    for i, v in enumerate(Vb):
        for co, j, d in t.find_n(v, 8):
            w = 1.0 / max(d, 0.004)
            for k in range(4):
                if W[j, k] > 0 and J[j, k] not in no:
                    A[i, J[j, k]] += w * W[j, k]
    A /= A.sum(1, keepdims=True) + 1e-12
    y = b2g(Vb)[:, 1]
    head = names.index("Head")
    wh = smoothstep(1.535, 1.590, y)
    A *= (1 - wh)[:, None]
    A[:, head] += wh
    fixed = y > 1.60
    for _ in range(8):
        S = np.array([A[a].mean(0) if len(a) else A[i] for i, a in enumerate(adj)])
        A = np.where(fixed[:, None], A, 0.5 * A + 0.5 * S)
    Jo = np.argsort(-A, 1)[:, :4]
    Wo = np.take_along_axis(A, Jo, 1)
    Wo /= Wo.sum(1, keepdims=True)
    used = sorted({names[j] for j in np.unique(Jo[Wo > 0.01])})
    return Jo.astype(np.uint16), Wo.astype(np.float32), used


def unpose(Vb, Nb, J, W, mats):
    """Drape pose -> bind (glTF frame): each vertex by the inverse of its blended skin matrix."""
    M = np.einsum("nk,nkij->nij", W.astype(float), mats[J.astype(int)])
    Mi = np.linalg.inv(M)
    p = np.einsum("nij,nj->ni", Mi[:, :3, :3], Vb) + Mi[:, :3, 3]
    n = np.einsum("nji,nj->ni", M[:, :3, :3], Nb)   # (normals by the inverse transpose)
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    return b2g(p), b2g(n)


# ================= 7. the piece =================
def corner_arrays(ob):
    """A triangulated copy's corners (Blender frame): vertex index, position, corner normal, uv, material per triangle."""
    me = ob.data
    me.calc_loop_triangles()
    nt = len(me.loop_triangles)
    tl = np.zeros(nt * 3, np.int64)
    me.loop_triangles.foreach_get("loops", tl)
    tm = np.zeros(nt, np.int64)
    me.loop_triangles.foreach_get("material_index", tm)
    lv = np.zeros(len(me.loops), np.int64)
    me.loops.foreach_get("vertex_index", lv)
    cn = np.zeros(len(me.loops) * 3)
    me.corner_normals.foreach_get("vector", cn)
    uv = loop_uv(ob) if me.uv_layers else np.zeros((len(me.loops), 2))
    return dict(tl=tl.reshape(-1, 3), tm=tm, lv=lv, cn=cn.reshape(-1, 3), uv=uv, P=verts(ob))


def prims_of(c, J, W, P_bind, N_bind_of_corner, mat_ids):
    """glTF primitives (one per material id): corners deduplicated on (vertex, normal, uv)."""
    out = {}
    for m in mat_ids:
        tris = c["tl"][c["tm"] == m]
        if not len(tris):
            continue
        loops = tris.ravel()
        v = c["lv"][loops]
        n = N_bind_of_corner[loops]
        uv = c["uv"][loops]
        key = np.concatenate([v[:, None].astype(float), np.round(n, 3), np.round(uv, 5)], 1)
        uk, inv = np.unique(key, axis=0, return_inverse=True)
        first = np.zeros(len(uk), np.int64)
        first[inv] = np.arange(len(loops))
        vv = v[first]
        out[m] = dict(pos=P_bind[vv].astype(np.float32), nrm=n[first].astype(np.float32),
                      uv=np.stack([uv[first, 0], 1 - uv[first, 1]], 1).astype(np.float32),
                      idx=inv.reshape(-1).astype(np.uint32), J=J[vv], W=W[vv])
    return out


def enc(im, fmt, q=92):
    import io
    b = io.BytesIO()
    im.save(b, fmt, quality=q) if fmt == "JPEG" else im.save(b, fmt, optimize=True)
    return b.getvalue()


def write_piece(pkg, path, parts):
    """armor/hood.glb: body.glb's skeleton and skin, its meshes replaced by the hood's (parts: [(node name, prims by
    material name)]) and the hood's materials."""
    g = Glb(os.path.join(pkg, "body.glb"))
    j = g.j
    drop = [i for i, n in enumerate(j["nodes"]) if n.get("name", "").startswith("ford_warden") and n.get("name") != "ford_warden"]
    g.drop_nodes(drop)
    j["materials"], j["textures"], j["images"], j["samplers"] = [], [], [], []
    j["meshes"] = []
    tex = MAPS
    tc = g.add_image(enc(tex["color"], "JPEG", 92), "image/jpeg", "hood_color")
    tn = g.add_image(enc(tex["normal"], "JPEG", 95), "image/jpeg", "hood_normal")
    tm = g.add_image(enc(tex["mr"], "PNG"), "image/png", "hood_mr")
    tf = g.add_image(enc(tex["fringe"], "PNG"), "image/png", "hood_fringe")
    mats = {
        MAT_WOOL: {"name": MAT_WOOL, "pbrMetallicRoughness": {"baseColorTexture": {"index": tc}, "metallicRoughnessTexture": {"index": tm},
                                                             "metallicFactor": 0.0, "roughnessFactor": 1.0},
                   "normalTexture": {"index": tn}},
        MAT_INNER: {"name": MAT_INNER, "pbrMetallicRoughness": {"baseColorFactor": [0.006, 0.007, 0.010, 1.0], "metallicFactor": 0.0,
                                                               "roughnessFactor": 0.95}},
        MAT_FRINGE: {"name": MAT_FRINGE, "pbrMetallicRoughness": {"baseColorTexture": {"index": tf}, "metallicFactor": 0.0, "roughnessFactor": 0.85},
                     "alphaMode": "MASK", "alphaCutoff": 0.45, "doubleSided": True},
    }
    order = list(mats)
    j["materials"] = [mats[k] for k in order]
    arm = j["scenes"][0]["nodes"][0]
    body_node = next(i for i, n in enumerate(j["nodes"]) if n.get("name") == "ford_warden")
    for k, (node_name, prims) in enumerate(parts):
        mesh = {"name": node_name, "primitives": []}
        for mat, arr in prims.items():
            a = {"POSITION": g.add_acc(arr["pos"], "VEC3", minmax=True), "NORMAL": g.add_acc(arr["nrm"], "VEC3"),
                 "TEXCOORD_0": g.add_acc(arr["uv"], "VEC2"), "JOINTS_0": g.add_acc(arr["J"].astype(np.uint16), "VEC4"),
                 "WEIGHTS_0": g.add_acc(arr["W"].astype(np.float32), "VEC4")}
            mesh["primitives"].append({"attributes": a, "indices": g.add_acc(arr["idx"], "SCALAR", target=34963),
                                       "material": order.index(mat), "mode": 4})
        j["meshes"].append(mesh)
        if k == 0:
            j["nodes"][body_node] = {"name": node_name, "mesh": 0, "skin": 0}
        else:
            j["nodes"].append({"name": node_name, "mesh": k, "skin": 0})
            j["nodes"][arm].setdefault("children", []).append(len(j["nodes"]) - 1)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    g.save(path)
    log(f"wrote {path} ({os.path.getsize(path) / 1e6:.1f} MB)")


MAPS = {}
GRAIN = (1.0, 0.0)


# ================= 8. the mantle under the capelet =================
def cut_mantle(pkg, out_pkg, HP, HF, margin=0.05):
    """body.glb and lod.glb: the generated fur mantle where the capelet covers it (a triangle whose outward ray, or
    level ray from the body's axis, meets the hood within 20 cm; of the ID map's wool class; more than `margin` above
    the capelet's hem at its side), and the collar filler (warden_patch) the hood covers. Index-only: the kept
    vertices, UVs and atlas untouched."""
    bvh = BVHTree.FromPolygons(HP.tolist(), HF.tolist())
    ths = np.arctan2(HP[:, 0] - X0, HP[:, 2] + 0.03)
    sec = ((ths + np.pi) / (2 * np.pi) * 72).astype(int) % 72
    hem = np.full(72, 9.0)
    np.minimum.at(hem, sec, HP[:, 1])
    hem = np.minimum(np.minimum(hem, np.roll(hem, 1)), np.roll(hem, -1))
    idm = np.asarray(Image.open(os.path.join(pkg, "id_generated.png")))
    stats = {}
    for fname in ("body.glb", "lod.glb"):
        g = Glb(os.path.join(pkg, fname))
        for mesh in g.j["meshes"]:
            for p in mesh["primitives"]:
                mat = g.j["materials"][p["material"]]["name"] if "material" in p else ""
                if mat not in ("generated", "warden_patch"):
                    continue
                P = g.acc(p["attributes"]["POSITION"]).astype(float)
                F = g.acc(p["indices"]).reshape(-1, 3).astype(np.int64)
                C = P[F].mean(1)
                N = np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]])
                N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-12
                cand = np.nonzero(C[:, 1] > (1.20 if mat == "generated" else 1.40))[0]
                drop = np.zeros(len(F), bool)
                if mat == "generated" and "TEXCOORD_0" in p["attributes"]:
                    uv = g.acc(p["attributes"]["TEXCOORD_0"])
                    tuv = uv[F].mean(1)
                    h, w = idm.shape[:2]
                    px = np.clip((tuv[:, 0] % 1) * w, 0, w - 1).astype(int)
                    py = np.clip((tuv[:, 1] % 1) * h, 0, h - 1).astype(int)
                    wool = (idm[py, px, 0] >> 5) == 0
                else:
                    wool = np.ones(len(F), bool)
                for t in cand:
                    if not wool[t]:
                        continue
                    c = C[t]
                    s = int(((math.atan2(c[0] - X0, c[2] + 0.03) + np.pi) / (2 * np.pi) * 72)) % 72
                    if c[1] < hem[s] + margin:
                        continue
                    radial = np.array([c[0] - X0, 0, c[2] + 0.03])
                    radial /= np.linalg.norm(radial) + 1e-9
                    for d in (N[t], radial):
                        if bvh.ray_cast(Vector(c + d * 0.002), Vector(d), 0.20)[0] is not None:
                            drop[t] = True
                            break
                if drop.any():
                    p["indices"] = g.add_acc(F[~drop].astype(np.uint32).ravel(), "SCALAR", target=34963)
                stats[f"{fname}:{mesh.get('name', '')}:{mat}"] = int(drop.sum())
        g.save(os.path.join(out_pkg, fname))
    log("mantle cut", json.dumps(stats))
    return stats


# ================= renders and numbers =================
def import_body(pkg):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(pkg, "body.glb"))
    return [o for o in bpy.data.objects if o not in before and o.type == "MESH"]


def eval_mesh_bvh(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    Vs, Fs, o = [], [], 0
    for ob in objs:
        e = ob.evaluated_get(dg)
        me = e.to_mesh()
        M = np.array(e.matrix_world)
        V = np.zeros(len(me.vertices) * 3)
        me.vertices.foreach_get("co", V)
        V = V.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
        me.calc_loop_triangles()
        F = np.zeros(len(me.loop_triangles) * 3, np.int64)
        me.loop_triangles.foreach_get("vertices", F)
        Vs.append(V)
        Fs.append(F.reshape(-1, 3) + o)
        o += len(V)
        e.to_mesh_clear()
    V, F = np.concatenate(Vs), np.concatenate(Fs)
    return BVHTree.FromPolygons(V.tolist(), F.tolist()), V, F


def face_numbers(face_obs, hood_obs):
    """Front view (parallel rays along -Z): the share of the face's front (above the chin) that shows past the hood;
    the highest and widest face points that show; the brim's depth before the brow; the moonlit share of the forehead
    and upper eye sockets that show (rays to a moon 35 and 50 degrees up, in front)."""
    fb, _, _ = eval_mesh_bvh(face_obs)
    hb, _, _ = eval_mesh_bvh(hood_obs)
    res = {}
    D = Vector(g2b(np.array([[0, 0, -1.0]]))[0])
    shown, total, pts = 0, 0, []
    for y in np.arange(1.50, 1.80, 0.002):
        for x in np.arange(X0 - 0.11, X0 + 0.11, 0.002):
            o = Vector(g2b(np.array([[x, y, 0.6]]))[0])
            hf = fb.ray_cast(o, D, 1.0)
            if hf[0] is None:
                continue
            p = b2g(np.array([hf[0]]))[0]
            if p[1] < 1.575 or p[2] < 0.0:   # (the face's front above the mouth; the beard's ground below)
                continue
            total += 1
            hh = hb.ray_cast(o, D, 1.0)
            if hh[0] is None or hh[3] > hf[3]:
                shown += 1
                pts.append(p)
    pts = np.array(pts) if pts else np.zeros((0, 3))
    res["faceShownShare"] = round(shown / max(total, 1), 3)
    if len(pts):
        res["shownTopAboveEyesMm"] = round((pts[:, 1].max() - EYE_Y) * 1000, 1)
        res["shownXmm"] = [round((pts[:, 0].min() - X0) * 1000, 1), round((pts[:, 0].max() - X0) * 1000, 1)]
    best = None
    for y in np.arange(BROW_Y, BROW_Y + 0.05, 0.001):
        o = Vector(g2b(np.array([[X0, y, 0.6]]))[0])
        h = hb.ray_cast(o, D, 1.0)
        if h[0] is not None:
            p = b2g(np.array([h[0]]))[0]
            best = p if best is None or p[2] > best[2] else best
    if best is not None:
        res["brimBeforeBrowMm"] = round((best[2] - BROW_Z) * 1000, 1)
        res["brimLowestYAboveBrowMm"] = None
    for y in np.arange(BROW_Y - 0.03, BROW_Y + 0.05, 0.001):
        o = Vector(g2b(np.array([[X0, y, 0.6]]))[0])
        if hb.ray_cast(o, D, 1.0)[0] is not None:
            res["brimLowestYAboveBrowMm"] = round((y - BROW_Y) * 1000, 1)
            break
    sel = pts[(pts[:, 1] > EYE_Y - 0.002) & (np.abs(pts[:, 0] - X0) < 0.055)] if len(pts) else pts
    for elev in (35, 50):
        e = math.radians(elev)
        L = Vector(g2b(np.array([[0.0, math.sin(e), math.cos(e)]]))[0])
        lit = sum(hb.ray_cast(Vector(g2b(np.array([p]))[0]) + L * 0.002, L, 2.0)[0] is None for p in sel)
        res[f"browLitShare{elev}"] = round(lit / max(len(sel), 1), 3)
    res["browPoints"] = int(len(sel))
    log("numbers", json.dumps(res))
    return res


def look_at(cam, eye_g, target_g):
    e, t = Vector(g2b(np.array([eye_g]))[0]), Vector(g2b(np.array([target_g]))[0])
    cam.location = e
    cam.rotation_euler = (t - e).to_track_quat("-Z", "Z").to_euler()


def sun(name, energy, colour, dir_g):
    s = bpy.data.objects.new(name, bpy.data.lights.new(name, "SUN"))
    bpy.context.scene.collection.objects.link(s)
    s.data.energy = energy
    s.data.color = colour
    s.data.angle = math.radians(1.0)
    d = Vector(g2b(np.array([dir_g]))[0]).normalized()   # (toward the light)
    s.rotation_euler = (-d).to_track_quat("-Z", "Z").to_euler()
    return s


def setup_render():
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE_NEXT"
    sc.render.resolution_x = sc.render.resolution_y = 900
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.010, 0.013, 0.025, 1)
    sun("moon", 4.0, (0.75, 0.85, 1.0), [0.35, math.sin(math.radians(40)), math.cos(math.radians(40))])
    sun("fill", 0.5, (0.5, 0.6, 0.9), [-0.6, 0.2, -0.7])
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.clip_start = 0.05


VIEWS = {  # name: eye, target, focal (package frame)
    "front": ([X0, 1.66, 1.10], [X0, 1.62, 0.0], 85),
    "bust34": ([0.70, 1.70, 0.85], [X0, 1.58, 0.0], 60),
    "side": ([1.10, 1.62, 0.02], [X0, 1.52, 0.0], 50),
    "back": ([-0.50, 1.80, -1.25], [X0, 1.45, -0.05], 45),
    "body": ([0.40, 1.45, 2.6], [X0, 1.25, 0.0], 45),
    "low": ([0.20, 1.35, 0.80], [X0, 1.64, 0.06], 60),
}


def renders(work, tag):
    cam = bpy.context.scene.camera
    out = []
    for name, (eye, tgt, f) in VIEWS.items():
        cam.data.lens = f
        look_at(cam, eye, tgt)
        p = os.path.join(work, f"{tag}_{name}.png")
        bpy.context.scene.render.filepath = p
        bpy.ops.render.render(write_still=True)
        out.append(p)
    ims = [Image.open(p).convert("RGB").resize((450, 450), Image.LANCZOS) for p in out]
    sheet = Image.new("RGB", (450 * 3, 900))
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % 3) * 450, (i // 3) * 450))
    sp = os.path.join(work, f"{tag}_sheet.jpg")
    sheet.save(sp, quality=88)
    log("sheet", sp)


def preview_mat(ob, rgb=(0.015, 0.019, 0.032), rough=0.85):
    mat = bpy.data.materials.new("wool_preview")
    mat.use_nodes = True
    bs = mat.node_tree.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (*rgb, 1)
    bs.inputs["Roughness"].default_value = rough
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    for p in ob.data.polygons:
        p.use_smooth = True


def save_drape(ob, path):
    me = ob.data
    cnt = np.array([p.loop_total for p in me.polygons])
    lv = np.zeros(len(me.loops), np.int64)
    me.loops.foreach_get("vertex_index", lv)
    np.savez(path, V=verts(ob), cnt=cnt, lv=lv, uv=loop_uv(ob), grain=np.array(GRAIN))


def load_drape(path):
    global GRAIN
    d = np.load(path)
    GRAIN = tuple(d["grain"])
    cnt, lv = d["cnt"], d["lv"]
    starts = np.concatenate([[0], np.cumsum(cnt)[:-1]])
    F = [lv[s:s + c].tolist() for s, c in zip(starts, cnt)]
    ob = mk("hood_shape", d["V"], F)
    uvl = ob.data.uv_layers.new(name="UVMap")
    uvl.data.foreach_set("uv", d["uv"].astype(np.float32).ravel())
    return ob


def preview_textured(ob):
    def img(pil, name, data):
        p = os.path.join(bpy.app.tempdir, name + ".png")
        pil.save(p)
        im = bpy.data.images.load(p)
        im.colorspace_settings.name = "Non-Color" if data else "sRGB"
        return im
    wool = bpy.data.materials.new("pv_wool")
    wool.use_nodes = True
    nt = wool.node_tree
    bs = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexImage")
    tc.image = img(MAPS["color"], "c", False)
    nt.links.new(tc.outputs[0], bs.inputs["Base Color"])
    tm = nt.nodes.new("ShaderNodeTexImage")
    tm.image = img(MAPS["mr"], "mr", True)
    sp = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(tm.outputs[0], sp.inputs[0])
    nt.links.new(sp.outputs[1], bs.inputs["Roughness"])
    tn = nt.nodes.new("ShaderNodeTexImage")
    tn.image = img(MAPS["normal"], "n", True)
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tn.outputs[0], nm.inputs[1])
    nt.links.new(nm.outputs[0], bs.inputs["Normal"])
    inner = bpy.data.materials.new("pv_inner")
    inner.use_nodes = True
    inner.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.006, 0.007, 0.010, 1)
    fr = bpy.data.materials.new("pv_fringe")
    fr.use_nodes = True
    nt = fr.node_tree
    bs = nt.nodes["Principled BSDF"]
    tf = nt.nodes.new("ShaderNodeTexImage")
    tf.image = img(MAPS["fringe"], "f", False)
    nt.links.new(tf.outputs[0], bs.inputs["Base Color"])
    nt.links.new(tf.outputs[1], bs.inputs["Alpha"])
    try:
        fr.surface_render_method = "DITHERED"
    except Exception:
        pass
    ob.data.materials.clear()
    for m in (wool, inner, fr):
        ob.data.materials.append(m)


def to_bind(ob, donors, names, mats):
    """An object's weights (drape pose) and its positions and corner normals at the bind (glTF frame)."""
    Vb = verts(ob)
    J, W, used = hood_weights(Vb, adjacency(ob), donors, names, len(names))
    c = corner_arrays(ob)
    P_bind, _ = unpose(Vb, np.tile([0, 0, 1.0], (len(Vb), 1)), J, W, mats)
    M = np.einsum("nk,nkij->nij", W.astype(float), mats[J.astype(int)])
    Ml = M[c["lv"]]
    n = np.einsum("nji,nj->ni", Ml[:, :3, :3], c["cn"])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    return c, J, W, P_bind, b2g(n), used


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    pkg = argv[0]
    opt = {argv[i][2:]: argv[i + 1] for i in range(len(argv) - 1) if argv[i].startswith("--")}
    work = opt.get("work", os.path.join(pkg, "..", "_check_hood"))
    src = opt.get("src", pkg)
    stage = opt.get("stage", "all")
    frames = int(opt.get("frames", FRAMES))
    os.makedirs(work, exist_ok=True)
    t0 = time.time()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    body = load_body(src)
    bobs = import_body(src)
    pose_arms(POSE_DEG)
    Vg, _, _ = posed_body(bobs)
    tent(Vg)
    if "drape" in opt:
        sh = load_drape(opt["drape"])
    else:
        sh = shell()
        smooth_edge(sh)
        hood_folds(sh)
        push_clear(sh, bobs)
        clean(sh)
        grain_uv(sh)
        pin_group(sh)
    setup_render()
    preview_mat(sh)
    if stage == "shell":
        face_numbers(bobs, [sh])
        renders(work, "shell")
        log(f"done in {time.time() - t0:.0f} s")
        return
    if "drape" not in opt:
        drape(sh, bobs, frames)
        save_drape(sh, os.path.join(work, "drape.npz"))
        if stage == "drape":
            face_numbers(bobs, [sh])
            renders(work, "drape")
            log(f"done in {time.time() - t0:.0f} s")
            return
    # ---- the tear, the budget, the maps ----
    tear_hem(sh)
    for p in sh.data.polygons:
        p.use_smooth = True
    lo = decimated(sh, LO_TRIS, "hood_lo")
    bk = bake_lo(sh, lo, TEX, [lo] + bobs)
    MAPS.update(wool_maps(bk, TEX))
    MAPS["fringe"] = fringe_map()
    for k in ("color", "normal", "mr", "fringe"):
        MAPS[k].save(os.path.join(work, f"map_{k}.png"))
    lod1 = decimated(lo, LOD_TRIS // 2, "hood_lod1")
    shadow = decimated(lo, SHADOW_TRIS, "hood_shadow")
    fr = fringe(lo, lo)
    slots = [bpy.data.materials.new(n) for n in ("slot_wool", "slot_inner", "slot_fringe")]
    for ob in (lo, lod1, shadow, fr):
        ob.data.materials.clear()
        for mt in (slots if ob is fr else slots[:2]):
            ob.data.materials.append(mt)
        for p in ob.data.polygons:
            p.material_index = 0
    thicken(lo)
    thicken(lod1)
    for p in fr.data.polygons:
        p.material_index = 2
    select_only(fr, lo)
    bpy.ops.object.join()
    sh.hide_render = True
    for ob in (lo, lod1):
        select_only(ob)
        bpy.ops.object.shade_smooth()   # (one smooth normal over the rim: a rounded wool edge, not a frame)
    # ---- skinned, unposed, written ----
    names = body["names"]
    mats = skin_mats(names)
    donors = body_posed_donors(body, mats)
    parts, info = [], {}
    for node, ob, ids in (("hood.wool", lo, (0, 1, 2)), ("hood.lod1.wool", lod1, (0, 1)), ("hood.shadow", shadow, (0,))):
        c, J, W, P_bind, Nc, used = to_bind(ob, donors, names, mats)
        prims = prims_of(c, J, W, P_bind, Nc, ids)
        parts.append((node, {(MAT_WOOL, MAT_INNER, MAT_FRINGE)[m]: a for m, a in prims.items()}))
        info[node] = {"tris": int(sum(len(a["idx"]) // 3 for a in prims.values())), "bones": used}
        if node == "hood.wool":
            HP, HF = P_bind, c["lv"][c["tl"]]
            HFw = c["lv"][c["tl"][c["tm"] < 2]]
    log("piece", json.dumps(info))
    write_piece(pkg, os.path.join(pkg, "armor", "hood.glb"), parts)
    cut = cut_mantle(src, pkg, HP, HFw)
    # ---- manifest ----
    mp = os.path.join(pkg, "manifest.json")
    m = json.load(open(mp))
    m["pieces"] = [{"id": "hood", "slot": "cloak", "file": "armor/hood.glb"}]
    m["hood"] = {"source": "tools/assets/warden_hood.py (cloth drape over the posed body, Warden 6)", "materials": [MAT_WOOL, MAT_INNER, MAT_FRINGE],
                 "tris": info["hood.wool"]["tris"], "lodTris": info["hood.lod1.wool"]["tris"], "shadowTris": info["hood.shadow"]["tris"],
                 "bones": info["hood.wool"]["bones"], "maps": TEX, "mantleCut": cut}
    json.dump(m, open(mp, "w"), indent=1)
    # ---- numbers and renders (the drape pose) ----
    preview_textured(lo)
    for o in (lod1, shadow):
        o.hide_render = True
    res = face_numbers(bobs, [lo])
    json.dump({"numbers": res, "piece": info, "mantleCut": cut}, open(os.path.join(work, "numbers.json"), "w"), indent=1)
    renders(work, "hood")
    log(f"done in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
