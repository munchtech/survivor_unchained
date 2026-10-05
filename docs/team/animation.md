# Animation: status

Agent a7dd95d00c4a6a017, branch `worktree-agent-a7dd95d00c4a6a017` (took over from a03acf30b3e9bdd70 on 5 October). Brief: `docs/handoff/animation.md`.

## State (2026-10-05)

**The owner's wrist and natural-motion pass: the systemic causes are fixed and every library has been rebuilt.**
- **What was wrong:** the same faults ran through her clips, the hero's and the folk's. All of them came from the tools, not from single clips:
  - **Direction keys were blended straight through the sphere.** Two keys pointing far apart passed near nothing between them, and the hand rolled over in one frame.
  - **The hand's aim was read in the wrong frame between keys.** One key aimed it in her space and the next in the chest's, and the frame switched at the nearest key.
  - **Controls a key left out were held from the nearest key that had them.** A blade keyed only at the end turned the hand from the first frame. An aim held on after the hand had moved on left the wrist strained, and it then flipped.
  - **Knuckles-only aims were rebuilt against the forearm's thumb axis,** which flipped wherever the two lined up.
  - **Elbows and knees could bend off their hinge.** The IK's shortest turn left the upper arm's roll anywhere, so the forearm spun and elbows bent sideways.
  - **No anatomical limits:** the wrist twisted up to 100°, with none of the twist in the forearm.
  - **Hand paths cut through the shoulder,** so the elbow whipped from one side to the other.
- **What was done** (`keyed.py`, `held.py`, `gait.py`, `retarget.py`):
  - **Directions turn round the sphere,** and a strike's "fast" no longer flicks the hand's roll.
  - **Every key's aim is made whole and put in one frame before blending.** A hand keyed without an aim lets go of it.
  - **A knuckles-only or blade-only aim is the least turn from how the hand rides the forearm.**
  - **The upper arm and thigh roll so the elbow and knee bend on their hinges.** Through a straight limb the hinge keeps its last direction.
  - **Limits:** the forearm turns up to 95° and the wrist bends up to 70°. Past them the elbow swings round, chosen to be like the last frame, and then the hand falls short. Half the roll goes into the forearm.
  - **The elbow's path is settled over the whole clip and smoothed** (`solve_frames`).
  - **Takes spread the forearm roll** (`retarget.spread_twist`).
  - **Runs swing the fist on an arc about the shoulder,** not a line through it.
- **Clip fixes at the source:**
  - `catch_breath`: the hand turns over on the way up and comes down round the front, not back through the shoulder;
  - `death_back`: the flung arms no longer pass straight, which rolled them over.
- **`audit.py`** checks every clip we make for:
  - a hand or forearm spinning more than 30° about its own length in one frame;
  - the wrist's bend and twist, and the forearm's twist;
  - an elbow or knee bent off its hinge.
- **Audit totals:**
  - before: 9,945 frames flagged; 131 of 185 clips turned a hand more than 30° in a frame, up to 179°;
  - after: 894 frames flagged, mostly the limits' own wrist-twist and bend counts. 13 clips still spin a hand more than 90° in one frame, all at the start of a fast move or in a fall:
    - chain_strike (her and his);
    - cast_bolt;
    - the reaver's and warden's show;
    - the reaver sprints;
    - sword_heavy;
    - vault_back;
    - the folk's die_front.
  - These need re-keying at the start of the move: a hand path through the shoulder, or a roll packed into one frame.
- **Strips:** before and after of the worst five (`run_reaver`, `idle_arcanist_break`, `death_back`, `warden_show`, `f_die_side`), close up and at the game camera. They are in the scratchpad (`anim4/sh/ba_*.png`).
- **The numbers are not the verdict.** `warden_show` passes the audit better but looks worse: the sword arm now comes up across her face in the hold. It is flagged below; don't pass it.

## Sign-off log (sceptical: guilty until shown natural)

