p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748\tools\uiforge\blender_links.py'
s = open(p, encoding='utf-8').read()
a = s.index('    if spec.get("eyelet"):\n        eyelet(')
b = s.index('if __name__ == "__main__":')
new = '''    if spec.get("eye"):
        eye(spec, sc, out, ss, length, width, wire, states[""], plane)


def eye(spec, sc, out, ss, length, width, wire, iron, plane):
    """The chain's anchor (the owner: the links must truly go through it): an eye-bolt driven
    into the band, its ring standing across the chain and leaning back, so a link passing
    through it goes under its near arc and over its far one. Rendered in two halves split at
    the chain's height: eye_back.png (the far arc, the shank, the washer, and every shadow) to
    lie under the links, eye_front.png (the near arc alone) over them."""
    import bmesh
    e = spec["eye"]
    R, bar = e["r"] * ss, e["bar"] * ss
    phi = math.radians(e.get("lean", 35))
    bpy.ops.mesh.primitive_torus_add(major_radius=R * U, minor_radius=bar * U, major_segments=128, minor_segments=24)
    ring = bpy.context.active_object
    ring.rotation_euler = (0, math.pi / 2 - phi, 0)
    zc = R * math.cos(phi) + bar * 0.4
    ring.location = (0, 0, zc * U)
    bpy.context.view_layer.update()
    bpy.ops.object.transform_apply(location=True, rotation=True)
    ring.data.materials.append(iron)
    # Where the chain has run through it: rubbed bright inside.
    lk, _ = C.link_mesh("pass", length * U, width * U, wire * U)
    lk.rotation_euler = (math.pi / 2, 0, 0)
    lk.location = (0, 0, zc * U)
    bpy.context.view_layer.update()
    C.mark_wear([lk, ring], wire * U * 1.6)
    bpy.data.objects.remove(lk, do_unlink=True)
    # Its shank down into the band from the ring's foot, and a washer under it.
    low = min(ring.data.vertices, key=lambda v: v.co.z).co
    bpy.ops.mesh.primitive_cylinder_add(radius=bar * 0.9 * U, depth=max(low.z, bar * U) * 1.2, location=(low.x, low.y, low.z / 2))
    shank = bpy.context.active_object
    shank.data.materials.append(iron)
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=bar * 2.6 * U, depth=bar * 0.6 * U, location=(low.x, low.y, bar * 0.3 * U))
    washer = bpy.context.active_object
    bev = washer.modifiers.new("b", "BEVEL")
    bev.width = bar * 0.25 * U
    bev.segments = 3
    washer.data.materials.append(iron)
    # Split the ring at the chain's height: the near arc (above) and the far arc (below).
    front = ring.copy()
    front.data = ring.data.copy()
    bpy.context.scene.collection.objects.link(front)
    for ob, keep_above in ((front, True), (ring, False)):
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        gone = [f for f in bm.faces if (f.calc_center_median().z > zc * U) != keep_above]
        bmesh.ops.delete(bm, geom=gone, context="FACES")
        bm.to_mesh(ob.data)
        bm.free()
    # The back: far arc, shank and washer seen, the near arc only casting its shadow.
    front.visible_camera = False
    sc.render.filepath = os.path.join(out, "eye_back.png")
    bpy.ops.render.render(write_still=True)
    # The front: the near arc alone, nothing under it, no shadow of its own on the page.
    front.visible_camera = True
    for ob in (ring, shank, washer):
        ob.hide_render = True
    plane.hide_render = True
    sc.render.filepath = os.path.join(out, "eye_front.png")
    bpy.ops.render.render(write_still=True)


'''
s = s[:a] + new + s[b:]
s = s.replace('''    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    plane = bpy.context.active_object
    plane.scale = (W * U * 1.5, H * U * 1.5, 1)
    plane.is_shadow_catcher = True
    rnd = random.Random''', '''    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    plane = bpy.context.active_object
    plane.scale = (W * U * 1.5, H * U * 1.5, 1)
    plane.is_shadow_catcher = True
    rnd = random.Random''')
