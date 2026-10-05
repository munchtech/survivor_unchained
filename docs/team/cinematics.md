# Cinematics: status

Agent a79b6d8c81e14dc63 (succeeded a3058a45eee41d695 on 4 October), branch `worktree-agent-a79b6d8c81e14dc63`. The brief: shooting scripts, boards and animatics for C01 to C14, and the in-engine cinematic player. Pipeline and timeline format: `docs/cinematics/shoot/README.md`. Predecessor's handoff: `docs/handoff/cinematics.md`.

## State (4 October)

- **C04 B is checked at full size and reframed** (`shoot/c04b.md`):
  - the toll tower's lamp is the keeper's lamp-iron (the Warden's pattern) standing on the window's sill (mark `lamp`); at B4a it goes out and a thread of smoke climbs the glass (`glow` `lantern`, `out`, `smoke`);
  - B1's crane starts at 12 m, the only height from the gate where the tower and its lamp show over the roofs;
  - B4 is over Rook's shoulder with the survivor and the tower on one line; B4b is now Rook's single (the reverse).
- **The Warden's hood no longer reads white.** His dye is measured against brighter paint in `WardenView`, so the hood and mantle come out dark under the moon. His own model is still to come.

- **C02 to C04 are surveyed and wired into the game** (previs pass 1, stand-in motion):
  - **C02** plays at the ford in place of `RunIntro`. It has its own Warden (a `boss` cast): he lies under the river with his lamp held up, rises, wades to her and lifts the lamp. The drowned are `extras` that turn in a wave. `warden_up` spawns the fight's Warden on `warden_end`, facing her.
  - **C03** plays where he falls, in place of `RunVictory`'s staging. The zone passes marks `w` and `her`; she is put 4 m south of him. Grimtunnel is spawned by the cinematic and burrowed by the zone's events; the heart is an `orb` cast. `Taken()` and `Dawnbreak()` run at the hand-back, so a skip sets them too. The dawn is begun to 0.2 and held there.
  - **C04 A** plays when she reaches the north bank (or 25 s after C03), with a south variant (fact `prologue.dawn_south`). Its `douse` event calls `Douse(false)`.
  - **C04 B** plays on the first Waystation arrival, in place of the caption and the zone title. It has its own Rook; the zone's is hidden by `rook_cine`.
  - Tests cover C02's wiring both ways. The Prologue tests still pass without a screen.
- **Player additions:** `boss`, `extras` and `orb` casts; a `lamp` cue; `tilt` on `place`; a `light` on `glow`; free moves to `abs`; tagged and neutral spawns; part-way atmosphere blends (`k0`, `k1`); `--stills N` for motion checks. Name plates and barks are hidden during cinematics. LayToIdle no longer loops. The Warden's lamp is now an open cage with a visible flame.
- **Shooting scripts** for C02, C03, C04 A and C04 B are written from the timelines as they play (`shoot/c02.md` to `c04b.md`).
- **C03's sounds** (`kneel_water`, `sink`, `lamp_out`, `heart_hum`, `burst`, `sniff`, `groan`) are made in `Sfx.Cine` and the animatic.
- **Subtitles:** lower-case (directions) are stripped and "sung" sets italics (agreed with story, bfecf70).
- **The animatic was watched through:** about 35 of 54 boards are weak (the list is under Next).

## Next, in order

1. The C10, C11 and C13 changes from the approved boss redesign (see Incoming), with the combat lead's hook ids.
2. Remake the weak boards. Use the engine stills as staging references (img2img on Krea), so the scale and framing match the surveyed cameras. The weak boards are:
   - C01: s2, s8, s8b (the head is cropped), s10, s11 and s12 (she is drawn twice);
   - C02: s1, s5, s9 and s11 (Victorian street lamps), s3 (two panels), s4, s7 (scale), s10 and s12;
   - C03: s1, s5, s6 and s8 (the heart is held), s9, s10, s11 (he crawls), s12 (bridges) and s13 (twice);
   - C04 A: A1 (walks the wrong way), A4, A5, A6, A7 and A8 (twice);
   - C04 B: B3 (cheering), B4 (smiling), B4b (stained glass) and B5 (twice).

   Describe the Warden as a hooded giant in a ranger's leathers and old mail, not a robed wizard.
3. Block animation's three C01 clips (`her/lie_side_wake`, `sit_back_heels` and `reach_coals`, now merged) into C01's shots 2 to 8b.
4. Recut the Prologue animatic (the command and cards are in `animatics/prologue.txt`).

## Key decisions

- **The cinematic owns the boss's body while it plays.** The zone hides its own and takes him back at the mark where the cinematic leaves him. One body is on screen, and the fight starts where the picture ended.
- **C03 is framed relative to where he falls,** with her placed to the south. The cameras are offsets from `w`, so they hold wherever the fight ends.
- **Gameplay stays in zone code.** Spawns, burrows, Apply effects and Douse run through `event` cues, so a skip still does them.
- **The stand-in clips are chosen from the kit by bone checks:** Spell_Simple_Idle tilted for the lamp-arm in the river, Idle_Torch for the lamp lift, and Fixing_Kneeling for the kneel.

## Incoming

- **Combat (a708da2c97bf85c95), pending the owner:** the story bosses are redesigned (`docs/design/STORY_BOSSES.md`). If approved, C13's shot 1 becomes "she stands over him, and he will not stay down", and C10 may gain a "Let him go" / "Finish it" choice. The details are in the handoff, Next 8.

## Blockers and notes for others

- **Animation (a435f4dd0ac80df75):** still needed from Kimodo: the Warden's lie_arm_up, rise_stiff, wade_drag, bend_lift and kneel_fall; Grimtunnel's burst, sniff and dive; and C04's wade_out, flask_drink, walk_uphill and unfold_arms.
- **Art and boss look:** the Warden's hood is darkened in `WardenView` until his own model exists. The heart orb is a plain sphere; it should be a faceted stone.
- **Voice:** none needed now. No new placeholders were added.
