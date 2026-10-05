# Arena art: how every arena looks, and reads

Status page for the arena art lead (agent `a26767f7f9955cb56`, branch
`worktree-agent-a26767f7f9955cb56`; took over from `a52b851395b3ab3f4`, whose
handoff is `docs/handoff/arena_art.md`). Sheets and concepts are in `docs/arena/`.

## The brief

I own every arena's look: the ground, the dressing, the landmarks, the light
and air, how readable the fight is on it, and how each arena shows its place in
the valley. Since the owner's story-fight direction this also covers each story
fight's own place. The endgame has two kinds of arena, each with its own look:
- the **ember scars**: the survivors arenas, one night each (`ArenaRun`);
- the **Wayfinder's atlas**: the permanent build maps, "like PoE" (story calls
  them "the places the road forgets").

## Current state

**The Hollow by Night (the first story place) is built to combat's outline, and
reads at the game camera** (sheet `docs/arena/hollow_night_1.jpg`):
- **The builder takes an outline.** `MapSpec.Story` holds the fight's id, and
  `ArenaGen` makes the place to `StoryScripts.For(id).Place`:
  - `Inside` is the signed distance to the outline;
  - the Rim is walked round it, with `Rim()` giving points and their way out;
  - the banks stand steep outside it, cut down only where a stream passes;
  - the story place is `HollowNight.cs`.
- **Layout mirrored to suit the camera.** The way now runs up the screen, from
  the clough at the bottom, through the water, to the den at the top. The den's
  mouth and root plate are at the top of the picture, so they never stand
  between her and the camera. The numbers are in Hollow.cs; combat has been told.
- **Gates:** the ember's burning line across each way, with a hedge of low
  flames, sparks and light (`ArenaEdge.Gate`, `ember_gate.gdshader`). The night
  hides `gate:ID` as it opens a gate, and the char stays on the ground.
- **Six deadfalls:** pale dead trunks with their brash (`arena/deadfall`). Each
  has its fires laid (two flames, one light) and handed to the night through
  `MapBuild.FireLights`, so lighting one burns the wood itself.
- **The den:** a moonlit clearing of trodden mud with runs and bones, the
  deadfalls at its corners, and the root plate over the mouth (`arena/rootplate`).
- **The water:** a still pool and its stream, painted by the ground shader
  (level water, the sky in it). The slurry runs in thin curling threads of sick
  light in the shallows. Reeds (`arena/reeds`) stand at the crowd's reed points.
- **The clough:** a stony dry watercourse, Old Blue's three rock knolls, and ferns
  and roots on the bank tops (no trees within 11 m: their tangles and shadows
  hid the cut).
- **Light:** the moon stands higher over story places (62°). Clearings are open
  to the sky (splat3 A); foxfire glows on rotting wood (splat3 B). The ember's
  lip burns low and there are no ring lights. Flat black is 8–17% of a frame at
  the game camera (target ≤20%).
- **Fixed for every arena:**
  - the ember char's plates no longer fill whole plates as "border" (they were
    the flat orange blobs at every ring);
  - the slurry glows in threads, not sheets;
  - standing water lies level.

**The round arenas** (unchanged this pass but for the fixes above): Barrow ~2.5,
Ruts ~2.5, Hollow ~3, Dig ~3. Their grounds read flat from the arena camera.
Grass tussocks are on in the Barrow and the Ruts. The new spoil (`gray_rocks`)
and road (`grassy_cobblestone`, slabs drawn ×1.7) are judged: the road reads as
the Legion's slabs; the spoil reads as lumpy but is still one dark field.

**Minute-25 hordes (seeds 947/311/523/739):** the Kerchiefs, the Risen and the
lamplings read over their ground. The Pack's dark wolves were a dark mass on the
Hollow's litter; the litter is now warmer and lighter (larger leaves, Y 0.11).

## Key decisions

- **A scar is its people's own ground** (story confirmed).
- **Landmarks stand at the edge only; cover inside stays under 2.2 m.** Tests
  hold this, for story places too.
- **Readability comes from local contrast and the place's own light, not a black
  ground.** Flat black stays at or under a fifth of a frame.
- **Grass is geometry, in tussocks.**
- **The ring is a line, not a field.** In a story place the banks are the edge,
  so its lip burns low and a gate is the ring drawn across a way.
- **A story place's way runs up the screen,** with its landmark at the top.

## Next (in order)

1. **Exact next step:** judge the Hollow by Night again (`hs.txt` in
   scratchpad `arena3/`, prefix hs5). Then:
   - the root plate fully on screen at the boss's start (it sits at the top edge);
   - the slurry threads fainter;
   - the moss reads as bubble wrap: give it a cushion texture;
   - the litter still reads partly as gravel.
2. The Dig:
   - rust as a mottle, not blobs;
   - spoil heaps with lumps and scatter;
   - grass toward the edges;
   - stones, timber and lamps.
3. The Barrow's howe and the Ruts' camp on screen; the grey cauldron replaced.
4. The moonless mood carried by each place's own lights (foxfire is the Hollow's).
5. Horde frames again on all four; lift each to 4–5.
6. The next story places (the Roost, the Dig's edge, the vault) once combat has
   their outlines.

## Notes for other areas

- **Combat:** I mirrored z in `HollowByNight.Ground` so the way runs up the
  screen. `StoryNight.Open` now hides `gate:ID`, and the deadfalls use the laid
  fire lights (`map.FireLights`). `--night hollow [--stage N] [--lit]` shoots it.
- **Performance:** arena grass is on in the Barrow and the Ruts (about 2.8M
  triangles, no shadows). The story place adds:
  - six deadfalls, each with two fires and one light;
  - two gate lights with a few flame cards each;
  - no stream mesh or mist sheets.
- **Experience:** the Hollow by Night is at 8–17% flat black at the game camera.
- **Skills:** the bomb marks at 0.28 on the Dig: I'll judge them in the Dig pass.
