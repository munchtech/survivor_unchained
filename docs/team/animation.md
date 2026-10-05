# Animation: status

Agent: the successor of a7dd95d00c4a6a017 (this session), branch `worktree-agent-aa15f092820132274` (took over on 5 October). Brief: `docs/handoff/animation.md`.

## State (2026-10-05)

**The wrist pass, second round: a wrist now bends as a wrist does, and weapons sit in the hand as they are held.**
- **What was still wrong** (the owner's "reverse weird wrist motions ... attempting to correct"):
  - **The wrist could bend 80 degrees sideways.** The solver had one limit for any bend. A wrist bends far toward the palm and back (about 80 and 70), but little to either side (about 25 toward the thumb, 40 toward the little finger). 8,899 frames across 165 clips were past that.
  - **Weapons sat square across the fist.** A sword's grip runs from the root of the forefinger to the heel of the hand, so the blade leans toward the fingers. Held square, every guard and cut needed the wrist kinked 60 to 80 degrees toward the little finger (the idle warden held it so all the time).
  - **The runs asked for the impossible.** The sword was keyed up over her shoulder behind her, so the hand flapped from 80 degrees one way to 60 the other every stride (`anim5/sh/wr_run_cur.png`).
- **What was done:**
  - **Anatomical wrist limits** (`keyed.Rig`): flexion 75, extension 65, toward the thumb 22, toward the little finger 38, read on the wrist's own axes (they turn with the forearm). The elbow swings round to meet them; past that the hand falls short. Retargeted takes are held to the same range (`retarget.keep_wrists`).
  - **The diagonal grip** (`keyed.GRIP`, `Arms.Spec.Lean`): swords 35 degrees, axes, daggers, mace and wand 30, staff and crossbow square. Her and the hero only (`Rig.grips`; `Arms.Hold` for people with their own clips): the folk also play the library's clips, held square. The game, the review scene and the solver use the same lean. A clip's `meta.weapon` sets it.
  - **A `thumb` control:** the wrist left straight and the forearm rolled so the thumb side faces a way. A carried weapon goes where the arm takes it.
  - **Re-keyed at the source:** the runs and sprints (the sword hand at her side and ahead, the blade out and forward; a sprint's arm no longer flung straight behind her); `warden_show`; `bull_rush`'s rebound; `chain_strike`'s blow (a frame for the axe to come down, contact 3/30); `cast_raise` (the staff across overhead, then upright in both fists); the reaver's twirl; the folk's `die_front`.
  - **Her fall** (the coordinator's report from the UI shot): the `death` knees went 17 cm into the ground and the shield stood on its edge 18 cm deep; `get_up`'s knees 17 cm. Re-keyed: the knees rest on the ground, the shield lies face up, the blade flat. **And she never fell at a story fall:** `StoryNight.OnFall` holds her at a breath of life, so the view kept her standing. `PlayerView.Fall()` (called from `GameFall.StoryFall`) puts her down, and `Revive()` (from `GetUp`) brings her up with `get_up`.
- **`audit.py`** also flags a wrist bent past its range. Totals: 894 flagged frames before this round (without the range check), **231 now with it**; one clip spins a hand over 90 degrees in a frame (the hero's `chain_strike`, 106, at the blow).
- **Ground:** retargeted takes keep knees and seats out of the ground. Left: toes 3 to 8 cm into it in some folk takes and sit_back_heels.

## Sign-off log (sceptical: guilty until shown natural)

"Audit" is `tools/anim/audit.py`; "blade" is scratch `blade.py` (a held blade never through her); "ground" is scratch `groundall.py` (nothing more than 3 cm into the ground).

| Clip(s) | Checked | Fixed | Verdict |
|---|---|---|---|
| warden_show | Audit; blade; sheets front, three-quarter, side, close | Re-keyed: the sword raised overhand, the elbow out, the point down over the rim at you; chin up, eyes over the rim | Good on sheets: face clear, arm beside her head. To judge at the creation screen |
| run_warden, sprint_warden | Audit; blade; the hand close every frame; side | The thumb carry; the hand at her side | Good: the wrist straight through the stride (was 80 one way, 60 the other) |
| Other runs and sprints | Audit; blade; sheets | The thumb carry; the sprint's arm kept bent | Good by numbers (sprint_reaver was 97 degrees in a frame) |
| Strikes (sword, axe, axes, daggers), casts, throw, vault_back | Audit; close sheet of sword_fore; all at the arena camera at 1.6 times (`anim5/sh/strikes_all_s1.png`) | The grip's lean; the wrist's range | Good: the arcs read, no flip shows at the game camera. The cuts roll the hand 60 to 87 degrees in a frame for one or two frames, which is a cut |
| Idles and breaks | Audit; close sheet (idle_warden) | The grip's lean; the reaver's twirl re-keyed | Good (idle_warden was 66 toward the little finger, always). The twirl rolls 36 a frame: it is a twirl |
| death, get_up | Ground; shield facing; sheets at the arena camera and the side | Knees, shield, blade | Good on sheets; to see in a story fall in the game |
| death_back | Ground; sheet at the arena camera | — | Fair: the shield's edge 5 cm into the ground |
| bull_rush, chain_strike, cast_raise | Audit; blade | Re-keyed | Good by numbers (were 136, 162, 132 degrees in a frame) |
| Folk die_front (and armed, pistol) | Audit; ground | The fall's arms; the shield arm lies as it falls | Good by numbers (was 164) |
| C04 flask_drink | Contact (spout to lips) | Rebuilt | Holds: the spout within 1.4 cm of her lips through the drink |
| C01 clips (cup_hands, letter, reach_coals, sit_back_heels, lie_side_wake, kneel_to_stand_snap, take_from_log) | Audit; ground; sheets (`anim5/sh/c01_all_s1.png`) | Rebuilt; lie_side_wake's forearm brought to the ground sooner | Fair on sheets; to judge in C01. lie_side_wake's elbow dips 5 cm for 3 frames (was 9 for 6; **the hero's 16**: his body is pending); sit_back_heels' toes 8 cm |
| leap | Ground | Retargeted takes keep knees and seats out of the ground (`retarget.retarget`: the hips lifted, the legs re-reached for the planted ankles) | Good: the landing knee on the ground (was 10 cm in). The toes 4 cm at the spring |
| The hero's chain_strike | Audit | — | **Flagged:** the blow spins his hand 106 degrees in a frame. His body is pending; fix with his rebuild |
| Folk arms_crossed, talk (retargeted) | Audit | Held to the wrist's range | The tucked hand toward the thumb 35 before; to re-audit |

## Next

1. C01 and C04 in their cinematics, once blocked.
2. Grimtunnel's four and the lampling's slam (`Beasts.cs`); the chain haul's landing crouch and a heavier running flinch.
3. The male hero's library when his body lands (his chain_strike and lie_side_wake are flagged).
4. Toes through the ground (a toe clamp in `retarget`).

## Notes for other areas

- **Combat and skills VFX:** her and the hero's swords, axes, daggers, mace and wand sit 30 to 35 degrees leaned in the fist (`Arms.Spec.Lean`, people with their own clips only). Anything reading a weapon's tip from its mount follows it.
- **Experience and UI:** at a story fall she now goes down (`PlayerView.Fall`) and gets up at the rise (`Revive`). The UI's build7 fall shot was a run as the male hero (green): `--sex female` for her.
- **Cinematics:** C01 and C04 clips were rebuilt; the hands are in the same places, turned within a wrist's reach. `chain_strike`'s contact moved to 3/30.

## Key decisions

- **Fix motion at its source.** A flip or a strained wrist is mended in the tool or the clip's keys, never with a correction laid over the result.
- **A wrist is not a ball joint.** Its range is anisotropic and read on its own axes; the forearm's roll carries them.
- **Weapons are held as people hold them** (the diagonal grip), in the solver and the game alike.
- **Contacts are measured** (`held.py`, scratch `ground.py`, `groundall.py`). Her arms are short for her legs.
- **A cinematic clip is staged for its camera.**
