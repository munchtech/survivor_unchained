# DraftCardFitTests: native script lifetime

Branch: `codex/draft-card-fit`, based on integration `ede4bf910`.
Status: ready; deterministic regression and ten consecutive full suites passed.

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

## Validation and existing findings

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
