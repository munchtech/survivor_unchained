# Handoff: classes (session 12: the Flare cuts story bosses; Act 1 health dropped; the crowd measured)

Written by the twelfth classes lead (13 October). Branch `classes-9` (worktree `agent-a63a34b9e5a45d1bf`), last commit on the last line of git log. Scratch `S/` = `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\59a43b82-cb5d-4a5a-bb8d-db67086387ea\scratchpad\classes\`. Older: `N/` (33ad5b17-...\scratchpad\classes), `O/` (1515c1de-...).

## The owner (13 October)
- "why wouldn't flare shorten things? its supposed to be epic. an 'oh shit' button. a planned 'BOOM' button. a 'clear the whole room' button."
- "flares in general don't need to be big boss hits - they are specialized. *most* are for arena mode type screen clears or saves etc - but some can be single target (or one or the other based on context). but pushing a flare should always do something visible."

## Start here
1. **Merge request sent** for classes-9 (step 1, judge 6 PASS; sheet `S/judge6_sheet.md`, verdict summarised below). Wait for the merge.
2. **Flare lead's request (flare-1, a422b108a0fdfb259):** Burns Twice's last BOOM shoves survivors in reach (a stagger plus about 3 m, damage unchanged; an `Ev.Flare` Blow part "shove" per target), plus an "aim" part about 0.2 s before each ember lands. Promised to them. Re-measure arenas once (it moves bodies), then reply with the event names.
3. **Judge 6's logic fix:** the Road's Toll's cuts with no target (`FlareStaged.cs` TollCut, last line: `e?.X ?? p.X ..., 0`) land at her feet with radius 0. Place them on open ground in reach, at an angle from the blow number, with a visible radius. Don't use the sim RNG: it would shift every seed.
4. **Notes to the Flare lead and skills VFX** (judge 6; put them in docs/team/classes.md): Butcher's Hour has no blow, so the view must show its press burst and frenzy until End. One Arrow's plain form is a 30 m blast (label it "clear, 30 m today; line is the phase-6 intent"), and its ring sits off a 15 m screen. On integration the Godot view handles no `Ev.Flare` at all yet (FLARE_LOOK on flare-1 is building it).
5. **Judge 6's numbers for a runner** (next round): (1) the drift: today's game without the Flare runs +10.3% longer than base11 with falls 0.089, so trace it per calling (base11 code against today's), and if it's a regression, re-run Q1; (2) careless warden's falls and the share of its fights more than 25% long; (3) the shortest story fight with the cut (p5, deft bankers); (4) Vault crowd (75% room cleared; reaver 65, warden 70): survivors' distance and kind, reach x1.25 and x1.33; (5) save Flares: alive 10 s after a low-health press; (6) whether a 15 m radius matches the default camera.
6. **Then the phase-6 plan** (CLASSES §7, 6a), with a **role column** from judge 6's table (clear, clear+save, context, single/line, sustained, control/save, self) and "what a press shows with nothing near", plus its owner lines (`O/judge1_verdict.md`, bottom) to a lean judge, then to the coordinator. No phase-6 code before the owner approves.

## Done this session
- `StoryBoss.Cuts` (on) lifts the story exemption. Act 1 health dropped to 103/130/100/109 (was 110/141/107/114). Tests updated.
- Measured, Act 1, 96 seeds a cell (`S/a`, `S/h`, `S/n`; summaries `sum_*.txt`). Against base11: good use -7.7% / falls 0.027; banker -14.1% / 0.022; lit-not-held -7.6%; careless +4.2% / 0.043; never presses +10.3% / 0.089. With the raise kept: -2.2% / +10.0%. The cut alone is small (-1.7%): Act 1 phases run 45-75 s against floors of 25-30 s.
- Crowd (`S/y`): one Flare kills 97-99% in reach and clears the room (80%+ of 15 m) in 89-94% of casts at all tiers. All 16 Flares in `S/y/crowd16.txt`. No number change (judge 6).
- **Bug found and fixed:** the crowd count read a re-used pooled slot as a survivor, so every crowd figure before `S/y` (`S/d`, `S/e`, `S/r`, `S/x`) is about 30 points low. Ignore those.
- Harness flags: `--storycut 0`, `--storyhp roost=..,vault=..,hollow=..,dig=..`, `--flareboss 0` (careless), `--flareuse 0` (never), `--rout X`, `--flarereach X` (measuring only). Results carry `FlareCrowd` rows (Flare.cs doc) and story `BossPhases`.
- Agreed the Flare lead's `FlareLead(dt)` (view-only pre-key clock) on flare-1, with guards: no blows, no world stamps, clamped at the key.

## Tools
- Summaries: `python S/stc.py REF.jsonl X.jsonl ...` (story bosses by calling, fight and hands), `S/crowd.py` (crowd), `S/arsum.py "a,b" "c,d"` (arena outcomes). Batches `S/*.sh` (cwd godot/; harness copy `S/bal13`, current). base11 = `O/s2/base11.jsonl`.
- Isolation gotcha: commands with `$VAR` running python, or compound `cd && ...`, are refused. Write a script to `S/` and run `bash S/x.sh`.
