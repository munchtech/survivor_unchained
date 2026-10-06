def edit(S, f):
    f["marks"]["rook2"] = [-10.3, 12.2, 2.04]
    f["cast"]["rook"] = {"kind": "npc", "def": "rook", "mark": "rook2"}
    S["B1"]["cues"].insert(0, {"do": "event", "name": "rook_cine"})
    S["B1"]["cues"].insert(1, {"do": "anim", "actor": "rook", "clip": "Idle_FoldArms_Loop", "blend": 0})
    S["B2"]["cam"] = {"pos": [-5.0, 2.0, 35.8], "at": [-1.0, 1.5, 26.0], "lens": 50}
    S["B4"]["cam"] = {"pos": [-11.1, 1.7, 13.3], "at": [0.0, 1.4, 7.0], "lens": 35, "focus": 1.3, "fstop": 2.8,
                      "move": {"focus": 12.5, "start": 0.8, "end": 2.2, "ease": "inout"}}
    S["B4"]["cues"].append({"at": 2.6, "do": "look", "actor": "rook", "where": {"abs": [31.9, 9.6, -5.7]}, "over": 0.5})
    S["B4a"]["cam"] = {"pos": [-10.0, 1.75, 12.0], "at": {"abs": [31.9, 9.6, -5.7]}, "lens": 200}
    S["B4b"]["cam"] = {"pos": [-11.1, 1.7, 13.3], "at": [0.0, 1.4, 7.0], "lens": 35, "focus": 1.3, "fstop": 2.8}
    S["B4b"]["cues"] = [
        {"do": "look", "actor": "rook", "where": [0.0, 1.4, 7.0], "over": 0.5},
        {"at": 0.8, "do": "anim", "actor": "rook", "clip": "Idle_Loop", "blend": 0.6},
    ]
