"""The boar's clips, first pass (animation owns them from here: a7dd95d00c4a6a017).

Each is a pose as a function of the clip's time, on the four-legged rig
(quadruped.py), keyed at 30 fps. What the game plays them for (Beasts.cs):

  trot    move: its going pace, the diagonal pairs together        (loop)
  gallop  charge: down the lane, head low, the back gathering and
          stretching, all four off the ground once a stride        (loop)
  idle    idle and rise: breathing, the snout working the air, an
          ear flicked, the weight shifting                         (loop)
  paw     windup: head down, tusks low, a forehoof raking the
          ground twice, the tail lashing                           (loop)
  gore    attack: down, then the hook up and out through whatever
          is there; the apex on an even frame                      (held)
  flinch  hit: the jolt back from a blow                           (held)
  dazed   stunned: run into a tree, the head shaken, the legs
          wandering                                                (loop)
  die     over onto its left side, the legs gone slack             (held)
  die2    onto its right side, the legs stiff and kicking out      (held)
  die3    sunk onto its belly, the legs folding under it           (held)

All read from the game camera (64 degrees down, 31 m): big moves of the
head, the back and the legs, and the tusks thrown wide.
"""
import math

from quadruped import FWD, LEFT, UP, SIDES, Gait, Poser, key_clip, legs, place_leg, pose_gait, smooth

FPS = 30


def ease(t, a, b):
    return smooth((t - a) / max(1e-6, b - a))


def bump(t, a, peak, b):
    """0 before a, up to 1 at peak, back to 0 at b (smoothly)."""
    if t <= peak:
        return ease(t, a, peak)
    return 1 - ease(t, peak, b)


# The gaits, in the model's own metres (the rig as built). The game's speed
# for each is its model speed times the game's scale (boar_build prints it).
TROT = dict(period=0.4, duty=0.42, phase={"FL": 0.0, "HR": 0.03, "FR": 0.5, "HL": 0.53},
            lift={"F": 0.13, "H": 0.1}, fold={"F": 1.9, "H": 0.95}, bob=0.025, bobs=2, roll=0.025, head_low=0.08, scapula=0.2)
GALLOP = dict(period=0.34, duty=0.27, phase={"HL": 0.0, "HR": 0.09, "FL": 0.42, "FR": 0.52},
              lift={"F": 0.17, "H": 0.13}, fold={"F": 2.2, "H": 1.2}, reach={"F": 0.06, "H": 0.04},
              bob=0.06, bobs=1, bob_phase=0.18, pitch=0.07, flex=0.22, roll=0.015, head_low=0.3, scapula=0.32)


def stride_speed(spec, stride):
    """Ground speed (model m/s) for a planted stride (metres the hoof travels
    back under the body while down)."""
    return stride / (spec["period"] * spec["duty"])


