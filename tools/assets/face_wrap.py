"""A face's whole shape taken from a head TRELLIS 2 made of its portrait
(tools/assets/face_trellis.py): her MakeHuman head (as heroine_head.py makes
it: face_shapes's MACROS, FACE and BUILD) laid, every point of her face,
on that head's surface, and written as a MakeHuman target of our own
(heroine_face/targets/portrait-<id>.target, which heroine_head.py loads as
it loads MakeHuman's own). Her topology, rig, UVs and expressions are kept;
only where her points lie changes.

    blender -b --python tools/assets/face_wrap.py -- <shape.glb> <painted.glb> <out.target> [--check <dir>]

shape.glb: TRELLIS's surface. painted.glb: the same, with its colours (by
which its hair is told from its skin). With --check, clay renders of her
before and after and of TRELLIS's head, and its hair as read.
WRAP_HAIR_DEPTH (metres, 0.005) is how far under its hair her skull lies.

Why: MakeHuman's targets move a face's outlines; fitted to a reference by
its landmarks they could not give full lips, soft full cheeks and a fine
jaw at once (FACE v1 to v3 were one face: heavy jaw, gaunt cheeks, thin
lips). MoGe-2 reads a picture's surface only from in front, flatter than it
is (face_warp.py). TRELLIS makes the whole head, its volumes, round to the
ears and under the jaw.

How:
  1. Landmarks on both heads: each drawn in clay from in front, lit alike
     (so the two are read alike), MediaPipe's landmarks found, and each
     cast back onto its surface (one through a gap, between her lips or
     past a lid's rim, brought to the surface in front).
  2. Placed on her: turned, scaled and moved so its landmarks on her eyes,
     nose and mouth lie on hers.
  3. Laid on it: her points pulled onto its surface (along her normal,
     point to plane, so they may slide along it), her nose's and lips'
     landmarks to its, her surface bent as little as can be: stiff at
     first, then freer (a non-rigid ICP). Her whole head, her cranium too
     (her skull a few millimetres under its hair); her ears carried along,
     her neck and nape held, her mouth's inside carried along. Each eye's
     opening made the shape of its (an affine map of her lids' landmarks).
  4. Her eyes moved, each eyeball whole, as the map moves its middle; her
     lids laid back on them as they lay; lashes, teeth and tongue moved
     with what they sit in.
  5. Made symmetrical (her left side and right side the mean of both):
     TRELLIS's guess is a little lopsided, and a lopsided face is a plainer one.

Also printed: where its hair begins over her eyes (for face_shapes.HAIRLINE).
"""
import gzip
import json
import math
import os
import subprocess
import sys

import bpy
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
from scipy.spatial import cKDTree

sys.stdout.reconfigure(line_buffering=True)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import face_shapes as fs  # noqa: E402

from bl_ext.user_default.mpfb.services.humanservice import HumanService  # noqa: E402
from bl_ext.user_default.mpfb.services.targetservice import TargetService  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:]
SHAPE, PAINTED, OUT = (os.path.abspath(a) for a in ARGS[:3])
CHECK = os.path.abspath(ARGS[ARGS.index("--check") + 1]) if "--check" in ARGS else None
WORK = CHECK or os.path.dirname(OUT)
os.makedirs(WORK, exist_ok=True)
FACEFIT_PY = os.path.join(os.environ.get("LOCALAPPDATA", ""), "facefit", ".venv", "Scripts", "python.exe")

# MediaPipe's landmarks by what they mark (face_fit.py's).
OVAL = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136,
        172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]
LIPS = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 185, 40, 39, 37, 0, 267, 269, 270, 409, 78, 95, 88, 178, 87, 14, 317,
        402, 318, 324, 308, 191, 80, 81, 82, 13, 312, 311, 310, 415]
INNER_LIPS = [78, 191, 80, 81, 82, 13, 312, 311, 310, 415, 308, 324, 318, 402, 317, 14, 87, 178, 88, 95]
EYE_A = [33, 246, 161, 160, 159, 158, 157, 173, 133, 155, 154, 153, 145, 144, 163, 7]
EYE_B = [263, 466, 388, 387, 386, 385, 384, 398, 362, 382, 381, 380, 374, 373, 390, 249]
BROWS = [70, 63, 105, 66, 107, 55, 65, 52, 53, 46, 300, 293, 334, 296, 336, 285, 295, 282, 283, 276]
NOSE = [1, 2, 98, 327, 4, 5, 195, 197, 6, 168, 48, 278, 64, 294, 129, 358, 49, 279, 115, 344, 220, 440]
IRIS = list(range(468, 478))
CORE = EYE_A + EYE_B + NOSE + LIPS


def weights(n):
    """How surely each landmark is taken where TRELLIS's head has it: her
    features' outlines most; her face's outline least (MediaPipe reads it
    off a soft edge, and the surface holds it anyway); her irises not at
    all (they are her eyeballs', not her skin's)."""
    w = np.full(n, 0.3)
    for group, v in ((OVAL, 0.25), (LIPS, 1.6), (EYE_A, 1.6), (EYE_B, 1.6), (BROWS, 0.6), (NOSE, 1.2)):
        w[group] = v
    w[[i for i in IRIS if i < n]] = 0.0
    return w


