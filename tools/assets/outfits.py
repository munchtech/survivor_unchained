"""The survivors' outfits, cut from their own bodies (tools/assets/heroes.py)
so that every piece fits every figure the sliders make and moves with the
same bones: a region of the body's surface chosen by its bones' weights and
its height, lifted off the skin, given its edge and its material.

    blender -b <out>/hero_<sex>.blend --python tools/assets/outfits.py -- <out> <look> [--render]

A piece is lifted along the body's normals in the basis and in every
shape key alike, so it stays the same height off the skin whatever shape
she or he is given. Pieces of hard material (plate) carry a fraction of the
breast bones' weight, so they move with the body but not as much as it.
"""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = os.path.abspath(ARGS[0])
LOOK = ARGS[1]
RENDER = "--render" in ARGS
TEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "godot", "art", "outfit")

body = next(o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("hero_") and "." not in o.name)
rig = next(o for o in bpy.data.objects if o.type == "ARMATURE")
SEX = "female" if "female" in body.name else "male"


def bone_head(name):
    b = rig.data.bones.get(name)
    return (rig.matrix_world @ b.head_local) if b else None


def weights(v, names):
    total = 0.0
    for g in v.groups:
        n = body.vertex_groups[g.group].name
        if n in names:
            total += g.weight
    return total


# ----------------------------------------------------------------- regions --
# Heights in the body's rest pose, from its bones.
Z = {n: bone_head(n).z for n in ("pelvis", "spine_01", "spine_02", "spine_03", "neck_01", "head", "thigh_l", "calf_l", "foot_l",
                                  "upperarm_l", "lowerarm_l", "hand_l") if bone_head(n)}
ARM = {"upperarm_l", "upperarm_r", "lowerarm_l", "lowerarm_r", "hand_l", "hand_r"}
ARM_ALL = ARM | {n for n in [g.name for g in body.vertex_groups] if any(k in n for k in ("index", "middle", "ring", "pinky", "thumb"))}
LEG = {"thigh_l", "thigh_r", "calf_l", "calf_r", "foot_l", "foot_r", "ball_l", "ball_r"}


HELPERS = {body.vertex_groups[n].index for n in ("HelperGeometry", "JointCubes") if n in body.vertex_groups}


def region(test):
    """Indices of the body's faces whose every vertex passes `test(v, co)`;
    never the base mesh's hidden helpers (tights, skirt, joint cubes)."""
    me = body.data
    ok = [not any(g.group in HELPERS and g.weight > 0.5 for g in v.groups) and test(v, v.co) for v in me.vertices]
    return [p.index for p in me.polygons if all(ok[i] for i in p.vertices)]


def breastplate(v, co):
    # The bust and the chest above it, front and back, ending just under the
    # bust: the midriff is left bare.
    under = Z["spine_02"] + (Z["spine_03"] - Z["spine_02"]) * 0.35
    top = Z["neck_01"] - 0.07
    return under < co.z < top and weights(v, ARM_ALL) < 0.3 and weights(v, {"neck_01", "head"}) < 0.1


def bra(v, co):
    # Two cups and a band: only what the breast bones move, and a band below.
    return weights(v, {"breast_l", "breast_r"}) > 0.25 and co.z < Z["neck_01"] - 0.06


def harness(v, co):
    return breastplate(v, co) and weights(v, {"breast_l", "breast_r"}) < 0.15


def briefs_cut(cut="full"):
    """A brief, high on the hip. The front always covers to below the crotch;
    behind, `full` covers the seat, `cheeky` shows the lower half of each
    cheek, and `thong` leaves only a strip down the middle."""
    def test(v, co):
        crotch = Z["thigh_l"] - 0.2
        top = Z["pelvis"] + 0.05
        if not (crotch < co.z < top) or weights(v, ARM_ALL) > 0.1:
            return False
        middle = abs(co.x) < 0.055 + (co.z - crotch) * 0.8
        if co.y < 0:
            return middle or weights(v, {"thigh_l", "thigh_r"}) < 0.6
        # Behind: the cut shapes the seat.
        if cut == "thong":
            return abs(co.x) < 0.018 + max(0, co.z - (Z["pelvis"] - 0.02)) * 2.5
        if cut == "cheeky":
            line = Z["pelvis"] - 0.07 + abs(co.x) * 0.25
            return co.z > line or abs(co.x) < 0.03
        return middle or weights(v, {"thigh_l", "thigh_r"}) < 0.6
    return test


briefs = briefs_cut("full")


def belt(v, co):
    return Z["pelvis"] + 0.02 < co.z < Z["pelvis"] + 0.09 and weights(v, ARM_ALL) < 0.1


def bracer(side):
    return lambda v, co: weights(v, {f"lowerarm_{side}"}) > 0.6 and weights(v, {f"hand_{side}"}) < 0.2


