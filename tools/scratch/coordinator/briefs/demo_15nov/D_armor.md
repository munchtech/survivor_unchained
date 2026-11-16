# Lane D: the one new armor set, as the set that drops in the den (brief, 15 Nov 2026, coordinator #14 on Fable; scope CUT by the owner the same night)

Read `tools/scratch/coordinator/briefs/wave1_15nov.md` "## Common" first (read "#13" as the coordinator who spawned you). Type `su-lead-high`, judged, own worktree from integration, branch `demo-armor`. State file: a new TOP block in `docs/handoff/armor.md`, kept current from your first commit. Read only that page's top block ("P2 GEAR LEAD 16", lines 1-40) and the lines this brief names. It is all new meshes (the plate set took 16 leads): keep the list fixed and bring pictures early.

## The owner (word for word, 15 Nov 2026, night; these REPLACE "a couple of each armor slot")
- "actually change the armor scope to just the 1 new set - the one we designed to replace her current starter one, have it be the set that drops"
- "and don't even worry about new other slots, just the armor set"
- "I want something to have people do the dungeon a few times at least, that should be more than enough trying to get the armor pieces to have enough testing"
10 Nov, on the kit sheets: "Yes, build it" (`docs/team/OWNER_NOTES.md` "THE KIT SHEET IS PICKED": the pick is the design, not a frozen look).
Standing: sex appeal, never looking bad; she is always on screen; her only (never build, pack or test the male hero).

## The scope (the coordinator's reading; do not widen it)
ONE set: the gunmetal-and-gold kit of the sheets, one tier, as items in the slots that draw today (head, body, feet). She STARTS the den in her current starter look. The set is the den's chase: its pieces drop over SEVERAL clears, and that is the reason to run the den again. OUT: new equipment slots, pieces for other slots, the adornment tiers (`03_tiers.png`), second silhouettes, the old plate top's strap and gold faults.

## What exists (found 15 Nov; verify before you lean on it)
- The kit sheets: `C:\Users\munch\Desktop\survivorsunchained_inputs\gpt_sol\kit\01_turnaround.png`, `02_pieces.png` (helm, pauldrons, bodice, vambraces, belt and hip plates, boots), `03_tiers.png`. NOTHING of it is built.
- Drawn slots are Head, Body, Feet (`godot/logic/Rpg/Wardrobe.cs:28-31`, `Wear.cs:25-31`): the Body item draws top, collar, bottom, legwear, greaves, gloves, bracers, belt, skirt, pauldrons, cloak (so the set's body item must be whole, shoulders to legs); Feet draws boots; Head draws head.
- No head piece exists for her (Leather Cap and Iron Helm draw nothing). An empty body slot draws her Warden set (her starter look). Items without `wear` in `godot/data/content/items.json` draw nothing.
- Today's plate set (`godot/art/armor/`, index `armor_index.json`, sources `src/<id>/piece.json`) is merged; lead 16's verdict: far from the sheet in shape, "takes a new kit, not a revision".
- The pipe (`docs/team/PIPELINE.md` rows P2, P2a, P2b): `python tools/armor/piece_ship.py <id>` (build, follow onto `godot/art/people/heroine.glb`, install), `--check`, `pytest tools/armor`, then pose_tuck, cover, gear_fit, gear_wear. One Godot shoot turn is about 12 minutes; restore the 8 `outfit_tex/*.import` files by name after each shoot.
- Her shipped body is the p1 body B. `body-p1b@cd356aa07` is parked and NOT merged: do not merge it; if the pauldrons cannot be fit without it, say so to the coordinator with the numbers.
- Do not: rebuild or re-follow the old cups (`armor.md` line 30); stash, `reset --hard` or `checkout .` in a worktree with asset links; leave a blend loading images from another worktree (`tools/assets/blend_relink.py`); spend Meshy credits without a judge and the coordinator's word; `git add -A` (generated `.uid` and `.import` files stay untracked).

## The fixed list, in order
1. **The route, proven on the hardest piece:** build the BODICE of the sheet on her and look at it at 1:1 in the den (play camera) and at the wardrobe's close view. Route is yours: Marionette's Gear stage (`C:\Users\munch\Desktop\Marionette`, read `Marionette/HANDOFF.md` "Start here"; its main's uncommitted edits are not ours) or the native build (`tools/armor/native_build.py`). Pick by the result, in one bake-off, and write why.
2. **The set, whole:** helm (head); bodice, pauldrons, vambraces, belt and hip plates (body); boots (feet). Fit in motion on the demo's clips: Prowl idle, run, Sunder, Bladestorm's spin, the leap. Pauldrons are fit by CLEARANCE (the old spaulder's motion fit is open after three designs, `armor.md` lines 39 and 75: do not start a fourth design of it). Metal need not swing.
3. **PICTURE FOR THE OWNER (stop here and send it to the coordinator):** the whole set on her beside the sheet, 1:1, front and back, plus one den frame at the play camera. The drops wait for the owner's word on this picture.
4. **It is the set that drops, and the reason to run the den again:** three items (head, body, feet) with names, icons and tips. The den's boss drops ONE set piece per clear, weighted toward pieces the player does not own, so the whole set takes a median of 4 clears and never fewer than 3 (prove it with a seeded drop test over 1,000 players). The tip and the bag say which piece of the set it is and what is still missing. Check first that owned gear carries from one den run to the next in the demo's loop; if it does not, tell the coordinator at once. Anything else in the den's table that draws nothing leaves the table.
5. **Every mix looks right:** each piece alone over her starter look, any two, all three; removing a piece shows the starter look for that slot again. Tests for slot draw.
6. **Materials inside lane E's sheet** (ask the coordinator for it): plate and trim bands, the gold warm and saturated, the trim reading clearly over the plate.

## The gate
Your own 1:1 look says bet on every piece and every mix, standing and moving. Then ONE max judge (`Item: demo-armor`, `Effort tier: always-seen`) on one sheet: the set and the mixes at the close view and at the play camera in the den, on the five clips. Tests: `pytest tools/armor`; suite in `godot/tests`: `python ../../tools/quiet.py -- dotnet test`. Report: verdict first, branch@sha, suite, sheet path.
