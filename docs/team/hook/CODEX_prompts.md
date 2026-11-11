# Codex prompts (10 Nov, coordinator #7)

Four jobs the owner can run in the Codex app. Each is spec work with a measurable pass and no look or feel call, picked from the post-demo queue so none waits on the demo-arpg1 notes. They touch different files, so up to three can run at once (the worktree cap is 8; 3 are on disk).

**How to use:** paste RULES, then one job, as a single prompt. One Codex task per job.

## RULES (paste above every job)

```text
You are working in the game repo at C:\Users\munch\Desktop\survivorsunchained (Godot 4 + C#; tests in godot/tests). Read CLAUDE.md and the "How we work" and "Safety and the owner's machine" sections of docs/team/README.md first. Then follow these without exception:

- Work on your own branch codex/<job-name>, cut from origin/claude/vigilant-galileo-l6jqyx, in your own git worktree (.claude/worktrees/codex-<job-name>, or the worktree the app gave you). Never work in the main checkout. Never link a worktree's godot/assets to the main checkout.
- Never run git stash, git reset --hard or git checkout . ; set work aside with a WIP commit.
- Run `dotnet test` in godot/tests before every commit and keep it green (baseline 2211 passed, 0 failed, 11 skipped; DraftCardFitTests is a known flake that passes alone).
- Any Godot run takes a turn first: `python tools/turn.py take godot "codex: <job>"`, and gives it back when done (`give godot "<same name>"`). dotnet test needs no turn. Never kill a process by name; stop only a PID you started.
- Commit as you go and push your own branch only. Open no PR and merge nothing into claude/vigilant-galileo-l6jqyx.
- American spelling. Comments are short prose that say why. Tunable numbers go in data files, not code.
- Do not change how anything looks or reads (shaders, art, UI layout, story text). If the job seems to need that, stop and say so.
- When done, append ONE line to C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_coord5\inbox.md:
  `<HH:MM> CODEX <job-name> codex/<job-name>@<short sha>: MR READY (<suite result>; <what was built, one clause>; <anything left open>)`
  If you stop short, write the same line with BLOCKED and the reason.
```

## Job 1: density (job-name: density)

```text
Goal: measure fight density as a rhythm. Build the instrument only; tune nothing.

Read docs/design/ARPG_FUN.md section 4, P0 item 3. Find the existing headless zone sim (the one that reports "2/2 through, 5.4 min, 0 falls" for a zone run; grep the harness flags in godot/ and tools/) and extend it, or add a recorder it feeds, so a run of Low Ford and of the first story zone reports per zone:
- kills per minute (whole run, and per 30 s window),
- seconds from the last kill of one pack to the first hit on the next (median, p90, max),
- seconds between elite packs (median, max),
- the longest stretch with no enemy within engage range.
A "pack" is the game's own spawn group; use the grouping the spawner already has rather than inventing one.

Output: one JSON per run in a git-ignored folder, and a table in docs/team/density.md with today's numbers beside the targets to playtest (next pack within 5-8 s, an elite pack every 60-90 s, a lull after each elite).

Pass: unit tests for the recorder's math on a scripted kill timeline; the sim runs both zones headless and writes the table; suite green.
```

## Job 2: local capped hit-stop (job-name: hitstop)

