"""The Ford-Warden's wool garment (Warden 7): hood, capelet and long cape as ONE sewn-pattern cloth piece (armor/hood.glb).

Concept A: a deep heavy wool hood with a soft peak and a centre gusset, a short ragged circular-cut capelet to mid upper
arm, a long dark cape from under the capelet's back hem to the calves. Built the way a Marvelous Designer garment is:

  1. the arrangement: the hood's rings (a soft peak at the back of the crown), the capelet hanging straight off the
     posed shoulders with its folds laid in (no bell), the cape a panel behind with its gathers and vertical folds;
     a 1 cm voxel cloth grid, the face opening (warden_hood.OPENING, the face judge's spec) and the hem cut out;
  2. cut into flat panels along the seams: two hood sides and a centre gusset (brow to nape), the capelet's two
     halves (centre front and back seams), the cape; each panel flattened (minimum stretch) = its sewing pattern and
     its UV island (the texture's grain is the cloth's own);
  3. simulated with the flat panels as the rest shape (rest lengths AND rest angles: the cloth wants to lie flat, so
     it folds where the body makes it), the seams sewn (sewing springs between the split seam vertices): the cape
     first, pinned along its attach line; then the hood and capelet over it, the face opening pinned to the spec;
     the seams welded after;
  4. the hems torn; reduced to the game budget (the big folds kept in the geometry), the 1 cm drape baked into the
     normal map with a 2/2 twill on top; the fold crests baked (pointiness) for the worn lighter ridges;
  5. thickness (the inside the same wool, a touch darker), a rolled frayed rim round the whole face opening, the
     frayed fringe on the hems;
  6. skinned: crown and rim to Head, blending to neck_01 and spine_03 under the rim; the capelet's yoke to spine_03
     and the clavicles, its hem to capelet_<b|l|r>_0; the cape to chain bones cape_<col>_<i> (the springs);
  7. a corrective shape capelet_bend (the capelet's back and the cape's top simulated once with spine_03 pitched 80 deg
     forward, stored as the delta at the bind); lod1, a shadow mesh; armor/hood.glb, armor/hood_id.png, the fur
     mantle cut under it, the manifest's springs and correctives.

Run (Blender 4.5, a blender turn):
  blender -b --python-exit-code 1 -P tools/assets/warden_garment.py -- PKG_DIR --pre PRE_PKG [--work DIR]
      [--write-body 1] [--frames N] [--stage arrange|cape|drape|all]
  PRE_PKG: the package before any mantle cut (its index buffers restore the current body's uncut mantle).
"""
import bpy, bmesh, json, math, os, shutil, sys, time
import numpy as np
import mathutils
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import warden_hood as WH  # noqa: E402
from warden_head import Glb, b2g, g2b, select_only, smoothstep  # noqa: E402
from warden_hood import (X0, mk, verts, set_verts, apply_mods, import_body, armature, pose_arms, skin_mats,  # noqa: E402
                         posed_body, decimated, bake_lo, blur, vnoise1, vnoise2, body_posed_donors, corner_arrays,
                         enc, cut_mantle, setup_render, face_numbers, adjacency, push_clear, smooth_edge, fringe_map,
                         MAT_WOOL, MAT_INNER, MAT_FRINGE, load_body)

# ---- the garment (package frame, glTF: Y up, metres, front +Z) ----
VOX = 0.010                      # the sim's cloth grid
HEM_Y = 1.245                    # the capelet's straight hem before the tear (mid upper arm with the arms down)
NECK = (0.222, 1.503)            # the hood/capelet seam: the plane y + a z = c (lower at the throat, under the beard)
GUSSET = 0.080                   # the hood's centre gusset, brow to nape
CAPE_TOP, CAPE_HEM = 1.290, 0.360   # the cape's attach line (under the capelet's back hem) and its hem (mid calf)
CAPE_SPAN = (0.40, 0.84)         # the cape's arranged width at the top (gathered) and the hem
CAPE_FOLDS = 6                   # the cape's vertical folds across
CAPE_AMP = (0.014, 0.062)        # their depth (peak to peak) at the top (the gathers) and the hem
CAPE_CLEAR = (0.016, 0.036)      # off the body at the top and the hem (the calves: >= 3 cm at rest)
FLUTE_K, FLUTE_AMP = 13, 0.030   # the capelet's laid-in folds round the shoulders, their depth at the hem
NECK_K, NECK_AMP = 9, 0.011      # the hood's folds bunched at the neck
FRAMES = 70
YOKE_FRAMES, YOKE_HOLD, YOKE_Y = 20, 0.6, (1.33, 1.42)   # the capelet's first frames: its yoke held softly
BEND = 2.2                       # wool's bending stiffness (the hood and capelet hold some body)
CROWN_HOLD = 0.30                # the crown's soft goal to its arranged shape (a deep hood keeps its volume)
LO_TRIS = 6000                   # the outer surface's budget (x2 with the inside, + rim and fringe: ~15k)
LOD_TRIS, SHADOW_TRIS = 1500, 1000
TEX = 4096
WOOL = (0.13, 0.145, 0.19)       # sRGB (the shader pulls the hue to its wool class; the map carries light and dark)
ALB_GAIN = float(os.environ.get("GARMENT_GAIN", "2.3"))   # the albedo's level (r1 measured in the C02 s7 / C03 s1 frames)
PANELS = ("hood_l", "hood_r", "gusset", "cape_l", "cape_r", "cape")   # (cape_l/r: the capelet's halves)
CAPE_COLS, CAPE_LINKS = 4, 5
# (r3) the bind: the game's own idle (BossViews.PoseDump, Idle_Shield), not the glb's wide A. Every frame the game draws
# sits 40-50 deg off the A at the spine, neck and clavicles (the body's own skin stretches 1.7x at the throat and 2.7x
# at the shoulders from the A to any idle), so a garment bound at the A measured 1.4-2.2x stretch standing still. The
# drape is skinned into the idle, relaxed there by the cloth sim (rest lengths and angles the drape's), and bound there.
BIND_POSE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "warden_garment_pose.json")
RELAX_FRAMES = 45
C_G2B = np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1.0]])   # glTF -> Blender
PROFILE = [   # the hood's rings (warden_hood's, the crown lifted and set back into a soft peak)
    # (r4, the max judge: concept A's soft peak: the apex ~5 cm above r3's dome, narrowing to a soft point set back
    #  over the crown and tipping back; the brow's rings as r3's)
    (1.930, 0.000, -0.142, 0.000, 0.000),
    (1.918, 0.014, -0.136, 0.016, 0.012),
    (1.900, 0.030, -0.122, 0.038, 0.028),
    (1.876, 0.050, -0.100, 0.068, 0.050),
    (1.848, 0.074, -0.072, 0.106, 0.080),
    (1.816, 0.096, -0.044, 0.142, 0.106),
    (1.782, 0.114, -0.022, 0.168, 0.126),
    (1.745, 0.127, -0.008, 0.182, 0.137),
] + WH.PROFILE[6:]
PEAK_HOLD = (0.55, 1.84, 1.90)   # (r4) the peak's own soft goal (wool's felted point keeps its shape), from y to y
HEM_SPREAD = (0.95, 0.40, 0.80, 0.33)   # (r4) the cape's hem spread on the water: x widened by 1 + this, unfolded by
#                                         this (fold depth eased to its mean), from y 0.80 to the hem's 0.33
CORR_PITCH = (25, 65)            # (r4) capelet_bend's pitch range (deg; was 40-80: at C02 s7's bend it was half on)


def log(*a):
    print("[warden_garment]", *a, flush=True)


# ================= 0. the body =================
def restore_uncut(cur, pre, out):
    """The current body (its later vertex and atlas work) with the mantle's index buffers from before any cut."""
    os.makedirs(out, exist_ok=True)
    for f in ("id_generated.png", "manifest.json"):
        shutil.copy(os.path.join(cur, f), os.path.join(out, f))
    for fname in ("body.glb", "lod.glb"):
        g, q = Glb(os.path.join(cur, fname)), Glb(os.path.join(pre, fname))
        n = 0
        for m, mq in zip(g.j["meshes"], q.j["meshes"]):
            for p, pq in zip(m["primitives"], mq["primitives"]):
                if g.j["accessors"][p["attributes"]["POSITION"]]["count"] != q.j["accessors"][pq["attributes"]["POSITION"]]["count"]:
                    raise RuntimeError(f"{fname}: the pre-cut package's vertices differ")
                F, Fq = g.acc(p["indices"]), q.acc(pq["indices"])
                if len(Fq) != len(F):
                    p["indices"] = g.add_acc(Fq.astype(np.uint32), "SCALAR", target=34963)
                    n += (len(Fq) - len(F)) // 3
        g.save(os.path.join(out, fname))
        log(f"{fname}: {n} cut triangles restored")


def collider_obs(Vg, F):
    """The posed body as collision meshes: above the hips (thin) and below (thick: the cape rests 3 cm off the robe)."""
    C = Vg[F].mean(1)[:, 1]
    out = []
    for name, sel, th in (("col_hi", C > 0.95, 0.007), ("col_lo", C <= 1.0, 0.030)):
        Fs = F[sel]
        used = np.unique(Fs)
        rm = -np.ones(len(Vg), np.int64)
        rm[used] = np.arange(len(used))
        ob = mk(name, g2b(Vg[used]), rm[Fs])
        ob.hide_render = True
        ob.modifiers.new("collide", "COLLISION")
        ob.collision.thickness_outer = th
        ob.collision.thickness_inner = 0.01
        ob.collision.cloth_friction = 6.0
        ob.collision.damping = 0.5
        out.append(ob)
    return out


def envelope_col(Vg, F, y0=1.22, y1=1.55, n=144):
    """The body's radial outer envelope over the capelet's and the hood's neck heights as a collider (d5: the cloth
    fell into the crevasse between the fur mantle's collar and the neck, on his right deepest, and through under the
    arm): per height (1 cm) and angle (2.5 deg) the outermost body point round the vertical axis, a max over the
    neighbouring sectors, smoothed in height; a ring mesh, normals out. The mantle is cut under the garment after, so
    resting on the envelope reads as resting on the mantle."""
    P = np.concatenate([Vg, Vg[F].mean(1)])
    ys = np.arange(y0, y1 + 1e-6, 0.01)
    th = np.arange(n) / n * 2 * np.pi
    t = np.arctan2(P[:, 0] - X0, P[:, 2] + 0.02) % (2 * np.pi)
    r = np.hypot(P[:, 0] - X0, P[:, 2] + 0.02)
    k = (t / (2 * np.pi) * n).astype(int) % n
    R = np.zeros((len(ys), n))
    for i, y in enumerate(ys):
        m = np.abs(P[:, 1] - y) < 0.008
        np.maximum.at(R[i], k[m], r[m])
    R = np.maximum(np.maximum(R, np.roll(R, 1, 1)), np.roll(R, -1, 1))
    R = np.maximum(R, np.maximum(np.roll(R, 2, 1), np.roll(R, -2, 1)))
    R[1:-1] = np.maximum(R[1:-1], 0.5 * (R[:-2] + R[2:]))
    V = np.array([[X0 + R[i, j] * np.sin(th[j]), ys[i], -0.02 + R[i, j] * np.cos(th[j])] for i in range(len(ys)) for j in range(n)])
    Fq = []
    for i in range(len(ys) - 1):
        for j in range(n):
            a_, b_ = i * n + j, i * n + (j + 1) % n
            Fq.append((a_, a_ + n, b_ + n, b_))
    ob = mk("col_env", g2b(V), Fq)
    ob.data.update()
    # (normals out: flipped if the first face points in)
    ob.data.calc_loop_triangles()
    f0 = ob.data.polygons[0]
    c0 = b2g(np.array([f0.center[:]]))[0]
    n0 = b2g(np.array([f0.normal[:]]))[0]
    if np.dot(n0[[0, 2]], c0[[0, 2]] - np.array([X0, -0.02])) < 0:
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
        bm.to_mesh(ob.data)
        bm.free()
        ob.data.update()
    ob.hide_render = True
    ob.modifiers.new("collide", "COLLISION")
    ob.collision.thickness_outer = 0.006
    ob.collision.thickness_inner = 0.02
    ob.collision.cloth_friction = 6.0
    ob.collision.damping = 0.5
    log(f"envelope collider: {len(ys)} rings x {n}, radius {R.min():.3f}-{R.max():.3f}")
    return ob


