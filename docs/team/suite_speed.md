# Suite speed

## Result on the current integration

On `e54402034`, the full suite fell from **13m 32s (812.362 s)**
to a median **6m 11s (370.824 s)**: **54.4% less wall time**.
Three consecutive full runs passed **2,386 passed, 0 failed, 11 skipped**, exactly
matching the current baseline. Every run checked the same 1,914 cards and
produced identical numerical output from all 35 stationary-harness cases.

The coordinator's older ruling was 2,349/0/11. Subsequent integration commits
added fixes/tests and widened balance sampling to **192 seeds per path** and
**eight crowd rolls per sampled build**. The current before/after comparison
uses that same expanded workload, with no sample or threshold reduction.
The required DraftCardFit lifetime dependency is present in both modes.

| Full run | End-to-end seconds | Time | Passed / failed / skipped | Cards | Matching numerical outputs |
| --- | ---: | --- | --- | ---: | --- |
| Before | 812.362 | 13m 32s | 2,386 / 0 / 11 | 1,914 | reference |
| 1 | 370.824 | 6m 11s | 2,386 / 0 / 11 | 1,914 | 35/35 |
| 2 | 523.247 | 8m 43s | 2,386 / 0 / 11 | 1,914 | 35/35 |
| 3 | 339.612 | 5m 40s | 2,386 / 0 / 11 | 1,914 | 35/35 |

Times include `dotnet test` build/restore and engine startup, not just VSTest's
reported test interval. Competing test hosts at each start are recorded in the run JSON files; the
second optimized run had one other test host active. Wall time still varies; the table reports every final run, not a
selected fast run. Per-case times overlap because existing classes run
concurrently; shared lazy setup is charged to the first case that accesses it.

The committed [summary](suite_speed/summary.json),
[baseline CSV](suite_speed/current-before.csv),
[run 1](suite_speed/final-01.csv), [run 2](suite_speed/final-02.csv), and
[run 3](suite_speed/final-03.csv) retain every case and outcome. Run JSON files
also retain wall clocks, configuration, JIT flags, and host counts.

## The 25 slowest baseline cases

Seconds are TRX per-case elapsed times. After is the median of the three final
runs. Work descriptions come from reading each test and its helpers; they are
not sampled CPU percentages.

