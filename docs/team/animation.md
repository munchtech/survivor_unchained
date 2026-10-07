# Animation: status

Agent: a9a80800a7dae2519 (6 October), branch `worktree-agent-a9a80800a7dae2519`; paused. Brief and handoff: `docs/handoff/animation.md`.

## State (2026-10-06, paused by the wind-down)

**The owner's joint notes (OWNER_NOTES, 6 October): measured, and the skinning fix built but off.** Agent a9a80800a7dae2519; handoff `docs/handoff/animation.md`.
- **Measured** (`tools/anim/motion.py`, on her actual mesh with her springs; 6 clips so far):
  - elbows keep 70% of their volume at 90 degrees and 59% at 120; 67-80% in clips; the knee 66% in the run;
  - forearm roll at the elbow 25-48 degrees;
  - run_warden's left arm 11-15 mm into her chest; her hands pass through each other (shield-hidden);
  - warden_show's foot glides 23 cm;
  - in the game, every start, stop and turn slides (no walk cycle, no foot lock).
- **Root cause of the pinching:** the rig's twist and share bones were folded away when her body was built.
- **Built (off until checked):** twist and share bones (`tools/anim/helpers.py`, `tools/assets/heroine_rig.py`, the outfits build's `--helpers`), driven by `HerJoints.cs`. In the Python prototype, elbows keep 94% at 90 degrees and 83% at 120; wrists 98-100% under a turn.

## Next

1. Build her body with `--helpers`, check it at 1:1, then turn it on. The outfits lead rebuilds and reruns the motion check.
2. The full audit of her and the hero, then the solver: arm clearance against her mesh, follow-through down the arm, foot locking; in the game, a walk cycle and a runtime foot lock.
3. The earlier list (C01 and C04 in their cinematics, Grimtunnel's roles, the hero's library) after the joints.

## Sign-off log (sceptical: guilty until shown natural)

"Audit" is `tools/anim/audit.py`; "blade" is scratch `blade.py` (a held blade never through her); "ground" is scratch `groundall.py` (nothing more than 3 cm into the ground).

| Clip(s) | Checked | Fixed | Verdict |
|---|---|---|---|
| warden_show | Audit; blade; sheets front, three-quarter, side, close | Re-keyed: the sword raised overhand, the elbow out, the point down over the rim at you; chin up, eyes over the rim | **Reopened (6 Oct):** her left foot glides 23 cm flat on the floor (frames 8-16) |
| run_warden, sprint_warden | Audit; blade; the hand close every frame; side | The thumb carry; the hand at her side | **Reopened (6 Oct):** the wrist is good; her left upper arm goes 11-15 mm into her chest, and her hands pass through each other in front of her (shield-hidden) |
| Other runs and sprints | Audit; blade; sheets | The thumb carry; the sprint's arm kept bent | Good by numbers (sprint_reaver was 97 degrees in a frame) |
| Strikes (sword, axe, axes, daggers), casts, throw, vault_back | Audit; close sheet of sword_fore; all at the arena camera at 1.6 times (`anim5/sh/strikes_all_s1.png`) | The grip's lean; the wrist's range | Good: the arcs read, no flip shows at the game camera. The cuts roll the hand 60 to 87 degrees in a frame for one or two frames, which is a cut |
| Idles and breaks | Audit; close sheet (idle_warden) | The grip's lean; the reaver's twirl re-keyed | Good (idle_warden was 66 toward the little finger, always). The twirl rolls 36 a frame: it is a twirl |
| death, get_up | Ground; shield facing; sheets at the arena camera and the side | Knees, shield, blade | Good on sheets; to see in a story fall in the game |
| death_back | Ground; sheet at the arena camera | — | Fair: the shield's edge 5 cm into the ground |
| bull_rush, chain_strike, cast_raise | Audit; blade | Re-keyed | Good by numbers (were 136, 162, 132 degrees in a frame) |
| Folk die_front (and armed, pistol) | Audit; ground | The fall's arms; the shield arm lies as it falls | Good by numbers (was 164) |
| C04 flask_drink | Contact (spout to lips) | Rebuilt | Holds: the spout within 1.4 cm of her lips through the drink |
| C01 clips (cup_hands, letter, reach_coals, sit_back_heels, lie_side_wake, kneel_to_stand_snap, take_from_log) | Audit; ground; sheets (`anim5/sh/c01_all_s1.png`) | Rebuilt; lie_side_wake's forearm brought to the ground sooner | Fair on sheets; to judge in C01. lie_side_wake's elbow dips 5 cm for 3 frames (was 9 for 6; **the hero's 16**: his body is pending); sit_back_heels' toes 8 cm |
| flinch (new, a gesture) | Sheets over a run and a cut, three-quarter and the arena camera | New: laid over a run or a blow (`PlayerView`, when moving or busy); standing, the upper-body hit as before | Good on sheets: the chest caves, the head snaps back, the legs keep running and the arms their hold |
| leap | Ground | Retargeted takes keep knees and seats out of the ground (`retarget.retarget`: the hips lifted, the legs re-reached for the planted ankles) | Good: the landing knee on the ground (was 10 cm in). The toes 4 cm at the spring |
| The hero's chain_strike | Audit | — | **Flagged:** the blow spins his hand 106 degrees in a frame. His body is pending; fix with his rebuild |
| Folk arms_crossed, talk (retargeted) | Audit | Held to the wrist's range | The tucked hand toward the thumb 35 before; to re-audit |

## Notes for other areas

- **Outfits:** her helper bones come in through `heroine_outfits.py`'s `--helpers` (off for now). The split is the same field for skin and every garment. The motion check needs nothing more: `lookdev.gd` adds HerJoints.

- **Combat and skills VFX:** her and the hero's swords, axes, daggers, mace and wand sit 30 to 35 degrees leaned in the fist (`Arms.Spec.Lean`, people with their own clips only). Anything reading a weapon's tip from its mount follows it.
- **Experience and UI:** at a story fall she now goes down (`PlayerView.Fall`) and gets up at the rise (`Revive`). The UI's build7 fall shot was a run as the male hero (green): `--sex female` for her.
- **Cinematics:** C01 and C04 clips were rebuilt; the hands are in the same places, turned within a wrist's reach. `chain_strike`'s contact moved to 3/30.

## Key decisions

- **Fix motion at its source.** A flip or a strained wrist is mended in the tool or the clip's keys, never with a correction laid over the result.
- **A wrist is not a ball joint.** Its range is anisotropic and read on its own axes; the forearm's roll carries them.
- **Weapons are held as people hold them** (the diagonal grip), in the solver and the game alike.
- **Contacts are measured** (`held.py`, scratch `ground.py`, `groundall.py`). Her arms are short for her legs.
- **A cinematic clip is staged for its camera.**
