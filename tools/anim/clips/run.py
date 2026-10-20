"""Her runs: a carriage for each calling, and the way each weapon is
carried at a run (tools/anim/gait.py).

- Warden: heavy plate. Square shoulders, a wider, flatter, harder stride,
  the shield held up across the body; the weight lands.
- Arcanist: poise. Upright, chin up, feet on one line, the hips swaying,
  the staff held still in one hand and the other hand open and loose.
- Reaver: feral. Pitched forward and hunched, a short fast cadence, big
  knee drive and the arms pumping with the axes.
- Stalker: a predator's glide. Low in the knees, long and smooth with
  little bounce, the head level and forward.
"""
from __future__ import annotations

import math
from dataclasses import replace

import numpy as np

from gait import Gait, arc_of, run_cycle

SPEED = 5.1  # her skeleton's metres a second: 5.3 in the world (she stands 1.04 times her model)


def _dir(up_deg, out=0.0):
    a = math.radians(up_deg)
    v = np.array([out, math.sin(a), math.cos(a)])
    return tuple(v / np.linalg.norm(v))


def _perp(up_deg, out=0.0):
    """The knuckles' line for a blade at up_deg: square to it, below it."""
    a = math.radians(up_deg - 90)
    v = np.array([out * 0.3, math.sin(a), math.cos(a)])
    return tuple(v / np.linalg.norm(v))


def blade_carry(out=-1.0, up_back=0.35, up_fwd=0.5, swing=None, tuck=0.0):
    """A blade carried in the swinging hand as a running hand carries one:
    the wrist straight in the grip and the forearm rolled so the thumb side
    faces out and up (`out`: -1 her right, +1 her left), so the blade rides
    out and ahead of her, rising as the fist comes through and dipping as
    it goes back, never across her legs. `swing`: the fist's own path (back,
    forward: from the shoulder, in the chest's frame, as for her right hand),
    held steadier than the free arm's: a hand behind her with the wrist
    straight can only point a blade down or across her, so a long blade's
    hand stays at her side. (Keyed by direction, up over her shoulder behind
    her, it asked a wrist bent back past what one can, and the hand flapped
    from one side to the other.) `tuck`: the elbow drawn in toward her side
    as the fist goes back (the pole's sideways part, toward the middle, all
    of it with the fist back and none with it forward), so the forearm runs
    straight ahead from it, not in across her: the hilt and its cross ride
    beside her hip, not into it and her thigh."""
    def f(ph, k, hand):
        hand = dict(hand)
        hand.update({"thumb": (out, up_back + (up_fwd - up_back) * k, 0.0), "frame": "chest", "twist": 0.5})
        e = k * k * (3 - 2 * k)
        if swing is not None:
            back, fwd = np.array(swing[0], float), np.array(swing[1], float)
            v = (back + (fwd - back) * e) * [-out, 1, 1]
            v[1] += 0.03 * math.sin(math.pi * k)
            hand["arc"] = arc_of(v)
        if tuck:
            hand["pole"] = tuple(np.array(hand["pole"], float) + [-out * tuck * (1 - e), 0.0, 0.0])
        else:
            hand["pole"] = tuple(np.array(hand["pole"]))
        return hand
    return f


# The long blades' hands: the sword at her side and ahead; the reaver's axe
# pumped harder, but still never far behind her. The warden's sword fist
# rides back 4-5 cm out from her hip and 4 cm higher, its elbow tucked in
# behind it (blade_carry's tuck), so the pommel and cross pass clear of her
# side, the plates at her hip and the thigh driving up (the oath's longer
# pommel too; at the old line they went 2-5 cm into her, the fist 5); and
# forward it comes no further in than her shoulder's line, a touch lower,
# its cross clear of the shield's rim (3 cm; it touched).
SWORD_SWING = ((-0.045, -0.30, 0.0), (0.0, -0.22, 0.25))
SWORD_TUCK = 0.45
AXE_SWING = ((0.02, -0.30, -0.08), (0.0, -0.10, 0.31))


def _swivel(h, phi):
    """A pole (chest frame) that swings the elbow phi degrees about shoulder-to-hand (h, from the
    shoulder) from her left: far out, so the elbow goes exactly there."""
    d = np.array(h, float) / np.linalg.norm(h)
    ref = np.array([1.0, 0, 0]) - d * d[0]
    ref /= np.linalg.norm(ref)
    a = math.radians(phi)
    return tuple(20.0 * (math.cos(a) * ref + math.sin(a) * np.cross(d, ref)))


