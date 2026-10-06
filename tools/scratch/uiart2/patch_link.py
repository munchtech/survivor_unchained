p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748\tools\uiforge\blender_chainline.py'
s = open(p, encoding='utf-8').read()
a = s.index('def link_mesh(')
b = s.index('def iron_chain_material(')
new = '''def link_mesh(name, length, width, wire, gap=0.0, where="side"):
    """A stadium-shaped link of round bar, as a mesh, and the tips of its break if it has one.
    `gap` (Blender units) pries it open: in the middle of its lower side ("side"), or at its
    end toward -x ("minus") or +x ("plus"), the bar's ends there bent apart."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = wire
    cu.bevel_resolution = 5
    cu.use_fill_caps = True
    r = width / 2 - wire
    st = max(length - width, 0) / 2
    pts = []
    for i in range(24):                                   # lower side, middle to the right
        pts.append((st * i / 24, -r))
    for i in range(49):                                   # the right end
        t = -math.pi / 2 + math.pi * i / 48
        pts.append((st + r * math.cos(t), r * math.sin(t)))
    for i in range(1, 49):                                # the upper side
        pts.append((st - 2 * st * i / 48, r))
    for i in range(1, 49):                                # the left end
        t = math.pi / 2 + math.pi * i / 48
        pts.append((-st + r * math.cos(t), r * math.sin(t)))
    for i in range(1, 24):                                # lower side, back to the middle
        pts.append((-st + st * i / 24, -r))
    tips = []
    if gap:
        if where == "side":
            c = (0.0, -r)
            cut = [y < -r * 0.99 and abs(x) < gap / 2 for x, y in pts]
        elif where == "minus":
            c = (-st - r, 0.0)
            cut = [x < -st and abs(y) < gap / 2 for x, y in pts]
        else:
            c = (st + r, 0.0)
            cut = [x > st and abs(y) < gap / 2 for x, y in pts]
        n = len(pts)
        start = next(i for i in range(n) if not cut[i] and cut[i - 1])
        seq = [pts[(start + j) % n] for j in range(n) if not cut[(start + j) % n]]
        # Pried: the bar's ends near the break bent apart, away from the break's middle.
        m = max(6, len(seq) // 7)
        bent = []
        for j, (x, y) in enumerate(seq):
            f = max(0.0, 1 - min(j, len(seq) - 1 - j) / m) ** 2
            dx, dy = x - c[0], y - c[1]
            dl = math.hypot(dx, dy) or 1.0
            bent.append((x + f * gap * 0.45 * dx / dl, y + f * gap * 0.45 * dy / dl))
        pts = bent
        tips = [pts[0], pts[-1]]
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for i, (x, y) in enumerate(pts):
        sp.points[i].co = (x, y, 0, 1)
    sp.use_cyclic_u = not gap
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    for o in bpy.context.selected_objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.ops.object.convert(target="MESH")
    return bpy.context.view_layer.objects.active, tips


'''
s = s[:a] + new + s[b:]
old_call = '''            ob = link_mesh(f"c{ci}_{i}", length * sl * U, width * sw_ * U, wire * U, gap=gap)'''
assert old_call in s
s = s.replace(old_call, '''            where = ch.get("where", "side")
            if where == "end":
                where = "minus" if i == 0 else "plus"
            ob, tips = link_mesh(f"c{ci}_{i}", length * sl * U, width * sw_ * U, wire * U, gap=gap, where=where)''')
old_hot = '''            r = (width * sw_ / 2 - wire) * U
            ob.data.materials.append(hot_material([(gap / 2 * 1.35, -r - gap * 0.45, 0), (-gap / 2 * 1.35, -r - gap * 0.45, 0)],
                                                  gap * 1.6) if opened else mat)'''
assert old_hot in s
s = s.replace(old_hot, '''            ob.data.materials.append(hot_material([(tx_, ty_, 0) for tx_, ty_ in tips], gap * 1.6) if opened else mat)''')
open(p, 'w', encoding='utf-8').write(s)

p2 = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748\tools\uiforge\chain.py'
t = open(p2, encoding='utf-8').read()
t = t.replace('''                        "open": "first" if side == "r" else "last", "gap": gap * 2}],''', '''                        "open": "first" if side == "r" else "last", "gap": gap * 2, "where": "end"}],''')
open(p2, 'w', encoding='utf-8').write(t)
print('ok')
