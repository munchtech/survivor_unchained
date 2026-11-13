# Suite speed

## Measured baseline

The coordinator ruling at `0ed1bf202` was 2,349 passed, 0 failed, 11 skipped.
Before this job's changes, integration advanced to `c29abb87a` with SU-042..049:
its baseline is **2,358 passed, 0 failed, 11 skipped** (nine net additional passes
from upstream). The unchanged `dotnet test` run on November 12 took **939.234 s
(15m 39s) end to end**, including build/restore, with no other test host observed
at the start. VSTest reported 15.3774 minutes. This measured baseline replaces
the older approximate 8.5-minute figure for the comparison here.

A prior contended run at `9c593c216` took 846.199 s alongside three other suites:
2,348 passed, 1 failed, 11 skipped. The existing smooth-normals timing assertion
measured 269 ms against its unchanged 250 ms limit. That diagnostic run is not
the comparison baseline. A sandboxed startup attempt before it aborted before
executing any tests because VSTest could not connect to its local test host.

The real Godot card-fit harness ran in both measurements: 1,914 cards, 0 fit
failures. Its no-engine/import-cache guard was not taken.

## Baseline: 25 slowest cases

Seconds are per-case TRX elapsed time, including work first initialized by that
case. The work column describes the source and helpers, not sampled CPU shares.
Classes overlap, so case times do not add up to suite wall time. The complete
per-case baseline is in [before.csv](suite_speed/before.csv).

