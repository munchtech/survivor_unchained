"""Her arts: the vault, the bull rush and the chain haul, timed to the game
(godot/logic/Sim/Arts.cs) and played whole by PlayerView.

- vault: moving, she springs 6 m on the way she runs, 0.32 s in the air
  (the game lifts her 2.2 m at the top): a split leap, legs flung wide,
  landing on the lead foot into her run.
- vault_back: standing, she springs 6 m back from where she faces, eyes on
  what she escapes: a tucked back spring into a low three-point landing,
  one hand on the ground, the blade hand swept out behind.

The clips start at the moment the game moves her (no wind-up the game has
no time for) and land when it lands her; what comes after is the weight,
cut short by PlayerView as soon as she moves on.
"""
from __future__ import annotations

from clips.actions import arm, body
from keyed import build


def _feet(l, r, lrot=(6, 0, 0), rrot=(-6, 0, 0), ltoe=0, rtoe=0, lpole=None, rpole=None):
    fl = {"pos": l, "rot": lrot, "toe": ltoe}
    fr = {"pos": r, "rot": rrot, "toe": rtoe}
    if lpole:
        fl["pole"] = lpole
    if rpole:
        fr["pole"] = rpole
    return {"foot_l": fl, "foot_r": fr}


def _hips(x, y, z):
    return {"hips": {"pos": (x, y, z)}}


# ----------------------------------------------------------------- vault --
def vault(rig):
    """Moving: a split leap on the run, then the landing stride."""
    # In the air: the right arm reaching on with the leap, the left trailing
    # low and out with its blade.
    fly_r = arm((-0.16, 0.06, 0.44), (-0.7, -0.3, -0.4))
    fly_l = arm((0.30, -0.24, -0.30), (0.7, 0.3, 0.2))
    keys = [
        # Off the right toe, the left knee driven up and through, the right
        # arm thrown forward against it.
        (0, body({**_hips(0, 0.0, 0.06), **_feet((0.08, 0.40, 0.34), (-0.08, 0.06, -0.30), (4, 10, 0), (-4, 55, 0), rtoe=30),
                  "hand_r": arm((-0.10, 0.00, 0.42), (-0.6, -0.4, -0.6)), "hand_l": arm((0.16, -0.20, -0.36), (0.6, 0.4, 0.2)),
                  "fingers_l": "open", "fingers_r": "grip"},
                 hips=(0, 14, 0), spine=(0, 8, 0), neck=(0, -6, 0), head=(0, -10, 0)), "auto"),
        # The split, held a breath at the top: the front leg straight out,
        # the back one stretched long behind, toes pointed.
        (4, body({**_hips(0, 0.06, 0.0), **_feet((0.05, 0.86, 0.90), (-0.05, 0.62, -0.78), (4, 25, 0), (-4, 155, 0),
                                                  lpole=(0.1, 1, 0.2), rpole=(-0.1, -1, 0.1)),
                  "hand_r": fly_r, "hand_l": fly_l, "fingers_l": "spread", "fingers_r": "grip"},
                 hips=(8, 2, 0), spine=(-10, 4, 0), neck=(0, -6, 0), head=(6, -12, 0), clav_l=(4, -6), clav_r=(6, 8)), "ease"),
        (6, body({**_hips(0, 0.06, 0.0), **_feet((0.05, 0.80, 0.90), (-0.05, 0.64, -0.78), (4, 22, 0), (-4, 155, 0),
                                                  lpole=(0.1, 1, 0.2), rpole=(-0.1, -1, 0.1)),
                  "hand_r": arm((-0.18, 0.04, 0.44), (-0.7, -0.3, -0.4)), "hand_l": arm((0.32, -0.26, -0.28), (0.7, 0.3, 0.2)),
                  "fingers_l": "spread", "fingers_r": "grip"},
                 hips=(8, 4, 0), spine=(-10, 4, 0), neck=(0, -6, 0), head=(6, -12, 0), clav_l=(4, -6), clav_r=(6, 8)), "ease"),
        # The front leg drops to meet the ground; the back one stays up.
        (8, body({**_hips(0, 0.0, 0.04), **_feet((0.07, 0.30, 0.56), (-0.06, 0.56, -0.66), (4, 15, 0), (-4, 130, 0),
                                                   lpole=(0.1, 0.4, 1), rpole=(-0.1, -1, 0.1)),
                  "hand_r": arm((-0.14, -0.02, 0.42), (-0.6, -0.4, -0.6)), "hand_l": arm((0.26, -0.26, -0.30), (0.7, 0.3, 0.2)),
                  "fingers_l": "spread", "fingers_r": "grip"},
                 hips=(4, 10, 0), spine=(-6, 6, 0), neck=(0, -6, 0), head=(2, -10, 0)), "auto"),
        # Down on the left foot, the weight taken through the knee.
        (10, body({**_hips(0.02, -0.16, 0.08), **_feet((0.07, 0.0, 0.30), (-0.07, 0.40, -0.46), (4, 0, 0), (-4, 95, 0), rtoe=10,
                                                       rpole=(-0.1, -0.6, 0.4)),
                   "hand_r": arm((-0.10, -0.10, 0.36), (-0.5, -0.4, -0.6)), "hand_l": arm((0.16, -0.20, -0.30), (0.6, 0.4, 0.2)),
                   "fingers_l": "relaxed", "fingers_r": "grip"},
                  hips=(-4, 16, -3), spine=(4, 10, 2), neck=(0, -8, 0), head=(0, -10, 0)), "auto"),
        # The right leg comes through as the planted foot runs back under her.
        (13, body({**_hips(0.0, -0.08, 0.05), **_feet((0.07, 0.02, -0.18), (-0.07, 0.32, 0.12), (4, 25, 0), (-4, 10, 0)),
                   "hand_r": arm((-0.02, -0.24, 0.10), (-0.5, -0.4, -0.6)), "hand_l": arm((0.08, -0.20, 0.10), (0.6, -0.4, -0.6)),
                   "fingers_l": "relaxed", "fingers_r": "grip"},
                  hips=(0, 16, 0), spine=(0, 10, 0), neck=(0, -8, 0), head=(0, -10, 0)), "auto"),
        (16, body({**_hips(0.0, -0.10, 0.04), **_feet((0.07, 0.18, -0.34), (-0.07, 0.0, 0.34), (4, 45, 0), (-4, 0, 0), ltoe=20),
                   "hand_r": arm((0.02, -0.28, -0.20), (-0.5, 0.4, 0.2)), "hand_l": arm((0.0, -0.18, 0.26), (0.6, -0.4, -0.6)),
                   "fingers_l": "relaxed", "fingers_r": "grip"},
                  hips=(6, 16, 0), spine=(-8, 10, 0), neck=(0, -8, 0), head=(0, -10, 0)), "ease"),
    ]
    return build("vault", rig, keys, meta={"layer": "full", "note": "keyed: split leap on the run, 0.32 s flight"})


