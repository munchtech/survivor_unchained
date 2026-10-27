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
# Anim 46 judge r4: the arm flared ~40 deg out on screen from 315. Swing +10/-10 (the back swing made the flare), elbow
# 150-148, 13/10 out: upper arm on screen 42 -> 28 (sprint 48 -> 31), out of her side <= 13. At 10 out forward it met her
# trunk's cover (warden 6 mm, sprint 9) and +14 forward put it there too; 14+ forward out (or elbow 152) flips the sprint's
# elbow round (its own -5) and brings the second axe's head onto her knee (6 cm). Haft-to-leg min 31.6 (sprint 30.8).
AXES_L = ((10, 13, 150, -95), (-10, 10, 148, -95))
# The wand run's free fist (anim 44 judge r3: T-rex arms, the fist never behind her): forward at her lower ribs, under
# the bust (fist 129 cm in her rest frame, the underbust 130, navel 115) and 13 cm in front of it, the elbow 85 and
# 27 cm out; back behind the hip (7.5 cm in the run, 15 in the sprint), the elbow opened to 112 and the forearm less out.
WAND_L = ((10, 18, 85, -17), (-48, 8, 112, -23))
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

AXE_HANG = dict(back=26.0, out=-10.0, edge=0.0, swing=6.0)


def axe_hang(back=17.0, out=6.0, edge=0.0, swing=0.0, side="l", knuckles=True, out_swing=0.0):
    """The second axe hung at her left side (anim 44 judge r3): the haft down from the fist, trailing `back` degrees
    behind vertical and `out` out from her, its edge facing back (`edge` degrees turned out from straight back),
    the haft's trail growing `swing` degrees as the fist goes back (k 0) and easing it as it comes forward.
    (Animation 54: `side` "r" mirrors it for the right fist's trailing carries, run.TRAIL.)"""
    sg = 1.0 if side == "l" else -1.0

    def f(ph, k, hand):
        hand = dict(hand)
        b = math.radians(back + swing * (0.5 - k))
        o = math.radians(out + out_swing * (0.5 - k))
        haft = np.array([sg * math.sin(o), -math.cos(b) * math.cos(o), -math.sin(b) * math.cos(o)])
        e = math.radians(edge)
        eb = np.array([sg * math.sin(e), math.sin(b), -math.cos(b)])
        eb = eb - haft * float(np.dot(eb, haft))
        hand.update({"blade": tuple(haft / np.linalg.norm(haft)), "frame": "char"})
        if knuckles:
            hand["knuckles"] = tuple(eb / np.linalg.norm(eb))
        return hand
    return f


_ARM_LEN = []


def wand_along(lean=18.0, out=0.0):
    """The wand carried as an extension of the forearm (animation 54: at blade_carry's straight wrist it stood ~45 deg
    off the forearm, a T): the wand on the forearm's line from elbow to wrist, tipped `lean` degrees off it toward
    her front and up (the wrist's ulnar bend takes the rest), so it points ahead and down as the arm swings.
    `out` (animation 55): the tip turned that many degrees out to her right, clear of her front knee."""
    def f(ph, k, hand):
        hand = dict(hand)
        if not _ARM_LEN:
            from rig import Skeleton
            sk = Skeleton.load()
            _, p = sk.rest_globals()
            p, I = p[0], sk.index
            _ARM_LEN.extend([float(np.linalg.norm(p[I["lowerarm_r"]] - p[I["upperarm_r"]])),
                             float(np.linalg.norm(p[I["hand_r"]] - p[I["lowerarm_r"]]))])
        lu, lf = _ARM_LEN
        az, el, r = math.radians(hand["arc"][0]), math.radians(hand["arc"][1]), hand["arc"][2]
        H = r * np.array([math.sin(az) * math.cos(el), math.sin(el), math.cos(az) * math.cos(el)])
        fa = H - lu * np.array(hand["pole"], float)
        fa /= np.linalg.norm(fa)
        n = np.array([0.0, 0.5, 1.0]) - fa * float(np.dot([0.0, 0.5, 1.0], fa))
        n /= np.linalg.norm(n)
        a = math.radians(lean)
        v = fa * math.cos(a) + n * math.sin(a)
        if out:
            o = np.array([-1.0, 0.0, 0.0]) - v * float(v[0] * -1.0)
            o /= np.linalg.norm(o)
            v = v * math.cos(math.radians(out)) + o * math.sin(math.radians(out))
        hand.update({"blade": tuple(v), "frame": "chest", "twist": 0.5})
        return hand
    return f