def shield_guard(side="l", hand_at=(-0.02, -0.20, 0.38), swivel=-20, lift=0.0, fwd=0.0):
    """The shield up across the body, riding the step a little. It rides the
    forearm's hinge (its face is the plane of shoulder, elbow and wrist), so
    the guard is set by where the hand goes and how the elbow swings, never
    by the hand's aim: the hand well out ahead and the elbow open (120-130
    degrees) and out, so the disc stays clear of her own shoulder. (With the
    elbow near square it reached over the shoulder, through the pauldron.)
    The hand rides the forearm, the wrist straight in the grip."""
    def f(ph, k, hand):
        h = (hand_at[0], hand_at[1] + lift + 0.015 * math.cos(4 * math.pi * ph), hand_at[2] + fwd)
        return {"arc": arc_of(h), "pole": _swivel(h, swivel), "frame": "chest"}
    return f


def staff_hold():
    """The staff upright in the right fist at her side, tipped forward, the
    arm barely swinging. The hand 80 mm out to her right of where it was (x 0.02): with
    the fist closed on the shaft (WRAP["staff"], 17 October) its fingers went 80 mm into
    her right thigh as it came through (motion.py; 50 with the hand open), now 0.3."""
    def f(ph, k, hand):
        sway = 0.03 * (k - 0.5)
        return {"arc": arc_of((-0.08, -0.40, 0.10 + sway)), "pole": (-0.3, -0.1, -1.0),
                "blade": (0.05, 0.94, 0.33), "knuckles": (0.0, -0.33, 0.94), "frame": "chest", "twist": 0.5}
    return f


def crossbow_low():
    """The crossbow in the right fist on its pistol grip, the stock level and ahead (pitch -6..7 deg, yaw within 9 of
    her line), the forearm level from an elbow by her ribs, the fist at her waist 10 cm out. Pointed at the ground from
    beside the thigh (the old carry), the stock now the long axis put the bow 56-63 mm into her left thigh as it drove
    up (armscheck, 18 October); here 0, and the right arm 0 mm into her (motion.py)."""
    def f(ph, k, hand):
        sway = 0.06 * (k - 0.5)
        return {"arc": arc_of((-0.10, -0.15, 0.32 + sway)), "pole": (-0.2, -0.3, -1.0),
                "knuckles": (0.0, 0.64, 0.77), "blade": (0.0, 0.77, -0.64), "frame": "chest", "twist": 0.5}
    return f


# The warden's town carry: her free left hand rides the sheathed sword's hilt at her left hip (Arms.cs hip_blade),
# the classic hold that keeps a scabbard from swinging, fixed to the hilt in the pelvis bone's own frame (the space of
# arms_local.json "sheathed" mounts), so it rides her hips. Swinging free, the forearm went level through the hilt
# (28 mm in the run, 38-40 in the sprint). The hand lies on the scabbard's throat, just below the guards (local
# 0.16 m down the blade from the sheath point, which sits mid-grip; the four one-handed blades share the scabbard
# there, so one hand fits all four), the palm on its outer face tilted 27 degrees toward its front edge (the reaver
# outfit pushes the sword 14 mm further out than the warden's: square on, it went 8 mm into her palm), the fingers
# turned 8 degrees down from square across it, so the wrist stays 19-26 degrees from straight (more, and the
# radial limit clamped it and the palm rocked 3 mm on and off). Higher, the chevalier's guard met her hand.
# The elbow points out to her side and turns with her chest (pole_chest): pointed back, or fixed to the pelvis, it went
# 23-29 mm into the shield slung on her back mid-stride (now 6 at most; 5.3 swinging free). Hilt judge r1: from the
# front the elbow flared 12 cm out from her waist (a gunslinger's hand on the hip), so the hand sits 3.3 cm further
# down the throat, the arm hangs straighter (elbow 123-138, was 110-121) and the elbow swings 30 degrees in toward her
# side (4-6 cm closer; it can't come in and forward too, the hand fixes the circle it swings on). HILT: the wrist, the way the fingers lie (knuckles) and the thumb's side, the elbow's
# way from the shoulder (pole), all in the pelvis bone's frame (solved: tools/scratch/armor5 hilt notes); `clav`:
# the left shoulder's run swing kept (0: none, held at its mean; 0.3, so the held side rises and falls a little with
# each stride and doesn't read frozen, judge r1).
HILT = {"wrist": (0.3004, -0.0235, -0.0058), "knuckles": (0.0102, -0.2861, 0.9582), "thumb": (-0.1359, 0.9489, 0.2848),
        "pole": (0.69, -0.6385, -0.3101), "pole_chest": 1.0, "fingers": "relaxed", "clav": 0.3}


