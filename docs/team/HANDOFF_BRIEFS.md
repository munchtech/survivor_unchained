# Hand-off briefs (22 November 2026)

Ready-to-paste briefs for the packages in `docs/team/GAME_PLAN.md` section H. Paste "Common rules" plus one brief into a new session, or give both to an orchestrator's lead. Each brief names its spec in the plan instead of repeating it: the plan wins where they differ.

## Common rules (paste with every brief)

```
You are working on Survivor Unchained (Godot C#, repo C:\Users\munch\Desktop\survivorsunchained).
Read first, in this order: CLAUDE.md (repo root), docs/team/README.md, docs/team/RESUME.md, then the plan
sections your brief names in docs/team/GAME_PLAN.md. Never read a file over about 400 lines whole: grep, then
read ranges.
- Work in your own worktree (count .claude/worktrees first: cap 8) on your own branch. Commit as you go.
  Never push, never merge to the integration branch: hand back the branch name and its latest commit id (its sha).
- Keep a state file from your first step (path in your brief): what is done, what is left, numbers, decisions
  with their why, failed attempts. A later session must be able to continue from it alone.
- The owner's rulings in the plan are quoted word for word. Do not reinterpret them. If the spec looks wrong,
  stop and say so instead of building around it.
- She is never shown closer than the game camera (perspective FOV 34, 62 degrees down, 24 m, about 70 px tall
  at 1080p). Every look check is a 1:1 game-camera frame or film. No close-up cameras.
- Round cap: 3 rounds on any judged item. You never raise it. At the cap, report what failed and stop.
- Heavy Godot or Blender runs go through tools/turn.py. Shoot output goes in the worktree's godot/.shots/.
- No downloads, installs, purchases or credit spend unless your brief says so. Nothing deleted permanently.
- Report: what is now true, the numbers, what is not done or not verified, the branch name and its latest commit id (sha).
```

## P1. Godot 4.7.2 upgrade trial (Opus lead, one session)

```
Goal: say when the game moves from Godot 4.5.1 to 4.7.2 and list exactly what breaks. Upgrading is settled
(the owner: "we don't want to be trapped not updating"); you decide when and at what cost, not whether.
Spec: docs/team/GAME_PLAN.md decision 16 (section C, row 16). State file:
C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_godot47\STATE.md
Given: the 4.7.2 .NET editor is already at C:\Users\munch\Desktop\Godot_v4.7.2-stable_mono_win64 (checksum
verified). 4.5.1 stays at C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64. Our tools use fixed paths:
point only your trial at 4.7.2.
Do, in a trial worktree only:
1. Read the official pages first: godotengine.org/releases/4.6/ and /4.7/, and the docs pages "Upgrading to
   Godot 4.6" and "Upgrading to Godot 4.7". Known items are listed in decision 16 (brighter glow and fog,
   scene file format change, C# breaks on AnimationPlayer members and Animation.length, a Jolt world-boundary
   sign flip, input device ids). The pages say nothing about custom compositor effects, frame pacing or input
   latency: those are yours to find out.
2. Bump the SDK pin (Godot.NET.Sdk/4.5.1 in the csproj), open the project in 4.7.2, fix the build.
3. Run the test suite (baseline: 3081 passed on 4.5.1).
4. Measure the den on both engines: the perf trace, and the 12-shot movement harness (--moves12, from branch
   move-baseline, merged into the integration branch at a710f612c). Same takes, same seed.
5. Film the den at the game camera on both engines and compare the look side by side. Expect to re-tune glow
   and fog; say what you changed.
Optional tools, only after reading their code: api_lookup.py and migrate_scan.py from
https://github.com/EL4CTEO/godot-skills (MIT). Do not use its cs_build.py --init, scene_edit.py or
addon_inspect --disable: they edit project files.
Pass: clean C# build, tests pass, perf and movement numbers equal or better, no visible change in the look.
Limit: this one session. If fixes need more, stop, list what broke with file and line, and estimate the rest:
the upgrade then becomes the first task after the slice. "Stay on 4.5.1" is never the recommendation.
Deliverable: docs/team/GODOT_UPGRADE_TRIAL.md (verdict, breaks, both engines' numbers, the two films' paths)
and the trial branch.
```

