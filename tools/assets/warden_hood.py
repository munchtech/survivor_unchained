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
SHOULDER_RIG = os.environ.get("HOOD_SHOULDER", "1") == "1"   # r3: the capelet's shoulders weighted to the torso
ARM_MAX = float(os.environ.get("HOOD_ARM_MAX", "0.3"))      # the upper arm's most, at the outer fall
SH_ARM = (0.21, 0.36)            # |x - X0| over which the upper arm comes in (the shoulder joint at 0.17-0.18)
SH_ARM_Y = (1.46, 1.34)          # and only below the shoulder's top (glTF y, eased in downward)
CLAV_MAX = 0.6                   # the clavicle's most at the shoulder (the rest spine_03)
SH_CLAV = (0.04, 0.16)
NECK_MAX = 0.4                   # the collar's top at the throat follows the neck a little
SH_BLEND = (0.0, 0.06)           # the rig replaces the donors' weights from the centre line out (all of the capelet)
POSE_DEG = 40.0                 # the upper arms lowered from the bind pose for the drape (then unposed)
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
FOLD_DEPTH = 0.022               # the hood's main folds, ridge to centre (r1's 0.018 sine read as a smooth shell)
BACK_TEAR_MAX = 0.032            # the back's tears stop short of the cape's attach line
BAND_ABOVE = 0.065               # the attach line: this far above the straight hem, on the back (grain metres)
FRINGE_RGB = (0.085, 0.095, 0.13)  # sRGB: the shaded wool's colour (the fringe is a plain material, not the wet shader)
ALB_GAIN = 1.87                  # the albedo to the body's wool atlas level
ROLL = (0.0065, 0.0050)          # the opening's rolled edge: half-thickness across the cloth, half-width in its plane


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
    """The hood's own folds (it keeps its shape; only the capelet is draped), heavy wet wool (r2: the r1 folds read as
    a smooth shell): 7 deep vertical folds falling from the crown round the back and sides, sharp valleys and round
    ridges, deepening toward the neck, with a few shallower ones between; the brim's own sag (its lip drooping a few
    mm, a crease across the top ~4 cm behind the edge); a roll where the hood meets the capelet (the hood's base piled
    on the shoulders, a valley under it), back and sides only (the throat stays clean for the beard); a slow lumpiness,
    the peak slumped a little to one side. Displaced along the normal."""
    rng = np.random.default_rng(seed)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.normal_update()
    edge = [b2g(np.array([v.co]))[0] for v in bm.verts if v.is_boundary and b2g(np.array([v.co]))[0][1] > HEM_Y + 0.08]
    t = KDTree(len(edge))
    for i, p in enumerate(edge):
        t.insert(p, i)
    t.balance()
    ph = rng.uniform(0, 2 * np.pi, 6)
    down = Vector(g2b(np.array([[0, -1.0, 0]]))[0])
    for v in bm.verts:
        p = b2g(np.array([v.co]))[0]
        y = p[1]
        if y < 1.46:
            continue
        th = math.atan2(p[0] - X0, p[2] - prof(y)[1])
        back = smoothstep(-0.6, 0.2, -math.cos(th))
        side = 1 - abs(math.cos(th))
        de = t.find(p)[2]
        # the main folds: 7 round the head (fewer at the front), wandering with height; from the crown down
        x1 = 7 * th + 1.6 * math.sin(6 * y + ph[0]) + ph[1]
        f1 = (2 * abs(math.cos(x1 / 2)) ** 0.8 - 1) * FOLD_DEPTH * smoothstep(1.865, 1.70, y) * (0.25 + 0.75 * back)
        # shallower folds between them
        s2 = math.sin(12 * th + ph[2] + 4.0 * y)
        f2 = (abs(s2) ** 0.7 * (1 if s2 > 0 else -1.5)) * 0.007 * smoothstep(1.84, 1.66, y) * (0.3 + 0.7 * side)
        # the brim's sag: a crease across the top behind the lip, the lip itself dropped a little
        front_top = smoothstep(0.15, 0.65, math.cos(th)) * smoothstep(1.62, 1.69, y)
        f3 = -0.009 * math.exp(-((de - 0.042) / 0.013) ** 2) * front_top + 0.004 * math.exp(-((de - 0.075) / 0.02) ** 2) * front_top
        sag = 0.005 * math.exp(-de / 0.03) * front_top * smoothstep(0.5, 0.95, math.cos(th))
        # the roll where the hood meets the capelet: a ridge at ~1.555, a valley under it at ~1.52 (back and sides)
        f5 = (0.013 * math.exp(-((y - 1.556) / 0.016) ** 2) - 0.010 * math.exp(-((y - 1.522) / 0.012) ** 2)) *             smoothstep(-0.2, 0.35, -math.cos(th)) * (0.7 + 0.3 * math.sin(5 * th + ph[3]))
        f4 = 0.006 * math.sin(3 * th + 11 * y + ph[0]) * math.sin(2 * th - 7 * y + ph[2])
        w = smoothstep(1.50, 1.56, y) * smoothstep(0.0, 0.035, de)
        v.co = v.co + v.normal * ((f1 + f2 + f4) * w + f3 * smoothstep(1.50, 1.56, y) + f5) + down * sag
        v.co.x += 0.012 * smoothstep(1.79, 1.86, y)
    bm.to_mesh(ob.data)
    bm.free()
    log("hood folds laid")


