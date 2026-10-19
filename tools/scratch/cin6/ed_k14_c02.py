# k14 (C02): s4, s5, s6, s7, s8 cut (k13B_verdict.md); the call onto s2, lie_down onto s10, the warden's state carried.
def edit(shots, f):
    cut = {"4", "5", "6", "7", "8"}
    s2, s10 = shots["2"], shots["10"]
    s2["cues"].append({"at": 0.3, "do": "line", "id": "cin_none_cross.call"})
    s2["fit"] = ["cin_none_cross.call"]; s2["tail"] = 0.5
    s4 = shots["4"]
    atm = next(c for c in s4["cues"] if c.get("do") == "atmosphere")
    # s10: the warden up and standing where s5/s6 left him (lamp lit full, at his end mark); the night air s4 set (rim);
    # "Lie down." at 0.1, 2.6 s.
    s10["cues"][0:0] = [
        dict(atm),
        {"do": "place", "actor": "warden", "mark": "warden_end", "tilt": 0},
        {"do": "lamp", "actor": "warden", "glow": 1.0},
        {"at": 0.1, "do": "line", "id": "cin_none_cross.lie_down"},
    ]
    s10["dur"] = 2.6
    f["shots"][:] = [s for s in f["shots"] if s["id"] not in cut]
