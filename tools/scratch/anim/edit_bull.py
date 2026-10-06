from pathlib import Path
p = Path(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa4f5fc266b043035\tools\anim\clips\arts.py')
s = p.read_text()
s = s.replace('''from clips.actions import arm, body
from keyed import build
''', '''from dataclasses import replace

from clips.actions import arm, body
from clips.run import WARDEN
from clips.sword import GUARD, _n, guard_l
from gait import arc_of, pose_at
from keyed import build
''')
s = s.replace('''- vault_back: standing, she springs 6 m back from where she faces, eyes on
  what she escapes: a tucked back spring into a low three-point landing,
  one hand on the ground, the blade hand swept out behind.
''', '''- vault_back: standing, she springs 6 m back from where she faces, eyes on
  what she escapes: a tucked back spring into a low three-point landing,
  one hand on the ground, the blade hand swept out behind.
- bull_rush: 9 m in 0.4 s behind her shield: one driving stride cycle,
  pitched hard over it, the left shoulder and the shield leading, the
  sword cocked low behind; then the lead foot planted, the shield punched
  out, and the rebound into her guard.
''')
bull = '''

# ------------------------------------------------------------- bull rush --
def _shield_charge(ph, k, hand):
    """The shield square before her face and chest, riding the stride."""
    bounce = 0.02 * math.cos(4 * math.pi * ph)
    return {"arc": arc_of((-0.16, -0.04 + bounce, 0.32)), "pole": (1.0, -0.2, -0.2), "frame": "chest",
            "blade": _n(-0.15, 0.8, 0.55), "twist": 0.3}


def _sword_cocked(ph, k, hand):
    """The sword low behind her, edge trailing, ready to come through."""
    sway = 0.03 * math.cos(2 * math.pi * ph)
    return {"arc": arc_of((-0.10, -0.32, -0.16 + sway)), "pole": (-0.6, 0.3, 0.4), "frame": "chest",
            "blade": _n(-0.3, 0.45, -0.85), "twist": 0.5}


CHARGE = replace(WARDEN, frames=12, speed=4.4, duty=0.3, drop=0.13, bob=0.06, lean=36, spine_lean=6, hip_yaw=8,
                 hip_roll=3, chest_yaw=4, reach=0.44, kick=0.46, knee=0.40, shoulders=(8, 8),
                 arms={"l": _shield_charge, "r": _sword_cocked})


def bull_rush(rig):
    keys = []
    for f in range(12):
        pose = pose_at(CHARGE, rig, (f / 12 + 0.25) % 1.0)
        # The left shoulder driving: the chest turned to lead with it, the
        # head down behind the shield's rim.
        sp = pose["spine"]
        pose["spine"] = (sp[0] - 16, sp[1], sp[2])
        pose["head"] = (pose["head"][0] + 12, pose["head"][1] - 4, 0)
        keys.append((f, pose, "linear"))
    shove_l = {"arc": arc_of((-0.10, 0.02, 0.44)), "pole": (1.0, -0.2, -0.3), "frame": "chest",
               "blade": _n(-0.1, 0.85, 0.5), "twist": 0.3}
    sword_up = {"arc": arc_of((-0.18, -0.20, -0.06)), "pole": (-0.7, 0.0, -0.3), "frame": "chest",
                "blade": _n(-0.3, 0.75, -0.55), "twist": 0.5}
    plant = {"foot_l": {"pos": (0.12, 0.0, 0.56), "rot": (10, 0, 0), "pole": (0.2, 0, 1)},
             "foot_r": {"pos": (-0.14, 0.06, -0.46), "rot": (-16, 40, 0), "toe": 40},
             "fingers_l": "fist", "fingers_r": "grip"}
    keys += [
        # The lead foot slams down; the shield punches out, the body behind it.
        (12, body({**plant, "hips": {"pos": (0.02, -0.22, 0.10)}, "hand_l": shove_l, "hand_r": sword_up,
                   "clav_l": (6, 16), "clav_r": (6, -4)},
                  hips=(-12, 22, 0), spine=(-22, 16, 0), neck=(0, -10, 0), head=(18, -18, 0)), "fast"),
        (14, body({**plant, "hips": {"pos": (0.02, -0.24, 0.13)}, "hand_l": {**shove_l, "arc": arc_of((-0.08, 0.04, 0.47))},
                   "hand_r": sword_up, "clav_l": (6, 20), "clav_r": (6, -6)},
                  hips=(-14, 24, 0), spine=(-24, 16, 0), neck=(0, -10, 0), head=(20, -18, 0)), "ease"),
        # The rebound: back up over her feet, shield home, sword raised.
        (19, body({"foot_l": {"pos": (0.13, 0.0, 0.38), "rot": (12, 0, 0)},
                   "foot_r": {"pos": (-0.16, 0.0, -0.24), "rot": (-22, 0, 0)},
                   "hips": {"pos": (0.0, -0.12, 0.04)}, "hand_l": guard_l(0.06),
                   "hand_r": {"arc": arc_of((-0.08, -0.22, 0.12)), "pole": (-0.6, -0.3, -0.6), "frame": "chest",
                              "blade": _n(-0.25, 0.7, 0.65), "twist": 0.5},
                   "fingers_l": "fist", "fingers_r": "grip"},
                  hips=(-6, 6, 0), spine=(-8, 2, 0), neck=(0, -2, 0), head=(8, -4, 0)), "auto"),
        (30, GUARD, "ease"),
    ]
    return build("bull_rush", rig, keys, meta={"layer": "full", "note": "keyed: 0.4 s shield charge, then the plant and shove"})
'''
old_all = '''

ALL = (("vault", vault), ("vault_back", vault_back))'''
assert old_all in s
s = s.replace(old_all, bull + '''

ALL = (("vault", vault), ("vault_back", vault_back), ("bull_rush", bull_rush))''')
s = s.replace('from __future__ import annotations\n', 'from __future__ import annotations\n\nimport math\n', 1)
p.write_text(s)
print('ok')