## P2. Movement (Fable lead for tasks 3 and 4, Opus for task 5; the critical lane)

```
Goal: her movement matches Path of Exile 2's observable movement design and responsiveness, on a controller
and on keyboard with mouse. The owner: "Path of Exile 2 is the specific movement benchmark. Treat matching
its observable movement design and responsiveness as a serious target, not a loose inspiration." and "Do not
quietly replace the target with a generic ARPG controller."
Spec: docs/team/GAME_PLAN.md section G tasks 3, 4 and 5, criteria D1, decision 3 (the dash follows the held
direction; nothing held, it goes to the cursor; on a stick, to her facing), and the paragraph "The PoE2
reference is closed". State file: C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_move\STATE.md
Evidence you start from:
- Our baseline: task 1's table (merged at a710f612c; harness flag --moves12, tools/motion/move_baseline.py;
  its state file is survivorsunchained_inputs\scratch_devplan\task1_move_baseline\STATE.md). The 12 shots are
  in survivorsunchained_inputs\scratch_devplan\moves12.md. The baseline is in (per-shot CSVs in raw\; measured at
  998aa9f48; TABLE.md, READING.md and the film are in that state file's folder; the plan's section G has the
  table against PoE2). It confirms the camera: it leads her by 1.52 m and scrolls on for about 1 s after a
  stop. Start (9 frames to 90%) and stop (19 frames) are several times slower than the reference. The dash
  always goes to the cursor on keyboard and mouse. Shot 12 (the 0.3 to 0.55 m hit-stop slide) has no numbers:
  the harness's stand-in foe vanishes a tick after it spawns. Your first step: take shot 12 in a den room with
  a real pack.
- The target: docs/design/POE2_MOVE_REF.md. Measured from public clips: start reaches full speed in 1 to 3
  frames with no ramp, stop takes 2 to 3 frames with no slide, the camera keeps her mid-frame with no lead or
  trail (two clips agree); a roll from rest is about 0.45 s and about 4.7 of her heights (one clip). The other
  eight shots have no reading. The owner does not own PoE2: never ask for a recording. For those eight, write
  your own targets, derived from the measured ones, and mark each as an inference.
- Do not claim to know PoE2's internals. Describe only what footage shows.
Engine facts: fixed 60 Hz sim with view interpolation; Jolt. Do the work on the engine P1's verdict names.
How: every change sits behind a flag so the harness can run before and after on the same takes. Fix causes in
order of the baseline's worst numbers, one at a time, and re-measure after each. Injected input has limits
(listed in task 1's state file): confirm feel-critical fixes with a real pad and mouse.
Pass: D1's criteria on both inputs, shown by harness numbers; then the owner plays and says it feels right.
Limits and stops: as written in tasks 3 to 5. If a fix needs a rewrite of the controller or the animation
graph, stop and bring the evidence first: no rebuild before its central assumption is tested small.
Deliverable: the branch, a before/after table for all 12 shots on both inputs, and a short film per shot.
```

## P3. Den roster re-cut (Opus lead, two sessions; the page is approved: the owner, 22 Nov, "I approve den roster")

```
Goal: clearing the den is fun. The owner: "the way the mobs are now is too derivative of when we were a
survivors roguelike.  everything just charges and it gets annoying.  clear speeds feel unfun.  its a fun
effect sometimes, but its like all our stuff does over and over".
Spec: docs/design/DEN_ROSTER.md (the page the owner approved) and docs/team/GAME_PLAN.md decision 17.
State file: C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_den_roster\STATE.md
The cause, verified: MapRun.Press (godot/logic/Play/Zones/MapRun.cs, lines 386 to 394) makes every ordinary
foe without a ranged attack in a woken pack cast the shared pack charge.
Session 1, in this order:
1. The gate alone: the shared charge off in dungeons. Build it, run the tests, and hand the owner a build to
   play before anything else. Arena nights and story fights keep the charge: prove it with their tests.
2. Open all six den foes at the demo's tier, each with the one move the page gives it, from existing specs.
   The boar is the one ordinary foe that keeps a charge. Then the five pack recipes.
Session 2: the re-tune against the page's targets (a pack dies in 6 to 10 s, half a pack fits inside one
Bladestorm or Leap, at most one lane every 8 s) and the re-cut tests (DungeonFightTests, MapTests,
DungeonTests, BossTests). The boss changes need a den-only switch in ArenaBosses.cs (it is shared with a
story night).
Check and report, do not change without asking: the same method runs a stand clock (press.Stand), and the
owner ruled "no stand clock" on 13 Nov. Say what it does in the den today.
Cut first if it must fit: the Pack-Mother changes, the Hunt's spawn points, Whitethroat.
Pass: the page's targets measured in a run, then the owner plays the den and says clearing is fun.
Stop: one re-tune after the owner's first play. After that, cut foes; do not add systems.
```