def smooth_throat(ob, col, iters=40):
    """The front of the throat under the chin (the drape crumples it where the hood's ring meets the capelet's tent):
    relaxed (Taubin, no shrink), the opening's edge held, then pushed clear of the body. A long beard will cover it."""
    V = b2g(verts(ob))
    th = np.arctan2(V[:, 0] - X0, V[:, 2] + 0.02)
    w = smoothstep(0.25, 0.75, np.cos(th)) * smoothstep(1.40, 1.45, V[:, 1]) * (1 - smoothstep(1.535, 1.56, V[:, 1]))
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bnd = np.array([v.is_boundary for v in bm.verts])
    bm.free()
    w[bnd] = 0
    adj = adjacency(ob)
    P = verts(ob)
    for it in range(iters):
        for lam in (0.55, -0.57):
            S = np.array([P[a].mean(0) if len(a) else P[i] for i, a in enumerate(adj)])
            P = P + (lam * w)[:, None] * (S - P)
    bvh = eval_mesh_bvh(col)[0]
    moved = 0
    for i in np.nonzero(w > 0.01)[0]:
        hit = bvh.find_nearest(Vector(P[i]), 0.04)
        if hit[0] is None:
            continue
        d = np.dot(P[i] - np.array(hit[0]), np.array(hit[1]))
        if d < 0.008:
            P[i] = np.array(hit[0]) + np.array(hit[1]) * 0.008
            moved += 1
    set_verts(ob, P)
    log(f"throat relaxed: {(w > 0.5).sum()} verts, {moved} pushed clear")


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
    # (the back: the tears held short of the long cape's attach line, BAND_ABOVE over the straight hem)
    C = np.array([b2g(np.array([p.center]))[0] for p in me.polygons])
    bw = smoothstep(-0.03, -0.09, C[:, 2] + 0.03)
    depth = depth * (1 - bw) + np.minimum(depth, BACK_TEAR_MAX) * bw
    HEM["bins"], HEM["v"] = {int(b): float(x) for b, x in zip(bins, hem)}, None
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
    # (r2: in game the wool is drawn by shaders/warden_wet.gdshader as the body's wool, class 0, which soaks it by
    #  height and pulls its hue: the map carries the felt's light and dark at the body's wool atlas level, linear
    #  luminance ~0.022 (the body's wool over the shoulders: mean 0.023, median 0.019), no soak of its own)
    k = (0.86 + 0.28 * mott + 0.10 * (fuzz - 0.5)) * (1 - 0.10 * wet) * (0.50 + 0.50 * ao) * ALB_GAIN
    col = base[None, None, :] * k[..., None]
    # a faint greenish river stain in the soaked hem (the river's silt), and the dry top a touch greyer (felted fibres)
    col = col * (1 + wet[..., None] * np.array([-0.06, 0.04, -0.02]) * (mott[..., None] > 0.45))
    srgb = np.where(col <= 0.0031308, col * 12.92, 1.055 * np.power(np.clip(col, 0, None), 1 / 2.4) - 0.055)
    albedo = Image.fromarray((np.clip(srgb, 0, 1) * 255 + 0.5).astype(np.uint8))
    log(f"wool albedo: linear luminance mean {float((col @ np.array([0.2126, 0.7152, 0.0722])).mean()):.4f}")
    rough = np.clip(0.62 - 0.08 * wet + 0.05 * (mott - 0.5) + 0.04 * (fuzz - 0.5), 0.3, 1.0)   # (the shader's variation round class 0's)
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
    # (r2: a thin felted root that frays straight away, in clumps, so the strip's edge never reads as a band of stubs)
    clump = np.clip(vnoise1(np.arange(w, dtype=float), 40.0, seed) * 1.6 - 0.3, 0, 1)[None, :]
    root = np.clip(1 - yy / (0.05 + 0.08 * clump), 0, 1) ** 0.8
    a = np.maximum(a, root * (0.55 + 0.45 * clump))
    xs = np.arange(w)[None, :]
    for _ in range(260):
        x0 = rng.uniform(0, w)
        L = rng.uniform(0.2, 0.7) if rng.random() > 0.12 else rng.uniform(0.7, 0.98)
        wd = rng.uniform(1.2, 3.0)
        bend = rng.uniform(-30, 30)
        cx = x0 + bend * yy ** 2 + 3 * np.sin(yy * rng.uniform(6, 14) + rng.uniform(0, 6))
        d = np.abs(((xs - cx) + w / 2) % w - w / 2)
        taper = np.clip(1 - yy / L, 0, 1) ** 0.35
        s = np.clip(1 - d / (wd * (0.4 + 0.6 * taper)), 0, 1) * (yy < L)
        a = np.maximum(a, s)
        lit = np.maximum(lit, s * yy / L)
    rgb = np.array(FRINGE_RGB)[None, None, :] * (0.80 + 0.85 * lit[..., None] ** 0.8)   # (r4: worn lighter fibre at the tips)
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


