# cine6 r3b: the one framing pass after the r3a shoot.
def edit(shots, f):
    s3, s5, s6, s9, s10, s12 = (shots[k] for k in ["3", "5", "6", "9", "10", "12"])
    # s3/s5: she was chopped by the right frame edge: pan off her (the beat is his)
    s3["cam"]["at"]["off"] = [0.2, 2.3, 0.2]; s3["cam"]["lens"] = 36
    s5["cam"]["at"]["off"] = [0.3, 1.3, 0.2]; s5["cam"]["lens"] = 32
    # s6: her shoulder/shield poked into the top-left corner: swing the camera north, longer lens for the heart
    s6["cam"]["pos"]["off"] = [4.4, 0.7, 1.8]; s6["cam"]["lens"] = 50
    # s9: Grim turned 3/4 to camera so the heart in his claws shows; she keeps her hands up (no hunched flinch);
    #     tilt up so her face isn't at the top edge and her shins (through the water) drop out under the letterbox
    s9["cam"]["at"]["off"] = [0.5, 1.3, -0.3]
    for c in s9["cues"]:
        if c.get("actor") == "grim" and c.get("do") == "anim":
            c["where"] = {"mark": "her", "off": [-0.5, 0, -2.0]}
        if c.get("do") == "move" and c.get("actor") == "heart":
            c["to"] = {"mark": "her", "off": [0.82, 0.8, -0.68]}
    s9["cues"] = [c for c in s9["cues"] if not (c.get("do") == "anim" and c.get("clip") == "her/flinch")]
    s9["cues"] += [
        {"at": 0.05, "do": "anim", "actor": "her", "clip": "her/cup_hands", "from": 2.5, "speed": 0.08, "blend": 0.1},
        {"at": 0.1, "do": "head", "actor": "her", "where": {"actor": "heart"}, "amount": 0.8, "over": 0.25},
    ]
    # s10: her eyes were above the frame: gentler low angle, pulled back, eyes on the upper third
    s10["cam"]["pos"]["off"] = [1.0, 1.35, -1.33]; s10["cam"]["at"]["off"] = [0.0, 1.67, -0.02]; s10["cam"]["lens"] = 40
    # s12: opening was her backside filling frame left, head cut: higher and further back, both of them whole
    s12["cam"]["pos"]["off"] = [3.8, 2.4, 3.6]; s12["cam"]["at"]["off"] = [0.8, 0.9, -0.5]
