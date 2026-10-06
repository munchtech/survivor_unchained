"""Where each MakeHuman head target moves the man's head: cranium vs jaw (mm)."""
import os, sys
import bpy
import numpy as np
from bl_ext.user_default.mpfb.services.humanservice import HumanService
from bl_ext.user_default.mpfb.services.targetservice import TargetService
MACROS = {"gender": 1.0, "age": 0.56, "muscle": 0.95, "weight": 0.55, "proportions": 1.0, "height": 0.6, "cupsize": 0.5,
          "firmness": 0.5, "race": {"african": 0.0, "asian": 0.0, "caucasian": 1.0}}
hm = HumanService.create_human(mask_helpers=True, detailed_helpers=True, extra_vertex_groups=True, feet_on_ground=True,
                               scale=0.1, macro_detail_dict=MACROS)
TD = os.path.join(bpy.utils.user_resource("EXTENSIONS"), "user_default", "mpfb", "data", "targets", "head")


def pts():
    e = hm.evaluated_get(bpy.context.evaluated_depsgraph_get())
    m = e.to_mesh()
    V = np.array([v.co[:] for v in m.vertices])
    e.to_mesh_clear()
    return V @ np.array(hm.matrix_world)[:3, :3].T


for mo in hm.modifiers:
    mo.show_viewport = False
base = pts()
body = hm.vertex_groups["body"].index
inb = np.array([any(g.group == body for g in v.groups) for v in hm.data.vertices])
top = base[inb, 2].max()
head = inb & (base[:, 2] > top - 0.26)
z = base[:, 2]
cran = head & (z > top - 0.09)
jaw = head & (z < top - 0.17)
print("head top", top)
for name in ["head-square", "head-scale-vert-decr", "head-oval", "head-round", "head-back-scale-depth-incr", "head-scale-depth-incr",
             "head-age-incr", "head-rectangular", "head-diamond"]:
    k = TargetService.load_target(hm, os.path.join(TD, name + ".target.gz"), weight=1.0, name="t_" + name)
    bpy.context.view_layer.update()
    d = pts() - base
    mag = np.linalg.norm(d, axis=1) * 1000
    # crown height change and back-of-head change
    print("%-28s cranium %.1f mm (dz top %.1f, dy back %.1f, dx side %.1f)  jaw %.1f mm" % (
        name, mag[cran].mean(), d[cran & (z > top - 0.02), 2].mean() * 1000,
        d[cran & (base[:, 1] > np.percentile(base[cran, 1], 90)), 1].mean() * 1000,
        (np.sign(base[cran, 0]) * d[cran, 0])[np.abs(base[cran, 0]) > 0.06].mean() * 1000, mag[jaw].mean()))
    hm.shape_key_remove(hm.data.shape_keys.key_blocks["t_" + name])
