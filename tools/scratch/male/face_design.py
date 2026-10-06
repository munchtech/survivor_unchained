"""Try a MakeHuman man's face: MACROS and FACE (JSON in env FACE_JSON) and render it.
    blender -b --python face_design.py -- <out prefix>"""
import bpy, json, math, os, sys
from mathutils import Vector
ARGS = sys.argv[sys.argv.index("--") + 1:]
OUT = ARGS[0]
os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
from bl_ext.user_default.mpfb.services.humanservice import HumanService
from bl_ext.user_default.mpfb.services.targetservice import TargetService
cfg = json.loads(open(os.environ["FACE_JSON"]).read())
MACROS = cfg["macros"]
hm = HumanService.create_human(mask_helpers=True, detailed_helpers=True, extra_vertex_groups=True, feet_on_ground=True,
                               scale=0.1, macro_detail_dict=MACROS)
TD = os.path.join(bpy.utils.user_resource("EXTENSIONS"), "user_default", "mpfb", "data", "targets")
TARGET = {}
for r, _, fs in os.walk(TD):
    for f in fs:
        if f.endswith(".target.gz") and "expression" not in r:
            TARGET.setdefault(f[:-10], os.path.join(r, f))
for f in os.listdir(os.path.join(TD, "expression", "units", "caucasian")):
    TARGET["x:" + f[:-10]] = os.path.join(TD, "expression", "units", "caucasian", f)
for t, v in cfg["face"].items():
    for n in ([t.replace("X-", "l-", 1), t.replace("X-", "r-", 1)] if t.startswith("X-") else [t]):
        TargetService.load_target(hm, TARGET[n], weight=v)
DATA = os.path.join(bpy.utils.user_resource("EXTENSIONS"), ".user", "user_default", "mpfb", "data")
for kind, name in (("eyes", "high-poly"), ("eyebrows", "eyebrow001"), ("eyelashes", "eyelashes03")):
    try:
        HumanService.add_mhclo_asset(os.path.join(DATA, kind, name, name + ".mhclo"), hm, asset_type=kind, subdiv_levels=0,
                                     material_type="NONE", set_up_rigging=False, interpolate_weights=False, import_subrig=False, import_weights=False)
    except Exception as e:
        print("PART", kind, name, e)
for mo in hm.modifiers:
    mo.show_render = mo.type in ("SUBSURF", "MASK")
bpy.context.view_layer.update()
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE_NEXT"
sc.render.resolution_x, sc.render.resolution_y = 900, 1100
sc.view_settings.view_transform = "AgX"
w = bpy.data.worlds.new("w"); sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.3, 0.31, 0.33, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.4
mat = bpy.data.materials.new("clay"); mat.use_nodes = True
b = mat.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.62, 0.45, 0.36, 1)
b.inputs["Roughness"].default_value = 0.55
for o in bpy.data.objects:
    if o.type == "MESH":
        o.data.materials.clear(); o.data.materials.append(mat)
for nm, rot, e in (("key", (60, 0, 35), 3.5), ("fill", (70, 0, -70), 0.8), ("rim", (75, 0, 170), 2.5)):
    l = bpy.data.lights.new(nm, "SUN"); l.energy = e; l.angle = math.radians(5)
    lo = bpy.data.objects.new(nm, l); sc.collection.objects.link(lo)
    lo.rotation_euler = [math.radians(a) for a in rot]
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
import numpy as np
e = hm.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
_b = hm.vertex_groups["body"].index
_in = np.array([any(g.group == _b for g in v.groups) for v in hm.data.vertices])
co = np.array([(hm.matrix_world @ v.co)[:] for v in hm.data.vertices])[_in]
top = co[:, 2].max()
print("OBJECTS", [o.name for o in bpy.data.objects])
eyes = next(o for o in bpy.data.objects if o.type == "MESH" and "high-poly" in o.name.lower())
ee = eyes.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
ec = np.array([(eyes.matrix_world @ v.co)[:] for v in ee.vertices])
tgt = Vector((0, ec[:, 1].mean() + 0.05, ec[:, 2].mean() - 0.04))
print("EYES at", ec.mean(0).round(3))
print("HUMAN height %.3f" % (top - co[:, 2].min()))
for nm, ang in (("front", 0), ("q", 35), ("side", 90)):
    a = math.radians(ang)
    cam.data.lens = 85
    cam.location = tgt + Vector((math.sin(a) * 0.85, -math.cos(a) * 0.85, 0.02))
    cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = OUT + "_" + nm + ".png"
    bpy.ops.render.render(write_still=True)
