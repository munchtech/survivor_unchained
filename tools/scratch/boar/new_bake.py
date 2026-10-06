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
    for i, m in enumerate(low.data.materials):
        pass
    ids = [emit_material(f"id{i}", (lambda v: lambda ns, ls: (lambda c: (setattr(c.outputs[0], "default_value", (v, v, v, 1)), c.outputs[0])[1])(ns.new("ShaderNodeRGB")))(1.0 if i == 1 else 0.0))
           for i in range(slots)]
    for i in range(slots):
        low.data.materials[i] = ids[i]
    img = bake_image("part", size)
    bake(low, img, "EMIT", margin=24)
    save_image(img, os.path.join(out, "part.png"), depth="8")

    wear(bpy.data.materials.new("ao"))
    img = bake_image("ao", size)
    bake(low, img, "AO", margin=24)
    save_image(img, os.path.join(out, "ao.png"))
    print("BAKED", out)