def smooth01(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def umeyama(src, dst, wt):
    """The scale, turn and shift taking src to dst, weighted (least squares)."""
    W = wt / wt.sum()
    ms, md = (W[:, None] * src).sum(0), (W[:, None] * dst).sum(0)
    a, b = src - ms, dst - md
    C = (W[:, None] * b).T @ a
    U, S, Vt = np.linalg.svd(C)
    D = np.diag([1, 1, np.sign(np.linalg.det(U @ Vt))])
    R = U @ D @ Vt
    s = (S * np.diag(D)).sum() / (W * (a * a).sum(1)).sum()
    return s, R, md - s * R @ ms


def inside(poly, pts):
    """Which 2D points lie inside a polygon (even-odd)."""
    x, y = pts[:, 0], pts[:, 1]
    res = np.zeros(len(pts), bool)
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        res ^= ((yi > y) != (yj > y)) & (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi)
        j = i
    return res


def vertex_normals(V, F):
    N = np.zeros_like(V)
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    for k in range(3):
        np.add.at(N, F[:, k], fn)
    return N / (np.linalg.norm(N, axis=1)[:, None] + 1e-12)


# ---------------------------------------------------------------- her --
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
hm = HumanService.create_human(mask_helpers=True, detailed_helpers=True, extra_vertex_groups=True, feet_on_ground=True,
                               scale=0.1, macro_detail_dict=fs.MACROS)
TARGET = fs.target_paths()
for t, v in {**fs.FACE, **fs.BUILD}.items():
    if t in fs.SCULPTS or t.startswith("portrait-"):
        continue
    for n in fs.sides([t]):
        TargetService.load_target(hm, TARGET[n], weight=v, name="face_" + n)
for mo in hm.modifiers:
    mo.show_viewport = mo.show_render = False
bpy.context.view_layer.update()
MW = np.array(hm.matrix_world)


def positions():
    dg = bpy.context.evaluated_depsgraph_get()
    e = hm.evaluated_get(dg)
    m = e.to_mesh()
    V = np.array([v.co[:] for v in m.vertices])
    e.to_mesh_clear()
    assert len(V) == len(hm.data.vertices)
    return V @ MW[:3, :3].T + MW[:3, 3]


P = positions()
for t, v in fs.FACE.items():                     # (her face's own sculpts, as heroine_head.py lays them)
    if t in fs.SCULPTS:
        P = P + v * fs.SCULPTS[t](P, fs.anatomy(P))
NV = len(P)
groups = {g.name: g.index for g in hm.vertex_groups}
member = {name: np.zeros(NV, bool) for name in groups}
_gi = {i: n for n, i in groups.items()}
for v in hm.data.vertices:
    for g in v.groups:
        if g.weight > 0.5:
            member[_gi[g.group]][v.index] = True
BODY = member["body"]
me = hm.data
me.calc_loop_triangles()
F = np.array([t.vertices[:] for t in me.loop_triangles])
F = F[BODY[F].all(1)]

NRM = vertex_normals(P, F)


# ---------------------------------------------------------- TRELLIS's head --
def load_glb(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    ob = next(o for o in new if o.type == "MESH")
    for o in new:
        if o != ob:
            bpy.data.objects.remove(o)
    mw = np.array(ob.matrix_world)
    ob.parent = None
    V = np.zeros(len(ob.data.vertices) * 3)
    ob.data.vertices.foreach_get("co", V)
    V = V.reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3]
    ob.matrix_world = Matrix.Identity(4)
    ob.data.vertices.foreach_set("co", V.ravel())
    ob.data.update()
    return ob, V


shape_ob, TV = load_glb(SHAPE)
paint_ob, PV = load_glb(PAINTED)
print("TRELLIS: %d points of surface (%d painted); %.3f across" % (len(TV), len(PV), np.ptp(TV, 0).max()))
sc = bpy.context.scene
for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
    try:
        sc.render.engine = eng
        break
    except TypeError:
        pass
sc.view_settings.view_transform = "Standard"
sc.world = bpy.data.worlds.new("w")
sc.world.use_nodes = True
sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.5, 0.5, 0.5, 1)
sc.world.node_tree.nodes["Background"].inputs[1].default_value = 0.8
_sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
_sun.data.energy = 2.0
_sun.data.angle = math.radians(20)
sc.collection.objects.link(_sun)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.type = "ORTHO"
sc.render.resolution_x = sc.render.resolution_y = 1024
sc.render.resolution_percentage = 100
grey = bpy.data.materials.new("clay")
grey.use_nodes = True
grey.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.62, 0.52, 0.47, 1)
grey.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.55
# (its colours on its points, for the hair it is read to have)
_pm = bpy.data.materials.new("painted")
_pm.use_nodes = True
_nt = _pm.node_tree
_attr = _nt.nodes.new("ShaderNodeVertexColor")
if paint_ob.data.color_attributes:
    _attr.layer_name = paint_ob.data.color_attributes[0].name
_nt.links.new(_attr.outputs["Color"], _nt.nodes["Principled BSDF"].inputs["Base Color"])
_nt.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.7
paint_ob.data.materials.clear()
paint_ob.data.materials.append(_pm)
shape_ob.data.materials.clear()
shape_ob.data.materials.append(grey)
paint_ob.hide_render = True
hm.hide_render = True


