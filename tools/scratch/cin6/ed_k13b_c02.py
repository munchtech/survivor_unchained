# k13b (C02): round-2 judge's one-action fixes (k12B_verdict.md) and the s9 cut.
GLOBE = "#8ac8ff"
POSTS = {4: [0.028, 3.279, -32.901], 5: [-9.586, 3.24, -49.039], 6: [9.624, 3.645, -49.033]}
GL = 0.07  # the globes' own emission, about 28% of the k12 0.25


def edit(shots, f):
    # 1. Globes and the lantern: dim, ember-blue, a soft halo (flame-lit glass), s1 on (they persist).
    s1 = shots["1"]["cues"]
    out = []
    for c in s1:
        if c.get("do") == "globe":
            li = c["light"]
            out.append({"do": "globe", "light": li, "level": GL, "color": GLOBE})
            out.append({"do": "glow", "name": f"post{li}", "where": POSTS[li], "color": GLOBE, "size": 0.001, "energy": 1,
                        "spread": 900, "halo": 0.32, "clear": True})
        else:
            out.append(c)
    out.insert(out.index(next(c for c in out if c.get("do") == "place")), {"do": "lamp", "actor": "warden", "flame": 0.28, "halo": 0.55})
    shots["1"]["cues"] = out

    # 3. s4: key about 60 deg off her nose; ember wider, about a quarter of the key.
    for c in shots["4"]["cues"]:
        if c.get("name") == "key": c["from"]["off"] = [0.8, 0.1, -0.45]
        if c.get("name") == "ember": c.update({"angle": 40, "range": 1.2, "energy": 0.25})

    # 13. s5: cut in at 40% (2.0 of 5.0 s): the body already up the water, the clip 2 s in.
    s5 = shots["5"]
    s5["dur"] = 3.0
    s5["still"] = 2.2
    cs = []
    for c in s5["cues"]:
        if c.get("do") == "place": c = dict(c, where={"abs": [5.0, -1.35, -44.5]})
        if c.get("do") == "move": continue
        if c.get("do") == "lamp": c = {"do": "lamp", "actor": "warden", "glow": 1.0}
        if c.get("do") == "anim": c = dict(c, **{"from": 2.0})
        if c.get("do") == "music": c = dict(c, intensity=0.35, over=2.0)
        cs.append(c)
    s5["cues"] = cs

    # 2. s8: the lamp from screen-left about 70 deg off the lens; the ember wider (40 deg, 1.2 m, 0.35).
    for c in shots["8"]["cues"]:
        if c.get("name") == "held": c["where"]["off"] = [0.28, 0.1, -0.33]
        if c.get("name") == "ember": c.update({"angle": 40, "range": 1.2, "energy": 0.35})

    # 10. s7: profile from the west, 35 mm, his head to her knees, the near post out of frame left.
    shots["7"]["cam"] = {"pos": [-2.21, 1.3, -31.16], "at": {"abs": [2.7, 1.25, -31.85]}, "lens": 35}

    # Cut s9: its cues onto s10 (him shown again, his straightening, the held light gone).
    s9 = shots.pop("9")
    f["shots"] = [s for s in f["shots"] if s["id"] != "9"]
    s10 = shots["10"]
    s10["cues"] = [{"do": "hide", "actor": "warden", "hidden": False},
                   {"do": "anim", "actor": "warden", "clip": "Sword_Idle", "blend": 0.8},
                   {"do": "glow", "name": "held", "remove": True}] + s10["cues"]

    # 7. s10: centred behind his legs toward the rows, 1.8 m from his feet, 0.5 m above the water, 35 mm;
    # a thin cool rim on the legs' inner edges from the rows' side.
    s10["cam"] = {"pos": {"abs": [1.71, -0.5, -31.41]}, "at": {"abs": [10.4, -0.7, -43.4]}, "lens": 35,
                  "focus": {"abs": [10.4, -0.7, -43.4]}, "fstop": 2.8}
    s10["cues"].insert(3, {"do": "rig", "name": "legrim", "energy": 1.6, "color": "#9fb8ff", "angle": 30,
                           "from": {"abs": [3.6, -0.6, -34.0]}, "aim": {"actor": "warden", "bone": "foot_l", "off": [-0.4, 0.5, 0]}})

    # s11: the globes gutter as he drinks them (W3), a dip in their glow, then back.
    s11 = shots["11"]["cues"]
    for li in (4, 5, 6):
        s11.append({"at": 0.4, "do": "globe", "light": li, "level": 0.02, "over": 0.5})
        s11.append({"at": 1.4, "do": "globe", "light": li, "level": GL, "over": 1.2})

    # s12: the globes stay glass through the crane, back to play's only at the very end; the lantern as built.
    for c in shots["12"]["cues"]:
        if c.get("do") == "globe": c.update({"at": 1.4, "over": 0.6})
    shots["12"]["cues"].append({"at": "end", "do": "lamp", "actor": "warden", "flame": 1, "halo": 1})