def pauldron(side):
    return lambda v, co: weights(v, {f"upperarm_{side}", f"clavicle_{side}"}) > 0.55 and co.z > Z["upperarm_l"] - 0.08


def greave(side):
    # The shin and the whole foot, toes included, as a boot.
    toes = {n for n in [g.name for g in body.vertex_groups] if n.startswith("toe") or n.endswith(f"_{side}") and "toe" in n}
    return lambda v, co: weights(v, {f"calf_{side}"}) > 0.5 or weights(v, {f"foot_{side}", f"ball_{side}"} | toes) > 0.3


def thighboot(side):
    knee = Z["calf_l"]
    return lambda v, co: (weights(v, {f"calf_{side}", f"foot_{side}", f"ball_{side}"}) > 0.4) or (weights(v, {f"thigh_{side}"}) > 0.7 and co.z < knee + 0.22)


# ------------------------------------------------------------- materials --
def material(name, tex, tint=(1, 1, 1), metal=0.0, rough=None, scale=6.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    uv = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    nt.links.new(uv.outputs["UV"], mp.inputs["Vector"])

    def img(suffix, non_color=False):
        for ext in ("jpg", "png"):
            p = os.path.join(TEX, f"{tex}_{suffix}.{ext}")
            if os.path.exists(p):
                n = nt.nodes.new("ShaderNodeTexImage")
                n.image = bpy.data.images.load(p)
                if non_color:
                    n.image.colorspace_settings.name = "Non-Color"
                nt.links.new(mp.outputs["Vector"], n.inputs["Vector"])
                return n
        return None

    d = img("diff")
    if d:
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 1
        mix.inputs[7].default_value = (*tint, 1)
        nt.links.new(d.outputs["Color"], mix.inputs[6])
        nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    else:
        bsdf.inputs["Base Color"].default_value = (*tint, 1)
    r = img("rough", True)
    if r and rough is None:
        nt.links.new(r.outputs["Color"], bsdf.inputs["Roughness"])
    else:
        bsdf.inputs["Roughness"].default_value = rough if rough is not None else 0.6
    n = img("nor", True)
    if n:
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(n.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Metallic"].default_value = metal
    return m


MATS = {}


def mat(key):
    if key not in MATS:
        MATS[key] = {
            "steel": lambda: material("steel", "metal_plate", (0.75, 0.75, 0.78), metal=1.0, rough=0.32, scale=4),
            "darksteel": lambda: material("darksteel", "metal_plate_02", (0.35, 0.36, 0.4), metal=1.0, rough=0.4, scale=4),
            "gold": lambda: material("gold", "metal_plate", (1.0, 0.72, 0.32), metal=1.0, rough=0.28, scale=4),
            "leather": lambda: material("leather", "brown_leather", (0.8, 0.7, 0.6), scale=5),
            "redleather": lambda: material("redleather", "leather_red_02", (0.9, 0.85, 0.85), scale=5),
            "blackleather": lambda: material("blackleather", "fabric_leather_02", (0.25, 0.23, 0.22), scale=6),
            "velvet": lambda: material("velvet", "velour_velvet", (0.35, 0.12, 0.5), scale=5),
            "linen": lambda: material("linen", "rough_linen", (0.25, 0.4, 0.22), scale=5),
            "fur": lambda: material("fur", "faux_fur_geometric", (0.55, 0.42, 0.3), scale=4),
        }[key]()
    return MATS[key]


# ----------------------------------------------------------------- pieces --
def piece(name, faces, lift, mat_key, jiggle=1.0):
    """The body's faces lifted off the skin as an object of their own."""
    if not faces:
        print("EMPTY", name)
        return None
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = body
    body.select_set(True)
    src = body.copy()
    src.data = body.data.copy()
    src.name = f"{body.name}.{name}"
    bpy.context.collection.objects.link(src)
    for mod in list(src.modifiers):
        if mod.type == "MASK":
            src.modifiers.remove(mod)
    keep = set(faces)
    bm = bmesh.new()
    bm.from_mesh(src.data)
    bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in keep], context="FACES")
    bm.to_mesh(src.data)
    bm.free()
    me = src.data
    me.update()
    # Lift along the basis normals, the same in every shape key.
    normals = [v.normal.copy() for v in me.vertices]
    if me.shape_keys:
        for kb in me.shape_keys.key_blocks:
            for i, d in enumerate(kb.data):
                d.co += normals[i] * lift
    for i, v in enumerate(me.vertices):
        v.co += normals[i] * lift
    me.materials.clear()
    me.materials.append(mat(mat_key))
    # Hard pieces move less with the breast bones.
    if jiggle < 1.0:
        for gname in ("breast_l", "breast_r"):
            g = src.vertex_groups.get(gname)
            if not g:
                continue
            for v in me.vertices:
                for e in v.groups:
                    if e.group == g.index:
                        e.weight *= jiggle
    # A rim: a thin solidify for an edge that reads as a thickness.
    so = src.modifiers.new("rim", "SOLIDIFY")
    so.thickness = 0.004 if mat_key not in ("fur",) else 0.012
    so.offset = 1
    bpy.ops.object.shade_smooth() if False else None
    for p in me.polygons:
        p.use_smooth = True
    print("PIECE", name, len(me.polygons), "faces")
    return src


