"""Her signature idles: a captured way of standing (100STYLE, CC BY 4.0) for
each calling's body, the arms re-solved to hold what that calling holds,
its way. The capture brings the weight shifts and the breath; the arms
ride the chest as it moves.

- Warden: Heavyset (tensed, square, settled). The shield at rest at her
  left side, its face turned a little to the front, off her body; the
  sword low at her right, point toward the ground ahead.
- Arcanist: Strutting (chin up, a little back, at ease). The staff upright
  at her side, the free hand on her hip.
- Reaver: Angry (tense, restless). The axe on her shoulder, its head
  behind her, the left hand a fist.
- Stalker: Crouched (low, ready). The crossbow low across her, the left
  hand under its stock.
"""
from __future__ import annotations

import math
import os

import numpy as np

from clips.mocap import idle_loop
from gait import arc_of
from rig import Clip
from clips import town_idle


def layered(name, rig, base: Clip, over, meta=None) -> Clip:
    """A clip with every frame of `base` under the controls `over(t, frame)`
    gives (hands, fingers, any extra turns)."""
    from keyed import solve_frames
    n = base.frames
    rot, pos = solve_frames(rig, [over(f / max(n - 1, 1), f) for f in range(n)], [(base.rot[f], base.pos[f]) for f in range(n)],
                            loop=base.loop, weapon=(meta or {}).get("weapon", ""), slide=float((meta or {}).get("grip_slide", 0.0)),
                            tilt=float((meta or {}).get("grip_tilt", 0.0)),
                            slide_l=float((meta or {}).get("grip_slide_l", 0.0)))
    m = dict(base.meta)
    m.update(meta or {})
    return Clip(name, base.fps, rot, pos, loop=base.loop, meta=m)


def _n(v):
    v = np.array(v, float)
    return tuple(v / np.linalg.norm(v))


# Her sword hand at rest (chest frame), shared with the stops (sprint_stop.py).
WARDEN_HAND_R = (-0.09, -0.45, 0.04)


def warden(t, f):
    breath = 0.008 * math.sin(2 * math.pi * t * 2)
    return {
        # The shield at rest at her left side, off her body: the elbow out
        # about 19 degrees, the upper arm back about 14 and bent about 58, the
        # forearm forward and about 50 degrees down, turned in about 10, so
        # the shield's face (the back of the forearm) looks out to her
        # left-front about 15 degrees, its plane near upright. The shield is
        # strapped low on the forearm, its boss over her wrist, so its top rim
        # sits about 145 cm up, level with her armpit and the top of her cup,
        # with air under the shoulder armour, and its bottom is 8 cm or more
        # clear of her hip and thigh. The wrist straight, the fist on the
        # strap; the forearm turned palm-up a little (the whole roll in the
        # forearm, which carries the shield), not wrung at the wrist.
        # (Carried across her body, the 66 cm shield sank 5 cm into her
        # breast and trunk.) The upper arm turned 8 degrees out about its
        # length (judges 46-47): the rim clear of her cup's outline from the
        # front by 2-5 cm. In the game the forearm bone keeps to its hinge
        # (HerJoints hands its roll to the hand), so the shield on it does not
        # take the forearm's roll: measure with the helpers driven.
        "hand_l": {"arc": arc_of((0.0817, -0.3796 + breath, 0.1299)), "pole": (0.3281, -0.4168, -0.8477), "frame": "chest",
                   "thumb": (-0.1498, 0.7455, 0.6495), "twist": 1.0},
        # The sword low at her right, its point 34 degrees below the chest's
        # level ahead and a little out: the hand near in line with the
        # forearm, its thumb forward, the turn shared by the forearm and the
        # wrist. The elbow swung 25 degrees out and forward about the
        # shoulder-wrist line (pole), so the forearm comes down over the
        # hilt: wrist flex -12, toward the little finger 19 (animation
        # 31: with the elbow back and the point 39 down the wrist sat 32 toward
        # the little finger, "a very weird angle at the wrists"; the swing alone
        # gets no lower than 23). (Keyed by the blade alone, the wrist cocked
        # back 42 degrees and 34 to the side.)
        "hand_r": {"arc": arc_of(WARDEN_HAND_R), "pole": (-0.744, 0.09, -0.662), "frame": "chest",
                   "blade": _n((-0.142, -0.560, 0.816)), "knuckles": _n((0.123, -0.828, -0.548)), "twist": 0.5},
        # The left thumb closed round the grip, swung in across the palm
        # (judge 47: held straight, it showed between the rim and her skirt).
        "fingers_l": {"curl": 0.95, "cascade": 0.05, "thumb": 1.6, "oppose": 0.9}, "fingers_r": "grip",
    }


# Her free hand on her hip (15 Oct, animation 30; judge l30-r1 chose it over the hand on the thigh: "a confident witch
# silhouette", the thigh hand read limp at the game camera). The palm on the front-side of her hip above the hip bone,
# fingers forward and down over it, the fan closed (index-middle 0.5 mm, ring-little 2.5), the thumb forward along the
# forefinger (r2: not a straight peg out of the glove: base 15, end 22, 22 deg off the index); elbow out ~107, back
# ~95. Wrist flex -13..-14, dev -2..+5. Every part 1.1-2.5 mm off what it lies on (the leotard's outer face, ~7-9 mm
# off her skin there; the trim; the little finger on bare skin past the leg opening). Kept on her pelvis as she sways
# (idle_arcanist, below): the wrist (character space at rest) and the hand's way in the pelvis's frame.
ARC_HIP = {"pos": (0.17502, 1.18299, 0.03956), "knuckles": (-0.3373, -0.70768, 0.62077), "blade": (-0.23811, 0.70218, 0.671)}
ARC_HIP_FINGERS = {"thumb": 0.1, "oppose": 0.05, "thumb_in": 15.4, "thumb_roll": -23.6,
                   "bends": {"index": [25.268, 25.268, 12.629], "middle": [23.594, 23.594, 11.792],
                             "ring": [23.795, 23.795, 11.892], "pinky": [17.923, 24.487, 11.913], "thumb": [0.5, 15.2, 22.1]},
                   "spreads": {"index": -13.35, "middle": 0.0, "ring": 8.3, "pinky": 13.4}}


def _arc_hand_fingers():
    from keyed import FINGER_PRESETS
    return dict(FINGER_PRESETS["relaxed"], **ARC_HIP_FINGERS)


# Her staff hand at rest (the shoulder to the wrist, and the staff's line, in her character's frame), shared with the
# breaks and the stops (soul.py, sprint_stop.py), and the elbow's pole. Animation 47: candidates for the max judge,
# picked by ARC_CAND (env "ARC_CAND"; every clip that takes the idle's arm follows it). Each: "arc" (shoulder to
# wrist, metres), "blade" (the staff's aim), "pole", "slide" (keyed.build's "grip_slide", metres: her fist that much
# lower on the shaft, the staff where the aim puts it), "stop_blade" (the stops' aim, sprint_stop.py).
# R1: animation 46's (PASSED at 45/90/play; FAILED close-up 0/315/135: the forearm level and swung 35-37 deg out
#   from her front, the fist 36 cm out of the hip joint at waist height, "a shelf", "handing the staff to someone").
# (On her fist fit the staff leaves the fist 64 deg off the forearm's line, so with the staff upright the forearm
# can't drop below level without the wrist at its radial limit (22) and the staff tipping; the slide costs the same.
# Scratch anim/a47/slide, s0*.txt, and a47/cand, ev.py.)
ARC_CANDS = {
    "R1": {"arc": (-0.24, -0.26, 0.28), "blade": (-0.38, 1.0, -0.03), "pole": (0.0, -1.0, -0.2), "slide": 0.0,
           "stop_blade": (-0.30, 1.0, -0.07)},
    # A: toward the town arm. The fist 11 cm in toward her hip and 5 cm forward, so the forearm points ahead from the
    #   elbow (13-16 deg out of her forward, not 34-37), the elbow by her side (14 deg out, 21 forward). The face at
    #   facing 45 sets the staff: with the fist in and forward the crescent comes onto the line from that camera to her
    #   face (at R1's 10 deg forward it covered 50-95 % of it, close-up pitch 15) unless the staff stands upright
    #   forward (2) and leans further out (28). Lower can't be: the wrist is at 21.9 of its 22 radial.
    "A": {"arc": (-0.13, -0.24, 0.33), "blade": (-0.72, 1.0, -0.17), "pole": (-0.15, -1.0, -0.2), "slide": 0.0,
          "stop_blade": (-0.60, 1.0, -0.18)},
    # C: halfway (the forearm 23-26 deg out, the fist 5 cm in), the staff nearer R1's lean (21 out, 3 forward).
    "C": {"arc": (-0.19, -0.24, 0.30), "blade": (-0.52, 1.0, -0.15), "pole": (-0.15, -1.0, -0.2), "slide": 0.0,
          "stop_blade": (-0.45, 1.0, -0.18)},
    # R3 (round 3, the default): the forearm PITCHED down, not swung (the judge: R1/A/C's level forearm read as a shelf
    #   at 315/135). The fist rolled 14 deg about the shaft ("knuckles"), so the wrist takes the staff's 64 deg off the
    #   forearm in 13-20 palmar as well as 21 radial: the forearm 8-13.5 deg below level (R1 4-10), the elbow 117
    #   inner (122), the upper arm 13 out of her side (18.5), the fist 4 cm lower and 3 cm nearer her hip, the staff on
    #   R1's line (7 fwd, 16 out). No lower can be (scratch anim/a47/r3, opt*.py): leaning the staff further out (the
    #   judge's 21) to let the forearm sink swings its foot to her right knee (10-80 mm), and keeping the foot off
    #   (>= 95 mm) leaves the fist where it is; the town hold on this stand is level (0.6-6).
    "R3": {"arc": (-0.214, -0.291, 0.254), "blade": (-0.397, 1.0, -0.057), "pole": (0.0, -1.0, -0.2), "slide": 0.0,
           "knuckles": (-0.2495, -0.0439, 0.9674), "stop_blade": (-0.317, 1.0, -0.097)},
}
# T1 (animation 48, restage round 2, the default on a restaged stand): the staff TILTED in her fist ("tilt", degrees: the
#   clip's "grip_tilt", keyed.grip_of / WRAP_TILT, the game's OwnClips.GripTilt), so the forearm slopes down to the fist
#   with the staff upright and the wrist easy (round 1's max judge: at 315/135 R1's arm on the restaged stand still read
#   as "a level white bar at waist height"; the wall was the fist fit's 64 deg, scratch anim/st/c).
#   Found by search on the stand's frame 0 (scratch anim/st/c opt.py, opt_run.py), checked over the loop (heldt.py): the
#   forearm 27-31 deg below level (S2H1/R1 9-12), the upper arm 11-14 deg off straight down (21-24), the fist 21 cm out
#   past her hip's side (26.5) and 3.6 cm lower on the shaft, the wrist 12-14 toward the thumb (radial limit 22).
ARC_CANDS["T1"] = {"arc": (-0.205, -0.318, 0.251), "blade": (-0.44, 1.0, -0.13), "pole": (0.285, -1.0, -0.052), "slide": 0.036,
                   "tilt": 20.0, "stop_blade": (-0.36, 1.0, -0.17),
                   # (The stops' own aim per side, animation 48: with the tilt the one aim above put the right stop's crescent
                   # over her face from her right (cover 0.82) and its foot 30 mm from her leg; scratch anim/st/stops.)
                   "stop_blade_l": (-0.30, 1.0, -0.11), "stop_blade_r": (-0.30, 1.0, 0.0)}
