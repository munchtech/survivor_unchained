import bpy
from bl_ext.user_default.mpfb.services.humanservice import HumanService
hm = HumanService.create_human(mask_helpers=True, detailed_helpers=True, extra_vertex_groups=True, feet_on_ground=True, scale=0.1)
names = [g.name for g in hm.vertex_groups]
print("VG", len(names))
print("VG", [n for n in names if any(k in n.lower() for k in ("ear", "head", "face", "scalp", "eye", "lip", "nose", "jaw", "mouth", "neck"))])
