def edit(shots, f):
    s8 = shots["8"]
    s8["cam"]["pos"]["off"] = [0.08, -0.03, -1.0]      # frontal, 100 mm (judge j2)
    s8["cam"]["at"]["off"] = [0, -0.03, 0]
    s8["cam"]["lens"] = 100
    for c in s8["cues"]:
        if c.get("do") == "glow" and c.get("name") == "held":
            # The lamp's light at her eye height, 35 deg off the lens toward her right: the flame in her
            # eyes, her right half blue; its reach ends at her jaw (no hot shoulder guards).
            c["where"] = {"actor": "her", "bone": "eyes", "off": [-0.20, 0.06, -0.28]}
            c["light"] = 0.8
            c["range"] = 0.55