# (Unset: T1 on a restaged stand, R1 with R1's stand: ARC_ST=R1 alone builds R1 as it was; ARC_ST=S2H1 ARC_CAND=R1 round 1.)
ARC_CAND = os.environ.get("ARC_CAND", "R1" if os.environ.get("ARC_ST", "S2H2") in ("R1", "") else "T1")
_ARC = ARC_CANDS[ARC_CAND]
ARC_HAND_R = _ARC["arc"]
ARC_BLADE_R = _ARC["blade"]
ARC_POLE_R = _ARC["pole"]
ARC_GRIP_SLIDE = _ARC["slide"]
ARC_GRIP_TILT = _ARC.get("tilt", 0.0)
ARC_KNUCKLES_R = _ARC.get("knuckles")   # (R3: the fist rolled about the shaft; None: the least turn from the forearm)


def arcanist(t, f):
    if ARC_ST:
        return _arc_free_arms(t)
    return {
        # (ARC_HIP at the captured standing's first frame, in the chest's frame, for the clips that take the idle's
        # arms as they are: its breaks, the stops, the Flare's settle.)
        "hand_l": {"arc": arc_of((-0.0251, -0.3226, 0.1052)), "pole": (1.0, 0.032, -1.243), "frame": "chest",
                   "knuckles": _n((-0.3849, -0.4502, 0.8057)), "blade": _n((-0.1819, 0.8929, 0.4120)), "twist": 0.3},
        # The staff upright at her side, its head leaning in a little and its foot out past her right leg
        # (13 Oct: on the seated bound staff, blade (-0.12, 1.0, 0.18) crossed its lower half behind her right
        # thigh and calf every frame; now >= 10 mm off her legs and her hat).
        # (18 Oct, animation 38: the grip 7 cm forward and the elbow's pole turned down and in, from (0.12 forward,
        # pole (-0.8, -0.3, -0.6)): at the close-up the elbow stood cocked out and back; now 20 deg out of her
        # side, not 32 (the hip arm's 26), 85 mm out from the shoulder, not 132, and 15 deg back, not 35.)
        # (20 Oct, animation 46: re-aimed as staff_town was. On the chest's frame at 12-16 deg forward and -4..+1 out,
        # the crescent sat 9-30 mm inside her hat's brim and covered her whole face at the close-up from facing 45.
        # Now on her character's frame (the line steady as the chest sways), 10 deg forward and 16-17 out, the fist
        # 8 cm further out and 9 cm forward, held ready ahead of her hip, the elbow bent 58, not 87; the crescent
        # 197-232 mm outside the brim, the shaft 104 mm or more off her legs, the wrist 20 deg toward the thumb, not 22.
        # Further out swings the shaft's foot into her right thigh (at 15 deg out with the fist 3 cm nearer, 63 mm).)
        "hand_r": _arc_hand_r(),
        "fingers_l": _arc_hand_fingers(), "fingers_r": "grip",
    }


def arc_grip():
    """The meta every clip that holds the idle's hold carries: its grip slide and tilt (keyed.build; the game eases
    the staff between clips by them, OwnClips.GripSlide / GripTilt). Empty for R1's."""
    return {k: v for k, v in (("grip_slide", ARC_GRIP_SLIDE), ("grip_tilt", ARC_GRIP_TILT)) if v}


def _arc_hand_r():
    return dict({"arc": arc_of(ARC_HAND_R), "pole": ARC_POLE_R, "frame": "char",
                 "blade": _n(ARC_BLADE_R), "twist": 0.5}, **({"knuckles": _n(ARC_KNUCKLES_R)} if ARC_KNUCKLES_R else {}))


def _arc_free_arms(t):
    """arcanist()'s arms on a restaged stand (ARC_ST): the left hand free (ARC_FREE), as it is at the captured
    standing's first frame in the chest's frame (_free0, filled by base_of; every caller takes the base first), its
    fingers as the idle's at phase t. (The clips keyed from these arms, the break, the show, the stops, the Flare,
    start and end on the idle's free hand; hip_layer then keeps it on each clip's own pelvis.)"""
    a = {"hand_r": _arc_hand_r(), "fingers_l": _free_fingers(ARC_STS[ARC_ST]["hand"], t), "fingers_r": "grip"}
    if ARC_ST not in _free0:
        raise RuntimeError("idle.arcanist(): base_of(rig, 'arcanist') must run first on a restaged stand (ARC_ST)")
    a["hand_l"] = dict(_free0[ARC_ST])
    return a


_free0 = {}
_arc_aims = {}


def arc_aim(rig):
    """The idle's right hand at its first frame (her character's frame): the grip's blade and knuckles as
    keyed._whole_aims fills them for a key that aims it by the blade alone (the blade as keyed), and the staff's line in it (the shaft
    through the fitted fist, data/arms_local.json mage_staff@hand_r, as scratch held.py reads it). For the break's
    staff turning about its own line (soul.arcanist_break). R1 keeps animation 46's numbers as they were."""
    if ARC_CAND == "R1" and not ARC_ST:
        return (-0.3547, 0.9342, -0.0275), (-0.4739, -0.1537, 0.8666), (-0.275, 0.936, 0.163)
    key = (ARC_CAND, ARC_ST)
    if key not in _arc_aims:
        import json
        from keyed import grip_of, wrap_of
        from rig import DATA, qaxis, qmul, qrot
        base = base_of(rig, "arcanist")
        grip, wrap = rig.grip, rig.wrap
        rig.grip, rig.wrap = grip_of("staff", ARC_GRIP_TILT), wrap_of("staff", ARC_GRIP_TILT)
        rig.swivel_force = {}
        layer = _free_hand(rig, base, arcanist, ARC_STS[ARC_ST]["hand"]) if ARC_ST else _on_hip(rig, base, arcanist)
        local, pos = rig.solve(layer(0, 0), base=(base.rot[0], base.pos[0]))
        rig.swivel_force = None
        g, _ = rig.globals(local, pos)
        hq = g[0, rig.I["hand_r"]]
        q = qmul(hq, qaxis([1.0, 0, 0], -rig.grip.get("r", 0.0)))
        rig.grip, rig.wrap = grip, wrap
        v = np.array(json.loads((DATA / "arms_local.json").read_text())["mage_staff@hand_r"]["v"], float)
        c0 = v.mean(0)
        d0 = np.linalg.svd(v - c0, full_matrices=False)[2][0]
        t0 = v @ d0
        thin = v[(t0 > -0.7) & (t0 < 0.25)]
        d = np.linalg.svd(thin - thin.mean(0), full_matrices=False)[2][0]
        if d @ d0 < 0:
            d = -d
        if ARC_GRIP_TILT:   # (the staff turned in her fist by the clip's grip_tilt, about hand_r +X)
            d = qrot(qaxis([1.0, 0, 0], ARC_GRIP_TILT), d)
        line = qrot(hq, d)
        if line[1] < 0:
            line = -line
        # (The blade as the idle keys it, as R1's was: the solved one differs by the wrist's clamp, ~1.5 deg.)
        _arc_aims[key] = (_n(ARC_BLADE_R), _n(ARC_KNUCKLES_R) if ARC_KNUCKLES_R else tuple(float(x) for x in qrot(q, [0, 1.0, 0])),
                               tuple(float(x) for x in line))
    return _arc_aims[key]


def _on_hip(rig, base, arms):
    """`arms` with the left hand kept on her pelvis (ARC_HIP) frame by frame, in the chest's frame the solver reads."""
    from rig import qmul, qinv, qrot
    I = rig.I
    grest, prest = (a[0] for a in rig.sk.rest_globals())
    pel, s3, ua = I["pelvis"], I["spine_03"], I["upperarm_l"]
    g, p = rig.sk.fk(base.rot, base.pos)

    def over(t, f):
        d = dict(arms(t, f))
        dp = qmul(g[f, pel], qinv(grest[pel]))
        ic = qinv(qmul(g[f, s3], qinv(grest[s3])))
        W = p[f, pel] + qrot(dp, np.array(ARC_HIP["pos"]) - prest[pel])
        d["hand_l"] = dict(d["hand_l"], arc=arc_of(qrot(ic, W - p[f, ua])),
                           knuckles=tuple(qrot(ic, qrot(dp, np.array(ARC_HIP["knuckles"])))),
                           blade=tuple(qrot(ic, qrot(dp, np.array(ARC_HIP["blade"])))))
        return d
    return over



# Animation 48 (solver st): the combat idle restaged, its staff hold kept (judge rounds 1-3: at the close-up from 0/315/135
# R1's forearm read as "a shelf", but staff_town's near-same arm passed 10/10 at every facing on a calmer stand with the
# left arm free, so the read is the stance and the free hand). ARC_ST (env) picks the candidate: "" keeps R1 (Strutting,
# the left hand on her hip). S1: the Strutting take stood (feet set, knees soft, the chest brought over her feet, the
# chin down from its 21 deg up); S2: the HandsInPockets take stood (the calmest 100STYLE ID take with a breath and soft
# knees). H1 "spell ready": the left hand ahead of her hip, palm down and in, fingers loose; H2 "low and charged": the
# arm down, the hand out from her thigh, fingers open.
# "stand": stand()'s arguments; "head": her head's mean pitch wanted (deg, + chin down; Neutral +2, WiggleHips +5).
# (Round 2, the max judge: H2 ships, its elbow 13 deg softer and H1's slow finger curl; H1 stays selectable.)
ARC_ST = os.environ.get("ARC_ST", "S2H2")
ARC_ST = "" if ARC_ST == "R1" else ARC_ST
_S1 = {"style": "Strutting", "stand": {"knee": 16.0, "over": 0.0, "pitch": -6.0, "width": 0.29, "stagger": 0.03}, "head": -2.0,
       "free_pos": {"H1": (0.275, 1.135, 0.15)}}
_S2 = {"style": "HandsInPockets", "stand": {"knee": 15.0, "over": 0.0, "pitch": 2.0, "width": 0.29, "stagger": 0.05, "drop": 0.06},
       "head": 3.0, "free_pos": {"H1": (0.27, 1.14, 0.16)}}
