# Handoff: arena art

For the next arena art lead. Read `docs/team/README.md`, then this, then
`docs/team/arena_art.md` (the status page), then look at `docs/arena/wip2.jpg` and
the concepts `docs/arena/concept_*.jpg`.

## The owner's words

- "AAA standard", "strive for excellent, above and beyond", "do we have soul?",
  "never settle: remake rather than polish", "how things are can be limiting".
- The endgame: "permanent ... our arpg build maps like poe and the normal arenas are
  for mindless survivors fun". Story's names: the **Wayfinder's atlas** (permanent
  build maps, "the places the road forgets", in Ysolde's hand, never the four scars
  by day) and the **ember scars** (a night's survivors arena). Each its own look.

## The brief (in full)

Own every arena's look: ground, dressing, landmarks, light and air, the fight's
readability on it, how each arena tells its place in the valley. Arenas are always
night; the atlas, once it exists, has day and night. Readability first: she reads at
the gameplay camera (56° pitch, 22 m opening, 31–34 m in a horde); enemies,
telegraphs (amber a blow, violet bad ground, pale blue stand here, grey solid) and
pickups read over the ground; the dead fade (experience's); ground effects never bury
the fight. Work with story (its must-nots are tests in `ArenaPlaceTests`) and the
experience director (readability over spectacle).

The current task list from the main session, in order: tame the ember ring (done);
lift the Hollow and the Dig to 4–5 (in progress, ~3.5 and ~3); full hordes at minute
25 on the new ground, judged at full resolution; the edge landmarks on screen; grass
that reads as grass from the arena camera.

## Done (this lead)

- **The ring** (`shaders/arena_ground.gdshader`, the lip block): the ground scorched
  inward; the char in voronoi plates with ash drifts and the ground's own grain; one
  white-hot line at `lip_at` (1.8 m) past the walkable edge, its distance divided by
  its slope (`dl`) so the noise that makes it wander cannot swell it into pools;
  veins on plate seams near it, coals strewn outward. Metres-inside comes per vertex
  in CUSTOM0 (float) from `Ground.cs`. Sparks emit along the line (`ArenaEdge`).
  The smoke curtain is dark and fades into the ground by depth.
- **Concepts** (Krea 2 via `concepts.py`): Hollow and Dig, the targets.
- **Hollow**: layers now `dry_decay_leaves` (warm litter), `forest_leaves_03` (rot),
  roots, mud, bed, needles, mossy rock; values raised, full hue. Moss is procedural
  in the shader (splat3 R, two-size domes, normals tilted). The stream has its own
  shader (`slurry_stream.gdshader`: dark water, the slurry's light in threads down
  the middle via UV2.x, scum at the banks) and two mist sheets (`mist_sheet.gdshader`).
  Pale stones and boulders along its banks, roots laid along the planned root lines,
  moss models on the wettest islands. Arena tree crowns dark (`KitLook.Look.Shade`).
- **Dig**: layers `dry_ground_rocks` (ochre clay and stone), `gravel_stones` (spoil),
  `stony_dirt_path` (ballast), `brown_mud_03` (slurry), `red_dirt_mud_01` (rust),
  burnt, `excavated_soil_wall` (faces). Rails as geometry (`ArenaEdge.Rails`:
  sleepers multimesh, iron with worn bright tops). The arena's own pieces
  (`src/World/Pieces.Arena.cs`, id `arena/NAME`): `headframe` (over the pit, origin
  on its floor, feet found by the ground probe) and `tub` (on the rails, a train of
  four near the pit). The pit: char on the lip only, bare walls, the floor hot; light
  at -5.5 m; a smoke vent (`MapBuild.Vents`). Slurry pools faintly lit (splat3 G).
- **Shader**: layer edges decided on heights a few mips up (follow clumps, not
  stones); splat3; slurry glow.

## Where it stands (honest)

Hollow ~3.5: reads as a forest floor with a sick stream; moss islands still a little
flat and big; the den (north edge, seed 311 near 11,83) is dark and unreadable.
Dig ~3: rails, tubs, headframe and pit read; the rust drifts and the black spoil still
read as flat blobs of paint; it lacks the concept's dry grass, stones and timber.
Barrow and ruts ~3, untouched this pass except the ring. No horde frames yet on the
new ground.

## Next, in order

See the status page's Next list. First: horde frames at minute 25 for all four.

## Decisions (why)

- Values raised and hue kept: the old "all under 0.1, half saturation" made grey mud.
- The ring is a line; only it and its veins glow.
- Moss and slurry glow live in a third paint so places can use them freely.
- The slurry stays faint: the Slurry Sow's glowing trail hurts, the stream must not
  read the same.

## Failures and gotchas

- A line drawn on a noisy distance swells where the noise flattens the slope: divide
  by the slope (screen-space derivatives, outside any branch).
- `texture()` and `fwidth()` inside a varying branch are undefined: sample first.
- The curtain lit from below read as flames on the ground from above; keep it dark.
- `source_color` uniforms take sRGB: pass hex colours, not linear values.
- Godot vertex COLOR is 8-bit: a metres field needs CUSTOM0 float (flags on
  `AddSurfaceFromArrays`).
- A full `--import` here rewrites hundreds of `.import` files with no content diff:
  stage your own files by path, never `git add -A`.
- PowerShell: `Set-Content -Encoding utf8` writes a BOM; batch.py reads utf-8-sig;
  commit messages need a no-BOM file (the first commit's subject has one).
- At 2.5 s the arena's title card covers the frame; past ~5 s the ember level-up
  cards can; 3.8 s is clean.
- `--cam` beyond ~35 does not widen much; the `--at X,Z` probe positions come from a
  throwaway test (`TmpRimProbe.cs.txt` in the scratchpad: rim radii, the stream, the
  rails, the vent, the howe, the camp, the den).
- The full test run can fail `A_map_can_be_walked...` on its 4-second timer under load;
  it passes alone.
- Copy `.godot` and `.packs/ground` from an older worktree to skip a 15-minute import
  and the downloads (robocopy); make `godot/assets` a junction to `public/assets`
  and `git update-index --skip-worktree godot/assets`.

## Tools (scratchpad `arena2/`)

`play.py`, `batch.py SPEC`, `sheet2.py OUT COLS WIDTH names`, `crop.py NAME x0 y0 x1 y1
[scale]` (full-res crops: always judge there), `concepts.py OUT [place]`. Specs:
`ring2.txt` (the four rings), `hd4.txt` (Hollow and Dig: middle, stream, den, pit,
wide), `feat.txt` (landmarks), `after2.txt` (minute-25 hordes, from the first lead).

## Collaborators

Experience (ad1f5623590e09883): readability, the dead, the camera. Combat
(a1d4562f44c7f6feb). Skills (a63cd93fc73d5ed79): effect colours; the lamplings'
white discs. Performance (a7145e18b3eb78294). Story (a73ca9d35d0c487a9): places'
lore and names.

## Files to read first

`godot/shaders/arena_ground.gdshader`, `godot/src/World/ArenaGround.cs`,
`godot/src/World/ArenaEdge.cs`, `godot/src/World/Pieces.Arena.cs`,
`godot/logic/Maps/ArenaGen.cs`, `Arenas/Hollow.cs`, `Arenas/Dig.cs`,
`tools/godot/arena_ground.py`, `godot/tests/ArenaPlaceTests.cs`.