L, R = "l", "r"
LOOKS = {
    "warden_f": [
        ("breastplate", breastplate, 0.012, "steel", 0.35),
        ("briefs", briefs_cut("cheeky"), 0.008, "darksteel", 1.0),
        ("belt", belt, 0.016, "leather", 1.0),
        ("pauldron_l", pauldron(L), 0.02, "steel", 1.0), ("pauldron_r", pauldron(R), 0.02, "steel", 1.0),
        ("bracer_l", bracer(L), 0.01, "leather", 1.0), ("bracer_r", bracer(R), 0.01, "leather", 1.0),
        ("greave_l", greave(L), 0.012, "steel", 1.0), ("greave_r", greave(R), 0.012, "steel", 1.0),
    ],
    "reaver_f": [
        ("bra", bra, 0.008, "fur", 1.0),
        ("briefs", briefs_cut("thong"), 0.008, "leather", 1.0),
        ("belt", belt, 0.014, "redleather", 1.0),
        ("bracer_l", bracer(L), 0.01, "leather", 1.0), ("bracer_r", bracer(R), 0.01, "leather", 1.0),
        ("boot_l", greave(L), 0.014, "fur", 1.0), ("boot_r", greave(R), 0.014, "fur", 1.0),
    ],
    "stalker_f": [
        ("corset", breastplate, 0.006, "blackleather", 0.8),
        ("briefs", briefs, 0.006, "blackleather", 1.0),
        ("belt", belt, 0.012, "leather", 1.0),
        ("bracer_l", bracer(L), 0.008, "leather", 1.0), ("bracer_r", bracer(R), 0.008, "leather", 1.0),
        ("thighboot_l", thighboot(L), 0.008, "blackleather", 1.0), ("thighboot_r", thighboot(R), 0.008, "blackleather", 1.0),
    ],
    "warden_m": [
        ("harness", harness, 0.008, "leather", 1.0),
        ("briefs", briefs, 0.01, "darksteel", 1.0),
        ("belt", belt, 0.016, "leather", 1.0),
        ("pauldron_l", pauldron(L), 0.022, "steel", 1.0), ("pauldron_r", pauldron(R), 0.022, "steel", 1.0),
        ("bracer_l", bracer(L), 0.012, "steel", 1.0), ("bracer_r", bracer(R), 0.012, "steel", 1.0),
        ("greave_l", greave(L), 0.014, "steel", 1.0), ("greave_r", greave(R), 0.014, "steel", 1.0),
    ],
}


def render(tag):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x, scene.render.resolution_y = 900, 1400
    if not scene.world:
        w = bpy.data.worlds.new("w")
        w.use_nodes = True
        w.node_tree.nodes["Background"].inputs[1].default_value = 0.25
        scene.world = w
    if not any(o.type == "LIGHT" for o in scene.objects):
        for name, loc, energy in (("key", (2.5, -3, 3.5), 900), ("fill", (-3, -2, 2), 300), ("rim", (0, 3, 3), 600)):
            light = bpy.data.lights.new(name, "AREA")
            light.energy, light.size = energy, 2
            obj = bpy.data.objects.new(name, light)
            obj.location = loc
            scene.collection.objects.link(obj)
            obj.rotation_euler = (-Vector(loc) + Vector((0, 0, 1))).to_track_quat("-Z", "Y").to_euler()
    cam = scene.camera
    if not cam:
        cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
        scene.collection.objects.link(cam)
        scene.camera = cam
    cam.data.lens = 75
    for t, ang in (("front", 0), ("three", 35), ("back", 180)):
        a = math.radians(ang)
        cam.location = (math.sin(a) * 6.2, -math.cos(a) * 6.2, 0.95)
        cam.rotation_euler = (math.radians(90), 0, a)
        scene.render.filepath = os.path.join(OUT, f"{tag}_{t}.png")
        bpy.ops.render.render(write_still=True)


for name, test, lift, mkey, jig in LOOKS[LOOK]:
    piece(name, region(test), lift, mkey, jig)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f"{LOOK}.blend"))
if RENDER:
    render(LOOK)
print("OUTFIT DONE", LOOK)
