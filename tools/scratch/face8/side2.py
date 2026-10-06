"""Her throat and chest in white clay under a light from her left (as the portraits' key), EEVEE.
blender -b X.blend --python side2.py -- out_prefix [modes...]
modes: asis (her normals as they are), smooth (her body's custom normals cleared), dev (each corner coloured by how
far its normal leans from her surface's own smooth normal: grey none, yellow 10 deg, red 30 or more)."""
import bpy, sys, math
import numpy as np
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
out, modes = args[0], (args[1:] or ["asis"])
sc = bpy.context.scene
for o in sc.objects:
    if o.type == "LIGHT":
        o.hide_render = True
keep = {"HeroineHead", "Heroine"}
for o in sc.objects:
    if o.type == "MESH" and o.name not in keep:
        o.hide_render = True
for o in sc.objects:
    if o.type == "MESH" and o.name in keep:
        for m in o.modifiers:
            if m.type != "ARMATURE":
                m.show_render = False


def mat(name, rgb, attr=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*rgb, 1)
    bsdf.inputs["Roughness"].default_value = 0.7
    if attr:
        a = m.node_tree.nodes.new("ShaderNodeAttribute")
        a.attribute_name = attr
        m.node_tree.links.new(a.outputs["Color"], bsdf.inputs["Base Color"])
    return m


def smooth_dev(me):
    V = np.array([v.co[:] for v in me.vertices])
    LV = np.array([l.vertex_index for l in me.loops])
    CN = np.array([n.vector[:] for n in me.corner_normals])
    key = np.unique(np.round(V / 1e-5).astype(np.int64), axis=0, return_inverse=True)[1].ravel()
    acc = np.zeros((key.max() + 1, 3))
    for p in me.polygons:
        vs = list(p.vertices)
        for i in range(1, len(vs) - 1):
            a, b, c = V[vs[0]], V[vs[i]], V[vs[i + 1]]
            fn = np.cross(b - a, c - a)
            for k in (vs[0], vs[i], vs[i + 1]):
                acc[key[k]] += fn
    acc /= np.linalg.norm(acc, axis=1)[:, None] + 1e-12
    return np.degrees(np.arccos(np.clip((CN * acc[key][LV]).sum(1), -1, 1)))


def joined(me):
    V = np.array([v.co[:] for v in me.vertices])
    LV = np.array([l.vertex_index for l in me.loops])
    key = np.unique(np.round(V / 1e-5).astype(np.int64), axis=0, return_inverse=True)[1].ravel()
    acc = np.zeros((key.max() + 1, 3))
    for p in me.polygons:
        vs = list(p.vertices)
        for i in range(1, len(vs) - 1):
            a, b, c = V[vs[0]], V[vs[i]], V[vs[i + 1]]
            fn = np.cross(b - a, c - a)
            for k in (vs[0], vs[i], vs[i + 1]):
                acc[key[k]] += fn
    acc /= np.linalg.norm(acc, axis=1)[:, None] + 1e-12
    return acc[key][LV]


def lap(me):
    """How far each point stands off the plane of its ring (joined across seams), in metres."""
    V = np.array([v.co[:] for v in me.vertices])
    key = np.unique(np.round(V / 1e-5).astype(np.int64), axis=0, return_inverse=True)[1].ravel()
    K = key.max() + 1
    P = np.zeros((K, 3)); np.add.at(P, key, V); P /= np.bincount(key, minlength=K)[:, None]
    nb = [set() for _ in range(K)]
    for e in me.edges:
        a, b = key[e.vertices[0]], key[e.vertices[1]]
        nb[a].add(b); nb[b].add(a)
    n = joined_vert(me, V, key, K)
    d = np.zeros(K)
    for i in range(K):
        if len(nb[i]) >= 3:
            c = P[list(nb[i])].mean(0)
            d[i] = abs((P[i] - c) @ n[i])
    return d[key]


def joined_vert(me, V, key, K):
    acc = np.zeros((K, 3))
    for p in me.polygons:
        vs = list(p.vertices)
        for i in range(1, len(vs) - 1):
            a, b, c = V[vs[0]], V[vs[i]], V[vs[i + 1]]
            fn = np.cross(b - a, c - a)
            for k in (vs[0], vs[i], vs[i + 1]):
                acc[key[k]] += fn
    return acc / (np.linalg.norm(acc, axis=1)[:, None] + 1e-12)


sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items] else "BLENDER_EEVEE"
sc.view_settings.view_transform = "Standard"
sc.render.resolution_x, sc.render.resolution_y = 900, 900
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[1].default_value = 0.05
ld = bpy.data.lights.new("key", "SUN"); ld.energy = 4.0
lo = bpy.data.objects.new("key", ld); sc.collection.objects.link(lo)
import os
VIEW = os.environ.get("SIDE_VIEW", "chest")
# (light from, camera target, camera offset, ortho scale) for each view
VIEWS = {"chest": ((1.5, -1.0, 1.2), (0, -0.02, 1.53), (-0.25, -1.0, 0.05), 0.32),
         "torso": ((1.5, -1.0, 1.2), (0, -0.02, 1.25), (-0.25, -1.0, 0.05), 0.75),
         "back": ((-1.5, 1.0, 1.2), (0, 0.02, 1.35), (0.25, 1.0, 0.05), 0.6),
         "under": ((1.2, -1.0, 0.3), (0.0, -0.08, 1.33), (-0.5, -1.0, -0.25), 0.4)}
lf, tg, co, osc = VIEWS[VIEW]
lo.rotation_euler = (Vector((0, 0, 0)) - Vector(lf)).to_track_quat("-Z", "Y").to_euler()
cam_d = bpy.data.cameras.new("c"); cam_d.type = "ORTHO"; cam_d.ortho_scale = osc
cam = bpy.data.objects.new("c", cam_d); sc.collection.objects.link(cam); sc.camera = cam
tgt = Vector(tg)
cam.location = tgt + Vector(co)
cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
objs = [bpy.data.objects[n] for n in keep if n in bpy.data.objects]
for mode in modes:
    for o in objs:
        if mode == "smooth" and o.name == "Heroine":
            o.data.normals_split_custom_set([(0.0, 0.0, 0.0)] * len(o.data.loops))
            print("SMOOTH custom normals now:", o.data.has_custom_normals)
        if mode == "joined" and o.name == "Heroine":
            o.data.normals_split_custom_set([tuple(n) for n in joined(o.data)])
        if mode == "flat":
            for p_ in o.data.polygons:
                p_.use_smooth = False
            if o.data.has_custom_normals:
                a_ = o.data.attributes.get("custom_normal")
                if a_ is not None:
                    o.data.attributes.remove(a_)
        if mode == "lap":
            d = lap(o.data)
            print("LAP", o.name, "points off their ring's plane by >0.3 mm: %d, >1 mm: %d of %d" % ((d > 0.0003).sum(), (d > 0.001).sum(), len(d)))
            ca = o.data.color_attributes.get("lapc") or o.data.color_attributes.new("lapc", "FLOAT_COLOR", "POINT")
            t1 = np.clip(d / 0.0003, 0, 1)
            t2 = np.clip((d - 0.0003) / 0.0007, 0, 1)
            col = np.stack([0.8 + 0.2 * t1, 0.8 - 0.75 * t2, 0.8 - 0.75 * t1, np.ones_like(d)], 1)
            ca.data.foreach_set("color", col.astype(np.float32).ravel())
        if mode == "lap":
            m = mat("lap" + o.name, (0.8, 0.8, 0.8), "lapc")
        elif mode == "dev":
            d = smooth_dev(o.data)
            print("DEV", o.name, "corners >10 deg: %d, >30: %d of %d" % ((d > 10).sum(), (d > 30).sum(), len(d)))
            ca = o.data.color_attributes.get("dev") or o.data.color_attributes.new("dev", "FLOAT_COLOR", "CORNER")
            t1 = np.clip(d / 10.0, 0, 1)
            t2 = np.clip((d - 10.0) / 20.0, 0, 1)
            col = np.stack([0.8 + 0.2 * t1, 0.8 - 0.0 * t1 - 0.75 * t2, 0.8 - 0.75 * t1, np.ones_like(d)], 1)
            ca.data.foreach_set("color", col.astype(np.float32).ravel())
            m = mat("dev" + o.name, (0.8, 0.8, 0.8), "dev")
        else:
            m = mat(mode + o.name, (0.8, 0.8, 0.8))
        for i in range(len(o.material_slots)):
            o.material_slots[i].material = m
            if mode == "mat":
                # her skin grey, the graft green, her head red
                c = (0.85, 0.35, 0.3) if o.name == "HeroineHead" else [(0.8, 0.8, 0.8), (0.4, 0.8, 0.45), (0.4, 0.5, 0.9)][min(i, 2)]
                o.material_slots[i].material = mat("mat%s%d" % (o.name, i), c)
    sc.render.filepath = out + "_" + mode + ("" if VIEW == "chest" else "_" + VIEW) + ".png"
    bpy.ops.render.render(write_still=True)
print("SIDE done")
