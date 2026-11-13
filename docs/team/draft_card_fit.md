# Draft-card fit flake

Branch: `codex/draft-card-fit`.
Merged integration: `0b1d2d638853e4c679ac7d68250d379083d6af8b`.
Validated merge commit: `3aaf621da3a8dd08785aa7852693a8cc7e95b51f`.

## Current validation

Three consecutive full `dotnet test` runs passed on the merged code, with
2,516 passed, 0 failed, and 11 skipped each. Times below are Pacific,
November 13, 2026. Every TRX contains real engine output; the missing-engine
guard was not taken. The three runs retained identical source hashes for
`Ornate.cs`, `CardFit.cs`, and `DraftCardFitTests.cs`.

| Full run | Start | End | Passed | Failed | Skipped | Cards checked |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| r3-proof-01 | 04:57:59 | 05:17:50 | 2,516 | 0 | 11 | 1,914 |
| r3-proof-02 | 05:17:57 | 05:52:04 | 2,516 | 0 | 11 | 1,914 |
| r3-proof-03 | 05:52:15 | 06:08:13 | 2,516 | 0 | 11 | 1,914 |

Integration still uses Godot.NET.Sdk 4.5.1. Upstream has not changed `OrnateBox`,
the card harness, or `DraftCardFitTests` since the reproduction base. On this
merged code, removing only the script pin made the GC regression fail with
"OrnateBox's C# script was collected between frame instances." Restoring the
pin passed the regression and checked 1,914 cards with zero fit failures.
Those controls are `r3-proof-lifetime-red` and `r3-proof-lifetime-green`.

## Cause and fix

Godot 4.5.1 can retire the last temporary `OrnateBox` instance's native C# type
script on the finalizer thread while another instance is being constructed.
Its type cache then supplies a dying or null script and aborts. This matches
[Godot issue 109711](https://github.com/godotengine/godot/issues/109711).

`OrnateBox` retains its type script in its static constructor. The temporary
frame used to obtain it is disposed. The harness releases a frame in a helper
that cannot be inlined, forces collection and finalization, and checks that
the script survives. Drawing, sizes, colors, fonts, text, and layout are
unchanged. No retries, relaxed fit assertions, or scheduling changes were added.

## Original reproduction

The unchanged full suite failed on baseline run 13 at `ede4bf910`, after
runs 3-12 had passed: 2,210 passed, 1 failed, 11 skipped.
`DraftCardFitTests.cs:50` rejected exit `-1073741795` (`0xC000001D`). Godot
reported `script.is_null()` in `tie_user_managed_to_unmanaged`, reached through
`OrnateBox.Make` during `DraftPanel.Mark`.

Immediately before that failure, the parallel suite's completion log shows
the two `FlareStagedTests` for Butcher's Hour and Banked Flame, then
`RecipeTests.Every_branch_is_earned_by_its_passive_and_offered_and_fights` for
`gravecall` / `bone_knights` / `vitality`. `baseline-13-order.json` retains the
approximate order derived from completion timestamps minus test durations;
the log and TRX retain the full trace.

The original fix also passed ten consecutive full suites on November 11 at
`531307d9b`, each with 2,211 passed, 0 failed, and 11 skipped. Those historical
counts are separate from the current integration results above.

## Existing findings and evidence

The union-gather coverage defect is recorded under
[Noted by Codex job 6](hook/CODEX_audit.md#noted-by-codex-job-6), including
`CardFit.cs:301-302`, the missing coverage, and how it was found. Only the
1,914 Warden cards gathered before the exception are checked. That defect
remains open and is not fixed in this branch.

An earlier full run, `r3-latest-01` on `5a3a1b2e5`, finished with 2,468 passed,
1 failed, and 11 skipped. Its draft-card check passed; the unchanged
`SmoothNormalsTests.cs:127` wall-clock benchmark failed at 284 ms against
250 ms. Shared CPU usage was 82-94% immediately after completion. That timing
test remains unchanged. The interrupted `r3-final-01` run on `ca64d558b`
produced no final TRX. Neither run counts toward the three green runs above.

Current logs, TRX results, card reports, order reports, GC controls, and
`r3-proof-validation.json` are preserved in
`C:/Users/munch/Desktop/survivorsunchained_inputs/scratch_codex_draft_card_fit/round3/`.
Original reproduction and ten-run evidence are in its parent directory.
