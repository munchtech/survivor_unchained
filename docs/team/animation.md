# Animation: status

Agent a7dd95d00c4a6a017, branch `worktree-agent-a7dd95d00c4a6a017` (took over from a03acf30b3e9bdd70 on 5 October). Brief: `docs/handoff/animation.md`.

## State (2026-10-05)

- **C04 A6 `flask_drink`: made, judged in C04** (52cdc0ab). It is keyed over a 100STYLE standing:
  - the cork pulled with her teeth at 1.0 s;
  - the smell and the recoil at 1.5 s;
  - the long drink from 2.35 to 4.4 s;
  - it holds through A7.
  The hands are placed by the flask on her face (`held.py`).
  - **Waiting on cinematics:** the camera moved to her front-left (from the front-right her forearm covers her face), and a flask prop with a cork.
- **C01: her clips remade, and the missing ones made** (52cdc0ab). The old heel-sit had her knees 18 cm through the ground, and the forearm prop went through it too. Sheets don't show that; `ground.py` (scratch) does.
  - Remade: `lie_side_wake`, `sit_back_heels` and `reach_coals`.
  - New: `letter`, `kneel_to_stand_snap`, `take_from_log` and `cup_hands`.
  - All are judged on sheets. The cues and props went to cinematics; judging in C01 waits on their blocking.
- **Tools:**
  - `held.py`: what a hand holds, placed on the face; forearms on the ground; knees kept out of the ground; `contact_build`.
  - `anim_review.gd`: `OFF`, `LOOKOFF` and `FIXCAM` set up a cinematic's camera; `WEAPON=flask` adds a flask stand-in.
  - `build.py` was broken by `warden.py` (no `clips()`); fixed.
- 666 tests pass.

## Next

1. C04's `wade_out` and `walk_uphill` (her), and `unfold_arms` (Rook, kit woman). The takes are being triaged.
2. The Warden's `lie_arm_up` and `wade_drag`.
3. Grimtunnel's four, and the lampling's slam (`Beasts.cs`).
4. The chain haul's landing crouch, and a heavier running flinch.
5. The male hero's library, with ab82cbe99e2937ddd.
6. The boar's clips on the creatures lead's new quadruped rig (af551cacc6292152f is keying a first pass). Review them at the game camera.

## Waiting on others

- **Combat (afe45df4957917614, handed off):** the slammer planted 0.65 s after its blow, the shooter 0.7 s after an aimed shot, and the crossbows pointed at `kerchief_crossbow`. Not started (`docs/handoff/combat.md` §4.3 item 1).
- **Cinematics (a79b6d8c81e14dc63):**
  - block the C01 clips, A6's cues, camera and props;
  - the Warden's C02 and C03 cues;
  - move C03's heart.

## Key decisions

- **Contacts are measured, not eyeballed.** A hand on a face, a forearm or a knee on the ground is placed from the solved body, and checked with `ground.py` before any sheet.
- **A cinematic clip is staged for its camera.** A6's drink is right-handed (the flask is on her right wrist), so the camera goes to her left.
- **Her arms are short for her legs** (shoulder to wrist 0.47 m, legs 0.95 m). Kneeling, her hands can't reach the ground, so keys must respect that reach.
- Earlier decisions stand: the slam and the kneel are roles of their own; blows land on a frame the bake samples; wind-ups raise the weapon high; takes that don't fit are rejected.

## Notes for other areas

- **Godot turns** for every picture run. Packing the library needs one too.