## P4. Skills (Fable or an author lead for the page; Opus for the code)

```
Goal: skills work as in other ARPGs. The owner: "we should just copy normal arpg skills probably", "i mean
not every single one.  just mirror what others do.  auras can exist etc", "groundbreaker would be like a node
you know? every 3rd attack groundbreaks.", "stances and unions are already things that set us apart".
Spec: docs/design/BUILD_DIRECTION.md Round 9 (it overrides the auto-slot lines above it), and
docs/team/GAME_PLAN.md decision 15 and section G task 8.
State file: C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_skills\STATE.md
Part 1, paper, half a session, no code: docs/design/SKILL_KINDS.md, one page. Every current skill with its
new kind (pressed, aura, a tree node, or cut) and one line of why. Where an aura sits and what it costs (the
plan's lean: no key, paid by reserving a resource). What the auto support gem does to a skill and what it
costs. The four pressed skills for the slice (Sunder, Heroic Leap, Bladestorm and a fourth). Note from the den
roster page: Shield Charge, Heroic Leap and the dash are all line moves, so pick a fourth that is not one.
Stop there. The owner approves the page before part 2.
Part 2, code, after approval: the bar rule in godot/logic/Rpg/SkillBook.cs (lines 69 to 74), the taught
builds and their tests, the four pressed skills on four keys, no auto slot, Groundbreaker as a node.
Pass: the page approved; then tests green and the owner plays the four skills in the den.
```

## P5. Look target and clarity (Opus lead with the image route; Fable only if the look system stalls)

```
Goal: one approved picture of what the den looks like at the game camera, and a list of what makes fights
hard to read.
Spec: docs/team/GAME_PLAN.md section G tasks 6 and 7, decision 6, and the sentence after task 9 about cutting
prop references. State file: C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_look\STATE.md
Do: take real screenshots of a den room at the game camera. Paint over them (the image route the team
already uses; log provenance) into the options task 6 asks for. Nothing is shown closer than the game
camera. The owner picks one. Then cut each prop out of the picked painting as a clean reference image and keep
the painting as the placement target at the same camera. Meshes from those references wait for the
environment bake-off after the slice.
Task 7 is paper: the den's clarity list, from game-camera films.
Pass: the owner's pick. No shader, light or asset work starts before it.
```

## P6. Story beat (author lead)

```
Goal: one story beat for the den and the camp that lands in play. The owner: "I want a rich story with genuine
emotional impact." and "Do not assume expensive close-up cinematics are necessary."
Spec: docs/team/GAME_PLAN.md section G task 9 and decision 12.
State file: C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_story_beat\STATE.md
Do: three pitches on one page (docs/design/SLICE_STORY_BEAT.md), one plain paragraph each, each told in play
(a line from someone at the camp, a thing found in the den, the boss's last words). No close-ups. Not the
toll: the owner scrapped that beat for the slice, and the story bible stays unchanged (it hides the toll until
Act 3). The model already in the bible: the Ford-Warden, dying, asks "whether it is morning"
(docs/STORY_BIBLE.md, lines 30 to 31). Stop after the pitches: the owner picks one.
Then: the script, at most 40 lines, and one session to wire it.
Pass: after playing, the owner can say what happened in the den's story beat and how they felt about it (D7).
Stop: if the built beat does not land, rewrite it once. Do not rebuild the system.
```

## P7. Body and gear (owned by the Marionette session; already running, do not start it elsewhere)

