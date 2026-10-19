# Armor 5 solver 2: the warden's town run and sprint, her left hand riding the sword's hilt

Context budget: 180k

You are a coding solver for the armor 5 lead. Return your report as your final message to the agent that spawned you. Do not message the coordinator ("main"). The coordinator approved this change for this MR.

## Where and the rules
- Worktree `C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\armor-5`, branch `armor-5`. DANGER: `godot/assets` is a junction. Never run `git stash`, `git reset --hard` or `git checkout .`. Restore named files only.
- Commit as you go, WIP is fine, and end with a commit carrying the numbers. Never commit `godot/art/anim/*.res`, `*_clips.json`, `tools/anim/manifest.json` or `.import` files.
- Building and packing her clips (`python tools/anim/build.py run_warden_town sprint_warden_town`) packs through Godot, so take a Godot turn first: `python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py take godot "<why>" --wait 600 --stale-ok --root <worktree>`, then `give`. Use `build.py --no-pack` to write the clip JSON only (no turn) while iterating. The measuring tools read the JSON in `tools/anim/out/clips`. Pack once at the end. After any Godot run, restore `godot/project.godot` and regenerated `.import` files by name.
- Change ONLY `run_warden_town` and `sprint_warden_town`. Leave every other clip byte-identical: check `stop_warden_town_l/_r` and `idle_warden_town`, and if the stops derive from the run's arms, keep them as they are. Never edit `keyed.py` WRAP/GRIP, the hand pockets, or another calling's runs.
- The male hero is out of scope. Don't build, test or judge him.

## The problem
In town she carries her one-handed sword sheathed at her left hip: the `hip_blade` socket in `godot/src/Actors/Arms.cs` `Sockets`, hilt forward and up, the scabbard about 30 degrees back, flat to her side. In the town run and sprint, her free LEFT forearm swings level through the hilt:
- 38-40 mm in `sprint_warden_town` frames 0-3 and 19-21
- about 28 mm in `run_warden_town` frames 0 and 20

No socket position fixes it (the first solver's notes are in `tools/scratch/armor5/solver/`).

The fix: in those two clips her left hand rides on the hilt, the classic carry that keeps a scabbard from swinging. The hand rests at the scabbard's throat just below the guard, the palm on it and the fingers loosely round it. The elbow is relaxed and bent, and the forearm lies along her side, never across her belly. The hand is fixed to the hilt in pelvis space, so it rides her hips. Her right arm keeps its swing as it is.

The throat is the piece's sheath point (`anchor_sheath`; `Arms.Sheathed`), pushed out by the warden outfit's clearance (`godot/art/anim/socket_clearance.json` warden hip_blade). It is the same point for every one-handed blade: chevalier_sword, viking_sword, oathbrand, longsword. Their sheathed points in pelvis space are in `tools/anim/data/arms_local.json` "sheathed" (key `<id>@hand_r`, "mount" and "v"). Check the hand on each.

## Where the code is
- `tools/anim/clips/run.py` `RUNS["run_warden_town"]` (the Gait's per-side `arms` callables, `{"arc","pole","frame":"chest",...}`; see `shield_guard`, `blade_carry`).
- `tools/anim/clips/sprint_stop.py` `sprint()` (`SPRINT_SWING_RUN`, `SPRINT_ARMS`).
- `tools/anim/gait.py` `run_cycle`.
- `tools/anim/keyed.py` (the hand spec: frames "char" and "chest" only; `two_bone_ik` in `tools/anim/rig.py`).

A hand fixed in PELVIS space may need a per-frame target in the chest frame, from the gait's own pelvis and chest at that phase, or a small post-pass that IKs the left arm onto the hilt per frame. Pick the cleanest that keeps the clip's other joints unchanged.

## Acceptance (numbers; the lead's max judge rules on the look afterwards)
1. The swords against her arm: `python tools/scratch/armor5/sockdeep.py run_warden_town sprint_warden_town --step 1`. Arm depth 3 mm or less for the four Blade1H keys, every outfit. Body stays 0. The shield, crossbow and other keys get no worse than `tools/scratch/armor5/deep2_after.txt`.
2. The hand on the hilt: per frame, her left hand and fingers go at most 2 mm into the piece (any of the four) and its palm sits at most 10 mm off it. Fingers don't need to be fitted (the owner: "animations rarely show fingers ... don't chase finger detail").
3. Her own body: `python tools/anim/motion.py run_warden_town sprint_warden_town --outfits` gives no new skin or outfit hits against the same command run before your change (save a baseline first: `--save base_town`, then `--against base_town`). Left arm into her body 0, the left hand not through her belt or skirt, and the elbow clear of the shield on her back (armscheck shield arm depth 5.4 now; no worse).
4. No pop. The game crossfades `idle_warden_town` <-> `run_warden_town` <-> `sprint_warden_town`, and the town stops. Report the left hand's and elbow's distance between `idle_warden_town`'s pose and the run's frames, and between the run and the sprint at matching phase. Keep the run-to-sprint change small (the same hand target). If idle-to-run is a big move, say so with the numbers; no idle change is in scope.
5. The pose reads natural at 1:1. The elbow is 70-120 degrees and stays off her ribs. Report the forearm's angle off vertical and the wrist's bend at frames 0 and 10 of each clip; the wrist stays within 35 degrees.
6. `python tools/anim/audit.py` raises no new flags on these two clips, and the clips loop seamlessly (the first frame equals the last).

## Report (your final message, under 40 lines)
What you changed (file and function), the numbers for items 1-6, the commit hash, and whether the final pack is done (heroine.res rebuilt).

Note: the lead's shoot is running in this worktree, and it reads `godot/art/anim/heroine.res`. Don't pack (no build.py without `--no-pack`) until `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\b8d13e5f-b1a5-4365-9d36-63505c60b8a1\scratchpad\armor5\shoot1.log` contains "STEP DONE".