# Animation 54 (a max judge, 26 Oct: at the run's pump the sword, the reaver's axe, the right dagger and the wand stood
# out level, ~90 deg off the forearm, the sword ~70 cm out of her silhouette): the held piece trailing low at her side
# as the hung second axe is (axe_hang mirrored), the arm near straight and turned out so the thumb side faces back,
# swinging with the stride; the wand on the forearm's line (wand_along). The thumb side is turned back by the outside
# route (the upper arm turned 70 out, as AXES_L's), so the game's walk-run blend rolls the blade out past her side, not
# in across her legs (turned in, a 50/50 blend with walk_warden put the sword 89 mm into her thigh). Keyed by the blade
# alone (blade and knuckles together asked more than the wrist can, and the sword stood out sideways). Measured
# (solver runs1): sword and dagger points 40-65 deg below level, trailing; the axe 63 deg; the reaver's axe trails
# steeper (42) as the reaver's lean is smaller. (Run ahead and down as the walk's, the axe went 22-38 mm into the thigh
# driving up.)
# Animation 55 (a max judge on runs1: the long pieces too near the floor, the sword's tip at her soles, the arms near
# straight, a dead carry): the elbows bent 48-62 and the pieces raised. A trailing piece in a bent arm's fist can only
# trail if the forearm swings out from her side (the wrist turns a blade 17-77 degrees off the forearm's line, the
# axe's 20-66; a forearm reaching ahead turns the piece out of her shadow, sideways), so the solve brings the forearm
# out and down from an elbow kept by her side; the hand no further out than runs1's. Each trailing piece asked a little
# in toward her (`out` < 0) and further in as the fist goes back (`out_swing` < 0): asked straight back, the pieces
# yawed 20-30 out where the wrist ran out of reach. Measured (solver runs2): sword pitch -38..-40, -1..9 out, tip
# 0.40 m off the floor (was 0.10), elbow 60, the fist +-8 cm fore and aft; axes -46..-49, -8..13 out; daggers -34..-46.
# WIP, NOT SHIPPABLE: the game's walk-run blend (50/50 per-bone slerp) now rolls the sword and daggers 37-44 deg off
# the walk-run arc, out sideways (the walk's thumb forward, this hold's thumb back and the forearm out: a bent arm turns
# the piece with the forearm), the daggers 75-104 mm into her legs mid-blend; the daggers' upper arms 45-68 mm into
# her outfits (motion --outfits). runs1's near-straight arms kept the piece near the forearm's line, so the twist barely
# moved it (blend 6-8 deg).
TRAIL_ARM = ((20, 14, 120, -40), (-25, 13, 120, -40))
TRAIL = dict(back=53.0, out=-5.0, edge=0.0, swing=0.0, side="r", knuckles=False, out_swing=-22.0)
# The daggers keep round 1's near-straight carry (Animation 55 r2's bent arms put both upper arms 45-68 mm into all
# four outfits on held frames); they passed the runs1 judge with notes.
DAGGER_ARM = ((10, 1, 125, -85), (-10, 0, 123, -85))
DAGGER_TRAIL = dict(back=26.0, out=0.0, edge=0.0, swing=0.0, side="r", knuckles=False, out_swing=10.0)
# The reaver's axe: forward the fist no more than 10 ahead of hanging (at 20, the forearm reached ahead and the wrist
# could only trail the haft 20-30 out); its upper arm 22-24 out (at 15 it met her outfits, runs1). The second axe
# (run_reaver_axes) on the same carry mirrored (it hung near vertical from a straight arm, a different hold).
# Animation 55 runs3 tried a steeper haft (-58..-64, elbow 67, upper arm swept back 39-44, abducted 30): it fixed the
# level read but the arm read winged out from her body (max judge, round 3). The round-2 hold below is kept as an
# interim (better than the old level jut in every view); a different hold family (haft along the forearm, or a
# shoulder carry) is next.
AXE_TRAIL = dict(TRAIL, back=54.0, out=-6.0, out_swing=-28.0)
AXE_TRAIL_ARM = ((10, 24, 132, -50), (-22, 22, 132, -55))


