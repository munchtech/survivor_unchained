import os

LEFT = os.environ.get("CAM", "") == "left"


def shot(d, sid):
    return next(s for s in d["shots"] if s["id"] == sid)


def EDITS(d):
    a6 = shot(d, "A6")
    # Her hands emptied (unseen in A5's close-up), the flask clip from A6's start.
    shot(d, "A5")["cues"].insert(0, {"do": "hold", "slot": "all", "piece": None})
    a6["cues"].insert(0, {"do": "anim", "clip": "her/flask_drink", "blend": 0.3})
    if LEFT:
        a6["cam"]["pos"] = {"actor": "her", "bone": "eyes", "off": [-1.25, -0.15, -1.45]}
