"""C01 pass 2: she lies 0.45 m nearer the fire (her hand reaches the coals' edge), and the cameras
of shots 2 to 8b are reframed on the lying, rising and kneeling body."""


def cam(s, **kw):
    s["cam"] = kw


def edit(shots, f):
    m = f["marks"]
    lx, lz, lh = m["lie"]
    m["lie"] = [round(lx - 0.43, 2), round(lz - 0.12, 2), lh]
    EYES = {"actor": "her", "bone": "eyes"}
    # 2: straight down over her and the ring, sinking.
    cam(shots["2"], pos=[-9.95, 4.0, 90.62], at=[-9.97, 0.0, 90.6], lens=28, focus=3.9, fstop=4.0,
        move={"pos": [-9.95, 3.6, 90.62], "ease": "slow"})
    # 3: her face on its side, from the fire's side, a little above.
    s = shots["3"]
    old = s["cam"]
    cam(s, pos={"actor": "her", "bone": "eyes", "off": [-0.6, 0.18, -0.45]}, at={"actor": "her", "bone": "eyes", "off": [0, -0.02, 0]},
        lens=85, focus=EYES, fstop=2.0, move=old.get("move", {"push": 0.1, "start": 0, "end": "end", "ease": "linear"}))
    # 5: low on the fire's far side, through the embers, as she comes up onto her elbow.
    cam(shots["5"], pos=[-11.5, 0.42, 90.9], at={"actor": "her", "bone": "chest", "off": [0, 0.1, 0]}, lens=40,
        focus={"actor": "her", "bone": "head"}, fstop=2.8)
    # 6: front three-quarter from her left, the head tracked as she kneels up.
    cam(shots["6"], pos=[-10.69, 0.85, 91.82], at={"actor": "her", "bone": "head", "track": True}, lens=50,
        focus={"actor": "her", "bone": "eyes", "track": True}, fstop=2.8)
    # 6a: the hand going out over the coals, from the south, low.
    cam(shots["6a"], pos=[-9.95, 0.75, 91.35], at=[-10.15, 0.25, 90.6], lens=50, focus=0.8, fstop=2.0)
    # 7: behind her, over her left shoulder, down the trail; then up it into the dark.
    s = shots["7"]
    mv = s["cam"].get("move", {})
    cam(s, pos=[-9.35, 1.12, 91.48], at=[-8.9, 0.0, 86.5], lens=28, focus=3.0, fstop=4.0, move=mv)
    s["cues"] = [c for c in s["cues"] if c.get("do") != "look"]
    s["cues"].insert(0, {"at": 0.0, "do": "look", "where": [-8.9, 0.6, 86.5], "over": 0.9})
    # 8, 8b: frontal from the trail's side, a little under her eyes.
    for sid, off in (("8", [0.08, -0.1, -0.95]), ("8b", [0.06, -0.08, -0.82])):
        s = shots[sid]
        cam(s, pos={"actor": "her", "bone": "eyes", "off": off}, at={"actor": "her", "bone": "eyes", "off": [0, -0.04, 0]},
            lens=85, focus=EYES, fstop=2.0)
