"""UI art's GPU batch: macro materials, the four icon repaints, Crashing Leap's second concept.
Run only while holding the gpu turn. Frees ComfyUI's models at the end, whatever happens.
Every output is checked to be new (the machine has run out of memory before)."""
import json
import os
import sys
import time
import urllib.request

WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748"
SCR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(WT, "tools", "uiforge"))
os.chdir(os.path.join(WT, "tools", "uiforge"))
import emblems  # noqa: E402
import items  # noqa: E402
import kit  # noqa: E402
import krea  # noqa: E402

SEED = 1130
ICONS = {
    "red_cord": "a hank of faded red cord coiled round in several loose loops, bound once round the middle of the hank, "
                "its frayed end hanging free below, small tight knots tied all along the cord at even intervals, nothing else",
    "lamp_glass": "the tall glass chimney of an old oil lamp standing upright, a bulging tube of thick smoky amber glass, "
                  "a long crack running down one side and a jagged piece broken out of its rim, a small ember-orange flame "
                  "glowing inside it behind the glass, a dented blackened brass collar round its foot, soot streaks",
    "scar_glass": "a jagged shard of dark smoky glass, nearly black, a cold pale blue glow like a lamp flame trapped "
                  "deep inside it, a thin crust of scorched earth and ash on one edge",
    "flask": "a flat pewter hip flask in a stitched brown leather sleeve, a small screw cap on a short chain, worn and "
             "dented, warm candlelight gleaming on the pewter, plain metal with no marks, no engraving, no letters",
}


def fresh(paths, t0):
    return [p for p in paths if os.path.exists(p) and os.path.getmtime(p) >= t0]


t0 = time.time()
try:
    res = kit.paint_materials()
    for k, v in res.items():
        print("material", k, len(fresh(v, t0)), "new of", len(v), flush=True)
    made = krea.t2i_many([(k, items.LOOK + p + ".", SEED) for k, p in ICONS.items()], tag="items_t2i", n=4)
    for k, v in made.items():
        print("icon", k, len(fresh(v, t0)), "new of", len(v), flush=True)
    for dn in (0.55, 0.62):
        res = emblems.paint_many(["leap2"], dn, 1340, n=3, guides=False)
        for k, v in res.items():
            print("emblem", k, len(fresh(v, t0)), "new of", len(v), flush=True)
finally:
    req = urllib.request.Request("http://127.0.0.1:8188/free", data=json.dumps({"unload_models": True, "free_memory": True}).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=30)
        print("freed", flush=True)
    except OSError as e:
        print("free failed", e, flush=True)
    print("took", int(time.time() - t0), "s", flush=True)