HEAD_C = np.array([0.0204, 1.68, 0.0])   # (glTF) inside the head: the cloth's outward side faces away from it


def boundary_loops(bm, pred):
    """The boundary's closed loops (bmesh verts, the edges between them, True), each walked by turning round its vertex
    through the faces to the next boundary edge (right at a bow-tie vertex); kept where pred(verts) holds."""
    def nxt(v, e):
        ce, cf = e, e.link_faces[0]
        for _ in range(64):
            oe = next((x for x in cf.edges if x is not ce and v in x.verts), None)
            if oe is None:
                return None
            if oe.is_boundary:
                return oe
            cf = next((f for f in oe.link_faces if f is not cf), None)
            if cf is None:
                return None
            ce = oe
        return None
    used, loops = set(), []
    for e0 in bm.edges:
        if not e0.is_boundary or e0 in used:
            continue
        seq, es = [e0.verts[0]], [e0]
        used.add(e0)
        v, e = e0.verts[1], e0
        closed = False
        for _ in range(100000):
            if v is seq[0]:
                closed = True
                break
            seq.append(v)
            e = nxt(v, e)
            if e is None or e in used:
                break
            used.add(e)
            es.append(e)
            v = e.other_vert(v)
        if len(seq) >= 4 and pred(seq):
            loops.append((seq, es, closed))
    return loops


