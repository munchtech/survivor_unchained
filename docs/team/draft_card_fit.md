# DraftCardFitTests: native script lifetime

Branch: `codex/draft-card-fit`, based on integration `ede4bf910`.
Status: fix built; focused regression and first full suite green; ten-run validation in progress.

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

Evidence in this worktree: `godot/.shots/draft-card-fit/`, especially
`baseline-13.log`, `baseline-13.trx`, `baseline-13-order.json`,
`lifetime-red.log`, and `lifetime-green.log`.

## Validation and existing findings

- Focused regression: red before the fix, green after it; 1,914 cards, zero fit failures.
- First full suite after the fix: 2,211 passed, 0 failed, 11 skipped.
  Ten consecutive green runs are still in progress.
- Before the fix, full run 2 independently failed `SmoothNormalsTests.SixtyThousandVertsBakeFast`
  at 382 ms. That test and its bound were not changed.
- Existing harness limitation: `Gather` indexes an absent union ingredient evolution,
  logs an exception, and checks only the Warden cards gathered before it. This separate
  coverage defect remains open; the script-lifetime regression still runs and fails
  the process when its check fails.
