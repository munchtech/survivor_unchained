import bpy, collections
import numpy as np
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=r"C:/Users/munch/Desktop/ComfyUI_00008.glb")
for o in bpy.data.objects:
    print("OBJ", o.type, o.name, tuple(round(x, 3) for x in o.dimensions), "loc", tuple(round(x, 3) for x in o.location), "rot", tuple(round(x, 3) for x in o.rotation_euler))
    if o.type == "MESH":
        me = o.data
        print("  verts", len(me.vertices), "faces", len(me.polygons), "uv", [u.name for u in me.uv_layers], "col", [a.name for a in me.color_attributes])
        print("  materials", [m.name for m in me.materials])
        co = np.array([(o.matrix_world @ v.co)[:] for v in me.vertices])
        print("  bounds", co.min(0).round(3), co.max(0).round(3))
for im in bpy.data.images:
    print("IMAGE", im.name, im.size[:], im.packed_file is not None)
for m in bpy.data.materials:
    if m.node_tree:
        print("MAT", m.name, [(n.type, n.image.name if getattr(n, 'image', None) else '') for n in m.node_tree.nodes])
        for l in m.node_tree.links:
            print("   LINK", l.from_node.type, l.from_socket.name, "->", l.to_node.type, l.to_socket.name)
for im in bpy.data.images:
    im.filepath_raw = r"C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/male/glb_" + im.name.replace(" ", "_") + ".png"
    im.file_format = "PNG"
    im.save()
bpy.ops.wm.save_as_mainfile(filepath=r"C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/male/glb.blend")