def edge_frames(seq, es, closed):
    """Per loop vertex (glTF): position, the cloth's outward normal, the tangent, the in-plane direction off the cloth,
    the arc length."""
    P = np.array([b2g(np.array([v.co]))[0] for v in seq])
    N = np.array([b2g(np.array([v.normal]))[0] for v in seq])
    if np.mean(np.sum(N * (P - HEAD_C), 1)) < 0:
        N = -N
    n = len(P)
    nxt = np.roll(P, -1, 0) if closed else np.vstack([P[1:], P[-1:] * 2 - P[-2:-1]])
    prv = np.roll(P, 1, 0) if closed else np.vstack([P[:1] * 2 - P[1:2], P[:-1]])
    T = nxt - prv
    T /= np.linalg.norm(T, axis=1, keepdims=True) + 1e-12
    B = np.cross(T, N)
    B /= np.linalg.norm(B, axis=1, keepdims=True) + 1e-12
    # off the cloth: away from the faces the loop bounds
    FC = np.zeros((n, 3))
    for i in range(n):
        fs = []
        if closed or i > 0:
            fs.append(es[i - 1].link_faces[0])
        if i < len(es):
            fs.append(es[i].link_faces[0])
        FC[i] = np.mean([b2g(np.array([f.calc_center_median()]))[0] for f in fs], 0)
    flip = np.sum(B * (P - FC), 1) < 0
    B[flip] *= -1
    B = B - N * np.sum(B * N, 1, keepdims=True)
    B /= np.linalg.norm(B, axis=1, keepdims=True) + 1e-12
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    S = np.concatenate([[0], np.cumsum(seg)])
    return P, N, T, B, S


def roll_data(ob, K=8, seed=3):
    """The face opening's rolled edge (r2: the r1 edge read as a thin blocky frame): a soft thick lumpy roll of wool
    round the opening, about 13 mm thick and 10 mm across, wrapping the cut edge, its texture the brim's own (each
    quad's UVs from the face its edge bounds, stepping into the island). Built from the outer surface (before the
    thickness); laid on with add_roll() after it."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.normal_update()
    uvl = bm.loops.layers.uv.active
    loops = boundary_loops(bm, lambda q: np.mean([v.co.z for v in q]) > HEM_Y + 0.12)
    loops.sort(key=lambda L: -len(L[0]))
    seq, es, closed = loops[0]
    P, N, T, B, S = edge_frames(seq, es, closed)
    lump = 1 + 0.24 * (2 * vnoise1(S, 0.05, seed) - 1) + 0.08 * (2 * vnoise1(S, 0.015, seed + 1) - 1)
    if not closed:   # (a break in the decimated edge: the roll tapers to nothing at its ends, no stumps)
        lump = lump * np.maximum(smoothstep(0, 0.04, S) * smoothstep(0, 0.04, S[-1] - S), 0.05)
    rn, rb = ROLL[0] * lump, ROLL[1] * lump
    # (wrapping the cut edge, most of it over the cloth: the opening's outline stays where the spec puts it)
    Cc = P - B * (rb * 0.4)[:, None] - N * (THICK * 0.5 - 0.0015)
    ang = np.arange(K) / K * 2 * np.pi
    R = Cc[:, None, :] + N[:, None, :] * (rn[:, None, None] * np.cos(ang)[None, :, None]) + B[:, None, :] * (rb[:, None, None] * np.sin(ang)[None, :, None])
    perim = 2 * np.pi * np.sqrt((rn ** 2 + rb ** 2) / 2)
    scale = GRAIN[0]
    quads = []   # (ring i, ring j, uv rows for i and j: K+1 each)
    m = len(seq)
    for i in range(m if closed else m - 1):
        j = (i + 1) % m
        f = es[i].link_faces[0]
        luv = {l.vert: np.array(l[uvl].uv[:]) for l in f.loops}
        ua, ub = luv[seq[i]], luv[seq[j]]
        fc = np.mean([np.array(l[uvl].uv[:]) for l in f.loops], 0)
        d = fc - (ua + ub) / 2
        d /= np.linalg.norm(d) + 1e-12
        steps = np.arange(K + 1) / K
        quads.append((i, j, ua[None] + d[None] * (steps * perim[i] * scale)[:, None], ub[None] + d[None] * (steps * perim[j] * scale)[:, None]))
    bm.free()
    log(f"rolled edge: {m} rings x {K}, thickness {2 * rn.min() * 1000:.0f}-{2 * rn.max() * 1000:.0f} mm, closed {closed}")
    return dict(R=R, C=Cc, N=N, B=B, S=S, rn=rn, rb=rb, quads=quads, K=K, closed=closed)


def add_roll(ob, rd):
    """The rolled edge onto ob (material 0, smooth, outward)."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    uvl = bm.loops.layers.uv.active
    K = rd["K"]
    R = g2b(rd["R"].reshape(-1, 3)).reshape(rd["R"].shape)
    C = g2b(rd["C"])
    vs = [[bm.verts.new(Vector(R[i, k])) for k in range(K)] for i in range(len(R))]
    bm.verts.ensure_lookup_table()
    for i, j, uvi, uvj in rd["quads"]:
        for k in range(K):
            k1 = (k + 1) % K
            f = bm.faces.new((vs[i][k], vs[j][k], vs[j][k1], vs[i][k1]))
            f.material_index = 0
            f.smooth = True
            for l, uv in zip(f.loops, (uvi[k], uvj[k], uvj[k + 1], uvi[k + 1])):
                l[uvl].uv = Vector(uv)
            f.normal_update()
            if f.normal.dot(f.calc_center_median() - Vector(C[i])) < 0:
                f.normal_flip()
    bm.to_mesh(ob.data)
    bm.free()


