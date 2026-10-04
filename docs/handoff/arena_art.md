# Handoff: arena art

For the next arena art lead. Read `docs/team/README.md`, then this, then
`docs/team/arena_art.md` (the status page), then look at the sheets in `docs/arena/`.

## The owner's words

- "AAA standard", "strive for excellent, above and beyond", "do we have soul?",
  "never settle: remake rather than polish", "how things are can be limiting".
- The endgame's structure: "permanent ... our arpg build maps like poe and the normal
  arenas are for mindless survivors fun". Story has named them: the **Wayfinder's
  atlas** (permanent build maps: "the places the road forgets", in Ysolde's hand,
  never the four scars by day) and the **ember scars** (a night's survivors arena).
  Each kind, and each arena, needs its own identity.

## The brief (in full)

Own every arena's look: ground, set dressing, landmarks, lighting and atmosphere,
the fight's readability on it, and how each arena tells its place in the valley.
1. Audit every arena in play at 1920×1080, empty and in a full horde, and grade it
   (soul, sense of place, readability, beauty). Arenas are always night; the atlas,
   once it exists, has day and night.
2. Make each arena a place: a strong silhouette and landmarks that frame the fight
   without blocking it; ground with life and variety (scans, decals, blended
   materials); lighting and atmosphere with mood; dressing that tells its story.
3. Readability first: she reads at the gameplay camera (it opens at 22 m and stands
   back to 31–34 m as the horde grows); enemies, telegraphs (amber a blow, violet bad
   ground, pale blue stand here, grey solid) and pickups read over the ground; the
   dead fade or darken (done by experience); ground effects never bury the fight.
4. Use the GPU (ComfyUI at 127.0.0.1:8188 via `tools/comfy/comfy.py`), `tools/make3d`,
   `tools/modelgen` and Blender (`C:/Users/munch/Tools/blender-4.5.14-windows-x64`).
   CC0 downloads are consented; name what you fetch.

## Done

- **Audit** (before): `docs/arena/before_{empty,wide,horde}.jpg`; grades on the status
  page. Every arena was the same lit lawn with lilac gravel, whatever its name.
- **Each people's place** (`godot/logic/Maps/ArenaPlaces.cs`): barrow (Risen), hollow
  (Pack), ruts (Kerchiefs), dig (Lamplings), each with its own night
  (`AtmospherePreset`) and air (`ArenaAir`: mist, haze, dapple, ember colour). Moods
  from the table's adjective (Ashen/Scorched burned, Drowned water, Lampless/Moonless
  darker, Quiet/Praying/Fogbound mist, Briared/Crooked thorn, Gallows). Names are
  story's, in the valley's words (`Names`, `Moods`); `MapOffers` names a place by its
  people's word.
- **The generator** (`logic/Maps/ArenaGen.cs`, `logic/Maps/Arenas/*.cs`): MapGen hands
  arenas to it. Common: the wandering edge, the walls, the ember ring's char, lanes
  that cover keeps off, a 1024² paint (two splats + a grass mask). Each place plans
  big shapes, relief, paint, wall/fringe/open scatter and dressing (see the class
  comments for what each place is).
- **The ground** (`godot/art/arena/<place>/`, `tools/godot/arena_ground.py`): seven
  Poly Haven CC0 scans per place (names in each `layers.json` and
  `public/assets/CREDITS.md`). The tool flattens each photograph's broad shading (or it
  tiles as a grid from 30 m up) and records its mean linear colour.
- **The shader** (`shaders/arena_ground.gdshader`, `src/World/ArenaGround.cs`): the
  place's layers height-blended; every layer brought to a chosen mean albedo and
  saturation (`ArenaGround.Looks`: all low, so the living read over it); IQ-style
  offset anti-tiling with explicit gradients; standing water (dark, smooth, a sky
  sheen); trodden ground; the char with thin glowing cracks; moon dapple; the dark past
  the ring.
- **The edge** (`src/World/ArenaEdge.cs`, `shaders/ember_curtain.gdshader`): sparks off
  the ring, a low lit smoke curtain past it, a mist fog volume, the stream's water.
- **Tests** (`godot/tests/ArenaPlaceTests.cs`): each people's place; nothing over
  2.2 m in the fight (thin poles excepted); the story's must-nots; names and moods;
  the ring all round. 552 tests green.
- **Work-in-progress sheets**: `docs/arena/wip1_{empty,wide,edge}.jpg`.

