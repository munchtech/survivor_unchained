# Handoff: classes (session 10: stagger hotfix merged, Banked Flame C40 in, three checks owed)

Written by the tenth classes lead (12 October), stopped clean for a new coordinator. Branch `classes-8` (worktree `agent-a54ebb1323cb25841`), last commit on the last line of git log. Scratch `N/` = `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\1515c1de-1208-43e2-b6eb-5133e0d07e1c\scratchpad\classes\`. Nothing is running and no turn is held.

## Start here
1. **Owner question (open):** should arena phase floors let a Flare's burst through? See §2.2 for judge 2's wording. Build nothing until the owner answers.
2. **Re-run judge 2's measurements:** `bash N/bq4.sh` (about 90 min, stopped at the wind-down). It measures C40 against no lamp with arena floors ON (T4 L10 and L30, deft and plain, banks or not), plus the reserve run (plain hands, T4 L10, 96 seeds, falls). If `--seed0` errors on `arena`, drop it.
   - Pass: the non-banker's worst calling is within +3% of no lamp, and the Flare's share of a boss is at or under 35%.
   - Summarize with `python c8/bstat.py ref.jsonl ...` (`c8` = `...\ba85aba8-36f4-4cf9-99c5-4c5ef9e4a65c\scratchpad\c8`).
   - CLASSES §7 (2) still says to soften the price to 20% if the reserve saves nothing. Decide that from the reserve run.
3. **Butcher's Hour Dig deft cell, -7.4% against its plain form** (bar ±6%; after the stagger fix). Measure it, find why (suspect: the deepened bleed ignores Grimtunnel's half damage on his ground and his lamps' quarter), and trim the Hour on him only. Falls are no longer a question: 0.049 against 0.043, 1 sigma. No solver needed.
4. **Write two results into CLASSES §7.** First, the Bell's Vault plain cell is waived: -4.5% after the fix, within ±6%, and the arms show the Bell's own damage is the cause (below). Second, the Hour's falls follow-up is closed.
5. Then: the phase-6 owner lines (`N/judge1_verdict.md`, bottom) go to the coordinator. More Embers / Toll Doubled checks (the session-9 list). Phase 6 waits for the owner's yes.

## 1. Done this session
- **Press-stagger hotfix MERGED** (integration 8450b738; also in classes-8 via 9c0a0175).
  - Press 0.15 of the gauge (`Battle.PressStaggerBoss`); the Bell's toll 0.15.
  - The Toll's boss measure 0.85 -> 0.25; Burns Twice 1.0.
  - Story-boss HealthMul: Redcowl 110, Barrow Lord 141, Greymuzzle 107, Grimtunnel 114.
  - The target is the real pre-Flare game (`N/s2/base11.jsonl` = the 11 Oct baseline). `SU_NOFLARE` on today's build is 7-14% slower and falls three times as often, so don't use it.
  - Result: every calling within 3%; falls 0.037 against 0.030, which is the stagger fix itself. Arena power is unchanged; only the Toll's arena boss share drops.
  - Tools: `N/fc.py` (fight x calling against a reference), `N/fshare.py` (the Flare's share of boss health), `N/sf/mk.py` (the hotfix builder).
- **Banked Flame: judge 2** (agent ac3d24521b4fd4b75): "FAIL as the finished lamp, PASS for C40 replacing cur now".
  - Applied in 4ddba3ab: "Hold two Flares. Each fills 30% slower and strikes 40% harder." (harder 0.4). The data is in lamps.json and `tools/classes/lamps_build.py`; CLASSES lines 252 and 901 are updated.
  - Post-fix numbers are in `N/bk3/` (`ar_table.md`):
    - Act 1 banked -7.1%, unbanked +1.3%.
    - Arena floors off: banked -16% (median), unbanked +11%.
  - Falls on Act 1: 23 against 36 runs (1.7 sigma).
- **Phase-6 plan:** judge 1's ten fixes are in CLASSES §7 (bd2fd49e, fc2e2c1e). The Branding's live length stays 1.0 until 6a is approved.
- **Bell Vault arms** (`N/bell/`, 384 seeds, plain hands): staged 171.4 s, plain form 179.9 s. Arm results: mend 0 gives 173.3 s; stun 0 gives 171.5 s; no interrupt and no stagger gives 169.8 s.
- **Hour post-fix** (`N/hr/`, 192 seeds a side): mean about -1.4%. The plain Stand needs `blows: 2` (`N/over/plainhour2`).

## 2. Owner and coordinator lines
1. The Toll trim, to pass on: "The Road's Toll's four cuts on a boss now strike about a third as hard as before (poison included); it took over a third of an Act 1 boss, now about a sixth like every other Flare. Its twelve cuts on the horde, its executes and its look are unchanged."
2. **Floors (owner):** judge 2 recommends yes, narrowly.
   - When a Flare pushes a boss past a phase mark, that phase's minimum time is cut in proportion, never by more than half. Only Flare damage counts, so every phase is still seen.
   - Risk: burst Flares shorten arena boss fights, and the Flare's share of a boss climbs toward 33-56%. The cut gets tuned until the 35% line holds.
   - If no: Banked Flame stays a story-boss and safety lamp.

## 3. Tools
- Harness builds:
  - `N/bal2` is classes-8 at 9c0a0175. It has no C40 in its data, so pass `--over N/bover2/C40`.
  - `N/st5` is a scratch tree with a Bell `interrupt` knob.
  - Rebuild after logic changes: `cd godot/balance && dotnet build -c Release`.
- Story runs use cwd `godot/`. A data override covers the whole file, so make it from the *current* lamps.json.
- Python on Windows: give it `C:/...` paths.
