# Cinematics: status

Agent a79b6d8c81e14dc63 (succeeded a3058a45eee41d695 on 4 October), branch `worktree-agent-a79b6d8c81e14dc63`. The brief: shooting scripts, boards and animatics for C01 to C14, and the in-engine cinematic player. Pipeline and timeline format: `docs/cinematics/shoot/README.md`. Predecessor's handoff: `docs/handoff/cinematics.md`.

## State (5 October)

- **The Prologue (C01 to C04) is surveyed, wired and playing in the game** (previs). This pass:
  - **C01 is on animation's clips:** she lies curled at the fire's edge (`lie_side_wake`), comes up onto her elbow, kneels back on her heels (`sit_back_heels`), and holds her hand to the coals (`reach_coals`, now shot 6a after the kneel). Every face shot is reframed on her bones; her looks are head turns.
  - **C02 and C03 play the Warden's Kimodo and keyed clips** (animation's `folk/m_rise_stiff`, `m_bend_lift`, `m_kneel_lamp`, `m_lamp_down`, `m_fold_forward`). He now falls forward at her feet, so the heart rises from his chest nearer her.
  - **C04 B is checked at full size and reframed.** The tower's lamp is the keeper's lamp-iron (the Warden's pattern) on the sill; at B4a it goes out and a thread of smoke climbs the glass. B1's crane starts at 12 m, the only height where the tower shows over the roofs. B4 is over Rook's shoulder, with the survivor and the tower on one line. B4b is Rook's single.
  - **Gestures are laid over her:** the nod (C03 3b), the shiver (C04 A5) and the exhale (C01 8).
- **The player's new cues:** `head` (a look with the neck and head, kept level, the body left as it is; `HeadTurn`), and `glow` with `lantern` / `out` / `smoke`.
- **The Warden's look, until his own model:** his hood and mantle are dyed dark (they read white); his lamp hangs plumb from his fist on a bail (it floated under it); the heart is a faceted stone with the light inside, not a white ball.
- **C10, C11 and C13 follow the approved boss redesign.** The spent boss and her choice are play, and the cinematic starts from them. The hook ids and the marks a fight passes are in `docs/cinematics/README.md` 11a. Combat's successor has the two requests (marks; `c10_spared` at the choice) in its handoff, §4.3.
- **Boards are drawn over the engine's own frames** (`boards.py`, `"from": "staging"`). C02's are remade; C01, C03 and C04 follow.

## Next, in order

1. Finish the board remakes: C01, C03, C04 A and C04 B over the new staging, and C02's s3, s5, s7, s8 and s11 again (the lamp now hangs in his fist). Look at every one at full size.
2. Recut the Prologue animatic (`animatics/prologue.txt`; C01's shot 4 is now 6a).
3. Check the Prologue with the male hero (`--sex male --body hero`): every face camera should hold on his bones; his clips (`him/`) need C01's three.
4. C02's and C03's line choices (handoff Next 6), then C07 and C09.
5. C10 to C13's timelines once their fights and places are built.

## Key decisions

- **The engine's frame is the staging truth; boards are drawn over it.** God of War's team previs'd first and boarded second; ours does the same in the engine, so scale and lens match the surveyed cameras.
- **Cameras aim at bones, not heights** (Baldur's Gate 3's adaptive cameras): a face shot follows the body it is given.
- **Looks are head turns.** A turn of the whole body on its knees read as a statue on a turntable.
- **The cinematic owns the boss's body while it plays,** and the fight takes him back at the cinematic's end mark. A spared part plays at the choice and owns his going.
- **The tower lamp is the Warden's lamp-iron with an ordinary warm flame:** the eye can tie Vonnra to the keepers before anyone says so.

## Blockers and notes for others

- **Heavy work takes turns** (`tools/turn.py`); renders queue behind other leads' jobs. `boards.py` and my previs runs take and give their turns.
- **Animation:** still to come: the Warden's `lie_arm_up` and `wade_drag`; Grimtunnel's burst, sniff and dive; C04's `wade_out`, `flask_drink`, `walk_uphill` and `unfold_arms`; C01's `letter` and `kneel_to_stand_snap`.
- **Set:** the camp's tripod legs cut across C01's shots 5 and 6; a lower tripod, or a hook on a stake, would free them.
- **Face:** `mouth_open` above 0.15 shows the teeth as a grin in C01's close-ups.
- **Voice:** none needed. No new placeholders.
