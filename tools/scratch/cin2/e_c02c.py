def edit(S, f):
    f["marks"]["warden_end"] = [2.9, -32.9, 0.0]
    f["marks"]["bed"] = [2.6, -44.5, -1.5708]
    # s1: he lies on his back under the river, the left fist and the lamp held up out of it.
    cues = []
    for c in S["1"]["cues"]:
        if c.get("do") == "glow":
            continue
        if c.get("do") == "place" and c.get("actor") == "warden":
            c = {"do": "place", "actor": "warden", "where": {"abs": [2.6, -1.75, -44.5]}, "heading": -1.5708, "tilt": -90}
        if c.get("do") == "anim" and c.get("actor") == "warden":
            c = {"do": "anim", "actor": "warden", "clip": "Spell_Simple_Idle_Loop", "from": 0.5, "speed": 0, "blend": 0}
        cues.append(c)
    S["1"]["cues"] = cues
    S["1"]["cam"] = {"pos": [3.1, 1.6, -25.6], "at": {"abs": [5.2, -0.5, -44.0]}, "lens": 28}
    S["2"]["cam"] = {"pos": {"abs": [5.2, -0.75, -36.6]}, "at": {"abs": [10.6, -0.5, -44.0]}, "lens": 35}
    S["3"]["cam"] = {"pos": {"abs": [5.1, -0.6, -42.3]}, "at": {"abs": [6.37, -0.25, -44.0]}, "lens": 85, "move": {"push": 0.25, "ease": "linear"}}
    # s5: the cut from her face hides the change to the getting-up clip, lying flat.
    S["5"]["cues"] = [c for c in S["5"]["cues"] if c.get("do") not in ("glow",)]
    for c in S["5"]["cues"]:
        if c.get("do") == "move" and c.get("actor") == "warden":
            c.update({"to": {"abs": [5.0, -1.35, -44.5]}, "dur": 0.01})
    S["5"]["cues"].insert(0, {"do": "place", "actor": "warden", "where": {"abs": [5.0, -2.2, -44.5]}, "heading": 1.5708, "tilt": 0})
    S["5"]["cues"] = [c for c in S["5"]["cues"] if not (c.get("do") == "move" and c.get("actor") == "warden")]
    S["5"]["cues"].insert(1, {"do": "move", "actor": "warden", "to": {"abs": [5.0, -1.35, -44.5]}, "dur": 1.2, "heading": 1.5708})
    for c in S["7"]["cues"]:
        if c.get("do") == "anim" and c.get("actor") == "warden":
            c.update({"clip": "Idle_Torch", "from": 0.4, "speed": 0.4})
    S["7"]["cam"] = {"pos": [-2.0, 1.3, -26.8], "at": {"abs": [2.7, 1.1, -32.0]}, "lens": 28}
    S["9"]["cam"] = {"pos": [2.1, 0.75, -30.5], "at": {"actor": "warden", "bone": "head"}, "lens": 50}
    S["10"]["cam"] = {"pos": {"abs": [1.4, -0.5, -31.6]}, "at": {"abs": [10.4, -0.4, -43.4]}, "lens": 65}