FRINGE_MIN_Y = -1.0   # (Warden 7 r4) no hem strands below this height (glTF y): the cape's hem lies in the river


def fringe(lo, rd=None, seed=11):
    """Frayed strands along the boundary: the hem's (2.6 cm, off the cloth and a little down) and, with the rolled
    edge, the opening's (1.4 cm, from the roll's outer underside, hanging); continuous strips (shared verts, the
    length wandering smoothly along the edge: r1's per-edge lengths stepped into square stubs); u along the edge
    (10 cm a repeat), v across."""
    bm = bmesh.new()
    bm.from_mesh(lo.data)
    bm.normal_update()
    down = np.array([0, -1.0, 0])
    V, F, UV = [], [], []
    loops = boundary_loops(bm, lambda q: True)
    big = max((len(L[0]) for L in loops if np.mean([v.co.z for v in L[0]]) > HEM_Y + 0.12), default=0)
    for k_loop, (seq, es, closed) in enumerate(loops):
        if len(seq) < 4:
            continue
        P, N, T, B, S = edge_frames(seq, es, closed)
        if P[:, 1].mean() > HEM_Y + 0.12:
            if rd is None or len(seq) != big:
                continue
            # (from the roll: its outer underside)
            P = rd["C"] + rd["B"] * rd["rb"][:, None] * 0.85 - rd["N"] * rd["rn"][:, None] * 0.25
            N, B, S, closed = rd["N"], rd["B"], rd["S"], rd["closed"]
            L = 0.014 * (0.65 + 0.7 * vnoise1(S, 0.06, seed + k_loop))
            out = B * 0.55 + down[None] * 0.45
        else:
            L = 0.026 * (0.7 + 0.6 * vnoise1(S, 0.08, seed + k_loop))
            out = B * 0.75 + down[None] * 0.25
            P = P - N * 0.0005
        out /= np.linalg.norm(out, axis=1, keepdims=True) + 1e-12
        n = len(P)
        idx = list(range(n)) + ([0] if closed else [])
        total = S[-1] + (np.linalg.norm(P[0] - P[-1]) if closed else 0)
        k0 = len(V)
        for c, i in enumerate(idx):
            u = (S[i] if c < n else total) / 0.10
            V.append(P[i])
            V.append(P[i] + out[i] * L[i] - N[i] * 0.0015)
            UV += [(u, 1.0), (u, 0.0)]
        for c in range(len(idx) - 1):
            a = k0 + 2 * c
            if P[idx[c], 1] < FRINGE_MIN_Y and P[idx[c + 1], 1] < FRINGE_MIN_Y:
                continue
            F.append((a, a + 2, a + 3, a + 1))
    bm.free()
    ob = mk("fringe", g2b(np.array(V)), F)
    uvl = ob.data.uv_layers.new(name="UVMap")
    lu = np.zeros((len(ob.data.loops), 2))
    for p in ob.data.polygons:
        for li in p.loop_indices:
            lu[li] = UV[ob.data.loops[li].vertex_index]
    uvl.data.foreach_set("uv", lu.astype(np.float32).ravel())
    log(f"fringe: {len(F)} strips over {len(loops)} edge loops")
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


