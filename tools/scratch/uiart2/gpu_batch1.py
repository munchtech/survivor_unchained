"""UI art's first GPU batch: the materials, the flask, Crashing Leap's second concept.
Run only while holding the gpu turn. Frees ComfyUI's models at the end."""
import os
import sys
import time

sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748\tools\uiforge")
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748\tools\comfy")
import comfy  # noqa: E402
import emblems  # noqa: E402
import items  # noqa: E402
import kit  # noqa: E402

t0 = time.time()
try:
    res = kit.paint_materials()
    for k, v in res.items():
        print("material", k, [os.path.getmtime(p) > t0 for p in v], v, flush=True)
    res = items.t2i(["flask"], seed=1100, n=4)
    for k, v in res.items():
        print("item", k, [os.path.getmtime(p) > t0 for p in v], flush=True)
    for dn in (0.55, 0.62):
        res = emblems.paint_many(["leap2"], dn, 1340, n=3, guides=False)
        for k, v in res.items():
            print("emblem", k, [os.path.getmtime(p) > t0 for p in v], flush=True)
finally:
    try:
        comfy.post("/free", {"unload_models": True, "free_memory": True})
        print("freed", flush=True)
    except Exception as e:  # noqa: BLE001
        print("free failed", e)
    print("took", int(time.time() - t0), "s")
