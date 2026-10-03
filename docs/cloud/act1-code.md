# Act 1 code tasks (WRITING_PASS.md section 11)

Branch `claude/cloud-act1-code`, from `claude/vigilant-galileo-l6jqyx`. All
seven items in section 11 are built. Each has its scenario as a test, and
each **[CODE, to do]** mark in `WRITING_PASS.md` now reads **[CODE, done]**.
Only the marks changed in that file. Tests: 238 passed before, 247 pass now
(`cd godot/tests && dotnet test`), StoryLint included.

## C1. The strongbox, found, says whose it is and where to take it

- `godot/logic/Play/Zones/Verge.cs`, `MakeInteractables`, the `strongbox`
  interactable: `Act` gives the box and writes `caravan/strongbox_found` in
  the same `Apply`, which makes the quest active.
- `godot/data/content/quests.json`: `caravan.entries.strongbox_found`, after
  `roost_found`, with the spec's text.
- `godot/logic/World/Objectives.cs`, `Caravan()`: while the box is carried
  and `caravan.cargo` is unset, the main step is "Take the Coyle strongbox to
  Harlan Coyle, at Coyle Trading in the Waystation, or keep it", whatever
  `caravan.survivors` says. "Still in the Roost" still waits until the
  survivors are settled, as it did before.
- Test (K4): `VergeTests.A_strongbox_taken_before_anyone_asked_says_whose_it_is_and_where_it_goes`.
  It runs in the real Verge zone because it needs the interactable.

## C2. The ledger's next step follows what the survivor knows

- `Objectives.cs`: `H.Any(params string[])`. `Caravan()` works out
  `CTX_KERCHIEF` (including `Knows("hint.roost")`) and `CTX_COYLE` exactly as
  the table in section 3 defines them. The three ledger steps replace the old
  single line, in the spec's order. "Someone paid the toll clerk..." stays
  for `clerk_turned` without the ledger.
- `Verge.cs`, `MapMarks()`: the Coyle wagons are `Quest` (gold) when
  `ledger_read` is set and `wreck` is not.
- Tests (K5b): `BreadcrumbTests.The_ledgers_next_step_follows_what_the_survivor_knows`
  for the tracker, and `VergeTests.A_ledger_read_for_its_date_sends_you_to_the_wagons`
  for the map.

## C3. The dead watchman's book opens the lamps

- `godot/logic/Play/Zones/Prologue.cs`, the `watchman` interactable: the
  `Apply` now also writes `lamps/book`, with status active.
- Test (L1): `PrologueTests.The_dead_watchmans_book_opens_the_lamps`.

## C4. The chapter's page

- `godot/logic/World/Chapter.cs`, `Summary`: the open threads are `vault`,
  `below` and `lamps`, with `lamps` shown only while its quest is active.
  `Caravan()` beats now include `roost_told`, `crates_redcowl`,
  `crates_harlan`, `jory_told`, `pell_given` and `pell_hunted`. `Beasts()`
  beats include `redcowl_charge`. `Epithet`: `vonnra.accused` gives
  "{name}, who said it to Vonnra's face", placed straight after "who runs
  with wolves".
- Tests (E2): `BreadcrumbTests.The_chapters_page_keeps_the_lamps_open_and_remembers_who_said_it_to_Vonnra`
  plays the accusation through the fortune and then reads the page.
  `QuestTests.Vonnra_reads_back_what_you_did_and_the_chapter_closes` still
  asserts `vault, below` for a world that never started the lamps, then
  asserts `vault, below, lamps` once `lamps/book` is written.

## C5. The crates in an empty Roost

- `Verge.cs`, `MakeInteractables`, next to the strongbox: `crates_charge`
  ("Take a charge") and `crates_sink` ("Sink them in the stream"), both named
  "The B.E. crates". The shared condition is `CratesLeft()`: Redcowl `dead`
  or `tricked`, or `roost.cleared`; `be.crates` unset; no `burned_roost` in
  the history. The charge also needs `crates.charge_taken` unset. The
  effects and lines are the spec's.
