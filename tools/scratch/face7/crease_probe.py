# Her surface across her middle, seen from in front: at each height, how deep her front lies at each x (rays from
# in front), and how sharply it bends there (degrees of turn per 2 mm step), to find a crease down her throat
# and chest where her two halves meet.
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

dg = bpy.context.evaluated_depsgraph_get()
trees = []
for n in ("Heroine", "HeroineHead"):
    o = bpy.data.objects.get(n)
    if o is None:
        continue
    me = o.evaluated_get(dg).to_mesh()
    V = [o.matrix_world @ v.co for v in me.vertices]
    F = [list(p.vertices) for p in me.polygons]
    trees.append((n, BVHTree.FromPolygons(V, F)))
xs = np.arange(-0.04, 0.0401, 0.002)
import os
ZS = [float(v) for v in os.environ.get("ZS", "1.50,1.47,1.44,1.41,1.38,1.35,1.32").split(",")]
for z in ZS:
    ys, who = [], []
    for x in xs:
        best = None
        for n, t in trees:
            h = t.ray_cast(Vector((x, -0.6, z)), Vector((0, 1, 0)))
            if h[0] is not None and (best is None or h[3] < best[1]):
                best = (h[0].y, h[3], n[7:8] or "B")
        ys.append(best[0] if best else np.nan)
        who.append(best[2] if best else "-")
    ys = np.array(ys)
    ang = np.degrees(np.arctan2(np.diff(ys), 0.002))     # the slope of each step
    turn = np.diff(ang)                                   # how much it turns at each point
    print("z %.2f  y at x=0: %.4f  who: %s" % (z, ys[len(xs) // 2], "".join(who)))
    print("   turn: " + " ".join("%+5.1f" % t for t in turn))
