import bpy
import numpy as np
o = bpy.data.objects["Hero"]
co = np.array([(o.matrix_world @ v.co)[:] for v in o.data.vertices])
print("TOP", co[:, 2].max().round(3))
mid = co[np.abs(co[:, 0]) < 0.01]
# front profile: min y per z band; back profile: max y per z band
for z in np.arange(1.40, 1.99, 0.02):
    m = np.abs(mid[:, 2] - z) < 0.01
    if m.any():
        sl = co[np.abs(co[:, 2] - z) < 0.005]
        print("Z %.2f front y %.3f back y %.3f  half-width %.3f" % (z, mid[m, 1].min(), mid[m, 1].max(), np.abs(sl[:, 0]).max() if len(sl) else 0))
arm = bpy.data.objects["Armature"]
for b in ("neck_01", "Head", "spine_03", "clavicle_l", "upperarm_l"):
    print("BONE", b, np.round((arm.matrix_world @ arm.data.bones[b].head_local)[:], 3))