- `quests.json`: `caravan.entries.crates_sunk`, after `crates_harlan`.
  `dialogue.json`: the `f_ember` variant for `be.crates` `sunk`, placed
  before the `clue.blasting_ember` one.
- Tests (K14): `VergeTests.With_the_Kerchiefs_gone_the_six_crates_can_be_robbed_once_or_sunk`
  covers one charge, then sinking, both interactables gone afterwards, and
  neither offered after `burned_roost`.
  `BreadcrumbTests.Crates_sunk_in_the_stream_are_the_one_thing_Vonnra_approves_of_throwing_away`
  covers Harlan's "Your six crates" going away and the fortune line. A
  `sunk` case in `When_the_chapter_closes_the_crates_go_wherever_nobody_stopped_them`
  shows that `crates.settle` leaves `sunk` alone.

## C6. A shop line that becomes true is on the shelf when you next look

- `godot/logic/World/State.cs`, `ShopState.Offered` (`List<string>`, saved
  with the shop).
- `godot/logic/Play/Journey.cs`: on restock, `RollStock` records every
  conditional line whose `when` held, whether or not its chance came up.
  Between restocks, `OpenShop` adds any conditional line that now holds and
  isn't in `Offered`, records it, and rolls its chance once with the same
  `Roll` used at restock. A restock creates a fresh `ShopState`, which
  clears the list.
- `godot/logic/World/Save.cs`, `Migrate`: if a shop's `Offered` is null, it
  becomes an empty list.
- Tests: `BreadcrumbTests.Pells_charge_is_on_the_shelf_as_soon_as_you_know_what_it_is_for`
  (B9) and `SaveTests.A_shop_saved_before_it_kept_its_offered_lines_still_opens`
  (the migration).

## C7. Where you stand with the Kerchiefs (optional, done)

- `godot/logic/World/Standing.cs`: when the Kerchiefs tolerate the survivor
  and `be.crates` is `redcowl`, the reason reads "Redcowl keeps the Coyle
  crates from the Dig, on your word." It is checked straight after the
  colours.
- Test: one more step in `WorldTests.Reads_the_powers_of_the_Verge_from_what_the_world_holds`.
- C7 had no status mark, so there was nothing to flip.

## Judgement calls

- **Where the zone scenarios live.** K4, K14 (the interactables), the K5b
  map check and L1 need a running Verge or prologue. They sit in
  `VergeTests` and `PrologueTests`, which already have that harness, so the
  harness isn't duplicated in `BreadcrumbTests`. The dialogue and world
  halves are in `BreadcrumbTests`.
- **Tracker text.** The two new ledger steps drop the spec's final full stop
  so they match the other tracker lines, which have none. The words are
  unchanged.
- **K5b setup.** The first ledger step only shows while the caravan is
  active. With the ledger alone the quest is not started, and the tracker
  shows nothing. So the test starts from Harlan's plea, which is
  `CTX_COYLE` without `CTX_KERCHIEF`.
- **`crates_sunk` on the chapter page.** C4 lists the crates beats but
  predates C5, so I added `crates_sunk` to the caravan beats alongside
  `crates_redcowl` and `crates_harlan`.
- **C6 and `Offered`.** A line whose `when` held at restock but whose chance
  failed is not re-rolled on later visits. That matches "rolling its chance
  as at restock": once per cycle. Lines are tracked by item id. No shop has
  two conditional lines with the same id today; if one ever does, they
  would share a slot.
- **C5 placement.** The two crate interactables sit at `cargo` (-2.4, +1.2)
  and (-3.4, +3.4), on the other side of the cargo from the strongbox. I
  couldn't look at this in a window, so check it in the Roost: they should
  stand apart from each other and from the strongbox prompt.

## Left open

- The `burned_roost` history is written only when the Roost burns with
  prisoners still caged. If the powder is fired after the cages are opened,
  the camp burns without that history, and C5's crates (and `f_ember`'s
  "still waiting") behave as if they survived. This is existing behaviour
  that the spec's conditions inherit. I didn't change it.
- Section 12 still says "to write" against K4, K5b, K14, L1, B9 and E2. I
  left that text alone so I only changed the marks. The test names above
  can replace it.
