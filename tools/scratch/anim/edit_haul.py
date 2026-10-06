from pathlib import Path
p = Path(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa4f5fc266b043035\tools\anim\clips\arts.py')
s = p.read_text()
s = s.replace('''  sword cocked low behind; then the lead foot planted, the shield punched
  out, and the rebound into her guard.
''', '''  sword cocked low behind; then the lead foot planted, the shield punched
  out, and the rebound into her guard.
- chain_haul and chain_strike: the chain bites and hauls her to it at
  28 m/s (from 0.08 s to some 0.4 s, by the gap): yanked off her feet by
  the chain arm, flown in nearly flat with the axe cocked high behind her
  head, held until she arrives; then (PlayerView, as the haul ends) the
  feet swing down under her and the axe comes over and down two-handed,
  the blow landing in the second frame, as the game's does on arrival.
''')
haul = '''

# ------------------------------------------------------------ chain haul --
def _axe_cocked(lift=0.0):
    """The axe high behind her head, ready to come over."""
    return {"arc": arc_of((-0.10, 0.30 + lift, -0.06)), "pole": (-0.6, 0.7, -0.3), "frame": "chest",
            "blade": _n(-0.25, 0.55, -0.8), "twist": 0.5}


def _chain_arm(reach=0.48, up=0.02):
    """The chain arm straight out at what it bit, the fist shut on it."""
    return {"arc": arc_of((0.04, up, reach)), "pole": (0.8, -0.3, -0.4), "frame": "chest",
            "knuckles": _n(0.0, 0.2, 1.0), "twist": 0.3}


def _flight(t):
    """Hauled through the air: nearly flat, legs trailing, chin up at it."""
    sway = 0.02 * math.sin(t * 1.3)
    return body({"hips": {"pos": (0.0, -0.08 + sway, 0.10)},
                 "foot_l": {"pos": (0.10, 0.62 + sway, -0.58), "rot": (8, 120, 0), "pole": (0.1, -1, 0.2)},
                 "foot_r": {"pos": (-0.10, 0.46 - sway, -0.70), "rot": (-8, 130, 0), "pole": (-0.1, -1, 0.2)},
                 "hand_l": _chain_arm(0.50, 0.04), "hand_r": _axe_cocked(0.02),
                 "clav_l": (4, 14), "clav_r": (10, -6), "fingers_l": "fist", "fingers_r": "grip"},
                hips=(6, 46, 0), spine=(-10, 20, 0), neck=(0, -24, 0), head=(4, -36, 0))


def chain_haul(rig):
    keys = [
        # The chain has bitten: the arm that threw it still out, the axe
        # coming up, the weight thrown forward off the back foot.
        (0, body({"hips": {"pos": (0.0, -0.10, 0.08)},
                  "foot_l": {"pos": (0.14, 0.0, 0.30), "rot": (12, 0, 0)},
                  "foot_r": {"pos": (-0.15, 0.08, -0.36), "rot": (-16, 45, 0), "toe": 40},
                  "hand_l": _chain_arm(0.46, 0.0), "hand_r": _axe_cocked(-0.10),
                  "fingers_l": "fist", "fingers_r": "grip"},
                 hips=(6, 18, 0), spine=(-8, 10, 0), neck=(0, -8, 0), head=(4, -12, 0)), "fast"),
        # Yanked off her feet.
        (3, body({"hips": {"pos": (0.0, -0.06, 0.12)},
                  "foot_l": {"pos": (0.11, 0.30, -0.10), "rot": (10, 70, 0)},
                  "foot_r": {"pos": (-0.11, 0.36, -0.52), "rot": (-10, 110, 0)},
                  "hand_l": _chain_arm(0.50, 0.04), "hand_r": _axe_cocked(0.0),
                  "clav_l": (4, 12), "clav_r": (8, -4), "fingers_l": "fist", "fingers_r": "grip"},
                 hips=(6, 34, 0), spine=(-10, 16, 0), neck=(0, -18, 0), head=(4, -28, 0)), "auto"),
        (6, _flight(0.0), "auto"),
        (12, _flight(1.0), "auto"),
        (18, _flight(2.0), "auto"),
        (24, _flight(3.0), "ease"),
    ]
    return build("chain_haul", rig, keys, meta={"layer": "full", "note": "keyed: yanked off her feet and flown in on the chain, held"})


def chain_strike(rig):
    both = {"pole": (-0.6, -0.4, -0.4), "frame": "chest", "twist": 0.5}
    keys = [
        (0, _flight(3.0), "fast"),
        # Feet swung down under her as the axe comes over the top, both
        # hands on it.
        (1, body({"hips": {"pos": (0.0, -0.22, 0.10)},
                  "foot_l": {"pos": (0.20, 0.12, 0.20), "rot": (14, 10, 0)},
                  "foot_r": {"pos": (-0.20, 0.16, -0.20), "rot": (-20, 30, 0)},
                  "hand_r": {**both, "arc": arc_of((-0.04, 0.30, 0.20)), "blade": _n(-0.1, 0.9, 0.4)},
                  "hand_l": {"arc": arc_of((0.02, 0.26, 0.24)), "pole": (0.6, -0.4, -0.4), "frame": "chest", "twist": 0.3},
                  "fingers_l": "grip", "fingers_r": "grip"},
                 hips=(0, 26, 0), spine=(0, 8, 0), neck=(0, -16, 0), head=(0, -24, 0)), "linear"),
        # The blow: down hard into a wide crouch, the axe buried low before her.
        (2, body({"hips": {"pos": (0.0, -0.40, 0.10)},
                  "foot_l": {"pos": (0.24, 0.0, 0.24), "rot": (18, 0, 0)},
                  "foot_r": {"pos": (-0.24, 0.02, -0.26), "rot": (-26, 20, 0), "toe": 20},
                  "hand_r": {**both, "arc": arc_of((-0.02, -0.22, 0.44)), "blade": _n(0.0, -0.75, 0.65)},
                  "hand_l": {"arc": arc_of((0.06, -0.26, 0.38)), "pole": (0.6, -0.4, -0.4), "frame": "chest", "twist": 0.3},
                  "fingers_l": "grip", "fingers_r": "grip", "clav_l": (-4, 14), "clav_r": (-4, 14)},
                 hips=(0, 34, 0), spine=(0, 30, 0), neck=(0, -18, 0), head=(0, -26, 0)), "ease"),
        (5, body({"hips": {"pos": (0.0, -0.44, 0.10)},
                  "foot_l": {"pos": (0.24, 0.0, 0.24), "rot": (18, 0, 0)},
                  "foot_r": {"pos": (-0.24, 0.02, -0.26), "rot": (-26, 20, 0), "toe": 20},
                  "hand_r": {**both, "arc": arc_of((-0.02, -0.28, 0.42)), "blade": _n(0.0, -0.85, 0.5)},
                  "hand_l": {"arc": arc_of((0.06, -0.30, 0.36)), "pole": (0.6, -0.4, -0.4), "frame": "chest", "twist": 0.3},
                  "fingers_l": "grip", "fingers_r": "grip", "clav_l": (-4, 16), "clav_r": (-4, 16)},
                 hips=(0, 38, 0), spine=(0, 32, 0), neck=(0, -20, 0), head=(0, -28, 0)), "ease"),
        # Wrenched free and up, the free hand back to its fist.
        (14, body({"hips": {"pos": (0.0, -0.18, 0.04)},
                   "foot_l": {"pos": (0.20, 0.0, 0.20), "rot": (16, 0, 0)},
                   "foot_r": {"pos": (-0.21, 0.0, -0.20), "rot": (-24, 0, 0)},
                   "hand_r": {**both, "arc": arc_of((-0.10, -0.26, 0.20)), "blade": _n(-0.3, 0.6, 0.7)},
                   "hand_l": {"arc": arc_of((0.04, -0.30, 0.16)), "pole": (0.7, -0.5, -0.3), "frame": "chest", "twist": 0.4},
                   "fingers_l": "fist", "fingers_r": "grip"},
                  hips=(0, 16, 0), spine=(0, 12, 0), neck=(0, -8, 0), head=(0, -10, 0)), "auto"),
        (26, AXE_GUARD, "ease"),
    ]
    return build("chain_strike", rig, keys, meta={"layer": "full", "contact": 2 / 30,
                                                   "note": "keyed: the haul's landing blow, two-handed"})
'''
old_all = '''

ALL = (("vault", vault), ("vault_back", vault_back), ("bull_rush", bull_rush))'''
assert old_all in s
s = s.replace(old_all, haul + '''

ALL = (("vault", vault), ("vault_back", vault_back), ("bull_rush", bull_rush), ("chain_haul", chain_haul),
       ("chain_strike", chain_strike))''')
s = s.replace('from clips.sword import GUARD, _n, guard_l\n', 'from clips.axe import GUARD as AXE_GUARD\nfrom clips.sword import GUARD, _n, guard_l\n')
p.write_text(s)
print('ok')