```
This package is owned by the Marionette session (repo C:\Users\munch\Desktop\Marionette; read its HANDOFF.md
"Start here" and its audit state file first). Paste this only to continue it in a new session there.
What is open, on the owner's words of 22 Nov: the body, the skeleton and the clip set are all candidates for
replacement. "well I wasn't against completely changing our body...not trying to look the same." and "it
might need a new skeleton and new animations.  thats the whole reason were doing these audits.  if we have a
bad foundation we need to change it". Never write "B stays" or "the rig is fixed": neither was ruled.
What was judged: the first test body (a low-detail copy of B) lost on looks at the game camera ("eh - b looks
a lot better."). That is a verdict on that build, not on a new body. A new body need not look like B.
Decided: "the face obviously no matter what dosn't need to be extensive anymore".
Running there (that session's own report, not checked from the game side): a proving session (a new body on
the current skeleton without helpers, in motion beside B, an engine frame, the corset carried to other body
shapes with no refit), and the measuring of B's named rings at rest and over her clips so armor is built to
numbers.
Rules: report every result as measured, the lead's reading, or unknown. Show the owner a sheet early; looks
decide, not vertex counts. Say what each piece (body, skeleton, helpers, clips) costs to keep and to replace;
the owner picks. Judged at the game camera only. Gear is the first end-to-end route (the owner: "gear first,
but we may be changing our body still I believe") and re-fits on whichever body wins.
Nothing is edited or committed in the game checkout.
```

## P8. Blender upgrade trial (in the Marionette session)

```
Goal: say when Marionette moves to the current stable Blender and what breaks. Upgrading is settled; "stay
on the old version" is never the recommendation.
Spec: the game repo's docs/team/GAME_PLAN.md decision 16.
Do: look up the current stable Blender (do not answer from memory) and report the version Marionette runs
now. With the owner's go-ahead for the download, install the new one beside the old one. Run one full
pipeline pass on each (a body export and one garment fit) and compare the outputs: file diffs, the fit
numbers, a game-camera look. Check that each .blend's images still resolve before an export.
Also read, code first, the few scripts worth testing from https://github.com/EL4CTEO/blender-skills (MIT,
written for Blender 5.2 and later): garment.py (builds a garment from body regions and reports poke numbers),
stress_poses.py, rig_check.py, qa_check.py. Do not install all 28 skills into every agent.
Deliverable: a page in Marionette's docs with the verdict, the breaks, and both runs' numbers.
```

## Orchestrator (Opus)

```
You coordinate the packages in docs/team/GAME_PLAN.md section H. You do not design: every package has a
spec, a limit and a pass test. Read CLAUDE.md, docs/team/README.md, docs/team/RESUME.md, then the plan's
sections A and H, and docs/team/HANDOFF_BRIEFS.md.
Order: P1 first. Then P2 as the one critical lane, with P3 beside it now that the owner has approved (22 Nov)
docs/design/DEN_ROSTER.md. P4's page, P5's paint-overs and P6's pitches are paper and each stops at an
owner's pick. P7 and P8 belong to the Marionette session: do not start them here.
Rules: at most two build lanes at once, and only when they share no files. Count worktrees before each spawn
(cap 8) and remove a worktree in the same turn its branch is merged. Merge only what passed its test and the
owner's gate. Never raise a round cap or a session limit. Send a package to a Fable lead when an Opus lead
has spent one honest session without passing, or when the spec itself is in doubt; never for more rounds of
the same approach. The owner's gates are theirs: a judge's pass does not replace the owner's play.
Keep a state file with every branch and sha, each package's state, and the owner's words, word for word.
```

## Orchestrator #17 (Opus): the start prompt (written by #16 at its close, 22 Nov 2026, night)

You are orchestrator #17 for Survivor Unchained, on Opus. Orchestrator #16 closed on 22 Nov 2026 at night and you start from its handoff. Nothing is running: no lanes, no agents, no worktrees of ours.