# Animation 56 (hold B, a new family for the heavy pieces): the sword and the axes at a LOW POINT, carried ahead of her
# hip with the point (or the head) forward, down and out past her leg, the arm loose and swinging a little with the
# stride: her armed walk's and idle's own hold (walk_armed.sword/axe), so the walk-run re-grip barely moves the piece.
# Why: a trailing piece runs back-and-down, near the line of an elevated camera's view from her front, so it
# foreshortened flat from 330/30 (runs2: 1-18 deg off level on screen at the shoot's 29 deg pitch); a forward-down piece
# runs down the screen from the front and slants from the side (43-84 deg; the far-side piece reads near level only from
# her other side at the play camera, mostly behind her). Rejected: the shoulder carry for the reaver (the fist at her
# chest can't turn the haft back over the shoulder within the wrist: the solve stood the axe up beside her head, pitch
# +50 and the upper arm swept back 45), and the haft along the forearm (it needs a grip slide that follows the move
# blend, not the arm hold, so the axe would slide in her fist through every walk-run change).
# Measured (solver holdB p3): sword pitch -46..-29, 19-21 out, tip 0.29 m off the floor at the lowest, 61 mm from her
# thigh (sprint 34); axe -63..-46, 16-22 out, 96 mm (sprint 74); the second axe -55..-42, 23-30 out, never within 140 mm.
def low_point(pitch=(-34.0, -40.0), out=(18.0, 16.0), side="r"):
    """The held piece's line (hand to point or head) forward and down: `pitch` degrees (fist forward, fist back) and
    `out` degrees out to that side, in her character's frame, eased between with the arm's swing (k 1 forward)."""
    sg = 1.0 if side == "l" else -1.0

    def f(ph, k, hand):
        hand = dict(hand)
        p = math.radians(pitch[1] + (pitch[0] - pitch[1]) * k)
        o = math.radians(out[1] + (out[0] - out[1]) * k)
        hand.update({"blade": (sg * math.sin(o) * math.cos(p), math.sin(p), math.cos(o) * math.cos(p)), "frame": "char"})
        return hand
    return f


# The low-point arm: the upper arm a little ahead and behind hanging, 19 out (at 13 the sword passed 11-15 mm from her
# thigh as the knee drove through, the sprint's 10 mm into it), the elbow open 125-128 (the axe's 118-122: its head
# off the floor, 0.25 m at the lowest), the forearm turned a little out.
LOW_ARM = ((12, 19, 125, -10), (-18, 19, 128, -15))
LOW_ARM_R = ((12, 19, 118, -10), (-18, 19, 122, -15))
# The owner on the reaver run (routed, 27 Oct): "it reads as a careful jog". Her armed reaver runs drive harder: leant
# 18 (was 14) with the back 4, more flight (duty 0.27, was 0.30), a deeper, heavier drop and bob (0.11, 0.09), the
# knee up (0.42, was 0.36), the heel kicked (0.52) and the foot reaching (0.40); the hips turn less (9, was 11) and
# the chest more against them (10). run_reaver_town keeps REAVER (her town run is meant easy).
REAVER_ARMED = replace(REAVER, lean=18, spine_lean=4, duty=0.27, drop=0.11, bob=0.09, reach=0.40, kick=0.52, knee=0.42,
                       hip_yaw=9, chest_yaw=10)
# The wand: the upper arm a little behind hanging so the bent elbow's forearm (and the wand on its line) still points
# down 37-56 degrees; the forearm turned out behind her (turn -20: at -10 the wand passed 19 mm from her thigh, now
# 60) and the tip 5 more out past her front knee.
WAND_ARM = ((0, 15, 120, 0), (-30, 14, 120, -20))