def hood_weights(Vb, adj, donors, names, nb, band=None):
    """Per vertex (Blender frame, drape pose): the body's weights near it (6 nearest, by 1/d), minus the forearms and
    hands; the hood above the jaw to Head (eased in over 1.535-1.590), smoothed, the 4 largest kept."""
    P, J, W = donors
    # (r2: and the arms' share and twist helpers: the game drives them its own way, and the capelet weighted to them
    #  ballooned off the shoulder in play, hundreds of times its rest length)
    no = {names.index(n) for n in names if any(k in n for k in ("lowerarm", "hand", "index", "middle", "ring", "pinky", "thumb", "share", "twist"))}
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
    if SHOULDER_RIG:
        # (r3: the capelet over the shoulders on the torso, not the arm. The nearest-donor weights gave the shoulder's
        #  cloth a quarter upper arm all the way up over the deltoid's top, so a raised arm (C02 s7, the lamp lifted)
        #  swung the cloth over the shoulder up with it into a second hood. Wet heavy wool lies on the shoulder and the
        #  arm comes up from under it: spine_03 at the centre, the clavicle taking over toward the shoulder, the upper
        #  arm only at the outer fall below the shoulder's top, at most ARM_MAX.)
        g = b2g(Vb)
        u = np.abs(g[:, 0] - X0)
        sl = np.where(g[:, 0] > X0, 1, -1)
        cl_, cr_ = names.index("clavicle_l"), names.index("clavicle_r")
        ul_, ur_ = names.index("upperarm_l"), names.index("upperarm_r")
        sp_, nk_ = names.index("spine_03"), names.index("neck_01")
        lx = 1 if b2g(P)[(J[:, 0] == cl_) & (W[:, 0] > 0.3), 0].mean() > X0 else -1
        arm = ARM_MAX * smoothstep(SH_ARM[0], SH_ARM[1], u) * smoothstep(SH_ARM_Y[0], SH_ARM_Y[1], y)
        clv = (1 - arm) * CLAV_MAX * smoothstep(SH_CLAV[0], SH_CLAV[1], u)
        nck = (1 - arm - clv) * NECK_MAX * smoothstep(1.47, 1.53, y) * (1 - smoothstep(0.05, 0.10, u))
        T = np.zeros_like(A)
        rows = np.arange(len(Vb))
        side_l = sl == lx
        T[rows, np.where(side_l, ul_, ur_)] += arm
        T[rows, np.where(side_l, cl_, cr_)] += clv
        T[rows, nk_] += nck
        torso = 1 - arm - clv - nck
        low = 0.5 * smoothstep(1.32, 1.20, y)          # (the hem's front and back below spine_03 share spine_02)
        T[rows, sp_] += torso * (1 - low)
        T[rows, names.index("spine_02")] += torso * low
        s = smoothstep(SH_BLEND[0], SH_BLEND[1], u) * (1 - wh)
        A = A * (1 - s)[:, None] + T * s[:, None]
    fixed = y > 1.60
    for _ in range(8):
        S = np.array([A[a].mean(0) if len(a) else A[i] for i, a in enumerate(adj)])
        A = np.where(fixed[:, None], A, 0.5 * A + 0.5 * S)
    if band is not None and band.max() > 0:
        # the back's band over the hem (the long cape's attach line, Warden 6): spine_03 at the centre, the clavicle
        # of each side taking up to half toward the shoulders, so the cape hangs from the upper back, not the arms
        sp, cl, cr = names.index("spine_03"), names.index("clavicle_l"), names.index("clavicle_r")
        x = b2g(Vb)[:, 0] - X0
        mk_ = (J[:, 0] == cl) & (W[:, 0] > 0.3)
        lx = np.mean(b2g(P)[mk_, 0]) - X0 if mk_.any() else 1.0
        sw = 0.5 * smoothstep(0.05, 0.20, np.abs(x))
        Tg = np.zeros_like(A)
        Tg[:, sp] = 1 - sw
        Tg[np.arange(len(x)), np.where(np.sign(x) == np.sign(lx), cl, cr)] += sw
        A = A * (1 - band)[:, None] + Tg * band[:, None]
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
HEM = {}


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