## Where it stands (honest grades, from wip1)

- **Barrow ~3/5**: the Legion's road reads; turf no longer tiles; graves and ash
  read; the sealed howe and gate at the edge not yet seen on screen.
- **Hollow ~2/5**: dark umber with dapple; stream, roots, den not yet checked on
  screen; still featureless in the middle.
- **Ruts ~3/5**: the sunk road with its dark ruts reads; a red cast near the camp's
  fires; verges plain.
- **Dig ~2/5**: ochre clay; the pit reads as a black hole at 22 m (its glow is down
  inside); spoil heaps and rails need checking.
- **The ring is too strong**: it reads as a lava field (wip1_edge). Next: mostly
  black char, the cracks far thinner and sparser, glow only on the outermost metres.
- **Not yet done**: horde frames on the new ground (`after2.txt` below), the moods,
  the experience director's blocker (the crypt in the play space is gone with the
  new generator: there is no crypt now; confirm with a 5-minute autopilot run).

## Next, in order

1. Tame the ring (above); look at each place's landmarks at the edge (`--at X,Z`).
2. Horde frames at minute 25 for all four (`after2.txt`), and confirm the
   readability targets with experience: a stranger finds her in under a second;
   the living over the dead over the ground.
3. Bespoke landmarks where the kits fall short (Blender/make3d): the Legion's howe
   with VII and the dark seven-notch sigil, the den's fallen giant, the Roost's
   palisade with washing lines and red rags, COYLE-stencilled crates, the Dig's
   headframe and pump and the sough's outflow.
4. A per-place grass that reads from 30 m (the meadow's seven-blade tufts read as
   stars from above; it is off in arenas: `ArenaGround.Grasses` density 0, plumbing
   kept).
5. The atlas maps' look once their runtime exists (other places, in Ysolde's hand).
6. Measure draw calls and frame time with performance.

## Decisions (why)

- A scar is its people's own ground (story confirmed); never a "fen" for the Risen.
- Landmarks at the edge only; cover inside under 2.2 m (test-held).
- Ground albedo set per layer by target, not by eye per photograph: the scans
  ranged 0.013 to 0.42 mean albedo.
- No meadow grass in arenas until one reads from above.
- The ring is the scar's lip (story's words).

## Failures and gotchas

- A flat per-place value/saturation could not fix the barrow (its turf scan is 0.32
  albedo, its road 0.04): per-layer targets did.
- Broad shading inside a scan tiles visibly at 30 m whatever the anti-tiling:
  flatten it in the tool.
- The meadow grass (Grass.cs) reads as stars from the arena camera.
- Godot rewrites the arena `.import` files with uids after the first import: the
  tool now never rewrites an existing `.import`.
- `godot/assets` is a junction in this worktree: `git ls-files --others` lists the
  assets' `.uid` files through it; never delete untracked files under it.
- StoryLint reads `Is("x")` in logic as a fact read: the place's mood check is
  `HasMood`.
- A full headless `--import` after a merge takes 5–15 minutes; the arena arrays
  alone about 4 minutes.
- `--people` on the command line renames the offer to that people's word
  (`MapOffers.Renamed`); `--theme`, `--seed`, `--mood plain|ashen|...` exist for shots.

## Tools (scratchpad `arena/`)

`play.py NAME --timeout S -- [game args]` (a 1920×1080 run, frames in
`godot/.shots`), `batch.py SPEC.txt` (lines `NAME | args`), `sheet2.py OUT COLS WIDTH
names...`, `thumbs.py OUT ids...` (Poly Haven thumbnails). Specs: `after1.txt` (four
places at 22 m, 45 m and the edge), `after2.txt` (minute-25 hordes and moods).

## Collaborators

Experience (ad1f5623590e09883): readability, the dead, the camera. Combat
(a1d4562f44c7f6feb): what each arena must support. Skills (a63cd93fc73d5ed79):
effect colours. Performance (a7145e18b3eb78294). Story (a035208561a66c171): the
places' lore and names (its must-nots are in `ArenaPlaceTests`).

## Files to read first

`godot/logic/Maps/ArenaPlaces.cs`, `ArenaGen.cs`, `Arenas/Barrow.cs` (the pattern
for the others), `godot/src/World/ArenaGround.cs`, `godot/shaders/arena_ground.gdshader`,
`godot/src/World/ArenaEdge.cs`, `tools/godot/arena_ground.py`, `godot/tests/ArenaPlaceTests.cs`.
