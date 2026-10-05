# Handoff: arena art

For the next arena art lead. Read these first:
- `docs/team/README.md`
- `docs/team/RESUME.md`
- this page
- `docs/team/arena_art.md` (the status page)

Then look at the sheets `docs/arena/hollow_night_2.jpg` and `docs/arena/dig_1.jpg`, and the concepts `docs/arena/concept_*.jpg`.

## The owner's words

- "AAA standard", "we are striving for perfection", "do we have soul?"
- "never settle: remake rather than polish", "how things are can be limiting".
- Story fights: "much more specialized and fun - smaller arena", with "proper arpg end bosses".
- Endgame: the **Wayfinder's atlas** (permanent maps, "like poe") and the **ember scars** (survivors arenas).

## The brief

Own every arena's look:
- the ground, dressing, landmarks, light and air;
- readability at the game camera;
- each story fight's own place, built to combat's outline (combat's code is the shape).

Judge at 1920x1080, at the game camera, in play with the horde. In a frame, at most a fifth may be flat black (`black.py`).

## Your order (from the coordinator, newest)

1. **The Vault's hall.** Combat built the fight (`Play/Story/Vault.cs`, `VaultOpened.Ground`):
   - the Decurion's shield line, the Scorpion's lanes, the Signifer's three standards, and the Barrow Lord;
   - it has no place art: the hall's walls are invisible, and the cover (fallen beams, sarcophagi, `VaultOpened.Cover`) and the standards are stand-ins;
   - build `Maps/Arenas/Vault.cs` as `HollowNight.cs` was built: an `ArenaShape`, wired in `ArenaGen.StoryShapeFor` ("vault_opened"), then set `VaultOpened.PlaceBuilt => true`;
   - the hall runs up the screen (north is -z): a roofless Legion hall open to the moon, wall tops standing, the stair's mouth in the north wall.
2. **The Roost** (`Play/Story/Roost.cs`, `RaidOnTheRoost.Ground`): four spaces, the ruts, the cage yard, the camp's yard and his fire, joined by gates. Combat's full note is in its message, copied under Collaborators below.
3. Then the arenas' remaining lifts:
   - the Barrow's howe, judged at its new end (`--at` must be re-found with `landmarks`);
   - the Ruts;
   - the Hollow at minute 25 and its stream;
   - the atlas maps (experience's ask below).

## Done (this lead)

- **The Hollow by Night:**
  - flat black is down from 26% to 5-19%;
  - story canopy cover ×0.5;
  - char and scorch stay at the banks' feet (`RingChar`, `scorch_out`);
  - past the edge is only a quarter darker (`past_dark`);
  - no crown on the camera side (`HollowNight.Screens`);
  - the lip and its veins burn low in short stretches;
  - Old Blue's rocks are stone knolls (`arena/knoll`);
  - the clough's watercourse is half buried;
  - moss stops at the banks' tops;
  - `PlaceBuilt` is true.
- **Canopy pools:**
  - the finest noise term is dropped;
  - the moon has `LightAngularDistance` 1.2° under any canopy (PCSS, `Atmosphere.Set`), so pools have a soft rim while contact shadows stay sharp;
  - the Hollow's hemi light is up from 1.6 to 2.0.
- **The Hollow's litter reads as leaves:**
  - dry_decay_leaves over forest_ground_06 (`tools/godot/arena_ground.py`);
  - the loose geometric leaves are matte (they were slate chips);
  - moss is round cushions by hash (`arena_ground.gdshader`);
  - the scanned moss clumps are gone;
  - the round Hollow's stream mist sheets are gone, and its slurry curls instead of streaking;
  - pale root scans are toned (`Dressing.ScanTint`).
- **The Dig:**
  - tips are steep heaps of coal and rock lumps (`arena/spoil`), closed to the fight;
  - the pit is a throat (`arena/throat`): rock walls, fallen rock, a red heart;
  - its smoke is a column;
  - the clay is lighter;
  - rust, ballast and slurry mud are near the clay's value and graded wide (they were camouflage blots);
  - thick slurry pools are their own yellow-green (`slurry_body`);
  - dry grass drifts over the floor.
- **The Barrow:**
  - the howe stands at the road's far end, the top of the picture; this is not yet judged;
  - tussock tips are warm, not grey stars.
- **Tool:** `dotnet run -c Release --project godot/balance -- landmarks --people P --seed N`. It prints where streams, rails and pieces lie, for `--at`.

## Grades now (honest)

| Place | Grade |
|---|---|
| Hollow by Night | ~3.5-4 |
| Hollow | ~3.5 |
| Dig | ~3.5 |
| Barrow | ~3 |
| Ruts | ~3 |

None is a 5 yet.

What still holds each back:
- **Hollow by Night:**
  - the den floor is a big flat dark field;
  - the root plate is not yet judged;
  - the watercourse still reads grey.
- **Dig:**
  - the slurry pool is too lime and too flat;
  - the tips are still dark masses at a distance;
  - the floor wants the concept's terraces and walls seen at the edge.
- **Barrow:**
  - turf and road are blue-grey all over;
  - mounds don't read;
  - no grave mounds or stones like the concept's.

## Decisions (why)

- **Flat black is measured** (`black.py`): at most 20%.
- **Whole leaves read as leaves.** Pale chips read as gravel, however they are toned.
- **A story place's banks and wood are its walls, seen whole.** Never a void of char.
- **Moss is cushions by hash.** A threshold on paint is a cut-out of carpet.
- **A paint layer that is a stain is graded wide and near its ground's value.** A narrow threshold makes camouflage blots.
- **Fire in a hole is a red heart between fallen rock.** A lit floor reads as a pool or a fried egg.
- **A landmark stands at the far end, away from the camera** (the top of the picture), never under the HUD.

## Failures and why

- **LightAngularDistance 2.5°** washed the pools out into general shading; 1.2° keeps them.
- **A noise texture as an emission map** turned the pit's fire pink (three channels).
- **A whole-floor emissive in the pit** read as molten gold; then evenly lit under rock, as a red plate with black spots.
- **Fallen trunks on the camera side** lay across the frame's foot as black bars.

## Gotchas

- **The worktree guard refuses complex bash** (heredocs, loops with variables, `cd X && git`). Use the Edit tool, and plain commands.
- **`godot/assets` must be a junction** to `public/assets` with `git update-index --skip-worktree godot/assets`. A merge can reset the flag; set it again.
- **Restore `.import` noise** before committing: `git checkout -- "*.import"`. Remove untracked generated `godot/*.uid` files if a merge refuses: `git clean -f -- "godot/*.uid"`.
- **Turns are a fair queue now.** `batch.py` waits up to 45 min for a godot turn, and `imp.py` up to 60.
- **Credits:** after a new scan, run `WRITE_CREDITS=1 dotnet test --filter CreditsTests`.
- **Shaders are read at each run's start.** Don't edit them mid-batch.
- **The Hollow by Night camera:** stage 2 starts at the neck. `--at` frames use world x,z.

## Tools (scratchpad `arena4/`; repoint the paths to your worktree)

- `batch.py SPEC PREFIX [--build]`, `play.py`, `imp.py`
- `black.py names...`, `sheet2.py OUT COLS WIDTH names...`, `crop.py NAME x0 y0 x1 y1 [scale]`
- Specs: `b4.txt` (all places with landmarks), `b6.txt`/`b7.txt` (the Dig and the Barrow), `b2.txt` (Hollows)

## Collaborators

- **Combat (a5115633c7006e4d4, handed off):**
  - outlines in `Play/Story/*.cs`;
  - `PlaceBuilt` per fight;
  - the den's mouth stays at (21,-39).
  - The Roost: four spaces climb north, joined by gates:
    - the ruts: a capsule (0,-46)→(0,-24), r 7, with pickets on its lips;
    - the cage yard: a circle at (-19,-17), r 8.5, with four cages, the fourth open, and the store at (-15,-10.5);
    - the camp's yard: a circle at (-5,4), r 12, with six crates at (4,-4) under a torch post (a crater after);
    - his fire: a circle at (0,33), r 14.5, the big fire at (0,45) with the children behind the cart line north of it. In phase 2, cart walls are dragged across at x = ±11, z 27-39: they need carts at the ends and dragged ruts.
  - Walls are only posts (`StoryPlace.Posts`): banks and rims must carry the edge.
- **Experience (a9f0d6c64d891d56d):** the atlas maps look like another game:
  - stylised kit canopies cover fights;
  - the moss blotches read as camouflage;
  - they want maps dressed from each people's arena kit, nothing tall over a fight, and the ground a quiet stage.
  - I told them the maps come after the arenas.
- **Performance (a0eb8c612c94d4aa5):**
  - landed BC7/BC5 mipmaps for the world scans;
  - asked for a report if any scan blocks up or changes colour. None seen in my frames;
  - should measure the PCSS moon under the canopy.
- **Skills:** the attack marks over the ground.

## Files to read first

- `godot/logic/Maps/ArenaGen.cs`, `godot/logic/Maps/Arenas/HollowNight.cs` (the model for a story place), `Arenas/Dig.cs`
- `godot/logic/Play/Story/Vault.cs`, `Roost.cs`, `StoryPlace.cs`
- `godot/src/World/Pieces.Arena.cs` (the knoll, spoil and throat pieces), `ArenaGround.cs`, `ArenaEdge.cs`
- `godot/shaders/arena_ground.gdshader`
- `godot/tests/ArenaPlaceTests.cs`