def hilt_carry(rig, clip, hilt=None):
    """`clip` with her left arm laid onto the sheathed sword's hilt (HILT), frame by frame on the clip's own pelvis:
    the left arm solved afresh over the clip (keyed.solve_frames, the clip as its base), every other joint as it was."""
    from keyed import solve_frames
    from rig import qrot
    h = dict(HILT, **(hilt or {}))
    I = rig.I
    pel, ua = I["pelvis"], I["upperarm_l"]
    g, p = rig.sk.fk(clip.rot, clip.pos)
    n = clip.frames
    arm = [ua]
    for j in arm:
        arm += [k for k, q in enumerate(rig.sk.parent) if q == j and k not in arm]

    if h.get("clav", 1.0) != 1.0:
        # The left shoulder's run swing (gait.pose_at: drawn forward and back with the free arm) kept to this share
        # of it about its mean: with the hand on the hilt, the full swing opened and closed the elbow 12 degrees.
        from rig import qnorm, qslerp
        c = I["clavicle_l"]
        mean = qnorm(np.mean(clip.rot[:, c] * np.sign(clip.rot[:, c] @ clip.rot[0, c])[:, None], axis=0))
        for f in range(n):
            clip.rot[f, c] = qslerp(mean, clip.rot[f, c], h["clav"])
        g, p = rig.sk.fk(clip.rot, clip.pos)

    # `pole_chest`: the share of the chest's turn on the pelvis (about its clip mean) that the elbow's way follows.
    # The shield rides her back on spine_03; with the pole fixed to the pelvis, the chest's run twist swung the
    # shield's rim into the elbow mid-stride.
    from rig import qmul, qinv, qnorm, qslerp
    ch = I["spine_03"]
    Mf = np.array([qmul(qinv(g[f, pel]), g[f, ch]) for f in range(n)])
    Mm = qnorm(np.mean(Mf * np.sign(Mf @ Mf[0])[:, None], axis=0))

    def spec(f):
        R = g[f, pel]
        Rp = qslerp(R, qmul(g[f, ch], qinv(Mm)), h.get("pole_chest", 0.0))
        return {"hand_l": {"pos": tuple(p[f, pel] + qrot(R, np.array(h["wrist"], float))),
                           "knuckles": tuple(qrot(R, np.array(h["knuckles"], float))),
                           "blade": tuple(qrot(R, np.array(h["thumb"], float))),
                           "pole": tuple(qrot(Rp, np.array(h["pole"], float))), "pole_at": "shoulder"},
                "fingers_l": h["fingers"]}
    rot, _ = solve_frames(rig, [spec(f) for f in range(n)], [(clip.rot[f], clip.pos[f]) for f in range(n)],
                          loop=clip.loop, weapon=(clip.meta or {}).get("weapon", ""))
    for f in range(n):
        for j in arm:
            clip.rot[f, j] = rot[f, j]
    return clip


# Post-passes on a run (and its sprint: sprint_stop.sprint) after the gait is solved.
POST = {"run_warden_town": hilt_carry}


def open_hand():
    def f(ph, k, hand):
        return hand
    return f


