# cine6 r3i: the confirmation judge's light nudges. s8: the heart is her face key (blue on palm, chin), her warm key/fill halved,
# no rim; slower cup_hands (stays in the s8_2 hand pose). s9: front fill near zero, a cold rim from behind, the heart lights his
# claws, her key halved. s2: the lamp's core amber (the one warm light, the one that goes out).
def edit(shots, f):
    s2, s8, s9 = shots["2"], shots["8"], shots["9"]
    for c in s2["cues"]:
        if c.get("do") == "lamp" and c.get("actor") == "warden": c["flameColor"] = "#ffb45a"
    for c in s8["cues"]:
        if c.get("do") == "rig" and c.get("name") == "skin": c["energy"] = 0.45
        if c.get("do") == "atmosphere": c.update({"key": 0.7, "hemi": 0.75, "rim": 0.05})
        if c.get("do") == "rig" and c.get("name") == "spill": c["energy"] = 7.0
        if c.get("do") == "anim" and c.get("clip") == "her/cup_hands": c["speed"] = 0.45
        if c.get("do") == "lamp" and c.get("actor") == "heart": c["glow"] = 2.2
    s8["cues"].append({"do": "rig", "name": "chin", "from": {"actor": "heart"}, "aim": {"actor": "her", "bone": "head"},
                       "color": "#6fa8ff", "energy": 2.5, "angle": 40, "range": 2.5})
    for c in s9["cues"]:
        if c.get("do") == "rig" and c.get("name") == "skin": c["energy"] = 1.1
        if c.get("do") == "atmosphere": c.update({"key": 1.0, "hemi": 0.35, "env": 0.35, "rim": 25})
        if c.get("do") == "lamp" and c.get("actor") == "heart": c["glow"] = 3.0
