p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-af551cacc6292152f\tools\creatures\boar_build.py"
s = open(p, encoding="utf-8").read()
b = s.index("STAGES = {")
new = open(r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\boar\new_rig.py", encoding="utf-8").read()
s = s[:b] + new + s[b:]
s = s.replace('''STAGES = {"prep": stage_prep, "form": stage_form, "low": stage_low, "dress": stage_dress, "bake": stage_bake}''',
              '''STAGES = {"prep": stage_prep, "form": stage_form, "low": stage_low, "dress": stage_dress, "bake": stage_bake,
          "rig": stage_rig, "export": stage_export}''')
open(p, "w", encoding="utf-8").write(s)
c = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-af551cacc6292152f\tools\creatures\boar_config.py"
t = open(c, encoding="utf-8").read()
t = t.replace('''        "lean": 40, "splay": 18, "bend": 25, "width": 0.07, "tuft": 5,
    },
}''', '''        "lean": 40, "splay": 18, "bend": 25, "width": 0.07, "tuft": 5,
    },
    # The skeleton's joints (left side; quadruped.build_armature).
    "rig": dict(
        pelvis=(0, 0.44, 0.68), spine1=(0, 0.30, 0.70), spine2=(0, 0.08, 0.72), chest=(0, -0.18, 0.74),
        neck1=(0, -0.26, 0.73), neck2=(0, -0.35, 0.72), head=(0, -0.44, 0.70), snout=(0, -0.62, 0.52),
        snout_end=(0, -0.80, 0.40), jaw=(0, -0.50, 0.50), jaw_end=(0, -0.74, 0.38),
        ear=(0.12, -0.47, 0.82), ear_end=(0.2, -0.43, 0.92),
        tail1=(0, 0.58, 0.74), tail2=(0, 0.66, 0.70), tail3=(0, 0.68, 0.56), tail_end=(0, 0.67, 0.43),
        scapula=(0.13, -0.22, 0.80), shoulder=(0.15, -0.30, 0.55), elbow=(0.15, -0.22, 0.38),
        carpus=(0.145, -0.28, 0.20), fetlock=(0.145, -0.29, 0.09), front_toe=(0.145, -0.37, 0.01),
        hip=(0.13, 0.40, 0.64), stifle=(0.14, 0.34, 0.42), hock=(0.13, 0.52, 0.23),
        hind_fetlock=(0.13, 0.50, 0.10), hind_toe=(0.13, 0.42, 0.01),
    ),
    # The bones' height in the game (Beasts.cs's Height): what the bake
    # scales the skeleton's span of joints to.
    "game_height": 0.82,
}''')
open(c, "w", encoding="utf-8").write(t)
print("ok")
