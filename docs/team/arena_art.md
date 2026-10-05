# Arena art: how every arena looks, and reads

Status page for arena art (branch `worktree-agent-a26767f7f9955cb56`). The lead
(a26767f7f9955cb56) has handed off: read `docs/handoff/arena_art.md`. Sheets and
concepts are in `docs/arena/`.

## The brief

I own every arena's look: the ground, the dressing, the landmarks, the light and air,
how readable the fight is on it, and how each place tells its part of the valley. That
includes each story fight's own place, built to combat's outline. The endgame has two
kinds of arena, each with its own look: the **ember scars** (survivors runs, `ArenaRun`)
and the **Wayfinder's atlas** (permanent build maps, "like PoE").

## Current state

| Place | Grade | State |
|---|---|---|
| Hollow by Night (story) | ~3.5 | Built to combat's outline: gates, deadfalls with fires, the root plate over the den, reeds, still water, foxfire, moon pools. Start area 26% flat black. |
| Hollow | ~3 | Canopy moon pools (real shadow) and broken moss. Litter softened but still reads as gravel. Pool edges blocky. |
| Dig | ~3 | Tips of blasted rock, rust as a mottle, dry grass at the edges, timber stacks, a windlass and stakes at the pit. |
| Barrow | ~3 | Tussock grass; the Legion's slab road. Howe and gate not yet judged on screen. |
| Ruts | ~3 | Tussock grass; the cook pot on its tripod over a fire replaces the grey ball. |

**Fixed for every arena:**
- the ember plates' orange blobs;
- the slurry glows in threads;
- standing water lies level;
- the litter's micro-contrast is controlled.

## Key decisions

- **A scar is its people's own ground.**
- **Landmarks stand at the edge only; cover inside stays under 2.2 m.** Tests hold
  this, for story places too.
- **Readability comes from contrast and the place's own light, not a black ground.**
  Flat black stays at or under a fifth of a frame (`black.py`).
- **Grass is geometry in tussocks.** Moss stays small and broken.
- **The canopy is real shadow,** shadows-only and subdivided, not painted dapple.
- **A story place's way runs up the screen,** its landmark at the top. A gate is the
  ember's line across a way.

## Next (in order)

1. **Exact next step:**
   - set the story canopy cover to ×0.5;
   - drop the canopy's finest noise term (blocky pool edges);
   - shoot `hs.txt` and `r10.txt` (scratchpad `arena3/`).
2. The Hollow's litter: does it read as leaves from 30 m? If not, drop the geometric
   leaves.
3. The Dig: judge the tips, rust, grass, timber and windlass at the game camera, and
   the bomb marks (skills, 0.28).
4. The Barrow's howe and gate on screen; the Ruts' camp judged.
5. The moonless mood carried by each place's own lights.
6. Horde frames on all four; lift each to 4–5.
7. The next story places (the Roost, the Dig's edge, the vault) once combat has their
   outlines. Combat's successor may move the den's mouth to about 18 m from boss_start.

## Notes for other areas

- **Combat:** `--night ID [--stage N] [--lit]`. The gates hide as `gate:ID`; the
  deadfalls burn on `map.FireLights`.
- **Performance:** new per Hollow: a subdivided shadows-only canopy (75×75 quads) and
  leaf scatter (14 leaves per 0.6 m cell, in the meadow's ring). Grass is 0.72 ms in
  the barrow (yours).
- **Experience:** story Hollow 15–26%, round Hollow 11–21% flat black.
