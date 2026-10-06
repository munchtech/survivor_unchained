import bpy, os, sys
out = sys.argv[sys.argv.index("--") + 1]
arm = bpy.data.objects["Armature"]
objs = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("Hero") and o.name != "HeroBrows"]
print("EXPORT", [o.name for o in objs])
bpy.ops.object.select_all(action="DESELECT")
arm.select_set(True)
for o in objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_skins=True, export_animations=False, export_yup=True,
                          export_format="GLB", export_image_format="WEBP", export_image_quality=92)
print("SIZE", os.path.getsize(out))
