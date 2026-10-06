"""C04 A: flask_drink staged with the gourd and its cork; A6 from her front-left; A8's crane turns onto her."""


def edit(shots, f):
    a1 = shots["A1"]
    a1["cues"].insert(0, {"do": "hold", "slot": "wrist.r", "piece": "gourd_hung"})
    a1s = shots["A1s"]
    a1s["cues"].insert(0, {"do": "hold", "slot": "wrist.r", "piece": "gourd_hung"})

    a6 = shots["A6"]
    # Her left side: the drinking arm is her right, so the camera stands where it never crosses her face.
    a6["cam"] = {"pos": {"actor": "her", "bone": "eyes", "off": [-0.6, -0.1, -1.8]}, "at": {"actor": "her", "bone": "eyes", "off": [0, -0.1, 0]},
                 "lens": 50, "focus": {"actor": "her", "bone": "eyes", "track": True}, "fstop": 2.8}
    a6["note"] = ("From her front-left, the drinking arm away from camera: she lifts the gourd on its cord, bites the cork and "
                  "pulls it, and her left hand takes it from her teeth; under her nose she stops: the river. She drinks anyway, "
                  "long, eyes shut. She lowers it.")
    a6["cues"] = [
        {"do": "hold", "slot": "wrist.r", "piece": None},
        {"do": "hold", "slot": "cork", "piece": None},
        {"do": "hold", "slot": "all", "piece": None},
        {"do": "hold", "slot": "handslot.r", "piece": "gourd"},
        {"do": "anim", "clip": "her/flask_drink", "from": 0, "speed": 1, "blend": 0.3},
        {"at": 0.95, "do": "pass", "what": "cork", "to": "head"},
        {"at": 1.0, "do": "sfx", "name": "click", "gain": 0.5},
        {"at": 1.25, "do": "pass", "what": "cork", "to": "hand_l"},
    ] + [c for c in a6["cues"] if c.get("do") in ("face", "lids")]

    a8 = shots["A8"]
    a8["cam"]["move"] = {"at": {"actor": "her", "bone": "chest", "track": True}, "start": "end-3.0", "ease": "inout", "follow": True}
