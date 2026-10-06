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
    cutters = []

    def cutter(obj):
        cutters.append(obj)
        mod = form.modifiers.new(obj.name, "BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.solver = "EXACT"
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
    for m in list(form.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)
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