ARC_STS = {"S1H1": dict(_S1, hand="H1"), "S2H1": dict(_S2, hand="H1"), "S1H2": dict(_S1, hand="H2"), "S2H2": dict(_S2, hand="H2")}
# The free hand, kept on her pelvis as she sways (as ARC_HIP is): "pos" the wrist (character space at rest), the hand's
# way ("knuckles", "blade", or "thumb") in the pelvis's frame, the elbow's "pole" (chest frame).
ARC_FREE = {
    "H1": {"pos": (0.26, 1.16, 0.22), "knuckles": (-0.25, -0.6, 1.0), "blade": (-0.87, 0.5, 0.0), "pole": (0.35, -0.3, -1.0)},
    # (H2 rides her chest, as the town's free arms do: "arc" the wrist from the shoulder in the chest's frame, its
    # length 0.4925 for the elbow soft at 38 deg (round 1's 0.507 at 25: "10-15 deg softer", the max judge, round 2), the
    # hand as low, 1 cm further ahead; on the pelvis the arm went straight, 176.)
    "H2": {"arc": (0.12, -0.45, 0.16), "thumb": (0.15, -0.1, 1.0), "pole": (0.3, -0.2, -1.0)},
}


def _free_fingers(hand, t):
    """The free hand's fingers: loose between "relaxed" and "spread", softly curled, a slow life (one swell of the curl
    and one of the fan over the loop, out of phase with each other): H1's, and H2's since round 2 (the max judge: "H1's
    slow finger curl"); "H2r1" round 1's H2 (open, a little spread)."""
    from keyed import FINGER_PRESETS
    a, b = math.sin(2 * math.pi * t + 1.3), math.sin(2 * math.pi * t + 3.4)
    if hand in ("H1", "H2"):
        return dict(FINGER_PRESETS["relaxed"], curl=0.06 + 0.02 * a, thumb=0.2,
                    spreads={"index": -3.5 + 1.5 * b, "middle": 0.0, "ring": 4.0 - 1.0 * b, "pinky": 11.0 - 2.0 * b}, spread=3.0)
    return dict(FINGER_PRESETS["relaxed"], curl=0.04 + 0.015 * a, thumb=0.1,
                spreads={"index": -2.0 + 1.0 * b, "middle": 0.0, "ring": 3.0, "pinky": 8.0 - 1.5 * b}, spread=5.0)


def chest_pitch(rig, g, f):
    """Her chest's pitch at frame f of globals g (deg, + leaning forward), from its rest."""
    from rig import qmul, qinv, qrot
    s3 = rig.I["spine_03"]
    fw = qrot(qmul(g[f, s3], qinv(rig.sk.rest_globals()[0][0][s3])), [0.0, 0.0, 1.0])
    return math.degrees(math.atan2(-fw[1], fw[2]))


def pitched(arc, deg):
    """An arc (azimuth, elevation, reach) turned `deg` about her left-right axis (+ forward and down)."""
    az, el, r = arc
    a, e, t = (math.radians(x) for x in (az, el, deg))
    v = np.array([math.sin(a) * math.cos(e), math.sin(e), math.cos(a) * math.cos(e)]) * r
    c, s_ = math.cos(t), math.sin(t)
    return arc_of((v[0], v[1] * c - v[2] * s_, v[1] * s_ + v[2] * c))


def _free_spec(rig, hand, g, p, upright=None):
    """f -> the free hand's key (ARC_FREE[hand]) at frame f of a clip whose globals are (g, p): on its own pelvis
    (H1) or chest (H2), in the chest's frame the solver reads.
    `upright` (deg, the stand's chest pitch, or f, pitch -> deg): a chest-held hand (H2) turned against the clip's chest pitch away from
    it, so the arm hangs as in the idle while the trunk leans (the stops' thrown-back lean swung it out ahead of her
    and up, "thrown out", animation 49)."""
    from rig import qmul, qinv, qrot
    I = rig.I
    grest, prest = (a[0] for a in rig.sk.rest_globals())
    pel, s3, ua = I["pelvis"], I["spine_03"], I["upperarm_l"]
    H = dict(ARC_FREE[hand])
    # (Each stand carries her pelvis to its own place: the wrist as measured onto the hip's front, scratch anim/st lh.py.)
    if ARC_ST and hand in ARC_STS[ARC_ST].get("free_pos", {}):
        H["pos"] = ARC_STS[ARC_ST]["free_pos"][hand]

    def spec(f):
        dp = qmul(g[f, pel], qinv(grest[pel]))
        ic = qinv(qmul(g[f, s3], qinv(grest[s3])))
        if "arc" in H:
            way = _n
            arc = arc_of(H["arc"])
            if upright is not None:
                P = chest_pitch(rig, g, f)
                arc = pitched(arc, (upright(f, P) if callable(upright) else upright) - P)
            h = {"arc": arc, "pole": H["pole"], "frame": "chest", "twist": 1.0}
        else:
            W = p[f, pel] + qrot(dp, np.array(H["pos"]) - prest[pel])
            way = lambda v: tuple(qrot(ic, qrot(dp, np.array(_n(v)))))
            h = {"arc": arc_of(qrot(ic, W - p[f, ua])), "pole": H["pole"], "frame": "chest", "twist": 1.0}
        h.update({k: way(H[k]) for k in ("knuckles", "blade", "thumb") if k in H})
        return h
    return spec


def _free_hand(rig, base, arms, hand):
    """`arms` with the left hand held free (ARC_FREE[hand]) on her pelvis frame by frame, in the chest's frame."""
    spec = _free_spec(rig, hand, *rig.sk.fk(base.rot, base.pos))

    def over(t, f):
        d = dict(arms(t, f))
        d["hand_l"] = spec(f)
        d["fingers_l"] = _free_fingers(hand, t)
        return d
    return over


def pitch_head(rig, clip: Clip, want) -> Clip:
    """Her head's mean pitch (deg, + chin down) brought to `want`, half of the turn at the neck and half at the head,
    the take's nod about it kept."""
    from rig import qinv, qmul, qrot
    sk = rig.sk
    grest = sk.rest_globals()[0][0]
    rot = clip.rot.copy()
    for jn, share in (("neck_01", 0.5), ("Head", 1.0)):
        g, _ = sk.fk(rot, clip.pos)
        h = sk.i("Head")
        fw = np.array([qrot(qmul(g[f, h], qinv(grest[h])), [0, 0, 1.0]) for f in range(clip.frames)])
        pitch = float(np.degrees(np.mean(np.arcsin(np.clip(-fw[:, 1], -1, 1)))))
        turn = qaxis_((1.0, 0.0, 0.0), share * (want - pitch))
        j = sk.i(jn)
        par = sk.parent[j]
        for f in range(clip.frames):
            rot[f, j] = qmul(qinv(g[f, par]), qmul(turn, g[f, j]))
    return Clip(clip.name, clip.fps, rot, clip.pos, loop=clip.loop,
                meta={**clip.meta, "changes": clip.meta.get("changes", "") + f"; head's mean pitch brought to {want:+.0f} deg"})

def hip_layer(rig, clip, w, curl=None, thumb_pow=1.0, phase=None, upright=None):
    """`clip` with her left hand laid on her hip (ARC_HIP, idle_arcanist's) where the weight w(frame) > 0, kept on
    the clip's OWN pelvis frame by frame, and the left arm and fingers slerped by w from the clip's own into it.
    For the clips that took the idle's frame-0 hand in the chest's frame (the breaks, the stops, the Flare's settle,
    the flourish): there the hand floated 3-17 mm off her hip, or sank into it, as her hips moved under the chest.
    `curl` ({finger: [deg per frame]}): each finger closed that much more (0.6 at the knuckle, 0.4 at the middle
    joint; opened at the knuckle alone) where the clip's legs move the surface under it (the stops; following the thigh instead sank the thumb).
    `thumb_pow`: the left thumb's joints slerped by w**thumb_pow instead of w, so the thumb takes the clip's own shape
    before the hand leaves her hip (the Flare's reach: at w 0.25, f4, her glove's thumb sleeve folded 1.3 mm into
    her hand's thenar).
    On a restaged stand (ARC_ST, animation 48) the hand it lays is the idle's FREE hand (ARC_FREE, _free_spec) on the
    clip's own pelvis, blended in and out by the same w, its fingers the idle's (_free_fingers) at `phase`(frame)
    (default 0, the idle's first frame); `curl` (a hand on her hip's contact) does not apply; `upright` (_free_spec):
    the free hand held against the clip's chest pitch away from the stand's."""
    from keyed import solve_frames
    from rig import qmul, qinv, qrot, qslerp
    I = rig.I
    grest, prest = (a[0] for a in rig.sk.rest_globals())
    pel, s3, ua = I["pelvis"], I["spine_03"], I["upperarm_l"]
    g, p = rig.sk.fk(clip.rot, clip.pos)
    n = clip.frames
    ws = [min(1.0, max(0.0, float(w(f)))) for f in range(n)]
    thumb = {I[f"thumb_0{q}_l"] for q in (1, 2, 3)}
    arm = [ua]
    for j in arm:
        arm += [k for k, q in enumerate(rig.sk.parent) if q == j and k not in arm]
    hand0 = arcanist(0, 0)["hand_l"]
    free = _free_spec(rig, ARC_STS[ARC_ST]["hand"], g, p, upright=upright) if ARC_ST else None

    def fingers(f):
        fx = _arc_hand_fingers()
        if curl:
            b = {k: list(v) for k, v in fx["bends"].items()}
            for k, c in curl.items():
                d = c[min(f, len(c) - 1)]
                # (Opened, all at the knuckle: the finger lifts off from its base; opening the middle joint too
                # took the little finger's middle bone into her thigh.)
                b[k][0] += 0.6 * d if d > 0 else d
                b[k][1] += 0.4 * d if d > 0 else 0.0
            fx = dict(fx, bends=b)
        return fx

    def spec(f):
        if ARC_ST:
            hand = ARC_STS[ARC_ST]["hand"]
            return {"hand_l": free(f), "fingers_l": _free_fingers(hand, phase(f) if phase else 0.0)}
        dp = qmul(g[f, pel], qinv(grest[pel]))
        ic = qinv(qmul(g[f, s3], qinv(grest[s3])))
        W = p[f, pel] + qrot(dp, np.array(ARC_HIP["pos"]) - prest[pel])
        return {"hand_l": dict(hand0, arc=arc_of(qrot(ic, W - p[f, ua])),
                               knuckles=tuple(qrot(ic, qrot(dp, np.array(ARC_HIP["knuckles"])))),
                               blade=tuple(qrot(ic, qrot(dp, np.array(ARC_HIP["blade"]))))),
                "fingers_l": fingers(f)}
    # Each run of weighted frames solved on its own (the solver settles the elbow over the frames it is given).
    f = 0
    while f < n:
        if ws[f] <= 0:
            f += 1
            continue
        e = f
        while e < n and ws[e] > 0:
            e += 1
        idx = list(range(f, e))
        rot, _ = solve_frames(rig, [spec(k) for k in idx], [(clip.rot[k], clip.pos[k]) for k in idx],
                              weapon=(clip.meta or {}).get("weapon", ""))
        for i, k in enumerate(idx):
            for j in arm:
                clip.rot[k, j] = qslerp(clip.rot[k, j], rot[i, j], ws[k] ** thumb_pow if j in thumb else ws[k])
        f = e
    return clip


