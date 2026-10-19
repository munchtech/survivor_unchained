# k13b round 3: C02 s7 aimed higher and 3 deg right (his hood in, the west pillar off the left edge); C04 A A4's hold up to her knees.
import sys
def edit(shots, f):
    if f["id"] == "c02": shots["7"]["cam"]["at"] = {"abs": [2.7, 1.5, -31.6]}
    if f["id"] == "c04a": shots["A4"]["cam"]["move"]["at"]["off"] = [0, -0.2, 0]