def vault_back(rig):
    """Standing: a tucked back spring, eyes on the enemy, into a low
    three-point landing; then up into her guard."""
    # The landing: the right knee all but on the ground, the left foot
    # planted before her, the left hand down beside it, the right arm and
    # its blade swept out behind; her head up, watching.
    land = {**_hips(0.02, -0.58, -0.04),
            **_feet((0.20, 0.0, 0.30), (-0.13, 0.05, -0.40), (18, 0, 0), (-14, 62, 0), rtoe=60,
                    lpole=(0.5, 0.1, 1), rpole=(-0.2, -0.4, 1)),
            "fingers_l": "spread", "fingers_r": "grip"}
    hand_down = {"pos": (0.26, 0.20, 0.44), "pole": (0.8, 0.4, -0.2), "knuckles": (0.1, -0.95, 0.3)}
    keys = [
        # Off both feet, already tipping back, the arms coming up before her.
        (0, body({**_hips(0, -0.04, 0.06), **_feet((0.11, 0.06, 0.14), (-0.11, 0.03, 0.06), (6, 45, 0), (-6, 50, 0)),
                  "hand_l": arm((0.22, -0.02, 0.34), (0.7, -0.3, -0.5)), "hand_r": arm((-0.24, -0.04, 0.32), (-0.7, -0.3, -0.5)),
                  "fingers_l": "open", "fingers_r": "grip"},
                 hips=(0, -16, 0), spine=(0, -14, 0), neck=(0, 6, 0), head=(0, 14, 0)), "auto"),
        # Tucked: the knees pulled up to her chest, the body laid back, the
        # chin down to keep her eyes on it, the blades out before her.
        (3, body({**_hips(0, 0.04, 0.0), **_feet((0.12, 0.52, 0.30), (-0.11, 0.44, 0.22), (6, 50, 0), (-6, 55, 0),
                                                  lpole=(0.3, 0.6, 1), rpole=(-0.3, 0.6, 1)),
                  "hand_l": arm((0.30, -0.22, 0.28), (0.8, -0.2, -0.4)), "hand_r": arm((-0.30, -0.26, 0.26), (-0.8, -0.2, -0.4)),
                  "fingers_l": "spread", "fingers_r": "grip"},
                 hips=(0, -38, 0), spine=(0, -10, 0), neck=(0, 14, 0), head=(0, 30, 0)), "ease"),
        (5, body({**_hips(0, 0.05, -0.02), **_feet((0.13, 0.62, 0.30), (-0.12, 0.56, 0.24), (8, 45, 0), (-6, 50, 0),
                                                  lpole=(0.3, 0.6, 1), rpole=(-0.3, 0.6, 1)),
                  "hand_l": arm((0.32, -0.26, 0.24), (0.8, -0.2, -0.4)), "hand_r": arm((-0.32, -0.22, 0.26), (-0.8, -0.2, -0.4)),
                  "fingers_l": "spread", "fingers_r": "grip"},
                 hips=(0, -44, 4), spine=(0, -8, -3), neck=(0, 16, 0), head=(0, 30, 0)), "auto"),
        # Out of the tuck, legs reaching down for the ground, the body coming
        # forward over them.
        (8, body({**_hips(0, -0.10, 0.0), **_feet((0.17, 0.16, 0.24), (-0.13, 0.22, -0.20), (12, 15, 0), (-10, 40, 0)),
                  "hand_l": arm((0.30, -0.22, 0.26), (0.7, -0.2, -0.5)), "hand_r": arm((-0.42, -0.06, 0.04), (-0.7, -0.1, -0.5)),
                  "fingers_l": "spread", "fingers_r": "grip"},
                 hips=(0, -4, 0), spine=(2, 8, -2), neck=(0, 0, 0), head=(0, 0, 0)), "auto"),
        # Down, hard.
        (10, body({**land, **_hips(0.02, -0.50, -0.02), "hand_l": {**hand_down, "pos": (0.26, 0.32, 0.46)},
                   "hand_r": arm((-0.30, -0.22, -0.30), (-0.7, 0.3, -0.4))},
                  hips=(-10, 28, 0), spine=(8, 30, -6), neck=(0, -18, 0), head=(6, -36, 0)), "fast"),
        (13, body({**land, "hand_l": hand_down, "hand_r": arm((-0.26, -0.32, -0.26), (-0.7, 0.3, -0.4))},
                  hips=(-10, 40, 0), spine=(8, 40, -6), neck=(0, -28, 0), head=(6, -56, 0)), "ease"),
        # Held: still, low, breathing; the head turns a touch as she reads it.
        (26, body({**land, **_hips(0.02, -0.56, -0.04), "hand_l": {**hand_down, "pos": (0.26, 0.21, 0.44)},
                   "hand_r": arm((-0.27, -0.30, -0.27), (-0.7, 0.3, -0.4))},
                  hips=(-8, 39, 0), spine=(10, 38, -6), neck=(0, -28, 0), head=(-10, -54, 0)), "ease"),
        # Up into her guard.
        (38, body({**_hips(0.0, -0.08, 0.0), **_feet((0.16, 0.0, 0.14), (-0.15, 0.0, -0.12), (14, 0, 0), (-16, 0, 0)),
                   "hand_l": arm((0.10, -0.26, 0.20), (0.6, -0.4, -0.5)), "hand_r": arm((-0.10, -0.24, 0.18), (-0.6, -0.4, -0.5)),
                   "fingers_l": "relaxed", "fingers_r": "grip"},
                  hips=(-6, 8, 0), spine=(6, 6, 0), neck=(0, -2, 0), head=(0, -4, 0)), "ease"),
    ]
    return build("vault_back", rig, keys, meta={"layer": "full", "note": "keyed: back spring, 0.32 s flight, three-point landing"})


ALL = (("vault", vault), ("vault_back", vault_back))
# Judged on sheets and in the game. Any other clip here is work in progress:
# built only when named, so a full build (and the game, which plays anything
# in her library at once) leaves it out.
JUDGED = {"vault", "vault_back"}


def clips(rig, want):
    return [f(rig) for name, f in ALL
            if (want and any(w in name for w in want)) or (not want and name in JUDGED)]