def vert_grain(ob, n_base):
    """Per vertex (the cloth's own, < n_base, materials 0/1): the grain's (u signed by island, v) in metres; NaN else."""
    me = ob.data
    uv = loop_uv(ob)
    u, v, left = uv_metres(uv)
    t = np.where(left, -u, u)
    G = np.full((len(me.vertices), 2), np.nan)
    lv = np.zeros(len(me.loops), np.int64)
    me.loops.foreach_get("vertex_index", lv)
    for p in me.polygons:
        if p.material_index > 1:
            continue
        for li in p.loop_indices:
            vi = lv[li]
            if vi < n_base and np.isnan(G[vi, 0]):
                G[vi] = (t[li], v[li])
    return G


def band_of(ob, n_base):
    """The cape band's weight per vertex (the back, from BAND_ABOVE + 2 cm over the straight hem down to it) and the
    attach line's vertices (within 6 mm of BAND_ABOVE over the straight hem, the back)."""
    G = vert_grain(ob, n_base)
    Vg = b2g(verts(ob))
    bw = smoothstep(-0.03, -0.09, Vg[:, 2] + 0.03)
    bins = HEM.get("bins", {})
    hv = np.array([max(bins.get(int(round(t / 0.01)) + d, 0) for d in (-1, 0, 1)) if not np.isnan(t) else 0 for t in G[:, 0]])
    v = np.nan_to_num(G[:, 1], nan=-1)
    band = bw * smoothstep(hv - BAND_ABOVE - 0.045, hv - BAND_ABOVE - 0.015, v) * (v > 0.3)
    line = (bw > 0.5) & (np.abs(v - (hv - BAND_ABOVE)) < 0.006) & (v > 0.3)
    return band, line


def to_bind(ob, donors, names, mats, n_base=None):
    """An object's weights (drape pose) and its positions and corner normals at the bind (glTF frame). Vertices past
    n_base (the rolled edge and the fringe) take the weights of the nearest cloth vertex, so they never part from it."""
    Vb = verts(ob)
    nbv = len(Vb) if n_base is None else n_base
    band, line = band_of(ob, nbv)
    J, W, used = hood_weights(Vb, adjacency(ob), donors, names, len(names), band)
    if nbv < len(Vb):
        t = KDTree(nbv)
        for i in range(nbv):
            t.insert(Vb[i], i)
        t.balance()
        for i in range(nbv, len(Vb)):
            j = t.find(Vb[i])[1]
            J[i], W[i] = J[j], W[j]
    c = corner_arrays(ob)
    P_bind, _ = unpose(Vb, np.tile([0, 0, 1.0], (len(Vb), 1)), J, W, mats)
    M = np.einsum("nk,nkij->nij", W.astype(float), mats[J.astype(int)])
    Ml = M[c["lv"]]
    n = np.einsum("nji,nj->ni", Ml[:, :3, :3], c["cn"])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    att = {}
    if line.any():
        L = P_bind[line]
        top = {}
        for jj, ww in zip(J[line], W[line]):
            for k in range(4):
                if ww[k] > 0.05:
                    top[names[jj[k]]] = top.get(names[jj[k]], 0) + float(ww[k])
        att = {"verts": int(line.sum()), "yMin": round(float(L[:, 1].min()), 3), "yMax": round(float(L[:, 1].max()), 3),
               "yCentre": round(float(L[np.argmin(np.abs(L[:, 0] - X0)), 1]), 3), "zCentre": round(float(L[np.argmin(np.abs(L[:, 0] - X0)), 2]), 3),
               "xSpan": [round(float(L[:, 0].min()), 3), round(float(L[:, 0].max()), 3)],
               "weights": {k: round(v / line.sum(), 2) for k, v in sorted(top.items(), key=lambda x: -x[1])[:4]}}
    return c, J, W, P_bind, b2g(n), used, att


