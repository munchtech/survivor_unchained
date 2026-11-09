Spawning: allowed
Context budget: 300k

## Your area: A1 Stage B, her core motion on the picked body B (motion lead, Stage B lead 5)

(Written 9 Nov by coordinator ad002ada. Lead 4 handed off at HANDOFF READY motion-a1@a10ecbb09, Marionette motion-a1@bc87b03, both pushed.)

You are the motion lead for Stage B (`su-lead-max`: her motion is taste throughout; coding at medium through solvers; judges at max). Worktree `C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\motion-a1`, branch `motion-a1` at a10ecbb09, integration already merged, the P4 pipeline rebased on the picked body B (parity 0.19 mm / 0.02 deg; dotnet 1597/0/10). Work only there; never cd into the main checkout (use `git -C` and absolute paths). Marionette is a separate repo at `C:\Users\munch\Desktop\Marionette` (branch motion-a1 at bc87b03); the motion core lives in its `tools/motion/`. Commit to both, push both. Kill processes by PID only, never by image name (a P2 solver's taskkill /IM took down every Godot on the machine this morning).

Report to the coordinator (SendMessage "main"): a short oriented line first (plan and estimate), then at each judge, at `MR READY motion-a1@<sha>`, at a HANDOFF, at a block, and for any question only the owner can answer. Everything else goes in `docs/handoff/animation.md`'s top section.

Read first, by section: `docs/handoff/lead_brief.md` (all of it; the junction rule before any git merge/reset); `docs/handoff/animation.md` top block (lead 4's: done, open numbers, next); `docs/team/OWNER_NOTES.md` top four blocks (8 Nov ARPG pivot; 9 Nov proposal PICKED + hands rule; GATE P1 PICKED "B, go"); `docs/design/ARPG_DIRECTION.md` §4 (Heroic Leap, Cyclone/Bladestorm); `docs/design/MOTION_BIBLE.md`, `docs/design/MOTION_PLAN.md` Stage B and the Warden slice; `docs/team/ARPG_NOTES.md` last block (the `her_events.json` schema); lead 4's numbers at `C:\Users\munch\Desktop\survivorsunchained_inputs\motion_a1\stageB\rebase\numbers.md`; and the actions brief at `C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_motion_a1\actions\brief.md` (each clip's beats as numbers).

The job, in lead 4's order:
1. Spawn solver A from the actions brief (su-lead-high, medium effort, 280k): the action kind (Kimodo key poses and end effectors, de-rotation, loop ranges, the pelvis arc); the clearance test fixed (its 80 mm ceiling); the action measures and `her_events.json`; an `--act` shot harness; then heroic_leap end to end.
2. Solver B: bladestorm_loop, iron_vow, shield_charge. Bladestorm: P7 keeps the root yaw at 2.25 turns/s, so the clip is built de-rotated for that rate (lead 4's correction, already relayed to P7).
3. One max judge on all four at 1:1 (play camera and close zoom; whole-frame question first: "effortlessly badass; would it ship in a AAA ARPG?"), fix rounds to PASS (cap 3; ask main to raise it), then report to main so the P7 skills lead can shoot with them.
4. The Warden slice to PASS: fix round on lead 4's measured opens first (walk_warden's sword gap 78.8 mm; town clips' shield off the held list; the p4.py check misses: calf pops, town idle elbow 111.9, run_warden blade angle, thigh trail, walk sway; the runs' heel lift-off; the Marionette foot-roll test at 10.001), then judge round 2 at max.
5. Integration merged in (junction rule), both suites green, pushed, `MR READY motion-a1@<sha>` with merge notes.

Report shape: "P4: the app can now X; this batch cost Y; the next costs about Z." Budget: about 2.0-2.8M left for the area. Hand off at ~300k with `HANDOFF READY motion-a1@<sha>`. Scratch: `scratchpad\motion_a1\` only; back up to `survivorsunchained_inputs\scratch_motion_a1\` and clear only that subfolder. Worktree cap 8; helpers work in YOUR worktree. Godot turns through `python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py take godot "A1: <job>"`, Blender `take blender`; give back at once.
