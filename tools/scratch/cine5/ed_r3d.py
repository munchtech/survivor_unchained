# cine6 r3d: judge r3 (a25ec932) restages + cuts. CUT s3 (line to s2), s10 (lines to s9), s12's opening (crane starts moving).
# Restage s5 (wide, long lens, her hidden, the lamp his only key), s6 (90 mm on the heart), s8 (look at the heart, headroom,
# more spill), s9 (over her shoulder onto Grimtunnel, backlit, the heart brightest).
def edit(shots, f):
    s2, s3, s5, s6, s8, s9, s10, s12 = (shots[k] for k in ["2", "3", "5", "6", "8", "9", "10", "12"])
    # s2 carries "Is it morning?"
    s2["dur"] = 4.0
    s2["cues"].append({"at": 1.7, "do": "line", "id": "cin_heart_goes_down.morning"})
    # s5: she is hidden (her sword poked in; at the fold his head lands beside her), wide and long from the west
    s5["cam"] = {"pos": {"mark": "w", "off": [-12.5, 0.8, 1.6]}, "at": {"mark": "w", "off": [0.3, 1.6, 1.2]}, "lens": 55}
    s5["cues"] = [c for c in s5["cues"] if not (c.get("do") == "rig" and c.get("name") == "skin")]
    for c in s5["cues"]:
        if c.get("do") == "atmosphere": c.update({"key": 0.25, "hemi": 0.6})
        if c.get("do") == "lamp" and c.get("actor") == "warden" and c.get("at") == 3.6: c.update({"glow": 0.3, "over": 1.5})
    s5["cues"].insert(0, {"do": "hide", "actor": "her"})
    # s6: undo s5's multipliers (they stack on "now"); 90 mm on the heart, his head out of frame left, the heart brighter
    for c in s6["cues"]:
        if c.get("do") == "atmosphere": c.update({"key": 4.0, "hemi": 1.6667})
        if c.get("do") == "lamp" and c.get("actor") == "heart": c["glow"] = 3.0
    s6["cam"].update({"pos": {"mark": "w", "off": [4.4, 0.45, 1.0]}, "lens": 90, "fstop": 2.0})
    s6["cues"].insert(0, {"do": "hide", "actor": "her", "hidden": False})
    # s8: headroom (pulled back, raised), heart toward the right third; her head and eyes down on the heart; more spill, less rim
    s8["cam"].update({"pos": {"mark": "her", "off": [2.36, 1.75, -0.54]}, "at": {"mark": "her", "off": [0.0, 1.5, -0.18]}})
    for c in s8["cues"]:
        if c.get("do") == "atmosphere": c["rim"] = 0.2
        if c.get("do") == "rig" and c.get("name") == "spill": c.update({"energy": 4.0, "range": 3})
        if c.get("do") == "gaze": c["look"] = [0, 0.6]
        if c.get("do") == "head": c.update({"at": 0.6, "where": {"mark": "her", "off": [0.0, 1.29, -0.5]}, "amount": 1.0, "over": 1.0})
    # s9: over her right shoulder onto Grimtunnel (facing camera, moon behind him), the heart the brightest blue; s10's lines here
    s9["dur"] = 9.9
    s9["cam"] = {"pos": {"mark": "her", "off": [-0.35, 1.6, 0.6]}, "at": {"mark": "her", "off": [1.0, 0.85, -0.5]}, "lens": 50,
                 "focus": {"actor": "heart"}, "fstop": 2.8, "move": {"push": 0.3, "ease": "slow"}}
    for c in s9["cues"]:
        if c.get("actor") == "grim" and c.get("do") == "anim": c["where"] = {"mark": "her", "off": [-0.35, 0, 0.6]}
        if c.get("do") == "move" and c.get("actor") == "heart": c["to"] = {"mark": "her", "off": [0.8, 0.8, -0.34]}
        if c.get("do") == "lamp" and c.get("actor") == "heart": c["glow"] = 2.2
        if c.get("do") == "atmosphere": c["azimuth"] = 320
    s9["note"] = ("Over her right shoulder, her empty hand soft in the foreground: the mud bursts and Grimtunnel, up to the waist, has the heart "
                  "hugged to his chest, its blue the brightest thing in the frame, the moon behind him. G1; sniffs; G2. G3 begins and runs on over the crane.")
    s9["cues"] += [
        {"at": 3.9, "do": "sfx", "name": "sniff", "gain": 0.8},
        {"at": 4.4, "do": "sfx", "name": "sniff", "gain": 0.8},
        {"at": 5.3, "do": "line", "id": "cin_heart_goes_down.downstairs"},
        {"at": "after:cin_heart_goes_down.downstairs+0.4", "do": "line", "id": "cin_heart_goes_down.grateful"},
    ]
    # s12: the dive is heard, not seen: the crane starts already moving, mid-way, and settles on the held end frame
    s12["dur"] = 10.0
    s12["cam"] = {"pos": {"abs": [16.7, 4.8, -34.2]}, "at": {"abs": [1.3, 2.5, -35.5]}, "lens": 28,
                  "move": {"start": 0.0, "end": 6.0, "pos": {"abs": [30.0, 8.5, -34.0]}, "at": {"abs": [-4.0, 5.0, -31.0]}, "lens": 24, "ease": "out"}}
    for c in s12["cues"]:
        a = c.get("at")
        if isinstance(a, (int, float)):
            if a >= 7.9: c["at"] = round(a - 1.5, 2)      # groan 8.0 -> 6.5, music 10.1 -> 8.6
            elif a >= 2.9: c["at"] = round(a - 2.7, 2)    # the dive cues 3.0 -> 0.3, 4.6 -> 1.9
    s12["cues"] += [
        {"do": "hold", "actor": "her", "slot": "all", "piece": "@own"},
        {"do": "anim", "actor": "her", "clip": "@idle", "from": 0, "speed": 1, "blend": 0.4},
        {"do": "anim", "actor": "her", "clip": "Idle_Shield_Loop", "from": 0, "speed": 1, "blend": 0.4, "when": {"calling": ["warden"]}},
    ]
    f["shots"] = [s for s in f["shots"] if s["id"] not in ("3", "10")]
