# Suite speed

## Current result

On integration **`0af0bc73f01617d70e9f5de2a05404ffbe81cc20`**, the full command
fell from **14m 20s (860.083 s)** to a median
**9m 25s (565.242 s)**: **34.3% less wall time**.
The clean integration control and three consecutive optimized suites all
returned **2,603 passed, 0 failed, 11 skipped**. All four runs checked the same
**3,338 cards across all four callings**. Each optimized run matched every
baseline case name/outcome and all **35 stationary case outputs** exactly.

These measurements were made November 13, 2026 on the same owner's machine,
in the same isolated worktree. The control was the clean, fetched integration
tip before any cuts; its tests used the default unoptimized Debug build.
The cuts were then merged with that exact tip before the three final runs.
The latest inbox ruling named the older `d310d57db` and 2,442/0/11; fetching
origin found the newer tip above. This report uses its freshly measured
2,603/0/11 baseline, without allowances for added or missing cases.

| Full run | End-to-end seconds | Time | Passed / failed / skipped | Other test hosts at start |
| --- | ---: | --- | --- | ---: |
| Clean integration | 860.083 | 14m 20s | 2,603 / 0 / 11 | 0 |
| Optimized 1 | 564.102 | 9m 24s | 2,603 / 0 / 11 | 0 |
| Optimized 2 | 799.601 | 13m 20s | 2,603 / 0 / 11 | 1 |
| Optimized 3 | 565.242 | 9m 25s | 2,603 / 0 / 11 | 1 |

End-to-end clocks include build/restore and engine startup. Per-case TRX
durations overlap because existing classes run concurrently, so they do not
sum to command time or measure CPU cost. Scheduling, contention, and lazy
setup can move individual durations substantially; every final run is shown,
and the after ranking uses each case's median over all three runs. Some case
times increased. Optimized runs 2 and 3 began with another worktree's test
host present; its process identity and start time are retained in the run JSON.
Host checks are startup snapshots, rather than a continuous machine-idle
guarantee. The observed wall-time comparison includes all runs and does not
isolate the contribution of each cut.

The [summary](suite_speed/round3-summary.json) records configuration and the
stationary output digest. Complete per-case timings and outcomes are in the
[baseline CSV](suite_speed/round3-before.csv),
[run 1 CSV](suite_speed/round3-after-01.csv),
[run 2 CSV](suite_speed/round3-after-02.csv), and
[run 3 CSV](suite_speed/round3-after-03.csv). Each corresponding `-run.json`
retains wall time, source hash, host snapshot, and counters.

## The 25 slowest before

Seconds are elapsed TRX durations. Work descriptions come from reading the
tests and their helpers, rather than sampled CPU profiles.

