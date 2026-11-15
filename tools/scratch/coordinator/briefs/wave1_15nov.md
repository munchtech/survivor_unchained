# Wave 1, 15 Nov 2026 (coordinator #13): dungeon look, Warden polish, skin light

## Common (every lead of this wave)

You report to coordinator #13 (the main session). SendMessage to "main" only for a blocker or a decision that is the owner's; progress goes in your state file, not to me.

The week (the owner, 15 Nov): "we need to get towards having a playable demo with our female warden polished enough to play at least a dungeon or 2 worth of gameplay.  dungeons should not be the same everytime (most arpgs are like this)". The demo is cut on Friday 20 Nov. No lane measures arena nights.

- **Your state file:** read its TOP block first and restart from its "next in order". Keep that top block current from the start (state, branch@sha, done, next in order, cost). Compaction makes the cut at about 192k and you keep working after it. There is NO stop line: never stop or hand off because of context size. A full handoff only at a gate (a judge's verdict), at the end of the day or at a planned stop.
- **Read by section only** (grep the heading, read the range), from the main checkout `C:\Users\munch\Desktop\survivorsunchained`: `docs/team/README.md` "How we work", "Safety and the owner's machine", and in "Working lean" the bullets "The finish line", "Project finish line" and "DANGER, the assets junction"; `docs/handoff/lead_brief.md` "Effort" and "Usage rules". Nothing else whole.
- **Work only in your worktree,** on your branch. Commit as you go, run the suite before each commit, push your branch. Do NOT merge into integration: the coordinator merges. Merge `origin/claude/vigilant-galileo-l6jqyx` into your branch before judged shots (mind the junction paragraph if `godot/assets` is a link).
- **Runs:** heavy jobs take a turn (`python tools/turn.py take godot|blender|gpu "<area>: <job>"`, give it back at once). Noisy runs go through `python tools/quiet.py -- <cmd>` or `python tools/turn.py run <kind> "<who>: <job>" -- <cmd>`. Never kill a process by name. Working looks at half size (`python tools/half.py <files>`).
- **Judging:** your own 1:1 look and the numbers come before any judge; spend the judge only when you would bet on PASS. Your first FAR on your own look = stop and report. A judge is a fresh `su-lead-max` at `effort: "max"` whose brief carries `Context budget: 150k`, `Effort tier: always-seen`, `Item: <name>`, the sheet paths, the numbers, the owner's words, a checklist and the two finish-line sentences. It looks at game-camera frames at 1:1.
- **Waiting:** hand a long batch to a `su-runner`; do not poll. A decided mechanical change goes to a `su-worker`.
- **Final report** (your last message): verdict or result first, branch@sha pushed, suite numbers, sheet paths, what is left.

## Dungeon look (critical path)

Worktree `C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a04269dabfda645ea`, branch `dungeon-1@0c28cbb15` (= origin). State file `C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_coord12\dungeon_state.md`.

The generator is done and stays as it is (`godot/logic/Maps/DungeonGen.cs`; 50 seeds per dungeon distinct and walkable): do not change layouts or walkable areas. The first look was FAR (both dungeons read as sunlit forest clearings) and the forest-dressing approach is scrapped: do not bring it back. The look is being rebuilt as a system, by rule from the room graph. Built so far, never shot: walls as mass (`godot/src/World/DungeonWalls.cs`, `godot/shaders/dungeon_wall.gdshader`: den roots 4 m, ravine rock 13 m, cut away around her), the GroundPaint fix, the den pits.

Targets, approved by the owner (15 Nov, asked whether to build both dungeons toward those pictures: "Yes, build"): `C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_coord12\dungeon_concepts\` (`sheet_den.jpg`, `sheet_ravine.jpg`, `den_room.png`, `den_boss.png`, `ravine_room.png`, `ravine_boss.png`). The den pictures are the target as drawn (root walls over packed earth, black beyond, pale shafts, teal fungus, bone litter, sunken pits). For the ravine use `ravine_boss.png` for framing and walls, and `ravine_room.png` for kit and palette only (its camera is lower and closer than the game's; no leaf shadows).

In order: (1) run the imports in the worktree, shoot, and check the walls (winding, the cutaway); (2) a light rig per dungeon (den: no sky; ravine: a strip of sun); (3) floors per dungeon; (4) the ravine's drops and dressing per room kind; (5) frame time, the 50-seed bot rerun on the tip, your own look against the targets, then ONE max judge (always-seen) against the targets. Flags: `--zone map --dungeon hollow|roost --seed N`, `--at boss`, `--dungeon-seed N`. On PASS the coordinator merges `dungeon-1`, then `dungeon-fights` on top, and sends the owner a real frame.

## Warden polish

Worktree `C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a596c09f6fdf9c98b`, branch `warden-polish@6ccb32800` (= origin, suite 2797/0/11). State file `C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_coord12\warden_polish_state.md`.

The fixed list: (1) turning ("movement looked weird especially turning", the owner, 10 Nov): round 1 is in at `74a7f24eb`, WIP (the 180 from 125.8 to 41.9 deg/frame, the 90 from 62.9 to 27.0); (2) her held weapon per stance: done `53391e364`; (3) the orange double ring: merged `596723653`, its frames not compared yet; (4a-4c) numbers on the swap glint, the bush over her, the black bar in creation: diagnosed only; (4d) `--unequip offhand` clears the world shield: done `6ccb32800`, with a risk to check (anyone with no off-hand item, such as cinematics or the creation preview, may now show no shield); (5) gear data remaps: candidate frames `wpc_*` are shot and not looked at.

In order: look at `wp_w1_*`; fix 4a-4c; check the 4d risk; pick the item 5 remaps; the after batch; your own look; ONE max judge (always-seen); merge integration in; suite; push. The `warden-turn` worktree was removed unused: a turning solver works in your worktree, or ask me before a new one (worktree cap).

## Skin light

Worktree `C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\determined-leakey-726ff5`, branch `skin-light@34d6b6b75` (= origin). State file `C:\Users\munch\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_a86b1f76-a492-4a36-ad66-5017183184ff\skin_light_state.md`. Judged frames `C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_coord12\skin_judge4\`.

Judge 4 (max) was CLOSE. TWO fix rounds are left (rounds 2 and 3 of 3), then it merges or stops. It matters because the den is lit by a cold key and her skin is always on screen. Failing: (1) at night her shade is more orange than her lit skin (her and the NPC); (2) the NPC by day regressed (pale cream forehead, ochre shade); (3) the NPC's smudge under the nose; (4) her chest is two-tone at the Look by day. "ShadeKey" (a shade fill in the moon's colour) failed and is reverted: do not retry it.

Leads from the last lead, read in code and unmeasured: fault 1 is built into the rig (at night the moon's cool key lights her lit side while her shade gets only warm lamps, ember #ff8a3a and lamp #ffe6b8, plus a warm fill and floor; the warm-lamp hold runs only in the close-up and NPCs never get it); fault 4 is the collar band only partly taking the neck treatment.

In order: rerun `r5split.sh` (copy in `skin_judge4\`; 5 trial settings on close_night, play_night, look_night and the NPC at night; about 40 minutes in a Godot turn, so hand the wait to a runner); measure with `fx/mz.py r5dump r5fl r5em r5ft r5gr r5ho` against r4c; then cause, change, the 1:1 batch, your own look, ONE max judge per round (always-seen) on the four failing rows plus a regression row. PASS = full suite, push, report. Otherwise stop after round 3 and report what is strictly better than integration.
