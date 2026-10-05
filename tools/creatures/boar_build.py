"""Our boar, built in Blender from its TRELLIS 2 sculpt: the model the game
draws as every Thicket Tusker, Slurry Sow, Old Tusk and Outflow Sow.

    blender -b --python tools/creatures/boar_build.py -- STAGE --work DIR [--sculpt SCULPT.glb] [--out godot/art/beasts]

Stages, each reading the last one's .blend from the work folder:
  prep    the sculpt imported, cleaned of loose bits, turned to face -Y,
          set on the ground at its size, and made symmetrical    -> prep.blend
  (the rest are added as they are built)

Take a turn first (tools/turn.py take blender ...); the bake stage wants the
GPU's turn too.
"""
import math
import os
import sys

import bpy
import bmesh
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

argv = sys.argv[sys.argv.index("--") + 1:]
STAGE = argv[0]


def opt(name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default


WORK = opt("--work")
os.makedirs(WORK, exist_ok=True)

from boar_config import CONFIG, override  # noqa: E402

override(argv[1:])


def save(name):
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, name))


def load(name):
    bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, name))


def only(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def stage_prep():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=opt("--sculpt"))
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    only(meshes[0])
    for o in meshes:
        o.select_set(True)
    bpy.ops.object.join()
    hi = bpy.context.active_object
    hi.name = "Sculpt"
    bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
    for o in [o for o in bpy.context.scene.objects if o.type != "MESH"]:
        bpy.data.objects.remove(o)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    # Loose bits: anything under one percent of the vertices is a crumb.
    bm = bmesh.new()
    bm.from_mesh(hi.data)
    # glTF splits vertices wherever the UVs do: weld them first (the UVs
    # live on the face corners and are kept).
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bm.verts.index_update()
    parts, seen = [], set()
    for v in bm.verts:
        if v.index in seen:
            continue
        stack, part = [v], []
        seen.add(v.index)
        while stack:
            u = stack.pop()
            part.append(u)
            for e in u.link_edges:
                w = e.other_vert(u)
                if w.index not in seen:
                    seen.add(w.index)
                    stack.append(w)
        parts.append(part)
    parts.sort(key=len, reverse=True)
    crumbs = [v for p in parts[1:] if len(p) < 0.01 * len(bm.verts) for v in p]
    print("PARTS", [len(p) for p in parts[:8]], "crumbs", len(crumbs))
    bmesh.ops.delete(bm, geom=crumbs, context="VERTS")
    bm.to_mesh(hi.data)
    bm.free()
    # Turned to face -Y, centred on X, set on the ground, scaled to its length.
    hi.rotation_mode = "XYZ"  # (glTF brings objects in turned by quaternions)
    hi.rotation_euler = (0, 0, math.radians(CONFIG["yaw"]))
    bpy.ops.object.transform_apply(rotation=True)
    vs = [hi.matrix_world @ v.co for v in hi.data.vertices]
    lo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
    hi_ = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    s = CONFIG["length"] / (hi_.y - lo.y)
    hi.location = (-(lo.x + hi_.x) / 2 * s, -(lo.y + hi_.y) / 2 * s, -lo.z * s)
    hi.scale = (s, s, s)
    bpy.ops.object.transform_apply(location=True, scale=True)
    # Straightened: a sculpt whose head is turned, or whose body curves, is
    # sheared back onto x = 0 along its length before it is made symmetrical.
    if CONFIG.get("straighten"):
        for v in hi.data.vertices:
            v.co.x += interp(CONFIG["straighten"], v.co.y)
    print("SIZE", tuple(round(d, 3) for d in hi.dimensions))
    save("prep.blend")


