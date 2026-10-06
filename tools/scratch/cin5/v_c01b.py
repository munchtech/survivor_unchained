"""C01 pass 6b variants (mkt.py): cameras for 6b, 6c and 10."""
ONLY = ["6a", "6b", "6c", "9", "10", "11", "11m", "12"]
V = {
    "6b": [
        {"id": "6bB", "cam": {"pos": [-11.37, 1.2, 91.27], "at": [-9.75, 0.76, 90.9], "lens": 40,
                              "focus": {"actor": "her", "bone": "eyes", "track": True}, "fstop": 4.0}},
        {"id": "6bC", "cam": {"pos": [-11.07, 1.12, 90.84], "at": [-9.75, 0.8, 90.86], "lens": 50,
                              "focus": {"actor": "her", "bone": "eyes", "track": True}, "fstop": 4.0}},
    ],
    "6c": [
        {"id": "6cB", "cam": {"pos": [-10.28, 0.46, 90.66], "at": [-9.73, 1.0, 90.87], "lens": 35,
                              "focus": {"abs": [-9.95, 0.6, 90.79]}, "fstop": 4.0}},
    ],
    "10": [
        {"id": "10B", "cam": {"pos": [-9.29, 1.4, 92.52], "at": {"actor": "her", "bone": "head", "track": True}, "lens": 50,
                              "focus": {"actor": "her", "bone": "eyes", "track": True}, "fstop": 2.8}},
    ],
}


def EDIT(shots, d):
    # A variant replays its shot from the same moment, the letter as it was then.
    for v in ("6bB", "6bC"):
        shots[v]["cues"] = [{"do": "hold", "slot": "letter", "piece": None}] + shots[v]["cues"]
    shots["6cB"]["cues"] = [{"do": "anim", "clip": "her/letter", "from": 4.4, "speed": 1, "blend": 0},
                            {"do": "hold", "slot": "letter", "piece": "letter_open"}] + shots["6cB"]["cues"]