# ================= 1. the arrangement =================
def back_line(Vg):
    """The body's back (glTF z) under the cape by height: the furthest back point at or above each height, over the
    cape's width (a cape falls straight from the most protruding point above)."""
    ys = np.arange(CAPE_HEM - 0.02, CAPE_TOP + 0.03, 0.01)
    zb = np.zeros(len(ys))
    for i, y in enumerate(ys):
        s = Vg[(np.abs(Vg[:, 1] - y) < 0.012) & (np.abs(Vg[:, 0] - X0) < 0.30)]
        zb[i] = s[:, 2].min() if len(s) else 0
    zc = np.minimum.accumulate(zb[::-1])[::-1]   # (from the top down: the furthest back above)
    return ys, zc


def cape_arrangement(Vg):
    ys, zc = back_line(Vg)
    L = CAPE_TOP - CAPE_HEM
    nt = int(round(L / VOX)) + 1
    W = CAPE_SPAN[1]
    ns = int(round(W * 1.15 / VOX)) + 1
    V, F = [], []
    for it in range(nt):
        t = it / (nt - 1)
        y = CAPE_TOP - t * L
        w = CAPE_SPAN[0] + (CAPE_SPAN[1] - CAPE_SPAN[0]) * t ** 0.8
        amp = CAPE_AMP[0] + (CAPE_AMP[1] - CAPE_AMP[0]) * t ** 0.9
        clr = CAPE_CLEAR[0] + (CAPE_CLEAR[1] - CAPE_CLEAR[0]) * smoothstep(0.0, 0.8, t)
        z0 = np.interp(y, ys, zc) - clr
        for js in range(ns):
            s = js / (ns - 1) * 2 - 1
            ph = CAPE_FOLDS * np.pi * s + 0.6 * np.sin(2.1 * s + 0.4)
            x = X0 + s * w / 2
            z = z0 - amp * 0.5 * (1 + np.sin(ph)) + 0.55 * (s * w / 2) ** 2   # (the sides wrap a little forward)
            V.append((x, y, z))
    for it in range(nt - 1):
        for js in range(ns - 1):
            a = it * ns + js
            F.append((a, a + 1, a + ns + 1, a + ns))
    ob = mk("cape_arr", g2b(np.array(V)), F)
    log(f"cape arranged: {len(V)} verts, top {CAPE_TOP}, hem {CAPE_HEM}, width {CAPE_SPAN}")
    return ob


def ring_r_garment(old):
    def f(y, th):
        r = old(y, th)
        th2 = th + 0.16 * np.sin(3 * th + 1.1)
        cap = FLUTE_AMP * smoothstep(1.50, HEM_Y, y)
        neck = NECK_AMP * smoothstep(1.47, 1.52, y) * smoothstep(1.64, 1.55, y)
        return r + cap * 0.5 * (1 + np.sin(FLUTE_K * th2)) + neck * 0.5 * (1 + np.sin(NECK_K * th2 + 0.7))
    return f


def hood_arrangement(Vg_tent):
    WH.PROFILE[:] = PROFILE
    WH.HEM_Y = HEM_Y
    WH.VOXEL = VOX
    WH.tent(Vg_tent)
    WH.ring_r = ring_r_garment(WH.ring_r)
    sh = WH.shell()
    smooth_edge(sh)
    return sh


# ================= 2. the panels =================
def label_faces(bm):
    lab = bm.faces.layers.int.new("panel")
    for f in bm.faces:
        c = b2g(np.array([f.calc_center_median()]))[0]
        if c[1] + NECK[0] * c[2] - NECK[1] < 0:
            k = 3 if c[0] > X0 else 4
        elif abs(c[0] - X0) < GUSSET / 2 and (c[1] > 1.62 or c[2] < 0.0):
            k = 2
        else:
            k = 0 if c[0] > X0 else 1
        f[lab] = k
    return lab


def panels(sh, cape):
    """The hood/capelet arrangement cut along its seams, the cape joined: one object of separate panels; the seam
    pairs (vertex index tuples, coincident) returned for sewing."""
    bm = bmesh.new()
    bm.from_mesh(sh.data)
    for co, no in ((g2b(np.array([[X0 + GUSSET / 2, 0, 0]]))[0], (1, 0, 0)), (g2b(np.array([[X0 - GUSSET / 2, 0, 0]]))[0], (1, 0, 0)),
                   (g2b(np.array([[X0, 0, 0]]))[0], (1, 0, 0)), (g2b(np.array([[X0, NECK[1], 0]]))[0], tuple(g2b(np.array([[0, 1.0, NECK[0]]]))[0]))):
        geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
        bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-5, plane_co=Vector(co), plane_no=Vector(no))
    # (the cuts' slivers merged into their neighbours: a 1 mm edge is a stiff spring and a pattern's noise)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0035)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=0.001)
    lab = label_faces(bm)
    seams = [e for e in bm.edges if len(e.link_faces) == 2 and e.link_faces[0][lab] != e.link_faces[1][lab]]
    bmesh.ops.split_edges(bm, edges=seams)
    # the cape, its own panel
    bc = bmesh.new()
    bc.from_mesh(cape.data)
    off = len(bm.verts)
    vm = [bm.verts.new(v.co) for v in bc.verts]
    for f in bc.faces:
        nf = bm.faces.new([vm[v.index] for v in f.verts])
        nf[lab] = 5
    bc.free()
    bm.to_mesh(sh.data)
    bm.free()
    bpy.data.objects.remove(cape)
    # the seam pairs: coincident vertices of different panels
    V = verts(sh)
    t = KDTree(len(V))
    for i, v in enumerate(V):
        t.insert(v, i)
    t.balance()
    bnd = set()
    bm = bmesh.new()
    bm.from_mesh(sh.data)
    bnd = {v.index for v in bm.verts if v.is_boundary}
    bm.free()
    pairs = set()
    for i in bnd:
        for co, j, d in t.find_range(V[i], 1e-5):
            if j != i:
                pairs.add((min(i, j), max(i, j)))
    sh.name = "garment"
    log(f"panels: {len(sh.data.polygons)} faces, {len(pairs)} seam pairs")
    return sorted(pairs)


def flatten(ob):
    """Each panel unwrapped (minimum stretch), scaled to its true area, packed: the UVs; their metres = the rest shape
    (the flat pattern). Returns UV units per metre."""
    select_only(ob)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    try:
        bpy.ops.uv.unwrap(method="MINIMUM_STRETCH", margin=0.0)
        m = "minimum stretch"
    except Exception as e:
        log("minimum stretch unwrap failed:", e)
        bpy.ops.uv.unwrap(method="ANGLE_BASED", margin=0.0)
        m = "angle based"
    bpy.ops.uv.select_all(action="SELECT")
    bpy.ops.uv.average_islands_scale()
    bpy.ops.uv.pack_islands(rotate=True, margin=0.004)
    bpy.ops.object.mode_set(mode="OBJECT")
    me = ob.data
    uv = WH.loop_uv(ob)
    me.calc_loop_triangles()
    a3 = sum(t.area for t in me.loop_triangles)
    tl = np.array([t.loops[:] for t in me.loop_triangles])
    q = uv[tl]
    d1, d2 = q[:, 1] - q[:, 0], q[:, 2] - q[:, 0]
    a2 = 0.5 * np.abs(d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]).sum()
    s = math.sqrt(a2 / a3)
    # the rest shape: each vertex's UV in metres (a vertex sits in one island: the seams were split)
    lv = np.zeros(len(me.loops), np.int64)
    me.loops.foreach_get("vertex_index", lv)
    flat = np.zeros((len(me.vertices), 3))
    flat[lv, 0] = uv[:, 0] / s
    flat[lv, 1] = uv[:, 1] / s
    # (the panel's flat length against its arrangement, edge by edge: the pattern's strain)
    E = np.array([e.vertices[:] for e in me.edges])
    V = verts(ob)
    L3 = np.linalg.norm(V[E[:, 0]] - V[E[:, 1]], axis=1)
    # (each panel to its true size: the median edge as long flat as arranged; the packer's scale is not trusted)
    lab = panel_of_verts(ob)
    per = {}
    for k in range(len(PANELS)):
        sel = (lab[E[:, 0]] == k) & (L3 > 0.003)
        if not sel.any():
            continue
        rk = np.median(np.linalg.norm(flat[E[sel, 0]] - flat[E[sel, 1]], axis=1) / L3[sel])
        vk = lab == k
        c = flat[vk].mean(0)
        flat[vk] = c + (flat[vk] - c) / rk
        per[PANELS[k]] = round(float(rk), 3)
    log("flat panels rescaled by", per)
    r = (np.linalg.norm(flat[E[:, 0]] - flat[E[:, 1]], axis=1) / (L3 + 1e-9))[L3 > 0.003]
    log(f"flattened ({m}): {s:.4f} UV a metre ({1 / s / TEX * 1000:.2f} mm a texel at {TEX}); pattern/arrangement edge p1 {np.percentile(r, 1):.3f} p50 {np.median(r):.3f} p99 {np.percentile(r, 99):.3f}")
    ob.shape_key_add(name="Basis")
    k = ob.shape_key_add(name="flat")
    k.data.foreach_set("co", flat.ravel())
    return s


def panel_of_verts(ob):
    lab = np.full(len(ob.data.vertices), -1)
    a = ob.data.attributes["panel"].data
    for p in ob.data.polygons:
        for v in p.vertices:
            lab[v] = max(lab[v], a[p.index].value)
    return lab


# ================= 3. the simulation =================
def cloth(ob, pins, frames, bend, cols, sew=False, log_every=10):
    sc = bpy.context.scene
    g = ob.vertex_groups.get("pin") or ob.vertex_groups.new(name="pin")
    g.remove(list(range(len(ob.data.vertices))))
    for i in np.nonzero(pins > 0.001)[0]:
        g.add([int(i)], float(pins[i]), "REPLACE")
    m = ob.modifiers.new("cloth", "CLOTH")
    cs = m.settings
    cs.quality = 10
    cs.mass = 0.40
    cs.air_damping = 2.0
    cs.tension_stiffness = cs.compression_stiffness = 35
    cs.shear_stiffness = 12
    cs.bending_stiffness = bend
    cs.tension_damping = cs.compression_damping = 8
    cs.bending_damping = 0.8
    cs.vertex_group_mass = "pin"
    cs.pin_stiffness = 3.0
    if ob.data.shape_keys and "flat" in ob.data.shape_keys.key_blocks:
        cs.rest_shape_key = ob.data.shape_keys.key_blocks["flat"]
    cs.use_sewing_springs = sew
    cs.sewing_force_max = 0.0
    cc = m.collision_settings
    cc.collision_quality = 4
    cc.distance_min = 0.004
    cc.use_self_collision = False
    m.point_cache.frame_start = 1
    m.point_cache.frame_end = frames
    sc.frame_start, sc.frame_end = 1, frames
    coll = bpy.data.collections.new("colliders_" + ob.name)
    for o in cols:
        coll.objects.link(o)
    cc.collection = coll
    t0 = time.time()
    for f in range(1, frames + 1):
        sc.frame_set(f)
        if f % log_every == 0:
            e = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
            P = np.array([v.co[:] for v in e.data.vertices])
            log(f"  frame {f}/{frames} ({time.time() - t0:.0f} s): box {np.round(b2g(P).min(0), 2).tolist()} {np.round(b2g(P).max(0), 2).tolist()}")
    e = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    P = np.array([v.co[:] for v in e.data.vertices])
    sc.frame_set(1)
    ob.modifiers.remove(m)
    log(f"simulated {frames} frames in {time.time() - t0:.0f} s")
    return P