| Rank | Test (under `SurvivorUnchained.Tests`) | Before s | After median s | Work |
| --- | --- | ---: | ---: | --- |
| 1 | `BalanceTests.Every_path_reaches_its_power` | 247.461 | 86.347 | Initializes the shared 192-seed-per-path probe matrix: drafting, crowd and champion combat, then path medians. |
| 2 | `BlockAnswerTests.Measured_held_ten_minutes_with_blocks_the_chain_against_the_written_blows` | 199.723 | 125.714 | 122 ten-minute combat simulations: two hold references, eight seeds, three block gaps, and four answer waits. |
| 3 | `RestedOpeningTests.No_press_pattern_beats_the_written_wait_or_the_hold(id: "oathblade")` | 152.151 | 65.094 | 400 seeded 60-second patterns per weapon, held references, and every-step weight/heavy-count assertions. |
| 4 | `StoryExplorerTests.A_quick_play_of_the_story_finds_nothing_new` | 71.067 | 67.853 | Two roots and up to 150 story states: dialogue/zone traversal, save serialization, and findings. |
| 5 | `BalanceTests.No_single_rule_carries_a_build` | 70.901 | 33.186 | The first 12 builds per path, each averaged over eight crowd rolls; checks the unchanged 45% rule-share bar. |
| 6 | `ProcWeightTests.A_status_from_a_proc_builds_at_the_blows_rate` | 68.903 | 69.410 | Status/proc combat, including 700-seed bleed sweeps and 3,834 ticks per run. |
| 7 | `StatusWeightTests.A_refreshed_bleed_does_the_same_damage_a_second` | 68.775 | 46.197 | 1,200 seeds per chain mode, 3,834 ticks each; bleed damage, mean ratio, and sampling error. |
| 8 | `RestedOpeningTests.No_press_pattern_beats_the_written_wait_or_the_hold(id: "sunder")` | 60.027 | 22.891 | 400 seeded 60-second patterns per weapon, held references, and every-step weight/heavy-count assertions. |
| 9 | `DraftCardFitTests.Every_draft_card_fits_its_card` | 59.468 | 56.235 | Builds the game, launches headless Godot, checks native script lifetime and all 1,914 gathered cards. |
| 10 | `TailWeightTests.Poachers_mercy_doubles_as_often_as_the_blows_did` | 58.533 | 67.114 | 40 seeds per chain mode, 3,834 ticks each; chance-based doubling and its rate. |
| 11 | `ZoneSimTests.The_human_bot_reaches_the_Ford_Warden_within_the_cap` | 51.860 | 31.981 | The complete Low Ford at tier II under the human bot, including packs, the Warden, and density recording. |
| 12 | `FxTests.FlipbookCellsKeepTheirLightInside` | 47.964 | 16.463 | Reads/decodes every flipbook PNG and scans each frame border and rim. |
| 13 | `MomentumChainTests.Scarce_kills_measured_chained_against_unchained` | 39.621 | 43.278 | Three kill rates by four seeds by two chain modes, 7,200 ticks per run; payout comparisons. |
| 14 | `BattleTests.Every_weapon_fires_and_kills` | 35.665 | 11.095 | A fresh battle for every weapon and 20 seconds of held combat per weapon, checking kills. |
| 15 | `BattleTests.Every_evolution_applies_and_still_fights` | 32.587 | 34.270 | Builds every evolution and simulates 12 seconds of combat for each, checking kills. |
| 16 | `RestedOpeningTests.The_answer_pays_one_blow_in_its_wait_full_bank_or_empty` | 32.468 | 49.485 | Four answer waits by three block gaps, 240-second combat traces, plus full-bank cases. |
| 17 | `LingerChainTests.A_held_chain_lays_one_ground_a_written_blow_at_the_blows_size(id: "oathblade", shipped: False)` | 29.511 | 37.388 | Four 630-second runs: chained/unchained, with/without ground; checks rates, damage, and procs. |
| 18 | `CutLeakTests.The_barrow_lords_holy_window_is_open_as_much_of_a_second_under_a_chain(wait: 1.05)` | 29.151 | 33.208 | Two real Barrow Lord fights, reaches his down state, then compares 60 seconds of holy-window ticks. |
| 19 | `CutLeakTests.The_barrow_lords_holy_window_is_open_as_much_of_a_second_under_a_chain(wait: 1.6000000000000001)` | 27.211 | 10.550 | Two real Barrow Lord fights, reaches his down state, then compares 60 seconds of holy-window ticks. |
| 20 | `MapGenTests.An_arena_is_dressed_as_its_people_keep_it(people: "kerchiefs", piece: "props/")` | 26.609 | 12.656 | Generates the named arena and a Pack-wood reference; checks dressing, lights, cover, and trees. |
| 21 | `BattleBalanceTests.A_crowd_is_dangerous_not_lethal` | 26.292 | 21.060 | 48 full Low Ford human-bot runs at tier I; checks the no-fall floor of 41/48. |
| 22 | `ArenaTests.The_kindling_puts_a_core_and_the_rulers_keeper_before_the_great_blessing(people: "dead", keeperDef: "lt_dead")` | 25.316 | 10.302 | Two generated arenas: breaks one core and simulates the other for 61 seconds to test its timeout and blessing. |
| 23 | `ArenaTests.The_kindling_puts_a_core_and_the_rulers_keeper_before_the_great_blessing(people: "pack", keeperDef: "lt_pack")` | 22.426 | 8.648 | Two generated arenas: breaks one core and simulates the other for 61 seconds to test its timeout and blessing. |
| 24 | `LingerChainTests.A_held_chain_lays_one_ground_a_written_blow_at_the_blows_size(id: "sunder", shipped: False)` | 22.132 | 9.626 | Four 630-second runs: chained/unchained, with/without ground; checks rates, damage, and procs. |
| 25 | `ArenaTests.The_kindling_puts_a_core_and_the_rulers_keeper_before_the_great_blessing(people: "lamplings", keeperDef: "lt_lamplings")` | 20.085 | 7.072 | Two generated arenas: breaks one core and simulates the other for 61 seconds to test its timeout and blessing. |

## Safe cuts