def mesh_object(name, V, Fc):
    m_ = bpy.data.meshes.new(name)
    m_.from_pydata([tuple(p) for p in V], [], [tuple(int(i) for i in f) for f in Fc])
    for p_ in m_.polygons:
        p_.use_smooth = True
    o_ = bpy.data.objects.new(name, m_)
    sc.collection.objects.link(o_)
    m_.materials.append(grey)
    return o_


def look(centre, fwd, scale):
    """The orthographic camera on `centre`, looking along `fwd`, `scale` across;
    the sun from over the camera's shoulder."""
    fwd = Vector(fwd).normalized()
    cam.location = Vector(centre) - fwd * 3.0
    cam.rotation_euler = fwd.to_track_quat("-Z", "Y").to_euler()
    cam.data.ortho_scale = scale
    cam.data.clip_end = 10.0
    _sun.rotation_euler = (fwd + Vector((0.2, 0, -0.5))).normalized().to_track_quat("-Z", "Y").to_euler()
    bpy.context.view_layer.update()


def marks(png):
    """MediaPipe's landmarks in a render, in its pixels (None: no face)."""
    js = png[:-4] + ".json"
    if os.path.exists(js):
        os.remove(js)
    subprocess.run([FACEFIT_PY, os.path.join(HERE, "face_fit.py"), "marks", png, js, "whole"], capture_output=True)
    return np.array(json.load(open(js))["points"]) if os.path.exists(js) else None


def to_world(px):
    """Pixels of the camera's picture as points on its plane, and its forward."""
    mwc = cam.matrix_world
    right, up, fwd = (np.array((mwc.to_3x3() @ Vector(a))[:]) for a in ((1, 0, 0), (0, 1, 0), (0, 0, -1)))
    res = sc.render.resolution_x
    u = (px[:, 0] / res - 0.5) * cam.data.ortho_scale
    v = (0.5 - px[:, 1] / res) * cam.data.ortho_scale
    return np.array(mwc.translation)[None] + u[:, None] * right + v[:, None] * up, fwd


def landmarks(objs, bvhs, V, name, fwds=((0, 1, 0),)):
    """MediaPipe's landmarks on a head (`objs` drawn, in clay, lit from in
    front: the same for hers and TRELLIS's, so the two are read alike),
    cast back onto its surfaces (`bvhs`): each landmark's point, and which
    surface it fell on (-1 none) with its face there."""
    for o in bpy.data.objects:
        if o.type == "MESH":
            o.hide_render = o not in objs
    mid = (V.min(0) + V.max(0)) / 2
    L2 = None
    for fwd in fwds:
        look(mid, fwd, np.ptp(V, 0).max() * 1.05)
        sc.render.filepath = os.path.join(WORK, name + "_find.png")
        bpy.ops.render.render(write_still=True)
        L2 = marks(sc.render.filepath)
        if L2 is not None:
            break
    if L2 is None:
        raise SystemExit("no face found on " + name)
    # (then closer: the face filling the picture, for MediaPipe's best)
    pts, f_ = to_world(L2)
    span = np.ptp(L2, 0).max() / sc.render.resolution_x * cam.data.ortho_scale
    look(pts.mean(0), fwd, span * 1.6)
    sc.render.filepath = os.path.join(WORK, name + "_front.png")
    bpy.ops.render.render(write_still=True)
    L2 = marks(sc.render.filepath)
    if L2 is None:
        raise SystemExit("no face found close up on " + name)
    pts, f_ = to_world(L2)
    out = np.full((len(L2), 3), np.nan)
    which = -np.ones(len(L2), int)
    face = -np.ones(len(L2), int)
    for i, p in enumerate(pts):
        best = None
        for k, bvh in enumerate(bvhs):
            r = bvh.ray_cast(Vector(p), Vector(f_), 10.0)
            if r[0] is not None and (best is None or r[3] < best[1][3]):
                best = (k, r)
        if best is not None:
            out[i], which[i], face[i] = best[1][0][:], best[0], best[1][2]
    # A ray through a gap (between her lips, past the rim of a lid) goes on
    # deep into her: such a landmark is brought to the surface in front,
    # where the camera saw it (the front-most of its points within 2 mm).
    # (Only round her openings: elsewhere a slope alone is that deep.)
    Vt = cKDTree(V[:, [0, 2]])
    deep = 0
    for i in [j for j in INNER_LIPS + EYE_A + EYE_B if which[j] >= 0]:
        near = Vt.query_ball_point(out[i, [0, 2]], 0.002)
        if near:
            k = near[int(np.argmin(V[near, 1]))]
            if out[i, 1] > V[k, 1] + 0.002:
                out[i], which[i], face[i] = V[k], -2, k
                deep += 1
    print("LANDMARKS on %s: %d of %d (%d through a gap, brought to the surface)" % (name, (which != -1).sum(), len(L2), deep))
    return out, which, face


# Her landmarks: her head as she is (her face's targets and sculpts), with
# her eyeballs in, so the rims of her lids are read where they lie.
DATA = os.path.join(bpy.utils.user_resource("EXTENSIONS"), ".user", "user_default", "mpfb", "data")
_eo = HumanService.add_mhclo_asset(os.path.join(DATA, "eyes", "high-poly", "high-poly.mhclo"), hm, asset_type="eyes",
                                   subdiv_levels=0, material_type="NONE", set_up_rigging=False, interpolate_weights=False,
                                   import_subrig=False, import_weights=False)
