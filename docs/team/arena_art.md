# Arena art: how every arena looks, and reads

Status page for arena art (branch `worktree-agent-aba487928a1515c93`). The lead `aba487928a1515c93`
has **handed off**: read `docs/handoff/arena_art.md`. Sheets and concepts are in `docs/arena/`
(latest: `hollow_night_2.jpg`, `dig_1.jpg`).

## The brief

I own every arena's look: the ground, the dressing, the landmarks, the light and air, how readable
the fight is on it, and how each place tells its part of the valley. That includes each story
fight's own place, built to combat's outline, and the endgame's two kinds of arena: the **ember
scars** (survivors runs) and the **Wayfinder's atlas** (permanent maps, "like PoE").

## Current state

| Place | Grade | State |
|---|---|---|
| Hollow by Night (story) | ~3.5–4 | 5–19% flat black (was 26%). The banks read as wood now, not a void. Old Blue's knolls are stone. `PlaceBuilt` is set. |
| Hollow | ~3.5 | The litter reads as leaves. Moss grows in cushions. The canopy pools are soft. The stream is still weak (dark, 36% black at the water). |
| Dig | ~3.5 | The tips are heaps of coal and rock lumps. The pit is a throat with a red heart. The clay is lighter, and the rust and ballast are graded (no blots). Still: the slurry pool is too lime, and the tips are dark masses from afar. |
| Barrow | ~3 | The tussock tips are warm. The howe has moved to the top of the picture, not yet judged. Still blue-grey all over. |
| Ruts | ~3 | Not yet re-judged. |

## Key decisions

- **A scar is its people's own ground.** Landmarks stand at the edge; cover inside stays under 2.2 m.
- **Flat black is measured, not guessed** (`black.py`): at most a fifth of a frame.
- **The Hollow's litter is whole red-brown leaves** (dry_decay_leaves) over black earth
  (forest_ground_06). leaves_forest_ground's pale chips read as gravel however they were toned.
- **The canopy is real shadow with a soft rim.** The moon's 1.2° breadth (PCSS) blurs shadows cast
  from 9 m up, and leaves contact shadows sharp. At 2.5° the pools washed out.
- **Moss is cushions, each there or not by its own hash.** A threshold on the paint drew a
  cut-out of carpet. No scanned moss clumps: they read as plastic rings.
- **A story place's walls are its banks and the wood, seen whole:**
  - char and scorch stay at the banks' feet;
  - past the edge is only a quarter darker;
  - no crown stands between the camera and the place;
  - the lip burns in short stretches.
- **No mist sheets over arena streams.** They hid the water under one grey smear.

## Next (in order)

1. **The Vault's hall** (combat built the fight; it has no place art: invisible walls, stand-in cover and standards). Build `Maps/Arenas/Vault.cs` to `VaultOpened.Ground`, then set `PlaceBuilt`.
2. **The Roost**, built to `RaidOnTheRoost.Ground`.
3. The Barrow's howe at its new end; the Dig's slurry and tips from afar; the Ruts.
4. The Hollow at minute 25, and its stream.
5. The atlas maps from each people's kit (experience's ask: nothing tall over a fight, the ground a quiet stage).

## Notes for other areas

- **Combat:** `HollowByNight.PlaceBuilt` is true (its pieces and cover are its own). Old Blue's
  rocks are `arena/knoll` pieces sheathing the rise; his points are their tops.
- **Performance:** the Hollow's moon now has `LightAngularDistance` 1.2 (PCSS) wherever a place
  has a canopy. Please measure it with `--perf-flip`. The mist sheets over arena streams are gone.
- **Experience:** Hollow by Night 5–19% flat black at the game camera; round Hollow 3%.
- **Everyone:** the root scans (root_cluster_01/02, single_root, pine_roots) are toned down in
  `Dressing.ScanTint`. They read as pale card from above.
- **Tool:** `dotnet run -c Release --project godot/balance -- landmarks --people P --seed N`
  prints where an arena's streams, rails and own pieces lie, for `--at X,Z`.

## Notes from performance (agent a20bdef993e00f26b, 6 October)

- **The see-through is remade** (`shaders/kit.gdshader`, `KitLook.Rim`): the dithered tunnel
  (the owner: "a little pedestrian in its pixelation") is gone. What stands nearer the camera
  than she does, and above her ankles, opens in a soft round window round her: measured on the
  screen in metres at her distance, clear to 1.45 m and feathered to 2.5 m, so it is round and
  the same at every zoom. A piece only partly in the way (near her depth, or low by her feet)
  gets a smaller window, never a fainter one. The cut is in the piece's own pass; only the
  feathered rim is drawn again, translucent, by each kit material's next pass (copies more than
  14 m off her line of sight are culled in its vertex stage). It opens only in the camera's own
  view, so a tree opened for her still casts its whole shadow. The trees' look is yours: the
  radii and easing are the numbers at the top of `see_through()`. Pictures in the performance
  report (house behind her in the Waystation, the Verge's pines).
- **The Hollow's soft moon** (PCSS, `LightAngularDistance` 1.2): 0.43 ms of GPU at 1440
  (paired flip, `--perf-flip softshadow`, quartiles 0.14 to 0.54). Keep it if it earns that.
