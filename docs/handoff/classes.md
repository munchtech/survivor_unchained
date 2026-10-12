# Handoff: classes (phase 2 in progress)

Written by the sixth classes lead (12 October), at the context budget. Branch `classes-6` (worktree `agent-a5b513003773e2317`), from integration 52a0cc22. See the last line for the commit.

## 1. The owner's words

- "go with all 8 recommendations" (CLASSES §8); the Flare "should be AWESOME. it should look AWESOME."; "we are striving for perfection". 12 October: "go just classes for now" (experience, VFX and animation paused: classes owns the logic, numbers and harness; the look waits).
- 11 October: "rebuke should probably do a little more damage than that yeah"; home bonus x1.03 accepted until phase 5 (don't chase it).
- Story: keep `Ev.Rise`, `Ev.PlayerDeath`, `Ev.Flare.Clutch`, `Battle.FlareClutches` clean and countable; don't build the toll.

## 2. The brief (from the main session) and where each step stands

1. **Banked Flame in the pilot:** DONE, judged PASS WITH FIXES. `Pilot.cs` banks (`--bank 0` for the old hands). Recommendation for the owner (relay): Light my way should never light it (banked it's a sidegrade within noise; unbanked a trap: sunderer T4 L10 boss 120 s vs 90-94 s). If the owner agrees: make `LampBook.Suggest` skip `flare.banked`'s lamp, then re-run the sunderer T4 L10 and L30 full cells. Judge's fixes left: report "first charge ready" beside "first cast" for banked runs (the 5.2-min first cast is the pilot holding it); phase 7: a falling pilot (plain, T4 L10) with and without it, compare falls and FlareClutches; if the reserve saves nothing, price 30% to 20%. §7 exemption written.
2. **The rebuke:** BUILT, judged PASS WITH FIXES, fixes 1-4 done (stones.barrier at 3; Mortar text; cadence text; Wider Rebuke re-specified as *Readier Wall*, five stones; Parry without Shield Arm no longer fires zero-radius rebukes). **Two checks before merge (not done):** (a) the rebuke's share of boss health taken (`BossHealthBy["rebuke"]`; add a harness field) and the bulwark's boss kill time before (integration) vs after; above ~10% of a boss it competes with the Flare. (b) Story fights with a bulwark (Shield Arm is lit from level 1): Prologue and Act 1's four bosses, length and falls vs the restored lengths (`Balance.dll story`; see the 69a94126 commit and CLASSES §7 Open (5)).
3. **The Road's Toll:** DONE, judged PASS. It never missed: the share's denominator counted damage poured into boss gates. New measure `Battle.BossHealthBy` / `FlareBossTook`; §7 acceptance moved to it. Reopened: T1 median 26.9%, butcher 28-31% at T1-T3.
4. **Phase 2 logic:** BUILT AND TESTED (827 green), **UNMEASURED, UNJUDGED.** `godot/logic/Sim/FlareStaged.cs`: Bell (tolls stun the lesser, sear, mend 4%; last a holy blast 8 m), Burns Twice (frost freezes, embers seek frozen packs, 4 of 12 on a boss, shatter then fire), Road's Toll (12 single-target cuts, weakest first, last four on a boss, poison, execute below 25%), Butcher's Hour (no pulses: Frenzy full, waits x0.5, every blow bleeds, executes below 15%, kill +0.3 s up to its length again, mend 1%). All 12 modifier lamps live (`Lamps.LivePhase = 2`). Data in `lamps_quarters.py` (`beat=`, `args=`); events in `Events.cs`. Next: measure all four (types T1-T4 full and empty, 48 seeds; health-taken share 15-25%, T1 at most 25%, T4 full at least 15%; the band), tune the args, then a judge on the design and numbers.
   - **The judge's must-dos for the Toll before measuring:** boss cuts carry the whole boss share (12 / boss cuts each), so damage doesn't swing x3 with the add count; skip a boss that can't be hurt (TakenMul 0) or is pinned at its gate with its Break full; credit the cuts' poison to the Flare (`ApplyStatus` keeps the first poisoner: `cur.From ??= from`).
   - Butcher's Hour has no damage of its own now: judge its value by boss kill time and the butcher's band, not by Flare share (the harness credits its blows to her skills). Its extension cap (its own length again) is my call: put it to the judge.
5. **Butcher band:** watched, lowest (0.76-0.86), in band. Don't trim lamps.

## 3. Numbers and scripts

Scratchpad `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\ba85aba8-36f4-4cf9-99c5-4c5ef9e4a65c\scratchpad\c6\`: `sheet1.md` (every step 1-3 number), `s3/` (the post-change sweep: all types T1-T4 full, bulwark and roadknife empty), `bank/`, `reb/`, `toll/` (runs). Scripts: `flarecmp.py` (configs per type), `fshare.py` (Flare share both ways, rebuke), `rebstat.py`, `tollstat.py <type>`, `typeband.py`, `reb.sh`/`reb2.sh` (patched-rule variants), `s3.sh`. Copy, don't edit in place.

## 4. Gotchas

- The harness reads `godot/data/content/lamps.json` from the worktree at process start: never run `lamps_build.py` or rebuild `godot/balance` Release while a sweep runs.
- Spawn judges, workers and runners in the foreground. Worktree bash guard: no `git` in compound commands, no `bash <script>` with `cd` + variables in one line; put loops in a script file and run it alone.
- A full all-types T1-T4 sweep at 48 seeds takes about 25 min at `--par 20`; T4 L30 about 13 min per config. Waiting: `for i in $(seq 1 58); do [ -f done ] && break; sleep 10; done` in a foreground call (Monitor notices don't wake an agent that ended its turn).
- Healing in tests runs through the build's healing stats: compare ratios, not absolutes.

## 5. Files to read first

`godot/logic/Sim/FlareStaged.cs`, `Flare.cs` (UseFlare, FlareBlow, TickFlare), `godot/balance/Harness/Pilot.cs` (Act), `WardenLamps.cs` (AddStone, LampsOnBlowLanded), `docs/design/CLASSES.md` §3.5-3.6 and §7, `docs/team/classes.md`.

Commits: steps 1-3 at 02691c99 (before the judge's fixes); phase 2 WIP at 9b91bd0e; the judge's fixes and docs on top. Steps 1-3 can't merge alone cleanly any more (the fixes sit after the phase 2 commit): cherry-pick 02691c99 and the fixes commit, or merge the branch once phase 2 is judged.