for mo in _eo.modifiers:
    mo.show_viewport = mo.show_render = False
bpy.context.view_layer.update()
_ee = _eo.evaluated_get(bpy.context.evaluated_depsgraph_get())
_em = _ee.to_mesh()
EV = np.array([(_ee.matrix_world @ v.co)[:] for v in _em.vertices])
_em.calc_loop_triangles()
EF = np.array([t.vertices[:] for t in _em.loop_triangles])
_ee.to_mesh_clear()
bpy.data.objects.remove(_eo)
her_ob = mesh_object("her", P, F)
eyes_ob = mesh_object("her_eyes", EV, EF)
HBVH = BVHTree.FromPolygons([tuple(p) for p in P], F.tolist())
EBVH = BVHTree.FromPolygons([tuple(p) for p in EV], EF.tolist())
_sub = np.where(BODY & (P[:, 2] > P[BODY, 2].max() - 0.32))[0]
L0, _w0, _f0 = landmarks([her_ob, eyes_ob], [HBVH, EBVH], P[_sub], "her")
# Each landmark on her skin anchored there (its face and where in it, or
# the point of her it was brought to), to move as her skin does.
hit = (_w0 == 0) | (_w0 == -2)
tri = np.zeros((len(L0), 3), int)
bary = np.zeros((len(L0), 3))
for i in np.where(_w0 == -2)[0]:
    tri[i], bary[i] = [_sub[_f0[i]]] * 3, [1.0, 0.0, 0.0]
for i in np.where(_w0 == 0)[0]:
    a_, b_, c_ = P[F[_f0[i]]]
    v0, v1, v2 = b_ - a_, c_ - a_, L0[i] - a_
    d00, d01, d11, d20, d21 = v0 @ v0, v0 @ v1, v1 @ v1, v2 @ v0, v2 @ v1
    den = d00 * d11 - d01 * d01
    bv, bw = (d11 * d20 - d01 * d21) / den, (d00 * d21 - d01 * d20) / den
    tri[i], bary[i] = F[_f0[i]], [1 - bv - bw, bv, bw]
hit[IRIS] = False
her_ob.hide_render = eyes_ob.hide_render = True

TBVH = BVHTree.FromObject(shape_ob, bpy.context.evaluated_depsgraph_get())
Lt, _wt, _ = landmarks([shape_ob], [TBVH], TV, "trellis", fwds=((0, 1, 0), (0, -1, 0), (1, 0, 0), (-1, 0, 0)))
ok_t = np.isfinite(Lt).all(1)
print("LANDMARKS: her lips and nose %d on her skin; her eyes' rims %d on her eyeballs" % (hit[LIPS + NOSE].sum(), (_w0[EYE_A + EYE_B] == 1).sum()))

# ------------------------------------------------------------ 2. placed --
n_l = min(len(L0), len(Lt))
wc = np.zeros(n_l)
wc[[i for i in CORE if i < n_l]] = 1.0
ok0 = np.isfinite(L0).all(1)
wc *= ok0[:n_l] & ok_t[:n_l]
use = wc > 0
s_, R_, t_ = umeyama(Lt[:n_l][use], L0[:n_l][use], wc[use])
TVh = s_ * TV @ R_.T + t_
Lt = s_ * Lt @ R_.T + t_
_turn = math.degrees(math.acos(min(1, (np.trace(R_) - 1) / 2)))
print("PLACED: scaled %.4f, turned %.1f deg; landmarks %.1f mm from hers (rms, eyes nose mouth)" % (
    s_, _turn, 1000 * np.sqrt((wc[use] * ((Lt[:n_l][use] - L0[:n_l][use]) ** 2).sum(1)).sum() / wc[use].sum())))
for nm, g in (("oval", OVAL), ("lips", LIPS), ("eyes", EYE_A + EYE_B), ("brows", BROWS), ("nose", NOSE)):
    g = [i for i in g if i < n_l and ok0[i] and ok_t[i]]
    dd = (Lt - L0)[g]
    print("MOVES %-6s %.1f mm (rms): across %.1f, up %.1f, in depth %.1f" % (
        nm, 1000 * np.sqrt((dd ** 2).sum(1).mean()), 1000 * np.sqrt((dd[:, 0] ** 2).mean()), 1000 * np.sqrt((dd[:, 2] ** 2).mean()),
        1000 * np.sqrt((dd[:, 1] ** 2).mean())))
shape_ob.data.vertices.foreach_set("co", TVh.ravel())
shape_ob.data.update()
TBVH = BVHTree.FromObject(shape_ob, bpy.context.evaluated_depsgraph_get())
TTREE = cKDTree(TVh)

# Where TRELLIS's head is hair, not skin (its colours: unlike her cheeks'
# and forehead's): her skull lies under it, a little in (HAIR_DEPTH).
HAIR_DEPTH = float(os.environ.get("WRAP_HAIR_DEPTH", "0.005"))
_ca = paint_ob.data.color_attributes[0]
_cols = np.zeros(len(_ca.data) * 4)
_ca.data.foreach_get("color", _cols)
_cols = _cols.reshape(-1, 4)[:, :3]
if _ca.domain == "CORNER":
    _vi = np.zeros(len(paint_ob.data.loops), int)
    paint_ob.data.loops.foreach_get("vertex_index", _vi)
    _acc = np.zeros((len(TV), 3))
    np.add.at(_acc, _vi, _cols)
    _cnt = np.bincount(_vi, minlength=len(TV))
    _cols = _acc / np.maximum(_cnt, 1)[:, None]
