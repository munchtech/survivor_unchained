# Story and writing: status

Owner of the canon, the words and the story data. Signs off every voice packet
before recording. Agent a7ba8903f4c8261b1 (the sixth story lead), branch
`worktree-agent-a7ba8903f4c8261b1`. A fresh successor starts from
`docs/handoff/story.md`.

## State (4 October)

- **Canon:** `docs/STORY_BIBLE.md`; `docs/VOICES.md`; `docs/WRITING_PASS.md`
  §22 (the owner's story-fight decisions) and §23 (the three fights' words).
- **Done this session:**
  - **Chid gives *The Keeper's Office*** (`keepers_office`, which teaches the
    art Not Yet), once:
    - on Act 2's first morning (`chid.office`, the shrine marked "!" until
      he has), with "What's at the end?" ("Somebody answering.") and "Who
      wrote it?" ("Nobody makes a C like that any more.");
    - or at his waking after a lost fight, if she went out before he could
      (a first variant of `carried_chid`: "Read it before you go out again.
      Please."). Tested both ways.
  - **The Roost, the Dig and the Door, every word, slot by slot**
    (WRITING_PASS §23), for combat to paste as it builds them in the
    Hollow's shape:
    - the sights between stages, read against the world (the cages empty or
      full, the pump running or not, the crates fired);
    - the signs, goals, announcements, labels, re-entries, weaknesses and the
      soft and hard words;
    - Snib's commentary, Grimtunnel's lamp trap, the levy's step, the Legion's
      orders, and Redcowl's knee.
  - **The Door's ends rewritten for its place** (she fights at the stair's
    head and never goes down it). Won: "At the door, yours are the only
    bootprints coming out." Lost: the moon going by over the broken roof.
  - **A false line fixed:** a boss growing wild no longer promises "the
    horde comes back" in a map or a story night, where it doesn't. Greymuzzle
    has his own soft and hard words.
  - **StoryLint holds the fights' rules over their code:** no "Ashford", no
    finished "surface-meat" from Grimtunnel, no genre word, no clock in a pull.
- **Checks:** StoryLint, the seed check, the signature phrases and the body's
  hours are clean.

## Key decisions (why)

- **The book is given once, by Chid, whichever way she comes to him.** It is
  the only way she gets up in Act 2 besides a legendary blessing, so it must
  not be missable. "Not now" at the morning and "Please" at the waking show
  his fear without his saying it.
- **"Somebody answering" plants the rise.** The art's text is "something
  answers for you: not yet"; Chid's want is company. The Ford-Warden's "Is it
  morning?" is the question.
- **"All Downstairs", not "The Fall",** for Grimtunnel's end here: in a story
  night "a fall" is hers.
- **The Legion's orders are never translated in a bark or a label.** What
  follows shows what they mean; only C13's subtitles translate, for a reader.
- **Snib speaks only while he lives,** and gets the last word, as the bible
  says, with his gag: "Snib is not going down there. ...Snib is going down
  there."
- Everything older stands (the handoff's §4).

## Packet notes, text-only (voice is paused)

- **Final:** narrator, Rook, Holloway, Brannoc, Sella, Vonnra, Harlan.
  Vonnra's final packet changed: `f_door` .0/.1 shortened; `f_chart` .0/.1
  new; `f_ember` gained a .0 (the old .0–.6 are .1–.7).
- **Sella** still needs new takes of `say_calling.2` and `bark.sella.night.1`.
- **Read, with notes:**
  - **Chid** wants company, the shrine lit, and this one to stay up. He hides
    that he is Unchained, that he carries her in, that he is "C.", and that he
    was at the ford. "…" not "..…" in takes 13 and 14. Bark day.1 is said
    without noticing. Re-take `cb_nemesis_slain.0`. **New:** `office` (the
    book "held the way you hold a bird"; "Not now. It reads better in the
    dark." is gentle, a little too quick), `office_end` ("Somebody answering."
    is the plainest thing in it), `office_who` (said without noticing: it is
    his own line about the note). **`carried_chid` has a new .0** ("Please."
    is the only time he asks her for anything), so its old .0–.8 are .1–.9.
  - **Maeca** wants the Pack cured and let be. She hides Ashford, her
    neighbours in the Kerchiefs, and the boots. Bark said.3, "Listen.", is
    very quiet but not a whisper. Re-take `driving.0`.
  - **Ysolde** wants the maps walked and the margins full. She hides Sallow
    and Edric. "My brother didn't." is her one lie, practised smooth. Re-take
    `places.0`.
- **New since the last packets:** Chid `carried`, `carried_chid`,
  `carried_who`, `office`, `office_end`, `office_who`; Rav
  `cb_spared_redcowl`, `owes_two`; Redcowl `spared`, `flit`; barks for
  Holloway, Maeca, Rav and Keegan (appended to `said`).
- **For the fights, once built** (WRITING_PASS §21 and §23.5): Firepot Nan,
  the Pike-Captain, a Kerchief's "DOWN!", Snib's ten, Grimtunnel's five, and
  the Barrow Lord's three orders in C13's dry whisper.
- **Ids shifted** when the explicit slots came out: `sella.night` .1–.3 →
  .0–.2, `sella.free_night` .1–.2 → .0–.1, `maeca.blind` .1–.2 → .0–.1.

## Next

1. **Review the fights' words in place** as combat builds the Roost, the Dig
   and the Door; answer combat's asks.
2. **C14, "The Road Back"**, once combat builds it in the story-fight shape:
   `brannoc.road`, the `nell.burial` variant, its won and lost lines, and a
   RouteTests play.
3. **See it as the player does** (the GPU is free): Chid's gift and the
   waking on his bench, the Hollow's lines between stages, the spared
   ending's result line, the fortune's chart.
4. **The result screen's new slots**, when experience sends them; **C01 to
   C04**, the cinematics lead's line asks.
5. **Act 2's text**, when the owner asks (bible §7).

## Blockers

None.

## For other areas

- **Combat (`afe45df4957917614`):** WRITING_PASS §23 has every word for the
  Roost, the Dig and the Door, keyed to the Hollow's slots. Some sights read
  the world (`Between` by `caravan.survivors`, `dig.pump` and the crates).
  `SoftWords`/`HardSub` are virtual on `ArenaBoss` now; give each story boss
  its row. StoryLint now reads the fights' code. *The Keeper's Office* is
  wired (`chid.office`).
- **Experience:** the Door's `EndWon`/`EndLost` in `StoryFights.cs` are
  rewritten for the hall (words only).
- **Cinematics:** C13's shot 3 says the way out is "at the head of the
  stair"; in the place she leaves back down the hall to the door (§23.3).
- **Voice:** paused; notes above.