# The runs the game asks for: calling and what is in hand.
RUNS = {
    # (Animation 56: the low point; was the trailing carry, TRAIL_ARM and axe_hang(**TRAIL).)
    "run_warden": (replace(WARDEN, swing_r=LOW_ARM), {"r": low_point(out=(26, 24)), "l": shield_guard(lift=0.04, fwd=-0.005)}, "sword+shield"),
    # The free fist's forward end higher and out, by her hip (anim 41: it landed at her groin from the close-up).
    "run_reaver": (replace(REAVER_ARMED, swing_r=LOW_ARM_R, swing=((20, 16, 70, 5), REAVER.swing[1])),
                   {"r": low_point(pitch=(-40, -46), out=(22, 20))}, "axe"),
    # The pair not mirrored: the second axe's head higher and further out than the first's.
    "run_reaver_axes": (replace(REAVER_ARMED, swing_r=LOW_ARM_R, swing=LOW_ARM_R),
                        {"r": low_point(pitch=(-40, -46), out=(22, 20)), "l": low_point(side="l", pitch=(-36, -42), out=(22, 20))}, "axes"),
    "run_arcanist": (replace(ARCANIST, fingers_r="grip"), {"r": staff_hold()}, "staff"),
    # The wand fist turned further out behind her (judge r2: it brushed her buttock's outline at the close-up).
    # Its thumb up, not out (blade_carry's out=-1 is a blade's, riding out from her): with it out the wand stood
    # 58-61 degrees out of her sagittal plane at the back swing, 29-34 forward; up, at most 13 (run and sprint).
    "run_arcanist_wand": (replace(ARCANIST, fingers_r="grip", swing_r=WAND_ARM,
                                  fingers="fist", swing=WAND_L), {"r": wand_along(out=5.0)}, "wand"),
    # The free left hand a fist and closer behind (its open fingers met her thigh, 7 mm; 31 in the sprint). The right
    # fist closed on the crossbow's pistol grip (WRAP["crossbow"], 18 October; relaxed, it stood off the grip).
    "run_stalker": (replace(STALKER, fingers="fist", fingers_r="grip", swing=((6, 10, 80, 20), (-30, 12, 62, -35))),
                    {"r": crossbow_low()}, "crossbow"),
    # Both fists closed on the daggers ("grip": each the fitted dagger fist, keyed.wrap_of: WRAP["daggers"] right,
    # WRAP["daggers_l"] left; with the gait's relaxed hands the fingers stood 10-73 mm off the hilts).
    "run_stalker_daggers": (replace(STALKER, fingers="grip", swing=DAGGER_ARM), {"r": axe_hang(**DAGGER_TRAIL), "l": axe_hang(**{**DAGGER_TRAIL, "side": "l"})}, "daggers"),
    # In town, weapons sheathed: her calling's carriage, the arms swinging free.
    # The free right hand a loose fist (hilt judge r1: open and limp, beside the still left arm the run read inert).
    "run_warden_town": (replace(WARDEN, fingers="relaxed", fingers_r="fist", swing=SWING), {}, ""),
    # Her other callings in town (animation 44): run_warden_town's free arms and hands on each calling's own carriage,
    # no hilt to hold (the armed runs' fists closed round a sheathed piece's absence). The arcanist's serves the wand
    # (on her belt) and the staff (slung on her back, animation 45): Sheath.Names falls through to run_<calling>_town.
    # (The stalker on her armed run's free-arm swing: on SWING her sprint's hands went 34 mm into her thighs. The
    # arcanist's right on the wand run's, out behind her past the wand on her belt.)
    "run_reaver_town": (replace(REAVER, fingers="relaxed", fingers_r="fist", swing=SWING, swing_r=None), {}, ""),
    "run_arcanist_town": (replace(ARCANIST, fingers="relaxed", fingers_r="fist", swing=SWING, swing_r=((6, 10, 80, 25), (-30, 13, 70, -35))), {}, ""),
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
