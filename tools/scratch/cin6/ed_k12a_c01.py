# k12a pass 1 (C01): s2/s3 on death_back's held end pose at heading pi (on her back, the clip's own head turned to her
# left = to the coals, her flung left hand at the ring's edge); s2 reframed on the new layout; s3 at ground level west of
# her face, the face on its side, moon from above, ember low from the coals; s8a ford lamps blue (globe colour, halos,
# blue pools, a mist band on the water); grade cues on s8, s8b, s10.
DOWN = [-9.31, 89.235, 3.1416]   # head lands at about (-9.45, 0.14, 90.45), the left hand at (-9.85, 90.59)
HEAD = [-9.45, 0.15, 90.47]
FORD = {4: (0.0, 3.309, -33.5), 5: (-9.71, 3.26, -49.626), 6: (9.71, 3.67, -49.626)}
CAM8A = (1.8, 1.4, 5.0)
SAT = {"8": 0.72, "8b": 0.78, "10": 0.72}


def toward(p, q, d):
    v = [q[i] - p[i] for i in range(3)]; n = sum(x * x for x in v) ** 0.5
    return [round(p[i] + v[i] / n * d, 3) for i in range(3)]


def edit(shots, f):
    f["marks"]["down"] = DOWN
    s1 = shots["1"]["cues"]
    for c in s1:
        if c.get("do") == "anim": c.update({"clip": "her/death_back", "from": 1.33, "speed": 0, "blend": 0})
        if c.get("do") == "head": c.clear(); c.update({"do": "head", "amount": 0, "over": 0.1})
        if c.get("do") == "gaze": c.update({"look": [0.15, 0.3], "wander": 0.03})
    s1.insert(0, {"do": "place", "mark": "down", "heading": DOWN[2]})

    # s2: straight down at 3 m, the coals upper left, her body on the diagonal to the upper right.
    s2 = shots["2"]
    s2["cam"] = {"pos": [-9.83, 3.0, 90.02], "at": [-9.85, 0.0, 90.0], "lens": 28, "focus": 2.9, "fstop": 4.0,
                 "move": {"pos": [-9.83, 2.7, 90.02], "ease": "slow"}}
    s2["cues"] = [c for c in s2["cues"] if c.get("do") != "anim"]

    # s3: at ground level west of her face (the coals behind the lens), her face on its side.
    s3 = shots["3"]
    s3["cam"] = {"pos": [-10.12, 0.1, 90.52], "at": [HEAD[0], HEAD[1], HEAD[2] + 0.04], "lens": 65,
                 "focus": {"actor": "her", "bone": "head"}, "fstop": 2.0, "move": {"push": 0.03, "ease": "linear"}}
    s3["cues"] = [
        {"do": "atmosphere", "preset": "night", "key": 0.4, "hemi": 0.1575, "env": 0.1575, "exposure": 0.92, "fog": 1.5, "fogColor": "#0a1018", "rim": 0.6, "elevation": 75},
        {"do": "light", "light": 0, "level": 0.06, "color": "#ff9a5a", "rate": 0.45},
        # Moon from overhead and a little behind her: the face's upper side (her right cheek, brow, the nose's ridge).
        {"do": "rig", "name": "moon", "energy": 0.6, "color": "#a9bfff", "angle": 25, "from": {"actor": "her", "bone": "head", "off": [0.25, 1.4, 0.1]}, "aim": {"actor": "her", "bone": "head"}},
        # Ember from the coals, low and narrow on the face: its lower side warm.
        {"do": "rig", "name": "ember", "energy": 0.22, "color": "#ffa860", "angle": 16, "from": {"mark": "fire", "off": [0.35, 0.06, 0.05]}, "aim": {"actor": "her", "bone": "head", "off": [0, -0.02, 0]}},
        {"at": 2.0, "do": "lids", "value": 0, "over": 0.35},
        {"at": 2.0, "do": "face", "keys": {"eyes_wide": 0.1}, "over": 0.4},
        {"at": 2.8, "do": "face", "keys": {"eyes_wide": 0.0}, "over": 1.0},
        {"at": 2.4, "do": "lids", "value": None},
    ]

    # s8a: the ford's three lamps blue and small.
    s8a = shots["8a"]
    keep = [c for c in s8a["cues"] if c.get("do") not in ("light", "globe")]
    ford = []
    for i, p in FORD.items():
        ford.append({"do": "light", "light": i, "level": 0.55, "color": "#6e9bff"})
        ford.append({"do": "globe", "light": i, "level": 0.3, "color": "#6e9bff"})
        ford.append({"do": "glow", "name": f"ford{i}", "where": toward(p, CAM8A, 0.6), "color": "#7aa2ff", "size": 0.07, "energy": 5, "spread": 16, "halo": 0.45, "clear": True})
    ford.append({"do": "mist", "name": "ford", "where": [0.0, -1.05, -44.0], "size": [80, 1.4, 30], "density": 0.3, "color": "#5a6e8c", "falloff": 3.0, "grain": 0.2, "sink": 0.1})
    s8a["cues"] = [{"do": "grade", "sat": 1}] + keep[:1] + ford + keep[1:]

    # s8b: the ford's halos and mist go (they would show past the camp), the grade for her face.
    s8b = shots["8b"]
    s8b["cues"] = [{"do": "grade", "sat": SAT["8b"]}] + [{"do": "glow", "name": f"ford{i}", "remove": True} for i in FORD] + \
                  [{"do": "mist", "name": "ford", "density": 0}] + s8b["cues"]
    shots["8"]["cues"].insert(0, {"do": "grade", "sat": SAT["8"]})
    shots["9"]["cues"].insert(0, {"do": "grade", "sat": 1})
    shots["10"]["cues"].insert(0, {"do": "grade", "sat": SAT["10"]})
    shots["11"]["cues"].insert(0, {"do": "grade", "sat": 1})
