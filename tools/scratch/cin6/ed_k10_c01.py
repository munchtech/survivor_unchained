# Staging solver s4 (k10), C01 pass 1: the scene's own darker night, s3 face on its side, s6 head bowed to her hands,
# s10 cut on the first lift, keys from the fire on the close-ups. Places are world metres; headings 0 = +z.
NIGHT = {"do": "atmosphere", "preset": "night", "key": 0.4, "hemi": 0.45, "env": 0.45, "exposure": 0.92, "fog": 1.5, "fogColor": "#0a1018", "rim": 0.6}
FIRE = "#ff7a3a"


def cues(s):
    return s.setdefault("cues", [])


def drop(s, pred):
    s["cues"] = [c for c in cues(s) if not pred(c)]


def edit(shots, f):
    # s1 (black): the scene's night, and her head tipped toward the coals (no stretched throat).
    c1 = cues(shots["1"])
    c1.insert(0, dict(NIGHT))
    c1.append({"do": "head", "where": [-10.35, 0.08, 90.45], "amount": 0.65, "over": 0.3})

    # s3: at ground level from where her face points; variants for the framing test (removed after).
    s3 = shots["3"]
    s3["cam"] = {"pos": {"actor": "her", "bone": "head", "off": [-0.8, -0.02, 0.05]}, "at": {"actor": "her", "bone": "head", "off": [0, -0.01, 0]},
                 "lens": 85, "focus": {"actor": "her", "bone": "head"}, "fstop": 2.0, "move": {"push": 0.06, "ease": "linear"}}
    drop(s3, lambda c: c.get("do") == "rig")
    cues(s3)[0:0] = [
        {"do": "rig", "name": "moon", "energy": 1.2, "color": "#9fb8ff", "angle": 30, "from": {"actor": "her", "bone": "head", "off": [-0.6, 1.15, 0.75]}, "aim": {"actor": "her", "bone": "head"}},
        {"do": "rig", "name": "ember", "energy": 1.5, "color": FIRE, "angle": 35, "from": {"actor": "her", "bone": "head", "off": [-0.6, -0.15, 0.05]}, "aim": {"actor": "her", "bone": "head"}},
    ]
    i = [s["id"] for s in f["shots"]].index("3")
    for n, off in enumerate([[-0.7, -0.02, -0.35], [-0.5, -0.02, -0.6], [0.0, -0.02, -0.8]]):
        v = {"id": f"3v{n+1}", "type": "CU", "dur": 0.8, "still": 0.5, "note": "framing test",
             "cam": {"pos": {"actor": "her", "bone": "head", "off": off}, "at": {"actor": "her", "bone": "head", "off": [0, -0.01, 0]}, "lens": 85,
                     "focus": {"actor": "her", "bone": "head"}, "fstop": 2.0},
             "cues": [dict(c) for c in cues(s3) if c.get("do") == "rig"]}
        f["shots"].insert(i + 1 + n, v)

    # s5: the clip has her head again as she pushes up.
    cues(shots["5"]).insert(0, {"do": "head", "amount": 0, "over": 0.8})

    # s6: the head bowed from the neck to her hands (not the clip's collapse), the hands in frame, a warm edge on her nape.
    s6 = shots["6"]
    s6["cam"]["pos"] = [-11.3, 0.9, 91.75]
    s6["cam"]["at"] = {"actor": "her", "bone": "chest", "off": [0, 0.06, 0], "track": True}
    s6["cam"]["lens"] = 32
    cues(s6)[1:1] = [
        {"at": 1.6, "do": "head", "where": [-11.6, 0.4, 94.8], "amount": 0.6, "over": 0.6},
        {"at": 3.4, "do": "head", "where": [-10.15, 0.3, 90.8], "amount": 0.85, "over": 0.9},
        {"do": "rig", "name": "nape", "energy": 0.9, "color": FIRE, "angle": 24, "from": {"actor": "her", "bone": "head", "off": [-0.55, 0.75, 0.35]},
         "aim": {"actor": "her", "bone": "head", "off": [0.06, -0.12, 0]}},
    ]

    # s8, s8b: the key from the fire (west, low: her left, frame right), the lens-side fill gone; s8b keeps its eye light.
    fire_key = {"do": "rig", "name": "key", "energy": 1.6, "color": FIRE, "angle": 30,
                "from": {"actor": "her", "bone": "eyes", "off": [-0.75, -0.35, -0.3]}, "aim": {"actor": "her", "bone": "eyes", "off": [0, -0.04, 0]}}
    drop(shots["8"], lambda c: c.get("do") == "rig")
    cues(shots["8"]).insert(0, dict(fire_key))
    cues(shots["8b"]).insert(0, dict(fire_key))

    # s9: mist lying past the firelight, west and north, where the frost breaks.
    cues(shots["9"])[0:0] = [
        {"do": "mist", "name": "west", "where": [-19.0, 0, 90.0], "size": [22, 1.2, 30], "density": 0.35, "color": "#7f8ea4", "falloff": 2.5},
        {"do": "mist", "name": "north", "where": [-8.0, 0, 76.0], "size": [30, 1.2, 20], "density": 0.35, "color": "#7f8ea4", "falloff": 2.5},
    ]

    # s10: the head turns hard to the sound and she starts to rise; cut on the lift (s11 has her up at the log's end).
    s10 = shots["10"]
    s10["dur"] = 1.0
    s10["still"] = 0.8
    drop(s10, lambda c: c.get("do") in ("move",) or (c.get("do") == "anim") or (c.get("do") == "head" and c.get("amount") == 0))
    cues(s10)[0:0] = [
        {"at": 0.3, "do": "anim", "clip": "her/kneel_to_stand_snap", "from": 0, "speed": 1, "blend": 0.25},
        {"do": "rig", "name": "key", "energy": 1.4, "color": FIRE, "angle": 30, "from": {"actor": "her", "bone": "eyes", "off": [-0.8, -0.3, -0.15]},
         "aim": {"actor": "her", "bone": "eyes", "off": [0, -0.03, 0]}},
    ]

    # s11: the clip has her head again (the s10 look let go on the cut).
    cues(shots["11"]).insert(0, {"do": "head", "amount": 0, "over": 0.25})

    # s12: back into play's night over the crane, the mist thinned away.
    cues(shots["12"])[0:0] = [
        {"do": "atmosphere", "preset": "night", "from": "now", "over": 3.0},
        {"do": "mist", "name": "west", "density": 0, "over": 3.0},
        {"do": "mist", "name": "north", "density": 0, "over": 3.0},
    ]
