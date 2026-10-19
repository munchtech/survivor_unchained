import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# k11a pass 3 (C01): death's held end pose puts her face into the ground (no ground-level lens finds it): back to
# lie_side_wake (k10's s1/s2), her head tipped to the coals; s3 on it from the face's north-west at ground level, roll 0,
# the moon high so the breastplate's shadow falls to the ground, not her throat. s8/s8b keys paler (face saturation).
from ed_k11a_c01 import air, FIRE


def edit(shots, f):
    s1 = shots["1"]
    s1["cues"] = [c for c in s1["cues"] if c.get("do") not in ("place", "head") and not (c.get("do") == "anim")]
    i = next(k for k, c in enumerate(s1["cues"]) if c.get("do") == "gaze") + 1
    s1["cues"][i:i] = [{"do": "anim", "clip": "her/lie_side_wake", "from": 0, "speed": 0, "blend": 0}]
    s1["cues"].append({"do": "head", "where": [-10.2, 0.0, 90.2], "amount": 1.0, "over": 0.3})
    s2 = shots["2"]
    s2["cam"] = {"pos": [-9.95, 4.0, 90.62], "at": [-9.97, 0.0, 90.6], "lens": 28, "focus": 3.9, "fstop": 4.0, "move": {"pos": [-9.95, 3.6, 90.62], "ease": "slow"}}
    for c in s2["cues"]:
        if c.get("do") == "anim": c.update({"clip": "her/lie_side_wake", "from": 0, "speed": 0.24, "blend": 0})
    s3 = shots["3"]
    s3["cam"]["pos"]["off"] = [-0.4, -0.16, -0.38]
    s3["cam"]["at"]["off"] = [0, -0.01, 0]
    for k, c in enumerate(s3["cues"]):
        if c.get("do") == "atmosphere": s3["cues"][k] = air(hemi=0.35, env=0.35, elevation=75)
        if c.get("do") == "rig" and c["name"] == "moon": c["from"]["off"] = [0.05, 1.1, -0.25]
        if c.get("do") == "rig" and c["name"] == "ember": c["from"]["off"] = [-0.75, -0.2, 0.1]
    for sid in ("8", "8b"):
        for c in shots[sid]["cues"]:
            if c.get("do") == "rig" and c["name"] == "key": c["color"] = "#ffc79a"
    for c in shots["8"]["cues"]:
        if c.get("do") == "light" and c.get("light") == 0: c["color"] = "#ffb47c"
    shots["10"]["dur"] = 0.55