- `Tests.csproj` enables compiler optimization while retaining Debug,
  portable symbols, and the same `TRACE;DEBUG;NET;NET8_0;NETCOREAPP` constants.
  The actual assembly's `IsJITOptimizerDisabled` changed from true to false.
  `SurvivorUnchained.csproj` is unchanged and excludes `tests/**`; this setting
  does not alter the game build. Use `dotnet test -p:Optimize=false` for
  unoptimized debugging.
- One reusable `TestContent` class fixture serves `LampBoardTests`,
  `LampNavTests`, and `LampCardDemoTests`: three builds of the same 574-node
  content model instead of 22. Each class owns its model because `Hit` has a
  mutable scratch list. Lazy construction retains the existing data guards.
- `BlockAnswerTests`, `ClockTests`, `StatusWeightTests`, `ProcWeightTests`, and
  `TailWeightTests` use a 16 m stationary arena instead of 120 m, configured in
  `tests/fixtures/suite_speed.json`. Her origin and the dummies at x=2 stay well
  inside its bounds; distant pathing is outside those assertions. The collision
  grid drops from 14,400 to 256 cells. Every tick, seed, and stochastic sample
  remains, including the ten-minute matrices and all 220-blow clock checks.

For the current control, the two board test files used integration's uncached
setup, the stationary size was 120, and the CLI set `Optimize=false`. The native
lifetime dependency was common to control and final modes. The final fixture
files and size 16 were restored before all three final runs.

Every current original `Assert.` line was compared before and after restoration.
This job adds, deletes, and skips no xUnit cases, and weakens no assertion.
The comparison tool requires exact names/outcomes, real card output, and all
35 identical stationary outputs. The [numerical reference](suite_speed/current-stationary-output.json)
and its digest are committed. No `Thread.Sleep` or `Task.Delay` was added.

## Parallelism

No parallelism setting or collection membership changed. Classes already run
concurrently by default. Additional parallelism is unsafe to assume: Balance
changes the global Lamps version, development overrides and save settings;
PilotFeet changes `Pilot.StepsAndStands`; smooth-normal timing has an isolated
collection. Those boundaries remain. The content fixture keeps mutable board
scratch storage inside its owning class; its static spec value is immutable.

## Required DraftCardFit dependency

An earlier merged run reproduced the known native failure: 2,363 passed,
1 failed, 11 skipped; Godot aborted at `OrnateBox.Make` /
`tie_user_managed_to_unmanaged`, exit `0xC000001D`. That failure reset the green
streak and remains in the logs.

The validated fix from `codex/draft-card-fit@531307d9b` is ported exactly:
retain the frame type's native Script and check its lifetime across forced
collection. The focused regression failed before the root (34.665 s) and passed
after it (30.851 s), with all 1,914 card fits preserved. The collection barrier
waits for finalizers to complete; it does not use a timed delay.

The drawing body, fonts, colors, sizes, layout, and player text are unchanged.
[lifetime-regression.json](suite_speed/lifetime-regression.json) records the
red/green result and unchanged drawing-body hash. The original dependency's ten
earlier full green runs are documented in [draft_card_fit.md](draft_card_fit.md).

**Existing open item:** the card harness's union-ingredient gathering limitation
remains. Its baseline 1,914-card coverage is preserved.

## Measurement history and reproduction

The first measured `c29abb87a` baseline was 2,358/0/11 in 939.234 s. An earlier
contended run failed the existing 250 ms smooth-normal bound at 269 ms; its
bound was retained. A sandboxed startup attempt aborted before executing tests
because VSTest could not connect to its test host. An interrupted wrapper after
one successful run was not counted as three runs.

On `8d30ec648` plus the cuts and native dependency, three full runs passed
2,364/0/11 in 224.383, 209.663, and 235.012 s, with the same 1,914 cards and 35
outputs. [checkpoint-8d30ec648.json](suite_speed/checkpoint-8d30ec648.json) and
its CSVs preserve that checkpoint. The matched current comparison above
supersedes it after integration expanded the workload.

Raw TRX, console, comparison, and wall-clock files remain under the ignored
`godot/tests/results/suite-speed/`. The committed CSV/JSON files preserve the
measurement evidence independently. To measure another full run:

```powershell
# From godot/tests; also time the entire command.
dotnet test --logger "trx;LogFileName=run.trx" --results-directory results/suite-speed
python ../../tools/suite_speed.py results/suite-speed/run.trx --out results/suite-speed/run.csv --compare results/suite-speed/current-before.trx
```
