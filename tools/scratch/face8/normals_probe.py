# What her body's normals are in heroine_body.blend: custom split normals,
# sharp edges, flat faces, modifiers; and how far her corners' normals lean
# from the joined smooth ones over her throat and upper chest.
import sys
import bpy
import numpy as np

her = bpy.data.objects["Heroine"]
me = her.data
print("OBJ", her.name, "verts", len(me.vertices), "faces", len(me.polygons), "loops", len(me.loops))
print("MODS", [(m.name, m.type) for m in her.modifiers])
print("custom normals:", me.has_custom_normals, "domain:", me.normals_domain)
for nm in ("sharp_edge", "sharp_face", "custom_normal"):
    a = me.attributes.get(nm)
    if a is None:
        print("ATTR", nm, "none")
        continue
    print("ATTR", nm, a.domain, a.data_type, len(a.data))
    if a.data_type == "BOOLEAN":
        v = np.zeros(len(a.data), bool)
        a.data.foreach_get("value", v)
        print("   true:", int(v.sum()))
flat = sum(1 for p in me.polygons if not p.use_smooth)
print("flat polygons:", flat)
tri = sum(1 for p in me.polygons if p.loop_total == 3)
print("tris", tri, "quads", sum(1 for p in me.polygons if p.loop_total == 4))

V = np.array([v.co[:] for v in me.vertices])
LV = np.array([l.vertex_index for l in me.loops])
CN = np.array([n.vector[:] for n in me.corner_normals])
VN = np.array([v.normal[:] for v in me.vertices])
# Smooth normals joined by position (across UV seams).
key = np.unique(np.round(V / 1e-5).astype(np.int64), axis=0, return_inverse=True)[1].ravel()
acc = np.zeros((key.max() + 1, 3))
for p in me.polygons:
    vs = list(p.vertices)
    for i in range(1, len(vs) - 1):
        a, b, c = V[vs[0]], V[vs[i]], V[vs[i + 1]]
        fn = np.cross(b - a, c - a)
        for k in (vs[0], vs[i], vs[i + 1]):
            acc[key[k]] += fn
acc /= np.linalg.norm(acc, axis=1)[:, None] + 1e-12
SN = acc[key]
ang = np.degrees(np.arccos(np.clip((CN * SN[LV]).sum(1), -1, 1)))
angv = np.degrees(np.arccos(np.clip((VN * SN).sum(1), -1, 1)))
P = V[LV]
regions = {
    "all": np.ones(len(LV), bool),
    "throat+chest front (z 1.30-1.52, y<0, |x|<0.12)": (P[:, 2] > 1.30) & (P[:, 2] < 1.52) & (P[:, 1] < 0) & (np.abs(P[:, 0]) < 0.12),
    "upper chest (z 1.38-1.48, y<-0.05)": (P[:, 2] > 1.38) & (P[:, 2] < 1.48) & (P[:, 1] < -0.05),
    "middle (|x|<0.01, z 1.3-1.55)": (np.abs(P[:, 0]) < 0.01) & (P[:, 2] > 1.3) & (P[:, 2] < 1.55),
}
for nm, m in regions.items():
    a = ang[m]
    print("REGION %s: %d corners; corner vs joined smooth: mean %.1f, p50 %.1f, p90 %.1f, p99 %.1f, >10deg %d (%.1f%%), >25deg %d"
          % (nm, m.sum(), a.mean(), np.percentile(a, 50), np.percentile(a, 90), np.percentile(a, 99), (a > 10).sum(), 100 * (a > 10).mean(), (a > 25).sum()))
# Geometry itself: the angle between each face and its neighbours (dihedral)
# over the same region, to tell a bumpy surface from bent normals.
me.calc_loop_triangles()
FN = np.array([p.normal[:] for p in me.polygons])
FC = np.array([p.center[:] for p in me.polygons])
edge_faces = {}
for p in me.polygons:
    for ek in p.edge_keys:
        edge_faces.setdefault(ek, []).append(p.index)
dih = []
for ek, fs in edge_faces.items():
    if len(fs) == 2:
        c = (V[ek[0]] + V[ek[1]]) / 2
        d = np.degrees(np.arccos(np.clip(FN[fs[0]] @ FN[fs[1]], -1, 1)))
        dih.append((c[0], c[1], c[2], d, np.linalg.norm(V[ek[0]] - V[ek[1]])))
dih = np.array(dih)
m = (dih[:, 2] > 1.30) & (dih[:, 2] < 1.52) & (dih[:, 1] < 0) & (np.abs(dih[:, 0]) < 0.14)
print("DIHEDRAL throat+chest: %d edges, mean %.1f deg, p90 %.1f, p99 %.1f, edge len mean %.1f mm"
      % (m.sum(), dih[m, 3].mean(), np.percentile(dih[m, 3], 90), np.percentile(dih[m, 3], 99), 1000 * dih[m, 4].mean()))
m2 = (dih[:, 2] > 0.9) & (dih[:, 2] < 1.2)
print("DIHEDRAL hips/belly (z 0.9-1.2): %d edges, mean %.1f, p90 %.1f, p99 %.1f, edge len mean %.1f mm"
      % (m2.sum(), dih[m2, 3].mean(), np.percentile(dih[m2, 3], 90), np.percentile(dih[m2, 3], 99), 1000 * dih[m2, 4].mean()))
# The worst corners in the chest region, where.
r = regions["throat+chest front (z 1.30-1.52, y<0, |x|<0.12)"]
idx = np.where(r)[0][np.argsort(-ang[r])[:15]]
for i in idx:
    print("  worst corner at", np.round(P[i], 3), "%.1f deg" % ang[i])
# Do corners at one vertex disagree (split normals) or agree but lean (custom smooth set)?
spread = np.zeros(len(V))
for vi in range(len(V)):
    pass
cn_by_v = {}
for li, vi in enumerate(LV):
    cn_by_v.setdefault(vi, []).append(CN[li])
sp_ = np.array([max(np.degrees(np.arccos(np.clip(np.dot(a, b), -1, 1))) for a in L for b in L) if len(L) > 1 else 0 for L in cn_by_v.values()])
vk = np.array(list(cn_by_v.keys()))
mv = (V[vk, 2] > 1.30) & (V[vk, 2] < 1.52) & (V[vk, 1] < 0) & (np.abs(V[vk, 0]) < 0.12)
print("SPLIT at a vertex (throat+chest): vertices %d, with corners disagreeing >5deg: %d, >20deg: %d" % (mv.sum(), (sp_[mv] > 5).sum(), (sp_[mv] > 20).sum()))
print("SPLIT at a vertex (all): >5deg %d, >20deg %d of %d" % ((sp_ > 5).sum(), (sp_ > 20).sum(), len(sp_)))
