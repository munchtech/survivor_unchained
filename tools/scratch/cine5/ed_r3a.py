# cine5 r3a: the last round. Cut s4/s7/s11 and fold their beats; the Warden low-lit (lamp as the source) and wide
# (his model is a placeholder); her key ~4200 K, the halo down, the heart's spill doubled; s9 heart in Grimtunnel's
# claws + her recoil; s10 MCU from his eye line (+ the "grateful" line's head); s12 opens on the dive and cranes up.
WARM = "#ffd8b0"   # ~4200 K


def cue(s, pred):
    return [c for c in s["cues"] if pred(c)]


def drop(s, pred):
    s["cues"] = [c for c in s["cues"] if not pred(c)]


def skinrig(s, frm, energy, aim_bone="head"):
    drop(s, lambda c: c.get("do") == "rig" and c.get("name") == "skin")
    s["cues"].insert(0, {"do": "rig", "name": "skin", "from": {"lens": frm}, "aim": {"actor": "her", "bone": aim_bone},
                         "color": WARM, "energy": energy, "angle": 32, "range": 6})


def edit(shots, f):
    s2, s3, s5, s6, s8, s9, s10, s12 = (shots[k] for k in ["2", "3", "5", "6", "8", "9", "10", "12"])
    s4, s7, s11 = shots["4"], shots["7"], shots["11"]

    # --- s2: wide, side-on from the east, low at the water; the night darker, his lamp the light on him.
    s2["type"] = "WS"
    s2["note"] = ("Wide and low at the water from the east: he goes down on his knees in the river; the greatsword falls from his right hand "
                  "and sinks. His left arm stays up, the lamp held clear of the water. His lamp is the light on him; the moon only edges him.")
    s2["cam"] = {"pos": {"mark": "w", "off": [7.5, 1.0, 2.2]}, "at": {"mark": "w", "off": [0.0, 1.9, 1.2]}, "lens": 30}
    for c in s2["cues"]:
        if c.get("do") == "atmosphere":
            c.update({"key": 0.45, "hemi": 0.18, "env": 0.2, "rim": 0.7, "exposure": 1.0, "azimuth": 195})
        if c.get("do") == "lamp":
            c.update({"glow": 1.2, "flame": 0.5, "halo": 0.8})

    # --- s3: no close-up on him (placeholder): a wide profile from the west, his silhouette against the moon, the lamp on his hood.
    s3["type"] = "WS"
    s3["note"] = ("Wide, low, from the west: his kneeling profile against the moonlit water, the lamp held up before his face, "
                  "its light the only light on him. He looks at the lamp, not at her. W4, in a tired man's voice.")
    s3["cam"] = {"pos": {"mark": "w", "off": [-6.5, 1.1, 1.4]}, "at": {"mark": "w", "off": [0.2, 2.3, 0.6]}, "lens": 32}
    s3["cues"].insert(0, {"do": "atmosphere", "preset": "now", "azimuth": 15})

    # --- s5: s4 folded in: the fist lowers, the lamp goes under and glows there; then the fold, from the water.
    s5["dur"] = 5.8
    s5["note"] = ("Low at the water from the west, the moon behind him: the fist lowers and the lamp goes under, glowing in the river beside him; "
                  "then he folds forward into the water and is still. A beat. The water over his back lightens from beneath.")
    s5["cam"] = {"pos": {"mark": "w", "off": [-6.0, 0.9, 3.4]}, "at": {"mark": "w", "off": [0.3, 1.3, 0.8]}, "lens": 30}
    skinrig(s5, [2.5, 1.5, -2.5], 3.2, aim_bone="chest")
    drop(s5, lambda c: c.get("do") in ("anim", "place", "lamp") or (c.get("do") == "sfx" and c.get("name") == "water_close"))
    s5["cues"] += [
        {"do": "atmosphere", "preset": "now", "azimuth": 10},
        {"at": 0.0, "do": "anim", "actor": "warden", "clip": "folk/m_lamp_down", "from": 0, "speed": 1, "blend": 0.3},
        {"at": 1.1, "do": "sfx", "name": "lamp_out", "gain": 0.6},
        {"at": 1.1, "do": "lamp", "actor": "warden", "glow": 0.45, "flame": 0.25, "halo": 0.5, "over": 0.5},
        {"at": 2.3, "do": "anim", "actor": "warden", "clip": "folk/m_fold_forward", "from": 0, "speed": 1, "blend": 0.3},
        {"at": 3.2, "do": "sfx", "name": "water_close", "gain": 0.4},
        {"at": 3.6, "do": "lamp", "actor": "warden", "glow": 0.0, "over": 1.0},
        {"at": 4.4, "do": "place", "actor": "heart", "where": {"mark": "w", "off": [0, 0, 2.0], "y": -1.25}},
        {"at": 4.4, "do": "lamp", "actor": "heart", "glow": 0.4, "over": 1.2},
    ]

    # --- s6: wide on his back, low, the heart rising against the dark trees and lighting the wet cloak.
    s6["type"] = "MLS"
    s6["note"] = ("Low and wide from the east: the heart lies on his back over his chest, then lifts off it, a fist of cold light, turning, "
                  "water running off it, its light on the wet cloak. No line: its hum, and the river.")
    s6["cam"] = {"pos": {"mark": "w", "off": [4.2, 0.7, 3.6]}, "at": {"actor": "heart", "track": True}, "lens": 40,
                 "focus": {"actor": "heart"}, "fstop": 2.8, "move": {"push": 0.4, "ease": "slow"}}
    for c in s6["cues"]:
        if c.get("do") == "lamp" and c.get("actor") == "heart":
            c.update({"glow": 1.5})
    s6["cues"].insert(0, {"do": "atmosphere", "preset": "now", "azimuth": 200})

    # --- s8: s7 folded in. Side MCU; the heart drifts in from frame right as her hand comes up.
    s8["type"] = "MCU"
    s8["dur"] = 3.2
    s8["note"] = ("Side-on, close: the heart drifts in from frame right, like a thing finding its way; her hand comes up under it, and they "
                  "hang a hand's breadth apart, its blue light in her palm and on her fingers and chin.")
    s8["cam"]["fstop"] = 4.0
    s8["cues"] = [
        {"do": "rig", "name": "skin", "from": {"lens": [0.95, 0.55, -0.95]}, "aim": {"actor": "her", "bone": "head"}, "color": WARM, "energy": 0.85, "angle": 32, "range": 6},
        {"do": "atmosphere", "preset": "now", "azimuth": 160, "key": 1.3, "hemi": 1.4, "rim": 0.35},
        {"do": "skin", "sky": 0.3, "ear": 0.4},
        {"do": "hold", "actor": "her", "slot": "all", "piece": None},
        {"do": "place", "actor": "her", "mark": "her", "heading": 2.18},
        {"do": "music", "mood": "mystery", "intensity": 0.75, "over": 3.0},
        {"do": "anim", "clip": "her/cup_hands", "from": 0.6, "speed": 0.6, "blend": 0.3},
        {"do": "gaze", "look": [0, 0.1], "wander": 0.02},
        {"do": "face", "keys": {"eyes_wide": 0.3, "mouth_open": 0.12, "brows_sad": 0.15}, "over": 1.0},
        {"do": "place", "actor": "heart", "where": {"mark": "her", "off": [0.15, 1.5, -1.25]}},
        {"do": "lamp", "actor": "heart", "glow": 1.5, "over": 0.6},
        {"do": "move", "actor": "heart", "to": {"mark": "her", "off": [0.0, 1.29, -0.5]}, "dur": 1.6},
        {"do": "rig", "name": "spill", "from": {"actor": "heart"}, "aim": {"actor": "her", "bone": "hand_l", "off": [0, 0, -0.05]}, "color": "#6fa8ff", "energy": 2.0, "angle": 35, "range": 2},
        {"do": "sfx", "name": "heart_hum", "gain": 1.0},
        {"at": 0.2, "do": "head", "actor": "her", "where": {"actor": "heart"}, "amount": 0.8, "over": 0.6},
    ]

    # --- s9: from the north, her face to camera, Grimtunnel in profile; the heart glowing in his claws; she recoils, hands still up.
    s9["note"] = ("The mud bursts up under her hand: Grimtunnel, up to the waist, snatches the heart out of the air and hugs it up to his chest, "
                  "its light on his face. She jerks back, her hands still up where it was. G1. A hard shake on the burst.")
    s9["cam"] = {"pos": {"mark": "her", "off": [-0.7, 1.25, -3.1]}, "at": {"mark": "her", "off": [0.5, 1.0, -0.3]}, "lens": 30}
    skinrig(s9, [1.6, 0.9, -1.6], 2.2)
    drop(s9, lambda c: (c.get("do") == "hold") or (c.get("do") == "anim" and c.get("actor") == "her")
         or c.get("do") == "atmosphere" or (c.get("do") == "lamp" and c.get("actor") == "heart")
         or (c.get("do") == "move" and c.get("actor") == "heart"))
    s9["cues"] += [
        {"do": "atmosphere", "preset": "now", "azimuth": 110},
        {"do": "lamp", "actor": "heart", "glow": 1.3},
        {"at": 0.25, "do": "move", "actor": "heart", "to": {"mark": "her", "off": [0.92, 0.78, -0.42]}, "dur": 0.25},
        {"at": 0.05, "do": "anim", "actor": "her", "clip": "her/flinch", "from": 0, "speed": 1, "blend": 0.05},
    ]

    # --- s10: MCU from his eye line (low, close to where his head is), face in the upper third, key low and frontal,
    #     the heart's blue on her chin; the weapons back in her hands off-frame. Then the "grateful" line begins (s11 cut).
    s10["type"] = "MCU"
    s10["dur"] = 8.6
    s10["note"] = ("From his eye line, up at her, close: in his arms the heart's light goes on straining out toward her, blue on her chin. "
                   "Sniffs; G2 (downstairs); a laugh. G3 begins over her face and runs on over the dive.")
    s10["cam"] = {"pos": {"mark": "her", "off": [0.72, 1.2, -0.95]}, "at": {"mark": "her", "off": [0.0, 1.45, -0.02]}, "lens": 35,
                  "focus": {"actor": "her", "bone": "eyes"}, "fstop": 4.0}
    skinrig(s10, [0.45, 0.1, -0.25], 1.0)
    drop(s10, lambda c: c.get("do") in ("atmosphere", "head"))
    s10["cues"] += [
        {"do": "atmosphere", "preset": "now", "azimuth": 150},
        {"do": "hold", "actor": "her", "slot": "all", "piece": "@own"},
        {"do": "anim", "actor": "her", "clip": "@idle", "from": 0, "speed": 1, "blend": 0.4},
        {"do": "anim", "actor": "her", "clip": "Idle_Shield_Loop", "from": 0, "speed": 1, "blend": 0.4, "when": {"calling": ["warden"]}},
        {"do": "rig", "name": "spill", "from": {"actor": "heart"}, "aim": {"actor": "her", "bone": "head"}, "color": "#6fa8ff", "energy": 0.6, "angle": 35, "range": 2.5},
        {"do": "head", "actor": "her", "where": {"mark": "her", "off": [0.9, 0.95, -0.55]}, "amount": 0.85, "over": 0.3},
        {"at": "after:cin_heart_goes_down.downstairs+0.4", "do": "line", "id": "cin_heart_goes_down.grateful"},
    ]

    # --- s12: opens behind her on the dive (mud, the glow going down), then cranes up and back to the ELS.
    s12["dur"] = 11.5
    s12["note"] = ("Behind her, low: the end of G3; Grimtunnel turns away and dives head first, still clutching the heart; the mud closes, its light "
                   "shows going down and is gone. The camera rises and pulls back high over the north bank, far east of the ford: her small in it, the "
                   "road's lamps ember-blue. Silence; then a groan from under everything; the river shivers; every lamp dips and comes back; "
                   "the sky's lowest edge has gone rose and grey.")
    s12["cam"] = {"pos": {"mark": "her", "off": [3.2, 1.5, 2.6]}, "at": {"mark": "her", "off": [0.9, 0.5, -0.6]}, "lens": 32,
                  "move": {"start": 3.6, "end": 7.8, "pos": {"abs": [30.0, 8.5, -34.0]}, "at": {"abs": [-4.0, 5.0, -31.0]}, "lens": 24, "ease": "inout"}}
    drop(s12, lambda c: c.get("do") in ("hide",) or (c.get("do") == "event" and c.get("name") == "grim_gone"))
    for c in s12["cues"]:
        a = c.get("at")
        if isinstance(a, (int, float)):
            c["at"] = round(a + 6.5, 2)
        if c.get("do") == "atmosphere":
            c["over"] = 10.0
    s12["cues"] += [
        {"do": "rig", "name": "skin", "from": {"lens": [1.75, 1.0, -1.75]}, "aim": {"actor": "her", "bone": "head"}, "color": WARM, "energy": 1.7, "angle": 32, "range": 6},
        {"do": "anim", "actor": "grim", "clip": "hug", "where": {"mark": "her", "off": [3.0, 0, -2.5]}},
        {"do": "move", "actor": "heart", "to": {"mark": "her", "off": [1.0, 0.78, -0.62]}, "dur": 0.05},
        {"at": 3.0, "do": "event", "name": "grim_down"},
        {"at": 3.0, "do": "sfx", "name": "roots", "gain": 1.0},
        {"at": 3.0, "do": "move", "actor": "heart", "to": {"mark": "her", "off": [1.0, 0, -0.5], "y": -2.2}, "dur": 0.9},
        {"at": 3.0, "do": "lamp", "actor": "heart", "glow": 0.0, "over": 1.3},
        {"at": 4.6, "do": "hide", "actor": "heart"},
        {"at": 4.6, "do": "event", "name": "grim_gone"},
    ]

    # the cut shots go
    f["shots"] = [s for s in f["shots"] if s["id"] not in ("4", "7", "11")]
