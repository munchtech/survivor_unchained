# Staging solver k11a (C01). Places are WORLD metres (north = -z, east = +x); headings 0 faces +z (south), pi/2 faces +x (east).
# s0 and s5 cut; s2/s3 on death's held end pose (face down, cheek on the ground, face to the coals); s3 at ground level;
# close and mid shots with ambient down ~1.5 stops; keys at ~2700 K from below; s10 static three-quarter, head snap, rise out;
# s11 from behind her (west) on take_from_log; night grade (s7, s8a, s9, s12), frost thinner.
NIGHT = {"do": "atmosphere", "preset": "night", "key": 0.4, "hemi": 0.45, "env": 0.45, "exposure": 0.92, "fog": 1.5, "fogColor": "#0a1018", "rim": 0.6}
K27 = "#ffa45c"   # ~2700 K


def air(**k):
    a = dict(NIGHT)
    for n, v in k.items():
        a[n] = round(NIGHT.get(n, 1) * v, 4) if n in ("key", "hemi", "env", "exposure", "fog", "rim") else v
    return a


CU = air(hemi=0.35, env=0.35)            # her off-key side to a cool dark (-1.5 stops of ambient)
FIRE = lambda lv, col="#ff7430": {"do": "light", "light": 0, "level": lv, "color": col, "rate": 0.45}


def cues(s):
    return s.setdefault("cues", [])


def drop(s, pred):
    s["cues"] = [c for c in cues(s) if not pred(c)]


