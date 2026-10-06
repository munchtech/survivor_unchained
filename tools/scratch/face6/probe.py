import bpy
import numpy as np
for o in bpy.data.objects:
    if o.type == "MESH":
        co = np.array([o.matrix_world @ v.co for v in o.data.vertices])
        sk = len(o.data.shape_keys.key_blocks) if o.data.shape_keys else 0
        print("OBJ", o.name, len(o.data.vertices), "keys", sk, "min", np.round(co.min(0), 3), "max", np.round(co.max(0), 3))
head = bpy.data.objects["HeroineHead"]
me = head.data
ef = {}
for p in me.polygons:
    for ek in p.edge_keys:
        ef[ek] = ef.get(ek, 0) + 1
bv = sorted({v for ek, c in ef.items() if c == 1 for v in ek})
co = np.array([head.matrix_world @ me.vertices[i].co for i in bv])
print("BOUNDARY", len(bv))
for z0 in np.unique(np.round(co[:, 2], 2)):
    s = co[np.round(co[:, 2], 2) == z0]
    print("  z %.2f: %d pts, x %.3f..%.3f y %.3f..%.3f" % (z0, len(s), s[:, 0].min(), s[:, 0].max(), s[:, 1].min(), s[:, 1].max()))
e = bpy.data.objects["HeroineEyes"]
ec = np.array([e.matrix_world @ v.co for v in e.data.vertices])
for sx in (-1, 1):
    ev = ec[np.sign(ec[:, 0]) == sx]
    print("EYE", sx, np.round(ev.mean(0), 4), "r", np.round(np.linalg.norm(ev - ev.mean(0), axis=1).max(), 4))
print("KEYS", [k.name for k in me.shape_keys.key_blocks][:80])
