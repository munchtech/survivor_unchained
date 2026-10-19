# k14 (C01): the final judge round's cuts (k13A_verdict.md): s6, s7, s8b, s9 cut; their lines, setup and resets carried.
def edit(shots, f):
    cut = {"6", "7", "8b", "9"}
    s3, s8, s8a, s10, s12 = shots["3"], shots["8"], shots["8a"], shots["10"], shots["12"]
    s9 = shots["9"]
    # s3: the eye light from 0.0; the bedroll line at 2.8 (was s6).
    s3["cues"].append({"do": "rig", "name": "eye", "energy": 0.2, "color": "#fff3e6", "angle": 5, "from": {"lens": [0, 0.25, 0]}, "aim": {"actor": "her", "bone": "eyes"}})
    s3["cues"].append({"at": 2.8, "do": "line", "id": "cin_drowned_fire.bedroll"})
    s3["fit"] = ["cin_drowned_fire.bedroll"]; s3["tail"] = 0.6
    # s8: her setup from s6/s7 (place, the held reach pose, the head toward the prints, the cloth sound); the prints line (was s7).
    s8["cues"][0:0] = [
        {"do": "place", "mark": "lie"},
        {"do": "anim", "clip": "her/reach_coals", "from": 2.0, "speed": 1.0, "blend": 0},
        {"at": 0.0, "do": "head", "where": [-8.9, 0.3, 86.5], "over": 1.2},
        {"at": 0.3, "do": "sfx", "name": "cloth_water", "gain": 0.3},
        {"at": 0.3, "do": "line", "id": "cin_drowned_fire.prints"},
    ]
    s8["fit"] = ["cin_drowned_fire.prints"]; s8["tail"] = 0.7
    # s8a: the lamp and the call (was s8b), a slow push, R1's rise and the crack at its end (was s9).
    s8a["fit"] = ["cin_drowned_fire.lamp", "cin_drowned_fire.call"]; s8a["tail"] = 0.8
    s8a["cam"]["move"] = {"push": 0.04, "ease": "linear"}
    s8a["cues"] += [
        {"at": "after:cin_drowned_fire.lamp+0.5", "do": "line", "id": "cin_drowned_fire.call"},
        {"at": "end-0.4", "do": "world", "rate": 0.11},
        {"at": "end-0.4", "do": "spawn", "actor": "r1", "def": "risen", "mark": "r1", "style": "rise"},
        {"at": "end-0.4", "do": "sfx", "name": "drone"},
        {"at": "end-0.3", "do": "sfx", "name": "frost_crack", "where": {"mark": "r1"}, "gain": 0.8},
    ]
    # s10: what s8b reset after s8a (the ford's lamps and mist back to play's), now at the first shot after s8a.
    s10["cues"][0:0] = [
        {"do": "glow", "name": "ford4", "remove": True},
        {"do": "glow", "name": "ford5", "remove": True},
        {"do": "glow", "name": "ford6", "remove": True},
        {"do": "mist", "name": "ford", "density": 0},
        {"do": "light", "light": 4, "level": 1.0, "color": "#8ac8ff"},
        {"do": "light", "light": 5, "level": 1.0, "color": "#8ac8ff"},
        {"do": "light", "light": 6, "level": 1.0, "color": "#8ac8ff"},
        {"do": "lit", "light": 7, "on": True},
        {"do": "lit", "light": 8, "on": True},
    ]
    # s12: the face key on to 2.0; the mists s9 made (s12 fades them); the frost line (was s9) and R1's sounds.
    mists = [c for c in s9["cues"] if c.get("do") == "mist"]
    s12["cues"][0:0] = mists + [
        {"do": "rig", "name": "key", "energy": 0.8, "color": "#ffc79a", "angle": 20, "from": {"actor": "her", "bone": "eyes", "off": [-0.6, -0.38, -0.3]}, "aim": {"actor": "her", "bone": "eyes", "off": [0, -0.03, 0]}},
        {"at": 2.0, "do": "rig", "name": "key", "energy": 0},
        {"at": 0.3, "do": "line", "id": "cin_drowned_fire.frost"},
        {"at": 0.4, "do": "sfx", "name": "roots", "where": {"mark": "r1"}},
        {"at": 1.5, "do": "sfx", "name": "rasp", "where": {"mark": "r1"}, "gain": 0.7},
    ]
    f["shots"][:] = [s for s in f["shots"] if s["id"] not in cut]
