"""C01 pass 6c: 6b low across the coals; the snap cheated 20 degrees on the cut so it ends on R1, who rises
clear of the pack; the take and the crane with her head in frame; the arcanist's shot for her new facing."""
import math

H_KNEEL = -1.9451
CHEAT = math.radians(20)
SNAP = math.radians(55)


def edit(shots, f):
    m = f["marks"]
    # West, past the fire, as it was first written; 10 degrees right of where the snap now leaves her.
    m["r1"] = [-15.14, 91.29]
    # Shot 10 turns her where she kneels, 20 degrees to her right, on its cut (an MCU: the coals are off frame),
    # so the snap's 55 degrees to her left end on R1.
    m["kneel10"] = [-9.65, 90.9, round(H_KNEEL - CHEAT, 4)]
    m["stood"] = [-9.86, 90.95, round(H_KNEEL - CHEAT + SNAP, 4)]

    s6b = shots["6b"]
    s6b["type"] = "MCU"
    s6b["cam"] = {"pos": [-11.01, 0.6, 90.72], "at": [-9.78, 0.82, 90.86], "lens": 35,
                  "focus": {"actor": "her", "bone": "eyes", "track": True}, "fstop": 2.8}
    s6b["note"] = ("Low across the coals, under her eyes, so she is lit from below and the night is behind her: the hand comes "
                   "back from the coals; she turns the wrist up to the cord wound on it and the full gourd; across at the "
                   "bedroll, dry (N1); then from inside her top the letter, folded, and both hands open it below her face. She looks.")

    s9 = shots["9"]
    s9["cam"]["pos"] = [-4.3, 1.5, 94.6]
    s9["cam"]["at"] = [-10.0, 0.6, 92.3]

    s10 = shots["10"]
    s10["cam"] = {"pos": [-10.56, 1.35, 92.13], "at": {"actor": "her", "bone": "head", "off": [-0.24, 0.0, 0.06], "track": True},
                  "lens": 50, "focus": {"actor": "her", "bone": "eyes", "track": True}, "fstop": 2.8}
    cues = [c for c in s10["cues"] if c.get("do") != "place"]
    cues.insert(0, {"do": "place", "mark": "kneel10"})
    cues.append({"at": 0.85, "do": "head", "where": {"mark": "r1", "off": [0, 1.3, 0]}, "amount": 0.8, "over": 0.4})
    s10["cues"] = cues

    s11 = shots["11"]
    s11["cam"] = {"pos": [-6.07, 1.1, 86.77], "at": [-8.85, 1.0, 89.5], "lens": 35,
                  "focus": {"mark": "reach", "off": [0, 1.0, 0]}, "fstop": 4.0}
    # The look from 10 is let go as she comes to the log.
    s11["cues"].insert(0, {"do": "head", "amount": 0, "over": 0.3})

    s11m = shots["11m"]
    s11m["cam"] = {"pos": [-10.6, 1.02, 91.28], "at": [-10.03, 1.48, 90.99], "lens": 35,
                   "focus": {"abs": [-10.15, 1.2, 91.02]}, "fstop": 2.8}
    s11m["cues"].insert(0, {"do": "head", "amount": 0, "over": 0.3})

    s12 = shots["12"]
    s12["cam"]["at"] = {"mark": "end", "off": [0, 1.4, 0]}