| Rank | Test (under `SurvivorUnchained.Tests`) | Seconds | Work |
| --- | --- | ---: | --- |
| 1 | `BlockAnswerTests.Measured_held_ten_minutes_with_blocks_the_chain_against_the_written_blows` | 244.639 | 122 ten-minute held combat simulations: eight seeds, three block gaps, and four answer waits. |
| 2 | `RestedOpeningTests.No_press_pattern_beats_the_written_wait_or_the_hold(id: "oathblade")` | 203.290 | 400 seeded 60-second patterns for the named weapon, plus held references; every-step invariant checks. |
| 3 | `RestedOpeningTests.No_press_pattern_beats_the_written_wait_or_the_hold(id: "sunder")` | 142.470 | 400 seeded 60-second patterns for the named weapon, plus held references; every-step invariant checks. |
| 4 | `StoryExplorerTests.A_quick_play_of_the_story_finds_nothing_new` | 124.269 | Two roots, up to 150 story states, dialogue/zone traversal, save serialization, and finding checks. |
| 5 | `BalanceTests.Every_path_reaches_its_power` | 116.203 | Initializes the shared path probe batch: every path at 48 seeds, crowd and champion measurements. |
| 6 | `ProcWeightTests.A_status_from_a_proc_builds_at_the_blows_rate` | 106.413 | On-hit/status trigger simulations, including 700-seed bleed sweeps and 3,834 ticks per run. |
| 7 | `StatusWeightTests.A_refreshed_bleed_does_the_same_damage_a_second` | 98.713 | 1,200 seeds on each side, each holding combat for 3,834 ticks; bleed damage and sampling error. |
| 8 | `DraftCardFitTests.Every_draft_card_fits_its_card` | 88.854 | Builds the game, starts Godot headless, measures all 1,914 gathered draft cards. |
| 9 | `TailWeightTests.Poachers_mercy_doubles_as_often_as_the_blows_did` | 81.473 | Chained and unchained combat across 40 seeds, 3,834 ticks per run; chance-based doubling. |
| 10 | `BattleBalanceTests.A_crowd_is_dangerous_not_lethal` | 58.061 | 48 complete Low Ford human-bot runs at tier I; counts no-fall outcomes against the 85% floor. |
| 11 | `ZoneSimTests.The_human_bot_reaches_the_Ford_Warden_within_the_cap` | 52.314 | Plays the entire Low Ford with the human bot at tier II, including packs and the Warden. |
| 12 | `RestedOpeningTests.The_answer_pays_one_blow_in_its_wait_full_bank_or_empty` | 48.352 | Four answer waits by three block gaps, 240-second combat traces, plus full-bank cases. |
| 13 | `BattleTests.Every_weapon_fires_and_kills` | 48.327 | Builds a fresh battle for every weapon and simulates 20 seconds of firing and killing per weapon. |
| 14 | `FxTests.FlipbookCellsKeepTheirLightInside` | 48.026 | Reads and decodes every flipbook PNG, then scans every frame border and rim for excess light. |
| 15 | `MomentumChainTests.Scarce_kills_measured_chained_against_unchained` | 47.417 | Three kill rates by four seeds by two chain modes; 7,200 ticks per run and payout checks. |
| 16 | `BattleTests.Every_evolution_applies_and_still_fights` | 44.911 | Builds every evolution and simulates 12 seconds of combat for each, checking kills. |
| 17 | `ArenaPlaceTests.The_story_s_rules_hold_in_every_place(seed: 2)` | 37.465 | Generates three complete arenas (dead, Pack, Kerchiefs) and checks all placed pieces. |
| 18 | `LingerChainTests.A_held_chain_lays_one_ground_a_written_blow_at_the_blows_size(id: "sunder", shipped: False)` | 33.649 | Four 630-second combat runs: chained/unchained, with/without ground; checks rates, damage, and procs. |
| 19 | `LingerChainTests.A_held_chain_lays_one_ground_a_written_blow_at_the_blows_size(id: "oathblade", shipped: False)` | 33.211 | Four 630-second combat runs: chained/unchained, with/without ground; checks rates, damage, and procs. |
| 20 | `FlareMarksTests.A_marked_foe_killed_by_something_else_is_re_picked_marked(id: "burns_twice")` | 32.446 | Seeded marked-Flare fights with random intervening kills; checks replacement marks and timing. |
| 21 | `CutLeakTests.The_barrow_lords_holy_window_is_open_as_much_of_a_second_under_a_chain(wait: 1.6000000000000001)` | 29.517 | The same two-fight comparison at the other written wait; real zone and boss callbacks. |
| 22 | `CutLeakTests.The_barrow_lords_holy_window_is_open_as_much_of_a_second_under_a_chain(wait: 1.05)` | 28.074 | The same two-fight comparison at the other written wait; real zone and boss callbacks. |
| 23 | `BoardTests.Other_tiers_and_story_nights_take_no_board` | 27.837 | Generates non-board tier and story arenas and checks their contents. |
| 24 | `ArenaPlaceTests.The_story_s_rules_hold_in_every_place(seed: 1)` | 27.236 | Generates three complete arenas (dead, Pack, Kerchiefs) and checks all placed pieces. |
| 25 | `ArenaTests.The_horde_thickens_with_the_minutes` | 26.927 | Builds an arena and runs 45 seconds of combat across early and ten-minute horde states. |

## Cuts

- `Tests.csproj` sets `Optimize=true`. The configuration stays Debug, with
  portable symbols and the same `TRACE;DEBUG;NET;NET8_0;NETCOREAPP` constants.
  The game project excludes `tests/**` and is unchanged. For unoptimized
  debugging, use `dotnet test -p:Optimize=false`.
- `TestContent` is one reusable xUnit class fixture for `LampBoardTests`,
  `LampNavTests`, and `LampCardDemoTests`. The same 574-node content model is
  built three times instead of 22. Each class owns its model: `Hit` has a mutable
  scratch list, so a global model would introduce shared state. Lazy loading
  preserves the existing missing-content guards.
- The stationary melee dummies in `BlockAnswerTests`, `ClockTests`,
  `StatusWeightTests`, `ProcWeightTests`, and `TailWeightTests` use a 16 m arena
  instead of 120 m, from `tests/fixtures/suite_speed.json`. Her origin and the
  dummies at x=2 fit inside its playable bounds; pathing far away is irrelevant
  to their timing, status, and proc assertions. The collision grid drops from
  14,400 to 256 cells. Every simulated tick, seed, and stochastic sample stays.