def build(arm, scale_to_game):
    """Every clip onto the armature; returns the game's paces."""
    L = legs(arm)
    leg = arm.data.bones["Arm_L"].head_local.z          # the shoulder joint's height
    # The stride each gait can carry while a hoof is down: a trot's hooves
    # pass about a third of the leg's height either side of under the
    # shoulder; a gallop's reach is half again more.
    trot = Gait(speed=stride_speed(TROT, leg * 0.75), **TROT)
    gallop = Gait(speed=stride_speed(GALLOP, leg * 1.25), **GALLOP)

    def trot_pose(p, t):
        pose_gait(p, trot, t, L, extra=lambda p, t: (
            p.bend("Tail2", yaw=0.25 * math.sin(2 * math.pi * t)),
            [p.bend(f"Ear_{s}", pitch=0.12 * math.sin(4 * math.pi * t + (0 if s == "L" else 1))) for s in SIDES]))

    key_clip(arm, "trot", trot.period, FPS, trot_pose, loop=True)

    def gallop_pose(p, t):
        pose_gait(p, gallop, t, L, extra=lambda p, t: (
            p.bend("Jaw", pitch=0.0),
            [p.bend(f"Ear_{s}", pitch=0.5) for s in SIDES],           # pinned back
            p.bend("Tail1", pitch=-0.5), p.bend("Tail2", yaw=0.3 * math.sin(2 * math.pi * t))))

    key_clip(arm, "gallop", gallop.period, FPS, gallop_pose, loop=True)

    # --------------------------------------------------------------- idle --
    def idle_pose(p, t):
        a = 2 * math.pi * t
        breath = math.sin(a * 2)
        shift = math.sin(a)
        p.move("Pelvis", (0.006 * shift, 0, -0.004 + 0.004 * breath))
        p.bend("Spine2", pitch=0.01 * breath)
        p.bend("Chest", pitch=-0.015 * breath, roll=0.01 * shift)
        # The head low, working the air: a sweep down and up, the snout twitching.
        sweep = 0.12 + 0.1 * math.sin(a + 0.6)
        p.bend("Neck1", pitch=sweep * 0.5, yaw=0.12 * math.sin(a * 1 + 2.0))
        p.bend("Head", pitch=sweep * 0.5, yaw=0.08 * math.sin(a * 2 + 1.0))
        sniff = sum(bump(t, c - 0.05, c, c + 0.05) for c in (0.18, 0.26, 0.34, 0.68, 0.74))
        p.bend("Snout", pitch=-0.12 * sniff, yaw=0.05 * math.sin(a * 7))
        p.bend("Jaw", pitch=0.04 * sniff)
        # An ear flicked, then the other.
        p.bend("Ear_L", pitch=0.5 * bump(t, 0.38, 0.42, 0.5), yaw=-0.2 * bump(t, 0.38, 0.42, 0.5))
        p.bend("Ear_R", pitch=0.5 * bump(t, 0.82, 0.86, 0.94), yaw=0.2 * bump(t, 0.82, 0.86, 0.94))
        p.bend("Tail1", yaw=0.3 * math.sin(a * 3), pitch=0.1)
        p.bend("Tail2", yaw=0.3 * math.sin(a * 3 - 0.8))
        for key, leg in L.items():
            place_leg(p, leg, leg.fetlock.copy(), 0.0)

    key_clip(arm, "idle", 3.0, FPS, idle_pose, loop=True)

    # ---------------------------------------------------------------- paw --
    def paw_pose(p, t):
        # Two rakes in the clip (it loops for however long the wind-up lasts).
        k = (t * 2) % 1.0
        a = 2 * math.pi * t
        p.move("Pelvis", (0, 0.04, -0.03))               # back on its haunches
        p.bend("Pelvis", pitch=0.06)
        p.bend("Spine2", pitch=-0.05)
        p.bend("Chest", pitch=0.08 + 0.03 * math.sin(a * 2))
        p.bend("Neck1", pitch=0.3)
        p.bend("Head", pitch=0.35 + 0.05 * math.sin(a * 4))   # tusks low, at you
        p.bend("Snout", pitch=-0.1)
        for s in SIDES:
            p.bend(f"Ear_{s}", pitch=0.55)
        p.bend("Tail1", pitch=-0.4)
        p.bend("Tail2", yaw=0.5 * math.sin(a * 6))
        p.bend("Tail3", yaw=0.4 * math.sin(a * 6 - 1))
        for key, leg in L.items():
            pos = leg.fetlock.copy()
            fold = 0.0
            if key == "FL":
                # Up and forward, down, and raked back hard along the ground.
                up = bump(k, 0.0, 0.25, 0.45)
                fwd = ease(k, 0.0, 0.35) - ease(k, 0.45, 0.85)
                pos += FWD * (0.18 * fwd - 0.06) + UP * (0.16 * up)
                fold = 1.3 * up
            elif key == "FR":
                pos += FWD * 0.04
            place_leg(p, leg, pos, fold, 0.6 * bump(k, 0.0, 0.2, 0.45) if key == "FL" else 0.0)

    key_clip(arm, "paw", 0.9, FPS, paw_pose, loop=True)

    # --------------------------------------------------------------- gore --
    GORE = 0.5
    APEX = 8 / FPS / GORE        # frame 8 of 15 at 30 fps: an even frame, so the 15 fps bake has it

    def gore_pose(p, t):
        down = bump(t, 0.0, 0.18, APEX)
        hook = bump(t, 0.2, APEX, 0.95)
        lunge = bump(t, 0.05, APEX, 1.0)
        p.move("Pelvis", FWD * (0.12 * lunge) + UP * (-0.04 * down + 0.03 * hook))
        p.bend("Pelvis", pitch=0.05 * down - 0.05 * hook)
        p.bend("Chest", pitch=0.12 * down - 0.18 * hook, roll=0.12 * hook)
        p.bend("Neck1", pitch=0.35 * down - 0.6 * hook, yaw=-0.15 * hook)
        p.bend("Head", pitch=0.35 * down - 0.7 * hook, yaw=-0.25 * hook, roll=0.45 * hook)
        p.bend("Jaw", pitch=0.25 * hook)
        for s in SIDES:
            p.bend(f"Ear_{s}", pitch=0.6)
        p.bend("Tail1", pitch=-0.5 * hook)
        for key, leg in L.items():
            pos = leg.fetlock.copy()
            if key[0] == "F":
                # The forehooves planted wide and ahead, driving up into it.
                pos += FWD * (0.1 * lunge) + LEFT * ((0.04 if key[1] == "L" else -0.04) * lunge)
            else:
                pos += FWD * (-0.04 * lunge)
            place_leg(p, leg, pos, 0.0)

    key_clip(arm, "gore", GORE, FPS, gore_pose)

    # ------------------------------------------------------------- flinch --
    def flinch_pose(p, t):
        k = bump(t, 0.0, 0.3, 1.0)
        p.move("Pelvis", FWD * (-0.06 * k) + UP * (0.02 * k))
        p.bend("Chest", pitch=-0.15 * k, roll=0.15 * k)
        p.bend("Neck1", pitch=-0.25 * k, yaw=0.2 * k)
        p.bend("Head", pitch=-0.3 * k, yaw=0.2 * k)
        p.bend("Jaw", pitch=0.2 * k)
        for s in SIDES:
            p.bend(f"Ear_{s}", pitch=0.7 * k)
        for key, leg in L.items():
            place_leg(p, leg, leg.fetlock.copy(), 0.0)

    key_clip(arm, "flinch", 0.3, FPS, flinch_pose)

    # -------------------------------------------------------------- dazed --
    def dazed_pose(p, t):
        a = 2 * math.pi * t
        p.move("Pelvis", (0.02 * math.sin(a), 0.01 * math.sin(a * 2), -0.03))
        p.bend("Pelvis", roll=0.06 * math.sin(a))
        p.bend("Chest", roll=-0.08 * math.sin(a + 0.5))
        p.bend("Neck1", pitch=0.25, yaw=0.25 * math.sin(a))
        # The head shaken hard, twice, then hanging.
        shake = math.sin(a * 6) * (bump(t, 0.0, 0.1, 0.3) + bump(t, 0.5, 0.6, 0.8))
        p.bend("Head", pitch=0.3, roll=0.4 * shake, yaw=0.2 * shake)
        for s in SIDES:
            p.bend(f"Ear_{s}", pitch=-0.2, roll=0.3 * shake)
        for key, leg in L.items():
            off = {"FL": 0.0, "FR": 0.25, "HL": 0.5, "HR": 0.75}[key]
            wander = bump((t + off) % 1.0, 0.0, 0.15, 0.3)
            pos = leg.fetlock + LEFT * (0.06 * math.sin(a + off * 6)) + UP * (0.05 * wander)
            place_leg(p, leg, pos, 0.4 * wander)

    key_clip(arm, "dazed", 1.8, FPS, dazed_pose, loop=True)

    # -------------------------------------------------------------- deaths --
    def fall_pose(p, t, side, stiff):
        """Over onto a side (side +1: its left down, -1: its right),
        tipped about the edge of the flank, the legs slack or stiff."""
        k = ease(t, 0.0, 0.7)
        knees = ease(t, 0.0, 0.3)
        width = 0.22
        roll = side * 1.45 * k
        p.turn("Pelvis", FWD, -roll, about=(side * width, 0, 0))
        p.move("Pelvis", UP * (-0.08 * k))
        p.bend("Neck1", pitch=0.1 * k)
        p.bend("Head", pitch=0.2 * k)
        p.bend("Jaw", pitch=0.35 * ease(t, 0.5, 0.9))
        settle = math.sin(min(1.0, max(0.0, (t - 0.7) / 0.3)) * math.pi) * 0.08
        for s in SIDES:
            p.bend(f"Ear_{s}", pitch=0.3 * k)
        for key, leg in L.items():
            sg = 1 if key[0] == "F" else -1
            if stiff:
                # Legs locked straight and kicked out, a last spasm at the end.
                kick = 0.35 * ease(t, 0.3, 0.8) + settle
                p.local(leg.top, x=sg * kick)
            else:
                p.local(leg.top, x=sg * 0.25 * knees)
                p.local(leg.mid, x=-sg * 0.5 * knees)
                p.local(leg.meta, x=sg * 0.8 * k)
        p.bend("Tail1", pitch=0.4 * k)

    key_clip(arm, "die", 0.9, FPS, lambda p, t: fall_pose(p, t, +1, False))
    key_clip(arm, "die2", 0.9, FPS, lambda p, t: fall_pose(p, t, -1, True))

    def belly_pose(p, t):
        k = ease(t, 0.0, 0.8)
        hind = ease(t, 0.0, 0.5)
        fore = ease(t, 0.15, 0.75)
        p.move("Pelvis", UP * (-0.42 * hind))
        p.bend("Pelvis", pitch=0.0)
        p.bend("Chest", pitch=0.1 * fore)
        p.move("Chest", UP * (-0.38 * fore))
        p.bend("Neck1", pitch=0.25 * k)
        p.bend("Head", pitch=0.3 * k, roll=0.25 * ease(t, 0.6, 1.0))
        for s in SIDES:
            p.bend(f"Ear_{s}", pitch=0.3 * k)
        for key, leg in L.items():
            fold = fore if key[0] == "F" else hind
            sg = 1 if key[0] == "F" else -1
            p.local(leg.top, x=sg * 0.9 * fold)
            p.local(leg.mid, x=-sg * 1.9 * fold)
            p.local(leg.meta, x=sg * 1.2 * fold)
        p.bend("Tail1", pitch=0.6 * k)

    key_clip(arm, "die3", 1.0, FPS, belly_pose)
    return {"pace": trot.speed * scale_to_game, "charge_pace": gallop.speed * scale_to_game}