open(p, 'w', encoding='utf-8').write(s)

p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748\tools\uiforge\chain.py'
s = open(p, encoding='utf-8').read()
s = s.replace('''            "eyelet": {"hole": 12.5 * 2, "bar": 3.4 * 2, "nail": 1.8 * 2}}''', '''            "eye": {"r": 11.5 * 2, "bar": 2.7 * 2, "lean": 35}}''')
s = s.replace('''    names = [f"{pre}{kind}_{k}" for pre in ("", "warm_", "hot_") for kind in ("face", "edge") for k in range(variants)] + ["open", "eyelet"]''',
              '''    names = [f"{pre}{kind}_{k}" for pre in ("", "warm_", "hot_") for kind in ("face", "edge") for k in range(variants)] + ["open", "eye_back", "eye_front"]''')
s = s.replace('''        if nm == "eyelet":
            img = hole_dark(img, 12.5 * 2)
''', '')
s = s.replace('''    made.update(eyelet_parts(cell))
''', '''    made["chain/tab.png"] = tab()
''')
s = s.replace('''FEEL = {"eyelet": True, "fade": 0, "run": 72, "heat": 2, "hole": 12.5,''', '''FEEL = {"eye": True, "fade": 0, "run": 56, "tail": 20, "heat": 2,''')
s = s.replace('''def links(variants=6''', '''def tab(Ws=30, Hs=30, seed=23):
    """chain/tab.png, Ws x Hs shown in a cell with room for its shadow: where the chain ends,
    a tab of the band's goatskin riveted down over it, so its last links go under leather and
    are gone, nothing faded. Its inner end (toward the chain) is cut square; the outer end
    rounded; one domed iron rivet through it."""
    import kit
    pad = 6
    W, H = int((Ws + 2 * pad) * K), int((Hs + 2 * pad) * K)
    sd, x, y = kit.box_sd(W, H, pad, pad, Ws + pad, Hs + pad, 3.5)
    skin = kit.morocco(N=128, seed=seed, tone="#1d1516")
    skin = np.tile(skin, (H // skin.shape[0] + 1, W // skin.shape[1] + 1, 1))[:H, :W]
    inside = np.clip(sd * K + 0.5, 0, 1)
    # The leather's edge turned down, lit as the panels' are.
    edge = kit.raised(Ws + 2 * pad, Hs + 2 * pad, out=pad, r=3.5, mid=None, wear=1.1, lift=1.2, shadow=0.75)
    img = kit.under(edge, np.dstack([skin[..., :3], inside]))
    # The rivet: a small domed head of iron, lit from the upper left.
    S = F.Surface(W, H)
    cx, cy = (pad + Ws * 0.58) * K, (pad + Hs / 2) * K
    d = np.hypot(S.xx - cx, S.yy - cy)
    rr = 3.4 * K
    S.height = (np.sqrt(np.clip(1 - (d / rr) ** 2, 0, 1)) * rr * 0.6).astype(np.float32)
    cov = np.clip((rr - d) + 0.5, 0, 1)
    S.paint(cov, F.Mat(tuple(F.hexc("#3a3440")), 0.75, 0.32))
    S.alpha = cov
    rv = np.asarray(S.finish(S.shade(normal_strength=1.0, ao=0.3, shadow=0.0)), np.float32) / 255
    sh = np.roll(cv2.GaussianBlur(cov, (0, 0), 1.2 * K), int(1.0 * K), 0) * 0.6 * (1 - cov)
    img = kit.under(rv, kit.under(np.dstack([np.broadcast_to(np.array([0.02, 0.015, 0.015], np.float32), cov.shape + (3,)), sh]), img))
    return img.astype(np.float32)


def links(variants=6''')
open(p, 'w', encoding='utf-8').write(s)
print('ok')