def edit(shots, f):
    # s0 cut: its set-up moves onto s1's black; she lies face down by the coals (death's end, held).
    s0, s1 = shots["0"], shots["1"]
    keep0 = [c for c in s0["cues"] if c.get("do") != "anim"]
    drop(s1, lambda c: c.get("do") == "head")
    for c in s1["cues"]:
        if c.get("do") == "frost": c["amount"] = 0.22
        if c.get("do") == "glow" and c.get("name") == "tower": c.pop("under", None)
    s1["cues"][0:0] = keep0 + [
        {"do": "place", "where": [-9.5, 89.38], "heading": 0.0},
        {"do": "anim", "clip": "her/death", "from": 1.5, "speed": 0, "blend": 0},
        {"do": "head", "amount": 0, "over": 0.1},
    ]
    f["shots"] = [s for s in f["shots"] if s["id"] not in ("0", "5")]

    # s2: straight down, lower (about 3 m), her and the coals filling the frame.
    s2 = shots["2"]
    s2["cam"] = {"pos": [-9.95, 3.25, 90.05], "at": [-9.97, 0.0, 90.03], "lens": 28, "focus": 3.1, "fstop": 4.0,
                 "move": {"pos": [-9.95, 2.95, 90.05], "ease": "slow"}}
    for c in s2["cues"]:
        if c.get("do") == "anim": c.update({"clip": "her/death", "from": 1.5, "speed": 0, "blend": 0})

    # s3: at ground level, 7 cm off the frost, 0.55 m from her face, from her face's side and off the coals' line;
    # ember (2700 K) from the coals at ground level, a cool moon from above; the fire's own light down.
    s3 = shots["3"]
    s3["cam"] = {"pos": {"actor": "her", "bone": "head", "off": [-0.4, -0.05, 0.38]}, "at": {"actor": "her", "bone": "head", "off": [0, 0.0, 0]},
                 "lens": 75, "focus": {"actor": "her", "bone": "eyes"}, "fstop": 2.0, "roll": 0, "move": {"push": 0.04, "ease": "linear"}}
    drop(s3, lambda c: c.get("do") == "rig")
    s3["cues"][0:0] = [
        dict(CU), FIRE(0.12, "#ff9448"),
        {"do": "rig", "name": "moon", "energy": 0.35, "color": "#9fb8ff", "angle": 30, "from": {"actor": "her", "bone": "head", "off": [0.15, 1.1, 0.35]}, "aim": {"actor": "her", "bone": "head"}},
        {"do": "rig", "name": "ember", "energy": 0.3, "color": K27, "angle": 35, "from": {"actor": "her", "bone": "head", "off": [-0.75, -0.02, 0.1]}, "aim": {"actor": "her", "bone": "head"}},
    ]

    # s6: back on her mark; the clip from its kneel (the hip-sit never shows); jaw closed to a parting; ambient down.
    s6 = shots["6"]
    for c in s6["cues"]:
        if c.get("do") == "anim" and c.get("clip") == "her/sit_back_heels": c["from"] = 2.2; c["blend"] = 0
        if c.get("do") == "face" and "mouth_open" in c.get("keys", {}): c["keys"]["mouth_open"] = 0.02
    s6["cues"][0:0] = [dict(CU), FIRE(0.24), {"do": "place", "mark": "lie"}]

    # s7: the frost field down a stop; her head a dark shape with only the fire's edge on it.
    s7 = shots["7"]
    drop(s7, lambda c: c.get("do") == "rig")
    s7["cues"][0:0] = [air(key=0.5, hemi=0.5, env=0.5), FIRE(0.1),
                       {"do": "rig", "name": "rim", "energy": 0.7, "color": "#ff8a40", "angle": 18,
                        "from": {"actor": "her", "bone": "eyes", "off": [-0.7, -0.15, -0.15]}, "aim": {"actor": "her", "bone": "eyes", "off": [0, 0.05, 0]}}]

    # s8: the key from the coals, 2700 K, 0.7 stop down, from below her eye line; a cool fill (1/6), a warm bounce; panned off the braid.
    key8 = {"do": "rig", "name": "key", "energy": 1.0, "color": K27, "angle": 20, "from": {"actor": "her", "bone": "eyes", "off": [-0.6, -0.38, -0.3]},
            "aim": {"actor": "her", "bone": "eyes", "off": [0, -0.03, 0]}}
    fill = {"do": "rig", "name": "fill", "energy": 0.17, "color": "#9fb8ff", "angle": 25, "from": {"actor": "her", "bone": "eyes", "off": [0.6, 0.35, -0.6]},
            "aim": {"actor": "her", "bone": "eyes"}}
    bounce = {"do": "rig", "name": "bounce", "energy": 0.12, "color": "#ffb27a", "angle": 25, "from": {"actor": "her", "bone": "eyes", "off": [0.05, -0.7, -0.5]},
              "aim": {"actor": "her", "bone": "eyes", "off": [0, -0.05, 0]}}
    s8 = shots["8"]
    drop(s8, lambda c: c.get("do") == "rig")
    s8["cues"][0:0] = [dict(CU), FIRE(0.16, "#ff9d55"), dict(key8), dict(fill), dict(bounce)]
    s8["cam"]["at"] = {"actor": "her", "bone": "eyes", "off": [0.085, -0.05, 0]}
    for c in s8["cues"]:
        if c.get("do") == "face" and c.get("at") == 1.2: c["keys"]["mouth_open"] = 0.06

    # s8a: sky down a stop toward blue-grey; the ford's three lamps cold blue and dimmer; the tower's shaft gone; 1.2 m left.
    s8a = shots["8a"]
    s8a["cam"]["pos"] = [1.8, 1.4, 5.0]
    s8a["cam"]["at"] = [-0.6, 9.0, -70.0]
    s8a["cues"][0:0] = [air(env=0.5, exposure=0.85, fogColor="#141a24")] + \
        [{"do": "light", "light": i, "level": 0.4, "color": "#6e9bff"} for i in (4, 5, 6)] + \
        [{"do": "globe", "light": i, "level": 0.35} for i in (4, 5, 6)]

    # s8b: 1.12x s8's framing (75 mm at 0.97 m), the frame top at her hairline, lips closed, panned off the braid; s8's keys.
    s8b = shots["8b"]
    s8b["cam"] = {"pos": {"actor": "her", "bone": "eyes", "off": [0.06, -0.02, -0.97]}, "at": {"actor": "her", "bone": "eyes", "off": [0.1, -0.03, 0]},
                  "lens": 75, "focus": {"actor": "her", "bone": "eyes"}, "fstop": 2.0, "move": {"push": 0.02, "ease": "linear"}}
    drop(s8b, lambda c: c.get("do") == "rig")
    for c in s8b["cues"]:
        if c.get("do") == "face" and "mouth_open" in c.get("keys", {}): c["keys"]["mouth_open"] = 0.0
    s8b["cues"][0:0] = [dict(CU), dict(key8), dict(fill), dict(bounce),
                        {"do": "rig", "name": "eye", "energy": 0.15, "color": "#fff3e6", "angle": 5, "from": {"lens": [0, 0.25, 0]}, "aim": {"actor": "her", "bone": "eyes"}}] + \
        [{"do": "light", "light": i, "level": 1.0, "color": "#8ac8ff"} for i in (4, 5, 6)]

    # s9: the camp the island of light: the moon off the near frost (-1.5 stops), the fire's pool up a stop; thin low mist past the firelight.
    s9 = shots["9"]
    drop(s9, lambda c: c.get("do") in ("mist", "light"))
    thin = {"density": 0.14, "color": "#7f8ea4", "falloff": 3.0, "grain": 0.2, "sink": 0.1}
    s9["cues"][0:0] = [air(key=0.35, hemi=0.5, env=0.5), FIRE(0.84),
                       dict({"do": "mist", "name": "west", "where": [-21.5, 0, 90.0], "size": [17, 0.5, 30]}, **thin),
                       dict({"do": "mist", "name": "north", "where": [-8.0, 0, 76.0], "size": [30, 0.5, 20]}, **thin),
                       {"at": 1.3, "do": "rig", "name": "r1rim", "energy": 3.0, "color": "#9fb8ff", "angle": 30, "range": 7,
                        "from": {"mark": "r1", "off": [-1.6, 2.4, -0.6]}, "aim": {"mark": "r1", "off": [0, 1.1, 0]}}]

    # s10: static, three-quarter front from the fire side (37 deg off her nose line, her left-front), at her eye height, 55 mm.
    # Looking down into the coals at frame 0; the head snaps to her right (screen left) in the first 0.2 s, lips closed;
    # she rises straight up out of frame (the clip's 55-degree turn to her left taken back by turning her root right).
    s10 = shots["10"]
    s10["dur"] = 0.75
    s10["still"] = 0.3
    s10["cam"] = {"pos": [-11.6, 0.98, 91.245], "at": [-9.744, 1.06, 90.863], "lens": 55, "focus": {"actor": "her", "bone": "eyes", "track": True}, "fstop": 2.8}
    s10["cues"] = [
        dict(CU), FIRE(0.16, "#ff9d55"),
        {"do": "rig", "name": "key", "energy": 0.9, "color": K27, "angle": 24, "from": {"actor": "her", "bone": "eyes", "off": [-0.75, -0.4, -0.25]},
         "aim": {"actor": "her", "bone": "eyes", "off": [0, -0.03, 0]}},
        dict(fill, energy=0.15),
        {"do": "head", "where": [-10.3, 0.15, 90.65], "amount": 0.9, "over": 0.02},
        {"do": "gaze", "look": [0, 0.8], "wander": 0.0},
        {"do": "world", "rate": 0},
        {"at": 0.05, "do": "head", "where": [-11.74, 1.15, 87.4], "amount": 1.0, "over": 0.14},
        {"at": 0.05, "do": "gaze", "look": [0, 0.05], "wander": 0.02},
        {"at": 0.05, "do": "face", "keys": {"eyes_wide": 0.35, "brows_sad": 0, "brows_angry": 0.25, "mouth_open": 0}, "over": 0.15},
        {"at": 0.2, "do": "anim", "clip": "her/kneel_to_stand_snap", "from": 0.3, "speed": 0.8, "blend": 0.1},
        {"at": 0.24, "do": "look", "where": [-10.35, 0, 87.98], "over": 0.38},
    ]

    # s11: from behind her, west, 5.5 m, hip height, 35 mm, boots in frame: she bends to the log (her body hides the grip),
    # comes up with it and round to her left onto it, screen left, on stepping feet (take_from_log); r2 and r4 break the frost left and right.
    s11 = shots["11"]
    s11["dur"] = 1.45
    s11["still"] = 0.6
    s11["cam"] = {"pos": [-14.45, 0.95, 89.3], "at": [-8.95, 0.85, 89.3], "lens": 35, "focus": {"mark": "reach", "off": [0, 1.0, 0]}, "fstop": 4.0}
    for c in s11["cues"]:
        if c.get("do") == "rig" and c.get("name") == "edge": c["energy"] = 1.8
        if c.get("do") == "prop": c["at"] = 0.3
        if c.get("do") == "hold": c["at"] = 0.3
        if c.get("do") == "anim" and c.get("clip") == "PickUp_Table": c.update({"clip": "her/take_from_log", "from": 0.3, "speed": 1.0, "blend": 0})
        if c.get("do") == "face" and c.get("at") == 0.7 and "mouth_open" in c.get("keys", {}): c["keys"]["mouth_open"] = 0.0
    s11["cues"][0:0] = [dict(CU), FIRE(0.3, "#ff8a45")]

    # s12: opens at s11's exposure and comes up to play's over the crane; the mist eases to a quarter, then out before play.
    s12 = shots["12"]
    drop(s12, lambda c: c.get("do") == "mist")
    s12["cues"][0:0] = [air(hemi=0.35, env=0.35, exposure=0.45), FIRE(0.42)]
    for c in s12["cues"]:
        if c.get("do") == "atmosphere" and c.get("from") == "now": c["over"] = 3.2
    s12["cues"] += [{"do": "mist", "name": n, "density": 0.035, "over": 2.4} for n in ("west", "north")] + \
                   [{"at": 2.4, "do": "mist", "name": n, "density": 0, "over": 1.0} for n in ("west", "north")]