| Rank | Test under `SurvivorUnchained.Tests` | Before s | After median s | Work |
| --- | --- | ---: | ---: | --- |
| 1 | `BalanceTests.Every_path_reaches_its_power` | 232.630 | 93.891 | Initializes the shared 192-seed-per-path probe matrix: drafting, crowd and champion combat, then path medians. |
| 2 | `BlockAnswerTests.Measured_held_ten_minutes_with_blocks_the_chain_against_the_written_blows` | 180.734 | 223.541 | 122 ten-minute combat simulations: two hold references, eight seeds, three block gaps, and four answer waits. |
| 3 | `RestedOpeningTests.No_press_pattern_beats_the_written_wait_or_the_hold(id: "oathblade")` | 150.842 | 158.081 | 400 seeded 60-second patterns per weapon, held references, and every-step weight/heavy-count assertions. |
| 4 | `DraftCardFitTests.Every_draft_card_fits_its_card` | 91.781 | 133.474 | Builds the game, launches headless Godot, gathers all four callings, and checks 3,338 cards. |
| 5 | `StoryExplorerTests.A_quick_play_of_the_story_finds_nothing_new` | 85.867 | 185.461 | Two roots and up to 150 story states: dialogue/zone traversal, save serialization, and findings. |
| 6 | `ZoneSimTests.The_human_bot_reaches_the_Ford_Warden_within_the_cap` | 85.178 | 159.544 | The complete Low Ford at tier II under the human bot, including packs, the Warden, and density recording. |
| 7 | `StatusWeightTests.A_refreshed_bleed_does_the_same_damage_a_second` | 83.078 | 209.204 | 1,200 seeds per chain mode, 3,834 ticks each; bleed damage, mean ratio, and sampling error. |
| 8 | `BalanceTests.No_single_rule_carries_a_build` | 82.290 | 33.514 | The first 12 builds per path, each averaged over eight crowd rolls; checks the unchanged 45% rule-share bar. |
| 9 | `TailWeightTests.Poachers_mercy_doubles_as_often_as_the_blows_did` | 64.385 | 130.493 | 40 seeds per chain mode, 3,834 ticks each; chance-based doubling and its rate. |
| 10 | `ProcWeightTests.A_status_from_a_proc_builds_at_the_blows_rate` | 62.513 | 153.676 | Status/proc combat, including 700-seed bleed sweeps and 3,834 ticks per run. |
| 11 | `RestedOpeningTests.No_press_pattern_beats_the_written_wait_or_the_hold(id: "sunder")` | 55.294 | 26.131 | 400 seeded 60-second patterns per weapon, held references, and every-step weight/heavy-count assertions. |
| 12 | `BattleTests.Every_weapon_fires_and_kills` | 44.134 | 52.238 | A fresh battle for every weapon and 20 seconds of held combat per weapon, checking kills. |
| 13 | `CutLeakTests.The_barrow_lords_holy_window_is_open_as_much_of_a_second_under_a_chain(wait: 1.6000000000000001)` | 37.406 | 27.609 | Two real Barrow Lord fights, reaches his down state, then compares 60 seconds of holy-window ticks. |
| 14 | `ArenaPlaceTests.The_story_s_rules_hold_in_every_place(seed: 2)` | 36.511 | 12.118 | Generates Barrow, Hollow, and Ruts arenas for the seed, then checks the story-specific piece exclusions. |
| 15 | `ArenaTests.The_kindling_puts_a_core_and_the_rulers_keeper_before_the_great_blessing(people: "dead", keeperDef: "lt_dead")` | 35.749 | 18.417 | Two generated arenas: breaks one core and simulates the other for 61 seconds to test its timeout and blessing. |
| 16 | `FxTests.FlipbookCellsKeepTheirLightInside` | 35.418 | 35.267 | Reads/decodes every flipbook PNG and scans each frame border and rim. |
| 17 | `BattleBalanceTests.A_crowd_is_dangerous_not_lethal` | 32.827 | 21.878 | 48 full Low Ford human-bot runs at tier I; checks the no-fall floor of 41/48. |
| 18 | `MapGenTests.An_arena_is_dressed_as_its_people_keep_it(people: "lamplings", piece: "halloween/lantern_standing")` | 32.813 | 19.120 | Generates the Lamplings arena and a Pack-wood reference, then checks dressing, lights, cover, and trees. |
| 19 | `BoardTests.Other_tiers_and_story_nights_take_no_board` | 31.372 | 35.987 | Generates four tier, story-night, and people variants to check their board exclusions and story spec. |
| 20 | `MomentumChainTests.Scarce_kills_measured_chained_against_unchained` | 31.242 | 113.811 | Three kill rates by four seeds by two chain modes, 7,200 ticks per run; payout comparisons. |
| 21 | `BattleTests.Every_evolution_applies_and_still_fights` | 28.584 | 59.422 | Builds every evolution and simulates 12 seconds of combat for each, checking kills. |
| 22 | `CutLeakTests.The_barrow_lords_holy_window_is_open_as_much_of_a_second_under_a_chain(wait: 1.05)` | 26.614 | 78.803 | Two real Barrow Lord fights, reaches his down state, then compares 60 seconds of holy-window ticks. |
| 23 | `LingerChainTests.A_held_chain_lays_one_ground_a_written_blow_at_the_blows_size(id: "oathblade", shipped: False)` | 23.261 | 29.850 | Four 630-second runs: chained/unchained, with/without ground; checks rates, damage, and procs. |
| 24 | `RestedOpeningTests.The_answer_pays_one_blow_in_its_wait_full_bank_or_empty` | 22.531 | 63.111 | Four answer waits by three block gaps, 240-second combat traces, plus full-bank cases. |
| 25 | `StatusWeightTests.An_eighty_percent_stun_lands_as_often` | 22.438 | 40.406 | 600 seeds per chain mode, 3,834 ticks each; compares stun counts, rate, and sampling error. |

## The 25 slowest after

