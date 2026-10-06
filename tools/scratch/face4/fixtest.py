import os
import shutil
import sys

import bpy
import numpy as np

W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a833b7942e978d994"
SC = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face4"
sys.path.insert(0, W + r"\tools\assets")
import heroine_face_fixes as hf  # noqa: E402

head = bpy.data.objects["HeroineHead"]
kb = head.data.shape_keys.key_blocks
print("KEYS face_:", [k.name for k in kb if k.name.startswith("face_")])
P0 = hf.shaped(head)
hf.SHAPE_KEY = "face_vixen"
P1 = hf.shaped(head)
print("KEY moves up to %.1f mm" % (1000 * np.linalg.norm(P1 - P0, axis=1).max()))
raw = W + r"\tools\comfy\out\heroes\heroine_head_raw_vixen.jpg"
for key in (None, "face_vixen"):
    out = SC + r"\fix_%s.jpg" % (key or "none")
    shutil.copy(raw, out)
    hf.fix(head, out, raw=raw, key=key)
print("DONE")
