"""lamp_glass again (the 1130 takes read as a whole oil lamp), then fit the picks: red_cord,
scar_glass, flask at the set's 0.82; Crashing Leap from em_leap2_55_1340_0. Inside a gpu turn."""
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
import krea  # noqa: E402

LAMP = ("the empty glass chimney of an oil lamp lying on its side by itself, a bulging tube of thick smoky amber "
        "glass open at both ends, a long crack down its side and a jagged piece broken out of its rim, a tiny "
        "ember-orange flame still glowing caught inside the glass, soot streaks, no lamp, no base, no brass, "
        "only the glass")
t0 = time.time()
try:
    made = krea.t2i_many([("lamp_glass", items.LOOK + LAMP + ".", 1140)], tag="items_t2i", n=4)
    print("lamp_glass", [os.path.getmtime(p) >= t0 for p in made["lamp_glass"]], flush=True)
    for j in range(4):
        items.OUT = os.path.join(SCR, "fit", f"lamp_glass_b{j}")
        items.fit("lamp_glass", (1140, j), fill=0.82)
    items.OUT = os.path.join(WT, "godot", "art", "ui", "icons", "item")
    for k, j in (("red_cord", 2), ("scar_glass", 3), ("flask", 2)):
        items.fit(k, (1130, j), fill=0.82)
        print("fit", k, flush=True)
    emblems.fit("leap2", os.path.join(emblems.RAW, "em_leap2_55_1340_0.png"),
                os.path.join(WT, "godot", "art", "ui", "icons", "glyph_color", "leap.png"))
    print("fit leap", flush=True)
finally:
    req = urllib.request.Request("http://127.0.0.1:8188/free", data=json.dumps({"unload_models": True, "free_memory": True}).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=30)
        print("freed", flush=True)
    except OSError as e:
        print("free failed", e, flush=True)
