# cine6 r3h: s9 her head clear of the frame top (less push, aim higher); the heart between his claws, not at his mouth.
def edit(shots, f):
    s9 = shots["9"]
    s9["cam"]["at"]["off"] = [0.5, 1.3, -0.3]; s9["cam"]["move"]["push"] = 0.15
    for c in s9["cues"]:
        if c.get("do") == "move" and c.get("actor") == "heart": c["to"] = {"mark": "her", "off": [0.8, 0.72, -0.72]}