def hood_id_map(pos, uv, idx, size=1024):
    """armor/hood_id.png in the wool's UVs, warden_id_map.py's format for shaders/warden_wet.gdshader: R class*32 +
    puff (all wool: 0), G bind height / 2 m (the soak by height), B/A the detail normal (flat: the wool's own normal
    map carries the twill). Rasterized, then grown into the gutters."""
    from scipy import ndimage
    H = np.full((size, size), np.nan, np.float32)
    T = idx.reshape(-1, 3)
    for tri in T:
        q = uv[tri] * size - 0.5
        y = pos[tri, 1]
        x0, y0 = np.floor(q.min(0)).astype(int)
        x1, y1 = np.ceil(q.max(0)).astype(int)
        x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, size - 1), min(y1, size - 1)
        if x1 < x0 or y1 < y0:
            continue
        gy, gx = np.mgrid[y0:y1 + 1, x0:x1 + 1]
        a, b_, c = q
        den = (b_[1] - c[1]) * (a[0] - c[0]) + (c[0] - b_[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        l1 = ((b_[1] - c[1]) * (gx - c[0]) + (c[0] - b_[0]) * (gy - c[1])) / den
        l2 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / den
        l3 = 1 - l1 - l2
        ins = (l1 >= -0.02) & (l2 >= -0.02) & (l3 >= -0.02)
        H[gy[ins], gx[ins]] = (l1 * y[0] + l2 * y[1] + l3 * y[2])[ins]
    hole = np.isnan(H)
    near = ndimage.distance_transform_edt(hole, return_distances=False, return_indices=True)
    H = H[near[0], near[1]]
    img = np.zeros((size, size, 4), np.uint8)
    img[..., 1] = np.clip(H / 2.0 * 255 + 0.5, 0, 255).astype(np.uint8)
    img[..., 2] = 128
    img[..., 3] = 128
    log(f"hood ID map: {size}, height {np.nanmin(H):.2f}-{np.nanmax(H):.2f} m, {(~hole).mean() * 100:.0f}% covered")
    return Image.fromarray(img, "RGBA")


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
    smooth_throat(sh, bobs)
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
    rd, rd1 = roll_data(lo, 8), roll_data(lod1, 5)
    fr = fringe(lo, rd)
    slots = [bpy.data.materials.new(n) for n in ("slot_wool", "slot_inner", "slot_fringe")]
    for ob in (lo, lod1, shadow, fr):
        ob.data.materials.clear()
        for mt in (slots if ob is fr else slots[:2]):
            ob.data.materials.append(mt)
        for p in ob.data.polygons:
            p.material_index = 0
    thicken(lo)
    thicken(lod1)
    n_base = {"hood.wool": len(lo.data.vertices), "hood.lod1.wool": len(lod1.data.vertices)}
    add_roll(lo, rd)
    add_roll(lod1, rd1)
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
    attach = {}
    for node, ob, ids in (("hood.wool", lo, (0, 1, 2)), ("hood.lod1.wool", lod1, (0, 1)), ("hood.shadow", shadow, (0,))):
        c, J, W, P_bind, Nc, used, att = to_bind(ob, donors, names, mats, n_base.get(node))
        if node == "hood.wool":
            attach = att
            log("attach line", json.dumps(att))
        prims = prims_of(c, J, W, P_bind, Nc, ids)
        parts.append((node, {(MAT_WOOL, MAT_INNER, MAT_FRINGE)[m]: a for m, a in prims.items()}))
        info[node] = {"tris": int(sum(len(a["idx"]) // 3 for a in prims.values())), "bones": used}
        if node == "hood.wool":
            HP, HF = P_bind, c["lv"][c["tl"]]
            HFw = c["lv"][c["tl"][c["tm"] < 2]]
            wp = prims[0]
    log("piece", json.dumps(info))
    write_piece(src, os.path.join(pkg, "armor", "hood.glb"), parts)
    hood_id_map(wp["pos"], wp["uv"], wp["idx"]).save(os.path.join(pkg, "armor", "hood_id.png"))
    # (the mantle cut and the manifest are the body's and the package's: r2 writes them to --work only, unless
    #  --write-body 1; three solvers share the package)
    body_out = pkg if opt.get("write-body") == "1" else work
    cut = cut_mantle(src, body_out, HP, HFw)
    if body_out == pkg:
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
    json.dump({"numbers": res, "piece": info, "mantleCut": cut, "attach": attach}, open(os.path.join(work, "numbers.json"), "w"), indent=1)
    renders(work, "hood")
    log(f"done in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
