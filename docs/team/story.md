# Story and writing: status

Owner of the canon, the words and the story data. Signs off every voice packet
before recording. Agent a54dc034ed29f2e02 (the fifth story lead), branch
`worktree-agent-a54dc034ed29f2e02`. The predecessor's brief is in `docs/handoff/story.md`.

## State (4 October)

- **Canon:** `docs/STORY_BIBLE.md`; `docs/VOICES.md`; `docs/WRITING_PASS.md` §22 is
  the latest: the owner's decisions on the story fights, the clock and the first chart.
- **Done, from the owner's decisions** (all tested, all in data):
  - **Redcowl spared or killed.** At his knee: "Spare him" or "Finish it" (the
    hook, `ArenaSpec.OnSpare`/`EndSpared`/`SpareVerb`, is agreed with combat).
    - Spared: C11's `spared` and `flit` ("the rest of me"; "We're flitting!").
      He strikes the camp by first light, takes the crates only if he swore to
      keep them, and returns in Act 2 owing her.
    - Every later reader knows: Rav's two cups, the morning report, barks,
      concerns, standing, the chapter page, the fortune's crates, and the bible.
    - Greymuzzle has the same choice; "Finish it" breaks the promise.
  - **A lost story fight wakes her on Chid's bench the next morning.**
    - The lost line is the last thing she knows.
    - The waking is a seed for each fight; then Chid's carter lie, the cost
      ("a night"), and a pointer to whoever can help her get ready.
    - Morning reports and barks for each loss.
    - Experience wired it (`WakeAfterLoss` → `CarriedHome` → the shrine → Chid).
  - **The clock's words** are in experience's `Journey.DayLines`: dusk, the
    night's fight, the nudge, the night left alone, the rise, straight on.
  - **The fortune gives the first chart** (`vonnra.f_chart`, "The Lampless
    Howes", priced and waived). It uses a new change, `{ "chart": ... }`. Charts
    are named in the valley's words now.
  - **The rise's words** (combat's): the art "Not Yet" and the blessing "Cold,
    Then Not", with their texts and captions. The art comes from *The Keeper's
    Office*, Chid's book, in Act 2 (bible §7).
- **Checks:** StoryLint, the seed check, the signature phrases and the body's
  hours are clean.
- **Voice is paused:** text-only packet notes are in WRITING_PASS §22.5 and below.

## Key decisions (why)

- **Spared, Redcowl owes her and leaves.** A beaten captain moves his people; a
  debt is how he talks ("Redcowl owes Rav a leg"). He never says the word:
  it is spent dying.
- **The loss's cost is the night, said once by Chid.** It costs no gold,
  wound or things, so it buys a day to get ready rather than punishing her.
  The pointers turn the day into getting ready.
- **She wakes at the shrine, not the inn:** every death's waking is Chid's, with
  his carter lie wearing thin. The narrator never says who carried her.
- **Two names for the one rise:** the ember's "Cold, Then Not" (Chid's line)
  and the Order's "Not Yet". The book's Cs are Chid's hand (Act 3).
- **The chart is the Wayfinder's, margins full:** Vonnra buys from Ysolde too.
- Everything older stands (the handoff's §4).

## Packet notes, text-only (for when voice resumes)

- **Final:** narrator, Rook, Holloway, Brannoc, Sella, Vonnra, Harlan. Vonnra's
  final packet changed: `f_door` .0/.1 shortened; `f_chart` .0/.1 new; `f_ember`
  gained a .0 (the old .0–.6 are .1–.7).
- **Sella's final packet** still needs new takes of `say_calling.2` and
  `bark.sella.night.1`.
- **Read, with notes:**
  - **Chid** wants company, the shrine lit, and this one to stay up. He hides
    that he is Unchained, that he carries her in (the carter is his lie), that
    he is "C.", and that he was at the ford. "…" not "..…" in takes 13 and 14.
    Bark day.1, "I should know.", is said without noticing. Re-take
    `cb_nemesis_slain.0`.
  - **Maeca** wants the Pack cured and let be. She hides Ashford, her
    neighbours in the Kerchiefs, and the boots. Bark said.3, "Listen.", is very
    quiet but not a whisper. Re-take `driving.0`.
  - **Ysolde** wants the maps walked and the margins full. She hides Sallow and
    Edric. "My brother didn't." is her one lie, practised smooth. Re-take
    `places.0`.
- **New lines since:** Chid `carried`, `carried_chid`, `carried_who`; Rav
  `cb_spared_redcowl`, `owes_two`; Redcowl `spared`, `flit`; barks for
  Holloway, Maeca, Rav and Keegan (appended to `said`).
- **Ids shifted** when the explicit slots came out: `sella.night` .1–.3 → .0–.2,
  `sella.free_night` .1–.2 → .0–.1, `maeca.blind` .1–.2 → .0–.1.

## Next

1. **Chid gives *The Keeper's Office*** (`keepers_office`, combat's item) from
   Act 2's first morning and at his waking after a lost Act 2 fight, once the
   item is on the integration branch.
2. **C14, "The Road Back"**, once combat builds it in the story-fight shape:
   `brannoc.road`, the `nell.burial` variant, its won and lost lines, and a RouteTests play.
3. **The result screen's new slots**, when experience sends them.
4. **C01 to C04:** the cinematics lead's line asks.
5. **Act 2's text**, when the owner asks (bible §7; Redcowl spared is planned).

## Blockers

None. No Godot until the main session says the GPU is free.

## For other areas

- **Combat:** the spare fields are yours to call (`Won(j, spec, spared)`). For
  Redcowl, play `.spared` then `.flit`. `chapter.done` is the Act 2 fact.
  Charts are named by `MapOffers.Name`.
- **Experience:** story fights' specs live in `StoryFights.cs`; edit words there.
  Check the waking on Chid's bench in play when Godot is free.
- **Cinematics:** C09's chart beat, C10's choice, C11's spared ending
  (`docs/handoff/cinematics.md`, item 8).
- **UI:** the atlas words are agreed; the chart arrives at the fortune.
