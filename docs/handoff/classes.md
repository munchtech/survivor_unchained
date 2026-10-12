# Handoff: classes (phase 2: staged Flares measured, judge next)

Written by the seventh classes lead (12 October) at the context budget. Branch `classes-6` (worktree `agent-a5b513003773e2317`). See the last line for the commit.

## 1. The owner's words
- "go with all 8 recommendations" (CLASSES §8); the Flare "should be AWESOME. it should look AWESOME."; "we are striving for perfection". 12 October: "go just classes for now" (classes is the only lead running).
- 11 October: "rebuke should probably do a little more damage than that yeah".
- 12 October, Banked Flame: (1) "sounds good": Light my way never lights it (DONE, `LampBook.Suggest` skips `flare.banked`). (2) "0-5% faster is barely anything though, seems like its a lot of risk with not much reward". Played well, it must be a clear reward worth the risk of its 30% slower fill, and its text must make it a trap-free choice. "A blue lamp should feel worth building around."

## 2. The brief (main session, 12 October) and where each step stands
1. **The rebuke's checks: DONE, reported to main.** Whole, it took 8-14% of a boss, a rival to the Flare. A boss now takes half (`shield_arm boss=0.5`, in its text): 4.5-5.3%. Act 1 with a bulwark (`story --type bulwark`) is within -5%/+4% of the old rule, falls no higher. The Prologue can't hold a bulwark (no type choice in play yet; SetType is harness-only) and has no balance harness; Act 1 at level 1 stands in for it.
2. **Merge: GO sent to main** (judge's verdict, 12 October, below). The judge's one before-merge check (fix 1) already holds: the Strike stretches to its last blow (`flareLen` in Flare.cs:184), and `The_fourth_toll_and_the_healing_peal` lands four tolls and the blast.
3. **Phase 2 judged: GO, PASS WITH FIXES.** The numbers are in `scratchpad/c7/sheet2.md`; `c7/fin/` holds Burns at x0.8 in the arena plus the Banked Flame cells (unread). The judge's fixes, in priority:
   - (2) `TollCut`'s fallback puts the boss last (`OrderBy(x => x.Boss)`), and a re-picked cut on a boss carries onBoss/Blows; re-run Act 1 for the stalker and keep x0.85 if the mean stays within ±3%.
   - (3) Burns: run Act 1 for the arcanist at x0.9 and x1.0 (after the ember fix) and take 1.0 if it meets the bar (mean within ±3%, no cell beyond ±6%).
   - (4) Called Down keeps its target from the frost and moves to the next toughest. No ember falls on open ground while anything stands in reach. Seeking embers pass over a boss that can't be hurt (rename `TollCanHurt` to `FlareCanHurt`). Re-measure the kindler (band 1.29 at T3; full T4 at 15% or more).
   - (5) Butcher's Hour: "each kill adds 0.3 s, up to 8 s more" goes in its brief and lamp text; Overtime caps at 12 s more. Measure the butcher's band and Not Today's deaths.
   - (6) CLASSES §7 acceptance becomes: (i) Act 1 calibration per staged Flare against its plain form: mean kill time within ±3%, no cell beyond ±6%, falls in noise; (ii) arena, health taken, full board: median of types 15-25% at every tier, each Flare 15-30%, the empty board reported but not banded; (iii) Stands judged by uplift (boss dps while it holds over outside, times uptime); (iv) once: a gates-off arena boss to prove the reading.
   - (7) The sheet's 3.78 is 3.0 nominal (3.78 is after the build's damage).
   - (8) Burns's first impact gets 3 frames of hitstop.
   - (9) A boss killed by the Toll's poison after the Strike still plays the last blow (`FlareOnKilled` returns once FlareT <= 0).
   Measure before the owner plays (not blocking): which modifiers Light my way lights before an Act 1 boss (if Called Down or Toll Doubled, run Act 1 with them: no cell more than 5% faster); Act 1 for bulwark/Bell and butcher/Hour against their plain forms; the Hour's uplift, its plain form's T3-T4 kill time, its mending on a boss, and executes a second at T4. Tier-1 median (25.8%): wait for phase 6, then re-measure at 96 seeds.
4. **Banked Flame, after the verdict:** re-run the two cells (in `c7/fin/`, the banking pilot). Then propose 2-3 options with numbers at 48 seeds for the banking pilot and a non-banking one (`--bank 0`), for example a 15-20% price, a second charge that fills faster or comes cheaper, or a gift that pays even when spent at once (say, a banked charge's Flare 25% stronger). Have the judge pick, and fold the pick into the go/no-go.

## 3. Decisions this session (why)
- The Toll's poison is its own DoT (`TollVenom`/`TickVenom` in FlareStaged.cs). Her poison stack ticks at its strongest rate times its stacks, so a 2100-power cut lifted her whole stack and took its credit (71% of a boss at T4).
- The Toll's boss cuts carry four cuts' worth (`onBoss`; data `bossWorth` overrides). This is the plain form's worth after power went 700 to 2100. The judge had written "12/boss cuts", but at 12 it did 5-8x the plain form per cast.
- Burns' embers strike a boss only when aimed at it, and never fall back onto a lone boss.
- `bossMul` (a Flare arg in FlareHit, bosses only), calibrated on Act 1 story kill time: Burns 0.8, Toll 0.85. The arena took-share is set by the boss gates, so it is no lever (sheet D).

## 4. Gotchas
- The harness reads `lamps.json` at process start. Variant scripts patch `lamps_quarters.py`, rebuild and restore (`c7/var.sh`, `c7/r3.sh`). Never build Release balance while a run is going: the dll is locked, the build fails quietly with "2 Error(s)" and the old dll runs.
- Baseline (integration) harness: `c7/base/godot/balance/bin/Release/net8.0/Balance.dll` (git archive of integration, built). Its story has no `--type`.
- In foreground bash, wait with `for i in $(seq 1 58); do [ -f done ] && break; sleep 10; done`.
- Scripts in `c7/`: `rebcheck.py` (rebuke A/B), `p2stat.py [--split] label=file` (Flare per type/tier, boss split by source), `stcmp.py base now [callings]` (story), and c6's `typeband.py`. Scratch root: `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\ba85aba8-36f4-4cf9-99c5-4c5ef9e4a65c\scratchpad\`.

## 5. Files to read first
`godot/logic/Sim/FlareStaged.cs`, `Flare.cs` (FlareBlow), `WardenLamps.cs` (Rebuke), `godot/logic/Rpg/LampBook.cs` (Suggest), `tools/classes/lamps_quarters.py` (the flare() lines), `docs/design/CLASSES.md` §3.6 and §7, `c7/sheet2.md`.
