"""The heroine's face, tried out: MakeHuman's woman as heroine_head.py makes
her (its MACROS and BUILD), shaped by any targets at any weights, rendered
from the front, three-quarters and the side; and the points of her face
that MediaPipe's landmarks fall on, with how each target moves them (for
tools/assets/face_fit.py to fit her face to a reference's).

    blender -b --python tools/assets/face_lab.py -- render <faces.json> <out dir> [views]
    blender -b --python tools/assets/face_lab.py -- anchor <landmarks.json> <out.npz> <targets.json> [<faces.json> <name>]

faces.json: {name: {target: weight, ...}, ...}, every weight over her FACE
(a "-" before a name: without FACE, MakeHuman's woman as she is). Targets
are MakeHuman's (X- both sides), or face_shapes.py's sculpts by name.
landmarks.json (face_fit.py's): the landmarks in the front render, in
pixels, and that render's camera. The npz holds, for each landmark, its
point on her face (the triangle and where in it), its place as she is, and
how every target moves it.
"""
import json
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import face_shapes as fs  # noqa: E402

from bl_ext.user_default.mpfb.services.humanservice import HumanService  # noqa: E402
from bl_ext.user_default.mpfb.services.targetservice import TargetService  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:]
MODE = ARGS[0]
DATA = os.path.join(bpy.utils.user_resource("EXTENSIONS"), ".user", "user_default", "mpfb", "data")
RES = 1024
SCALE = 0.30                         # metres across a render
VIEWS = {"front": 0.0, "q": 32.0, "side": 90.0}

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
hm = HumanService.create_human(mask_helpers=True, detailed_helpers=True, extra_vertex_groups=True, feet_on_ground=True,
                               scale=0.1, macro_detail_dict=fs.MACROS)
TARGET = fs.target_paths()
for t, v in {**fs.FACE, **fs.BUILD}.items():
    if t in fs.SCULPTS:                              # (her face's sculpts: set_face lays them)
        continue
    for n in fs.sides([t]):
        TargetService.load_target(hm, TARGET[n], weight=v, name="face_" + n)
SK = {}
PROXIES = []


def key(name):
    """A target's shape key (made at nothing the first time it is asked for)."""
    if name not in SK:
        SK[name] = TargetService.load_target(hm, TARGET[name], weight=0.0, name="sk_" + name).name
    return hm.data.shape_keys.key_blocks[SK[name]]


for mo in hm.modifiers:
    mo.show_viewport = mo.show_render = mo.type == "MASK"
MW = np.array(hm.matrix_world)
_body = hm.vertex_groups["body"].index
INBODY = np.array([any(g.group == _body for g in v.groups) for v in hm.data.vertices])


def positions():
    """Her points as she stands (every shape key at its weight, no
    modifiers), in the world."""
    # (the helpers' mask off first: every point, numbered as the mesh numbers them)
    for mo in hm.modifiers:
        mo.show_viewport = False
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    e = hm.evaluated_get(dg)
    m = e.to_mesh()
    V = np.array([v.co[:] for v in m.vertices])
    e.to_mesh_clear()
    assert len(V) == len(hm.data.vertices)
    for mo in hm.modifiers:
        mo.show_viewport = mo.type == "MASK"
    bpy.context.view_layer.update()
    return V @ MW[:3, :3].T + MW[:3, 3]


REST = None


def delta(name):
    """How a target (or a sculpt) moves each of her points, in the world."""
    global REST
    if name in fs.SCULPTS:
        if REST is None:
            REST = positions()
        return fs.SCULPTS[name](REST, fs.anatomy(REST))
    kb = key(name)
    co = np.zeros(len(kb.data) * 3)
    kb.data.foreach_get("co", co)
    ref = np.zeros(len(kb.data) * 3)
    hm.data.shape_keys.reference_key.data.foreach_get("co", ref)
    return (co - ref).reshape(-1, 3) @ MW[:3, :3].T