| Rank | Test under `SurvivorUnchained.Tests` | After median s | Before s | Work |
| --- | --- | ---: | ---: | --- |
| 1 | `BlockAnswerTests.Measured_held_ten_minutes_with_blocks_the_chain_against_the_written_blows` | 223.541 | 180.734 | 122 ten-minute combat simulations: two hold references, eight seeds, three block gaps, and four answer waits. |
| 2 | `StatusWeightTests.A_refreshed_bleed_does_the_same_damage_a_second` | 209.204 | 83.078 | 1,200 seeds per chain mode, 3,834 ticks each; bleed damage, mean ratio, and sampling error. |
| 3 | `StoryExplorerTests.A_quick_play_of_the_story_finds_nothing_new` | 185.461 | 85.867 | Two roots and up to 150 story states: dialogue/zone traversal, save serialization, and findings. |
| 4 | `ZoneSimTests.The_human_bot_reaches_the_Ford_Warden_within_the_cap` | 159.544 | 85.178 | The complete Low Ford at tier II under the human bot, including packs, the Warden, and density recording. |
| 5 | `RestedOpeningTests.No_press_pattern_beats_the_written_wait_or_the_hold(id: "oathblade")` | 158.081 | 150.842 | 400 seeded 60-second patterns per weapon, held references, and every-step weight/heavy-count assertions. |
| 6 | `ProcWeightTests.A_status_from_a_proc_builds_at_the_blows_rate` | 153.676 | 62.513 | Status/proc combat, including 700-seed bleed sweeps and 3,834 ticks per run. |
| 7 | `DraftCardFitTests.Every_draft_card_fits_its_card` | 133.474 | 91.781 | Builds the game, launches headless Godot, gathers all four callings, and checks 3,338 cards. |
| 8 | `TailWeightTests.Poachers_mercy_doubles_as_often_as_the_blows_did` | 130.493 | 64.385 | 40 seeds per chain mode, 3,834 ticks each; chance-based doubling and its rate. |
| 9 | `MomentumChainTests.Scarce_kills_measured_chained_against_unchained` | 113.811 | 31.242 | Three kill rates by four seeds by two chain modes, 7,200 ticks per run; payout comparisons. |
| 10 | `HordeBench.A_great_horde_plays_the_same_twice` | 112.676 | 16.986 | Runs two identical 300-creature hordes, each with 60 warmup and 120 measured ticks, and compares fingerprints and kills. |
| 11 | `BalanceTests.Every_path_reaches_its_power` | 93.891 | 232.630 | Initializes the shared 192-seed-per-path probe matrix: drafting, crowd and champion combat, then path medians. |
| 12 | `CutLeakTests.The_barrow_lords_holy_window_is_open_as_much_of_a_second_under_a_chain(wait: 1.05)` | 78.803 | 26.614 | Two real Barrow Lord fights, reaches his down state, then compares 60 seconds of holy-window ticks. |
| 13 | `ArenaTests.The_horde_thickens_with_the_minutes` | 70.096 | 12.083 | Generates and opens an arena, runs 20 seconds, advances to minute ten, then runs 25 seconds and compares crowd size and composition. |
| 14 | `RestedOpeningTests.The_answer_pays_one_blow_in_its_wait_full_bank_or_empty` | 63.111 | 22.531 | Four answer waits by three block gaps, 240-second combat traces, plus full-bank cases. |
| 15 | `BattleTests.Every_evolution_applies_and_still_fights` | 59.422 | 28.584 | Builds every evolution and simulates 12 seconds of combat for each, checking kills. |
| 16 | `BattleTests.Every_weapon_fires_and_kills` | 52.238 | 44.134 | A fresh battle for every weapon and 20 seconds of held combat per weapon, checking kills. |
| 17 | `CraftingEconomy.Act_one_crafting_meets_its_targets` | 50.360 | 7.735 | Generates arena rules and runs three eight-seed, ten-day crafting economies, then checks timing, spending, and resource targets. |
| 18 | `WickRulesTests.Every_lamp_on_the_four_skills_changes_the_number_its_sentence_promises` | 48.424 | 17.463 | Builds paired lit/unlit combat scenes for every lamp across four skills and measures the promised numeric change. |
| 19 | `BoardTests.A_tier_one_pack_arena_is_a_board_held_through_its_gaps(seed: 3)` | 45.975 | 19.602 | Generates the board and story-night reference, flood-checks walkable ground and chokes, and checks lights, dimensions, and cover. |
| 20 | `BoardTests.A_tier_one_pack_arena_is_a_board_held_through_its_gaps(seed: 311)` | 45.897 | 9.534 | Generates the board and story-night reference, flood-checks walkable ground and chokes, and checks lights, dimensions, and cover. |
| 21 | `MapGenTests.An_arena_is_dressed_as_its_people_keep_it(people: "kerchiefs", piece: "props/")` | 42.614 | 6.041 | Generates the named arena and a Pack-wood reference; checks dressing, lights, cover, and trees. |
| 22 | `OfferTests.A_fourth_card_comes_with_luck_and_never_without` | 40.800 | 8.087 | Builds 300 seeded battles for each of two luck settings, drafts each, and checks the fourth-card count and rate. |
| 23 | `StatusWeightTests.An_eighty_percent_stun_lands_as_often` | 40.406 | 22.438 | 600 seeds per chain mode, 3,834 ticks each; compares stun counts, rate, and sampling error. |
| 24 | `EncounterTests.Spikes_come_by_themselves_every_half_minute_or_so_once_there_are_runners` | 39.538 | 15.959 | Simulates a 40-boar ring for 400 seconds and checks the number of charge spikes. |
| 25 | `LootM9ZoneTests.World_tiers_raise_rare_and_legendary_shares_and_item_level` | 39.217 | 16.053 | Rolls loot across four world tiers with tier effects enabled and disabled, then compares rarity shares and item levels. |

