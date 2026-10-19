Context budget: 200k

You are a coding solver for the armor lead 4 (Survivor Unchained), round 3, the last round. Worktree C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\armor-1, branch armor-1. Work only there. The same rules and context as round 2: read tools/scratch/armor4/brief_r2.md (its rules and Context sections), then round 2's judge verdict, tools/scratch/armor4/verdict_r2.md. Round 2's solver changed tools/armor/adorn.py, tools/armor/piece_blender.py, the three godot/art/armor/src/plate_top_*/piece.json and outfit_materials.json (`blacksteel`); see commits ea0e185d and 0ff9c5ed (`git show --stat`).

Fix these three, rebuild, shoot, commit, report. Stop there.

**F2, etched** (verdict_r2 has the judge's words). The vine must be the cup's own steel and light like it. Find out first why it renders flat cream-white, equally bright in light and shadow: is it a gap showing an unlit layer, a film whose material or normals are wrong, or a texture? The metal shader draws only its texture's mean color, so the etch is a geometry film layer. Fix that cause. Then: blacksteel ground around sRGB 70-80, roughness about 0.3; the vine a smooth wave with alternating leaves about 4 mm long. Keep etched at 3 draws or fewer.

**F7, the gore over her skin in the ranger's idle.** In `idle_stalker` (arms in) her cleavage skin comes through the lower half of the rigid gore plate. Make the plate's tuck cover the gore's whole footprint (full tuck under it, or sink her skin about 3 mm there), so no calling's idle shows skin through it. Measure the minimum skin-to-plate clearance over the gore footprint in each calling's idle (idle_warden, idle_stalker, the arcanist's and the reaver's idles; the clip names are in godot/art/anim/heroine_clips.json). Use the build's pose machinery, or sample those clips' poses on her armature in Blender. It must be at least 1.5 mm, with the tuck applied as the game applies it. Report the four numbers.

**F5, the strap through the pauldron.** In the heavy swing (`--hold sword_heavy@0.5 --facing 30`, the close camera) the top's left shoulder strap pokes through the warden's pauldron. The fix is slot-aware: when her pauldrons slot is filled (godot/src/Actors/HerWear.cs knows what she wears), the part of the strap a pauldron covers isn't drawn. The strap ends about 5 mm inside the pauldron's rim. Pick the cheapest robust way and say which:
- a separate strap-top mesh that HerWear drops when pauldrons are worn (mind HerLod.Merge's merge by material and the gameplay LOD);
- a vertex flag the outfit shader discards on a uniform;
- or another way.
It must hold for any pauldron, not just the warden's, so key it to the slot being filled. Add a unit test if the logic is in logic/ (no Godot). Run `dotnet test` in godot/tests at the end (about 5 min, in the background).

Then:
1. Build what changed (`python tools/armor/build.py <ids>`, a blender turn), and reimport.
2. Shoot `bash tools/scratch/armor4/shoot.sh <abs path of tools/scratch/armor4/r3.txt>` under a godot turn, and make the strips: `python tools/scratch/armor4/strips.py`.
3. Check at half size only that your changes landed; the judge rules on taste.
4. Commit. Return under 400 words: the cause of F2, what changed (files and functions), the F7 numbers, the F5 method, the tests, and the commit.
