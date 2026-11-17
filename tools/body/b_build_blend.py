"""Build body B's blend for lane D's armor tools (piece_ship.py --src <blend> -> tools/armor/piece_blender.py).

Run: blender -b --factory-startup --python tools/body/b_build_blend.py -- <body.glb> <out.blend>

Empty scene, glTF import of body.glb, then names made to match A's twin (heroine_built_armroot.blend):
one armature object and data named "Armature"; meshes keep the glb's names (Heroine, HeroineHead, HeroineEyes,
HeroineLashes, HeroineTeeth, HeroineTongue); each mesh parented to the armature with an ARMATURE modifier;
images packed. No hair: hair is not B's yet (no hair_long etc. in this blend).

Import bone settings: bone_heuristic=TEMPERANCE (the default). BLENDER was tried: same result plus a stray Icosphere
(bone shape), so TEMPERANCE. Result: all 124 joint names, inverse binds (4.7e-6 by name) and positions (0.0007 mm)
survive; only the joint ORDER differs (105 slots), because the glTF exporter orders joints by its own bone walk, which no
import setting changes. The skin is self-consistent (vertex joint indices follow), so armor output is unaffected.
"""
import sys
import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
GLB, OUT = argv[0], argv[1]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB, bone_heuristic="TEMPERANCE", import_shading="NORMALS")

arms = [o for o in bpy.data.objects if o.type == "ARMATURE"]
assert len(arms) == 1, "expected one armature, got %d" % len(arms)
arm = arms[0]
arm.name = "Armature"
arm.data.name = "Armature"
for o in list(bpy.data.objects):
    if o.type == "MESH":
        o.parent = arm
        o.matrix_parent_inverse = arm.matrix_world.inverted()
        mods = [m for m in o.modifiers if m.type == "ARMATURE"]
        if not mods:
            mods = [o.modifiers.new("Armature", "ARMATURE")]
        mods[0].object = arm
    elif o.type == "EMPTY":
        bpy.data.objects.remove(o)   # importer's stray root/node empties
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("BUILT", OUT, [o.name for o in bpy.data.objects], len(arm.data.bones), "bones")
