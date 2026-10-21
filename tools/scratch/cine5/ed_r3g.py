# cine6 r3g: CUT s5 (the judge's fallback: no camera shows the lamp drowning and the fold without the placeholder or the env
# marks failing it); s6 opens on him already down (the fold clip's end), the water closing, the title. s9 heart lower in his claws.
def edit(shots, f):
    s6, s9 = shots["6"], shots["9"]
    s6["dur"] = 3.6
    for c in s6["cues"]:
        if c.get("do") == "atmosphere": c.pop("key", None); c.pop("hemi", None)
        if c.get("do") == "move" and c.get("actor") == "heart": c["dur"] = 3.2
    s6["cues"] = [
        {"do": "skin", "sky": 0.3, "ear": 0.4},
        {"do": "anim", "actor": "warden", "clip": "folk/m_fold_forward", "from": 3.5, "speed": 1, "blend": 0.0},
        {"do": "lamp", "actor": "warden", "glow": 0.0},
        {"do": "sfx", "name": "water_close", "gain": 0.4},
        {"at": 0.3, "do": "title", "title": "The Ford-Warden falls", "kind": "boon", "seconds": 2.6},
    ] + s6["cues"]
    for c in s9["cues"]:
        if c.get("do") == "move" and c.get("actor") == "heart": c["to"] = {"mark": "her", "off": [0.82, 0.62, -0.68]}
    f["shots"] = [s for s in f["shots"] if s["id"] != "5"]