# Each calling's arm swing by its joints (gait.Gait.swing: forward, back = upper arm forward of hanging,
# out from her side, the elbow's inside angle, the upper arm turned in; chest frame): a natural run's arms,
# the elbows near square and close to her ribs, the fist ahead of the shoulder through the swing, in toward
# her middle and under her bust in front, by her hip behind. (Their old keys flared the elbows 35-55 degrees
# out and swung the fist 0.8-1.3 arm-lengths fore and aft: "chicken wing", "weird exaggerated arm movements".)
# (Round 2, animation 37: behind her the elbow closes to 65-75 and the forearm turns out (turn -25/-30), so the
# fist rides up and out past her hip; at 85-90 and turned in it went 45-80 mm into the thigh driving through.
# The Reaver leans 14+3, not 32+12: bent that far her own thigh came up into her hand, and from the play camera's
# 53-degree look down 24+8 still read as a stoop (judge r2).)
# The town run carries the shield slung on her back (Arms.cs Back socket, 66 cm across): the elbow no further than
# about 12 cm behind the shoulder, or it comes out through the shield's face (judge r2: at -36 it did, 27 mm; the
# sprint 56). The swing a touch further forward instead.
SWING = ((8, 12, 80, 20), (-20, 14, 70, -22))
# A heavy axe's arm (judge r2: the axe elbow winged out 30-35 degrees at the close-up): in by her side, half the
# free arm's swing, the forearm barely turned out.
AXE_ARM = ((6, 10, 80, 10), (-20, 11, 70, -10))
# The free left arm's own swing (anim 43 judge r1: forward, the wand run's open hand came to her lower belly and the
# second axe's fist to her navel, its haft toward her groin). Out from her side and the forearm not turned in, as
# run_reaver's: forward, the fist at the front of her left hip (wrist 25-28 cm out from the pelvis's midline, was 21-22).
# Anim 44 judge r3: the second axe hung at her side, the haft trailing, its edge back. Her left fist holds it with the
# head out of the thumb side, so a trailing haft wants the thumb turned back: the upper arm turned 95 out (the elbow's
# small bend goes out, not forward) and the wrist at its ulnar end. Swing +14/-20, elbow 152-146, 14 out (at 12 the arm
# met her trunk's cover, 1 mm). Measured (m7c): haft 14-32 back, head 39-41 cm clear of knee, shin and feet, never
# ahead of the knee (4 cm at most, with the knee passing back), fist always behind her hip crease, edge back.
AXES_L = ((14, 14, 152, -95), (-20, 14, 146, -95))
# The wand run's free fist (anim 44 judge r3: T-rex arms, the fist never behind her): forward at her lower ribs, under
# the bust (fist 129 cm in her rest frame, the underbust 130, navel 115) and 13 cm in front of it, the elbow 85 and
# 27 cm out; back behind the hip (7.5 cm in the run, 15 in the sprint), the elbow opened to 112 and the forearm less out.
WAND_L = ((10, 18, 85, 0), (-48, 8, 112, -10))
WARDEN = Gait(frames=21, speed=SPEED, duty=0.33, drop=0.09, bob=0.05, lean=19, spine_lean=4, hip_yaw=6, hip_roll=3,
              hip_shift=0.02, chest_yaw=6, width=0.08, reach=0.38, kick=0.36, knee=0.28, shoulders=(4, 4),
              fingers="fist", swing=((6, 14, 85, 20), (-32, 15, 75, -25)))
ARCANIST = Gait(frames=20, speed=SPEED, duty=0.30, drop=0.05, bob=0.06, lean=13, spine_lean=2, hip_yaw=8, hip_roll=5.5,
                hip_shift=0.03, chest_yaw=7, width=0.03, reach=0.34, kick=0.40, knee=0.30, head_up=4,
                arm_fwd=(0.0, -0.20, 0.25), arm_back=(0.0, -0.32, -0.22), elbow_out=0.25, fingers="open",
                swing=((6, 10, 80, 25), (-30, 12, 70, -25)))
REAVER = Gait(frames=19, speed=SPEED, duty=0.30, drop=0.10, bob=0.08, lean=14, spine_lean=3, hip_yaw=11, hip_roll=4,
              hip_shift=0.025, chest_yaw=8, width=0.07, reach=0.36, kick=0.48, knee=0.36, shoulders=(8, 10),
              arm_fwd=(0.0, -0.06, 0.34), arm_back=(0.04, -0.24, -0.32), elbow_out=0.5, fingers="fist",
              swing=((10, 14, 75, 20), (-36, 15, 65, -30)))
STALKER = Gait(frames=20, speed=SPEED, duty=0.34, drop=0.14, bob=0.035, lean=26, spine_lean=8, hip_yaw=8,
               hip_roll=4.5, hip_shift=0.025, chest_yaw=8, width=0.045, reach=0.40, kick=0.38, knee=0.26,
               head_up=6, arm_fwd=(0.0, -0.18, 0.26), arm_back=(0.03, -0.30, -0.24), elbow_out=0.2,
               swing=((6, 10, 80, 20), (-32, 12, 70, -25)))

AXE_HANG = dict(back=17.0, out=-10.0, edge=0.0, swing=0.0)


def axe_hang(back=17.0, out=6.0, edge=0.0, swing=0.0):
    """The second axe hung at her left side (anim 44 judge r3): the haft down from the fist, trailing `back` degrees
    behind vertical and `out` out from her, its edge facing back (`edge` degrees turned out from straight back),
    the haft's trail growing `swing` degrees as the fist goes back (k 0) and easing it as it comes forward."""
    def f(ph, k, hand):
        hand = dict(hand)
        b = math.radians(back + swing * (0.5 - k))
        o = math.radians(out)
        haft = np.array([math.sin(o), -math.cos(b) * math.cos(o), -math.sin(b) * math.cos(o)])
        e = math.radians(edge)
        eb = np.array([math.sin(e), math.sin(b), -math.cos(b)])
        eb = eb - haft * float(np.dot(eb, haft))
        hand.update({"blade": tuple(haft / np.linalg.norm(haft)), "knuckles": tuple(eb / np.linalg.norm(eb)), "frame": "char"})
        return hand
    return f