**TAKEN BACK 11 Nov 00:55 (coordinator #8): do NOT run this job in Codex.** (01:05: it WAS running in the owner's Codex app with nothing pushed; the owner stopped it ~01:10; `codex/hitstop` is not merged if it ever appears.) The feel lane (F1 lead 19, `feel-f1`) was blocked on it, so F1 builds it to this spec.

```text
Goal: hit-stop that is local, scaled and capped, driven by data and off by default.

Read docs/design/ARPG_FUN.md section 4, P0 item 1. Find the current hit-shake (grep HitShake). Build beside it, behind one data flag that ships OFF so today's behavior is unchanged:
- the freeze applies to the attacker and the target only; never to UI, audio, the camera or other actors;
- duration by hit class from a data file: trash hits 0 ms, heavy hits and crits 40-60 ms, elite kills and finishers 80-100 ms, hard cap 150 ms whatever stacks;
- a crowd rule from data: above N live enemies within the screen, scale durations down (start N=30, scale 0.5);
- a hit that lands while its target is already frozen extends to the longer of the two, never the sum.

Pass: unit tests for the class table, the cap, the crowd scale and the no-stacking rule; with the flag off the suite and the zone sim's result are unchanged; with it on the zone sim still completes. Do not tune the feel: the team judges that at the game camera after merge.
```

## Job 3: the flaky test (job-name: draftfit-flake)

```text
Goal: DraftCardFitTests passes alone and sometimes fails inside the full suite. Find the cause and fix it at the cause.

Reproduce first (run the full suite until it fails, note the order and the failing assert). Expect shared static state, a culture or font-metrics dependency, or test order. Fix the leak in the code or the fixture that owns it; do not skip, retry or loosen the test, and do not serialize the whole suite to hide it.

Pass: the cause written in the commit message in two lines; ten full `dotnet test` runs in a row green.
```

## Job 4: the wick audit (job-name: wick-audit; a report, no code)

```text
Goal: a design report the classes lead can pick from. Change no game data and no code.

Read docs/design/ARPG_FUN.md section 4 item 9, docs/design/ONE_BUILD.md, godot/data/content/skill_lamps.json and the wicks data the game reads (grep wicks.json). Write docs/design/WICK_AUDIT.md:
1. A table of every Warden wick and lamp: its skill, what it does today, and one of two marks: NUMBER (only a stat changes: damage, cooldown, cost, duration, size) or BEHAVIOR (the skill's shape, count, trigger or element changes).
2. The counts, and which skills have no BEHAVIOR option at all.
3. For each NUMBER entry, two replacement ideas that change behavior and that the current skill code could plausibly carry (say which system each leans on). Keep every idea in this game's world: ember, lamps, chains, the drowned, the Watch. No generic fantasy filler.
4. The ten strongest ideas overall, ranked, with the first one a player could meet inside the first ten minutes at the top.

Pass: every entry in the data appears in the table exactly once; the file is the only change on the branch.
```

# Round 2 (11 Nov, coordinator #8)

Six more jobs. The first two are owed from round 1; the other four are new. All are code or a report with a measurable pass and no look or feel call. Run at most two at once (two leads are live and share the Godot turn). Order: 5 and 6 first; 10 only after 6 is merged (same test files).

**How to use:** paste RULES (above), then ROUND 2 ADDITIONS, then one job, as a single prompt. One Codex task per job.

## ROUND 2 ADDITIONS (paste after RULES)

```text
These replace the matching lines in RULES:
- Baseline: 2268 passed, 0 failed, 11 skipped at integration 34586016e (about 8.5 minutes). The newest line starting `RULING ALL` in C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_coord5\inbox.md has the current tip and baseline; use that one.
- Two leads are working right now. Do not edit godot/src/View/PlayerView.cs, the animation clips, or combat hit effects (launches, lanes, crack decals, damage numbers, hit reactions, hit-stop). If a job seems to need one of those, stop and post BLOCKED.
- Before your MR line, merge origin/claude/vigilant-galileo-l6jqyx into your branch and run the full suite again on the merged result. The MR line carries that result.
- No test you add may take longer than 60 seconds inside the suite. A long run is a tool run, not a test.
- If you cannot push, keep the branch local and write "local only" in the MR line; the coordinator fetches it from your copy.
```

## Job 5: density, back to green (job-name: density; continue the branch codex/density)

```text
Goal: bring the density instrument back into integration, green and fast.

State: codex/density@7735979fb was merged into integration and then backed out (revert commit e344f2239), because on integration DensityProbeTests.Verge_walk_clears_the_field_and_returns_past_the_camp_wall failed (Assert.True(r.Reached) was false, godot/tests/DensityProbeTests.cs line 47) and that one test ran 20 minutes 47 seconds (the suite took 32 minutes).

Do, on codex/density:
1. Merge origin/claude/vigilant-galileo-l6jqyx. That merge removes your work (it carries the revert), so then run `git revert e344f2239` to bring it back as a new commit.
2. Find why VergeZoneSim.Play(new VergeZoneSpec(2)) no longer reaches the end on integration when it did on your branch: something that landed since (boss, map or combat changes) changed the walk. Fix the sim or its assumptions. Do not change the game to suit the test. If the game itself now stops a player from finishing the Verge walk, stop and post BLOCKED with the evidence.
3. Give the sim a step and time budget so it fails fast with a reason instead of running on. The suite test finishes in under 60 seconds; the long two-zone run stays a tool run.

Pass: full suite green on the merged result and within one minute of the baseline time; docs/team/density.md regenerated from a fresh tool run; MR line.
```

## Job 6: the flaky test (job-name: draftfit-flake)

```text
Goal: DraftCardFitTests passes alone and has sometimes failed inside the full suite. Find the cause and fix it at the cause.

Known: it is the suite's one engine test (about 41 seconds). No failure log was kept, and every full run on 10-11 Nov was green, so it is rare. Reproduce first: up to 15 full `dotnet test` runs in the background, keeping each log; on a failure note the test order and the failing assert. Expect shared static state, a culture or font-metrics dependency, or test order.

If it fails: fix the leak in the code or the fixture that owns it. Do not skip, retry or loosen the test, and do not serialize the whole suite to hide it.
If 15 runs are green: read the test and what it touches for shared statics, culture and font loading. Fix a real leak if the reading finds one; otherwise post BLOCKED "not reproducing in 15 runs" with what you checked, and change nothing.

Pass: the cause in the commit message in two lines; ten full runs in a row green after the fix.
```

## Job 7: one rule for a lit lamp (job-name: lamps-count)

```text
Goal: the Lamps board, the stats and the tooltip agree on which lamps are lit.

Reported by the tooltips lane: the board (godot/src/Ui/LampBoard.cs) draws a held lamp as Lit, while the stats and the tip count only lit ones (rules in godot/logic/Rpg/LampBook.cs and godot/logic/Content/Lamps.cs). Check the report first; if it does not reproduce, say so in the MR line and change nothing.

Find the one predicate the stats use for "lit". Move the board's per-lamp state into logic so it comes from that same predicate: a lamp that is held but not lit is not Lit. Use only states the board already draws. No new art, colors, layout or wording. If the board has no existing drawn state for held-not-lit, stop and post BLOCKED saying what is missing (the UI lead owns looks).

Pass: a unit test that, for every held/lit combination in a book, the board's model, the stats and the tip give the same lit count; suite green.
```

## Job 8: no tutorial freeze during a boss windup (job-name: callout-windup)

```text
Goal: a tutorial freeze callout never starts while a boss attack is winding up.

Reported: the "THE LAMPS" freeze callout came up during the boss's windup. Callouts live in godot/logic/Play/Teach.cs (Callout, CalloutKind.Freeze, Teacher.Offer(callout, clock, busy)); the game side is godot/src/Game/GameTeach.cs (Teach and the busy check it passes).

Make "a boss windup or telegraphed attack is live" count as busy for Freeze callouts. The callout waits and shows on the first frame no windup is live. It is never dropped, and queued callouts keep their order. Do not change any callout's words, timing once shown, or look.

Pass: unit tests on the Teacher: offered during a windup it does not show; it shows on the first tick after the windup resolves; two queued callouts come out in the order offered; suite green.
```

## Job 9: renderer messages (job-name: renderer-noise)

```text
Goal: explain two renderer messages, and remove them if the cause is ours.

(a) Godot prints "did not unpair geometries from light" 6 to 8 times in a run (a message, not an exception). (b) The shader-cache write errors you saw in the rendered close-up harness.

Find when each fires (which zone change, which node, which light) and whether it is our lifetime order, like the close-up lights fixed in codex/closeup-blackscreen, or the engine's own. If ours, fix it without changing how anything looks. If not, change no code.

Output: docs/experience/renderer_noise.md with the cause of each, why it is or is not harmless, how to tell a real failure from it, and the count of each message before and after over one rendered run through Low Ford, the Waystation and one arena. Godot runs take a turn (see RULES).

Pass: the doc; the counts; suite green.
```

## Job 10: a faster suite (job-name: suite-speed; run only after Job 6 is merged)

```text
Goal: the full suite gates every merge and takes about 8.5 minutes. Make it faster with no loss of coverage.

Measure first: per-test durations (`dotnet test --logger trx`), and a table of the 25 slowest in docs/team/suite_speed.md with what each spends its time on.

Then land the safe cuts: one shared fixture for content that many tests load again, a smaller sim spec where the assert does not need the size, no sleeps or real-time waits. Do not delete, skip or weaken any assertion. Turn on parallel test classes only if you show there is no shared static state between them, and say so in the doc.

Pass: the same passed and skipped counts as the baseline; three full runs in a row green; the before and after time in the doc.
```
