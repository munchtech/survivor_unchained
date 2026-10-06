import bpy
import numpy as np
o = bpy.data.objects["hair_ponytail"]
V = np.array([(o.matrix_world @ v.co)[:] for v in o.data.vertices])
eyes = bpy.data.objects["HeroineEyes"]
ez = np.mean([(eyes.matrix_world @ v.co).z for v in eyes.data.vertices])
col = o.data.color_attributes.get("ao")
C = np.zeros(len(V) * 4)
col.data.foreach_get("color", C)
C = C.reshape(-1, 4)
# hair hanging beside her cheek: in front of her ears, below her eyes
m = (V[:, 2] < ez - 0.01) & (V[:, 2] > ez - 0.12) & (V[:, 1] < -0.0) & (np.abs(V[:, 0]) > 0.055) & (np.abs(V[:, 0]) < 0.11)
print("TENDRIL points beside her cheeks:", m.sum(), "alpha mean %.2f" % (C[m, 3].mean() if m.any() else -1))
print("all points", len(V), "z range", V[:, 2].min(), V[:, 2].max(), "eye z", ez)
