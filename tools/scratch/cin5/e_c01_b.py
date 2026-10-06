"""C01 pass 6b: cameras for the letter, the snap and the take; R1 clear of the bedroll; the weapon taken into
her hand where it lies; the arcanist's own shot with her first light."""
import copy, math

WEAPONS = {"calling": ["warden", "reaver", "stalker"]}
ARC = {"calling": ["arcanist"]}


def edit(shots, f):
    m = f["marks"]
    # R1 9 degrees right of where the snap turns her, 5 m off, where shot 9 sees it clear of the bedroll.
    m["r1"] = [-14.22, 92.94]
    # Where each ending leaves her body (her own body takes it there).
    m["took"] = [-9.0, 89.43, round(math.pi, 4)]
    m["stood"] = [-9.8, 91.0, round(-1.9451 + math.radians(55), 4)]

    s6b = shots["6b"]
    s6b["type"] = "MS"
    s6b["cam"] = {"pos": [-11.32, 1.15, 90.83], "at": [-9.75, 0.76, 90.85], "lens": 40,
                  "focus": {"actor": "her", "bone": "eyes", "track": True}, "fstop": 4.0}
    s6b["note"] = ("Across the coals, a little above her eyes, so her face and her hands are both in: the hand comes back "
                   "from the coals; she turns the wrist up and looks at the cord wound on it and the full gourd; across at "
                   "the bedroll, dry (N1); then from inside her top the letter, folded, and both hands open it. She looks.")

    s6c = shots["6c"]
    s6c["cam"] = {"pos": [-9.63, 1.06, 90.61], "at": [-9.95, 0.58, 90.79], "lens": 50,
                  "focus": {"abs": [-9.95, 0.58, 90.79]}, "fstop": 4.0}
    s6c["note"] = ("Close over her right shoulder, down onto the open letter: wet through, the ink run to blue water down the "
                   "lines it was, no word left. She folds it.")

    s9 = shots["9"]
    s9["cam"]["pos"] = [-4.3, 1.5, 94.6]
    s9["cam"]["at"] = [-10.0, 0.6, 92.3]

    s10 = shots["10"]
    # On her left, 45 degrees off where the snap leaves her facing: her face comes round through the light
    # and past the lens, and she ends looking off it, screen left, at R1.
    s10["cam"] = {"pos": [-9.92, 1.35, 92.27], "at": {"actor": "her", "bone": "head", "track": True}, "lens": 50,
                  "focus": {"actor": "her", "bone": "eyes", "track": True}, "fstop": 2.8}

    s11 = shots["11"]
    keep = [c for c in s11["cues"] if c.get("do") in ("sfx", "world", "spawn") or (c.get("do") == "face" and "when" not in c)]
    s11["when"] = WEAPONS
    s11["note"] = ("From the north-east, low, across the log's end: she steps in, takes her weapon up off the log, and comes "
                   "round 110 degrees onto the road, low and ready, toward camera. Behind her, south-west, the frost breaks.")
    s11["cam"] = {"pos": [-6.9, 1.05, 87.6], "at": [-8.75, 0.95, 89.55], "lens": 35,
                  "focus": {"mark": "reach", "off": [0, 1.0, 0]}, "fstop": 4.0}
    s11["cues"] = [
        {"do": "place", "mark": "reach"},
        {"do": "anim", "clip": "her/take_from_log", "from": 0, "speed": 1, "blend": 0},
        # Taken up where it lies, settling into her grip as she lifts it.
        {"at": 0.55, "do": "prop", "name": "weapon", "to": "handslot.r", "over": 0.35},
    ] + keep

    s11m = copy.deepcopy(s11)
    s11m["id"] = "11m"
    s11m["when"] = ARC
    s11m["type"] = "MCU"
    s11m["note"] = ("The arcanist, where she rose: low before her, her hands in the foreground: she cups them, and waits; "
                    "nothing; then a spark catches and her palms fill with light in her school's colour, lighting her face "
                    "from below. A smile, half a second, gone.")
    s11m["cam"] = {"pos": [-10.41, 1.02, 91.59], "at": [-9.95, 1.45, 91.1], "lens": 35,
                   "focus": {"abs": [-10.08, 1.2, 91.19]}, "fstop": 2.8}
    s11m["cues"] = [
        {"do": "anim", "clip": "her/cup_hands", "from": 0, "speed": 1, "blend": 0.25},
        {"do": "gaze", "look": [0, 0.7], "wander": 0.02},
        {"at": 1.4, "do": "hold", "slot": "palms", "piece": "@palms"},
        {"at": 1.6, "do": "face", "keys": {"smile": 0.15, "eyes_wide": 0.3}, "over": 0.15},
        {"at": 2.1, "do": "face", "keys": {"smile": 0, "brows_angry": 0.3}, "over": 0.2},
    ] + [c for c in keep if c.get("do") != "face"]
    i = [s["id"] for s in f["shots"]].index("11")
    f["shots"].insert(i + 1, s11m)

    s12 = shots["12"]
    s12["cues"] = [
        {"at": 0.0, "do": "place", "mark": "took", "when": WEAPONS},
        {"at": 0.0, "do": "place", "mark": "stood", "when": ARC},
        # What was left on the log: her own body has it from the cut.
        {"at": 0.0, "do": "prop", "name": "weapon", "remove": True, "when": ARC},
        {"at": 0.0, "do": "prop", "name": "shield", "remove": True},
        {"at": 0.0, "do": "hold", "slot": "palms", "piece": None, "when": ARC},
        {"at": 0.0, "do": "play"},
    ] + [c for c in s12["cues"] if c.get("do") not in ("play", "place", "prop", "hold")]
