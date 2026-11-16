# Lane C: the den, round 13 (brief, 15 Nov 2026 night, coordinator #14 on Fable; #15 spawns it)

Read `tools/scratch/coordinator/briefs/wave1_15nov.md` "## Common" first (read "#13" as the coordinator who spawned you). Type `su-lead-high`, judged, `Context budget: 250k`, `Item: dungeon-den`. Work in the EXISTING worktree `C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a04269dabfda645ea`, branch `dungeon-1` (tip `f715d6102`, pushed; suite 2860/0/11, DungeonTests 20/0). State file: the top block of `C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_coord12\dungeon_state.md` (read its first two bullets only; add an "R13" bullet with your first commit and keep it current at every commit). Round 11's numbers and list: `survivorsunchained_inputs\scratch_coord14\dungeon\R11_handback.md`. The worktree's `.import` and `godot/src/Shots.cs` churn is line endings: never commit it, never `git add -A`, no stash, no `reset --hard`, no `checkout .`.

The spawn prompt must carry: `Spawning: allowed`, `Context budget: 250k`, `Item: dungeon-den`, "Round cap raised for dungeon-den to 6" (round 11 and round 12 each spent one judge; two left) and "Round cap raised for dungeon-den-corridor to 3" (a NEW solver item for the corridor approach below; `dungeon-den-set` is spent at 6 of 6 and stays closed).

## The owner (15 Nov 2026, word for word)
"wind down the other dungeons and focus on the den." The demo is the den (`hollow`) only. The camera stays 62/24 and is never moved to match concept art. Targets (approved): `survivorsunchained_inputs\gpt_den\den_room.png`, `den_boss.png`. No ledges in the den. No Meshy, no Krea. New painted art only by ChatGPT imaging through the owner's Chrome, ONE Sonnet `claude` driver under `survivorsunchained_inputs\chatgpt.lock`, provenance per image (`gpt_den\PROMPTS.md`).

## Where it stands (round 12, max judge `a367e59d6b6369b13`)
Rooms and lairs CLOSE on seeds 11 and 23; CORRIDORS FAR, and they are what blocks. Sheet after the last solver: `godot\.shots\c_r12b.jpg` in the worktree (1:1 frames `v1_*.png`, `v2_*.png`). Two leads and six solvers tuned cards on the corridor walls; it did not work, so do not tune that route further.

## The corridor: a new approach (the coordinator's decision, with why)
Why it fails: a corridor is the generator's straight capsule with a thin layer of painted cards on a lit wall mesh. In a room the banks are far from the frame's middle; in a corridor both banks fill the frame, so every straight thing shows: the cards' floor-side border, the wall mesh's own edges, the ruled underside of the far bank, module seams.
Do, in this order, and stop at the first that reads right at 1:1 on both seeds:
1. **A corridor is dressed as a thin room.** Use the route that judged CLOSE in the rooms (edge stations by facing, banks first, root spills, boulders, bones), not the corridor card layer.
2. **The drawn wall line leaves the capsule.** Outward only (the walkable area and collision do not change): ragged alcoves and bulges of 0.5-2 m, seed-salted, filled with root mass, spills and stones so no open floor shows that she cannot walk on.
3. **Nothing straight is lit.** The wall mesh behind the banks is a dark mass with no drawn edge, top or side (hide it, darken it to the gloom, or cut it away); the foot line is always under a root spill, a stone or a ragged contact, never a card border.
4. Only if 1-3 fail: let the generator bend the corridor's centre line (same width, seed-salted). That changes walkable ground, so re-run DungeonTests and the hollow tables (`survivorsunchained_inputs\scratch_coord14\ledge\x_s1.md`, `x_s51.md` show the shape) and tell the coordinator before you commit it.
Also in the seed-23 corridor frame: a translucent RED RECTANGLE lies across the floor right of her (about x700-1200, y1800-1900 on the 2560-wide sheet's bottom-left frame) and a black smudge at (470-580, 560-720) in the frame. Find the cause of each (a stretched decal? a card?) before anything else: they are bugs, not look.
Build the judge's runner tools first, they are cheap and you will lean on them: a straight-edge detector, a grit measure on floor pixels, hue and saturation per brightness band on floor pixels.

## Then, the judge's ranked list for rooms and lairs (do not widen it)
1. Pits too neon: brightest green near (118,155,101), saturation .47 or less, hue about 97 deg; veins in clusters with 30-40 % of each pit dark; green haze spilling onto the floor; a ragged rock lip, not the braided ring; one or two dark empty pits per lair.
2. Room cards: B4 pale sliver (seed 23, 20-95, 625-865), B5 pale card (seed 23, 1337-1460, 283-423), B6 right-angle card (seed 11, 1070-1145, 150-195).
3. Floor material: fine grit 1.4-4.5 against the target's 4.8-9.3; every floor has the same diagonal brush streak; hold the darks at hue about 18 deg and saturation about .42 (the colour cap pushed them mauve); a worn path between the exits.
4. Beams are hard-edged planes; the seed-23 lair has a milky veil over (0-700, 0-520) with an edge at x about 650.
5. Edge rocks too pale: their brightest 10 % at luminance 85 or below.
6. Lair dressing: at most 3 root-crowns and 3 deer skulls, the rest small scatter. The seed-23 lair's lit floor reads salmon; a skull under an olive dome prop; small seams.
7. Checks never done: her skin before/after, boulder gain 1.4, frame time on a quiet machine.
The coordinator's own look at `c_r12b.jpg`, for what it is worth to your order of work: beside the targets the room floors still read empty and flat (the target has big lit boulders, a log, warm pools); density and the worn path matter more than further colour tuning.

## The gate
Your own 1:1 look says CLOSE on room, lair AND corridor, seeds 11 and 23. Then ONE max judge (`su-lead-max`, `Item: dungeon-den`, `Effort tier: always-seen`, `Context budget: 150k`) on one sheet, game left, targets right; apply a fail list once and judge again (two rounds left). Not CLOSE on your own look after two honest passes: stop and bring the coordinator the sheet. Nothing merges before a judge PASS; the coordinator merges and shows the owner the judged sheet. Lane E (art style) will own the den's grade and rig numbers once it starts: send it requests, do not fight it.
Tests before any hand-back: in `godot/tests`, `python ../../tools/quiet.py -- dotnet test`, and DungeonTests. Report: verdict first, branch@sha, suite, sheet path, the numbers table, what is left in order, agents used.
