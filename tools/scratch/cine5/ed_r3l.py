# cine6 r3l: s9 her face went cyan (heart spill 1.4 over a 0.5 warm key), head cut, the hat-lamp cage in frame: raise, re-balance.
def edit(shots, f):
    s9 = shots["9"]
    s9["cam"]["pos"]["off"] = [1.8, 2.05, -1.3]; s9["cam"]["at"]["off"] = [0.0, 1.68, 0.0]
    for c in s9["cues"]:
        if c.get("do") == "rig" and c.get("name") == "skin": c["energy"] = 0.9
        if c.get("do") == "rig" and c.get("name") == "spill": c["energy"] = 0.55
