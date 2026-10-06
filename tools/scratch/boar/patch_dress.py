p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-af551cacc6292152f\tools\creatures\boar_build.py"
s = open(p, encoding="utf-8").read()
old = '''    symmetrise(low, CONFIG["mirror"])
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.004, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
    bpy.ops.uv.pack_islands(rotate=True, margin=0.004)
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.shade_smooth()
    print("LOW", len(low.data.vertices), "verts", len(low.data.polygons), "faces")
    save("low.blend")'''
new = '''    symmetrise(low, CONFIG["mirror"])
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
    obj.data.normals_split_custom_set_from_vertices([(0.0, 0.35, 0.94)] * len(obj.data.vertices))'''
assert old in s
s = s.replace(old, new)
s = s.replace('''STAGES = {"prep": stage_prep, "form": stage_form, "low": stage_low, "bake": stage_bake}''',
              '''STAGES = {"prep": stage_prep, "form": stage_form, "low": stage_low, "dress": stage_dress, "bake": stage_bake}''')
s = s.replace('''    load("low.blend")
    size = int(opt("--tex", 2048))''', '''    load("dressed.blend")
    size = int(opt("--tex", 2048))''')
open(p, "w", encoding="utf-8").write(s)
print("ok")