Each line says what was checked, what was fixed, and the verdict. "Audit" is `tools/anim/audit.py`. "Ground" is the contact check: nothing through the ground, and knees and forearms on it where they bear weight. The only real-motion reference available is the 100STYLE captures, which back the idles and walks. No video was used: the web isn't ours to use.

| Clip(s) | Checked | Fixed | Verdict |
|---|---|---|---|
| flask_drink (C04 A6) | Audit; hand on the lips per frame; the cinematic at both cameras | The hands are placed by the flask | Good. Needs the flask prop and the camera move |
| lie_side_wake, sit_back_heels, reach_coals (C01) | Ground; audit; sheets | Remade: knees and forearm through the ground; a prop hand that jumped | Good on sheets; to judge in C01 |
| letter, kneel_to_stand_snap, take_from_log, cup_hands | Ground; audit; sheets | The snap's knees cleared; the cup turned palm up | Good on sheets; to judge in C01 |
| walk_tired, walk_uphill, wade | 100STYLE capture; audit; sheets | — | Good |
| catch_breath | Audit; frame trace | Re-keyed the rise and fall of the hand | Good by numbers; re-sheet |
| death_back | Audit | Arms kept from passing straight | Fair: a violent fall, 45–65° a frame over 3 frames |
| Strikes (sword_*, axe_*, axes_*, daggers_*) | Audit | Systemic fixes | The cuts roll 40–56° a frame for 3–4 frames: fast but even. Judge at speed in the game |
| Runs | Audit; close-up strip | Arc swing; systemic fixes | Good |
| Sprints (reaver) | Audit | — | **Flagged:** up to 97° a frame at f3; re-key |
| idle_arcanist_break | Audit; strips | The tuck re-keyed (up before the shoulder, then back over the ear) | Good by numbers; re-sheet |
| warden_show | Strips | — | **Regressed:** the sword arm comes up across her face in the hold. Re-key its pole and blade, or restore the old look |
| chain_strike, cast_bolt, sword_heavy, vault_back, reaver_show | Audit | — | **Flagged:** one-frame rolls at the move's start; re-key |
| Hero library | Audit | Rebuilt with the fixes | Same as hers. His body is pending (male hero lead) |
| Folk slam (armed) | Audit | The axe swung up in front of the shoulder | Good by numbers |
| Folk die_front | Audit | — | **Flagged:** up to 164° a frame; re-key |
| Folk rally, kneel, lurch, walks | Audit | Rebuilt | Good by numbers |

## Next

1. **Finish the wrist pass:**
   - re-key the flagged clips above, `warden_show` first;
   - judge the strikes at speed in the game (`--on casts`);
   - send the strips to the coordinator.
2. Re-judge the C01 and C04 clips in their cinematics once cinematics blocks them in.
3. The Warden's `wade_drag` (made: 100STYLE Heavyset over his body, the lamp up, the sword trailing; to judge in C02) and `lie_arm_up` (made).
4. Grimtunnel's four, and the lampling's slam (`Beasts.cs`).
5. The chain haul's landing crouch, and a heavier running flinch.
6. The male hero's library; the boar's clips on the creatures lead's rig (af551cacc6292152f).

## Waiting on others

- **Combat (a5115633c7006e4d4, handed off):** the plants (0.65 s and 0.7 s) and the kerchief_crossbow repoint are on their branch (3760c299). Check them in the game with `--on casts` once merged.
- **Cinematics (successor of a79b6d8c81e14dc63):**
  - block the C01 clips;
  - A6's cues, camera and props (the flask, its cork and the letter need small builders);
  - the Warden's C02 and C03 cues, and the heart's move.

## Key decisions

- **Fix motion at its source.** A flip is mended in the tool that makes it, or in the clip's keys. A second correction is never laid over the result.
- **Contacts are measured** (`held.py`, `ground.py` in scratch). Her arms are short for her legs: when kneeling, her hands can't reach the ground.
- **A cinematic clip is staged for its camera.** A6's drink is right-handed, so the camera goes to her left.
- Earlier decisions stand: the slam and the kneel are roles of their own; blows land on a frame the bake samples; takes that don't fit are rejected.
