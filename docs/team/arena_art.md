# Arena art: how every arena looks, and reads

Status page for the arena art lead (agent `ab03c3c85571e5085`, branch
`worktree-agent-ab03c3c85571e5085`). Sheets in `docs/arena/`.

## The brief

Own every arena's look: ground, dressing, landmarks, light and air, the fight's
readability on it, and how each tells its place in the valley. The endgame has two
kinds, each with its own identity: the **ember scars** (the survivors arenas, a
night each, `ArenaRun`) and the **Wayfinder's atlas** (the permanent build maps,
"like PoE"; story: "the places the road forgets", in Ysolde's hand, never the four
scars by day).

## Audit (before), 1920×1080, all four peoples, empty, wide and at minute 25

Sheets: `docs/arena/before_empty.jpg`, `before_wide.jpg`, `before_horde.jpg`.
Grades 1–5 (the owner's bar is 5). Arenas are always night (the ember burns only in
the dark), so "day and night" applies to the atlas, not the scars.

| Arena | Soul | Place | Reads | Beauty | Why |
|---|---|---|---|---|---|
| The Risen (barrow) | 2 | 2 | 2 | 2 | one lit lawn with lilac gravel blotches; KayKit graves in rows are the only story; skeleton crowd blue-grey on grey-green |
| The Pack | 1 | 1 | 1 | 1 | same lawn; wolves a dark mass on dark green; flat-shaded pale-blue cliff rocks in the play space read as the pale-blue "stand here" telegraph |
| The Kerchiefs | 1 | 1 | 2 | 1 | same lawn; a few broken walls and crates; the red crowd reads, nothing says "road" |
| The Lamplings | 1 | 1 | 2 | 1 | same lawn; lanterns; nothing says "dig" |

Common faults: every arena the same ground whatever its name ("The Ashen Fen" was a
Risen map); the clearing's edge a hard tree line with no meaning; the ground's value
as bright as the dead; no landmark at all; cover up to 8 m tall (crypts) in the play
space.

## Current state

**Handed off** (context past 500k): `docs/handoff/arena_art.md` has the state, honest
grades from the first on-screen sheets (`docs/arena/wip1_*.jpg`: barrow ~3, ruts ~3,
hollow ~2, dig ~2; the ring too strong, a lava field) and the next steps.

**Built and seen on screen (first pass):**
- `logic/Maps/ArenaPlaces.cs`: each people's place (barrow, hollow, ruts, dig), its
  own night (key, hemi, fog, grade) and air (mist, haze, moon dapple, ember colour),
  and moods read from the table's adjective (Ashen, Drowned, Lampless...). Names in
  the valley's words from story.
- `logic/Maps/ArenaGen.cs` + `Arenas/{Barrow,Hollow,Ruts,Dig}.cs`: an arena per
  place. Common: the wandering edge, the ember ring's char, the walls, cover kept off
  lanes. Barrow: the Legion's straight road, long barrows, opened graves, ash, a
  sealed howe and a broken gate at the ends. Hollow: a bowl, the slurry stream, roots
  from great trees, the den under a fallen giant, the Pack's runs. Ruts: the hollow
  way with water in its ruts, the ravine's walls, the camp (fires, palisade, cage,
  the pot for forty), wrecked wagons. Dig: the pit at the edge with its glow and
  headframe, rails and carts, spoil heaps, slurry pools, terraced walls, gold lamps.
- `tools/godot/arena_ground.py` → `godot/art/arena/<place>/`: seven Poly Haven CC0
  scans per place (names in `layers.json` and `public/assets/CREDITS.md`).
- `shaders/arena_ground.gdshader`, `View/ArenaGround.cs`: the place's materials
  height-blended by two paints; standing water that holds the moon; trodden ground;
  the ember's char with glowing cracks; dapple; the dark past the ring; the whole
  ground held below the living (value, sat).
- `View/ArenaEdge.cs`, `shaders/ember_curtain.gdshader`: sparks off the ring, a low
  lit smoke curtain past it, mist in a fog volume, the stream's water.
- Tests: `ArenaPlaceTests` (each people's place; nothing over 2.2 m in the fight
  but thin posts; the story's rules; names and moods; the ring all round).

## Key decisions

- **A scar is its people's own ground** (story confirmed): never "a fen" for the Risen.
- **Landmarks at the edge only; cover inside under 2.2 m** (thin poles excepted):
  the experience director's rule, held by a test.
- **The ground is the darkest thing that matters:** its value and saturation are held
  down in the shader so the living, the dead and her light read over it.
- **The ring is the scar's lip** (story's words): char and glowing cracks, sparks,
  smoke lit from below; the place goes on past it into the dark.
- **Story's must-nots are in code:** no crypt (the sealed door is the Verge's), no
  human bones in the Hollow, no skulls in the Kerchiefs' camp, empty rusted lamp
  posts on the Legion road (no oil for years), lamplings' lamps gold.

## Next

1. Tame the ring; check each place's edge landmarks; minute-25 hordes on the new
   ground; iterate every place to 5s.
2. Per-layer albedo targets (`ArenaGround.Looks`) are the value knob; the meadow
   grass is off in arenas (it reads as stars from above).
3. Landmark art per place (the Legion's sealed howe with its VII and dark sigil, the
   den's fallen giant, the Roost's palisade and washing lines, the Dig's headframe
   and pump) via Blender/make3d where the kits fall short.
4. The atlas maps' look (other places: a Legion camp in the hills, an Order chapel,
   the Kiln Ford's ferry), once their runtime exists.
5. Measure draw calls and frame time with performance.

## Notes for other areas

- **Experience (ad1f5623590e09883):** the ground's value is held under the living and
  the dead; the crypt is gone from the play space (the new barrow has none; a test
  holds it); confirm with a 5-minute autopilot run.
- **Skills:** large ground effects should not be pale blue, amber, violet or grey
  discs; the ground under them is now darker and less saturated.
- **Performance:** new per arena: one ground material (7-layer arrays), ~700 ring
  sparks, a smoke ring mesh, one fog volume, up to ~30 omni lights (ring 14).
- **Story:** names wired as sent (`ArenaPlaces.Names`, `Moods`).