def opening_pins(ob, lab, Ob):
    """The face opening's points (the arrangement's opening boundary, before the split) -> pin weights: 1 on it, eased
    to 0 over 1.5-4.5 cm; the crown held softly (CROWN_HOLD) above the brow."""
    V = b2g(verts(ob))
    t = KDTree(len(Ob))
    for i, p in enumerate(Ob):
        t.insert(p, i)
    t.balance()
    d = np.array([t.find(p)[2] for p in V])
    w = 1 - smoothstep(0.015, 0.045, d)
    w = np.maximum(w, CROWN_HOLD * smoothstep(1.62, 1.72, V[:, 1]))
    w = np.maximum(w, PEAK_HOLD[0] * smoothstep(PEAK_HOLD[1], PEAK_HOLD[2], V[:, 1]))
    w[lab >= 3] = 0
    return w


def diag(ob, lab, cols, tag):
    """Per panel: points inside the body / within 5 mm of it, within 4 mm of the cape collider; edge strain vs the flat."""
    V = verts(ob)
    if ob.data.shape_keys and "Basis" in ob.data.shape_keys.key_blocks:
        V = np.zeros(len(ob.data.vertices) * 3)
        ob.data.shape_keys.key_blocks["Basis"].data.foreach_get("co", V)
        V = V.reshape(-1, 3)
    bvh = WH.eval_mesh_bvh([cols[0]])[0]
    bvc = WH.eval_mesh_bvh([cols[1]])[0] if len(cols) > 1 else None
    E = np.array([e.vertices[:] for e in ob.data.edges])
    fl = None
    if ob.data.shape_keys and "flat" in ob.data.shape_keys.key_blocks:
        fl = np.zeros(len(ob.data.vertices) * 3)
        ob.data.shape_keys.key_blocks["flat"].data.foreach_get("co", fl)
        fl = fl.reshape(-1, 3)
    out = {}
    for k in range(5):
        idx = np.nonzero(lab == k)[0]
        ins = near = nc = 0
        for i in idx:
            h = bvh.find_nearest(Vector(V[i]), 0.05)
            if h[0] is not None:
                d = np.dot(V[i] - np.array(h[0]), np.array(h[1]))
                ins += d < 0
                near += 0 <= d < 0.005
            if bvc is not None:
                h = bvc.find_nearest(Vector(V[i]), 0.004)
                nc += h[0] is not None
        r = {"in": int(ins), "near5mm": int(near), "nearCape": int(nc)}
        if fl is not None:
            sel = (lab[E[:, 0]] == k) & (lab[E[:, 1]] == k)
            L3 = np.linalg.norm(V[E[sel, 0]] - V[E[sel, 1]], axis=1)
            Lf = np.linalg.norm(fl[E[sel, 0]] - fl[E[sel, 1]], axis=1)
            q = L3 / (Lf + 1e-9)
            r["strain"] = [round(float(np.percentile(q, x)), 3) for x in (1, 50, 99)]
        if k != 2:
            dep = radial_depth(V, lab, bvh, (lab == k) & (b2g(V)[:, 1] < 1.60))[idx]
            dep = dep[~np.isnan(dep)]
            r["radial_in"] = int((dep < 0).sum())
            r["radial_lt5mm"] = int((dep < 0.005).sum())
        if len(idx):
            g = b2g(V[idx])
            r["x"] = [round(float(g[:, 0].min()), 3), round(float(g[:, 0].max()), 3)]
        out[PANELS[k]] = r
    log(f"diag {tag}:", json.dumps(out))


def radial_depth(V, lab, bvh, sel):
    """Per selected point (Blender coords): how far it sits outside the body's OUTERMOST surface along the horizontal
    ray from the body's axis through it (negative = inside or under it: trapped). A ray cast from outside inward, so
    inner surfaces (the mantle's underside, the torso under the arm) don't count."""
    out = np.full(len(V), np.nan)
    G = b2g(V)
    for i in np.nonzero(sel)[0]:
        g = G[i]
        d = np.array([g[0] - X0, 0.0, g[2] + 0.02])
        r = np.linalg.norm(d)
        if r < 1e-4:
            continue
        d /= r
        o = g2b(np.array([[X0, g[1], -0.02] + d * 0.8]))[0]
        dirb = g2b(-d[None])[0]
        h = bvh.ray_cast(Vector(o), Vector(dirb), 0.8)
        if h[0] is None:
            out[i] = 1.0
            continue
        rh = 0.8 - h[3]
        out[i] = r - rh
    return out


def radial_push(V, sel, bvh, adj, gap, spread=10):
    """Selected points (Blender coords) under the body's outermost surface or nearer than gap (radial_depth) moved
    out radially; the move diffused to the selected neighbours (decaying 0.9 a ring: the folds kept, no smoothing of
    positions, no spikes from a nearest normal in the beard). Returns the new points and the seed count."""
    dep = radial_depth(V, None, bvh, sel)
    G = b2g(V)
    seed = sel & (dep < gap)
    D = np.zeros_like(G)
    for i in np.nonzero(seed)[0]:
        d = np.array([G[i, 0] - X0, 0.0, G[i, 2] + 0.02])
        D[i] = d / np.linalg.norm(d) * (gap - dep[i])
    for _ in range(spread):
        Dn = np.array([D[a].mean(0) if len(a) else D[i] for i, a in enumerate(adj)])
        mag, magn = np.linalg.norm(D, axis=1), np.linalg.norm(Dn, axis=1)
        D = np.where((sel & ~seed & (magn * 0.9 > mag))[:, None], Dn * 0.9, D)
    return g2b(G + D), int(seed.sum()), float(np.linalg.norm(D, axis=1).max())


def clear_capelet(ob, lab, cols, gap=0.010):
    """The capelet's points pushed radially clear of the posed body (radial_push); the Basis key set."""
    kb = ob.data.shape_keys.key_blocks["Basis"]
    V = np.zeros(len(ob.data.vertices) * 3)
    kb.data.foreach_get("co", V)
    V = V.reshape(-1, 3)
    bvh = WH.eval_mesh_bvh([cols[0]])[0]
    V, n, mx = radial_push(V, (lab == 3) | (lab == 4), bvh, adjacency(ob), gap)
    kb.data.foreach_set("co", V.ravel())
    set_verts(ob, V)
    log(f"capelet cleared radially: {n} seeds, max push {mx * 1000:.1f} mm")


def clear_arrangement(sh, col, gap=0.010):
    """The hood/capelet arrangement below the face opening pushed radially clear of the body (replaces warden_hood's
    push_clear here: its nearest-normal push and global smoothing made the throat's shards and the chest's pinches)."""
    bvh = WH.eval_mesh_bvh([col])[0]
    V = verts(sh)
    sel = b2g(V)[:, 1] < 1.530
    V, n, mx = radial_push(V, sel, bvh, adjacency(sh), gap, spread=14)
    set_verts(sh, V)
    log(f"arrangement cleared radially: {n} seeds, max push {mx * 1000:.1f} mm")


def weld(ob, pairs):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    # (chains: a vertex sewn to two others, at the gusset's ends)
    root = {}

    def find(i):
        while root.get(i, i) != i:
            i = root[i]
        return i
    for a, b in pairs:
        ra, rb = find(a), find(b)
        if ra != rb:
            root[max(ra, rb)] = min(ra, rb)
    groups = {}
    for i in set(root) | set(root.values()):
        groups.setdefault(find(i), []).append(i)
    gap = []
    tm = {}
    for r, g in groups.items():
        P = np.array([bm.verts[i].co[:] for i in g])
        gap.append(np.linalg.norm(P - P.mean(0), axis=1).max())
        bm.verts[r].co = Vector(P.mean(0))
        for i in g:
            if i != r:
                tm[bm.verts[i]] = bm.verts[r]
    bmesh.ops.weld_verts(bm, targetmap=tm)
    bmesh.ops.delete(bm, geom=[e for e in bm.edges if not e.link_faces], context="EDGES")
    bm.to_mesh(ob.data)
    bm.free()
    log(f"seams welded: {len(groups)} points, the sewn gap before: max {max(gap) * 1000:.1f} mm, p95 {np.percentile(gap, 95) * 1000:.1f} mm")


def drop_specks(ob, min_faces=40):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    seen, dead = set(), []
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
        if len(part) < min_faces:
            dead += part
    if dead:
        bmesh.ops.delete(bm, geom=dead, context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.to_mesh(ob.data)
    bm.free()


def cape_clear(ob, Vb_body, Fb, gap=0.034, ylim=0.85, iters=3):
    """The cape's lower part held >= gap off the body at rest (behind the calves and the robe: the judge's 3 cm): points
    nearer moved straight away from their nearest body point, the move diffused along the cape (decaying)."""
    bvh = BVHTree.FromPolygons([tuple(v) for v in Vb_body], [tuple(f) for f in Fb])
    lab = panel_of_verts(ob)
    adj = adjacency(ob)
    V = verts(ob)
    sel = (lab == 5) & (b2g(V)[:, 1] < ylim)
    nseed = 0
    for _ in range(iters):
        D = np.zeros_like(V)
        seed = np.zeros(len(V), bool)
        for i in np.nonzero(sel)[0]:
            h = bvh.find_nearest(Vector(V[i]), gap)
            if h[0] is not None and h[3] < gap:
                d = V[i] - np.array(h[0])
                n = np.linalg.norm(d)
                d = d / n if n > 1e-6 else np.array(h[1])
                D[i] = d * (gap - h[3])
                seed[i] = True
        nseed = max(nseed, int(seed.sum()))
        if not seed.any():
            break
        for _ in range(8):
            Dn = np.array([D[a].mean(0) if len(a) else D[i] for i, a in enumerate(adj)])
            mag, magn = np.linalg.norm(D, axis=1), np.linalg.norm(Dn, axis=1)
            D = np.where(((lab == 5) & ~seed & (magn * 0.9 > mag))[:, None], Dn * 0.9, D)
        V = V + D
    set_verts(ob, V)
    log(f"cape held {gap * 100:.1f} cm off the body below {ylim} m: {nseed} points moved")


# ================= 4. tear, budget, maps =================
def tear(ob, seed=7):
    """The capelet's hem and the cape's hem torn: faces within a ragged depth of the hem go (a wavering 1-3 cm line
    and V tears 4-10 cm deep; the cape's a little deeper)."""
    me = ob.data
    lab = np.array([a.value for a in me.attributes["panel"].data])
    C = b2g(np.array([p.center[:] for p in me.polygons]))
    bm = bmesh.new()
    bm.from_mesh(me)
    hemv = {3: [], 5: []}
    for v in bm.verts:
        if not v.is_boundary:
            continue
        ks = {lab[f.index] for f in v.link_faces}
        p = b2g(np.array([v.co[:]]))[0]
        if ks & {3, 4} and p[1] < NECK[1] - 0.12:
            hemv[3].append(p)
        if 5 in ks and p[1] < CAPE_HEM + 0.10:
            hemv[5].append(p)
    gone = np.zeros(len(C), bool)
    for k, sel, scale, deep in ((3, (lab == 3) | (lab == 4), 0.35, 1.0), (5, lab == 5, 1.0, 1.3)):
        H = np.array(hemv[k])
        t = KDTree(len(H))
        for i, p in enumerate(H):
            t.insert(p, i)
        t.balance()
        idx = np.nonzero(sel)[0]
        d = np.array([t.find(C[i])[2] for i in idx])
        # one coordinate along the hem: the angle round the body (capelet) or across (cape), in metres
        u = np.arctan2(C[idx, 0] - X0, C[idx, 2]) * scale if k == 3 else C[idx, 0]
        depth = 0.008 + 0.022 * vnoise1(u + 5, 0.06, seed + k) ** 1.5 + 0.008 * vnoise1(u + 5, 0.017, seed + k + 1)
        if k == 3:   # (r3, concept A: shorter at the front, the back left long)
            depth = depth + 0.050 * np.clip(np.cos(u / scale), 0, 1) ** 2
        rng = np.random.default_rng(seed + k)
        for c in u.min() + (u.max() - u.min()) * np.sort(rng.random(13 if k == 3 else 7)):
            w, dp = rng.uniform(0.025, 0.055), rng.uniform(0.05, 0.13 if k == 3 else 0.10) * deep
            depth = np.maximum(depth, dp * np.clip(1 - np.abs(u - c) / (w / 2), 0, None) ** 1.3)
        gone[idx[d < depth * deep]] = True
    bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.faces[i] for i in np.nonzero(gone)[0]], context="FACES")
    bm.to_mesh(me)
    bm.free()
    drop_specks(ob)
    log(f"hems torn: {int(gone.sum())} faces")