_skin_at = [i for i in (50, 280, 151, 108, 337, 9, 205, 425) if i < n_l and ok_t[i]]
_skin = np.median(_cols[TTREE.query(Lt[_skin_at])[1]], 0)
_lum = _cols @ [0.3, 0.59, 0.11]
_chroma = _cols / (_cols.sum(1)[:, None] + 1e-6)
_sk_ch = _skin / _skin.sum()
_d = np.linalg.norm(_chroma - _sk_ch, axis=1) * 6 + np.abs(np.log((_lum + 0.01) / (_skin @ [0.3, 0.59, 0.11] + 0.01)))
HAIR_T = float(os.environ.get("WRAP_HAIR_T", "0.6"))
HAIR = (_d > HAIR_T).astype(float)
# (smoothed along its surface, a few millimetres; never her brows nor anything below them in front)
_ed = np.zeros(len(paint_ob.data.edges) * 2, int)
paint_ob.data.edges.foreach_get("vertices", _ed)
_ed = _ed.reshape(-1, 2)
_TA = sp.coo_matrix((np.ones(len(_ed)), (_ed[:, 0], _ed[:, 1])), shape=(len(TV), len(TV))).tocsr()
_TA = _TA + _TA.T + sp.identity(len(TV))
_TA = sp.diags(1 / np.asarray(_TA.sum(1)).ravel()) @ _TA
for _ in range(12):
    HAIR = _TA @ HAIR
_brow_zone = (TVh[:, 2] < L0[BROWS, 2].max() + 0.012) & (TVh[:, 1] < L0[[234, 454], 1].mean())
HAIR[_brow_zone] = 0.0
print("HAIR: %.0f%% of TRELLIS's head (skin %s)" % (100 * (HAIR > 0.5).mean(), np.round(_skin, 3)))

# ------------------------------------------------------------ 3. laid on it --
chin_z = L0[152, 2]
brow_z = L0[BROWS, 2].max()
region = BODY & (P[:, 2] > chin_z - 0.09)
idx = np.where(region)[0]
n = len(idx)
loc = -np.ones(NV, int)
loc[idx] = np.arange(n)
Fr = F[region[F].all(1)]
e = loc[np.vstack([Fr[:, [0, 1]], Fr[:, [1, 2]], Fr[:, [2, 0]]])]
Adj = sp.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)).tocsr()
Adj = ((Adj + Adj.T) > 0).astype(float)
Lap = sp.eye(n) - sp.diags(1 / np.maximum(np.asarray(Adj.sum(1)).ravel(), 1)) @ Adj
LTL = (Lap.T @ Lap).tocsr()
ear_x = np.abs(L0[[234, 454], 0]).max()
ear_y = L0[[234, 454], 1].mean()
ear_top = L0[[234, 454], 2].mean() + 0.025
print("EARS (her face's outline by them): %.1f mm out, %.1f mm back, %.1f mm up (over her eyes' middle)" % (
    1000 * ear_x, 1000 * ear_y, 1000 * (ear_top - 0.025 - L0[EYE_A + EYE_B, 2].mean())))
Pi = P[idx]
# Held: her neck below her jaw (her body's, and what she wears there), and
# her nape behind her ears (where TRELLIS's head had its hair tied).
hold = np.max([smooth01((chin_z - 0.035 - Pi[:, 2]) / 0.04),
               smooth01((Pi[:, 1] - ear_y - 0.02) / 0.03) * smooth01((ear_top - 0.03 - Pi[:, 2]) / 0.03)], 0)
# Her ears are carried along (bent as little as can be), not laid on its ears.
ears = smooth01((np.abs(Pi[:, 0]) - ear_x + 0.004) / 0.006) * smooth01((Pi[:, 1] - ear_y + 0.016) / 0.008) \
    * smooth01((Pi[:, 2] - L0[2, 2] + 0.02) / 0.008) * smooth01((ear_top + 0.012 - Pi[:, 2]) / 0.008)
