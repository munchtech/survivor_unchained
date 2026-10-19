# k13a (C01): round 2's one-action fixes and cuts (k12A_verdict.md), scoped to what carries over to the new art.
def edit(shots, f):
    S = f["shots"]
    # Fire: soft shadows scene-wide (light_size 0.4 m; given back at the end).
    for c in shots["1"]["cues"]:
        if c.get("do") == "light" and c.get("light") == 0: c["size"] = 0.4
    # CUT s2: its two drips onto s3 at the same offsets.
    s3 = shots["3"]
    s3["cues"] += [{"at": 1.4, "do": "sfx", "name": "drip", "pan": 0.1}, {"at": 2.6, "do": "sfx", "name": "drip", "pan": 0.05}]
    # s3: a warm 2700 K key from the coals' side, low (bottom of frame, 65 deg off the lens), fill ~1/5,
    # the moon cool from the top of frame (narrow, on her head only, so the chest third falls dark); eyes 22 deg off the lens toward the key.
    keep = [c for c in s3["cues"] if c.get("name") not in ("moon", "ember")]
    i = next(k for k, c in enumerate(keep) if c.get("do") == "light")
    keep[i + 1:i + 1] = [
        {"do": "rig", "name": "key", "energy": 0.5, "color": "#ffa757", "angle": 20, "from": {"actor": "her", "bone": "head", "off": [-0.34, -0.72, 0.0]}, "aim": {"actor": "her", "bone": "head"}},
        {"do": "rig", "name": "moon", "energy": 0.35, "color": "#a9bfff", "angle": 12, "from": {"actor": "her", "bone": "head", "off": [0.15, 1.0, 0.25]}, "aim": {"actor": "her", "bone": "head"}},
        {"do": "rig", "name": "fill", "energy": 0.1, "color": "#ffdcc0", "angle": 25, "from": {"lens": [0, 0.05, 0]}, "aim": {"actor": "her", "bone": "head"}},
        {"at": 1.9, "do": "gaze", "look": [0.7, 0.05], "wander": 0.02},
    ]
    s3["cues"] = keep
    # s6: the per-shot saturation grade (firelit skin ran 0.61-0.72).
    for c in shots["6"]["cues"]:
        if c.get("do") == "grade": c["sat"] = 0.62
    # CUT s6a (s6 to s7): its held hand pose and its cloth sound carried onto s7.
    shots["7"]["cues"][0:0] = [{"do": "anim", "clip": "her/reach_coals", "from": 2.0, "speed": 1.0, "blend": 0}]
    shots["7"]["cues"].append({"at": 0.3, "do": "sfx", "name": "cloth_water", "gain": 0.3})
    # s7: half the field of view, tilted down onto the prints in the frost (trail from bottom-centre up), her head a soft
    # dark edge at frame-left; then the same tilt up along the trail.
    c7 = shots["7"]["cam"]
    c7.update({"pos": [-9.54, 1.3, 91.8], "at": [-8.66, 0.0, 86.6], "lens": 60, "focus": 4.2})
    # s8b: lips closed to a hairline for the listening beat.
    for c in shots["8b"]["cues"]:
        if c.get("do") == "face" and "at" not in c: c["over"] = 0.3
    # s8a: the gold lamp small, its halo cut (the move into the gatehouse is skipped: today's castle).
    i = next(k for k, c in enumerate(shots["8a"]["cues"]) if c.get("do") == "mist")
    shots["8a"]["cues"].insert(i, {"do": "glow", "name": "tower", "where": {"abs": [3.0, 44.0, -260.0]}, "color": "#ffc870", "size": 0.35, "spread": 4, "halo": 0.45, "clear": True})
    # s9: the riser comes up in the gap past the warm pool (frame x ~540), rimmed warm by the coals, a faint cool top.
    f["marks"]["r1"] = [-14.3, 90.0]
    for c in shots["9"]["cues"]:
        if c.get("name") == "r1rim": c.update({"energy": 1.2, "from": {"mark": "r1", "off": [-1.2, 2.4, -0.6]}, "aim": {"mark": "r1", "off": [0, 1.2, 0]}})
    j = next(k for k, c in enumerate(shots["9"]["cues"]) if c.get("name") == "r1rim")
    shots["9"]["cues"].insert(j + 1, {"at": 1.3, "do": "rig", "name": "r1coal", "energy": 2.5, "color": "#ff8a45", "angle": 25, "range": 6, "from": {"mark": "r1", "off": [2.6, 0.4, 0.35]}, "aim": {"mark": "r1", "off": [0, 1.3, 0]}})
    # s10: out on the first lift (0.2 s earlier).
    shots["10"]["dur"] = 0.35
    # CUT s11: her setup (place, weapons in hand), the three risers and their sounds, the arcanist's spell onto s12.
    s12 = shots["12"]
    s12["cam"] = {"pos": [-8.9, 1.55, 85.6], "at": {"actor": "her", "bone": "chest", "off": [0, 0.2, 0], "track": True}, "lens": 35,
                  "move": {"path": [[-7.3, 1.6, 85.83], [-5.27, 2.3, 86.91], [-2.99, 5.0, 89.64], [-3.11, 10.0, 95.49], [-8.9, 19.9, 101.2]],
                           "start": 0, "end": "end", "ease": "inout", "follow": True, "followFrom": 0.5}}
    old = [c for c in s12["cues"] if c.get("do") != "mist"]
    for c in old:
        if c.get("do") == "sfx" and c.get("name") == "rasp": c["at"] = 0.5
    setup = [
        {"do": "grade", "sat": 0.72},
        {"at": 1.2, "do": "grade", "sat": 1, "over": 2.0},
        {"do": "head", "amount": 0, "over": 0.25},
        {"do": "place", "mark": "reach", "heading": 3.1416},
        {"do": "prop", "name": "weapon", "remove": True},
        {"do": "prop", "name": "shield", "remove": True},
        {"do": "hold", "slot": "all", "piece": "@own", "when": {"calling": ["warden", "reaver", "stalker"]}},
        {"do": "face", "keys": {"eyes_wide": 0.2, "brows_angry": 0.35, "mouth_open": 0.0}, "over": 0.3},
        {"at": 0.0, "do": "sfx", "name": "hit"},
        {"at": 0.0, "do": "spawn", "actor": "r2", "def": "risen", "mark": "r2", "style": "rise"},
        {"at": 0.15, "do": "spawn", "actor": "r3", "def": "risen", "mark": "r3", "style": "rise"},
        {"at": 0.3, "do": "spawn", "actor": "r4", "def": "risen", "mark": "r4", "style": "rise"},
        {"at": 0.0, "do": "sfx", "name": "frost_crack", "where": {"mark": "r2"}, "gain": 0.6},
        {"at": 0.2, "do": "sfx", "name": "frost_crack", "where": {"mark": "r3"}, "gain": 0.6},
    ]
    arcanist = [
        {"at": 1.35, "do": "anim", "clip": "Spell_Simple_Enter", "from": 0, "speed": 0.9, "blend": 0.2, "when": {"calling": ["arcanist"]}},
        {"at": 1.95, "do": "face", "keys": {"smile": 0.15}, "over": 0.15, "when": {"calling": ["arcanist"]}},
        {"at": 2.45, "do": "face", "keys": {"smile": 0, "brows_angry": 0.3}, "over": 0.2, "when": {"calling": ["arcanist"]}},
        {"at": 2.35, "do": "anim", "clip": "@idle", "from": 0, "speed": 1, "blend": 0.3, "when": {"calling": ["arcanist"]}},
    ]
    # Mist fades as the crane rises: 15% of its density (0.14 -> 0.02) by the time the camera passes 4 m (~1.9 s), gone by 3.4 s.
    mist = [
        {"at": 1.0, "do": "mist", "name": "west", "density": 0.02, "over": 0.9},
        {"at": 1.0, "do": "mist", "name": "north", "density": 0.02, "over": 0.9},
        {"at": 2.4, "do": "mist", "name": "west", "density": 0, "over": 1.0},
        {"at": 2.4, "do": "mist", "name": "north", "density": 0, "over": 1.0},
    ]
    s12["cues"] = setup + old + arcanist + mist
    f["shots"] = [s for s in S if s["id"] not in ("2", "6a", "11")]
