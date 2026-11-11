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
