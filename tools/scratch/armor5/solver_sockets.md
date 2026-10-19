# Armor 5 solver: retune her sheathed-weapon sockets so no piece goes into her skin

Context budget: 150k

You are a numeric solver for the armor lead (armor 5). Return your report as your final message to the agent that spawned you. Do not message the coordinator ("main").

## Where and the rules
- Worktree `C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\armor-5`, branch `armor-5`. Work there only, and never in the main checkout.
- DANGER: `godot/assets` is a junction. Never run `git stash`, `git reset --hard` or `git checkout .`. Restore named files only (`git checkout -- <file>`).
- Commit as you go to `armor-5`, WIP is fine, and end with a clean commit carrying the numbers. Never commit `godot/art/anim/*.res`, `*_clips.json`, `tools/anim/manifest.json` or `.import` files. They show as modified and must stay that way.
- Heavy Godot runs need a turn: `python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py take godot "<why>" --wait 600 --stale-ok --root <worktree>`, then `give` afterwards. `tools/scratch/armor5/dump.sh <log>` already takes the turn, imports, runs the ArmsDump and gives the turn back. After any Godot run, restore `godot/project.godot` and any regenerated `.import` files by name. If `git diff` is empty for a file, leave it.
- Run `cd godot && dotnet build` after editing C#, before the dump.
- Her clips are already packed in `tools/anim/out/clips`. Don't rebuild them.
- Out of scope: clips, `tools/anim/keyed.py`, the hand pockets in `WeaponSockets.cs`, `fistfit.py`, and any armor `piece.json` or `armor_index.json`.

## The problem (measured, `tools/scratch/armor5/deep1_before.txt`)
She carries her pieces sheathed only in town, and only the warden has town clips today: `idle_warden_town`, `run_warden_town`, `sprint_warden_town`, `stop_warden_town_l` and `stop_warden_town_r`. Every calling's town set will reuse the same sockets later. So measure every kind on those five clips, against every outfit's clearance.

`python tools/scratch/armor5/sockdeep.py idle_warden_town run_warden_town sprint_warden_town stop_warden_town_l stop_warden_town_r --step 1` splits the worst depth of each sheathed piece into her ARM skin versus the rest of her BODY, and gives the clip, frame and skin bone. It takes about 12 minutes on 5 processes, so use `--step 3` and `--outfits warden,none` while iterating. Worst values now (mm, over all outfits):
- **hip_blade** (Blade1H: chevalier_sword, viking_sword, oathbrand, longsword). This is the warden's sword and the one the player sees today, so it comes first. Body 0. Arm 37-40: her LEFT forearm (`lowerarm_twist_01_l`) passes through the piece at `sprint_warden_town` frames 0-3 and 20-21.
- **back** (shield_round): left forearm 9.2 at `run_warden_town`@10; body 2.3 (thigh_l, `stop_warden_town_r`@9).
- **hip_loop** (Axe: viking_axe on the right and, mirrored, on the left; Blunt: the mace shares the socket): thigh_r 26-58 at `idle_warden_town`@25, thigh_l 45-74 at `sprint_warden_town`@16, mace pelvis 67-82. Its `At` is y 0.50 (knee height); check it.
- **hip_belt** (wand): spine_03 skin 21-36 at `sprint_warden_town`@11.
- **sling** (crossbow): body 5-15 (pelvis, spine_03), left upper arm 7-23 at `run_warden_town`@10.
- **belt_back** (daggers): 0. Leave it.
- **back_diag** (Blade2H zweihander, Axe2H snake_axe): their tips reach her calves (17-63). She can't hold these kinds (NPC only), so try them only if it's cheap and report either way.

## Files
- The socket rows are `godot/src/Actors/Arms.cs` `Sockets` (about lines 284-305; each row's comment says what it's meant to look like) and `Sheathed()`. Rows are in skeleton space at rest: `At`, `Shaft`, `Thick` and `Normal`, with `Mirrors` for the left hand.
- `tools/anim/data/arms_local.json` "sheathed" holds each key's points at its bare socket in the bone's space, plus "mount" and "normal". ArmsDump writes it (`godot/tools_scenes/ArmsDump.cs` via `arms_dump.gd`).
- `tools/anim/armscheck.py --sockets` refits `godot/art/anim/socket_clearance.json` (each outfit's push-out along the socket normal) and prints worst depth into skin and into the outfit. `--keep` measures without refitting.
- Tests that may pin socket values: `godot/tests/SheathTests.cs` and `WeaponSocketsTests.cs`.

## Method
Model trial rows in Python. Move the dumped "sheathed" points by new_mount times the inverse of the old mount, building the mount as `Sheathed()` does. Search near each row, so there is no Godot run per trial. Then write the rows to Arms.cs, run `dotnet build`, run the ArmsDump on one turn, run `armscheck.py --sockets` (the refit, and commit the clearance file), confirm with sockdeep.py on the five clips at step 1, and run `dotnet test --filter` on the socket and sheath tests.

## Acceptance
1. BODY depth 0.0 mm (at most 0.5) for every key and every outfit (warden, arcanist, reaver, ranger, none) on the five clips, for hip_blade, back, hip_loop (both axes; the mace too if the same row allows it), hip_belt and sling.
2. ARM depth as low as the socket allows, target 3 mm at most. Two matter most: the sword against her left forearm in the sprint (38 mm now) and the shield against her left forearm in the run (9). If the sword can't get under about 5 mm without breaking its look, stop at the best that keeps the look and report the residual with its frames. I will route that to animation (a town sprint with her left hand riding on the hilt).
3. The look holds: each row keeps its comment's intent. The sword hangs at her left hip, hilt forward and up, the scabbard about 30 degrees back, flat to her side. The axes and mace hang head up at her hip outside the thigh. The wand is tucked in the belt, crystal up. The crossbow is slung across her back. Angles stay within about 15 degrees of now unless the numbers demand more. The piece stays snug: report each key's nearest gap to her skin or outfit at `idle_warden_town` frame 0 before and after. A piece may float at most 10 mm more than now, so it never hangs off her in the air. Update each row's comment if its description changes.

## Report (your final message, under 40 lines)
The new rows, a before and after table (key x outfit, body/arm mm), the snug gaps before and after, any residual with its frames, the test result, and the commit hash.
