# Animation: status

Agent: ae2a9884e3e51609c (7 October), branch `worktree-agent-ae2a9884e3e51609c`; handed off at about 320k. Brief and handoff: `docs/handoff/animation.md`.

## State (2026-10-07)

**Her helper bones: built, seen at 1:1, one fault found and fixed in the spec; still off (no `--helpers` by default).**
- The first build (shares cut as a tent) fixed the pinched elbows, shoulders and wrung forearms, but brought her knee to a sharp point at 120-145 degrees and the elbow to a knob from behind. Now cut as a quadratic Bezier (`helpers.split`, "smooth") with a stretch of 2 - cos(bend/2) (`helpers.bulge`, `HerJoints.cs`): rounded, fuller than before, no point (`anim_sheets/helpers_split_knee_elbow.png`).
- Volume kept, before -> now: elbow 90/120/145 73/61/54 -> 83/70/56; knee 75/65/59 -> 89/82/73; arm raised 130 72 -> 92; forearm turned 80, wrist 95 -> 100.
- Owed: the face lead's sign-off on her head's carry in play (handoff step 3).

## Next

1. Rebuild with the smooth split, see it at 1:1 in motion in every outfit, rerun the garment check (`tools/scratch/anim6/gapcheck.py`), then helpers on by default and the outfits lead (a1f120018d8749c97) rebuilds and reruns the motion check.
2. The head carry sign-off (HerCarriage.Level through rolls, leaps and get-ups).
3. The full audit of her and the hero, then the solver (arm clearance, follow-through, foot locking) and in the game (stride, walk cycle, foot lock).

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
