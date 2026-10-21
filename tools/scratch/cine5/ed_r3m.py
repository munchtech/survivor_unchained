# cine6 r3m: s9 can't show the placeholder Grimtunnel and pass, so the snatch happens IN s8 (which passed): the burst, the heart
# yanked down out of frame from her palm, her empty hand, her start and look down; G1 over her. s9 CUT. Grimtunnel is first seen
# tiny from the crane in s12, over which G2 and G3 play before he dives; then the groan.
def edit(shots, f):
    s8, s12 = shots["8"], shots["12"]
    s8["dur"] = 8.0
    s8["note"] = ("Side-on, close: the heart drifts in to her palm and she looks down at it, its blue on her face. Then the mud bursts below "
                  "frame: the heart is yanked down out of her hand and out of frame, its light now from below. She starts, eyes wide, and looks "
                  "down at him. G1 off-screen; two sniffs.")
    T = 3.2
    s8["cues"] += [
        {"at": T, "do": "event", "name": "grim_up"},
        {"at": T, "do": "sfx", "name": "burst", "gain": 1.0},
        {"at": T, "do": "vfx", "kind": "shake", "amount": 0.45},
        {"at": T + 0.05, "do": "move", "actor": "heart", "to": {"mark": "her", "off": [0.55, 0.25, -0.75]}, "dur": 0.18},
        {"at": T + 0.05, "do": "face", "keys": {"eyes_wide": 0.7, "mouth_open": 0.22, "brows_sad": 0.0}, "over": 0.12},
        {"at": T + 0.05, "do": "lids", "value": 1, "over": 0.06},
        {"at": T + 0.23, "do": "lids", "value": None},
        {"at": T + 0.1, "do": "head", "actor": "her", "where": {"mark": "her", "off": [0.55, 0.3, -0.85]}, "amount": 1.0, "over": 0.3},
        {"at": T + 0.1, "do": "music", "mood": "silence"},
        {"at": T + 0.5, "do": "line", "id": "cin_heart_goes_down.nobodys"},
        {"at": T + 3.9, "do": "sfx", "name": "sniff", "gain": 0.8},
        {"at": T + 4.4, "do": "sfx", "name": "sniff", "gain": 0.8},
    ]
    # s12: Grimtunnel up (tiny from the crane) with the heart; G2, G3; then the dive; the groan after.
    s12["dur"] = 16.0
    s12["cam"]["move"]["end"] = 9.0
    sh = 10.0   # the dive (was at 0.3) now after the lines
    for c in s12["cues"]:
        a = c.get("at")
        if isinstance(a, (int, float)):
            if a >= 6.0: c["at"] = round(a + 5.0, 2)       # groan 6.5 -> 11.5, lamps 7.6/8.2 -> 12.6/13.2, music 8.6 -> 13.6
            elif a >= 0.2: c["at"] = round(a + sh, 2)      # dive cues 0.3 -> 10.3, 1.9 -> 11.9
    s12["cues"] = [
        {"do": "spawn", "actor": "grim", "def": "grimtunnel", "where": {"mark": "her", "off": [1.0, 0, -0.5]}, "style": "burrow", "tag": "grim", "neutral": True, "sink": 0.55},
        {"at": 0.3, "do": "line", "id": "cin_heart_goes_down.downstairs"},
        {"at": "after:cin_heart_goes_down.downstairs+0.4", "do": "line", "id": "cin_heart_goes_down.grateful"},
    ] + s12["cues"]
    f["shots"] = [s for s in f["shots"] if s["id"] != "9"]