# Her eyes: each eye's opening made the shape of TRELLIS's (an affine map,
# across her face, of her lids' landmarks onto its; moved in depth as its
# lids lie), her lids and socket carried with it, her eyeball moved whole
# (4). Her mouth's inside only carried along.
eye_c, eye_map = [], []
goal = np.zeros((n, 3))
wgoal = np.zeros(n)
for ring in (EYE_A, EYE_B):
    sx = np.sign(L0[ring, 0].mean())
    _ev = (member["helper-l-eye"] | member["helper-r-eye"]) & (np.sign(P[:, 0]) == sx)
    c0 = P[_ev].mean(0)
    r0 = np.linalg.norm(P[_ev] - c0, axis=1).mean()
    rg = [i for i in ring if ok_t[i] and ok0[i]]
    src, dst = L0[rg][:, [0, 2]], Lt[rg][:, [0, 2]]
    Xa = np.c_[src, np.ones(len(src))]
    M = np.linalg.lstsq(Xa, dst, rcond=None)[0]                       # (3 x 2: dst = [x z 1] M)
    dy = float(np.median(Lt[rg, 1] - L0[rg, 1]))
    eye_c.append((c0, r0))
    eye_map.append((M, dy))

    def mapped(Q, M=M, dy=dy):
        out = Q.copy()
        out[:, [0, 2]] = np.c_[Q[:, [0, 2]], np.ones(len(Q))] @ M
        out[:, 1] += dy
        return out
    dist = np.linalg.norm(Pi - c0, axis=1) - r0
    w = 1 - smooth01((dist - 0.004) / 0.009)
    mine = w > wgoal
    goal[mine] = (mapped(Pi) - Pi)[mine]
    wgoal = np.maximum(wgoal, w)
    A2 = M[:2].T
    print("EYE at x %+.3f: its opening %.2f wide and %.2f tall as hers, tilted %+.1f deg; %.1f mm %s" % (
        sx * 0.03, np.linalg.norm(A2[:, 0]), np.linalg.norm(A2[:, 1]), math.degrees(math.atan2(A2[1, 0], A2[0, 0])),
        1000 * abs(dy), "deeper" if dy > 0 else "further out"))
near_eye = np.min([np.linalg.norm(Pi - c, axis=1) - r for c, r in eye_c], 0)
mouth_in = inside(L0[INNER_LIPS][:, [0, 2]], Pi[:, [0, 2]]) & (Pi[:, 1] > L0[INNER_LIPS, 1].min() + 0.002)
wsurf = (1 - hold) * (1 - ears) * smooth01((near_eye - 0.008) / 0.006) * ~mouth_in
# Landmarks: her nose's and lips' (her eyes have their own map; her face's
# outline and brows are left to the surface: MediaPipe reads the one off a
# soft edge, and TRELLIS's brows are hair standing off its skin).
lm_w = np.zeros(n_l)
lm_w[[i for i in NOSE if i < n_l]] = 1.2
lm_w[[i for i in LIPS if i < n_l]] = 1.6
rows = np.arange(n_l)[hit[:n_l] & ok_t[:n_l] & (lm_w > 0)]
Bm = sp.coo_matrix((bary[rows].ravel(), (np.repeat(np.arange(len(rows)), 3), loc[tri[rows]].ravel())), shape=(len(rows), n)).tocsr()
wa = lm_w[rows]
Lgoal = Lt[rows]
L0r = (P[tri[rows]] * bary[rows][:, :, None]).sum(1)
D = np.zeros((n, 3))
K_LM, K_HOLD, K_EYE = 3.0, 20.0, 30.0
I3 = sp.identity(3, format="csr")
cranium = Pi[:, 2] > brow_z + 0.02


def solve(Q, Nq, ws, k_bend):
    """Her points' moves: onto the surface (point to plane, and a little
    point to point), landmarks to landmarks, her eyes' openings to theirs,
    bent as little as can be, held where held."""
    # (unknowns: every point's x, then every point's y, then z)
    Nc = sp.hstack([sp.diags(Nq[:, k]) for k in range(3)]).tocsr()          # (n x 3n: each point's move along its normal)
    r = ((Q - Pi) * Nq).sum(1)
    A = Nc.T @ sp.diags(ws) @ Nc + 0.05 * sp.kron(I3, sp.diags(ws)) + K_LM * sp.kron(I3, Bm.T @ sp.diags(wa) @ Bm) \
        + k_bend * sp.kron(I3, LTL) + K_HOLD * sp.kron(I3, sp.diags(hold)) + K_EYE * sp.kron(I3, sp.diags(wgoal)) \
        + 1e-8 * sp.identity(3 * n)
    b = Nc.T @ (ws * r) + 0.05 * np.concatenate([ws * (Q - Pi)[:, k] for k in range(3)]) \
        + K_LM * np.concatenate([Bm.T @ (wa * (Lgoal - L0r)[:, k]) for k in range(3)]) \
        + K_EYE * np.concatenate([wgoal * goal[:, k] for k in range(3)])
    x = spl.spsolve(A.tocsc(), b)
    return x.reshape(3, n).T