def bake_crest(hi, lo, size):
    """The drape's fold crests (Cycles pointiness on the fine mesh) onto the game mesh's UVs."""
    sc = bpy.context.scene
    mat = bpy.data.materials.new("crest")
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    em = nt.nodes.new("ShaderNodeEmission")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(geo.outputs["Pointiness"], em.inputs["Color"])
    nt.links.new(em.outputs[0], out.inputs[0])
    old = list(hi.data.materials)
    hi.data.materials.clear()
    hi.data.materials.append(mat)
    img = bpy.data.images.new("crest", size, size, alpha=False, float_buffer=True)
    img.colorspace_settings.name = "Non-Color"
    tmat = lo.data.materials[0]
    tn = tmat.node_tree.nodes.new("ShaderNodeTexImage")
    tn.image = img
    tmat.node_tree.nodes.active = tn
    sc.cycles.samples = 4
    sc.render.bake.use_selected_to_active = True
    select_only(hi, lo)
    bpy.ops.object.bake(type="EMIT")
    a = np.array(img.pixels[:]).reshape(size, size, 4)[::-1, :, 0].copy()
    hi.data.materials.clear()
    for m in old:
        hi.data.materials.append(m)
    log(f"baked the crests at {size}: {np.percentile(a, 5):.3f}-{np.percentile(a, 95):.3f}")
    return a


def rasterize(vals, uv, idx, size):
    """A per-vertex value into the UV atlas (glTF uv, v down = image rows), grown into the gutters."""
    from scipy import ndimage
    H = np.full((size, size), np.nan, np.float32)
    for tri in idx.reshape(-1, 3):
        q = uv[tri] * size - 0.5
        y = vals[tri]
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
    return H[near[0], near[1]], ~hole


