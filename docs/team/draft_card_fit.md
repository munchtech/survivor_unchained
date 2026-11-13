# Draft-card fit flake



Branch: `codex/draft-card-fit`; original reproduction base `ede4bf910`.

Current integration merge: `0b1d2d638853e4c679ac7d68250d379083d6af8b`.

Status: the first full suite passed with 2,516 passed, 0 failed, and 11 skipped; two required suites remain.



## Round 3 validation



Integration still uses Godot.NET.Sdk 4.5.1. Its `OrnateBox`, card harness, and

`DraftCardFitTests` are unchanged from the reproduction base. The merged-code

negative control failed with the script-collection assertion after removing only

the script pin. Restoring the pin passed the same regression and checked 1,914

cards with zero fit failures. Controls: `r3-proof-lifetime-red` and

`r3-proof-lifetime-green`.



The separate union-gather coverage defect is recorded under "Noted by Codex job 6"

in `docs/team/hook/CODEX_audit.md`, with the exact lines, missing coverage, and

how it was found. Its logic is unchanged in this branch.



The interrupted `r3-final-01` run produced no final TRX and is not counted.

On the earlier `5a3a1b2e5` merge, `r3-latest-01` finished with 2,468 passed, 1 failed, and 11 skipped.

Its draft-card check passed with 1,914 cards; the failure was the unchanged

`SmoothNormalsTests.cs:127` wall-clock benchmark at 284 ms against 250 ms.

The failed run remains in the evidence and does not count toward the required

three consecutive green suites.



## Cause and fix



`OrnateBox.Make` creates temporary custom style resources. Godot 4.5.1 can retire

their type's native C# script on the finalizer thread while another instance is

being constructed. Its script cache then returns a null script and aborts.

This matches [Godot issue 109711](https://github.com/godotengine/godot/issues/109711).



`OrnateBox` now retains its type script in its static constructor. Drawing, sizes,

colors, fonts, text, and layout are unchanged. The card harness disposes a frame,

forces collection and finalization outside its helper's stack, and checks that

the script survives. That regression failed before the fix and passes afterward.

No retries, relaxed fit assertions, or test scheduling changes were added.



## Reproduction



The unchanged suite failed on run 13, after runs 3-12 had all passed. Result:

2,210 passed, 1 failed, 11 skipped. `DraftCardFitTests.cs:50` rejected exit

`-1073741795` (`0xC000001D`). Godot reported `script.is_null()` in

`tie_user_managed_to_unmanaged`, called from `OrnateBox.Make` during `DraftPanel.Mark`.



The suite ran in parallel. Immediately before the failure, its completion log

contains the two `FlareStagedTests` for Butcher's Hour and Banked Flame, then

`RecipeTests.Every_branch_is_earned_by_its_passive_and_offered_and_fights` for

`gravecall` / `bone_knights` / `vitality`. The saved TRX and order report retain

the full trace; start estimates use completion timestamps minus test durations.



Evidence is preserved in

`C:/Users/munch/Desktop/survivorsunchained_inputs/scratch_codex_draft_card_fit/`, especially

`baseline-13.log`, `baseline-13.trx`, `baseline-13-order.json`,

`lifetime-red.log`, `lifetime-green.log`, and `validation.json`.

The ten fixed runs' logs, TRX results, card reports, and order reports are there too.



## Original validation and existing findings



- Focused regression: red before the fix, green after it; 1,914 cards, zero fit failures.

- Ten consecutive full suites (`fixed-01` through `fixed-10`) passed on the

  code in `531307d9b`, November 11, 2026, 11:27-13:13 Pacific. Every run had

  2,211 passed, 0 failed, 11 skipped. Each TRX contains real harness output:

  1,914 cards, zero fit failures; the engine's skip guard was not taken.

- Before the fix, full run 2 independently failed `SmoothNormalsTests.SixtyThousandVertsBakeFast`

  at 382 ms. That test and its bound were not changed.

- Existing harness limitation: `Gather` indexes an absent union ingredient evolution,

  logs an exception, and checks only the Warden cards gathered before it. This separate

  coverage defect remains open; the script-lifetime regression still runs and fails

  the process when its check fails. The same gather exception occurs in green baseline

  runs; the reproduced crash additionally aborts while binding `OrnateBox`.