Floc = loc[Fr]
flip = None
for it, k_bend in enumerate((60.0, 25.0, 10.0, 5.0, 2.5, 1.5, 1.0, 0.7)):
    X = Pi + D
    Nx = vertex_normals(X, Floc)
    if (Nx[:, 1][(wsurf > 0.5) & ~cranium] < 0).mean() < 0.5:
        Nx = -Nx
    Q = X.copy()
    Nq = Nx.copy()
    ws = wsurf.copy()
    # (along her normal, either way; over her cranium, which may be far
    # from its (MakeHuman's is tall), the nearest of it if no ray meets it)
    reach = np.where(cranium, 0.06, 0.015)
    cand = []
    for i in np.where(wsurf > 0.01)[0]:
        best = None
        for sgn in (1.0, -1.0):
            hit_ = TBVH.ray_cast(Vector(X[i]), Vector(sgn * Nx[i]), float(reach[i]))
            if hit_[0] is not None and (best is None or hit_[3] < best[3]):
                best = hit_
        if best is None and cranium[i]:
            best = TBVH.find_nearest(Vector(X[i]), 0.06)
            best = best if best[0] is not None else None
        cand.append((i, best))
    if flip is None:
        # (TRELLIS's faces may be wound inward: its normals turned to face out as hers do)
        flip = np.median([np.dot(b_[1][:], Nx[i]) for i, b_ in cand if b_ is not None]) < 0
        print("TRELLIS's normals %s" % ("turned out (they were wound inward)" if flip else "face out"))
    for i, b_ in cand:
        if b_ is None:
            ws[i] = 0
            continue
        nq = -np.array(b_[1][:]) if flip else np.array(b_[1][:])
        # (a remeshed shell can be two surfaces back to back, a fraction of
        # a millimetre apart: either will do, turned to face as hers does)
        nq *= np.sign(np.dot(nq, Nx[i])) or 1.0
        if np.dot(nq, Nx[i]) < (0.6 if it < 3 else 0.3):     # (a surface facing another way: not hers to lie on)
            ws[i] = 0
            continue
        q = np.array(b_[0][:])
        hq = HAIR[TTREE.query(q)[1]]
        Q[i], Nq[i] = q - nq * HAIR_DEPTH * hq, nq
    if it == 0:
        _cr = cranium & (wsurf > 0.01)
        print("  cranium: %d of her points to lay, %d met its surface" % (_cr.sum(), (_cr & (ws > 0.01)).sum()))
        if os.environ.get("WRAP_DEBUG"):
            _dbg = [(i, -1.0 if b_ is None else float(np.dot((-1 if flip else 1) * np.array(b_[1][:]), Nx[i])),
                     -1.0 if b_ is None else float(np.linalg.norm(np.array(b_[0][:]) - X[i]))) for i, b_ in cand if cranium[i]]
            np.savez(os.environ["WRAP_DEBUG"], dbg=np.array(_dbg), X=X, Nx=Nx, cranium=cranium, wsurf=wsurf)
    D = solve(Q, Nq, ws, k_bend)
    res = (((Pi + D - Q) * Nq).sum(1))[ws > 0.5]
    print("ICP %d (bend %.1f): %d of her points on its surface, %.2f mm off it (rms), %.2f the most; moved up to %.1f mm" % (
        it, k_bend, (ws > 0.5).sum(), 1000 * np.sqrt((res ** 2).mean()), 1000 * np.abs(res).max(), 1000 * np.linalg.norm(D, axis=1).max()))
got = Bm @ (Pi + D)
print("LANDMARKS within %.2f mm (rms)" % (1000 * np.sqrt(((got - Lgoal) ** 2).sum(1).mean())))
DD = np.zeros((NV, 3))
DD[idx] = D


# ------------------------------------------------------------- 4. eyes --
eyes_all = member["helper-l-eye"] | member["helper-r-eye"]
for (c0, r0), (M, dy), ring in zip(eye_c, eye_map, (EYE_A, EYE_B)):
    sx = np.sign(L0[ring, 0].mean())
    eye = eyes_all & (np.sign(P[:, 0]) == sx)
    # (her eyeball moved whole as the map moves its middle: never stretched)
    c1 = c0.copy()
    c1[[0, 2]] = np.r_[c0[[0, 2]], 1.0] @ M
    c1[1] += dy
    shift = c1 - c0
    DD[eye] = shift
    for jn in ("joint-l-eye", "joint-r-eye", "joint-l-eye-target", "joint-r-eye-target"):
        j = member.get(jn, np.zeros(NV, bool)) & (np.sign(P[:, 0]) == sx)
        DD[j] = shift
    # (and every point of her lids and socket as far off it as it was, the
    # nearer the more so: her lids lie on her eyeball)
    rad = np.linalg.norm(P - c0, axis=1)
    lid = BODY & (rad < r0 + 0.007)
    off0 = rad[lid] - r0
    Ql = P[lid] + DD[lid]
    u = (Ql - c1) / np.linalg.norm(Ql - c1, axis=1)[:, None]
    lay = c1 + u * (r0 + off0)[:, None]
    t = 1 - smooth01((off0 - 0.003) / 0.004)
    DD[lid] += (lay - Ql) * t[:, None]
    print("EYEBALL at x %+.3f: moved %.1f mm (%.1f deeper); %d points of lid and socket laid on it"
          % (sx * 0.03, 1000 * np.linalg.norm(shift), 1000 * shift[1], lid.sum()))
body_pts = np.where(BODY)[0]
tree = cKDTree(P[body_pts])
for gname in ("helper-l-eyelashes-1", "helper-l-eyelashes-2", "helper-r-eyelashes-1", "helper-r-eyelashes-2", "helper-hair",
              "joint-mouth", "joint-jaw", "joint-head", "joint-head-2", "joint-l-upperlid", "joint-l-lowerlid", "joint-r-upperlid",
              "joint-r-lowerlid"):
    g = member.get(gname)
    if g is None or not g.any():
        continue
    _, nn = tree.query(P[g], k=4)
    DD[g] = DD[body_pts[nn]].mean(1)
_mouth = DD[tri[INNER_LIPS]].mean((0, 1))
for gname in ("helper-upper-teeth", "helper-lower-teeth", "helper-tongue"):
    DD[member[gname]] = _mouth

