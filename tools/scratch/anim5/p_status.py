from pathlib import Path
p = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274\docs\team\animation.md")
t = p.read_text(encoding="utf-8")
E = [
    ('''| Strikes (sword, axe, axes, daggers) | Audit; close sheet of sword_fore | The grip's lean; the wrist's range | Good on the close sheet (was 80 toward the little finger). The cuts still roll the hand 60 to 87 degrees in one frame (sword_heavy, sword_fore, the hero's axes): to judge at the game camera |''',
     '''| Strikes (sword, axe, axes, daggers), casts, throw, vault_back | Audit; close sheet of sword_fore; all at the arena camera at 1.6 times (`anim5/sh/strikes_all_s1.png`) | The grip's lean; the wrist's range | Good: the arcs read, no flip shows at the game camera. The cuts roll the hand 60 to 87 degrees in a frame for one or two frames, which is a cut |'''),
    ('''| C01 clips (cup_hands, letter, reach_coals, sit_back_heels, lie_side_wake, kneel_to_stand_snap, take_from_log) | Audit; ground | Rebuilt: hands keyed past a wrist's range now fall short | **To re-judge on sheets.** lie_side_wake's forearm 9 cm into the ground (the hero's 19); sit_back_heels' toes 8 |''',
     '''| C01 clips (cup_hands, letter, reach_coals, sit_back_heels, lie_side_wake, kneel_to_stand_snap, take_from_log) | Audit; ground; sheets (`anim5/sh/c01_all_s1.png`) | Rebuilt; lie_side_wake's forearm brought to the ground sooner | Fair on sheets; to judge in C01. lie_side_wake's elbow dips 5 cm for 3 frames (was 9 for 6; **the hero's 16**: his body is pending); sit_back_heels' toes 8 cm |'''),
    ('''| leap | Ground | — | **Flagged:** a knee 10 cm into the ground at the landing (a retargeted take) |''',
     '''| leap | Ground | Retargeted takes keep knees and seats out of the ground (`retarget.retarget`: the hips lifted, the legs re-reached for the planted ankles) | Good: the landing knee on the ground (was 10 cm in). The toes 4 cm at the spring |'''),
    ('''- **`audit.py`** also flags a wrist bent past its range. Totals: 894 flagged frames before this round (without the range check), **229 now with it**; one clip spins a hand over 90 degrees in a frame (the hero's `chain_strike`, 106, at the blow).''',
     '''- **`audit.py`** also flags a wrist bent past its range. Totals: 894 flagged frames before this round (without the range check), **231 now with it**; one clip spins a hand over 90 degrees in a frame (the hero's `chain_strike`, 106, at the blow).
- **Ground:** retargeted takes keep knees and seats out of the ground. Left: toes 3 to 8 cm into it in some folk takes and sit_back_heels.'''),
    ('''1. Judge the strikes at the game camera (`anim_review` at `VIEW=arena PLAY=1.6`); re-judge the C01 clips on sheets; leap's landing.
2. C01 and C04 in their cinematics; Grimtunnel's four and the lampling's slam (`Beasts.cs`); the chain haul's landing crouch and a heavier running flinch; the male hero's library.''',
     '''1. C01 and C04 in their cinematics, once blocked.
2. Grimtunnel's four and the lampling's slam (`Beasts.cs`); the chain haul's landing crouch and a heavier running flinch.
3. The male hero's library when his body lands (his chain_strike and lie_side_wake are flagged).
4. Toes through the ground (a toe clamp in `retarget`).'''),
]
for a, b in E:
    assert t.count(a) == 1, a[:60]
    t = t.replace(a, b)
p.write_text(t, encoding="utf-8")
print("ok")
