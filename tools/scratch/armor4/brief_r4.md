Context budget: 150k

You are a worker for the armor lead 4 (Survivor Unchained). Worktree C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\armor-1, branch armor-1. Work only there. Rules: read only the "Rules" section of tools/scratch/armor4/brief_r2.md (turns, junction, commits). Report to the lead that spawned you (your final message), not to "main".

## 1. Remove the strap hide under a worn pauldron (a judged regression)
Commit 906ae04a added it: tools/armor/under.py, its call in tools/armor/build.py, godot/logic/Rpg/ArmorUnder.cs, the `Under` field in godot/logic/Rpg/ArmorIndex.cs, `HerWear.Trim()` and its call in godot/src/Actors/HerWear.cs, godot/tests/ArmorUnderTests.cs, and the built files godot/art/armor/armor_under/ (with the `under` entries it wrote into godot/art/armor/armor_index.json). Remove all of it (git rm the new files; edit the others by hand; never `git checkout .`). KEEP everything else in 906ae04a: the etched vine film in tools/armor/adorn.py, the etched piece.json, outfit_materials.json `blacksteel`, and People.cs's metal roughness. Check with `git show 906ae04a -- <file>` which hunks are which.

## 2. Etched under 30k triangles at LOD0 (now 33,664; the vine film adds ~8k)
In godot/art/armor/src/plate_top_etched/piece.json and, if needed, `vine_band()` in tools/armor/adorn.py: halve the vine wave's segment count and keep leaves on every other crest. The target is 30,000 or fewer triangles at LOD0, still 3 draws or fewer. Don't change the band's width, colors or materials.

## 3. Build, check, shoot
1. Take a blender turn and run `python tools/armor/build.py plate_top_plain plate_top_etched plate_top_gilded`; give the turn back. From each piece's ARMOR NUMBERS line, grep only `triangles`, the draws and the skin-through counts; never print the whole line. Confirm `armor_index.json` has no `under` entries.
2. `python tools/armor/gore_idle.py`: the four idles must still be 1.5 mm or more. Report the numbers.
3. In godot/: `dotnet build` (0 errors), then reimport (`"C:/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe" --headless --path godot --import`).
4. Under one godot turn: `bash tools/scratch/armor4/shoot.sh <abs path of tools/scratch/armor4/r4.txt>`, then `python tools/scratch/armor4/strips.py`. Grep the shot logs (godot/.shots/armor4/log_<name>.txt) for `stale tuck` and for ERROR lines other than the RID leak and RenderingServer lines at exit.
5. Run `dotnet test` in godot/tests in the background meanwhile, and report passed/failed/skipped.
6. Commit (trailer `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`). Don't judge the pictures.
Return under 250 words: what you removed, the etched change, the numbers (triangles and draws per piece, the gore clearances), the tests, the log findings, the commit.
