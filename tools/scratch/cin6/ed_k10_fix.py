# k10 fix pass: the camp's ember pool up for s9-s11 (the island of firelight; s11's action read), a warm edge on her
# from the fire side in s11; C02: the drowned's backlight stronger (s10 read black), s8's lamp eased off her face.
import sys
def edit(shots, f):
    if f["id"] == "c01":
        shots["9"]["cues"].insert(0, {"do": "light", "light": 0, "level": 0.42, "color": "#ff7430", "rate": 0.45})
        shots["11"]["cues"].insert(0, {"do": "rig", "name": "edge", "energy": 2.5, "color": "#ff7a3a", "angle": 30,
            "from": {"mark": "fire", "off": [0, 0.8, 0]}, "aim": {"actor": "her", "bone": "chest"}})
    else:
        for c in shots["1"]["cues"]:
            if c.get("do") == "glow" and c.get("name") == "back": c["light"] = 9.0; c["range"] = 16
        for c in shots["8"]["cues"]:
            if c.get("do") == "glow" and c.get("name") == "held": c["light"] = 0.3
