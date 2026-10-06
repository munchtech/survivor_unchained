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


