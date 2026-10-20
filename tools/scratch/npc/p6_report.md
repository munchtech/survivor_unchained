The loader works: a Marionette package loads by name with no per-NPC code, its armor binds to the body's skeleton, and the clips play. I shot the test man at the play camera and at the close-up's closest zoom, idle and walking, and looked only at half-size copies. I made no taste call.

**Entry points**
- `godot/src/Actors/NpcPackage.cs` (new) does the work. `NpcPackage.Build(name)` loads `res://art/npc/<name>/manifest.json`, `body.glb` and each piece's file. `Read`, `Files` and `NameOf("npc:<name>")` support it.
- Any person or story NPC becomes a package by setting its body to `"npc:<name>"` (`PersonSpec.Body` in a story NPC's data). `People.Build` and `People.Files` (prefetch) pick that up. If the package is missing, it warns and falls back to the kit body.
- `HerWear.cs`: her piece-laying steps are now one shared method, `HerWear.WearPiece`, which her wear and the NPC loader both call. The materials therefore come from her code (`People.Fur` and `People.OutfitMaterials`, using `outfit_materials.json` and `metal_finishes.json`), not a copy. The extraction is mechanical and builds, but I didn't shoot her with `--wear` after it.
- At the play camera, each piece's lod1 and shadow meshes switch through `HerLod.For(p)`, `AddPiece` and `AddShadow`, and `HerLod.Merge` runs on them. Teeth and tongue hide at range as hers do.
- `HerJoints` drives the twist and share bones; the man's 79 joints include them.
- Clips are the shared library (`People.Clips()`) plus `folk.res`. `PersonView` now treats a package NPC as townsfolk when it holds nothing, so its idle and walk are the folk clips.
- Missing bones (`panel_front`, `breast_*`, `glute_*`): a piece bound to a bone the body lacks is moved to that bone's nearest ancestor the body has, with the bind pose recalculated so the piece doesn't move at rest. It logs one line per piece, for example `breast_l>spine_03, glute_l>pelvis, panel_front>pelvis`. Without this, Godot prints a skin error and pins those vertices to the root.
- `godot/src/Game/GameNpcShot.cs` (new) is the shot hook: `--npc NAME[:walk][:swap]`, called from `Game.cs` after the zone is entered.
  - Plain: the NPC stands 1.5 m to the camera's right of her, facing the camera.
  - `walk`: it walks a 1.4 m circle beside her.
  - `swap`: it takes her place and she is hidden, so the close-up frames it. With `walk` it walks on the spot, three-quarters to the camera.

**Dropping in a package and shooting it**
1. Copy Marionette's `generated/to_game/npc/<name>/` to `godot/art/npc/<name>/`.
2. Take a Godot turn: `python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py take godot "npc-1: <job>"`.
3. Import (a shot run does not import new files): `"C:/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe" --headless --path godot --import`.
4. Run `dotnet build` in `godot`.
5. Shoot: `bash tools/scratch/npc/shoot.sh <abs path to list>`. `tools/scratch/npc/shots.txt` is the list (the villager and the guard; change the name for another package). The four lines are:
   - `--quick warden --sex female --nohud --zone waystation --facing 0 --seed 1 --seconds 6 --npc NAME` (play, idle)
   - the same with `--npc NAME:walk` (play, walking)
   - `--quick warden --sex female --nohud --zone waystation --seed 1 --close 1 --idle-after 1 --seconds 9 --npc NAME:swap` (close-up, idle)
   - `... --close 1 --seconds 9 --npc NAME:walk:swap` (close-up, walking)
6. Give the turn back.

`shoot.sh` writes its frames to its second argument (default: a scratch folder, its `O=` line).

**What the loader needs beyond the contract**
1. **Hidden skin:** `hide` is read as triangle indices into the body mesh's surface whose material is named exactly `skin`, in glTF primitive order. The `skin_head` surface and other meshes can't be hidden. The order survives Godot's import here: the 60 test triangles dropped exactly where they were picked, on the upper chest. `hide` may also be a string naming a file in the package: a `.json` file holding such an array, or a binary file of bind positions in the `armor_tuck` record format. In the binary form a triangle is dropped when all three corners are listed, which doesn't depend on order. Recommend the binary form if Marionette can write it.
2. **Mesh names in a piece:** each piece's meshes should be named `<id>.<slot>.<mat>`, `<id>.lod1.<mat>` and `<id>.shadow`, with `<id>` equal to the manifest's `id`. A full mesh pairs with the lod1 mesh that has the same `<mat>`.
3. **Materials:** a piece's material names must be keys in `outfit_materials.json`, or they keep their imported material.
4. **Skeleton:** a piece's glb must contain its own skeleton, the full one or the body's, so missing bones can be re-bound.
5. **Root node:** `body.glb`'s root node must be `Armature` (as shift08_man's is), so clips find `Armature/Skeleton3D`.
6. **Body materials:** the body keeps its own imported materials, with vertex colour switched off as a colour on the teeth and tongue. It does not use her skin shader.
7. **Unused fields:** `height` and `joints` are read but not used. NPC scale is the story NPC's own `Scale`.
8. **Manifest defaults:** `sex` picks folk walk and idle (woman or man), default `"male"`. A missing `file` defaults to `armor/<id>.glb`.

**Test package:** `godot/art/npc/test_man/`. The body is `shift08_man.glb` with Marionette's test helmet, chest and socket nodes removed. The armor is `plate_top_plain` repacked as a glb, with its textures pointing at `art/people/outfit_tex`, and the manifest hides 60 chest triangles. Scripts to rebuild it are in `tools/scratch/npc/`. As expected, the plate doesn't fit him, and the hidden triangles show as holes around it.

**Acceptance**

| Check | Result |
|---|---|
| Loads by name, no per-NPC code | Yes |
| Armor bound to the body skeleton | Yes: no T-pose; the plate stays on his chest idle and walking |
| Clips play | Yes, idle and walk |
| Missing bones cause no errors | Yes |
| No new errors in the log | Yes: the same three exit-time texture-leak errors appear with and without `--npc` |
| `dotnet test` | Passed 977, failed 0, skipped 8 (985 total) |

**Half-size frames** (in `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\b8d13e5f-b1a5-4365-9d36-63505c60b8a1\scratchpad\marionette\p6\shots\`)
- `npc_play_idle_half.jpg`
- `npc_play_walk_half.jpg`
- `npc_close_idle_half.jpg`
- `npc_close_walk_half.jpg`

The logs (`log_*.txt`) are in the same folder.

**Commits** on `npc-1`: `71e1f716` (loader, shared wear method, shot hook) and `2eb4a6e7` (test package, one rebind log line per piece, shot list and scripts).

The worktree's first `--import` rewrote many unrelated tracked `.import` files. That's Godot's churn, not this work. I left them uncommitted rather than restoring them; they need restoring file by file or ignoring before any merge.
**Update (19 Oct, P6 skin fix):** `test_man` is removed. The packages are now `godot/art/npc/npc_villager` (warden skirt, boots, bracers) and `godot/art/npc/npc_guard` (warden greaves, boots, bracers, pauldrons). Marionette's "Send to game as NPC" (parts panel, `armorcarry.js` `npcPackage`) wrote both, and their body and head skin maps are now painted. `shots.txt` shoots both of them.
