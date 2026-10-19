# k14 (C04 A): A1, A3, A4, A5, A7 cut (k13B_verdict.md); back then face onto A8, which is lengthened to fit them.
def edit(shots, f):
    cut = {"A1", "A3", "A4", "A5", "A7"}
    a8 = shots["A8"]
    a8["cues"][0:0] = [
        {"do": "event", "name": "ford_clear", "when": {"facts": ["!prologue.dawn_south"]}},
        {"do": "atmosphere", "preset": "dawn", "from": "night", "k1": 0.2},
        {"do": "atmosphere", "preset": "dawn", "exposure": 0.78, "hemi": 0.3, "env": 0.3},
        {"do": "globe", "light": 4, "level": 0.25},
        {"do": "globe", "light": 5, "level": 0.25},
        {"do": "globe", "light": 6, "level": 0.25},
        {"do": "place", "mark": "road"},
        {"do": "anim", "clip": "@idle", "blend": 0},
    ]
    # atmosphere/music order: the existing "dawn from now over 1.5" follows; the walk starts 6.5 s from the end as it always ended.
    a8["cues"] = [c for c in a8["cues"] if c.get("do") != "move" and not (c.get("do") == "music")]
    a8["cues"] += [
        {"do": "prints", "from": [1.0, -49.0], "to": [0.6, -57.0], "stride": 0.8, "when": {"facts": ["!prologue.dawn_south"]}},
        {"at": 0.3, "do": "line", "id": "cin_first_light.reeds", "when": {"facts": ["!prologue.reeds_said"]}},
        {"at": "after:cin_first_light.reeds+0.5", "do": "line", "id": "cin_first_light.back", "when": {"facts": ["!prologue.reeds_said"]}},
        {"at": 0.3, "do": "line", "id": "cin_first_light.back", "when": {"facts": ["prologue.reeds_said"]}},
        {"at": 0.3, "do": "sfx", "name": "cloth_water", "gain": 0.4},
        {"at": 1.2, "do": "vfx", "kind": "nova", "where": {"mark": "road"}, "radius": 1.6, "school": "fire", "dur": 1.8},
        {"at": 0.3, "do": "music", "mood": "mystery", "intensity": 0.2, "over": 1.0},
        {"at": "after:cin_first_light.back+0.3", "do": "music", "mood": "silence"},
        {"at": "after:cin_first_light.back+0.8", "do": "line", "id": "cin_first_light.face"},
        {"at": "end-6.5", "do": "move", "to": "top", "dur": 6.5, "clip": "Walk_Formal_Loop", "speed": 0.8},
        {"at": "end-3.0", "do": "music", "mood": "explore", "intensity": 0.35, "over": 2.0},
    ]
    a8["fit"] = ["cin_first_light.back", "cin_first_light.face"]; a8["tail"] = 4.5
    # mist fades: at the crane's start (was 2.5 of 5.5), as they were.
    for c in a8["cues"]:
        if c.get("do") == "mist" and c.get("density") == 0: c["at"] = "end-3.0"
    f["shots"][:] = [s for s in f["shots"] if s["id"] not in cut]