def _smooth(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


# The reaver at ease in a fight (animation 55): each axe hangs low from an arm let down by her side, the elbow soft,
# the haft down and ahead and swung out past her thigh, its head before her knee, the wrist near straight. (Before: the
# axe held aloft on her shoulder, its haft across her face seen from her side; the second axe of a pair lay across her
# pelvis under a hand on her hip.) Not head-down and trailing: the axe leaves her fist on its thumb side (the socket's
# BladeDirR) about 90 deg off the forearm's line, so a plumb haft from a hanging forearm asks the wrist for ~90 deg
# of ulnar bend (it has 38): asked for plumb with the bit back (out 15, back 12-50) the solver pinned the wrist at its
# limits (ulnar 37-38, flex 20-37) and still left the haft plumb-forward with the bit forward. (Shoulder rest: the
# haft over her shoulder crosses her neck seen from her side, whatever the lie.) Scratch anim55/idlesA/rb.py.
# Each fist from its shoulder (chest frame, m; x toward her left), the elbow's pole (chest frame), and the haft: `out`
# deg out from plumb, `back` deg trailing behind it (- ahead), `edge` the bit turned that many deg out from straight
# back (with `knuckles`; off: the fist's roll left to the forearm, the bit forward and down).
# (Round 2, 27 Oct: the fist gripped at the very end of the haft read as holding the axe out, and the right and left
# were mirror images. Now: the fist AXE_GRIP up the haft (below); the haft ~65 deg below level (60 before, to ~24 deg from
# plumb) with the splay 16-17 -> ~8-9 deg, got by the target and the hand 2 cm lower (the wrist's strain 22-23 swing,
# 17 ulnar, below the 30 / 24 it had), not by asking the wrist; the elbow soft, 29-34 deg. `back` is the target's trail
# only: the wrist cannot reach what is asked for (45 asked, 24 got); it was 48 asked, 31 got.
# The left breaks the mirror: its arm hangs straighter (hand 1.4 cm lower, the shoulder ~6 deg back: the elbow ~15-22 deg),
# its haft ~8 deg nearer plumb (pitch -73) and its splay 4-5 deg wider (13 deg out), so the pair read as two angles and the
# head stays off her left foot.)
# (Animation 56, the max judge: at 330 the left haft hung near parallel to her left shin, its head on her moccasin's toe.
# Asked back -30 -> -19 (got: the wrist again delivers less than asked), the hand 8 mm higher and 5 mm forward: measured
# pitch -73.5 -> ~-78, splay 12-13, the head 7-8 cm further back (134-173 -> ~55-95 mm ahead of her toe), the elbow 19-25,
# >= 100 mm off her legs. The right stays at -65, so the two never read parallel.)
AXE_IDLE = {"hand": (0.085, -0.51, 0.05), "pole": (0.3, -0.2, -1.0), "out": 6.0, "back": -45.0, "edge": 0.0,
            "sway": 0.010, "knuckles": False}
AXE_IDLE_L = {"hand": (0.085, -0.516, 0.005), "out": 10.0, "back": -19.0}   # the left's own differences (mirrored otherwise)
# Her fist closed higher on the haft (animation 55, 27 Oct: gripped at the very end of a long haft the axe read as held out
# at arm's length): the fist `grip` m nearer the head, the end showing behind it. The clips carry it as a negative
# "grip_slide" (the right) and "grip_slide_l" (the left; keyed.solve_frames slide_l, OwnClips.GripSlideL), the game sliding
# the axe back through the fist by as much; the key's hand is laid that far back up the haft so the wrist stays where it
# hangs. The left's own `grip` may differ (AXE_IDLE_L).
AXE_GRIP = 0.13


def _axe_down(side, t, a):
    sg = 1.0 if side == "l" else -1.0
    h = np.array(a["hand"], float) * (sg, 1.0, 1.0)
    # A small hang to the breath, against the sway (the arm a pendulum, a beat behind).
    h = h + (0.0, 0.0, a["sway"] * math.sin(2 * math.pi * t * 2 - (0.6 if side == "l" else 0.0)))
    o, b, e = (math.radians(a[k]) for k in ("out", "back", "edge"))
    haft = np.array([sg * math.sin(o), -math.cos(b) * math.cos(o), -math.sin(b) * math.cos(o)])
    eb = np.array([sg * math.sin(e), math.sin(b), -math.cos(b)])
    eb = eb - haft * float(eb @ haft)
    pole = np.array(a["pole"], float) * (sg, 1.0, 1.0)
    # (A grip higher on the haft: the key's hand is where the piece's line passes `grip` m back toward the butt of the wrist
    # the clip wants; solve_frames' shift brings the wrist up the haft to the fist's place.)
    h = h - a.get("grip", AXE_GRIP) * np.array(_n(haft))
    spec = {"arc": arc_of(h), "pole": tuple(pole), "frame": a.get("frame", "char"), "blade": tuple(_n(haft)), "twist": 0.5}
    if a.get("knuckles", True):
        spec["knuckles"] = tuple(_n(eb))
    return spec


def axe_grip(both=False):
    """The meta of every clip that holds the hanging axe (idle_reaver, idle_reaver_axes, idle_reaver_break): the fist closed
    AXE_GRIP higher on the haft (a negative slide), the left's as well when `both`."""
    m = {"grip_slide": -AXE_IDLE.get("grip", AXE_GRIP)}
    if both:
        m["grip_slide_l"] = -{**AXE_IDLE, **AXE_IDLE_L}.get("grip", AXE_GRIP)
    return m


def reaver_shoulder(t, f):
    """The old reaver idle's arms (before Animation 55): the axe on her shoulder, its head behind her. reaver_show
    (soul.py) still opens and closes on them; the idle itself now hangs the axe (reaver below)."""
    return {
        "hand_r": {"arc": arc_of((-0.03, -0.13, 0.11)), "pole": (-0.6, -1.0, 0.0), "frame": "chest",
                   "blade": _n((-0.15, 0.35, -0.95)), "twist": 0.5},
        "hand_l": {"arc": arc_of((-0.02, -0.42, 0.06)), "pole": (0.4, 0.0, -1.0), "frame": "chest"},
        "fingers_r": "grip", "fingers_l": "fist",
    }


def reaver(t, f):
    """One axe (idle_reaver): it hangs from her right fist; the left hangs empty, loosely closed."""
    return {"hand_r": _axe_down("r", t, AXE_IDLE),
            "hand_l": {"arc": arc_of(np.add(AXE_IDLE["hand"], (0.0, 0.0, AXE_IDLE["sway"] * math.sin(2 * math.pi * t * 2 - 0.6)))),
                       "pole": (0.3, -0.2, -1.0), "frame": "chest", "thumb": _n((-0.15, -0.1, 1.0)), "twist": 1.0},
            "fingers_r": "grip", "fingers_l": "relaxed"}


def reaver_axes(t, f):
    """Two axes (idle_reaver_axes, on idle_reaver's standing): one hanging from each fist."""
    return {"hand_r": _axe_down("r", t, AXE_IDLE), "hand_l": _axe_down("l", t, {**AXE_IDLE, **AXE_IDLE_L}),
            "fingers_r": "grip", "fingers_l": "grip"}


# Her left hand laid over the crossbow's fore-stock, palm down, a hand ahead of the right fist, the fingers over its
# far side; the elbow bent and hanging by her side (animation 38, 18 Oct). Under the stock (as keyed before) the fore-
# stock sits 55 cm from her shoulder, past her reach with the stock carried this low: the arm went straight across her
# and the upper arm 60 mm into her side and breast. Shared by the crossbow's shot and the stops (which end here).
# The crossbow's carry moved as one (both hands, chest frame, m): ahead of her, so its butt clears her waist.
STALKER_SHIFT = (0.0, 0.0, 0.06)
STALKER_HAND_L = {"hand_l": {"arc": arc_of(np.add((-0.058, -0.335, 0.255), STALKER_SHIFT)), "pole": (0.0, -0.5, -1.0), "frame": "chest",
                             "knuckles": _n((-0.71, 0.33, 0.63)), "blade": _n((-0.49, 0.41, -0.77)), "twist": 0.4}}


STALKER_HAND_R = {"hand_r": {"arc": arc_of(np.add((0.12, -0.38, 0.20), STALKER_SHIFT)), "pole": (-0.7, -0.4, -0.5),
                             "frame": "chest", "knuckles": _n((0.5, -0.15, 0.85)), "twist": 0.5}}


def stalker(t, f):
    return {
        # The crossbow low across her, pointing ahead and to her left, the
        # left hand laid over its fore-stock.
        **STALKER_HAND_R, **STALKER_HAND_L,
        "fingers_r": "grip", "fingers_l": "relaxed",
    }


_STOCK = {}
STOCK_DROP = 0.003


def _stock_rel(rig):
    """Her left hand on the fore-stock as the idle lays it (stalker(), the base's first frame), in her right hand's
    frame: (wrist offset, turn). Made once per body."""
    from keyed import grip_of
    from rig import qinv, qmul, qrot
    key = id(rig)
    if key not in _STOCK:
        base = base_of(rig, "stalker")
        grip0 = rig.grip
        rig.grip = grip_of("crossbow") if rig.grips else {}
        rig.swivel_force = {}
        local, pos = rig.solve(stalker(0, 0), base=(base.rot[0], base.pos[0]))
        rig.swivel_force = None
        rig.grip = grip0
        g, p = rig.globals(local, pos)
        hr, hl, s3 = rig.I["hand_r"], rig.I["hand_l"], rig.I["spine_03"]
        # (Laid STOCK_DROP lower onto the stock, in the chest's frame: the idle's first frame has her palm 4-5 mm
        # over it, where the loop's breath lays it 1.5-4.5.)
        drop = qrot(qmul(g[0, s3], qinv(rig.grest[s3])), [0.0, -STOCK_DROP, 0.0])
        _STOCK[key] = (qrot(qinv(g[0, hr]), p[0, hl] + drop - p[0, hr]), qmul(qinv(g[0, hr]), g[0, hl]))
        # (And the crossbow's top there, in the chest's frame: a clip that keys the right hand's blade lands on it.)
        _STOCK[("top", key)] = tuple(float(x) for x in qrot(qinv(qmul(g[0, s3], qinv(rig.grest[s3]))), qrot(g[0, hr], [0, 0, 1.0])))
    return _STOCK[key]


def stalker_top(rig):
    """The crossbow's top (hand_r +Z) in her idle, in the chest's frame."""
    _stock_rel(rig)
    return _STOCK[("top", id(rig))]


# The fore-stock's centre line in hand_r's space (m): along +Y at this x, z (the stock 40 mm wide, its top at +z 0.09).
STOCK_AXIS = (-0.041, 0.045)


def cradle_rel(at, fingers=35.0, roll=0.0, lift=0.0, palm=0.020, reach=0.045):
    """A palm-up cradle under the fore-stock, in hand_r's space: (wrist offset, turn), as _stock_rel returns. at: the
    palm's centre (x, y, z; the stock's underside is z 0.00-0.02 from y 0.14 on); fingers: deg from the stock (+Y)
    toward its far side (+X); roll: deg the palm tips about the fingers toward her (-X, the heel of the hand down the
    near side); lift: deg the fingers rise toward the stock's top (+Z), up its far side. palm, reach: the palm's centre from the wrist's bone, out of the palm and along the fingers."""
    from rig import qfrom_basis
    a, r, l = math.radians(fingers), math.radians(roll), math.radians(lift)
    f = np.array([math.sin(a) * math.cos(l), math.cos(a) * math.cos(l), math.sin(l)])
    side = np.array([math.cos(a), -math.sin(a), 0.0])        # across the fingers, toward the far side
    up = np.cross(side, f)                                   # the palm's normal before the roll
    n = up * math.cos(r) - side * math.sin(r)                # the palm's normal (hand_l +X)
    z = np.cross(n, f)
    return (np.array(at, float) - reach * f - palm * n, qfrom_basis(n, f, z))


def blend_rel(a, b, t, via=None, out=0.0):
    """Between two of the left hand's relations to the stock: the wrist swung about the stock's centre line (round
    its near side, never through it), its turn slerped; via: a relation passed at t 0.5 (each half on its own), out:
    m the wrist stands off the stock at the middle (sin bump)."""
    from rig import qslerp
    if via is not None:
        p, q = (blend_rel(a, via, 2 * t) if t < 0.5 else blend_rel(via, b, 2 * t - 1))[:2]
        if out:
            c = np.array([STOCK_AXIS[0], p[1], STOCK_AXIS[1]])
            d = p - c
            p = p + d / max(1e-6, np.linalg.norm(d)) * out * math.sin(math.pi * t)
        return p, q
    (pa, qa), (pb, qb) = a[:2], b[:2]
    c = np.array([STOCK_AXIS[0], 0.0, STOCK_AXIS[1]])
    da, db = pa - c, pb - c
    ang = lambda d: math.atan2(d[2], d[0])
    ra, rb = math.hypot(da[0], da[2]), math.hypot(db[0], db[2])
    t1, t2 = ang(da), ang(db)
    t1 %= 2 * math.pi; t2 %= 2 * math.pi                     # (0 = +x far side, pi = the near side: no crossing 0)
    th = t1 + (t2 - t1) * t; rr = ra + (rb - ra) * t + out * math.sin(math.pi * t)
    p = c + np.array([rr * math.cos(th), da[1] + (db[1] - da[1]) * t, rr * math.sin(th)])
    return p, qslerp(qa, qb, t)


def ride_stock(rig, make, weight=lambda f: 1.0, rel=None):
    """A crossbow clip whose left hand rides the fore-stock wherever the crossbow goes (animation 38: keyed on its own
    arc from her shoulder, it parted from the stock or the stock swung through it as the two arms' arcs drifted apart:
    the crossbow 6-18 mm into her left hand in the shot, the show and the stops). make(post) builds the clip; the right
    hand's path is read from a first build and the left hand put where the idle lays it on the stock in the right
    hand's frame (weight(frame) 0..1: how far from its keyed place onto the stock)."""
    from rig import qinv, qmul, qrot
    idle_rel = _stock_rel(rig)
    c0 = make(None)
    g, p = rig.sk.fk(c0.rot, c0.pos)
    hr, s3 = rig.I["hand_r"], rig.I["spine_03"]
    tg = []
    for f in range(c0.frames):
        r = (rel(f, idle_rel) if rel else None) or idle_rel
        rel_p, rel_q = r[0], r[1]
        q = qmul(g[f, hr], rel_q)
        tg.append((p[f, hr] + qrot(g[f, hr], rel_p), qrot(q, [0, 0, 1.0]), qrot(q, [0, 1.0, 0]),
                   qmul(g[f, s3], qinv(rig.grest[s3])), r[2] if len(r) > 2 else 1.0, r[3] if len(r) > 3 else None))

    def post(fr, pose):
        w = float(weight(fr))
        if w <= 0 or not isinstance(pose.get("hand_l"), dict):
            return pose
        pos, bl, kn, chest, aim, fingers = tg[min(fr, len(tg) - 1)]
        spec = dict(pose["hand_l"])
        if spec.get("frame") == "chest":
            bl, kn = qrot(qinv(chest), bl), qrot(qinv(chest), kn)
        for k, v in (("blade", bl), ("knuckles", kn)):
            if w < 1 and k in spec:
                v = np.array(spec[k], float) * (1 - w) + v * w
            spec[k] = tuple(float(x) for x in v / np.linalg.norm(v))
        spec.pop("thumb", None)
        spec["pos"] = tuple(float(x) for x in pos)
        spec["mix"] = w if "arc" in spec else 1.0
        if aim < 1.0:
            spec["aim"] = aim     # (rel's third: how far the hand is turned to it, 0 = riding the forearm)
        if fingers is not None:
            return {**pose, "hand_l": spec, "fingers_l": fingers}   # (rel's fourth: the left fingers there)
        return {**pose, "hand_l": spec}
    return make(post)


def stalker_daggers(t, f):
    """The stalker's idle with a dagger in each hand (the game asks for idle_<calling>_<kind> first: OwnClips.For). Her
    crossbow idle let the left hang "relaxed" round the second dagger, an open hand with the blade stuck to it (judge,
    17 October); here both fists close on their hilts (the daggers' fitted WRAP, the left's mirrored: keyed.wrap_of)."""
    # Her own arms (animation 38: on the crossbow's, the right dagger lay 20 mm into her left hand): a relaxed ready
    # stance, both fists low ahead of her hips, a hand's width apart, the elbows soft by her sides, the wrists
    # straight and the forearms rolled so the blades rise forward and a little out (the left a little ahead, over
    # her leading foot).
    return {"hand_r": {"arc": arc_of(DAGGERS_HAND_R), "pole": (-0.7, -0.5, -0.4), "frame": "chest",
                       "thumb": _n((-0.25, 0.75, 0.6)), "twist": 0.5},
            "hand_l": {"arc": arc_of(DAGGERS_HAND_L), "pole": (0.7, -0.5, -0.4), "frame": "chest",
                       "thumb": _n((0.25, 0.75, 0.6)), "twist": 0.5},
            "fingers_r": "grip", "fingers_l": "grip"}


# The daggers' ready fists (chest frame, from each shoulder, m).
DAGGERS_HAND_R = (0.05, -0.34, 0.24)
DAGGERS_HAND_L = (-0.05, -0.33, 0.27)


# Animation 56 (idles B): the four idles' own arms, each over its calling's captured standing (IDLE_ARMS: the idle alone
# takes them; the clips keyed from the idle's arms, the stops, breaks, shows and the Flare, keep IDLES' own).
# The owner's bar: effortlessly badass, loose and confident, nothing held at a weird angle.

# The stalker's knives at ease (idle_stalker_daggers): each fist by her hip, a little ahead of it, the elbow soft, the blade
# down and ahead (below level from every side, never jutting at the camera); not mirrored, the left a little higher and
# further forward, its blade nearer level. Chest frame: the fist from its shoulder (x toward her left), the elbow's pole,
# the blade's way.
# (Animation 56: the blades' line 36-42 deg below level, the right splayed 25-29 deg out, the left 14-19; the elbows 26 and
# 34; 24-27 mm off her thighs, where the first tries, fists in at her groin's width, put both tips 23-62 mm into them.)
DAGGERS_IDLE = {"r": {"hand": (-0.06, -0.46, 0.22), "pole": (-0.5, 0.8, -1.0), "blade": (-0.315, -0.766, 0.563)},
                "l": {"hand": (0.06, -0.445, 0.24), "pole": (0.6, 1.8, -1.0), "blade": (0.31, -0.891, 0.332)}}
# (Animation 57 round 3: the left blade steepened by the ARM: its elbow lifted (pole y 1.8) so the forearm runs 82-86 deg
# below level, the hand 5 mm nearer straight (elbow 21), the blade 70-74 deg below level, 7-9 deg out (was 58-62, 1-4),
# 95 mm off the thigh; the right 5 deg more out, 37 mm off.)
# (Animation 57, from the close-up judge: both blades 44-54 deg below level (were 36-42), turned out <= 16 deg, so the far
# knife still reads steep on screen; the left fist 2 cm ahead and 2.5 cm out of the right's line, 2 cm higher; the poles
# lifted so the forearms run steeper than the wrist can cancel.)


def stalker_knives(t, f):
    """idle_stalker_daggers' arms (animation 56): the knife fighter at ease, DAGGERS_IDLE."""
    a = {}
    for s in "rl":
        d = DAGGERS_IDLE[s]
        a[f"hand_{s}"] = {"arc": arc_of(d["hand"]), "pole": d["pole"], "frame": "chest", "blade": _n(d["blade"]),
                          "twist": 0.5, **({"knuckles": _n(d["knuckles"])} if "knuckles" in d else {})}
        a[f"fingers_{s}"] = "grip"
    return a


# The wand at rest (idle_arcanist_wand, on the arcanist's standing; animation 56): the right arm let down by her thigh,
# the elbow soft, the wand on the forearm's line pointing down and a little ahead (as the runs carry it, run.wand_along);
# the left hand the staff idle's free one. Chest frame.
# (The wand 40-44 deg below level and 14 deg out, ~20 deg off the forearm's line as the run's; the elbow 28; 45 mm off her
# thigh.)
WAND_IDLE = {"hand": (-0.07, -0.47, 0.17), "pole": (-0.4, -0.2, -1.0), "blade": (-0.395, -0.707, 0.586)}
# (Animation 57: the tip turned 12 deg further out, off her thigh and kneecap (47 mm clear); 41-45 deg below level.)


def arcanist_wand(t, f):
    """idle_arcanist_wand's right arm (the left: the staff idle's free hand, build_one)."""
    w = WAND_IDLE
    return {"hand_r": {"arc": arc_of(w["hand"]), "pole": w["pole"], "frame": "chest", "blade": _n(w["blade"]), "twist": 0.5,
                       **({"knuckles": _n(w["knuckles"])} if "knuckles" in w else {})},
            "fingers_r": "grip"}


arcanist_wand.free_left = True


# The crossbow at a low ready (idle_stalker; animation 56): the carry of stalker() (STALKER_HAND_R/L, which the shot and
# the stops share and keep) turned muzzle-down `pitch` deg about her right fist and moved by `shift` (chest frame, m), the
# left hand carried with it on the fore-stock.
# (The bow's line 26-28 deg below level before, pointing ~60 deg across her toward her left; now 36-38, its muzzle 29-32
# below the wrist: an 11 deg turn.)
STALKER_LOW = {"pitch": 29.0,  # (animation 57: muzzle 46-49 deg below level, was 29-32)
                "yaw": 38.0, "shift": (0.02, 0.04, -0.02)}
# (The steeper turn dropped her left fist into her body and outfits: the carry raised 4 cm and 2 cm to her left.)
_SHOULDER_X = 0.19   # (each shoulder's x off her middle at rest, the chest frame: the two hands' arcs in one space)


def _arc_vec(arc):
    az, el, r = (math.radians(arc[0]), math.radians(arc[1]), arc[2])
    return np.array([math.sin(az) * math.cos(el), math.sin(el), math.cos(az) * math.cos(el)]) * r


def stalker_low(t, f):
    """idle_stalker's arms (animation 56): STALKER_LOW."""
    from keyed import _axis_matrix
    y = math.radians(STALKER_LOW["yaw"])
    Rx = _axis_matrix([math.cos(y), 0.0, -math.sin(y)], STALKER_LOW["pitch"])
    hr, hl = dict(STALKER_HAND_R["hand_r"]), dict(STALKER_HAND_L["hand_l"])
    sh = np.array(STALKER_LOW["shift"], float)
    pr = _arc_vec(hr["arc"]) + (-_SHOULDER_X, 0, 0)
    pl = _arc_vec(hl["arc"]) + (_SHOULDER_X, 0, 0)
    pl2 = pr + Rx @ (pl - pr)
    hr["arc"] = arc_of(pr + sh - (-_SHOULDER_X, 0, 0))
    hl["arc"] = arc_of(pl2 + sh - (_SHOULDER_X, 0, 0))
    hr["blade"] = tuple(Rx @ np.array(STALKER_TOP, float))
    for h in (hr, hl):
        for k in ("knuckles", "blade"):
            if k in h and not (h is hr and k == "blade"):
                h[k] = tuple(Rx @ np.array(h[k], float))
    return {"hand_r": hr, "hand_l": hl, "fingers_r": "grip", "fingers_l": "relaxed"}


# Animation 57 round 3 (idle_stalker; replaces the low ready above, which stays for reference): the crossbow RESTED ON HER
# RIGHT SHOULDER, the model reaver_shoulder. The fist on the grip just in front of the shoulder (the wrist can turn the
# muzzle back only with the hand this near: any lower or further in and the bow lies through her back), the elbow
# folded forward, the muzzle up (elev, chest frame) and out/back over the shoulder. The left arm hangs as the other idles
# hang it (free_left). The solver's wrist limit decides the final line, not the keyed one: see the numbers.
# (Measured: muzzle 44-46 deg above level, 41-43 out, ~20 cm back of the wrist; 86 mm off her body at the nearest, 305 mm
# off her head. The elbow is folded ~155, not the 100 asked: a fist at chest height cannot turn the muzzle back.)
STALKER_REST = {"hand": (-0.06, -0.07, 0.06), "pole": (0.0, -0.8, 3.0), "elev": 40.0, "out": 45.0}


def _rest_axes(d):
    """The bow's muzzle (hand +Y) and top (hand +Z, as upright as the muzzle allows), chest frame."""
    e, o = math.radians(d["elev"]), math.radians(d["out"])
    m = np.array([-math.sin(o) * math.cos(e), math.sin(e), -math.cos(o) * math.cos(e)])
    top = np.array([0.0, 1.0, 0.0]) - m * m[1]
    return m, top / np.linalg.norm(top)


def stalker_shoulder(t, f):
    """idle_stalker's right arm: STALKER_REST (the left: the free hand, build_one)."""
    d = STALKER_REST
    m, top = _rest_axes(d)
    return {"hand_r": {"arc": arc_of(d["hand"]), "pole": d["pole"], "frame": "chest", "blade": tuple(top),
                       "knuckles": tuple(m), "twist": 0.5}, "fingers_r": "grip"}


stalker_shoulder.free_left = True


# The crossbow's top (hand_r +Z) in stalker()'s carry, the chest frame (stalker_top on the heroine, 27 Oct): turned with
# the carry so the bow turns as one.
STALKER_TOP = (0.5221272672374219, 0.8379472461150218, -0.15604051294925717)


def free_arms(hand_l=(0.16, -0.46, 0.08), hand_r=(-0.14, -0.46, 0.08), reach=1.0, swing=0.012, pole_l=(0.3, -0.2, -1.0),
              pole_r=(-0.3, -0.2, -1.0)):
    """Free arms aimed from the shoulder in the chest's frame (animation 44-48's town arms, held out 17-25 deg to clear
    her swaying hips; the town stands now hang theirs, town_idle.hang_arms): each hand (chest frame, from the
    shoulder), `reach` the arm let out, a small counter-swing to the hips' sway. (staff_town's base.)"""
    hl, hr = np.array(hand_l, float) * reach, np.array(hand_r, float) * reach

    def arms(t, f):
        sw = swing * math.sin(2 * math.pi * t * 2)
        return {
            "hand_l": {"arc": arc_of(hl + (0, 0, sw)), "pole": pole_l, "frame": "chest", "thumb": _n((-0.15, -0.1, 1.0)), "twist": 1.0},
            "hand_r": {"arc": arc_of(hr - (0, 0, sw)), "pole": pole_r, "frame": "chest", "thumb": _n((0.15, -0.1, 1.0)), "twist": 1.0},
            "fingers_l": "relaxed", "fingers_r": "relaxed",
        }
    return arms


# Her town stands (animation 44; animation 48: each calling its own standing, town_idle.STANCES). Animation 50 (the
# owner, 26 Oct, of the arms held out from her sides: "nobody stands like that"): every free hand HANGS
# (town_idle.hang_arms), beside her outer thigh on her pelvis, the elbow soft at 18, the upper arm 8-12 deg out; the
# reaver's and the arcanist's left hand stay on her hip (town_idle.on_hip). Each hand's `out` (m beyond her hip joint)
# and elbow `pole` fitted to her body and every outfit (scratch anim50/hang harness: 0 mm into her or any outfit,
# the hand and forearm 5-25 mm off her own calling's): the hips sway and cock differently under each stand.
_P = lambda x: (x, -0.2, -1.0)   # an elbow pole behind her, x out (+) or in (-) of the arm, for a LEFT hand
_NONE = lambda t, f: {}
# The warden's WiggleHips: her hips swing out under the left hand further than the right.
# (Round 2: the left hand ahead of the sheathed sword, which hangs along her left thigh.)
# (Animation 51, the judge: the arms mirrored and angled out from the front. Her left hand rests on the sheathed sword's
# hilt as her town run's does (run.hilt_carry, POST below); the right hangs in closer, its forearm upright, the elbow
# softer.)
# (Animation 52, the owner reopened it, the judge: "as the pelvis moves over the right foot, the right arm floats about
# 8-10 cm off the skirt while her torso leans over that hip. It should hang straight down and meet the skirt." At a
# fixed out of 0.198 the hand was 6 mm off the warden skirt as the hip came in under it and up to 43 mm off as it swung
# away. Its out now follows the sway, and as that hip leans out under it (the wrist on the hip) the fingers lay in to
# the thigh at the wrist (flex, up to 3.3 deg): each fitted per frame to the skirt, then to a 4-harmonic loop. The
# hand and forearm 0.3-6.9 mm off the warden outfit all through, the hand 2.7-4.9 mm at the far sway. Scratch anim52/wh.)
WARDEN_TOWN = town_idle.hang_arms(r=dict(
    out=town_idle.loop_wave(0.1833, (0.0016, 0.0005), (-0.0064, 0.0104), (-0.0001, 0.0004), (0.0008, -0.0007)),
    flex=town_idle.loop_wave(0.78, (0.07, -0.27), (0.55, -1.11), (-0.24, -0.21), (-0.61, -0.53)), elbow=30.0))
TOWN = {
    # The axe (or two) on the hip loop at her right (and left) hip; her weight on her left hip, its hand on it.
    "reaver_town": town_idle.hang_arms(town_idle.on_hip(town_idle.REAVER_HIP_L, _NONE), r=dict(out=0.21, pole=_P(0.1))),
    # The wand on the belt at her right hip, her weight on her right leg.
    "arcanist_town": town_idle.hang_arms(town_idle.on_hip(town_idle.ARC_WRIST_L, _NONE), r=dict(out=0.19, pole=_P(0.1))),
    # The crossbow slung on her back, the daggers at the back of her belt.
    # (Round 2, the judge: "mirrored", "claws": the right elbow 13 more and the hand a little forward on her thigh,
    # both hands' fingers together in a loose half-curl.)
    # (Animation 51, the judge: the left forearm upright, the fingertips at her outer thigh; both hands' curl graded
    # index -> little, no spread.)
    # (Animation 51, round 3b: the right thumb hooked over her belt, town_idle.STALKER_THUMB_R.)
    "stalker_town": town_idle.hang_arms(town_idle.on_hip(town_idle.STALKER_THUMB_R, _NONE), l=dict(out=0.176, elbow=14.0, pole=_P(0.15), fingers=town_idle.graded())),
}

# A staff stays in her hand in town (WeaponSockets.SocketOf: null).
def staff_town(t, f):
    """The staff upright at her right side as her armed stand holds it (idle_arcanist's arm: the grip forward of her
    hip, the elbow easy by her side), a little lower, riding her chest as she sways, on the combat mount, its foot off the ground as her armed stand holds it
    (a planted walking staff cannot be: the plain shaft ends 1.11 m up, her elbow can't come below 1.25 m; animation 45).
    The left arm free. (Planted on the ground it cannot be: on
    the fitted fist's diagonal, WRAP["staff"], the shaft runs head-toward-the-fingers, so an upright staff needs the
    forearm near level and the wrist at 1.1 m or more, and the plain shaft above the drawn grip allows a slide of
    25 cm at most before her fingers reach the head: its foot stays 15 cm or more up. A pinned staff in her root
    frame drifted 24 cm, the wrist unable to hold its line as she swayed.)"""
    d = free_arms(reach=1.03)(t, f)
    # (The wrist rides her chest, the staff's line is kept in her character's space, "char": on the chest's, its foot
    # swung 57 cm across as the WiggleHips chest rolls.) Re-aimed (judge round 3: the crescent hung over her face from
    # facing 45 at 26 deg forward, 2 out): the real line 9-13 deg forward, 15-19 out, the fist 4 cm out, 8 cm
    # forward, 4 cm higher, the elbow 9 deg more open (72), the elbow pole down. Lower or further out cannot be:
    # the wrist's radial limit (22) leaves the line leaning forward with the forearm below level, and 22 deg out
    # swings the foot 30 mm into her right thigh.
    d["hand_r"] = {"arc": arc_of((-0.21, -0.26, 0.25)), "pole": (0.0, -1.0, -0.2), "frame": "char",
                   "blade": _n((-0.34, 1.0, -0.05)), "twist": 0.5}
    d["fingers_r"] = "grip"
    return d


# The staff stand's free left arm hangs as the others do.
TOWN["arcanist_staff_town"] = town_idle.hang_arms(staff_town, l=dict(out=0.21, pole=_P(0.1)))


# A captured standing's stretch (seconds into the take) where not the first 8 s. (Animation 44's WiggleHips windows for
# the town stands, (0, 8), (2, 10), (9, 16), went with them: town_idle.STANCES has each calling's own.)
TOWN_WINDOW = {}


def level_head(rig, clip: Clip, keep=0.4) -> Clip:
    """Her head's mean tilt to one side taken down to `keep` of itself (the take's sway of it kept): the WiggleHips
    stretches hold the head 3-8 deg toward one shoulder, more on some stretches than on warden_town's."""
    from rig import qinv, qmul, qrot
    sk = rig.sk
    h = sk.i("Head")
    grest = sk.rest_globals()[0][0]
    g, _ = sk.fk(clip.rot, clip.pos)
    left = np.array([qrot(qmul(g[f, h], qinv(grest[h])), [1.0, 0, 0]) for f in range(clip.frames)])
    roll = float(np.degrees(np.mean(np.arcsin(np.clip(left[:, 1], -1, 1)))))
    turn = qaxis_((0.0, 0.0, 1.0), -(1 - keep) * roll)
    rot = clip.rot.copy()
    par = sk.parent[h]
    for f in range(clip.frames):
        rot[f, h] = qmul(qinv(g[f, par]), qmul(turn, g[f, h]))
    return Clip(clip.name, clip.fps, rot, clip.pos, loop=clip.loop,
                meta={**clip.meta, "changes": clip.meta.get("changes", "") + f"; head's mean tilt {roll:+.1f} deg taken to {keep:.0%}"})


def qaxis_(axis, deg):
    from rig import qaxis
    return qaxis(axis, deg)


IDLES = {
    "idle_warden": ("Heavyset", warden, "sword+shield"),
    "idle_arcanist": ("Strutting", arcanist, "staff"),
    "idle_reaver": ("Angry", reaver, "axe"),
    "idle_reaver_axes": ("Angry", reaver_axes, "axes"),
    "idle_stalker": ("Crouched", stalker, "crossbow"),
    "idle_stalker_daggers": ("Crouched", stalker_daggers, "daggers"),
    "idle_arcanist_wand": ("Strutting", arcanist_wand, "wand"),
    # In town, weapons sheathed (the game asks for idle_<calling>_town).
    "idle_warden_town": ("WiggleHips", WARDEN_TOWN, ""),
    # Each other calling its own (animation 48; the owner, 21 Oct: "having their own is probably better than all the
    # same"): town_idle.STANCES' takes and stances, the arms above (TOWN).
    "idle_reaver_town": ("Proud", TOWN["reaver_town"], ""),
    "idle_arcanist_town": ("GracefulArms", TOWN["arcanist_town"], ""),
    "idle_stalker_town": ("HandsInPockets", TOWN["stalker_town"], ""),
    "idle_arcanist_staff_town": ("GracefulArms", TOWN["arcanist_staff_town"], "staff"),
}


_bases = {}
# An idle that stands on another's captured base (the same standing, other arms).
SHARES_BASE = {"idle_stalker_daggers": "stalker", "idle_reaver_axes": "reaver", "idle_arcanist_staff_town": "arcanist_town",
               "idle_arcanist_wand": "arcanist"}
# The idles' own arms where IDLES' (which the stops and shows start or end on) differ (animation 56), and their own meta.
IDLE_ARMS = {"idle_stalker_daggers": stalker_knives, "idle_stalker": stalker_shoulder}


# A captured standing stood up (18 Oct, the owner: the stalker "always crouching like they have to go to the
# bathroom"). The Crouched take's knees bent 55 deg with her hips 17 cm behind her feet and her chest 19 deg over; she
# keeps its breath and sway, her hips lifted and carried over the middle of her feet (the knees to about a third of
# the bend), the hips and everything above turned back so the chest leans a little and the head comes level, the legs
# reaching again for the same planted ankles. knee: the mean knee bend wanted (deg); over: the hips ahead of the
# middle of her feet, ankle to ball (m); pitch: the hips turned back (deg); width: her ankles apart (m; the take's,
# drawn in to her hips, were 14 cm apart, near touching once she stood); stagger: her left foot ahead of her right (m),
# a shooter's stance under the crossbow held across her.
STAND = {"stalker": {"knee": 19.0, "over": 0.03, "pitch": 10.0, "width": 0.21, "stagger": 0.05}}


def stand(rig, clip: Clip, knee, over, pitch, width=None, stagger=0.0, drop=0.0) -> Clip:
    from rig import qaxis, qbetween, qinv, qmul, qrot, two_bone_ik
    sk = rig.sk
    rot, pos = clip.rot.copy(), clip.pos.copy()
    T = rot.shape[0]
    pel, root = sk.i("pelvis"), sk.i("root")
    g, p = sk.fk(rot, pos)
    ank = {s: p[:, sk.i(f"foot_{s}")].copy() for s in "lr"}
    ball = {s: p[:, sk.i(f"ball_{s}")] for s in "lr"}
    foot_g = {s: g[:, sk.i(f"foot_{s}")].copy() for s in "lr"}
    bend0 = {s: p[:, sk.i(f"calf_{s}")] - (p[:, sk.i(f"thigh_{s}")] + ank[s]) / 2 for s in "lr"}
    fwd = sum(ball[s] - ank[s] for s in "lr").mean(axis=0)
    fwd[1] = 0
    fwd /= np.linalg.norm(fwd)
    left = np.cross([0.0, 1.0, 0.0], fwd)
    side = 1.0 if np.mean(np.sum((ank["l"] - ank["r"]) * left, axis=1)) > 0 else -1.0
    apart = np.mean(np.abs(np.sum((ank["l"] - ank["r"]) * left, axis=1)))
    for s, k in (("l", 1.0), ("r", -1.0)):
        # The feet set out (a fixed offset each, so planted stays planted).
        d = left * side * k * ((width - apart) / 2 if width else 0.0) + fwd * k * stagger / 2
        ank[s] = ank[s] + d
        ball[s] = ball[s] + d
    mid = sum(ank[s] + ball[s] for s in "lr") / 4
    # The hips turned back about her left-right axis (a turn about `left` tips her up toward her front).
    turn = qaxis(left, -pitch)
    rot[:, pel] = qmul(qinv(g[:, root]), qmul(turn, g[:, pel]))
    # Carried forward over her feet (the sway about it kept), then the whole of her moved back so her hips sway about
    # the root as the take's did (in_place): her feet go back under her rather than her hips forward off the root.
    shift = fwd * (over - np.mean(np.sum((p[:, pel] - mid) * fwd, axis=1)))
    centre = p[:, pel].mean(axis=0) + shift
    centre[1] = 0.0
    for s in "lr":
        ank[s] = ank[s] - centre
    shift = shift - centre

    def legs(dy):
        r, q = rot.copy(), pos.copy()
        d = shift + np.array([0.0, dy, 0.0])
        q[:, pel] = q[:, pel] + qrot(qinv(g[:, root]), np.broadcast_to(d, (T, 3)))
        gl, gp = sk.fk(r, q)
        bends = []
        for s in "lr":
            th, ca, fo = sk.i(f"thigh_{s}"), sk.i(f"calf_{s}"), sk.i(f"foot_{s}")
            for t in range(T):
                a, b_, c_ = gp[t, th], gp[t, ca], gp[t, fo]
                k = bend0[s][t] / max(np.linalg.norm(bend0[s][t]), 1e-6)
                nb, nc = two_bone_ik(a, b_, c_, ank[s][t], (a + ank[s][t]) / 2 + k)
                r1 = qbetween(b_ - a, nb - a)
                gth = qmul(r1, gl[t, th])
                c2 = nb + qrot(r1, c_ - b_)
                gca = qmul(qbetween(c2 - nb, nc - nb), qmul(r1, gl[t, ca]))
                r[t, th] = qmul(qinv(gl[t, sk.parent[th]]), gth)
                r[t, ca] = qmul(qinv(gth), gca)
                r[t, fo] = qmul(qinv(gca), foot_g[s][t])
                u, v = nb - a, nc - nb
                bends.append(math.degrees(math.acos(np.clip(np.dot(u, v) / np.linalg.norm(u) / np.linalg.norm(v), -1, 1))))
        return r, q, float(np.mean(bends))

    lo, hi = -drop, 0.25   # (drop: how far her hips may come down, for a take whose knees bend less than wanted)
    for _ in range(18):
        dy = (lo + hi) / 2
        _, _, b = legs(dy)
        lo, hi = (dy, hi) if b > knee else (lo, dy)
    r, q, _ = legs((lo + hi) / 2)
    meta = {**clip.meta, "changes": clip.meta.get("changes", "") +
            f"; stood up: hips raised and carried over her feet, knees to {knee:.0f} deg, the body turned back {pitch:.0f} deg"}
    return Clip(clip.name, clip.fps, r, q, loop=clip.loop, meta=meta)


def base_of(rig, calling):
    """A calling's captured standing (made once a run, shared by its idle,
    its breaks and its flourish)."""
    if calling not in _bases:
        style = IDLES[f"idle_{calling}"][0]
        st = ARC_STS[ARC_ST] if calling == "arcanist" and ARC_ST else None
        if st:
            style = st["style"]
        if calling in town_idle.STANCES:
            base = town_idle.town_base(rig, calling)
        else:
            base = idle_loop(f"idle_{calling}_base", rig, style, seconds=(5.0, 8.0), window=TOWN_WINDOW.get(calling))
        if calling in town_idle.SWAYS:
            base = town_idle.soften(rig, base, **town_idle.SWAYS[calling])
        if calling in town_idle.SHOULDERS:
            base = town_idle.shoulders(rig, base, *town_idle.SHOULDERS[calling])
        if calling in STAND:
            base = stand(rig, base, **STAND[calling])
        if st:
            base = pitch_head(rig, stand(rig, base, **st["stand"]), st["head"])
            _free0[ARC_ST] = _free_spec(rig, st["hand"], *rig.sk.fk(base.rot[:1], base.pos[:1]))(0)
        _bases[calling] = base
    return _bases[calling]


def base_r1(rig):
    """R1's captured standing (the Strutting take as it was, before the restage): the breaks' keys in her character's
    frame were made on it, and are carried from it onto a restaged stand (soul.arcanist_break)."""
    if "_r1" not in _bases:
        _bases["_r1"] = idle_loop("idle_arcanist_base", rig, IDLES["idle_arcanist"][0], seconds=(5.0, 8.0),
                                  window=TOWN_WINDOW.get("arcanist"))
    return _bases["_r1"]


def _warden_hilt(rig, clip):
    from clips.run import hilt_carry
    # (The wrist 12 mm further out than the run's: the sway's hip roll brought her hip into the hand, 8 mm into the warden outfit.)
    return hilt_carry(rig, clip, {"clav": 1.0, "wrist": (0.3124, -0.0235, -0.0058)})


# The sheathed viking sword's grip at her left hip (Arms.cs hip_blade; arms_local.json "sheathed" viking_sword@hand_r,
# in the pelvis bone's frame: x her left, y up, z ahead): the line through its leather's section centres, from under
# the pommel (top) to just above the guard (bot); 16.7 mm round it. (The other one-handed blades share the scabbard.)
GRIP_TOP, GRIP_BOT = (0.209, 0.1654, 0.0515), (0.2154, 0.0867, 0.0386)
# The grip's line in her left fist closed in WRAP["sword"] (hand_l's frame: a point on it, and its way out of the thumb
# side), fitted on her posed hand (scratch anim51/wh/fitline.py): each finger's middle bone 1-3 mm off a 15.6 mm round,
# the palm on it. (WeaponSockets.BladeAtR / BladeDirR taken through her mirror, the right fist's seat, sat 6 mm and 6 deg
# off it: her fingers went 12-14 mm into the grip.)
FIST_L = ((0.04016, 0.08475, -0.00967), (0.09099, 0.55736, 0.82527))
# The scabbard stands off her hip by her outfit's socket clearance (godot/art/anim/socket_clearance.json hip_blade, out
# along the pelvis's +x): the warden's.
HIP_BLADE_OUT = 0.0155


def grip_hilt(rig, clip, at=0.0, spin=20.0, pole=(1.0, -0.2, 0.3), fingers=None, push=HIP_BLADE_OUT, passes=2, twist=0.5):
    """`clip` with her left hand closed round the sheathed sword's grip (GRIP_TOP..GRIP_BOT), frame by frame on the
    clip's own pelvis, so the hand rides her hips with the sword: the fist's hollow on the grip's
    line (FIST_L), `at` m from its middle toward the guard (the scabbard `push` m out), its blade way pointing down the grip to the guard (the forefinger and
    thumb by the guard, the little finger under the pommel), turned `spin` deg about the grip (0: the least turn from
    the hand's rest); the elbow's way `pole` from the shoulder in the pelvis's frame. The left arm solved afresh
    (keyed.solve_frames, the clip as its base), every other joint as it was."""
    from keyed import WRAP, solve_frames
    from rig import qmatrix, qnorm
    I = rig.I
    pel, ua = I["pelvis"], I["upperarm_l"]
    g, p = rig.sk.fk(clip.rot, clip.pos)
    A, D = np.array(FIST_L[0]), np.array(FIST_L[1])
    D /= np.linalg.norm(D)
    top, bot = (np.array(v) + (push, 0.0, 0.0) for v in (GRIP_TOP, GRIP_BOT))
    down = (bot - top) / np.linalg.norm(bot - top)

    def turn(u, v):
        w, c = np.cross(u, v), float(u @ v)
        K = np.array([[0, -w[2], w[1]], [w[2], 0, -w[0]], [-w[1], w[0], 0]])
        return np.eye(3) + K + K @ K / (1 + c)

    s = math.radians(spin)
    K = np.array([[0, -down[2], down[1]], [down[2], 0, -down[0]], [-down[1], down[0], 0]])
    R = (np.eye(3) + math.sin(s) * K + (1 - math.cos(s)) * K @ K) @ turn(D, down)   # the hand's axes, pelvis frame
    W = (top + bot) / 2 + down * at - R @ A                                          # the wrist, pelvis frame
    arm = [ua]
    for j in arm:
        arm += [k for k, q in enumerate(rig.sk.parent) if q == j and k not in arm]

    n = clip.frames
    want = [qmatrix(qnorm(g[f, pel])) @ R for f in range(n)]
    at = [p[f, pel] + qmatrix(qnorm(g[f, pel])) @ W for f in range(n)]
    aim, put = list(want), list(at)
    base = [(clip.rot[f].copy(), clip.pos[f].copy()) for f in range(n)]
    for k in range(passes):
        # (The solve lands the wrist 4-6 mm off its key and the hand a degree or so: the shoulder settles after the arm is
        # laid. A second pass keys it that much the other way.)
        specs = [{"hand_l": {"pos": tuple(put[f]), "knuckles": tuple(aim[f][:, 1]), "blade": tuple(aim[f][:, 2]),
                             "pole": tuple(qmatrix(qnorm(g[f, pel])) @ np.array(pole, float)), "pole_at": "shoulder", "twist": twist},
                  "fingers_l": fingers if fingers is not None else WRAP["sword"]} for f in range(n)]
        rot, _ = solve_frames(rig, specs, base, loop=clip.loop, weapon=(clip.meta or {}).get("weapon", ""))
        for f in range(n):
            for j in arm:
                clip.rot[f, j] = rot[f, j]
        g2, p2 = rig.sk.fk(clip.rot, clip.pos)
        for f in range(n):
            got = qmatrix(qnorm(g2[f, I["hand_l"]]))
            aim[f] = aim[f] @ got.T @ want[f]
            u, _s, vt = np.linalg.svd(aim[f])
            aim[f] = u @ vt
            put[f] = put[f] + (at[f] - p2[f, I["hand_l"]])
    return clip


# The sheathed viking sword's pommel (arms_local.json "sheathed", pelvis frame, the scabbard's push not added): a flat
# lobed plate 25 mm thick (x 0.193-0.218), 60 mm fore and aft (z 0.025-0.085), its top edge at y 0.225-0.235.
POMMEL_TOP = (0.207, 0.231, 0.055)
# Her left palm on it (animation 55, the owner on the town close-up of the fist on the grip: "is this angle possible or
# natural?"; the forearm level, the elbow out, the wrist bent ~90 down, the fingers open). With the hilt where it hangs
# (its grip's top 0.29 m under her shoulder, the pommel's 0.22) no closed fist on the grip lets the elbow hang by her
# side with the wrist straight: the fist turned every way round the grip (scratch anim55/idlesA/g.py) left the wrist
# 29 deg or more bent with the elbow back, or straight only with the elbow out at shoulder height (as it was) or across
# her front. A palm laid on the pommel's top edge, the fingers draped over its front lobe, takes any forearm the
# elbow gives it: the wrist straight on the forearm's line, the elbow back by her side.
# PALM: the point of the palm (hand_l's frame; +x the palm side, +y the fingers, +z the thumb) laid on POMMEL_TOP;
# DRAPE: the fingers' bends over the lobe (deg, knuckle/middle/last).
PALM_L = (0.024, 0.085, -0.004)
# (27 Oct, the owner's note on limp fingers: the middle joints curled 15-20 deg more, graded from the index to the little
# finger, the knuckle bends 14-17 deg and the last joints 8-10 deg less to keep them off the pommel, as far from it as
# before (9-14 mm bone to pommel, now 10-18), and drawn together by about 5 deg of fan: spreads -4..7 -> -2.2..3.9.)
DRAPE_L = {"bends": {"index": [34.0, 70.0, 18.0], "middle": [36.0, 72.5, 19.0], "ring": [29.0, 71.0, 15.0],
                     "pinky": [40.0, 75.0, 17.0], "thumb": [6.0, 14.0, 12.0]},
           "spreads": {"index": -2.2, "middle": 0.0, "ring": 1.7, "pinky": 3.9}}


def rest_on_pommel(rig, clip, pole=(0.15, -0.55, -1.0), ext=10.0, palm=PALM_L, fingers=None, push=HIP_BLADE_OUT,
                   passes=4, twist=0.5):
    """`clip` with her left palm resting on the sheathed sword's pommel (POMMEL_TOP, the scabbard `push` m out), frame by
    frame on the clip's own pelvis so the hand rides her hips with the sword: the palm (`palm`, hand_l's frame) on its
    top edge, the palm facing down onto it, the hand on the forearm's line (bent back `ext` deg), the fingers draped
    over the front lobe (DRAPE_L); the elbow's way `pole` from the shoulder in the pelvis's frame (out, up, ahead).
    Each pass lays the hand on the forearm the last solve gave (the forearm follows the wrist, the wrist the hand)."""
    from keyed import solve_frames
    from rig import qmatrix, qnorm
    I = rig.I
    pel, ua, la, ha = I["pelvis"], I["upperarm_l"], I["lowerarm_l"], I["hand_l"]
    g, p = rig.sk.fk(clip.rot, clip.pos)
    C = np.array(POMMEL_TOP) + (push, 0.0, 0.0)
    arm = [ua]
    for j in arm:
        arm += [k for k, q in enumerate(rig.sk.parent) if q == j and k not in arm]
    n = clip.frames
    Mp = [qmatrix(qnorm(g[f, pel])) for f in range(n)]
    top = [p[f, pel] + Mp[f] @ C for f in range(n)]
    # The forearm's first guess: ahead and a little down from the elbow.
    fa = [Mp[f] @ _n((0.05, -0.25, 1.0)) for f in range(n)]
    base = [(clip.rot[f].copy(), clip.pos[f].copy()) for f in range(n)]
    e = math.radians(ext)
    for k in range(passes):
        specs = []
        for f in range(n):
            # The hand's axes: +y the forearm's line bent back `ext` about the palm's side-to-side axis, +x (the palm side)
            # facing down onto the pommel, +z = x cross y (the thumb side, toward her middle).
            y = fa[f] / np.linalg.norm(fa[f])
            x = np.array([0.0, -1.0, 0.0]) - y * (-y[1])
            x /= np.linalg.norm(x)
            y = y * math.cos(e) - x * math.sin(e)
            x = x * math.cos(e) + fa[f] / np.linalg.norm(fa[f]) * math.sin(e)
            x -= y * float(x @ y)
            x /= np.linalg.norm(x)
            z = np.cross(x, y)
            R = np.stack([x, y, z], axis=1)
            W = top[f] - R @ np.array(palm, float)
            specs.append({"hand_l": {"pos": tuple(W), "knuckles": tuple(y), "blade": tuple(z),
                                     "pole": tuple(Mp[f] @ np.array(pole, float)), "pole_at": "shoulder", "twist": twist},
                          "fingers_l": fingers if fingers is not None else DRAPE_L})
        rot, _ = solve_frames(rig, specs, base, loop=clip.loop, weapon=(clip.meta or {}).get("weapon", ""))
        g2, p2 = rig.sk.fk(rot, clip.pos)
        fa = [p2[f, ha] - p2[f, la] for f in range(n)]
    for f in range(n):
        for j in arm:
            clip.rot[f, j] = rot[f, j]
    return clip


# Passes after the arms (an idle's name: f(rig, clip) -> clip).
# (Animation 52: the owner reopened the warden's left hand, "on the hilt" from the front; Body 14's call: the pose is
# fine, the elbow volume drop was motion.py posing without her helpers. spin 40 over the fitted 20: the wrist's flex
# 30-58 -> 14-41 deg, the fist still on the grip.)
# (Animation 55: the owner, on the town close-up, "is this angle possible or natural?": the palm on the pommel instead,
# rest_on_pommel.)
def _warden_grip(rig, clip):
    return rest_on_pommel(rig, clip)


POST = {"idle_warden_town": _warden_grip}


def build_one(rig, name):
    """One idle (IDLES[name]) built: its arms (IDLE_ARMS over IDLES' own) on its captured base, its meta, its passes."""
    style, arms, weapon = IDLES[name]
    arms = IDLE_ARMS.get(name, arms)
    base = base_of(rig, SHARES_BASE.get(name, name[5:]))
    if arms is arcanist or getattr(arms, "free_left", False):
        arms = _free_hand(rig, base, arms, ARC_STS[ARC_ST]["hand"]) if ARC_ST else _on_hip(rig, base, arms)
    elif getattr(arms, "needs_base", False):
        arms = arms(rig, base)
    meta = {"weapon": weapon}
    if name == "idle_arcanist":
        meta.update(arc_grip())
    if name in ("idle_reaver", "idle_reaver_axes"):
        meta.update(axe_grip(name == "idle_reaver_axes"))
    clip = layered(name, rig, base, arms, meta)
    if name in POST:
        clip = POST[name](rig, clip)
    if name[5:] in TOWN or name == "idle_arcanist_staff_town":
        clip = level_head(rig, clip)
    return clip


def clips(rig, want):
    return [build_one(rig, name) for name in IDLES if not want or any(w in name for w in want)]
