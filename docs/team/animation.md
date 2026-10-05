# Animation: status

Agent a03acf30b3e9bdd70, branch `worktree-agent-a03acf30b3e9bdd70` (took over from a435f4dd0ac80df75). The brief, history and gotchas are in `docs/handoff/animation.md`.

## State (2026-10-04)

- **The slam: done** (ffab4040). Remade, not just mapped: the predecessor's draft read as a stretch from the game's camera.
  - `crowd.slam` / `slam_armed`: the lead foot planted in the gather; the fists locked (armed: the axe raised high, its head up and back where the camera sees it); the arch; the hang; the jack-knife with the body leading; the blow on frame 30 (1.0 s); held down glaring; up and settled 0.67 s after the blow.
  - Its own role `"slam"` (`Visuals.Clips.Slam`), on kerchief_brute (Barn-Door) and skeleton_minion (the Heap). `CrowdView` plays the windup so the blow lands with the sim's (`SlamImpact`), then plays the rest after the cast.
  - Judged on sheets (side, front, 64°) and in the game (`--on casts` bursts).
- **Kneel-to-shoot: done** (926efa47). `crowd.kneel_aim` (on the knee by 0.33 s, on the eye by 0.53 s, held) and `kneel_shot` (the kick, a beat, the rise, standing by 0.63 s).
  - Roles `"aim"` and `"shot"` (`Visuals.Kneels`) on skeleton_rogue and the new **kerchief_crossbow**. `CrowdView` plays the aim from `e.AnimT`, then the shot only after an aim (`Gait.Aimed`), so a melee strike stays the library's.
  - Judged in the game with levy_crossbow pointed at it locally (not committed: combat's).
- **Vat v13.**

## Next (exact)

1. The cinematics' Kimodo clips (handoff §4.3): rise_stiff and bend_lift first (C02, on the kit man), then kneel_fall (C03), flask_drink (C04), C01's, C04's rest. Grimtunnel's on the lampling rig in `Beasts.cs`.
2. Polish: the chain haul's landing crouch; a heavier flinch while running (a gesture).
3. The male hero's library rebuild once his body lands (with ab82cbe99e2937ddd).

## Waiting on others

- **Combat's successor** (queued as the first item of `docs/handoff/combat.md` §4.3): plant the slammer 0.65 s after its blow and the shooter 0.7 s after an aimed shot. Until then the Heap strikes again over its get-up and the crossbows skate as they rise. Then point levy_crossbow and mb_levy_sergeant at `kerchief_crossbow` and add it to `EncounterTests`' rigs.

## Key decisions

- **The slam and the kneel are their own roles, not `cast`/`attack`.** A rally's cast loops; a slam's must not. The shot after an aim must not replace the crossbow's melee strike.
- **The blow lands on a frame the bake samples** (15 fps), so it is never smeared between two.
- **From the game's camera a weapon hung behind the back is hidden by the body.** Wind-ups raise it high instead.
- Takes that don't fit the game's action are rejected, not bent to fit (Kimodo's slam).

## Tools

- `--on casts` (Game.cs): fifteen frames a second through every marked cast. Pair it with `--fixed-fps 30` so the frames land on time.
- `--lab --give +vitality`: no weapons, so the creature isn't flashing white from blows.

## Notes for other areas

- Combat: see "Waiting on others". The view needs no new state, only no move and no strike during the plants.
- Performance: the slam adds about 26 frames to skeleton_minion's and kerchief_brute's bakes, and the kneel adds about 22 to the crossbows'.
