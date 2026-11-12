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
| 2 | `RestedOpeningTests.No_press_pattern_beats_the_written_wait_or_the_hold(id: "oathblade")` | 203.290 | 400 seeded 60-second Sunder patterns, plus held references; every-step invariant checks. |
| 3 | `RestedOpeningTests.No_press_pattern_beats_the_written_wait_or_the_hold(id: "sunder")` | 142.470 | 400 seeded 60-second Sunder patterns, plus held references; every-step invariant checks. |
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

## Next measurement

Speed cuts and three consecutive full validation runs are pending.
