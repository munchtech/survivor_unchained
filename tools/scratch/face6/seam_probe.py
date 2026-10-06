"""Her neck and chest along her middle: for her head and body meshes, the points within 1 mm of x = 0 between her
collarbones and her chin, whether any lie twice (a split), whether the edges there are sharp, and how her normals
turn across her middle (each corner's normal: its x, which should run smoothly through 0 at her middle)."""
import bpy
import numpy as np

for name in ("HeroineHead", "Heroine"):
    o = bpy.data.objects.get(name)
    if o is None:
        print(name, "missing"); continue
    me = o.data
    M = np.array(o.matrix_world)
    co = np.array([v.co[:] for v in me.vertices]) @ M[:3, :3].T + M[:3, 3]
    sel = np.where((np.abs(co[:, 0]) < 0.001) & (co[:, 2] > 1.35) & (co[:, 2] < 1.62) & (co[:, 1] < 0.0))[0]
    print("MESH", name, "verts", len(me.vertices), "middle verts in neck/chest", len(sel))
    # duplicates (same place, different vertex)
    from collections import defaultdict
    d = defaultdict(list)
    for i in sel:
        d[tuple(np.round(co[i], 5))].append(i)
    dups = [v for v in d.values() if len(v) > 1]
    print("  points lying twice:", len(dups))
    sharp = me.attributes.get("sharp_edge")
    if sharp is not None:
        se = np.array([sharp.data[i].value for i in range(len(me.edges))])
        mid_e = [e.index for e in me.edges if e.vertices[0] in set(sel) and e.vertices[1] in set(sel)]
        print("  sharp edges along her middle:", int(se[mid_e].sum()) if mid_e else 0, "of", len(mid_e))
    print("  custom split normals:", me.has_custom_normals)
    # corner normals at those points: spread of normals at the same vertex
    me.calc_loop_triangles() if hasattr(me, "calc_loop_triangles") else None
    cn = np.array([l.vector[:] for l in me.corner_normals]) if hasattr(me, "corner_normals") else None
    if cn is not None:
        lv = np.array([l.vertex_index for l in me.loops])
        worst = 0
        for i in sel:
            ns = cn[lv == i]
            if len(ns) > 1:
                ang = np.degrees(np.arccos(np.clip((ns @ ns.T).min(), -1, 1)))
                worst = max(worst, ang)
        print("  most a middle point's corner normals differ: %.1f deg" % worst)
        # x of the normals just either side of the middle, by height
        for z in (1.40, 1.45, 1.50, 1.55):
            near = np.where((np.abs(co[:, 2] - z) < 0.008) & (np.abs(co[:, 0]) < 0.015) & (co[:, 1] < 0))[0]
            rows = []
            for i in near:
                ns = cn[lv == i]
                if len(ns):
                    rows.append((co[i, 0], ns.mean(0)[0]))
            rows.sort()
            print("   z %.2f:" % z, " ".join("x%+.3f:n%+.2f" % r for r in rows[:: max(1, len(rows) // 8)]))
