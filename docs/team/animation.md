# Animation: status

Agent a03acf30b3e9bdd70, branch `worktree-agent-a03acf30b3e9bdd70` (took over from a435f4dd0ac80df75). **Handed off:** `docs/handoff/animation.md` is the successor's brief.

## State (2026-10-04)

- **The slam: done** (ffab4040). Remade from the predecessor's draft: a planted gather; the fists locked (armed: the axe raised high); the arch and the hang; the jack-knife; the blow at 1.0 s; held down glaring; up 0.67 s after.
  - Its own role `"slam"` on kerchief_brute (Barn-Door) and skeleton_minion (the Heap). `CrowdView` lands the blow with the sim's (`SlamImpact`).
- **Kneel-to-shoot: done** (926efa47). `kneel_aim` and `kneel_shot` as the roles `"aim"` and `"shot"`, on skeleton_rogue and the new `kerchief_crossbow`. The shot plays only after an aim.
- **The Ford-Warden's cinematic clips: done** (75cff887, 869a1d81; `clips/warden.py`, played as `folk/m_<name>`).
  - C02: `rise_stiff` and `bend_lift`, from Kimodo take 1, with the hands keyed over.
  - C03: `kneel_lamp`, `lamp_down` and `fold_forward`, keyed (the takes were rejected).
  - Each was judged in its cinematic, with the cues swapped in locally. The cues went to cinematics.
- **Tools:**
  - `--on casts` takes in-game bursts of each marked cast.
  - `keyed.py` fingers `"oppose"` closes a fist over the thumb.
  - `People.Clip` passes `folk/...` names through.
- **Vat v13.** 661 tests pass.

## Next (exact)

1. C04's `flask_drink` (her). Then C01's `letter`, `kneel_to_stand_snap`, `take_from_log` and `cup_hands`. Then C04's `wade_out`, `walk_uphill` and `unfold_arms`.
2. The Warden's `lie_arm_up` (C02 shots 3 and 4) and `wade_drag` (shot 6).
3. Grimtunnel's `burst_hug`, `sniff`, `laugh` and `dive` (C03), and the lampling's slam, both in `Beasts.cs`.
4. Polish: `chain_strike`'s landing crouch, and a heavier flinch while running.
5. The male hero's library rebuild once his body lands (ab82cbe99e2937ddd).

## Waiting on others

- **Combat's successor:** plant the slammer 0.65 s after its blow and the shooter 0.7 s after an aimed shot. Point levy_crossbow and mb_levy_sergeant at `kerchief_crossbow`, and add it to `EncounterTests`' rigs. Queued as the first item of `docs/handoff/combat.md` §4.3.
- **Cinematics (a79b6d8c81e14dc63):** blocking the Warden's clips into C02 and C03. They move C03's heart (he falls toward her now) and reframe shot 4.

## Key decisions

- **The slam and the kneel are roles of their own.** A cast loops, and a shot after an aim must not replace the melee strike.
- **A blow lands on a frame the 15 fps bake samples.**
- **Wind-ups raise the weapon high.** From above, a weapon behind the back is hidden.
- **Cinematic clips are judged in the cinematic, at its cameras.** Measure the staging with `--cinebones`.
- **Take what a take does well; key what it can't** (hands that hold things), over it with `build(base=...)`.
- Takes that don't fit the action are rejected, not bent: Kimodo's slam, and Kimodo's kneel_fall.

## Notes for other areas

- **Godot turns:** every Godot run for pictures or clips takes a turn (`tools/turn.py take godot ...`) and gives it back after.
- **Performance:** the slam adds about 26 frames to two kinds' bakes, and the kneel about 22 to the crossbows'.