**Read first, in this order:** `CLAUDE.md`; `docs/team/README.md`; the top block of `docs/team/RESUME.md` ("22 Nov 2026, night: ORCHESTRATOR #16 CLOSED"); `docs/team/GAME_PLAN.md` sections A and H; `docs/team/HANDOFF_BRIEFS.md` ("Common rules" and "Orchestrator"). #16's state file has the owner's words, word for word, and every sha: `C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_coord16\STATE.md` (read its last three blocks, grep the rest). Start your own state file at `C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_coord17\STATE.md` in your first turn.

**Your job** is the standing "Orchestrator" brief in `HANDOFF_BRIEFS.md`: you coordinate packages and do not design. At most two build lanes at once, and only when they share no files. Count worktrees before each spawn (cap 8) and remove a worktree in the turn its branch merges. Merge only what passed its test and the owner's gate. Never raise a round cap or a session limit without the owner's word. P7 and P8 belong to the Marionette session.

**Where things stand**
- Integration is the local branch `claude/vigilant-galileo-l6jqyx`; nothing is pushed. All of 22 Nov's build work is merged (`ba97e1e98`): slice-base, the den roster, five pressed skills, feel, frame pacing 1-3, the Bladestorm re-hold fix.
- Suite: 3147 pass, 1 fail, 12 skip. The fail is `DungeonFightTests.The_den_clears_inside_the_pages_feel_targets` (pack fights 10.0 s against a 6-10 s target).
- The owner's play build is `release\godot\next4` in the main checkout (the command is in RESUME). Every play build for the owner starts with `--veteran 9`.

**Work** (RESUME's top block has the details and the smaller follow-ups)
1. Den re-tune, so the red feel test passes.
2. Godot 4.7.2 upgrade. The owner picked it as the "First task after the slice"; the trial is `godot47-trial@291fb2172`.
3. Frame pacing, session four. The owner granted it on 22 Nov ("we could try more?", then "yes"). D1's numbers are not met. Left over: about 15 boss-fight draw frames of 17-27 ms a run (cause unknown) and one 48-65 ms frame at the den's end. The "before" build is `release\godot\next2`, the "after" is `next4`. #16's recommendation, yours to settle: run it after the engine upgrade, since a new engine changes what there is to profile. Measure only when no other session's Godot run overlaps: session three's numbers were spoiled that way. No fifth session without the owner's word.
4. Parked items: P6 pitch 2 wiring (the owner: "Keep pitch 2, wire it"), Resolve shown on her, equip and pick-up sounds, the den load (half build-ahead, and moving the 3.5 s warm-up to the Verge's load).
5. Waiting on the owner. Ask all of it in one table, never one at a time: the Iron Vow pick (A warcry, B timed parry, C held; #16's pick is A), roll or dash, and for the look target: may a light pool be brighter than her, plain or detailed floor, and the route (#16's pick: scripted local fixes on round 3's set).

**Two rules the owner added on 22 Nov, word for word**
- "remember when we keep hitting walls to see how successful games have done it". A lane that failed twice or more on the same kind of fault starts its next brief with how shipped, successful games solve that exact problem, and says which of those it copies. This applies now to frame pacing and to the look target.
- "it will be opus orchestrated - it should know if things aren't working to give fable lead a try". When an Opus lead has spent one honest session without passing, or the spec itself is in doubt, the package goes to a Fable lead with a changed approach. Never spend more rounds on the same approach. Two packages are already at that point, so their next leads are Fable leads: frame pacing (three sessions, numbers not met) and the look target (round 5: three judged rounds, none passed, whole-picture remakes stopped converging).

**Traps**
- Godot runs go through `tools/turn.py` or `tools/quiet.py`. Another session's shoots share the turn lock (labels `game_frame: gf_*`): wait for it, never touch it. No export or windowed run while a game the owner started is running.
- Never `git add -A`. Engine churn (`.import`, `.uid`, `project.godot`) and a few untracked leftovers in the main checkout are not ours. Commit exact paths.
- The owner's gates are theirs: a judge's pass does not replace their play. A reaction is not a ruling: record their words word for word and mark your readings as readings.
- The look lane's ChatGPT image limit is separate from weekly usage. A lead that hits it stops; there is no workaround.
- Disk: C: has about 90 GB free. RESUME lists what the last sweep left behind and why.

**Reports to the owner:** short, result first; play commands in a `powershell` block; open decisions in one table.
