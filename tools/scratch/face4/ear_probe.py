"""Where her ears and neck are (for the hairline and the neck's keep-out)."""
import sys

import bpy
import numpy as np

sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a833b7942e978d994\tools\assets")
args = sys.argv[sys.argv.index("--") + 1:]
sys.argv = sys.argv[:sys.argv.index("--") + 1] + [args[0]]
import heroine_hair as hh  # noqa: E402

head = hh.head
kb = head.data.shape_keys.key_blocks
base = np.array([v.co[:] for v in kb["Basis"].data])
for k in ("ears_size+", "ears_out+", "ears_pointed+", "ears_lobes+", "ears_size-"):
    d = np.linalg.norm(np.array([v.co[:] for v in kb[k].data]) - base, axis=1)
    for thr in (0.0003, 0.001, 0.002):
        m = d > thr
        P = hh.HP[m]
        th = np.degrees(np.arctan2(np.abs(P[:, 0]), -P[:, 1]))
        print(k, thr, m.sum(), "theta %.0f..%.0f" % (th.min(), th.max()) if m.any() else "",
              "z-eye %.3f..%.3f" % (P[:, 2].min() - hh.EYE_Z, P[:, 2].max() - hh.EYE_Z) if m.any() else "",
              "|x| %.3f..%.3f y %.3f..%.3f" % (np.abs(P[:, 0]).min(), np.abs(P[:, 0]).max(), P[:, 1].min(), P[:, 1].max()) if m.any() else "")
print("EYE_Z", hh.EYE_Z)
mw = hh.arm.matrix_world
for n in ("neck_01", "Head", "spine_03", "clavicle_l"):
    b = hh.arm.data.bones.get(n)
    if b:
        print(n, np.round(np.array((mw @ b.head_local)[:]), 3), np.round(np.array((mw @ b.tail_local)[:]), 3))
# neck: skin points at heights below the jaw
for dz in (-0.08, -0.10, -0.12, -0.14, -0.16, -0.18, -0.20):
    z = hh.EYE_Z + dz
    m = (np.abs(hh.COLLIDE_P[:, 2] - z) < 0.004) & (np.abs(hh.COLLIDE_P[:, 0]) < 0.12) & (np.abs(hh.COLLIDE_P[:, 1]) < 0.12)
    P = hh.COLLIDE_P[m]
    if len(P):
        print("z-eye %.2f: x %.3f..%.3f  y %.3f..%.3f  n=%d" % (dz, P[:, 0].min(), P[:, 0].max(), P[:, 1].min(), P[:, 1].max(), len(P)))
