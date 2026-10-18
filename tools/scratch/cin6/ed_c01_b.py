# C01's end (the owner, 18 Oct: "the silly slide across the log"): shot 11 slid her 1.25 m along the log in 0.7 s on
# her idle. Now the cut lands on the action: she is at her weapon, already bending to it; every later cue 0.7 s sooner.
# Shot 12 framed her hips (head out of frame under the bars, the head 3 cm lower since the body build): aim at her chest.
def edit(shots, f):
    s = shots["11"]
    s["dur"] = 2.8
    s["still"] = 1.1
    s["note"] = ("Side-on and wide enough for all of her: on the cut she is at the log's end, already bending to her weapon; "
                 "she takes it and comes round with it ready. On three sides the frost breaks.")
    cues = []
    for c in s["cues"]:
        if c.get("do") == "move" and c.get("to") == "reach":
            cues.append({"do": "place", "mark": "reach", "heading": 1.5708})
            continue
        if isinstance(c.get("at"), (int, float)):
            c["at"] = round(max(0.0, c["at"] - 0.7), 2)
        if c.get("do") == "anim" and c.get("clip") == "PickUp_Table":
            c["from"] = 0.15
            c["blend"] = 0
        if c.get("do") == "anim" and c.get("clip") == "Spell_Simple_Enter":
            c["blend"] = 0
        cues.append(c)
    s["cues"] = cues
    t = shots["12"]
    t["cam"]["pos"] = [-8.6, 1.5, 86.4]
    t["cam"]["at"]["off"] = [0, 1.4, 0]
