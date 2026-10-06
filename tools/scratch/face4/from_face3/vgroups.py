import bpy, numpy as np, sys, os
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a6784044c82f101d9\tools\assets")
import face_shapes as fs
from bl_ext.user_default.mpfb.services.humanservice import HumanService
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
hm = HumanService.create_human(mask_helpers=True, detailed_helpers=True, extra_vertex_groups=True, feet_on_ground=True,
                               scale=0.1, macro_detail_dict=fs.MACROS)
print("MW", [list(r) for r in hm.matrix_world])
print("NV", len(hm.data.vertices))
cnt = {}
for v in hm.data.vertices:
    for g in v.groups:
        cnt[g.group] = cnt.get(g.group, 0) + 1
for g in hm.vertex_groups:
    print("VG", g.index, g.name, cnt.get(g.index, 0))
print("MODS", [(m.name, m.type) for m in hm.modifiers])
