# Arena art: how every arena looks, and reads

Status page for the arena art lead (agent `a26767f7f9955cb56`, branch
`worktree-agent-a26767f7f9955cb56`; took over from `a52b851395b3ab3f4`, whose
handoff is `docs/handoff/arena_art.md`). Sheets and concepts are in `docs/arena/`.

## The brief

I own every arena's look: the ground, the dressing, the landmarks, the light
and air, how readable the fight is on it, and how each arena shows its place in
the valley. The endgame has two kinds of arena, each with its own look:
- the **ember scars**: the survivors arenas, one night each (`ArenaRun`);
- the **Wayfinder's atlas**: the permanent build maps, "like PoE" (story calls
  them "the places the road forgets").

## Current state (paused for the owner, mid-pass)

**Honest grades, judged at full resolution:** Barrow ~2.5, Ruts ~2.5, Hollow
~3, Dig ~3. The ground reads flat, like asphalt or paint blobs, from the arena
camera. Under the moonless mood ("Deep" and "Lampless" names) 48–80% of the
frame is flat black.

**Minute-25 horde frames (done; seeds 947/311/523/739):**
- The Kerchiefs, the Risen and the lamplings all read over their ground.
- The Pack's dark-grey wolves are a dark mass on the Hollow's dark litter.
- The red elite discs are heavy on the Dig's clay.
- The skills lead says the lamplings' white-gold discs are blow telegraphs,
  already toned down on their branch.

**This pass so far (committed, not yet judged in full):**
- **Ground shader** (`arena_ground.gdshader`, `ArenaGround.Layer`):
  - per-layer contrast (`Con`), so a scan's grain survives 30 m;
  - macro relief: each layer's `Lift` and `Bump` in metres, plus moss domes,
    sunk pools and trodden ground. Bump mapping by derivatives turns these
    into light on the edges between materials.
- **Grass that reads** (`arena_grass.gdshader`, `Grass.Arena`, `ArenaGround.GrassLook`):
  - whole tussocks of 24–26 arched blades, dark at the root and lit at the
    tips, gathered into swathes with earth between;
  - on in the Barrow and the Ruts and judged there: they read as grass now;
  - the Dig and the Hollow have looks set but no grass paint yet.
- **New scans:** the Dig's spoil is now `gray_rocks` (blasted lumps) and the
  Barrow's road `grassy_cobblestone` (polygonal slabs like the Via Appia).
  Both are flattened with a wider radius so their stones keep their shading.
  They are imported but **not yet seen in game**.
- **Concepts** for the Barrow and the Ruts: `docs/arena/concept_barrow_{0,1}.jpg`
  and `concept_ruts_{0,1}.jpg`. The Barrow's targets are dense dry tussocks,
  slabs with grass in the joints, dark open graves and mist. The Ruts' are
  silvered puddles, green verges and the camp's fires.

## Key decisions

- **A scar is its people's own ground** (story confirmed).
- **Landmarks stand at the edge only; cover inside stays under 2.2 m.** A test holds this.
- **Readability by local contrast and light, not by a black ground.**
  - The old rule of keeping everything dark made asphalt.
  - The ground stays under the living, but keeps its grain, its relief and its
    own light pools.
  - The experience director's test: in a minute-6 frame, no more than a fifth
    of the screen reads as flat black (`black.py` in my scratchpad measures it).
- **Grass is geometry, in tussocks.** Thin blades in the ground's own colour
  read as scratches, and single tufts read as stars.
- **The ring is a line, not a field** (inherited, holds).

## Next (in order)

1. **Exact next step:** build, then shoot `dig.txt` and `e.txt` (the scratchpad
   `arena3/`; `batch.py SPEC PREFIX --build`). Judge the new spoil and road
   scans at full resolution, and tune their `Looks` (Y, Con, Lift, Bump).
2. The Dig:
   - rust drifts: make them a mottle inside the clay, not blobs;
   - spoil heaps: taller, lumpy, with coal-lump scatter;
   - grass paint toward the edges;
   - scattered stones;
   - timber pieces made in `Pieces.Arena.cs` (stacks, props, a windlass);
   - lamps.
3. The Hollow's den: on screen and readable. Also wolves against the litter:
   warmer, mid-value litter (try `leaves_forest_ground`) and moss that isn't paint.
4. The Barrow: the howe on screen, plus place light (corpse-candles over open
   graves) for the moonless mood. The Ruts: the camp on screen, the grey
   cauldron replaced, puddles that hold the sky (sheen).
5. The moonless mood: each place's own lights carry it.
6. Horde frames again on all four; lift each arena to 4–5.

## Story places (owner's new direction, not yet approved)

One small, hand-shaped place per Act 1 story fight, about 50–60 m across, with a boss ground.
I agreed this with experience (ab406cf9ddd22b03b), and the Hollow goes first.
- **The outline to build to:** `HollowByNight.Ground` in `godot/logic/Play/Story/Hollow.cs`
  (combat, worktree-agent-a708da2c97bf85c95@aa68f38e).
  - Spaces are capsules (the clough, the sick water, the den floor) joined by two necks.
  - Two gates open a stage's way.
  - Named points: the start, Old Blue's rocks, the reeds, the shallows, six deadfalls, the den's middle and mouth, and the crowd's points.
  - `StoryPlace.Dist(x, z)` is the signed distance, negative inside.
- **What needs my look:** the gates (shut and open), six deadfalls (wood that takes fire), the den's mouth under roots at the north edge, low cover only, and the fight reading at 30 m by night.
- **The ArenaGen change needed:** build from an outline. `Inside` becomes the signed distance from `Dist`, the Rim is traced from contours, and the ring's lights and placement follow it. A smaller grid gives finer paint.
- Combat owns the shapes' numbers. Change them in Hollow.cs or ask.

## Notes for other areas

- **Performance (a7145e18b3eb78294):** arena grass is now on in the Barrow and
  the Ruts:
  - about 36k tussock instances × 26 blades × 3 triangles, around 2.8M
    triangles, similar to the overworld meadow;
  - no shadows;
  - the wider cell at lower qualities follows `GrassCell`.
- **Experience (ad1f5623590e09883):** your near-black barrow (moonless) is on
  my list as item 4/5. The fix is place light, not a lifted floor.
- **Skills (a63cd93fc73d5ed79):** you're checking the telegraph discs against
  the brighter clay; I'll judge them again after the Dig pass.