def symmetrise(obj, keep="+X"):
    """Half kept (the side the picture showed) and mirrored over x = 0,
    its UVs with it, so the hidden side wears the seen side's paint."""
    only(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.symmetrize(direction="POSITIVE_X" if keep == "+X" else "NEGATIVE_X", threshold=0.0005)
    bpy.ops.object.mode_set(mode="OBJECT")


def duplicate(obj, name):
    o = obj.copy()
    o.data = obj.data.copy()
    o.name = o.data.name = name
    bpy.context.scene.collection.objects.link(o)
    return o


def stage_form():
    """The body's forms without TRELLIS's crust of fur flakes: the sculpt
    remeshed into one closed solid (its flakes swallowed into a coat a
    centimetre or two thick, which is what a boar's outline is), the parts
    we make ourselves cut away from it (the tail, the ears, the tusks and
    the crest's flakes, each rebuilt as our own pieces), and smoothed: hard
    over the body, lightly over the face and the lower legs, whose shapes
    are the sculpt's own. It is what the low mesh is laid over and what its
    normal map is baked from; the paint is still taken from the sculpt."""
    load("prep.blend")
    sculpt = bpy.data.objects["Sculpt"]
    symmetrise(sculpt, CONFIG["mirror"])
    form = duplicate(sculpt, "Form")
    only(form)
    form.data.materials.clear()
    form.data.remesh_voxel_size = CONFIG.get("voxel", 0.014)
    bpy.ops.object.voxel_remesh()
    print("REMESHED", len(form.data.vertices))
    cutters = []

    def cutter(obj):
        cutters.append(obj)
        mod = form.modifiers.new(obj.name, "BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.solver = "MANIFOLD"  # (EXACT emptied the remeshed body here)
        mod.object = obj

    cut = CONFIG.get("cut", {})
    if "tail_y" in cut:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, cut["tail_y"] + 0.5, 0.5))
        c = bpy.context.active_object
        c.name = "cut_tail"
        cutter(c)
    for i, (ex, ey, ez, er) in enumerate(cut.get("ears", [])):
        for s in (1, -1):
            bpy.ops.mesh.primitive_uv_sphere_add(radius=er, location=(s * ex, ey, ez), segments=24, ring_count=12)
            c = bpy.context.active_object
            c.name = f"cut_ear{i}{s}"
            cutter(c)
    if "tusks" in cut:
        ty, tx, z0, z1 = cut["tusks"]
        for s in (1, -1):
            bpy.ops.mesh.primitive_cube_add(size=1, location=(s * (tx + 0.25), ty - 0.25, (z0 + z1) / 2))
            c = bpy.context.active_object
            c.scale = (0.5, 0.5, z1 - z0)
            c.name = f"cut_tusk{s}"
            cutter(c)
    back = CONFIG.get("backline")
    if back:
        # The crest's cutter: the back's line raised, extruded across the spine and up.
        pts = back["line"]
        me = bpy.data.meshes.new("cut_crest")
        vs, fs = [], []
        for (y, z) in pts:
            for x in (-back["half"], back["half"]):
                vs.append((x, y, z + back["over"]))
                vs.append((x, y, z + 1.0))
        n = len(pts)
        # Each station: 0 (-x,low) 1 (-x,high) 2 (+x,low) 3 (+x,high).
        for i in range(n - 1):
            a, b = 4 * i, 4 * (i + 1)
            fs += [(a, b, b + 2, a + 2), (a + 1, a + 3, b + 3, b + 1), (a, a + 1, b + 1, b), (a + 2, b + 2, b + 3, a + 3)]
        fs += [(0, 2, 3, 1), (4 * (n - 1), 4 * (n - 1) + 1, 4 * (n - 1) + 3, 4 * (n - 1) + 2)]
        me.from_pydata(vs, [], fs)
        me.validate()
        c = bpy.data.objects.new("cut_crest", me)
        bpy.context.scene.collection.objects.link(c)
        only(c)
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.object.mode_set(mode="OBJECT")
        cutter(c)
    only(form)
    for name in [m.name for m in form.modifiers]:
        bpy.ops.object.modifier_apply(modifier=name)
        print("CUT", name, len(form.data.vertices))
    for c in cutters:
        bpy.data.objects.remove(c)
    # Closed again after the cuts, finer, and smoothed.
    form.data.remesh_voxel_size = CONFIG.get("fine", 0.007)
    bpy.ops.object.voxel_remesh()
    vg = form.vertex_groups.new(name="smooth")
    for v in form.data.vertices:
        x, y, z = v.co
        head = smoothstep(CONFIG.get("head_y", -0.5), CONFIG.get("head_y", -0.5) + 0.14, y)
        leg = smoothstep(CONFIG.get("leg_z", 0.26), CONFIG.get("leg_z", 0.26) + 0.14, z)
        vg.add([v.index], max(0.12, min(head, leg)), "REPLACE")
    sm = form.modifiers.new("smooth", "LAPLACIANSMOOTH")
    sm.iterations = CONFIG.get("smooth", 25)
    sm.lambda_factor = 0.5
    sm.use_volume_preserve = True
    sm.vertex_group = "smooth"
    bpy.ops.object.modifier_apply(modifier="smooth")
    sm = form.modifiers.new("even", "SMOOTH")
    sm.factor = 0.5
    sm.iterations = 4
    bpy.ops.object.modifier_apply(modifier="even")
    bpy.ops.object.shade_smooth()
    symmetrise(form, CONFIG["mirror"])
    print("FORM", len(form.data.vertices), "verts")
    save("form.blend")


