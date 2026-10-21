# cine6 r3e: s5 from the north-west behind him (she stays, small beyond him; the stones a leading line, not a ruler);
# s9 pulled back to a real over-the-shoulder (35 mm, 2.7 m from Grimtunnel), moon behind him.
def edit(shots, f):
    s5, s6, s9 = shots["5"], shots["6"], shots["9"]
    s5["cam"] = {"pos": {"mark": "w", "off": [-5.0, 1.0, -7.0]}, "at": {"mark": "w", "off": [0.0, 1.6, 1.0]}, "lens": 35}
    s5["cues"] = [c for c in s5["cues"] if c.get("do") != "hide"]
    s6["cues"] = [c for c in s6["cues"] if c.get("do") != "hide"]
    for c in s5["cues"]:
        if c.get("do") == "atmosphere": c["azimuth"] = 60
    s9["cam"].update({"pos": {"mark": "her", "off": [-0.2, 1.75, 1.9]}, "at": {"mark": "her", "off": [1.0, 1.0, -0.5]}, "lens": 35})
    for c in s9["cues"]:
        if c.get("actor") == "grim" and c.get("do") == "anim": c["where"] = {"mark": "her", "off": [-0.2, 0, 1.9]}
        if c.get("do") == "move" and c.get("actor") == "heart": c["to"] = {"mark": "her", "off": [0.92, 0.8, -0.32]}
        if c.get("do") == "atmosphere": c["azimuth"] = 300
