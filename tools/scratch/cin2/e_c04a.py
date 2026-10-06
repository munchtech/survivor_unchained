import copy

EYES = {"actor": "her", "bone": "eyes"}


def edit(S, f):
    f["draft"] = "Previs pass 1: surveyed on the north bank at dawn, stand-in motion and effects (Kimodo's wade_out, sun_face, flask_drink and walk_uphill, the ember draining, breath-smoke) to come."
    f["marks"]["shallows"] = [2.0, -41.0, 1.5708]
    f["marks"]["top"] = [0.2, -66.0, 3.1416]
    f["end"]["her"] = "top"
    a1 = S["A1"]
    a1["when"] = {"facts": ["!prologue.dawn_south"]}
    a1["cam"] = {"pos": [1.9, 0.3, -52.5], "at": {"abs": [0.8, -0.7, -47.0]}, "lens": 35}
    a1["cues"] = [
        {"do": "event", "name": "ford_clear"},
        {"do": "atmosphere", "preset": "dawn", "from": "night", "k1": 0.2},
        {"do": "music", "mood": "night", "intensity": 0.2},
        {"do": "place", "mark": "bank"},
        {"do": "move", "to": "road", "dur": 4.0, "clip": "Walk_Formal_Loop", "speed": 0.8},
        {"at": 3.9, "do": "anim", "clip": "@idle", "blend": 0.4},
        {"do": "prints", "from": [1.0, -49.0], "to": [0.6, -57.0], "stride": 0.8},
        {"at": 0.2, "do": "sfx", "name": "cloth_water", "gain": 0.6},
    ]
    south = {
        "id": "A1s", "type": "MS", "dur": 4.0, "when": {"facts": ["prologue.dawn_south"]},
        "note": "Still south, looting the ford: an MS of her standing in the shallows, turning toward the light that is starting in the east.",
        "cam": {"pos": {"abs": [-1.2, -0.3, -43.6]}, "at": {"actor": "her", "bone": "chest"}, "lens": 35},
        "cues": [
            {"do": "event", "name": "ford_clear"},
            {"do": "atmosphere", "preset": "dawn", "from": "night", "k1": 0.2},
            {"do": "music", "mood": "night", "intensity": 0.2},
            {"do": "place", "mark": "shallows", "heading": 0.0},
            {"do": "anim", "clip": "@idle", "blend": 0},
            {"at": 1.2, "do": "look", "where": [30.0, 2.0, -41.0], "over": 1.6},
        ],
    }
    f["shots"].insert(1, south)
    S["A2"]["cam"] = {"pos": [-5.0, 1.4, -58.0], "at": [10.0, 9.0, -64.0], "lens": 35}
    S["A2"]["cues"] = [
        {"do": "atmosphere", "preset": "dawn", "from": "night", "k0": 0.2, "over": 10.0},
        {"do": "place", "mark": "road"},
        {"do": "anim", "clip": "@idle", "blend": 0},
    ]
    S["A4"]["cues"].append({"at": 1.2, "do": "vfx", "kind": "nova", "where": {"mark": "road"}, "radius": 1.6, "school": "fire", "dur": 1.8})
    S["A5"]["cam"] = {"pos": {"actor": "her", "bone": "eyes", "off": [0.25, -0.02, -1.25]}, "at": EYES, "lens": 85, "focus": EYES, "fstop": 2.0}
    S["A6"]["cam"] = {"pos": {"actor": "her", "bone": "eyes", "off": [0.5, -0.15, -1.9]}, "at": {"actor": "her", "bone": "eyes", "off": [0, -0.12, 0]}, "lens": 50}
    S["A7"]["cam"] = {"pos": {"actor": "her", "bone": "eyes", "off": [0.08, 0.0, -1.15]}, "at": EYES, "lens": 85, "focus": EYES, "fstop": 2.0, "move": {"push": 0.05, "ease": "linear"}}
    for c in S["A8"]["cues"]:
        if c.get("do") == "move":
            c["to"] = "top"
