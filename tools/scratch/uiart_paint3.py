"""UI art: repaint the Muster-Cord (no letter shape), the Cracked Lamp-Glass (not a horn) and
Wenna's flask (warm light, no marks); four takes each at seed 1130, each take cut and fitted
into the scratchpad to judge. Run inside the gpu turn; frees ComfyUI at the end."""
import json
import os
import sys
import urllib.request

WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa9c11f1e40170a4d"
SCR = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad"
sys.path.insert(0, os.path.join(WT, "tools", "uiforge"))
os.chdir(os.path.join(WT, "tools", "uiforge"))
import items  # noqa: E402
import krea  # noqa: E402

SEED = 1130
JOBS = {
    "red_cord": "a hank of faded red cord coiled round in several loose loops, bound once round the middle of the hank, "
                "its frayed end hanging free below, small tight knots tied all along the cord at even intervals, nothing else",
    "lamp_glass": "the tall glass chimney of an old oil lamp standing upright, a bulging tube of thick smoky amber glass, "
                  "a long crack running down one side and a jagged piece broken out of its rim, a small ember-orange flame "
                  "glowing inside it behind the glass, a dented blackened brass collar round its foot, soot streaks",
    # The crafting lead's (their items.py at c8110833, word for word): the scars' steeping material.
    "scar_glass": "a jagged shard of dark smoky glass, nearly black, a cold pale blue glow like a lamp flame trapped "
                  "deep inside it, a thin crust of scorched earth and ash on one edge",
    "flask": "a flat pewter hip flask in a stitched brown leather sleeve, a small screw cap on a short chain, worn and "
             "dented, warm candlelight gleaming on the pewter, plain metal with no marks, no engraving, no letters",
}

try:
    made = krea.t2i_many([(k, items.LOOK + p + ".", SEED) for k, p in JOBS.items()], tag="items_t2i", n=4)
    print({k: len(v) for k, v in made.items()}, flush=True)
    for k in JOBS:
        for j in range(4):
            items.OUT = os.path.join(SCR, "uiart_fit", f"{k}_{j}")
            items.fit(k, (SEED, j))
            print("fit", k, j, flush=True)
finally:
    req = urllib.request.Request("http://127.0.0.1:8188/free", data=json.dumps({"unload_models": True, "free_memory": True}).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=30)
        print("freed", flush=True)
    except OSError as e:
        print("free failed", e, flush=True)
