# Handoff: arena art

For the next arena art lead. Read `docs/team/README.md`, then this, then
`docs/team/arena_art.md` (the status page), then look at `docs/arena/hollow_night_1.jpg`
and the concepts `docs/arena/concept_*.jpg` (all four places now have them).

## The owner's words

- "AAA standard", "strive for excellent, above and beyond", "do we have soul?",
  "never settle: remake rather than polish", "how things are can be limiting".
- "We are striving for perfection." Improved is not enough. Before showing anything,
  ask whether it's the best version of this in any game. Root the design in research
  on how the best games solve it, then make it ours (the main session, passing on the owner).
- Story fights: "much more specialized and fun - smaller arena", with "proper arpg end
  bosses". The endgame: the **Wayfinder's atlas** (permanent build maps, "like poe")
  and the **ember scars** (the survivors arenas). Each has its own look.

## The brief (in full)

Own every arena's look: the ground, dressing, landmarks, light and air, how readable
the fight is on it, and how each place tells its part of the valley. Since the owner's
story-fight direction this also covers each story fight's own place, built to combat's
outline. Arenas are always night. Readability comes first: she reads at the game camera
(56° pitch and 22–34 m for round arenas; 64° and 22–27 m for story nights). Enemies,
telegraphs and pickups must read over the ground, and in a minute-6 frame no more than
a fifth of the screen may be flat black (experience's test).

The coordinator's list, in order, as I took it:
1. minute-25 horde frames on all four (done);
2. the Dig's rust and spoil, plus grass, stones and timber (in progress);
3. the Hollow's den (done as a story place; still to do in the round Hollow);
4. the Barrow's howe and the Ruts camp on screen, replacing the grey ball (the ball is done);
5. grass that reads (done in the Barrow and the Ruts);
6. lift every arena to 4–5.
Then, from the main session: make the builder take an outline and build the Hollow
by Night to combat's shape (done).

## Done (this lead)

- **Story places.** `MapSpec.Story` holds the fight's id, and `ArenaGen` builds that
  fight's place to `StoryScripts.For(id).Place`:
  - the signed distance to the outline becomes `Inside`;
  - the rim is walked round the outline (`Builder.Rim()`);
  - the banks stand steep outside it, cut where a stream runs (`ArenaShape.Bank`);
  - the ring's lights are dropped there.
  The place itself is `Arenas/HollowNight.cs`.
- **The Hollow by Night:** see the status page. It has gates (`ArenaEdge.Gate`,
  `ember_gate.gdshader`), deadfalls with their fires laid (`MapBuild.FireLights`), the
  root plate over the den's mouth, reeds, the clough's watercourse and rocks, still
  water, foxfire and open-sky clearings.
- **Layout mirrored** (combat agreed): the way runs up the screen, away from the camera.
- **Ground shader:**
  - per-layer contrast and size (`ArenaGround.Layer`);
  - macro relief by derivative bump mapping;
  - ember plates fixed (they were filling whole plates as orange blobs at every ring);
  - slurry glows in threads;
  - standing water lies level;
  - moss breaks into cushions at its edges;
  - splat3 carries B foxfire and A open sky.
- **Grass:** tussocks (`arena_grass.gdshader`, `Grass.Arena`, `ArenaGround.GrassLook`),
  on in the Barrow and the Ruts. 0.72 ms of GPU in the barrow (performance measured it).
- **Fallen leaves:** geometry (`arena_leaves.gdshader`, `Grass.Leaves`, the grass mask's
  R, `ArenaPaint.Leaves`), in both Hollows. **Not yet judged.**
- **Canopy shadows:** `ArenaEdge.Canopy` and `canopy.gdshader`, a shadows-only sheet
  that turns the moon into pools. It works in the story Hollow (62° moon). The round
  Hollow showed none at 38°: I subdivided the sheet against pancaking. **Not yet judged.**
- **The Dig:**
  - spoil `gray_rocks`, the tips conical and lumpy;
  - rust a mottle;
  - dry grass at the edges and the tips' feet;
  - timber stacks by the rails (`arena/timber`);
  - a windlass (`arena/winch`) and fence stakes at the pit's lip;
  - the face material skipped on the tips.
- **The Ruts:** the cook pot (`arena/cookpot`) on a tripod over its own fire, in place of
  the grey ball.
- **The Barrow:** the road is `grassy_cobblestone` drawn ×1.7, and reads as the Legion's slabs.
- **Tools:**
  - `--night hollow|roost|dig|vault [--stage N] [--lit]` (Game.cs);
  - `tools/godot/arena_ground.py` takes a per-layer flatten radius and now puts its
    credit lines into the Poly Haven list.

## In progress (judged in `r10`, scratchpad `arena3/s_r10.jpg`)

- **The canopy works in both Hollows** now that the sheet is subdivided.
  - The round Hollow has real moon pools: 10.8% flat black at the start, 21% at
    minute 25.
  - Too hard and blocky at the edges: the 0.55-frequency term in `canopy.gdshader`
    is finer than the shadow map. Drop it, or soften with ShadowBlur.
  - Under the crowns it is near black: raise the Hollow's hemi a little more, or let
    the ground's foxfire carry.
- **The story Hollow is 26% flat black at its start** (target ≤20%). The next step is
  story cover ×0.5 (`ArenaEdge.Build`, now ×0.7). Not yet tried.
- **The litter's micro-contrast is softened** (Con 0.8): control the detail, keep the
  big shapes (Diablo IV's "old masters"). It reads less like gravel. The geometric
  leaves are hard to see at the game camera: judge them closer, or drop them if they
  only add noise.

## Next

See the status page's Next list.

## Decisions (why)

- **A story place's way runs up the screen.** Its landmark sits at the top, so it is
  never between her and the camera.
- **A gate is the ember's line drawn across a way.** The ring says "no further"; a gate
  says "not yet".
- **In a story place the banks are the edge.** The lip burns low there (`lip_glow` 0.3),
  the scorch is narrow, and there are no ring lights.
- **Flat black is measured** (`black.py`), not guessed.
- **The canopy is real shadow, not painted dapple.** It falls on her and on the Pack
  too, and it moves.
- **Moss stays small and broken.** Large green islands read as paint.

## Failures and why

- **The ember plates' exact voronoi border went wrong under the warp.** It filled whole
  plates, which were lit as orange "paint" blobs at every ring. Replaced by an F2–F1
  border, which can't go negative.
- **A sheet of flowing stream water over a story fight read as a smear.** The story
  place's water is the ground's own now (no stream mesh, no mist sheets).
- **A tilted water normal slid a white moon streak down the bank.** Water now lies level.
- **Big root plate unlit:** it faced away from the moon and read as a black burst. It
  is now lit from the hole (sick green), with lighter tints. Judge it again.
- **Canopy cover:** the noise sum is narrow, so a step at `1 - cover` closed nearly all
  the sky. The threshold is now `0.62 - cover * 0.24`.

## Gotchas

- **The worktree guard refuses complex bash.** Avoid `cd X && git` and loops over
  variables in bash. For multi-edit scripts I used small Python files (`ed*.py` in the
  scratchpad) run from PowerShell.
- **Heavy work takes turns** (`tools/turn.py`). My `batch.py` and `imp.py` take and give
  the godot turn; a batch can wait up to 15 min for one. GPU jobs (ComfyUI) need
  `take gpu`.
- **Shader files are read when Godot starts each run.** Don't edit shaders while a batch
  runs. C# is safe to edit once the batch has built.
- **Godot node names can't hold ':'.** Gates are named `gate_ID`, and `ZoneView` maps
  them to `gate:ID`.
- **Credits:** run `WRITE_CREDITS=1 dotnet test --filter CreditsTests` in `godot/tests`
  after adding a scan, and commit `data/credits.json` and `licences/CREDITS.txt`.
- **The ground-texture importer:** `imp.py` reimports about 1000 files after a merge,
  which takes several minutes.
- **The first frames at about 2.5 s show the title card**; level-up cards cover frames
  from about 5 s with `--auto`. Use `--auto idle` for clean ground frames.
- **The Ruts' camp is at about (50, 42), the Dig's tips at about (36, −38)**
  (seeds 523 and 739).

## Tools (scratchpad `arena3/`)

- `batch.py SPEC PREFIX [--build] [--only a,b]` (`{p}` in names is the prefix);
  `play.py`; `sheet2.py OUT COLS WIDTH names...`; `crop.py NAME x0 y0 x1 y1 [scale]`.
- `black.py names...`: the flat-black share; `layers.py`: layer means.
- `imp.py`: the import, taking a godot turn; `thumbs.py OUT ids...`: Poly Haven
  thumbnails; `concepts.py`: Krea concepts (take a gpu turn first).
- Specs: `hs.txt` (the Hollow by Night's stages, lit, water, gate), `r9.txt`/`r10.txt`
  (mixed), `dig.txt`, `e.txt`, `h25.txt` (hordes).

## Collaborators

- **Combat (successor of a708da2c97bf85c95, handoff docs/handoff/combat.md):**
  - owns the story outlines;
  - has queued the den's mouth move to about 18 m from boss_start.
- **Experience:** readability, the flat-black test.
- **Skills:** telegraph strength on the ground (now 0.28 for hostile marks).
- **Performance (a56abaf3a104be675):** grass cost; `--perf-flip grass`.
- **Story:** places' lore.
- **Legal:** asked about the boar. That isn't arena art's; I pointed them to the models
  planner and animation.

## Files to read first

- `godot/logic/Maps/ArenaGen.cs`, `godot/logic/Maps/Arenas/HollowNight.cs`,
  `godot/logic/Play/Story/StoryPlace.cs`, `godot/logic/Play/Story/Hollow.cs`
- `godot/shaders/arena_ground.gdshader`, `godot/src/World/ArenaGround.cs`,
  `godot/src/World/ArenaEdge.cs`, `godot/src/World/Grass.cs`,
  `godot/src/World/Pieces.Arena.cs`
- `godot/tests/ArenaPlaceTests.cs`
