# Round 3 (solver): C01 s11 on her own take_from_log (PickUp_Table maps to it for her), the swap on the cut;
# s12 crane starts 3.9 m off her chest.
import math
ARMED = {"calling": ["warden", "reaver", "stalker"]}
def edit(shots, f):
    s11 = shots["11"]
    s11["dur"] = 1.8
    s11["still"] = 0.9
    cues = []
    for c in s11["cues"]:
        if c.get("clip") == "PickUp_Table": c.update({"from": 0.5, "speed": 1.0, "blend": 0})
        if c.get("do") in ("prop", "hold"): continue                        # re-made below, on the cut
        if c.get("clip") == "@idle": c.update({"at": 1.0, "blend": 0.3, "when": {"calling": ["arcanist"]}})
        cues.append(c)
    # On the cut her hand has closed on the grip: the log's weapon (and shield) are hers from the first frame.
    cues[1:1] = [
        {"at": 0.0, "do": "prop", "name": "weapon", "remove": True},
        {"at": 0.0, "do": "prop", "name": "shield", "remove": True},
        {"at": 0.0, "do": "hold", "slot": "all", "piece": "@own", "when": ARMED},
        # Round onto R1 as the clip turns her (its 110 degrees to her left, and 60 more of her own).
        {"at": 0.45, "do": "look", "where": {"mark": "reach", "off": [1.53, 0, -2.58]}, "over": 1.15, "when": ARMED},
    ]
    s11["cues"] = cues
    s12 = shots["12"]
    s12["cam"]["pos"] = [-8.7, 1.45, 85.4]