# The runs the game asks for: calling and what is in hand.
RUNS = {
    "run_warden": (WARDEN, {"r": blade_carry(swing=SWORD_SWING, tuck=SWORD_TUCK), "l": shield_guard(lift=0.04, fwd=-0.005)}, "sword+shield"),
    # The free fist's forward end higher and out, by her hip (anim 41: it landed at her groin from the close-up).
    "run_reaver": (replace(REAVER, swing_r=AXE_ARM, swing=((20, 16, 70, 5), REAVER.swing[1])), {"r": blade_carry(up_fwd=0.75)}, "axe"),
    "run_reaver_axes": (replace(REAVER, swing_r=AXE_ARM, swing=AXES_L), {"r": blade_carry(up_fwd=0.75), "l": axe_hang(**AXE_HANG)}, "axes"),
    "run_arcanist": (replace(ARCANIST, fingers_r="grip"), {"r": staff_hold()}, "staff"),
    # The wand fist turned further out behind her (judge r2: it brushed her buttock's outline at the close-up).
    # Its thumb up, not out (blade_carry's out=-1 is a blade's, riding out from her): with it out the wand stood
    # 58-61 degrees out of her sagittal plane at the back swing, 29-34 forward; up, at most 13 (run and sprint).
    "run_arcanist_wand": (replace(ARCANIST, fingers_r="grip", swing_r=((6, 10, 80, 25), (-30, 13, 70, -35)),
                                  fingers="fist", swing=WAND_L), {"r": blade_carry(out=0.0)}, "wand"),
    # The free left hand a fist and closer behind (its open fingers met her thigh, 7 mm; 31 in the sprint). The right
    # fist closed on the crossbow's pistol grip (WRAP["crossbow"], 18 October; relaxed, it stood off the grip).
    "run_stalker": (replace(STALKER, fingers="fist", fingers_r="grip", swing=((6, 10, 80, 20), (-30, 12, 62, -35))),
                    {"r": crossbow_low()}, "crossbow"),
    # Both fists closed on the daggers ("grip": each the fitted dagger fist, keyed.wrap_of: WRAP["daggers"] right,
    # WRAP["daggers_l"] left; with the gait's relaxed hands the fingers stood 10-73 mm off the hilts).
    "run_stalker_daggers": (replace(STALKER, fingers="grip"), {"r": blade_carry(), "l": blade_carry(1.0)}, "daggers"),
    # In town, weapons sheathed: her calling's carriage, the arms swinging free.
    # The free right hand a loose fist (hilt judge r1: open and limp, beside the still left arm the run read inert).
    "run_warden_town": (replace(WARDEN, fingers="relaxed", fingers_r="fist", swing=SWING), {}, ""),
    # Her other callings in town (animation 44): run_warden_town's free arms and hands on each calling's own carriage,
    # no hilt to hold (the armed runs' fists closed round a sheathed piece's absence). The arcanist's is the wand's
    # alone (OwnClips: run_<calling>_<kind>_town first): her staff stays in hand in town and keeps run_arcanist.
    # (The stalker on her armed run's free-arm swing: on SWING her sprint's hands went 34 mm into her thighs. The
    # arcanist's right on the wand run's, out behind her past the wand on her belt.)
    "run_reaver_town": (replace(REAVER, fingers="relaxed", fingers_r="fist", swing=SWING, swing_r=None), {}, ""),
    "run_arcanist_wand_town": (replace(ARCANIST, fingers="relaxed", fingers_r="fist", swing=SWING, swing_r=((6, 10, 80, 25), (-30, 13, 70, -35))), {}, ""),
    "run_stalker_town": (replace(STALKER, fingers="relaxed", fingers_r="fist", swing=((6, 10, 80, 20), (-30, 12, 62, -35)), swing_r=None), {}, ""),
}

# The sprint's own arms where they differ from the run's (sprint_stop applies these over RUNS).
# The shield hand sits back toward her (run 2.5 cm, sprint 2 cm from the first pass) so the
# elbow stays bent: at most 124 degrees in the run, 119 in the sprint (a judge's bar: 125/120).
SPRINT_ARMS = {"run_warden": {"l": shield_guard(lift=0.08, fwd=0.0)}}


def clips(rig, want):
    out = []
    for name, (g, arms, weapon) in RUNS.items():
        if want and not any(w in name for w in want):
            continue
        clip = run_cycle(name, rig, replace(g, arms=arms), {"weapon": weapon})
        out.append(POST[name](rig, clip) if name in POST else clip)
    return out
