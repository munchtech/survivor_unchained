"""C01 pass 6: animation's new clips staged (letter, kneel_to_stand_snap, take_from_log, cup_hands),
the gourd on her wrist, the letter, R1 where the snap turns her, the weapon where the take finds it."""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geo import *

KNEEL = (-9.65, 90.9)
H_KNEEL = -1.9451
SNAP = math.radians(55.0)      # story.py SNAP_TURN: to her left
TAKE = math.radians(110.0)     # story.py TAKE_TURN
GRIP_AT = (-0.10, 0.78, 0.55)  # story.py: her right, up, ahead

# The seat log (Camp.cs): its axis from the north end to the south end, centre 0.215 up, r 0.265.
A, B = (-8.25, 89.18), (-8.75, 91.42)
axis = norm((B[0] - A[0], 0, B[1] - A[1]))
west = norm((-axis[2], 0, axis[0]))           # the log's west side, toward the fire
if west[0] > 0:
    west = tuple(-c for c in west)
zg = 89.9
t = (zg - A[1]) / (B[1] - A[1])
on_axis = (A[0] + (B[0] - A[0]) * t, zg)
# The grip just west of the axis, 0.78 up: the blade down over the log's top to the ground east.
grip = (on_axis[0] + west[0] * 0.015, 0.78, on_axis[1] + west[2] * 0.015)
dirY = norm((-west[0] * 0.5, -0.867, -west[2] * 0.5))
X, Y, Z = basis_for(dirY, axis)
ROT = euler_yxz(X, Y, Z)

# She comes at it facing so that the take's turn ends facing north, up the road (the end mark).
H_REACH = math.pi - TAKE
f, l = fwd(H_REACH), left(H_REACH)
reach = (grip[0] - f[0] * GRIP_AT[2] - l[0] * GRIP_AT[0], grip[2] - f[1] * GRIP_AT[2] - l[1] * GRIP_AT[0])
# R1 where the snap turns her: 55 degrees to her left of the kneel, 6.5 m off.
r1 = her(KNEEL, H_KNEEL + SNAP, 0, 6.5)
print("grip", [round(c, 3) for c in grip], "rot", ROT, "reach", [round(c, 3) for c in reach], round(H_REACH, 4), "r1", [round(c, 2) for c in r1])

# 6b: front-left of her, 40 degrees off her facing, at her eyes' height.
fl = fwd(H_KNEEL + math.radians(40))
CAM6B = [round(fl[0] * 1.1, 3), 0.04, round(fl[1] * 1.1, 3)]
# 6c: over her right shoulder, behind and above her head, down onto the letter.
b, r = fwd(H_KNEEL + math.pi), left(H_KNEEL - 0)  # behind; her left
rt = (-r[0], -r[1])
CAM6C = [round(b[0] * 0.10 + rt[0] * 0.13, 3), 0.07, round(b[1] * 0.10 + rt[1] * 0.13, 3)]
MID6C = [round(rt[0] * 0.10, 3), 0.0, round(rt[1] * 0.10, 3)]
print("cam6b", CAM6B, "cam6c", CAM6C, "mid6c", MID6C)

WEAPONS = {"calling": ["warden", "reaver", "stalker"]}
ARC = {"calling": ["arcanist"]}