def smoothstep(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def interp(points, y):
    """A line through (y, z) points, read at y (held flat past its ends)."""
    if y <= points[0][0]:
        return points[0][1]
    for (y0, z0), (y1, z1) in zip(points, points[1:]):
        if y <= y1:
            return z0 + (z1 - z0) * (y - y0) / (y1 - y0)
    return points[-1][1]


def stage_low():
    """The game mesh: the form laid out in quads by QuadriFlow, mirrored
    over x = 0, shrunk back onto the form, and unwrapped."""
    load("form.blend")
    form = bpy.data.objects["Form"]
    low = duplicate(form, "Boar")
    only(low)
    # QuadriFlow refuses a mesh with any edge under a tenth of a millimetre
    # on every axis ("not manifold"), and smoothing leaves a few of no length
    # at all: worked on a hundred times larger, with those collapsed.
    low.scale = (100, 100, 100)
    bpy.ops.object.transform_apply(scale=True)
    bm = bmesh.new()
    bm.from_mesh(low.data)
    bmesh.ops.collapse(bm, edges=[e for e in bm.edges if e.calc_length() < 2e-4], uvs=False)
    bm.to_mesh(low.data)
    bm.free()
    result = bpy.ops.object.quadriflow_remesh(use_mesh_symmetry=True, use_preserve_sharp=False, use_preserve_boundary=False,
                                              preserve_attributes=False, smooth_normals=False, mode="FACES",
                                              target_faces=CONFIG.get("faces", 4800), seed=CONFIG.get("seed", 3))
    assert result == {"FINISHED"}, "QuadriFlow refused the form"
    low.scale = (0.01, 0.01, 0.01)
    bpy.ops.object.transform_apply(scale=True)
    sw = low.modifiers.new("onto", "SHRINKWRAP")
    sw.target = form
    sw.wrap_method = "NEAREST_SURFACEPOINT"
    bpy.ops.object.modifier_apply(modifier="onto")
    symmetrise(low, CONFIG["mirror"])
    bpy.ops.object.shade_smooth()
    print("LOW", len(low.data.vertices), "verts", len(low.data.polygons), "faces")
    save("low.blend")


def stage_dress():
    """What the sculpt can't carry, made and put on: the tusks (ivory, their
    own material), the tail, and the bristle cards of the crest and the
    tuft. Then the body and the tusks are unwrapped together into one atlas."""
    import dress
    load("low.blend")
    low = bpy.data.objects["Boar"]
    hide = bpy.data.materials.new("Hide")
    ivory = bpy.data.materials.new("Ivory")
    low.data.materials.clear()
    low.data.materials.append(hide)
    low.data.materials.append(ivory)
    pieces = []
    for t in CONFIG.get("tusks", []):
        for s in (1, -1):
            root = Vector(t["root"]) * Vector((s, 1, 1))
            o = dress.tusk(f"tusk{s}", root, (s, 0, 0), (0, 0, 1), (0, -1, 0), t["length"], t["r0"],
                           sweep=tuple(t["sweep"]), curl=t.get("curl", 0.25), rings=t.get("rings", 10), sides=t.get("sides", 7))
            pieces.append(o)
    if "tail" in CONFIG:
        tl = CONFIG["tail"]
        pts = [Vector(p) for p in tl["path"]]
        path = [dress.bezier(pts[0], pts[1], pts[2], pts[3], i / 10) for i in range(11)]
        pieces.append(dress.horn("tail", path, tl["r0"], tl["r1"], rings=10, sides=6, flat=1.0))
    for o in pieces:
        o.data.materials.append(ivory if o.name.startswith("tusk") else hide)
    only(low)
    for o in pieces:
        o.select_set(True)
    bpy.ops.object.join()
    low = bpy.context.active_object
    low.name = "Boar"
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.004, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
    bpy.ops.uv.pack_islands(rotate=True, margin=0.004)
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.shade_smooth()
    crest(low)
    br = bpy.data.objects.get("Bristles")
    print("DRESSED", len(low.data.vertices), "verts;", len(br.data.vertices) if br else 0, "in the bristles")
    save("dressed.blend")


def crest(low):
    """The hedge down its back and the tuft of its tail: bristle cards
    rooted along the spine's top (found by casting down onto the body),
    leaning back, fanned to either side, longest over the hump."""
    import random
    import dress
    from mathutils.bvhtree import BVHTree
    cfg = CONFIG.get("crest")
    if not cfg:
        return
    rng = random.Random(9)
    deps = bpy.context.evaluated_depsgraph_get()
    tree = BVHTree.FromObject(low, deps)
    roots = []
    y0, y1, n = cfg["from"], cfg["to"], cfg["count"]
    for i in range(n):
        y = y0 + (y1 - y0) * (i + rng.random() * 0.6) / n
        k = (y - y0) / (y1 - y0)
        length = interp(cfg["length"], k)
        for side in cfg["fan"]:
            x = side * cfg["spread"] * (0.6 + 0.8 * rng.random())
            hit = tree.ray_cast(Vector((x, y, 2.0)), Vector((0, 0, -1)))
            if hit[0] is None:
                continue
            root = hit[0] - hit[1] * 0.01             # a little under the skin
            # Up and back, tipped out to its side, each a little different.
            lean = math.radians(cfg["lean"] + rng.uniform(-8, 8))
            out = side * math.radians(cfg["splay"] + rng.uniform(-6, 6))
            d = Vector((math.sin(out), math.sin(lean), math.cos(lean) * math.cos(out))).normalized()
            axis = Vector((1, 0, 0))
            w = cfg["width"] * (0.8 + 0.4 * rng.random())
            roots.append((root, d, axis, length * (0.8 + 0.4 * rng.random()), w, math.radians(cfg["bend"]), "crest"))
    if "tuft" in cfg and "tail" in CONFIG:
        end = Vector(CONFIG["tail"]["path"][-1])
        for k in range(cfg["tuft"]):
            a = 2 * math.pi * k / cfg["tuft"]
            d = Vector((0.25 * math.cos(a), 0.15, -1)).normalized()
            ax = Vector((math.cos(a), math.sin(a), 0))
            roots.append((end + Vector((0, 0, 0.03)), d, ax, 0.09, 0.05, 0.0, "tuft"))
    obj = dress.cards("Bristles", roots, {"crest": [0, 1, 2, 3], "fringe": [4, 5, 6], "tuft": [7]}, 8)
    mat = bpy.data.materials.new("Bristle")
    obj.data.materials.append(mat)
    for p in obj.data.polygons:
        p.use_smooth = True
    # Their normals point up and back along the body, as the hide's do, so
    # they light as part of the coat rather than as flat cards.
    obj.data.normals_split_custom_set_from_vertices([(0.0, 0.35, 0.94)] * len(obj.data.vertices))


def emit_material(name, build):
    """A material that only emits what `build(nodes, links)` returns: what a
    bake of EMIT writes out unchanged by any light."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(em.outputs[0], out.inputs[0])
    nt.links.new(build(nt.nodes, nt.links), em.inputs[0])
    return m


def bake_image(name, size, float_=False):
    img = bpy.data.images.new(name, size, size, alpha=False, float_buffer=float_)
    img.colorspace_settings.name = "Non-Color"
    return img


def bake(target, img, kind, selected=None, extrusion=0.03, distance=0.08, margin=12):
    """One bake onto the target's UVs (Cycles on the CPU: the GPU is
    ComfyUI's while it holds the card)."""
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 16 if kind != "AO" else 64
    for m in target.data.materials:
        nt = m.node_tree
        node = nt.nodes.get("bake_target") or nt.nodes.new("ShaderNodeTexImage")
        node.name = "bake_target"
        node.image = img
        nt.nodes.active = node
    bpy.ops.object.select_all(action="DESELECT")
    if selected is not None:
        for s in selected:
            s.select_set(True)
    target.select_set(True)
    bpy.context.view_layer.objects.active = target
    bs = scene.render.bake
    bs.use_selected_to_active = selected is not None
    bs.cage_extrusion = extrusion
    bs.max_ray_distance = distance
    bs.margin = margin
    bs.normal_space = "TANGENT"
    bpy.ops.object.bake(type=kind, pass_filter=set(), use_clear=True)


def save_image(img, path, fmt="PNG", depth="16"):
    img.filepath_raw = path
    img.file_format = fmt
    s = bpy.context.scene.render.image_settings
    s.file_format = fmt
    s.color_depth = depth if fmt == "PNG" else "32"
    s.color_mode = "RGB"
    img.save_render(path)


def stage_bake():
    """From the sculpt and the form onto the game mesh's atlas: the sculpt's
    own paint, the form's normals, the occlusion, and the maps the paint is
    made with (where each texel is on the body, which way it faces, which
    way its UVs run, and which part it is), all at the texture's size."""
    load("dressed.blend")
    size = int(opt("--tex", 2048))
    low = bpy.data.objects["Boar"]
    form = bpy.data.objects["Form"]
    sculpt = bpy.data.objects["Sculpt"]
    for o in bpy.data.objects:
        if o.name not in ("Boar", "Form", "Sculpt"):
            o.hide_render = True
    out = os.path.join(WORK, "maps")
    os.makedirs(out, exist_ok=True)
    slots = len(low.data.materials)

    def wear(mat):
        for i in range(slots):
            low.data.materials[i] = mat

    # The sculpt's paint, as it is (emitted, so no light is baked in).
    src = sculpt.data.materials[0]
    bsdf = next(n for n in src.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    paint_img = bsdf.inputs["Base Color"].links[0].from_node.image

    def sculpt_paint(ns, ls):
        t = ns.new("ShaderNodeTexImage")
        t.image = paint_img
        return t.outputs[0]
    sculpt.data.materials[0] = emit_material("paint_src", sculpt_paint)
    form.data.materials.clear()
    form.data.materials.append(bpy.data.materials.new("form_plain"))
    wear(emit_material("low_bake", lambda ns, ls: ns.new("ShaderNodeRGB").outputs[0]))

    img = bake_image("paint", size)
    img.colorspace_settings.name = "sRGB"
    bake(low, img, "EMIT", [sculpt], extrusion=0.04, distance=0.1)
    save_image(img, os.path.join(out, "paint.png"), depth="8")

    img = bake_image("normal_form", size)
    bake(low, img, "NORMAL", [form], extrusion=0.04, distance=0.1)
    save_image(img, os.path.join(out, "normal_form.png"))

    # Where each texel is on the body (object space, mapped from its box to
    # 0..1 so it keeps its precision in a 16-bit picture), which way it
    # faces, and which way its UVs' u runs.
    lo, hi_ = Vector((-1.0, -1.0, -0.1)), Vector((1.0, 1.0, 1.9))

    def remap(ns, ls, vec):
        sub = ns.new("ShaderNodeVectorMath")
        sub.operation = "SUBTRACT"
        sub.inputs[1].default_value = lo
        ls.new(vec, sub.inputs[0])
        div = ns.new("ShaderNodeVectorMath")
        div.operation = "DIVIDE"
        div.inputs[1].default_value = hi_ - lo
        ls.new(sub.outputs[0], div.inputs[0])
        return div.outputs[0]

    def half(ns, ls, vec):
        m = ns.new("ShaderNodeVectorMath")
        m.operation = "MULTIPLY_ADD"
        m.inputs[1].default_value = (0.5, 0.5, 0.5)
        m.inputs[2].default_value = (0.5, 0.5, 0.5)
        ls.new(vec, m.inputs[0])
        return m.outputs[0]

    def geo(ns, ls, what):
        g = ns.new("ShaderNodeNewGeometry")
        return g.outputs[what]

    def tangent(ns, ls):
        t = ns.new("ShaderNodeTangent")
        t.direction_type = "UV_MAP"
        t.uv_map = low.data.uv_layers[0].name
        return half(ns, ls, t.outputs[0])

    for name, build in (("position", lambda ns, ls: remap(ns, ls, geo(ns, ls, "Position"))),
                        ("onormal", lambda ns, ls: half(ns, ls, geo(ns, ls, "Normal"))),
                        ("tangent", tangent)):
        wear(emit_material(name, build))
        img = bake_image(name, size, float_=True)
        bake(low, img, "EMIT", margin=24)
        save_image(img, os.path.join(out, f"{name}.png"))
    # Which part each texel is: hide black, ivory white.
    def flat(v):
        def build(ns, ls):
            c = ns.new("ShaderNodeRGB")
            c.outputs[0].default_value = (v, v, v, 1)
            return c.outputs[0]
        return build
    for i in range(slots):
        low.data.materials[i] = emit_material(f"id{i}", flat(1.0 if i == 1 else 0.0))  # (slot 1 is the ivory)
    img = bake_image("part", size)
    bake(low, img, "EMIT", margin=24)
    save_image(img, os.path.join(out, "part.png"), depth="8")

    ao = bpy.data.materials.new("ao")
    ao.use_nodes = True
    wear(ao)
    # Its own shadowing only (the sculpt and the form sit over it).
    form.hide_render = sculpt.hide_render = True
    img = bake_image("ao", size)
    bake(low, img, "AO", margin=24)
    save_image(img, os.path.join(out, "ao.png"))
    print("BAKED", out)


def stage_rig():
    """The skeleton (quadruped.py, shared with the wolf to come) from the
    landmarks, the body skinned to it by bone heat, the tusks set rigid on
    the jaw and the skull, the bristles given the weights of the hide under
    them, and every clip keyed (boar_clips.py)."""
    import quadruped
    import boar_clips
    from mathutils.kdtree import KDTree
    load("dressed.blend")
    for n in ("Sculpt", "Form"):
        if n in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[n])
    body = bpy.data.objects["Boar"]
    bristles = bpy.data.objects.get("Bristles")
    lm = CONFIG["rig"]
    arm = quadruped.build_armature(lm, "Armature")
    # The hide by bone heat.
    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    # The tusks rigid: the great lower ones ride the jaw, the whetters the skull.
    roots = [(Vector(t["root"]) * Vector((s, 1, 1)), "Jaw" if i == 0 else "Head")
             for i, t in enumerate(CONFIG.get("tusks", [])) for s in (1, -1)]
    groups = {g.name: g for g in body.vertex_groups}
    ivory = {p.index for p in body.data.polygons if p.material_index == 1}
    tusk_verts = {v for p in body.data.polygons if p.index in ivory for v in p.vertices}
    for vi in tusk_verts:
        co = body.data.vertices[vi].co
        bone = min(roots, key=lambda r: (r[0] - co).length)[1]
        for g in body.vertex_groups:
            g.remove([vi])
        groups[bone].add([vi], 1.0, "REPLACE")
    # Four bones at most for each vertex, as the crowd's bake takes them.
    only(body)
    bpy.ops.object.vertex_group_limit_total(group_select_mode="ALL", limit=4)
    bpy.ops.object.vertex_group_normalize_all(group_select_mode="ALL", lock_active=False)
    # The bristles take the weights of the hide nearest each card's root.
    if bristles:
        kd = KDTree(len(body.data.vertices))
        for v in body.data.vertices:
            kd.insert(v.co, v.index)
        kd.balance()
        for g in body.vertex_groups:
            bristles.vertex_groups.new(name=g.name)
        bg = {g.name: g for g in bristles.vertex_groups}
        names = {g.index: g.name for g in body.vertex_groups}
        for v in bristles.data.vertices:
            _, idx, _ = kd.find(v.co)
            for ge in body.data.vertices[idx].groups:
                if ge.weight > 0:
                    bg[names[ge.group]].add([v.index], ge.weight, "REPLACE")
        bristles.parent = arm
        mod = bristles.modifiers.new("Armature", "ARMATURE")
        mod.object = arm
    # The scale the game draws it at, and the clips.
    heads = [b.head_local.z for b in arm.data.bones]
    extent = max(heads) - min(heads)
    scale = CONFIG["game_height"] / extent
    paces = boar_clips.build(arm, scale)
    print("RIG", len(arm.data.bones), "bones; bone extent", round(extent, 3), "scale", round(scale, 3), "paces", {k: round(v, 3) for k, v in paces.items()})
    with open(os.path.join(WORK, "paces.txt"), "w") as f:
        f.write(f"height {CONFIG['game_height']}\npace {paces['pace']:.3f}\ncharge_pace {paces['charge_pace']:.3f}\n")
    save("rigged.blend")


def stage_export():
    """Out to the game as glTF with its textures beside it (separate files,
    imported VRAM-compressed with mipmaps), every clip as its own animation."""
    load("rigged.blend")
    out = opt("--out")
    os.makedirs(out, exist_ok=True)
    maps = os.path.join(WORK, "final")
    body = bpy.data.objects["Boar"]
    bristles = bpy.data.objects.get("Bristles")

    def material(mat, albedo, normal=None, rough=0.8, clip=None):
        mat.use_nodes = True
        nt = mat.node_tree
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        outn = nt.nodes.new("ShaderNodeOutputMaterial")
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        nt.links.new(bsdf.outputs[0], outn.inputs[0])
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(albedo, check_existing=True)
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = rough
        if clip is not None:
            nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
            mat.blend_method = "CLIP"
            mat.alpha_threshold = clip
        if normal:
            nm = nt.nodes.new("ShaderNodeTexImage")
            nm.image = bpy.data.images.load(normal, check_existing=True)
            nm.image.colorspace_settings.name = "Non-Color"
            nmap = nt.nodes.new("ShaderNodeNormalMap")
            nt.links.new(nm.outputs["Color"], nmap.inputs["Color"])
            nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])

    hide, ivory = body.data.materials[0], body.data.materials[1]
    material(hide, os.path.join(maps, "boar_albedo.png"), os.path.join(maps, "boar_normal.png"), CONFIG.get("rough_hide", 0.82))
    material(ivory, os.path.join(maps, "boar_albedo.png"), os.path.join(maps, "boar_normal.png"), CONFIG.get("rough_ivory", 0.42))
    if bristles:
        material(bristles.data.materials[0], os.path.join(maps, "boar_bristles.png"), None, 0.75, clip=0.45)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.gltf(filepath=os.path.join(out, "boar.gltf"), export_format="GLTF_SEPARATE", export_texture_dir="",
                              use_selection=False, export_animations=True, export_animation_mode="NLA_TRACKS",
                              export_force_sampling=True, export_frame_step=1, export_def_bones=False, export_skins=True,
                              export_all_influences=False, export_image_format="AUTO", export_yup=True, export_apply=False,
                              export_cameras=False, export_lights=False)
    print("EXPORTED", out)


STAGES = {"prep": stage_prep, "form": stage_form, "low": stage_low, "dress": stage_dress, "bake": stage_bake,
          "rig": stage_rig, "export": stage_export}

if __name__ == "__main__":
    STAGES[STAGE]()
