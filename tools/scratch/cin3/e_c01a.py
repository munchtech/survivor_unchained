"""C01: animation's three clips in place of the log-sitting stand-in (first pass, cameras kept)."""
import math


def anim_cues(s):
    return [c for c in s["cues"] if c.get("do") == "anim"]


def edit(shots, f):
    # She lies on her right side by the embers, her face to the fire (the clip's +Z).
    fx, fz = f["marks"]["fire"]
    lx, lz = f["marks"]["lie"][0], f["marks"]["lie"][1]
    h = math.atan2(fx - lx, fz - lz)
    f["marks"]["lie"] = [lx, lz, round(h, 4)]
    for c in shots["0"]["cues"]:
        if c.get("do") == "anim":
            c.update({"clip": "her/lie_side_wake", "from": 0, "speed": 0, "blend": 0})
    # The two still breaths run slow under the top shot, the eyes and the hand.
    s2 = shots["2"]
    s2["cues"] = [c for c in s2.get("cues", []) if c.get("do") != "anim"]
    s2["cues"].insert(0, {"do": "anim", "clip": "her/lie_side_wake", "from": 0, "speed": 0.24, "blend": 0})
    # Up onto the elbow, slow, worn out.
    s5 = shots["5"]
    s5["dur"] = 4.5
    s5["cues"] = [c for c in s5["cues"] if c.get("do") != "anim"]
    s5["cues"].append({"at": 0.0, "do": "anim", "clip": "her/lie_side_wake", "from": 2.4, "speed": 1.0, "blend": 0.15})
    # From the elbow onto her knees and back on her heels, looking at her hands.
    s6 = shots["6"]
    s6["cues"] = [c for c in s6["cues"] if c.get("do") not in ("place", "anim")]
    s6["cues"].insert(0, {"do": "anim", "clip": "her/sit_back_heels", "from": 0, "speed": 1.0, "blend": 0})
    # The hand to the coals now comes after she kneels (the clip is from the kneel).
    s7 = shots["7"]
    s7["cues"] = [c for c in s7["cues"] if c.get("do") != "place"]
    s4 = shots["4"]
    f["shots"].remove(s4)
    s4["id"] = "6a"
    s4["note"] = ("The hand to the coals: kneeling, she holds her right hand out low over the embers, palm down, "
                  "closer than anyone could bear, and it stays.")
    s4["cues"] = [c for c in s4.get("cues", []) if c.get("do") != "anim"]
    s4["cues"].insert(0, {"do": "anim", "clip": "her/reach_coals", "from": 0, "speed": 1.0, "blend": 0})
    f["shots"].insert(f["shots"].index(s6) + 1, s4)