def set_face(weights):
    """Every lab key to nothing, then these (FACE's own, if not left out, under them)."""
    for kb in hm.data.shape_keys.key_blocks[1:]:
        if kb.name.startswith("sk_") or kb.name.startswith("sculpt_"):
            kb.value = 0.0
    bare = weights.get("-", False)
    for kb in hm.data.shape_keys.key_blocks[1:]:
        if kb.name.startswith("face_"):
            t = kb.name[5:]
            kb.value = 0.0 if bare and t not in fs.sides(list(fs.BUILD)) else fs.weight_of(t)
    weights = dict(weights)
    if not bare:
        for t, v in fs.FACE.items():
            if t in fs.SCULPTS:
                weights[t] = weights.get(t, 0.0) + v
    for t, v in weights.items():
        if t == "-":
            continue
        for n in fs.sides([t]):
            if n in fs.SCULPTS:
                kb = hm.data.shape_keys.key_blocks.get("sculpt_" + n)
                if kb is None:
                    kb = hm.shape_key_add(name="sculpt_" + n, from_mix=False)
                    base = np.zeros(len(kb.data) * 3)
                    hm.data.shape_keys.reference_key.data.foreach_get("co", base)
                    d = delta(n) @ np.linalg.inv(MW[:3, :3]).T
                    kb.data.foreach_set("co", (base + d.ravel()).astype(np.float32))
                    kb.slider_min, kb.slider_max = -3, 3
                kb.value = v
            else:
                kb = key(n)
                kb.slider_min, kb.slider_max = -3, 3
                kb.value = v
    bpy.context.view_layer.update()
    if PROXIES:
        follow()


# ------------------------------------------------------------ the look --
def image_material(name, path, alpha=False, rough=0.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(path, check_existing=True)
    nt.links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
    if alpha:
        nt.links.new(t.outputs["Alpha"], bsdf.inputs["Alpha"])
        m.surface_render_method = "DITHERED"
    bsdf.inputs["Roughness"].default_value = rough
    return m


def mhmat_texture(mhmat):
    tex = next(line.split()[1] for line in open(mhmat, encoding="utf-8-sig") if line.startswith("diffuseTexture"))
    return os.path.join(os.path.dirname(mhmat), tex)


def asset_mhmat(kind, name):
    d = os.path.join(DATA, kind, name)
    return next(os.path.join(d, f) for f in os.listdir(d) if f.endswith(".mhmat"))


hm.data.materials.clear()
skin_dir = os.path.join(DATA, *fs.SKIN)
hm.data.materials.append(image_material("skin", mhmat_texture(next(os.path.join(skin_dir, f) for f in os.listdir(skin_dir)
                                                                     if f.endswith(".mhmat"))), rough=0.45))
from bl_ext.user_default.mpfb.entities.clothes.mhclo import Mhclo  # noqa: E402

# Her eyes, brows and lashes, each with its fitting (MakeHuman's: each of its
# points rides on three of hers), so they follow her face as it is shaped:
# fitted once, to her face as loaded, they would stay where that face had
# them and a face judged with them would be judged wrongly.
PROXIES = []
for kind, name in fs.PARTS:
    if kind in ("teeth", "tongue"):
        continue
    o = HumanService.add_mhclo_asset(os.path.join(DATA, kind, name, name + ".mhclo"), hm, asset_type=kind, subdiv_levels=0,
                                     material_type="NONE", set_up_rigging=False, interpolate_weights=False, import_subrig=False,
                                     import_weights=False)
    mhmat = os.path.join(DATA, "eyes", "materials", fs.EYES + ".mhmat") if kind == "eyes" else asset_mhmat(kind, name)
    o.data.materials.clear()
    o.data.materials.append(image_material(kind, mhmat_texture(mhmat), alpha=True, rough=0.1 if kind == "eyes" else 0.8))
    for mo in o.modifiers:
        mo.show_viewport = mo.show_render = False
    mc = Mhclo()
    mc.load(os.path.join(DATA, kind, name, name + ".mhclo"))
    n = len(o.data.vertices)
    vi = np.zeros((n, 3), int)
    vw = np.zeros((n, 3))
    for i in range(n):
        if i in mc.verts:
            vi[i], vw[i] = mc.verts[i]["verts"], mc.verts[i]["weights"]
    co0 = np.zeros(n * 3)
    o.data.vertices.foreach_get("co", co0)
    PROXIES.append((o, vi, vw, co0.reshape(-1, 3)))
FITTED = None


def follow():
    """The proxies moved as her points have moved since they were fitted."""
    global FITTED
    P = positions()
    if FITTED is None:
        FITTED = P
    d = P - FITTED
    for o, vi, vw, co0 in PROXIES:
        dw = (d[vi] * vw[:, :, None]).sum(1)
        inv = np.linalg.inv(np.array(o.matrix_world)[:3, :3])
        o.data.vertices.foreach_set("co", (co0 + dw @ inv.T).ravel().astype(np.float32))
        o.data.update()


follow()

sc = bpy.context.scene
for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
    try:
        sc.render.engine = eng
        break
    except TypeError:
        pass
sc.render.resolution_x = sc.render.resolution_y = RES
sc.render.film_transparent = False
sc.view_settings.view_transform = "AgX"
sc.world = bpy.data.worlds.new("w")
sc.world.use_nodes = True
sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.32, 0.31, 0.30, 1)
sc.world.node_tree.nodes["Background"].inputs[1].default_value = 0.6
for rot, energy in (((math.radians(50), 0, math.radians(-30)), 3.0), ((math.radians(70), 0, math.radians(140)), 1.2),
                    ((math.radians(80), 0, math.radians(30)), 1.0)):
    ld = bpy.data.lights.new("sun", "SUN")
    ld.energy = energy
    ld.angle = math.radians(12)
    lo = bpy.data.objects.new("sun", ld)
    lo.rotation_euler = rot
    sc.collection.objects.link(lo)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.type = "ORTHO"
