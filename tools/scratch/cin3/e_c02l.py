"""C02: his own lamp, hanging from his fist, replaces the stand-in glow in the river; he lies higher so the
lamp hangs clear of the water; shot 3's insert and shot 8's light are on his lamp."""


def edit(shots, f):
    s1 = shots["1"]
    for c in s1["cues"]:
        if c.get("do") == "place" and c.get("actor") == "warden":
            w = c["where"]["abs"]
            c["where"]["abs"] = [w[0], -1.2, w[2]]
    s1["cues"] = [c for c in s1["cues"] if not (c.get("do") == "glow" and c.get("name") == "lamp")]
    shots["5"]["cues"] = [c for c in shots["5"]["cues"] if not (c.get("do") == "glow" and c.get("name") == "lamp")]
    shots["3"]["cam"]["at"] = {"actor": "warden", "bone": "hand_l", "off": [0, -0.35, 0]}
    for c in shots["8"]["cues"]:
        if c.get("do") == "glow" and c.get("name") == "held":
            # Only its light now: his own lamp's flame is in the frame.
            c.update({"where": {"abs": [2.83, 1.0, -31.05]}, "size": 0.001, "spread": 0.001, "halo": 0})
