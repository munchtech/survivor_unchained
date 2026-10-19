# Lead: her head out of the top in s9 (pull back, aim up); the heart still blows his torso out (glow 0.4 -> 0.15).
def edit(shots, f):
    shots["9"]["cam"]["pos"] = {"mark": "her", "off": [3.6, 0.95, 2.4]}
    shots["9"]["cam"]["at"] = {"mark": "her", "off": [0.5, 1.15, -0.3]}
    for c in shots["9"]["cues"]:
        if c.get("do") == "lamp" and c.get("actor") == "heart": c["glow"] = 0.15
