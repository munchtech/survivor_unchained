import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# k11a pass 2 (C01): her face to the coals (death's end pose faces east at heading 0: turned to pi); s3 from her face's
# north-west at ground level; s2 re-centred; s10 lens at her eye height (abs), slower rise; s8/s8b keys softer and less
# saturated, exposure down; s7/s9 less dark; the ford globes dimmer.
from ed_k11a_c01 import air, FIRE

KEY = "#ffbd85"


def edit(shots, f):
    for c in shots["1"]["cues"]:
        if c.get("do") == "place": c.update({"where": [-9.536, 91.561], "heading": 3.1416})
    s2 = shots["2"]
    s2["cam"]["pos"] = [-10.0, 3.25, 90.88]; s2["cam"]["at"] = [-10.0, 0.0, 90.86]; s2["cam"]["move"]["pos"] = [-10.0, 2.95, 90.88]
    s3 = shots["3"]
    s3["cam"]["pos"]["off"] = [-0.4, -0.07, -0.38]
    s3["cam"]["at"]["off"] = [0, -0.04, 0]
    for c in s3["cues"]:
        if c.get("do") == "rig" and c["name"] == "moon": c["from"]["off"] = [0.1, 1.1, -0.3]
        if c.get("do") == "rig" and c["name"] == "ember": c["from"]["off"] = [-0.75, -0.06, -0.05]

    cu8 = air(hemi=0.35, env=0.35, exposure=0.75)
    for sid in ("8", "8b"):
        s = shots[sid]
        for i, c in enumerate(s["cues"]):
            if c.get("do") == "atmosphere": s["cues"][i] = dict(cu8)
            if c.get("do") == "rig" and c["name"] == "key": c.update({"energy": 0.8, "color": KEY})
            if c.get("do") == "rig" and c["name"] == "fill": c.update({"energy": 0.2, "color": "#a8c0ff"})
        s["cam"]["at"] = {"actor": "her", "bone": "eyes", "off": [0.045, -0.02, 0]}
    shots["8"]["cues"].insert(1, FIRE(0.12, "#ffad70"))
    shots["8"]["cues"] = [c for i, c in enumerate(shots["8"]["cues"]) if not (c.get("do") == "light" and c.get("light") == 0 and c.get("level") == 0.16)]
    s8b = shots["8b"]
    s8b["cam"]["lens"] = 70
    s8b["cam"]["pos"]["off"] = [0.06, -0.02, -0.98]
    s8b["cam"].pop("move", None)

    s10 = shots["10"]
    s10["dur"] = 0.6
    s10["cam"]["pos"] = {"abs": [-11.6, 0.98, 91.245]}
    s10["cam"]["at"] = {"abs": [-9.744, 1.0, 90.863]}
    s10["cam"]["lens"] = 50
    for c in s10["cues"]:
        if c.get("do") == "anim": c.update({"at": 0.15, "from": 0.25, "speed": 0.6})
        if c.get("do") == "look": c.update({"at": 0.28, "over": 0.45})
        if c.get("do") == "rig" and c["name"] == "key": c["color"] = KEY
        if c.get("do") == "light" and c.get("light") == 0: c.update({"level": 0.12, "color": "#ffad70"})

    for c in shots["7"]["cues"]:
        if c.get("do") == "atmosphere": c.update(air(hemi=0.8, env=0.8))
        if c.get("do") == "light" and c.get("light") == 0: c["level"] = 0.12
    for c in shots["9"]["cues"]:
        if c.get("do") == "atmosphere": c.update(air(key=0.6, hemi=0.7, env=0.7))
    for c in shots["8a"]["cues"]:
        if c.get("do") == "globe": c["level"] = 0.1