# ------------------------------------------------------- 5. symmetrical --
_mir = cKDTree(P).query(P * [-1, 1, 1])
pair = np.where(_mir[0] < 2e-4, _mir[1], np.arange(NV))
DD = 0.5 * (DD + DD[pair] * [-1, 1, 1])
print("SYMMETRY: %d of %d points paired across her middle" % ((_mir[0] < 2e-4).sum(), NV))

# ---- written as a MakeHuman target: each moved point in MakeHuman's own
# frame (y up, z toward her front, decimetres).
dl_ = DD @ np.linalg.inv(MW[:3, :3]).T / 0.1
moved = np.where(np.linalg.norm(DD, axis=1) > 1e-5)[0]
os.makedirs(os.path.dirname(OUT), exist_ok=True)
lines = ["# face_wrap.py: her face laid on TRELLIS's head %s" % os.path.basename(os.path.dirname(SHAPE))]
lines += ["%d %.6f %.6f %.6f" % (i, dl_[i, 0], dl_[i, 2], -dl_[i, 1]) for i in moved]
with (gzip.open(OUT, "wt") if OUT.endswith(".gz") else open(OUT, "w")) as f:
    f.write("\n".join(lines) + "\n")
print("TARGET", OUT, len(moved), "points, %.1f mm the most" % (1000 * np.linalg.norm(DD, axis=1).max()))
np.savez(os.path.join(WORK, "wrap.npz"), P=P, D=DD, L0=L0, Lt=Lt, hit=hit, ok_t=ok_t)
# Where its hair begins, over her eyes, round the front of her head (for
# face_shapes.HAIRLINE: in MakeHuman's size, before heroine_head.py scales her head).
eye_z = L0[EYE_A + EYE_B, 2].mean()
_c = np.array([0.0, L0[[234, 454], 1].mean() + 0.02, eye_z + 0.03])
_th = np.degrees(np.abs(np.arctan2(TVh[:, 0] - _c[0], -(TVh[:, 1] - _c[1]))))
_up = (TVh[:, 2] > eye_z - 0.04) & (np.linalg.norm(TVh - _c, axis=1) > 0.05)
line = {}
for a in (0, 10, 20, 30, 40, 50, 60, 70, 80):
    m = _up & (np.abs(_th - a) < 4) & (HAIR > 0.5)
    if m.sum() > 50:
        line[a] = float(np.percentile(TVh[m, 2], 2) - eye_z)
print("HAIRLINE over her eyes (its hair's lowest edge, by degrees from her front): " +
      ", ".join("%d: %.3f" % (a, h) for a, h in line.items()))
json.dump(line, open(os.path.join(WORK, "hairline.json"), "w"))

# ---- check: her before and after in clay, and TRELLIS's head as placed,
# from in front, three-quarters and the side.
if CHECK:
    paint_ob.hide_render = True
    kb = hm.shape_key_add(name="portrait", from_mix=False)
    basek = np.zeros(NV * 3)
    hm.data.shape_keys.reference_key.data.foreach_get("co", basek)
    # (her points as evaluated, her face's targets on: the key lays the
    # portrait's moves over all of them)
    kb.data.foreach_set("co", (basek + (DD @ np.linalg.inv(MW[:3, :3]).T).ravel()).astype(np.float32))
    grey = bpy.data.materials.new("clay")
    grey.use_nodes = True
    grey.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.62, 0.52, 0.47, 1)
    grey.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.55
    hm.data.materials.clear()
    hm.data.materials.append(grey)
    shape_ob.data.materials.clear()
    shape_ob.data.materials.append(grey)
    for mo in hm.modifiers:
        mo.show_viewport = mo.show_render = mo.type == "MASK"
    sc.view_settings.view_transform = "AgX"
    sc.render.resolution_x = sc.render.resolution_y = 768
    centre = Vector((0.0, float(L0[hit, 1].mean()), float(L0[[168, 152], 2].mean() + 0.02)))
    for which in ("before", "after", "trellis"):
        hm.hide_render = which == "trellis"
        shape_ob.hide_render = which != "trellis"
        kb.value = 1.0 if which == "after" else 0.0
        for ang in (0.0, 35.0, 80.0):
            a_ = math.radians(ang)
            look(centre, (-math.sin(a_), math.cos(a_), 0), 0.26)
            sc.render.filepath = os.path.join(CHECK, "%s_%02d.png" % (which, ang))
            bpy.ops.render.render(write_still=True)
    # (where it was read as hair: red)
    shape_ob.hide_render = hm.hide_render = True
    paint_ob.hide_render = False
    paint_ob.data.vertices.foreach_set("co", TVh.ravel())
    paint_ob.data.update()
    _ha = paint_ob.data.color_attributes.new("hairmask", "FLOAT_COLOR", "POINT")
    _ha.data.foreach_set("color", np.c_[0.3 + 0.7 * HAIR, 0.3 * (1 - HAIR) + 0.1, 0.3 * (1 - HAIR) + 0.1, np.ones(len(HAIR))].ravel())
    _attr.layer_name = "hairmask"
    for ang in (0.0, 80.0):
        a_ = math.radians(ang)
        look(centre, (-math.sin(a_), math.cos(a_), 0), 0.30)
        sc.render.filepath = os.path.join(CHECK, "hair_%02d.png" % ang)
        bpy.ops.render.render(write_still=True)
    print("CHECK", CHECK)
