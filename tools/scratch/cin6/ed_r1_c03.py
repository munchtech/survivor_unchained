def edit(shots, f):
    c9 = shots["9"]["cues"]
    for c in c9:
        if c.get("clip") == "@idle": c["at"] = 0.12; c["blend"] = 0.35
    # The Warden's guard, shield up (a low guard rather than a hanging sword); others keep @idle.
    c9.append({"at": 0.12, "do": "anim", "actor": "her", "clip": "Idle_Shield_Loop", "from": 0, "speed": 1, "blend": 0.35, "when": {"calling": ["warden"]}})
    s10 = shots["10"]["cam"]
    s10["pos"]["off"] = [0.7, 1.55, 0.2]      # at her eye height, back 0.5 m: the heart in his arms and the lamp in frame
    s10["at"]["off"] = [0.35, 1.0, -1.25]
    shots["11"]["cam"]["at"]["off"] = [0.35, 1.0, -1.25]   # his head and shoulder as he speaks
