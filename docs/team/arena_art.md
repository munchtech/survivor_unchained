# Arena art: how every arena looks, and reads

Status page for arena art (lead `aba487928a1515c93`, branch `worktree-agent-aba487928a1515c93`).
The predecessor's handoff is `docs/handoff/arena_art.md`; sheets and concepts are in `docs/arena/`
(latest: `hollow_night_2.jpg`).

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
| Dig | ~3 | Next. The spoil is one black field with no heaps to see. The rust is camouflage blobs. The pit's smoke is an orange dome. |
| Barrow | ~3 | The tussocks are pale straw stars, all blue-grey. The howe sits at the frame's foot in the dark. |
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

1. **The Dig:**
   - heaps that read as heaps: lumps of coal-black rock with glints, spoil kept to the heap;
   - rust as the clay's own colour, not blobs;
   - the pit as a throat, not a dome of lit smoke;
   - judge the timber, the windlass and the lamplings' discs.
2. The Barrow's howe and gate on screen; its tussocks.
3. The Ruts.
4. The Hollow at minute 25, and its stream.
5. The atlas maps from each people's kit (experience's ask: nothing tall over a fight, the ground a quiet stage).
6. The Roost, built to combat's outline (`RaidOnTheRoost.Ground`), then the Dig's and the Vault's.

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
