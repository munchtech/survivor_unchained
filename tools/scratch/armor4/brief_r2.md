Context budget: 200k

You are a coding solver for the armor lead 4 (Survivor Unchained). Worktree C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\armor-1, branch armor-1. Work only there. Rules:
- godot/assets is a junction: never git stash, reset --hard or checkout . (check out named files only).
- Blender runs only under a turn: `python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py take blender "armor4 r2: <job>" --wait 60 --root <worktree>`, and `give` it back the moment the job ends. Godot as well (`take godot ...`). Never kill a process by name.
- Commit as you go (WIP is fine), with the trailer `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Don't push.
- No reading of the team docs: this brief is enough. Read code by grep and line ranges.

## Context
A smart armor slot part, the top `plate_top_plain` (built by tools/armor/build.py -> tools/armor/piece_blender.py in Blender on her body), with two tiers that add only adornment: `plate_top_etched` and `plate_top_gilded` (godot/art/armor/src/<id>/piece.json, built by tools/armor/adorn.py in about 2 s, no Blender). Material rows are in godot/art/people/outfit_materials.json. Each build writes godot/art/armor/<id>.gltf/.bin, <id>.sockets.json, armor_tuck/<id>.bin and its row in armor_index.json. Budgets: a large piece is at most 30k triangles at LOD0 and at most 2 draws (gilded is allowed 4 today, and must not grow past 4). Its gameplay LOD is at most 25% and its shadow mesh at most 10% (piece_lod.py runs inside the build).

A max judge at the game's cameras (1:1) ruled on round 1. Fix these three, then stop:

**F1. Gilded must read as the top tier.** At the close-up camera the 5 mm gold band is a 3-4 px pale line, and the sapphire is about 5 px. The warden's other pieces already carry gold trim, so gilded just matches the set, and etched's black band is the bigger change. The judge's fix:
- Gild the whole rolled rim (the cups' rolled edge) and the gore plate.
- Make the band about 12-15 mm, with a half-round bead profile, so it shows a lit line over a shadow line (a raised bead, not a flat strip).
- Make the sapphire 12 mm or more, in a gold setting (a bezel or claws), so it is 10+ px at the close camera.
Do it as data and adornment (piece.json; new profile or adorn options in adorn.py if needed). No shell, weight or clip change; a tier adds adornment and paint only. Keep the rolled edge and rivets of the base.

**F2. Etched: the blackened band reads as a matte, sewn-on ribbon** (pattern `etch_band_vine`, ground `darkleather`, sky 0). It must read as blackened metal: metallic 1, a dark base color, roughness about 0.45, so it picks up some sky sheen (try the existing `darksteel` material first, or a new `blacksteel` row in outfit_materials.json). Add small leaf shapes along the vine so it stops reading as a zigzag. The bright vine stays the plate's own steel.

**F7. The gore plate bends in the mixed look.** With the ranger's arms-in idle (`idle_stalker`), the gore plate between the cups reads as a bent sliver at the close camera, where the warden's reads as a neat plate. It is probably weighted to the breast bones and squeezed. Make the gore plate rigid: one blend of bones for the whole plate, taken at its center (as the rivets and buckles already ride one blend each; see `rigid_parts` in the build's ARMOR NUMBERS line), most likely spine_03 / the chest bone. This is a base change (piece_blender.py), so rebuild `plate_top_plain` (Blender, about 4 min) and then the two tiers. Check that the build still reports 0 skin through (`through_untucked`, `through_tucked`) in every pose, and say what the gore's standoff now is at `hug` and `arms_down`.

## Then
1. `python tools/armor/build.py plate_top_plain plate_top_etched plate_top_gilded` (a blender turn). It refuses if the four outfit files or heroine.glb change. Report its numbers: triangles, draws and LOD shares for each piece.
2. Reimport: `"C:/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe" --headless --path godot --import`.
3. Shoot under a godot turn: `bash tools/scratch/armor4/shoot.sh <abs path of tools/scratch/armor4/r2.txt>`. Frames go to godot/.shots/armor4/. Look at your own frames only at half size (`python tools/half.py <png>`), and only to check that the change landed: the lead's judge rules on taste.
4. Commit. Return under 400 words: what changed (files and functions), the numbers, the commit, and anything you couldn't do.
