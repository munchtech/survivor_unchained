def edit(S, f):
    f["draft"] = "Previs pass 1: surveyed in the Waystation at dawn; the zone's own Rook and Watch are framed where they stand. Townsfolk who stop and turn, Rook's look to the tower, and the lamp's smoke are to come."
    f["marks"]["window"] = [31.9, 9.6, -5.7]
    S["B1"]["cues"].insert(0, {"do": "glow", "name": "towerlamp", "where": {"abs": [31.9, 9.6, -5.7]}, "color": "#ffd9a0", "size": 0.07, "energy": 2.2, "spread": 5, "halo": 0.3})
    S["B2"]["cam"] = {"pos": [-5.2, 1.9, 36.8], "at": [-2.0, 1.5, 26.0], "lens": 50}
    S["B2"]["cues"].append({"do": "move", "to": [0.0, 21.5], "dur": 3.5, "clip": "Walk_Formal_Loop", "speed": 0.8})
    S["B4"]["cam"] = {"pos": [-13.4, 1.7, 11.8], "at": [0.0, 1.5, 11.8], "lens": 35, "focus": 2.3, "fstop": 2.8,
                      "move": {"focus": 13.5, "start": 0.8, "end": 2.2, "ease": "inout"}}
    S["B4a"]["cam"] = {"pos": [-11.0, 1.7, 11.0], "at": {"abs": [31.9, 9.6, -5.7]}, "lens": 200}
    S["B4a"]["cues"].append({"at": 0.6, "do": "glow", "name": "towerlamp", "remove": True})
    S["B4b"]["cam"] = {"pos": [-13.4, 1.7, 11.8], "at": [0.0, 1.5, 11.8], "lens": 35, "focus": 2.3, "fstop": 2.8}