No assertion text, test attribute, skip, simulation duration, or sample count
was changed. No `Thread.Sleep` or `Task.Delay` exists in the test sources.
The engine test still waits for its real child process to finish.

## Parallelism

No test-class parallelism setting or collection membership changed. Classes
already run concurrently by default. Extra parallelism is unsafe to assume:
the Balance collection changes `Lamps.UseV2`, development overrides and save
settings; PilotFeet changes `Pilot.StepsAndStands`; smooth-normal timing has its
own isolated collection. Those boundaries remain. The new class fixture does
not share mutable board state between classes; its only static spec value is
an immutable, lazily loaded number.

## Validation

### Required DraftCardFit dependency

The unfixed gate reproduced the known native crash on merged run 02:
2,363 passed, 1 failed, 11 skipped in 336.199 s. Godot aborted at
`OrnateBox.Make` / `tie_user_managed_to_unmanaged`, exit `0xC000001D`.
That run resets the consecutive-green count and is retained in the raw logs.

The already validated dependency from `codex/draft-card-fit@531307d9b` is now
ported exactly: a static root retains the frame type's native Script, and the
card harness checks its lifetime across forced collection. The focused
regression failed before that root and passed after it on this integration,
with 1,914 cards still checked. The drawing body, fonts, colors, sizes, layout,
and player text are unchanged. The lifetime check synchronizes with finalizer
completion rather than waiting a fixed amount of time.

[lifetime-regression.json](suite_speed/lifetime-regression.json) records the
red/green results and the unchanged drawing-body hash. The original dependency
report and ten earlier full green runs are in [draft_card_fit.md](draft_card_fit.md).
Its existing union-gather coverage limitation remains open; this job preserves
the baseline's card coverage. The three full runs with this dependency passed.

### Earlier measurements

The first optimized run on `94efc00bd` passed 2,358/0/11 in 773.476 s
(12m 53s), with all 35 stationary outputs identical and all 1,914 cards checked.
That is 17.6% below the 939.234 s baseline, despite another test host at its
start. The wrapper was interrupted before its second run executed tests; this
is one completed validation run, not three. Integration subsequently advanced
to `8d30ec648`; three fresh full runs are required after merging it.
`94efc00bd` itself adds only audit documentation over the measured `c29abb87a` code.
The comparison tool requires every original test name and outcome, the same
real card-fit count, and identical diagnostic output from all 35 cases in the
five stationary harnesses. A source comparison checks every original `Assert.`
line. Discovery on `8d30ec648` retained all 2,369 original cases and added
exactly six cases in `DelayedStrikeCastTests` and `RuleWickProgressionTests`.
Their exact names are in [upstream-cases.json](suite_speed/upstream-cases.json);
the tool requires all six to pass and rejects any other case-count difference.
The latest merged gate therefore expects 2,364 passed, 0 failed, 11 skipped.
This job adds, deletes, and skips no tests.

Raw TRX files, console logs, wall times, and comparison logs are retained under
`godot/tests/results/suite-speed/` (ignored). Committed CSV files preserve every
case's timing and outcome. `tools/suite_speed.py` exports them and verifies the
comparison:

```powershell
# From godot/tests; include build/restore in the wall timer.
dotnet test --logger "trx;LogFileName=run.trx" --results-directory results/suite-speed
python ../../tools/suite_speed.py results/suite-speed/run.trx --out results/suite-speed/run.csv --compare results/suite-speed/before-isolated.trx --upstream-cases ../../docs/team/suite_speed/upstream-cases.json
```

## Completed checkpoint on 8d30ec648

All three consecutive full suites passed 2,364/0/11, with 1,914 real card checks
and 35 identical stationary outputs each. Wall times were 224.383, 209.663, and
235.012 seconds (median 224.383 s, versus 939.234 s before the cuts). Their full
per-case CSVs and run metadata are under `suite_speed/verified-01` through `03`.

Integration later advanced to `e54402034`, with additional fixes and 192 balance
seeds plus eight crowd rolls. This checkpoint is preserved; a current-baseline
measurement and new merged-tree validation are pending. No expanded upstream
coverage will be reduced.
