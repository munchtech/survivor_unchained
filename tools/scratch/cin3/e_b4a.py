LAMP = {"mark": "lamp", "y": 7.18}


def edit(shots, f):
    m = f["marks"]
    m.pop("window", None)
    m["lamp"] = [30.95, -6.8]
    for c in shots["B1"]["cues"]:
        if c.get("do") == "glow":
            c.clear()
            c.update({"do": "glow", "name": "towerlamp", "where": LAMP, "lantern": 1.8, "turn": 30,
                      "color": "#ffd9a0", "size": 0.035, "energy": 2.4, "spread": 7, "halo": 0.35})
    for c in shots["B4"]["cues"]:
        if c.get("do") == "look":
            c["where"] = LAMP
    s = shots["B4a"]
    s["dur"] = 2.4
    s["note"] = ("From the square by her, compressed: the tower's upper window, the keeper's lamp-iron standing on the "
                 "sill, its flame pale in the shade, goes out. A thread of smoke climbs the glass. (Rook's own eyeline is "
                 "blocked by the roofs; this is the nearest clear line.)")
    s["cam"] = {"pos": [4.0, 1.8, 8.0], "at": {"mark": "lamp", "y": 7.5}, "lens": 200}
    s["cues"] = [{"at": 0.7, "do": "glow", "name": "towerlamp", "out": True, "smoke": 1.7}]