## Safe cuts and coverage

- `Tests.csproj` enables compiler optimization for the test assembly, including
  the linked simulation sources. Configuration remains Debug, with portable
  symbols and unchanged `TRACE;DEBUG;NET;NET8_0;NETCOREAPP` constants. The
  measured assembly has `IsJITOptimizerDisabled=false`. The game project is
  unchanged. `dotnet test -p:Optimize=false` remains available for stepping
  through unoptimized test code.
- One reusable `TestContent` fixture supplies the parsed 574-node board to
  `LampBoardTests`, `LampNavTests`, and `LampCardDemoTests`. Construction is
  lazy, preserving the existing data guards. Each class constructs its own
  model once instead of reloading JSON and rebuilding geometry for each use.
  These tests read model geometry; `Hit` mutates only its reusable scratch
  list. Keeping the model inside its class prevents cross-class scratch races.
- Five stationary combat harnesses (`BlockAnswerTests`, `ClockTests`,
  `StatusWeightTests`, `ProcWeightTests`, and `TailWeightTests`) use a 16 m
  collision world instead of 120 m. The value lives in
  `tests/fixtures/suite_speed.json`. Their actors stay near the origin and
  their assertions measure combat, clocks, and proc rates rather than distant
  navigation. The navigation grid shrinks from 14,400 cells to 256 cells.
  The [baseline outputs](suite_speed/round3-stationary-output.json), including
  the strike-distance probe, match all three optimized runs exactly.

All **10,839 original `Assert.` source lines** match the clean integration
control. No assertion, case, skip, threshold, loop length, seed, or stochastic
sample was deleted or weakened. In particular, the ten-minute combat matrix,
220-blow clocks, 192-seed balance paths, and eight crowd rolls remain intact.
No sleep, real-time wait, or retry was added. No test case was added; long
existing cases retain their complete workloads. No game source, art, shader,
layout, story text, player view, animation, or hit-effect change is included.
The earlier branch's draft-fit dependency was removed from this change; the
baseline and all three after runs use integration's own card harness and game
source unchanged.

## Parallelism

No parallelism setting or collection membership changed. Existing classes
already run concurrently by default. There is shared mutable static state:
the Balance collection contains tests that change Lamps versions, development
overrides, and save settings; the PilotFeet collection changes
`Pilot.StepsAndStands`. Both retain their nonparallel collection definitions,
as does the SmoothNormals timing collection. No extra class parallelism is
claimed safe or enabled. The fixture's only static value is the immutable
arena size; mutable board scratch storage stays within its owning class.

## Reproduction and evidence

Run from `godot/tests` in an isolated worktree with the owner's engine and
imported assets available:

```powershell
dotnet test --logger 'trx;LogFileName=run.trx' --logger 'console;verbosity=normal' --results-directory results/suite-speed
```

Time the whole command with a stopwatch and retain its exit code. Repeat the
default full command three times sequentially; no filters or parallelism
overrides were used. From the worktree root, export and compare each result:

```powershell
python tools/suite_speed.py godot/tests/results/suite-speed/run.trx --out docs/team/suite_speed/run.csv --compare godot/tests/results/suite-speed/round3-before.trx
```

The comparison requires an exact multiset of case names/outcomes, the same
successful real-engine card count, and identical stationary diagnostics. It
rejects a card-harness guard pass. Raw TRX, logs, wall clocks, and comparisons
remain in the ignored `godot/tests/results/suite-speed/` directory; the CSVs
and JSON evidence above are committed. Older-base timing artifacts are
superseded by this fresh matched measurement set.
