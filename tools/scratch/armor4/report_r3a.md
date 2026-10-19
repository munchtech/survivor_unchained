I didn't finish round 3. I ran out of context before the build, the shots, the F7 fix and the test run. The code for F2 and F5 is written, compiles and is committed as WIP. Nothing is rebuilt and nothing is shot. The godot turn is given back, and I never took a blender turn.

**Stale C# build, which affects the judge's round-2 verdict.** The worktree's `SurvivorUnchained.dll` predated metal r4 (its strings `metal_detail`, `piece_graze` and `OUTFIT_DEBUG_VIEW` were missing). Shots don't rebuild C#, so the round-2 frames were rendered without the current metal shader setup. After `dotnet build` the steel looks clearly different. Run `dotnet build` in `godot/` before every shoot.

**F2: why the vine reads flat cream.** The vine is gaps in the black film, so what shows through is the bare shell. The band sits 12 to 21 mm in from the rim, inside the metal shader's dirt band (2 to 20 mm in from a rim) and where the shell sees less sky. That grime makes the shell there partly non-metal, so it is lit evenly instead of catching highlights: a pale matte line in light and shadow alike. The fix (`tools/armor/adorn.py`):
- `vine_band()` now also returns the vine as its own film (the same triangles that fill the gaps). It goes into the shell's steel mesh, so it adds no draw call (etched stays at 3), and it takes the cup's own sky and curvature and sits outside the dirt band.
- `film_from()` and `film_strip()` gained an `edge_min`, and the ground films use 0.021 so they also sit outside the dirt band.
- `blacksteel` in `outfit_materials.json` is now sRGB about 74 (0.29) at roughness 0.3. The shader used to ignore a material's roughness; `People.OutfitMaterials` now applies a metal row's `roughness`.
- The etched `piece.json` now has sky 1.0, conv 0.5, leaf width 2.6.

**F7: measured, not fixed.** `tools/armor/gore_idle.py` poses her and the top the way the game does, tucks her skin as the game does, and measures over the gore's footprint. Current build, minimum clearance:

| Idle | Clearance |
|---|---|
| idle_warden | 1.65 mm |
| idle_stalker | 1.03 mm |
| idle_arcanist | 1.15 mm |
| idle_reaver | 1.32 mm |

Three of the four are under 1.5 mm. Under the gore, the tuck is as low as 0 mm, median 2.67 mm. Still to do: in `piece_blender.py` after `tuck_of`, set her skin under the gore's footprint to at least 3 mm of tuck (full in the middle), rebuild, and re-run the script until all four are at least 1.5 mm.

**F5: method chosen and coded.** The game drops the strap's triangles when it lays out the piece, keyed to the pauldrons slot being filled. This adds no draw call and no shader change, and covers both the full mesh and the gameplay mesh. `tools/armor/under.py` (run by `build.py` after each piece) writes the strap points a pauldron covers, 5 mm in from the edge. It writes one cut per known pauldron (warden, ranger) and a shared `*` cut, covered by every pauldron, for any other. The game side is `logic/Rpg/ArmorUnder.cs`, a new `Under` field in `ArmorIndex.cs`, and `HerWear.Trim()`. One risk to check in the shots: a cut strap could open a gap when the pauldron lifts away.

**Tests:** `godot/tests/ArmorUnderTests.cs`, 6 tests, not run yet.

**Commits:** 906ae04a and 190f4682.

**Next steps:**
1. The F7 tuck fix and `gore_idle.py`.
2. `python tools/armor/build.py plate_top_plain plate_top_etched plate_top_gilded` (a blender turn).
3. Reimport, `dotnet build`, then shoot `r3.txt` and run `strips.py`.
4. `dotnet test` in `godot/tests`.

Files:
- C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\armor-1\tools\armor\adorn.py
- C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\armor-1\tools\armor\under.py
- C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\armor-1\tools\armor\gore_idle.py
- C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\armor-1\tools\armor\build.py
- C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\armor-1\godot\logic\Rpg\ArmorUnder.cs
- C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\armor-1\godot\src\Actors\HerWear.cs
- C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\armor-1\godot\src\Actors\People.cs
- C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\armor-1\godot\tests\ArmorUnderTests.cs