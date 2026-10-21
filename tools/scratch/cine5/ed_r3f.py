# cine6 r3f: s9 back to a side two-shot from the north, pulled back; both backlit by the moon from the south; she snaps to her
# guard (weapons back across the cut) instead of the cup_hands hold that read as clutching her chest. s5: his head in frame.
def edit(shots, f):
    s5, s9 = shots["5"], shots["9"]
    s5["cam"]["at"]["off"] = [0.0, 2.4, 1.0]
    s9["cam"] = {"pos": {"mark": "her", "off": [-0.4, 1.4, -4.0]}, "at": {"mark": "her", "off": [0.5, 1.15, -0.3]}, "lens": 32,
                 "move": {"push": 0.3, "ease": "slow"}}
    s9["cues"] = [c for c in s9["cues"] if not (c.get("do") == "anim" and c.get("actor") == "her")]
    for c in s9["cues"]:
        if c.get("actor") == "grim" and c.get("do") == "anim": c["where"] = {"mark": "her", "off": [-0.5, 0, -2.0]}
        if c.get("do") == "move" and c.get("actor") == "heart": c["to"] = {"mark": "her", "off": [0.82, 0.8, -0.68]}
        if c.get("do") == "atmosphere": c["azimuth"] = 90
    s9["note"] = ("Side-on from the north, both backlit by the moon: the mud bursts and Grimtunnel, up to the waist, has the heart hugged to his "
                  "chest, its blue the brightest thing in the frame, lighting his claws from below. She snaps back into her guard. G1; sniffs; G2. "
                  "G3 begins and runs on over the crane.")
    s9["cues"] += [
        {"do": "hold", "actor": "her", "slot": "all", "piece": "@own"},
        {"at": 0.05, "do": "anim", "actor": "her", "clip": "@idle", "from": 0, "speed": 1, "blend": 0.15},
        {"at": 0.05, "do": "anim", "actor": "her", "clip": "Idle_Shield_Loop", "from": 0, "speed": 1, "blend": 0.15, "when": {"calling": ["warden"]}},
        {"at": 0.1, "do": "head", "actor": "her", "where": {"mark": "her", "off": [0.82, 0.9, -0.68]}, "amount": 0.9, "over": 0.25},
    ]