def edit(shots, f):
    m = f["marks"]
    m["reach"] = [round(reach[0], 3), round(reach[1], 3), round(H_REACH, 4)]
    m["r1"] = [round(r1[0], 2), round(r1[1], 2)]
    # Where the take leaves her body (her own body takes it there, facing up the road).
    m["took"] = [round(reach[0], 3), round(reach[1] - 0.15, 3), round(math.pi, 4)]
    m["stood"] = [KNEEL[0], KNEEL[1], round(H_KNEEL + SNAP, 4)]

    s0 = shots["0"]
    s0["cues"].insert(1, {"do": "hold", "slot": "wrist.r", "piece": "gourd_hung"})
    for c in s0["cues"]:
        if c.get("do") == "prop" and c.get("name") == "weapon":
            c["where"] = [round(grip[0], 3), grip[1], round(grip[2], 3)]
            c["rot"] = ROT

    s6 = shots["6"]
    s6["dur"] = 5.2
    s6["still"] = 3.6
    s6["note"] = ("Front three-quarter from her left, across the coals: she comes up off her elbow onto her knees and back "
                  "on her heels, and her hands come up before her, palms up; she looks down at them.")
    s6["cues"] = [
        {"do": "anim", "clip": "her/sit_back_heels", "from": 0, "speed": 1.0, "blend": 0},
        {"do": "face", "keys": {"brows_sad": 0.3, "mouth_open": 0.08}, "over": 1.2},
        {"do": "gaze", "look": [0, 0.8], "wander": 0.04},
        {"at": 3.3, "do": "lids", "value": 1, "over": 0.2},
        {"at": 3.65, "do": "lids", "value": None},
        {"at": 4.2, "do": "gaze", "look": [0, 0.75]},
    ]

    s6b = {
        "id": "6b", "type": "MCU", "dur": 4.4, "still": 4.2,
        "note": ("Front-left of her at her eyes' height, the coals under her: the hand comes back from the coals; she turns "
                 "the wrist up and looks at the cord wound on it and the full gourd; across at the bedroll, dry (N1); then "
                 "from inside her top the letter, folded, and both hands open it. She looks."),
        "cam": {"pos": {"actor": "her", "bone": "eyes", "off": CAM6B}, "at": {"actor": "her", "bone": "chest", "off": [0, 0.14, 0], "track": True},
                "lens": 50, "focus": {"actor": "her", "bone": "eyes", "track": True}, "fstop": 2.8},
        "cues": [
            {"do": "anim", "clip": "her/letter", "from": 0, "speed": 1.0, "blend": 0.35},
            {"do": "gaze", "look": [0, 0.85], "wander": 0.03},
            {"at": 0.6, "do": "sfx", "name": "cloth_water", "gain": 0.3},
            {"at": 1.35, "do": "gaze", "look": [0.55, 0.3]},
            {"at": 1.4, "do": "line", "id": "cin_drowned_fire.bedroll"},
            {"at": 2.7, "do": "gaze", "look": [0, 0.6]},
            {"at": 3.05, "do": "hold", "slot": "letter", "piece": "letter"},
            {"at": 3.3, "do": "gaze", "look": [0, 0.75]},
            {"at": 3.8, "do": "hold", "slot": "letter", "piece": "letter_open"},
            {"at": 3.9, "do": "sfx", "name": "cloth", "gain": 0.25},
            {"at": 4.0, "do": "face", "keys": {"brows_sad": 0.42, "mouth_open": 0.1}, "over": 0.5},
        ],
    }
    s6c = {
        "id": "6c", "type": "INSERT", "dur": 2.0, "still": 0.8,
        "note": ("Over her right shoulder, down onto the open letter: wet through, the ink run to blue water down the lines it "
                 "was, no word left. The coals' light comes up through the paper. She folds it."),
        "cam": {"pos": {"actor": "her", "bone": "head", "off": CAM6C}, "at": {"actor": "her", "bone": "hand_l", "off": MID6C},
                "lens": 50, "focus": {"actor": "her", "bone": "hand_l"}, "fstop": 2.8},
        "cues": [
            {"at": 1.5, "do": "hold", "slot": "letter", "piece": "letter"},
        ],
    }
    i = [s["id"] for s in f["shots"]].index("6a")
    f["shots"][i + 1:i + 1] = [s6b, s6c]

    s7 = shots["7"]
    s7["cues"].insert(1, {"at": 0.15, "do": "hold", "slot": "letter", "piece": None})

    s9 = shots["9"]
    s9["cam"]["at"] = [-10.4, 0.7, 91.6]

    s10 = shots["10"]
    s10["note"] = ("From the fire's side: her head snaps round to the sound and she is up off her heels in one movement, "
                   "without her hands, square to it: it is behind the camera, a little to its side.")
    s10["cues"] = [
        {"do": "world", "rate": 0},
        {"do": "anim", "clip": "her/kneel_to_stand_snap", "from": 0, "speed": 1, "blend": 0.15},
        {"at": 0.1, "do": "head", "amount": 0, "over": 0.15},
        {"at": 0.12, "do": "gaze", "look": [0.45, -0.05], "wander": 0.02},
        {"at": 0.12, "do": "face", "keys": {"eyes_wide": 0.6, "brows_sad": 0, "brows_angry": 0.2, "mouth_open": 0.1}, "over": 0.2},
        {"at": 0.35, "do": "gaze", "look": [0.05, 0.0], "wander": 0.02},
    ]

    s11 = shots["11"]
    s11["note"] = ("Side-on and wide enough for all of her, at the log: she steps in and takes her weapon off it, and comes "
                   "round with it 110 degrees onto the road, low and ready. On three sides the frost breaks. The arcanist "
                   "stands where she rose and cups her hands: nothing; then they fill.")
    keep = [c for c in s11["cues"] if c.get("do") in ("sfx", "world", "spawn") or (c.get("do") == "face" and "when" not in c)]
    s11["cues"] = [
        {"do": "place", "mark": "reach", "when": WEAPONS},
        {"do": "anim", "clip": "her/take_from_log", "from": 0, "speed": 1, "blend": 0, "when": WEAPONS},
        {"at": 0.6, "do": "prop", "name": "weapon", "remove": True, "when": WEAPONS},
        {"at": 0.6, "do": "prop", "name": "shield", "remove": True},
        {"at": 0.6, "do": "hold", "slot": "all", "piece": "@own", "when": WEAPONS},
        {"do": "anim", "clip": "her/cup_hands", "from": 0, "speed": 1, "blend": 0.25, "when": ARC},
        {"at": 1.4, "do": "face", "keys": {"smile": 0.15}, "over": 0.15, "when": ARC},
        {"at": 1.9, "do": "face", "keys": {"smile": 0, "brows_angry": 0.3}, "over": 0.2, "when": ARC},
    ] + keep

    s12 = shots["12"]
    s12["cues"] = [
        {"at": 0.0, "do": "place", "mark": "took", "when": WEAPONS},
        {"at": 0.0, "do": "place", "mark": "stood", "when": ARC},
        # The arcanist's staff was left on the log: her own body has it from the cut.
        {"at": 0.0, "do": "prop", "name": "weapon", "remove": True, "when": ARC},
        {"at": 0.0, "do": "play"},
    ] + [c for c in s12["cues"] if c.get("do") != "play"]