def wool_maps(bk, crest, hgt, s_uv, size):
    """Albedo, roughness and normal in the pattern UVs: dark slate wool, felted mottling and fuzz, the fold crests worn
    lighter, darker toward the hems (by the bind height), the drape's AO in the valleys; a 2/2 twill normal on top of
    the baked drape (UDN), the warp along the island's v."""
    m_px = 1.0 / s_uv / size
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    um, vm = xx * m_px, yy * m_px
    H = np.asarray(Image.fromarray(hgt.astype(np.float32)).resize((size, size), Image.BILINEAR), np.float32)
    wander = (vnoise2((size, size), size // 24, 3) - 0.5) * 0.10
    wet = np.clip(smoothstep(1.42, 1.22, H + wander) * 0.6 + smoothstep(1.05, 0.40, H + wander) * 0.4, 0, 1)
    mott = vnoise2((size, size), size // 40, 5) * 0.6 + vnoise2((size, size), size // 140, 6) * 0.4
    mott8 = (vnoise2((size, size), size // 60, 12) * 0.65 + vnoise2((size, size), size // 220, 13) * 0.35 - 0.5) * 2.0
    fuzz = blur(np.random.default_rng(9).random((size, size)).astype(np.float32), 0.7)
    up = lambda a: np.asarray(Image.fromarray(a.astype(np.float32)).resize((size, size), Image.BILINEAR), np.float32)
    ao = blur(np.clip(up(bk["ao"]), 0, 1), 1.2)
    cr = blur(up(crest), 2.0)
    isl = cr > 0.2   # (the islands: the gutters bake 0)
    c0 = np.median(cr[isl]) if isl.any() else np.median(cr)
    ridge = smoothstep(c0 + 0.015, c0 + 0.070, cr) * isl
    lin = lambda c: np.where(np.asarray(c) <= 0.04045, np.asarray(c) / 12.92, ((np.asarray(c) + 0.055) / 1.055) ** 2.4)
    base = lin(np.array(WOOL))
    k = (0.86 + 0.28 * mott + 0.10 * (fuzz - 0.5)) * (1 - 0.22 * wet) * (0.45 + 0.55 * ao) * (1 + 0.55 * ridge * (1 - 0.6 * wet)) * ALB_GAIN
    col = base[None, None, :] * k[..., None]
    col = col * (1 + wet[..., None] * np.array([-0.06, 0.04, -0.02]) * (mott[..., None] > 0.45))
    srgb = np.where(col <= 0.0031308, col * 12.92, 1.055 * np.power(np.clip(col, 0, None), 1 / 2.4) - 0.055)
    srgb = srgb + (mott8 * 8.0 / 255.0)[..., None]   # (r4: the felted mottling, +-8/255 in the albedo)
    albedo = Image.fromarray((np.clip(srgb, 0, 1) * 255 + 0.5).astype(np.uint8))
    log(f"wool albedo: linear luminance mean {float((col @ np.array([0.2126, 0.7152, 0.0722])).mean()):.4f}; ridges {float((ridge > 0.5).mean()) * 100:.0f}% of texels")
    rough = np.clip(0.93 - 0.03 * wet + 0.05 * (mott - 0.5) + 0.04 * (fuzz - 0.5) + 0.06 * ridge, 0.3, 1.0)
    mr = np.zeros((size, size, 3), np.uint8)
    mr[..., 1] = (rough * 255 + 0.5).astype(np.uint8)
    mr_img = Image.fromarray(mr).resize((size // 2, size // 2), Image.LANCZOS)
    P = 0.0024   # (r4: a coarse 2/2 twill, 5.5 texels a thread at 4096: r3's 1.1 mm aliased away by the close-up)
    i, j = np.floor(um / P), np.floor(vm / P)
    fu, fv = um / P - i, vm / P - j
    upw = ((i + j) % 4) < 2
    h = np.where(upw, np.sin(np.pi * fu) ** 0.7, np.sin(np.pi * fv) ** 0.7) * 0.6 + 0.4 * blur(fuzz, 1.5)
    h = blur(h.astype(np.float32), 0.6) * (1 - 0.5 * wet)
    gy, gx = np.gradient(h)
    nd = np.stack([-gx * 2.6, gy * 2.6], -1)
    nb = bk["normal"] * 2 - 1
    n = np.stack([nb[..., 0] + nd[..., 0], nb[..., 1] + nd[..., 1], nb[..., 2]], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-8
    nimg = Image.fromarray((np.clip(n * 0.5 + 0.5, 0, 1) * 255 + 0.5).astype(np.uint8))
    log(f"wool maps: {m_px * 1000:.2f} mm a texel, twill pitch {P * 1000:.1f} mm")
    return {"color": albedo, "mr": mr_img, "normal": nimg}


# ================= 6. skinning =================
def chain_bones(Vg, lab, names):
    """The cape's chains (CAPE_COLS x CAPE_LINKS, along its drape at the bind) and the capelet's hem bones: name,
    parent, head, tail (glTF, bind), radius."""
    cv = Vg[lab == 5]
    xs = np.linspace(np.percentile(cv[:, 0], 8), np.percentile(cv[:, 0], 92), CAPE_COLS)
    ys = np.linspace(CAPE_TOP - 0.01, CAPE_HEM + 0.02, CAPE_LINKS + 1)
    out = []
    for c, x in enumerate(xs):
        pts = []
        for y in ys:
            s = cv[(np.abs(cv[:, 0] - x) < 0.06) & (np.abs(cv[:, 1] - y) < 0.03)]
            s = s if len(s) else cv[np.argsort(np.abs(cv[:, 1] - y) + np.abs(cv[:, 0] - x))[:20]]
            p = np.array([x, y, np.median(s[:, 2]) + 0.006])
            pts.append(p)
        for i in range(CAPE_LINKS):
            out.append(dict(bone=f"cape_{c}_{i}", parent="spine_03" if i == 0 else f"cape_{c}_{i - 1}",
                            head=pts[i].round(4).tolist(), tail=pts[i + 1].round(4).tolist(), radius=0.045 if i < 2 else 0.06))
    # the capelet's hem: its back and its two sides
    capv = Vg[(lab == 3) | (lab == 4)]
    for key, par, sel in (("b", "spine_03", capv[:, 2] < -0.10), ("l", "clavicle_l", capv[:, 0] > X0 + 0.20), ("r", "clavicle_r", capv[:, 0] < X0 - 0.20)):
        s = capv[sel]
        lo_ = s[s[:, 1] < np.percentile(s[:, 1], 15)].mean(0)
        hi_ = s[(s[:, 1] > 1.36) & (s[:, 1] < 1.42)].mean(0) if ((s[:, 1] > 1.36) & (s[:, 1] < 1.42)).any() else lo_ + np.array([0, 0.12, 0])
        out.append(dict(bone=f"capelet_{key}_0", parent=par, head=hi_.round(4).tolist(), tail=lo_.round(4).tolist(), radius=0.05))
    return out


def smooth_along(A, adj, fixed, iters, a=0.5):
    """Weights eased along the cloth (vectorised neighbour means), the fixed rows held."""
    deg = np.array([len(x) for x in adj])
    K = max(int(deg.max()), 1)
    nbr = np.full((len(adj), K), -1, np.int64)
    for i, x in enumerate(adj):
        nbr[i, :len(x)] = x
    m = (nbr >= 0)[..., None]
    nbr = np.where(nbr >= 0, nbr, 0)
    for _ in range(iters):
        S = (A[nbr] * m).sum(1) / np.maximum(deg, 1)[:, None]
        A = np.where(fixed[:, None] | (deg == 0)[:, None], A, (1 - a) * A + a * S)
    return A


def garment_weights(Vg, lab, adj, donors, names, chains, open_pts):
    """Per vertex: (joint indices into names + chain bones, weights). The crown and rim to Head; under the rim to
    neck_01 then spine_03; the capelet's yoke to spine_03 and the clavicles (a share of the upper arm at its outer
    fall), its hem to its hem bones; the cape to its chains."""
    allnames = list(names) + [c["bone"] for c in chains]
    nb = len(allnames)
    ix = {n: i for i, n in enumerate(allnames)}
    A = np.zeros((len(Vg), nb))
    y = Vg[:, 1]
    u = np.abs(Vg[:, 0] - X0)
    left = Vg[:, 0] > X0
    lr = lambda a, b: np.where(left, ix[a], ix[b])
    rows = np.arange(len(Vg))
    t = KDTree(len(open_pts))
    for i, p in enumerate(open_pts):
        t.insert(p, i)
    t.balance()
    dop = np.array([t.find(p)[2] for p in Vg])
    hood = lab <= 2
    if donors is not None:   # (r3: donors = the body's weights near each vertex, dense over names)
        return body_garment_weights(Vg, lab, adj, donors, names, chains, A, ix, allnames, dop)
    # hood: Head over the rim (within 3 cm of the opening) and the crown, easing to neck_01 and spine_03 below
    # (r2: wider blends, the head's turn spread over the hood's lower half: r1's 4 cm bands stretched 2-3x at the throat)
    wh = np.maximum(1 - smoothstep(0.02, 0.10, dop), smoothstep(1.50, 1.65, y))
    wn = (1 - wh) * smoothstep(1.42, 1.53, y + 0.2 * np.clip(Vg[:, 2], 0, None))
    ws = 1 - wh - wn
    A[hood, ix["Head"]] += wh[hood]
    A[hood, ix["neck_01"]] += wn[hood]
    A[hood, ix["spine_03"]] += ws[hood]
    # capelet: the yoke
    cap = (lab == 3) | (lab == 4)
    arm = 0.30 * smoothstep(0.20, 0.34, u) * smoothstep(1.46, 1.34, y)
    clv = (1 - arm) * 0.55 * smoothstep(0.04, 0.17, u)
    nck = (1 - arm - clv) * 0.35 * smoothstep(1.47, 1.52, y) * (1 - smoothstep(0.05, 0.10, u))
    tor = 1 - arm - clv - nck
    for w, j in ((arm, lr("upperarm_l", "upperarm_r")), (clv, lr("clavicle_l", "clavicle_r")), (nck, np.full(len(Vg), ix["neck_01"])), (tor, np.full(len(Vg), ix["spine_03"]))):
        np.add.at(A, (rows[cap], j[cap]), w[cap])
    # the capelet's hem bones: the lower capelet by sector (back, left, right), eased in toward the hem
    hem = smoothstep(1.40, 1.27, y) * cap
    ang = np.arctan2(Vg[:, 0] - X0, Vg[:, 2])   # 0 front, +pi/2 left, pi back
    sec = {"b": np.cos(np.clip(np.abs(np.abs(ang) - np.pi), 0, np.pi / 2)) ** 2 * (np.abs(ang) > np.pi / 2),
           "l": np.clip(np.sin(ang), 0, 1) ** 2, "r": np.clip(-np.sin(ang), 0, 1) ** 2}
    tot = sum(sec.values()) + 1e-9
    for key, s in sec.items():
        w = hem * 0.85 * s / tot * (1.0 if key == "b" else (Vg[:, 2] < 0.12))
        A[:, :len(names)] *= (1 - w)[:, None]
        A[:, ix[f"capelet_{key}_0"]] += w
    # cape: along each chain (linear between links), across the columns
    cape = lab == 5
    cols = sorted({int(c["bone"].split("_")[1]) for c in chains if c["bone"].startswith("cape_")})
    cx = np.array([np.mean([c["head"][0] for c in chains if c["bone"].startswith(f"cape_{k}_")]) for k in cols])
    Lk = (CAPE_TOP - CAPE_HEM) / CAPE_LINKS
    f = np.clip((CAPE_TOP - y) / Lk, 0, CAPE_LINKS - 1e-3)
    i0 = np.floor(f).astype(int)
    fr = f - i0
    i1 = np.minimum(i0 + 1, CAPE_LINKS - 1)
    fr = np.where(i0 == CAPE_LINKS - 1, 0, fr)
    xc = np.clip(np.interp(Vg[:, 0], cx, np.arange(len(cx))), 0, len(cx) - 1 - 1e-3)
    c0 = np.floor(xc).astype(int)
    cf = xc - c0
    for cc, wc in ((c0, 1 - cf), (c0 + 1, cf)):
        for ii, wi in ((i0, 1 - fr), (i1, fr)):
            for r in np.nonzero(cape)[0]:
                A[r, ix[f"cape_{cc[r]}_{ii[r]}"]] += wc[r] * wi[r]
    # smoothed along the cloth (the rim held at Head)
    fixed = hood & (wh > 0.999)
    for _ in range(20):
        S = np.array([A[a].mean(0) if len(a) else A[i] for i, a in enumerate(adj)])
        A = np.where(fixed[:, None], A, 0.5 * A + 0.5 * S)
    A /= A.sum(1, keepdims=True) + 1e-12
    Jo = np.argsort(-A, 1)[:, :4]
    Wo = np.take_along_axis(A, Jo, 1)
    Wo /= Wo.sum(1, keepdims=True)
    return Jo.astype(np.uint16), Wo.astype(np.float32), allnames


SKIP_BONES = ("lowerarm", "hand", "index", "middle", "ring", "pinky", "thumb")
SMOOTH_ITERS = 80


def body_garment_weights(Vg, lab, adj, Ad, names, chains, A, ix, allnames, dop):
    """r3: the hood and capelet on the body's own weights (the body's skin is the one deformation known good in the
    game's poses; the r1-r2 hand-drawn neck_01 and clavicle bands stretched 2-7x from the idle to the zombie walk, where
    the body itself stretches 1.3-1.4x), the forearms and hands left out; the hood's rim and crown to Head; the
    capelet's free hem to its hem bones; the cape to its chains; all eased along the cloth further than the body's own
    (SMOOTH_ITERS: the cloth spreads what the skin does in a band)."""
    y = Vg[:, 1]
    hood = lab <= 2
    cap = (lab == 3) | (lab == 4)
    near = lab < 5
    D = Ad.copy()
    for n in names:
        if any(k in n for k in SKIP_BONES):
            D[:, names.index(n)] = 0
    D /= D.sum(1, keepdims=True) + 1e-12
    A[near, :len(names)] = D[near]
    head = ix["Head"]
    wh = np.maximum(1 - smoothstep(0.02, 0.08, dop), smoothstep(1.56, 1.68, y)) * hood
    A *= (1 - wh)[:, None]
    A[:, head] += wh
    hem = smoothstep(1.36, 1.27, y) * cap
    ang = np.arctan2(Vg[:, 0] - X0, Vg[:, 2])
    sec = {"b": np.cos(np.clip(np.abs(np.abs(ang) - np.pi), 0, np.pi / 2)) ** 2 * (np.abs(ang) > np.pi / 2),
           "l": np.clip(np.sin(ang), 0, 1) ** 2, "r": np.clip(-np.sin(ang), 0, 1) ** 2}
    tot = sum(sec.values()) + 1e-9
    for key, s_ in sec.items():
        w = hem * 0.6 * s_ / tot * (1.0 if key == "b" else (Vg[:, 2] < 0.12))
        A[:, :len(names)] *= (1 - w)[:, None]
        A[:, ix[f"capelet_{key}_0"]] += w
    cape = lab == 5
    cols = sorted({int(c["bone"].split("_")[1]) for c in chains if c["bone"].startswith("cape_")})
    cx = np.array([np.mean([c["head"][0] for c in chains if c["bone"].startswith(f"cape_{k}_")]) for k in cols])
    Lk = (CAPE_TOP - CAPE_HEM) / CAPE_LINKS
    f = np.clip((CAPE_TOP - y) / Lk, 0, CAPE_LINKS - 1e-3)
    i0 = np.floor(f).astype(int)
    fr = f - i0
    i1 = np.minimum(i0 + 1, CAPE_LINKS - 1)
    fr = np.where(i0 == CAPE_LINKS - 1, 0, fr)
    xc = np.clip(np.interp(Vg[:, 0], cx, np.arange(len(cx))), 0, len(cx) - 1 - 1e-3)
    c0 = np.floor(xc).astype(int)
    cf = xc - c0
    A[cape] = 0
    for cc, wc in ((c0, 1 - cf), (c0 + 1, cf)):
        for ii, wi in ((i0, 1 - fr), (i1, fr)):
            for r in np.nonzero(cape)[0]:
                A[r, ix[f"cape_{cc[r]}_{ii[r]}"]] += wc[r] * wi[r]
    A = smooth_along(A, adj, (hood & (wh > 0.999)) | cape, SMOOTH_ITERS)
    A /= A.sum(1, keepdims=True) + 1e-12
    Jo = np.argsort(-A, 1)[:, :4]
    Wo = np.take_along_axis(A, Jo, 1)
    Wo /= Wo.sum(1, keepdims=True)
    log(f"weights: the body's under the hood and capelet, {SMOOTH_ITERS} smoothing passes")
    return Jo.astype(np.uint16), Wo.astype(np.float32), allnames


def chain_mats(chains, mats_body, names):
    """Skin matrices for the chain bones at the current pose: each rides its body ancestor rigidly (the springs at
    rest), so the drape pose's matrices are the ancestor's."""
    out = []
    for c in chains:
        p = c["parent"]
        while p not in names:
            p = next(x["parent"] for x in chains if x["bone"] == p)
        out.append(mats_body[names.index(p)])
    return np.concatenate([mats_body, np.array(out)]) if out else mats_body


def unpose(Vb, J, W, mats):
    M = np.einsum("nk,nkij->nij", W.astype(float), mats[J.astype(int)])
    Mi = np.linalg.inv(M)
    return b2g(np.einsum("nij,nj->ni", Mi[:, :3, :3], Vb) + Mi[:, :3, 3]), M


def match_fine(o, Vo, Vh, Nh, grp_h, k=16):
    """Per vertex of a reduced mesh: the fine vertex its weights come from: of the same part (its faces' panel; the
    fringe's faces (material 2) any part), facing the same way or opposite (the inner shell), nearest."""
    me = o.data
    pa = me.attributes.get("panel")
    gv = np.full(len(Vo), -1)
    if pa is not None:
        for f in me.polygons:
            if f.material_index == 2:
                continue
            g = (0, 0, 0, 1, 1, 2)[min(max(pa.data[f.index].value, 0), 5)]
            for v in f.vertices:
                gv[v] = g if gv[v] < 0 else min(gv[v], g)
    No = np.zeros(len(Vo) * 3)
    me.vertices.foreach_get("normal", No)
    No = No.reshape(-1, 3)
    t = KDTree(len(Vh))
    for i, p in enumerate(Vh):
        t.insert(p, i)
    t.balance()
    out = np.zeros(len(Vo), np.int64)
    miss = 0
    for i, p in enumerate(Vo):
        c = t.find_n(p, k)
        best, bs = None, 1e9
        for _, j, d in c:
            if gv[i] >= 0 and grp_h[j] != gv[i]:
                continue
            sc = d + 0.03 * (1 - abs(float(np.dot(No[i], Nh[j]))))
            if sc < bs:
                best, bs = j, sc
        if best is None:
            miss += 1
            best = c[0][1]
        out[i] = best
    log(f"{o.name}: weights from the fine mesh, {miss} vertices with no same-part match in {k}")
    return out


def transfer(src_V, src_vals, dst_V):
    t = KDTree(len(src_V))
    for i, p in enumerate(src_V):
        t.insert(p, i)
    t.balance()
    out = np.zeros((len(dst_V),) + src_vals.shape[1:], src_vals.dtype)
    for i, p in enumerate(dst_V):
        nn = t.find_n(p, 3)
        w = np.array([1 / max(d, 1e-4) for _, _, d in nn])
        out[i] = sum(wi * src_vals[j] for wi, (_, j, _) in zip(w, nn)) / w.sum()
    return out


# ================= 7. the bent pose (the corrective) =================
def pose_spine(deg):
    """spine_03 pitched deg forward about its head (the head going +z)."""
    arm = armature()
    bpy.context.view_layer.update()
    Mw = arm.matrix_world
    pb = arm.pose.bones["spine_03"]
    head_w = Mw @ pb.head
    side = Vector(g2b(np.array([[1.0, 0, 0]]))[0])
    best = None
    for sgn in (1, -1):
        R = mathutils.Matrix.Translation(head_w) @ mathutils.Matrix.Rotation(math.radians(deg * sgn), 4, side) @ mathutils.Matrix.Translation(-head_w)
        hd = R @ (Mw @ arm.pose.bones["Head"].head)
        fz = b2g(np.array([hd[:]]))[0][2]
        if best is None or fz > best[0]:
            best = (fz, R)
    pb.matrix = Mw.inverted() @ best[1] @ Mw @ pb.matrix
    bpy.context.view_layer.update()
    log(f"bent pose: spine_03 pitched {deg} deg forward (the head at z {best[0]:.2f})")


def look_at(cam, eye_g, target_g):
    e, t = Vector(g2b(np.array([eye_g]))[0]), Vector(g2b(np.array([target_g]))[0])
    cam.location = e
    cam.rotation_euler = (t - e).to_track_quat("-Z", "Y").to_euler()   # (a camera's up is its local Y)


def sheet(work, tag, views):
    cam = bpy.context.scene.camera
    out = []
    for name, (eye, tgt, f) in views.items():
        cam.data.lens = f
        look_at(cam, eye, tgt)
        p = os.path.join(work, f"{tag}_{name}.png")
        bpy.context.scene.render.filepath = p
        bpy.ops.render.render(write_still=True)
        out.append(p)
    return out


VIEWS = {
    "front": ([X0, 1.62, 1.6], [X0, 1.45, 0.0], 70),
    "bust": ([0.55, 1.66, 0.95], [X0, 1.56, 0.0], 70),
    "side": ([2.6, 1.10, -0.05], [X0, 1.00, -0.05], 45),
    "back": ([-0.45, 1.45, -2.6], [X0, 0.95, -0.1], 45),
    "back34": ([-1.4, 1.65, -1.5], [X0, 1.05, -0.1], 45),
    "body": ([0.45, 1.35, 3.2], [X0, 1.00, 0.0], 45),
}


def preview(ob, maps):
    mat = bpy.data.materials.new("garment_preview")
    mat.use_nodes = True
    nt = mat.node_tree
    bs = nt.nodes["Principled BSDF"]
    def img(name, im, nonc):
        p = os.path.join(bpy.app.tempdir, name + ".png")
        im.save(p)
        i = bpy.data.images.load(p)
        if nonc:
            i.colorspace_settings.name = "Non-Color"
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = i
        return t
    tc = img("pc", maps["color"], False)
    nt.links.new(tc.outputs[0], bs.inputs["Base Color"])
    tn = img("pn", maps["normal"], True)
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tn.outputs[0], nm.inputs["Color"])
    nt.links.new(nm.outputs[0], bs.inputs["Normal"])
    bs.inputs["Roughness"].default_value = 0.85
    bs.inputs["Sheen Weight"].default_value = 0.5
    bs.inputs["Sheen Roughness"].default_value = 0.4
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    ob.data.materials.append(mat)
    ob.data.materials.append(mat)


# ================= the piece =================
def prims_of(c, J, W, P_bind, N_corner, mat_ids, delta=None):
    out = {}
    for m in mat_ids:
        tris = c["tl"][c["tm"] == m]
        if not len(tris):
            continue
        loops = tris.ravel()
        v = c["lv"][loops]
        n = N_corner[loops]
        uv = c["uv"][loops]
        key = np.concatenate([v[:, None].astype(float), np.round(n, 3), np.round(uv, 5)], 1)
        uk, inv = np.unique(key, axis=0, return_inverse=True)
        first = np.zeros(len(uk), np.int64)
        first[inv] = np.arange(len(loops))
        vv = v[first]
        out[m] = dict(pos=P_bind[vv].astype(np.float32), nrm=n[first].astype(np.float32),
                      uv=np.stack([uv[first, 0], 1 - uv[first, 1]], 1).astype(np.float32),
                      idx=inv.reshape(-1).astype(np.uint32), J=J[vv], W=W[vv],
                      delta=None if delta is None else delta[vv].astype(np.float32))
    return out


def write_piece(pkg, path, parts, maps, chains, Mg=None):
    """armor/hood.glb: body.glb's skeleton (plus the chain bones under their parents) and skin, the garment's meshes
    (capelet_bend a morph target on the full mesh) and materials (the inside the same wool: the wet shader darkens it)."""
    g = Glb(os.path.join(pkg, "body.glb"))
    j = g.j
    drop = [i for i, n in enumerate(j["nodes"]) if n.get("name", "").startswith("ford_warden") and n.get("name") != "ford_warden"]
    g.drop_nodes(drop)
    # the chain bones
    sk = j["skins"][0]
    G = g.global_mats()
    by = {n.get("name"): i for i, n in enumerate(j["nodes"])}
    ibm = list(g.acc(sk["inverseBindMatrices"]).reshape(-1, 4, 4))
    for c in chains:
        pi = by[c["parent"]]
        Gp = G[pi]
        head = np.array(c["head"])
        loc = np.linalg.inv(Gp) @ np.append(head, 1.0)
        j["nodes"].append({"name": c["bone"], "translation": loc[:3].tolist()})
        ni = len(j["nodes"]) - 1
        j["nodes"][pi].setdefault("children", []).append(ni)
        Gc = Gp.copy()
        Gc[:3, 3] = head
        G[ni] = Gc
        by[c["bone"]] = ni
        sk["joints"].append(ni)
        ibm.append(np.linalg.inv(Gc).T)   # (glTF: column-major)
    if Mg is not None:   # (r3: bound at the game's pose: inverse bind = the A's inverse bind x the pose's posed-from-A, inverted)
        ibm = [(np.asarray(b).T @ np.linalg.inv(m)).T for b, m in zip(ibm, Mg)]
    sk["inverseBindMatrices"] = g.add_acc(np.array(ibm, np.float32).reshape(-1, 16), "MAT4", target=None)
    j["materials"], j["textures"], j["images"], j["samplers"] = [], [], [], []
    j["meshes"] = []
    tc = g.add_image(enc(maps["color"], "JPEG", 92), "image/jpeg", "hood_color")
    tn = g.add_image(enc(maps["normal"], "JPEG", 95), "image/jpeg", "hood_normal")
    tm = g.add_image(enc(maps["mr"], "PNG"), "image/png", "hood_mr")
    tf = g.add_image(enc(maps["fringe"], "PNG"), "image/png", "hood_fringe")
    wool = {"pbrMetallicRoughness": {"baseColorTexture": {"index": tc}, "metallicRoughnessTexture": {"index": tm},
                                     "metallicFactor": 0.0, "roughnessFactor": 1.0}, "normalTexture": {"index": tn}}
    mats = {MAT_WOOL: dict(wool, name=MAT_WOOL), MAT_INNER: dict(wool, name=MAT_INNER),
            MAT_FRINGE: {"name": MAT_FRINGE, "pbrMetallicRoughness": {"baseColorTexture": {"index": tf}, "metallicFactor": 0.0, "roughnessFactor": 0.85},
                         "alphaMode": "MASK", "alphaCutoff": 0.45, "doubleSided": True}}
    order = list(mats)
    j["materials"] = [mats[k] for k in order]
    arm = j["scenes"][0]["nodes"][0]
    body_node = next(i for i, n in enumerate(j["nodes"]) if n.get("name") == "ford_warden")
    for k, (node_name, prims) in enumerate(parts):
        mesh = {"name": node_name, "primitives": []}
        morph = False
        for mat, arr in prims.items():
            a = {"POSITION": g.add_acc(arr["pos"], "VEC3", minmax=True), "NORMAL": g.add_acc(arr["nrm"], "VEC3"),
                 "TEXCOORD_0": g.add_acc(arr["uv"], "VEC2"), "JOINTS_0": g.add_acc(arr["J"].astype(np.uint16), "VEC4"),
                 "WEIGHTS_0": g.add_acc(arr["W"].astype(np.float32), "VEC4")}
            pr = {"attributes": a, "indices": g.add_acc(arr["idx"], "SCALAR", target=34963), "material": order.index(mat), "mode": 4}
            if arr.get("delta") is not None:
                pr["targets"] = [{"POSITION": g.add_acc(arr["delta"], "VEC3", minmax=True)}]
                morph = True
            mesh["primitives"].append(pr)
        if morph:
            for pr in mesh["primitives"]:
                if "targets" not in pr:
                    pr["targets"] = [{"POSITION": g.add_acc(np.zeros((g.j["accessors"][pr["attributes"]["POSITION"]]["count"], 3), np.float32), "VEC3", minmax=True)}]
            mesh["weights"] = [0.0]
            mesh["extras"] = {"targetNames": ["capelet_bend"]}
        j["meshes"].append(mesh)
        if k == 0:
            j["nodes"][body_node] = {"name": node_name, "mesh": 0, "skin": 0}
        else:
            j["nodes"].append({"name": node_name, "mesh": k, "skin": 0})
            j["nodes"][arm].setdefault("children", []).append(len(j["nodes"]) - 1)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    g.save(path)
    log(f"wrote {path} ({os.path.getsize(path) / 1e6:.1f} MB)")


def pose_game(path):
    """The armature set to the game's pose: each bone's skin matrix (global pose x bind, glTF frame) from the pose file,
    parents first (Blender's armature space = the glTF skeleton's, Y up turned Z up)."""
    d = json.load(open(path))["skin"]
    arm = armature()
    bpy.context.view_layer.update()
    Ci = np.linalg.inv(C_G2B)
    for pb in sorted(arm.pose.bones, key=lambda b: len(b.parent_recursive)):
        if pb.name not in d:
            continue
        Sg = np.eye(4)
        Sg[:3] = np.array(d[pb.name]).reshape(3, 4)
        pb.matrix = mathutils.Matrix((C_G2B @ Sg @ Ci).tolist()) @ pb.bone.matrix_local
        bpy.context.view_layer.update()
    log(f"bind pose: the game's ({os.path.basename(path)}, {len(d)} bones)")


def spine_pitch():
    """spine_03's forward pitch off its rest (deg), as PieceSprings reads it (the bone's Y axis, against the root)."""
    arm = armature()
    pb = arm.pose.bones["spine_03"]
    y0 = b2g(np.array([np.array(pb.bone.matrix_local.col[1][:3])]))[0]
    y1 = b2g(np.array([np.array(pb.matrix.col[1][:3])]))[0]
    a0, a1 = math.atan2(y0[2], y0[1]), math.atan2(y1[2], y1[1])
    return math.degrees(a1 - a0)


def blend_mats(J, W, mats):
    return np.einsum("nk,nkij->nij", W.astype(float), mats[J.astype(int)])


def donor_weights(Vb, donors, nb, k=8):
    """Per vertex (Blender, the drape pose): the body's weights near it (k nearest, by 1/d), all its bones (the game's
    pose has its share and twist bones too): to carry the drape into the game's pose following the body."""
    P, J, W = donors
    t = KDTree(len(P))
    for i, p in enumerate(P):
        t.insert(p, i)
    t.balance()
    A = np.zeros((len(Vb), nb))
    dist = np.zeros(len(Vb))
    for i, v in enumerate(Vb):
        nn = t.find_n(v, k)
        dist[i] = nn[0][2]
        for co, j, d in nn:
            w = 1.0 / max(d, 0.004)
            for q in range(4):
                if W[j, q] > 0:
                    A[i, J[j, q]] += w * W[j, q]
    return A / (A.sum(1, keepdims=True) + 1e-12), dist


def dense(J, W, nb):
    A = np.zeros((len(J), nb))
    np.add.at(A, (np.repeat(np.arange(len(J)), J.shape[1]), J.ravel().astype(int)), W.ravel())
    return A


def top4(A):
    Jo = np.argsort(-A, 1)[:, :4]
    Wo = np.take_along_axis(A, Jo, 1)
    Wo /= Wo.sum(1, keepdims=True) + 1e-12
    return Jo.astype(np.uint16), Wo.astype(np.float32)


def spread_hem(Vo, lab):
    """(r4, the max judge) The cape's hem spread where it meets the water: below HEM_SPREAD's top its x widened about
    the cape's centre and its folds eased toward their mean depth (the cloth unfolding as it lies out), to the hem.
    Vo: Blender (z up), the bound pose; lab: each vertex's panel."""
    k, k_un, y0, y1 = HEM_SPREAD
    V = np.array(Vo, float)
    c = lab == 5
    if not c.any():
        return V
    mid = c & (V[:, 2] > 0.85) & (V[:, 2] < 1.05)
    xc = np.median(V[mid, 0]) if mid.any() else np.median(V[c, 0])
    s = smoothstep(y0, y1, V[:, 2]) * c
    s = s ** 1.3
    # (the fold depth about a smooth mean back-line, per height band)
    yb = np.round(V[:, 2] / 0.03)
    mean_y = np.zeros(len(V))
    for b in np.unique(yb[c & (s > 0)]):
        sel = c & (yb == b)
        mean_y[sel] = np.median(V[sel, 1])
    V[:, 0] = xc + (V[:, 0] - xc) * (1 + k * s)
    V[:, 1] = np.where(s > 0, V[:, 1] + (mean_y - V[:, 1]) * k_un * s, V[:, 1])
    w = V[c & (V[:, 2] < y1 + 0.06), 0]
    log(f"cape hem spread: hem width {((w.max() - w.min()) * 100 if len(w) else 0):.0f} cm (x {xc:.3f})")
    return V


def tris_of(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    pkg = argv[0]
    opt = {argv[i][2:]: argv[i + 1] for i in range(len(argv) - 1) if argv[i].startswith("--")}
    work = opt.get("work", os.path.join(pkg, "..", "_check_garment"))
    stage = opt.get("stage", "all")
    frames = int(opt.get("frames", FRAMES))
    os.makedirs(work, exist_ok=True)
    t0 = time.time()
    src = os.path.join(work, "uncut")
    restore_uncut(pkg, opt["pre"], src)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    body = load_body(src)
    bobs = import_body(src)
    for o in [o for o in bobs if len(o.data.vertices) < 1000]:   # (the glb's stray helper sphere)
        o.hide_render = True
        bobs.remove(o)
    pose_arms(WH.POSE_DEG)
    Vg, Vb_body, Fb = posed_body(bobs)
    cols = collider_obs(Vg, Fb)
    col_env = envelope_col(Vg, Fb)
    # ---- 1. the arrangement ----
    cape = cape_arrangement(Vg)
    push_clear(cape, [cols[0], cols[1]], gap=0.012, iters=4)
    sh = hood_arrangement(np.concatenate([Vg, b2g(verts(cape)) + np.array([0, 0, -0.012])]))
    clear_arrangement(sh, cols[0], gap=0.010)
    bm = bmesh.new()
    bm.from_mesh(sh.data)
    open_pts = np.array([b2g(np.array([v.co[:]]))[0] for v in bm.verts if v.is_boundary and v.co.z > HEM_Y + 0.05])
    bm.free()
    log(f"the face opening: {len(open_pts)} boundary points")
    pairs = panels(sh, cape)
    ob = sh
    s_uv = flatten(ob)
    WH.GRAIN = (s_uv, 0.0)
    lab = panel_of_verts(ob)
    log("panels:", {PANELS[k]: int((lab == k).sum()) for k in range(6)})
    setup_render()
    for o in bobs:
        o.hide_render = False
    diag(ob, lab, [cols[0]], "arrangement")
    if stage == "arrange":
        WH.preview_mat(ob)
        sheet(work, "arr", VIEWS)
        return
    if opt.get("drape"):   # (the drape from an earlier run: the later stages iterated without the sims)
        with bpy.data.libraries.load(opt["drape"]) as (src_, dst_):
            dst_.meshes = ["garment_drape"]
        old_me = ob.data
        ob.shape_key_clear()
        ob.data = dst_.meshes[0]
        bpy.data.meshes.remove(old_me)
        log(f"the drape loaded from {opt['drape']}: {len(ob.data.vertices)} verts")
    else:
        # ---- 3a. the cape ----
        V0 = b2g(verts(ob))
        pins = np.where(lab != 5, 1.0, 1 - smoothstep(0.004, 0.030, CAPE_TOP - V0[:, 1]))
        P = cloth(ob, pins, frames, 1.6, cols, sew=False)
        ob.data.shape_keys.key_blocks["Basis"].data.foreach_set("co", P.ravel())
        set_verts(ob, P)
        # the cape as the capelet's collider
        capeV = b2g(P)[lab == 5]
        log(f"cape draped: hem y {capeV[:, 1].min():.3f}, z {capeV[:, 2].min():.3f}..{capeV[:, 2].max():.3f}")
        me = ob.data
        Fc = [p.vertices[:] for p in me.polygons if lab[p.vertices[0]] == 5]
        idmap = -np.ones(len(lab), np.int64)
        idmap[lab == 5] = np.arange((lab == 5).sum())
        col_cape = mk("col_cape", P[lab == 5], [tuple(idmap[list(f)]) for f in Fc])
        col_cape.hide_render = True
        col_cape.modifiers.new("collide", "COLLISION")
        col_cape.collision.thickness_outer = 0.005
        col_cape.collision.thickness_inner = 0.004
        col_cape.collision.cloth_friction = 6.0
        if stage == "cape":
            WH.preview_mat(ob)
            sheet(work, "cape", VIEWS)
            return
        # ---- 3b. the hood and capelet over it ----
        diag(ob, lab, [cols[0], col_cape], "before clear")
        clear_capelet(ob, lab, [cols[0], col_cape])
        diag(ob, lab, [cols[0], col_cape], "after clear")
        pins = opening_pins(ob, lab, open_pts)
        pins[lab == 5] = 1.0
        # the sewing springs: a loose edge between each seam pair (coincident, rest length 0)
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bm.verts.ensure_lookup_table()
        for a_, b_ in pairs:
            bm.edges.new((bm.verts[a_], bm.verts[b_]))
        bm.to_mesh(ob.data)
        bm.free()
        # (phase 1: the capelet's yoke held softly on the shoulders while the seams pull shut; phase 2 free)
        Vy = b2g(verts(ob))
        yoke = np.where((lab == 3) | (lab == 4), YOKE_HOLD * smoothstep(YOKE_Y[0], YOKE_Y[1], Vy[:, 1]), 0.0)
        P = cloth(ob, np.maximum(pins, yoke), YOKE_FRAMES, BEND, [cols[0], col_env, col_cape], sew=True)
        ob.data.shape_keys.key_blocks["Basis"].data.foreach_set("co", P.ravel())
        set_verts(ob, P)
        diag(ob, lab, [cols[0], col_cape], "after yoke phase")
        P = cloth(ob, pins, frames, BEND, [cols[0], col_env, col_cape], sew=True)
        ob.data.shape_keys.key_blocks["Basis"].data.foreach_set("co", P.ravel())
        set_verts(ob, P)
        diag(ob, lab, [cols[0], col_cape], "after drape")
        ob.shape_key_clear()
        set_verts(ob, P)
        weld(ob, pairs)
        for p in ob.data.polygons:
            p.use_smooth = True
        ob.data.name = "garment_drape"
        bpy.data.libraries.write(os.path.join(work, "drape.blend"), {ob.data}, fake_user=True)
    np.savez(os.path.join(work, "drape.npz"), V=verts(ob))
    if stage == "drape":
        WH.preview_mat(ob)
        sheet(work, "drape", VIEWS)
        return
    # ---- 4. tear ----
    cape_clear(ob, Vb_body, Fb)
    tear(ob)
    hi = ob
    hi.name = "garment_hi"
    # ---- the weights, designed on the drape (the fine mesh; carried to each reduced one later) ----
    names = body["names"]
    mats_d = skin_mats(names)
    Vh = b2g(verts(hi))          # (the drape: the weights' and masks' frame)
    labh = panel_of_verts(hi)
    chains = chain_bones(Vh, labh, names)
    Pd = verts(hi)
    Ad, dd = donor_weights(Pd, body_posed_donors(body, mats_d), len(names))
    Jh, Wh, allnames = garment_weights(Vh, labh, adjacency(hi), None if opt.get("weights") == "r2" else Ad, names, chains, open_pts)
    bindp = opt.get("bind", BIND_POSE)
    if bindp != "drape":
        # ---- r3: carried into the game's idle on the final weights, relaxed there, bound there ----
        mats_dall = chain_mats(chains, mats_d, names)
        Jp, Wp = Jh, Wh
        pins = opening_pins(hi, labh, open_pts)
        pins = np.where(labh == 5, 1 - smoothstep(0.004, 0.030, CAPE_TOP - Vh[:, 1]), pins)
        for o in cols + [col_env]:
            bpy.data.objects.remove(o)
        pose_game(bindp)
        Vg2, Vb_body, Fb = posed_body(bobs)
        cols = collider_obs(Vg2, Fb)
        mats_g = skin_mats(names)
        rel = chain_mats(chains, mats_g, names) @ np.linalg.inv(mats_dall)
        Mp = blend_mats(Jp, Wp, rel)
        Pg = np.einsum("nij,nj->ni", Mp[:, :3, :3], Pd) + Mp[:, :3, 3]
        hi.shape_key_clear()
        hi.shape_key_add(name="Basis").data.foreach_set("co", Pg.ravel())
        hi.shape_key_add(name="flat").data.foreach_set("co", Pd.ravel())
        set_verts(hi, Pg)
        diag(hi, labh, [cols[0]], "skinned into the game's idle")
        rf = int(opt.get("relax", RELAX_FRAMES))
        if opt.get("relax-all") != "1":
            # (the cape alone relaxed: it hangs again from its attach line once spine_03's 18 deg idle pitch tilted it
            #  out 34 cm off the calves; the hood and capelet held as skinned (a free relax drew the left capelet in
            #  18 cm: the drape's rest angles against the idle's lowered arms, WIP)
            pins = np.where(labh < 5, 1.0, pins)
        P = cloth(hi, pins, rf, BEND, [cols[0], cols[1]], sew=False) if rf > 0 else Pg
        hi.shape_key_clear()
        set_verts(hi, P)
        diag(hi, labh, [cols[0]], "relaxed in the game's idle")
        # the chain bones laid on the relaxed cape, written in the rest frame (they ride spine_03)
        Ms = np.linalg.inv(C_G2B) @ mats_g[names.index("spine_03")] @ C_G2B
        Msi = np.linalg.inv(Ms)
        Vgg = b2g(P)
        cidx = np.nonzero(labh == 5)[0]
        tc = KDTree(len(cidx))
        for q, i in enumerate(cidx):
            tc.insert(Vh[i], q)
        tc.balance()

        def relay(pt):
            nn_ = [cidx[q] for _, q, _ in tc.find_n(pt, 12)]
            g_ = Vgg[nn_].mean(0) + (np.array(pt) - Vh[nn_].mean(0))
            return (Msi @ np.append(g_, 1.0))[:3].round(4).tolist()
        for c_ in chains:
            if c_["bone"].startswith("cape_"):
                c_["head"], c_["tail"] = relay(c_["head"]), relay(c_["tail"])
        log(f"spine_03 pitch in the bind pose: {spine_pitch():.1f} deg")
    mats = skin_mats(names)
    mats_all = chain_mats(chains, mats, names)
    # the bind: the pose the garment is in now (the game's idle; with --bind drape the glb's A, unposed, as r1-r2 did)
    if bindp == "drape":
        Ph_bind, _ = unpose(verts(hi), Jh, Wh, mats_all)
        Mg_all = np.tile(np.eye(4), (len(mats_all), 1, 1))
    else:
        Ph_bind = b2g(verts(hi))
        Mg_all = np.linalg.inv(C_G2B)[None] @ mats_all @ C_G2B[None]     # posed-from-A per joint, glTF
    Mb_bind = C_G2B[None] @ Mg_all @ np.linalg.inv(C_G2B)[None]           # the same, Blender
    # ---- budget, maps ----
    lo = decimated(hi, LO_TRIS, "garment_lo")
    bk = bake_lo(hi, lo, TEX, [lo] + bobs)
    crest = bake_crest(hi, lo, TEX // 2)
    lod1 = decimated(lo, LOD_TRIS, "garment_lod1")
    shadow = decimated(lo, SHADOW_TRIS, "garment_shadow")
    # ---- 7. the corrective: the bent pose ----
    # (the arms as draped, then the spine bent: r1's bent sim ran with the arms back at the bind's wide A, the capelet
    #  tented over them into a dome and the cape caught on the arm)
    arm0 = armature()
    for pb in arm0.pose.bones:
        pb.matrix_basis = mathutils.Matrix.Identity(4)
    bpy.context.view_layer.update()
    if bindp == "drape":
        pose_arms(WH.POSE_DEG)
        pose_spine(80.0)
    else:
        pose_game(bindp)
        p0_ = spine_pitch()
        pose_spine(80.0 - p0_)
        log(f"bent from the bind pose's {p0_:.1f} deg to {spine_pitch():.1f} deg")
    Vbent, _, Fbent = posed_body(bobs)
    mats_b = chain_mats(chains, skin_mats(names), names) @ np.linalg.inv(Mb_bind)   # (from the bind)
    Mb = np.einsum("nk,nkij->nij", Wh.astype(float), mats_b[Jh.astype(int)])
    Pb_start = np.einsum("nij,nj->ni", Mb[:, :3, :3], g2b(Ph_bind)) + Mb[:, :3, 3]
    for o in cols:
        bpy.data.objects.remove(o)
    cols_b = collider_obs(b2g(Vbent), Fbent)
    hb = hi.copy()
    hb.data = hi.data.copy()
    bpy.context.scene.collection.objects.link(hb)
    set_verts(hb, Pb_start)
    head = allnames.index("Head")
    hw = np.array([w[list(jj).index(head)] if head in jj else 0 for jj, w in zip(Jh, Wh)])
    bend_mask = np.where((labh == 3) | (labh == 4), smoothstep(1.47, 1.40, Vh[:, 1]), 0.0)
    bend_mask = np.maximum(bend_mask, (labh == 5) * smoothstep(CAPE_TOP - 0.45, CAPE_TOP - 0.15, Vh[:, 1]))
    pins_b = np.clip(1 - bend_mask, 0, 1)
    pins_b = np.maximum(pins_b, hw)
    Pb = cloth(hb, pins_b, 45, BEND, [cols_b[0]], sew=False)
    Pb_bind, _ = unpose(Pb, Jh, Wh, mats_b)
    delta_h = (Pb_bind - Ph_bind) * bend_mask[:, None]
    log(f"capelet_bend: max {np.linalg.norm(delta_h, axis=1).max() * 100:.1f} cm, mean over the mask {np.linalg.norm(delta_h, axis=1)[bend_mask > 0.5].mean() * 100:.1f} cm")
    np.savez(os.path.join(work, "bend.npz"), start=b2g(Pb_start), bent=b2g(Pb), mask=bend_mask)
    # (a look at the bent drape, the body bent: no dome over the shoulders)
    bpy.context.scene.render.engine = "BLENDER_EEVEE_NEXT"
    for o in (hi, lo, lod1, shadow):
        o.hide_render = True
    set_verts(hb, Pb)
    WH.preview_mat(hb)
    sheet(work, "bend", {"side": ([2.4, 1.45, 0.2], [X0, 1.15, 0.0], 45), "high": ([1.3, 2.7, 1.5], [X0, 1.25, -0.05], 40),
                         "back": ([0.8, 2.2, -1.8], [X0, 1.2, -0.1], 40)})
    for o in (lo, lod1, shadow):
        o.hide_render = False
    # (back to the drape pose for the renders)
    bpy.data.objects.remove(hb)
    for o in cols_b:
        bpy.data.objects.remove(o)
    arm = armature()
    for pb in arm.pose.bones:
        pb.matrix_basis = mathutils.Matrix.Identity(4)
    if bindp == "drape":
        pose_arms(WH.POSE_DEG)
    else:
        pose_game(bindp)
    # ---- 5. thickness, rim, fringe; the maps ----
    rd, rd1 = WH.roll_data(lo, 8), WH.roll_data(lod1, 5)
    WH.FRINGE_MIN_Y = 0.48   # (r4: no strands on the cape's hem where it lies in the river)
    fr = WH.fringe(lo, rd)
    slots = [bpy.data.materials.new(n) for n in ("slot_wool", "slot_inner", "slot_fringe")]
    for o in (lo, lod1, shadow, fr):
        o.data.materials.clear()
        for mt in (slots if o is fr else slots[:2]):
            o.data.materials.append(mt)
        for p in o.data.polygons:
            p.material_index = 0
    WH.thicken(lo)
    WH.thicken(lod1)
    WH.add_roll(lo, rd)
    WH.add_roll(lod1, rd1)
    for p in fr.data.polygons:
        p.material_index = 2
    select_only(fr, lo)
    bpy.ops.object.join()
    hi.hide_render = True
    for o in (lo, lod1):
        select_only(o)
        bpy.ops.object.shade_smooth()
    # ---- skinned, unposed, written ----
    parts, info = [], {}
    Vh_b = verts(hi)
    Nh_b = np.zeros(len(Vh_b) * 3)
    hi.data.vertices.foreach_get("normal", Nh_b)
    Nh_b = Nh_b.reshape(-1, 3)
    grp_h = np.array([0, 0, 0, 1, 1, 2])[np.clip(labh, 0, 5)]
    for node, o, ids in (("hood.wool", lo, (0, 1, 2)), ("hood.lod1.wool", lod1, (0, 1)), ("hood.shadow", shadow, (0,))):
        Vo = verts(o)
        # weights by the nearest fine vertex of the same part (hood / capelet / cape; the fringe any) whose surface
        # faces the same way (r1: the plain nearest gave an inner-shell or a touching fold's vertex the other layer's
        # bones: Head on the capelet, cape chains on the fringe; stretch p99 2-5 in the motion check)
        nn = match_fine(o, Vo, Vh_b, Nh_b, grp_h)
        J, W = Jh[nn], Wh[nn]
        dl = delta_h[nn] if node != "hood.shadow" else None   # (r3: the bend on LOD1 too)
        c = corner_arrays(o)
        Vo = spread_hem(Vo, labh[nn])
        P_rest, M = unpose(Vo, J, W, mats_all)    # (the A frame: the mantle cut and the ID map)
        if bindp == "drape":
            P_bind = P_rest
            n = np.einsum("nji,nj->ni", M[c["lv"]][:, :3, :3], c["cn"])
        else:
            P_bind = b2g(Vo)
            n = np.array(c["cn"], float)
        n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
        prims = prims_of(c, J, W, P_bind, b2g(n), ids, dl)
        parts.append((node, {(MAT_WOOL, MAT_INNER, MAT_FRINGE)[m]: a for m, a in prims.items()}))
        info[node] = {"tris": int(sum(len(a["idx"]) // 3 for a in prims.values())),
                      "bones": sorted({allnames[x] for x in np.unique(J[W > 0.01])})}
        if node == "hood.wool":
            HP = P_rest
            wp = prims_of(c, J, W, P_rest, b2g(n), (0,))[0]
            # (the mantle cut under the hood and capelet only: the cape hangs clear of the robe, and swings)
            lab_lo = labh[nn]
            tri = c["lv"][c["tl"][c["tm"] < 2]]
            HFw = tri[(lab_lo[tri] < 5).all(1)]
    log("piece", json.dumps(info))
    maps = wool_maps(bk, crest, rasterize(wp["pos"][:, 1], wp["uv"], wp["idx"], TEX // 4)[0], s_uv, TEX)
    maps["fringe"] = fringe_map()
    for k_ in ("color", "normal", "mr", "fringe"):
        maps[k_].save(os.path.join(work, f"map_{k_}.png"))
    out_pkg = pkg if opt.get("write-body") == "1" else work
    write_piece(src, os.path.join(out_pkg, "armor", "hood.glb"), parts, maps, chains, Mg_all)
    WH.hood_id_map(wp["pos"], wp["uv"], wp["idx"]).save(os.path.join(out_pkg, "armor", "hood_id.png"))
    # the mantle cut: under the hood and capelet only (the cape hangs clear of the robe)
    cut = cut_mantle(src, out_pkg, HP, HFw)
    springs = [dict(c_, head=[round(x, 4) for x in c_["head"]], tail=[round(x, 4) for x in c_["tail"]]) for c_ in chains]
    if out_pkg == pkg:
        mp = os.path.join(pkg, "manifest.json")
        m = json.load(open(mp))
        m["pieces"] = [{"id": "hood", "slot": "cloak", "file": "armor/hood.glb", "springs": springs,
                        "correctives": [{"shape": "capelet_bend", "bone": "spine_03", "axis": "pitch", "from": CORR_PITCH[0], "to": CORR_PITCH[1]}]}]
        m["hood"] = {"source": "tools/assets/warden_garment.py (sewn-pattern cloth: hood, gusset, capelet, cape; Warden 7)",
                     "materials": [MAT_WOOL, MAT_INNER, MAT_FRINGE], "tris": info["hood.wool"]["tris"], "lodTris": info["hood.lod1.wool"]["tris"],
                     "shadowTris": info["hood.shadow"]["tris"], "bones": info["hood.wool"]["bones"], "maps": TEX, "mantleCut": cut}
        json.dump(m, open(mp, "w"), indent=1)
    # ---- numbers and renders (the drape pose) ----
    bpy.context.scene.render.engine = "BLENDER_EEVEE_NEXT"
    preview(lo, maps)
    for o in (lod1, shadow):
        o.hide_render = True
    res = face_numbers(bobs, [lo])
    # the cape's clearance off the body at rest (behind the calves and the robe)
    bvh = BVHTree.FromPolygons([tuple(v) for v in Vb_body], [tuple(f) for f in Fb])
    cv = verts(hi)[labh == 5]
    dd = []
    for p in cv:
        if b2g(p[None])[0][1] < 0.75:
            h = bvh.find_nearest(Vector(p), 0.5)
            dd.append(h[3] if h[0] is not None else 0.5)
    clr = {"p1": round(float(np.percentile(dd, 1)) * 100, 2), "min": round(float(np.min(dd)) * 100, 2)} if dd else {}
    if dd:
        cl = [b2g(p[None])[0] for p in cv if b2g(p[None])[0][1] < 0.75]
        clr["minAt"] = [round(float(x), 3) for x in cl[int(np.argmin(dd))]]
    log("cape clearance below 0.75 m (cm):", clr)
    json.dump({"numbers": res, "piece": info, "mantleCut": cut, "springs": springs, "capeClearanceCm": clr},
              open(os.path.join(work, "numbers.json"), "w"), indent=1)
    sheet(work, "garment", VIEWS)
    log(f"done in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