cam.data.ortho_scale = SCALE


def head_centre():
    P = positions()
    eyes = P[INBODY & (P[:, 2] > P[INBODY, 2].max() - 0.25)]
    top = P[INBODY, 2].max()
    return np.array([0.0, eyes[:, 1].mean() * 0 + P[INBODY & (P[:, 2] > top - 0.25), 1].mean(), top - 0.115])


def place_camera(ang, centre):
    a = math.radians(ang)
    c = Vector(centre)
    cam.location = c + Vector((math.sin(a), -math.cos(a), 0)) * 2.0
    cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.view_layer.update()                      # (its matrix as placed, not as it last was)
    return {"angle": ang, "centre": list(centre), "scale": SCALE, "res": RES,
            "matrix": [list(r) for r in cam.matrix_world]}


def render(path, ang, centre):
    info = place_camera(ang, centre)
    bpy.context.view_layer.update()
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return info


if MODE == "render":
    faces = json.load(open(ARGS[1], encoding="utf-8-sig"))
    out = os.path.abspath(ARGS[2])
    views = ARGS[3].split(",") if len(ARGS) > 3 else list(VIEWS)
    os.makedirs(out, exist_ok=True)
    set_face({})
    centre = head_centre()
    cams = {}
    for name, w in faces.items():
        set_face(w)
        for v in views:
            ang = float(v) if v not in VIEWS else VIEWS[v]
            cams[f"{name}_{v}"] = render(os.path.join(out, f"{name}_{v}.png"), ang, centre)
    json.dump(cams, open(os.path.join(out, "_cams.json"), "w"), indent=1)

elif MODE == "anchor":
    lm = json.load(open(ARGS[1], encoding="utf-8-sig"))
    out = os.path.abspath(ARGS[2])
    targets = json.load(open(ARGS[3], encoding="utf-8-sig")) if len(ARGS) > 3 else []
    # (the face the landmarks were read off: as faces.json gives one)
    set_face(json.load(open(ARGS[4], encoding="utf-8-sig"))[ARGS[5]] if len(ARGS) > 5 else {})
    P = positions()
    me = hm.data
    me.calc_loop_triangles()
    T = np.array([t.vertices[:] for t in me.loop_triangles])
    T = T[INBODY[T].all(1)]
    bvh = BVHTree.FromPolygons([tuple(p) for p in P], T.tolist())
    M = np.array(lm["camera"]["matrix"])
    res, scale = lm["camera"]["res"], lm["camera"]["scale"]
    fwd = -M[:3, 2]
    tri, bary, hit = [], [], []
    for x, y in lm["points"]:
        # (an orthographic camera: a ray from the image's point straight ahead)
        u, v = (x / res - 0.5) * scale, (0.5 - y / res) * scale
        o = M[:3, 3] + M[:3, 0] * u + M[:3, 1] * v
        loc, nor, idx, dist = bvh.ray_cast(Vector(o), Vector(fwd), 5.0)
        if loc is None:
            tri.append([0, 0, 0]), bary.append([1, 0, 0]), hit.append(False)
            continue
        a, b, c = (P[i] for i in T[idx])
        p = np.array(loc[:])
        m = np.array([b - a, c - a]).T
        st = np.linalg.lstsq(m, p - a, rcond=None)[0]
        tri.append(T[idx].tolist()), bary.append([1 - st.sum(), st[0], st[1]]), hit.append(True)
    tri, bary = np.array(tri), np.array(bary)
    D = np.zeros((len(targets), len(tri), 3), np.float32)
    for j, t in enumerate(targets):
        d = sum(delta(n) for n in fs.sides([t])) if t.startswith("X-") else delta(t)
        D[j] = (d[tri] * bary[:, :, None]).sum(1)
    np.savez(out, tri=tri, bary=bary, hit=np.array(hit), P0=(P[tri] * bary[:, :, None]).sum(1), D=D,
             targets=np.array(targets))
    print("ANCHORS", int(np.sum(hit)), "of", len(hit), "landmarks on her face;", len(targets), "targets")
