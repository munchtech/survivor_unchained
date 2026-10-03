# Voice-over casting sheet

Who each voice is, how it was made, and where it stands. The people and how
they talk are `VOICES.md`; the model choice is `VO_RESEARCH.md`; the
pipeline is `tools/vo/README.md`. Every voice here was designed from a text
description by VoxCPM2 (Apache 2.0); none is, or is modelled on, a real
person. The design wording is `tools/vo/cast.json`; the chosen takes are
`tools/vo/refs/`.

The test for every voice is the owner's: does it have soul? A specific
person with a history, regional texture, idiosyncrasy and breath, not a
clean generic fantasy read. Where a voice falls short of that it says so
below, plainly.

<!-- CAST TABLE -->
| Part | Wanted | Cast take | Heard as | Pitch | Pace | Moods | Lines (parts) | Recorded | Failed | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| The narrator (`narrator`) | 55 m, neutral southern English (RP) | c11 | england 1.00 | 101 Hz | 3.1 w/s | - | 292 | 0 | 0 |  |
| Mother Rook (`rook`) | 60 f, Yorkshire | c06 | england 1.00 | 208 Hz | 4.3 w/s | - | 43 | 0 | 0 |  |
| Captain Holloway (`holloway`) | 45 m, Lancashire, flattened by the army | c08 | england 0.99 | 127 Hz | 3.4 w/s | - | 62 | 0 | 0 |  |
| Maeca Barefoot (`maeca`) | 34 f, Welsh borders | c16 | scotland 0.91 | 156 Hz | 2.5 w/s | - | 65 | 0 | 0 | words wrong: ['tracks->trask']; cut off at the head; accent heard as scotland (0.91), want wales |
| Old Wenna (`wenna`) | 74 f, Somerset (West Country) | not cast |  |  |  | - | 30 | 0 | 0 |  |
| Tam (`tam`) | 9 m, Somerset (West Country) | not cast |  |  |  | - | 16 | 0 | 0 |  |
| Brannoc (`brannoc`) | 52 m, Cornish | c02 | england 0.77 | 106 Hz | 2.2 w/s | - | 48 | 0 | 0 |  |
| Harlan Coyle (`harlan`) | 55 m, Bristol | not cast |  |  |  | - | 59 | 0 | 0 |  |
| Pell Varrow (`pell`) | 40 m, precise London RP | not cast |  |  |  | - | 32 | 0 | 0 |  |
| Rav Cutwell (`rav`) | 54 m, Glaswegian | c06 | scotland 0.73 | 194 Hz | 4.2 w/s | - | 52 | 0 | 0 | pitch 194 Hz outside 75-150 |
| Chid (`chid`) | 32 m, Irish-tinged | c06 | us 1.00 | 237 Hz | 4.1 w/s | - | 38 | 0 | 0 | pitch 237 Hz outside 75-150; accent heard as us (1.00), want ireland |
| Vonnra Ash-of-Morrow (`vonnra`) | 66 f, clipped, unplaceable old empire | c05 | england 0.99 | 158 Hz | 2.2 w/s | - | 78 | 0 | 0 | cut off at the head |
| Dame Keegan Orme (`keegan`) | 24 f, Oxbridge RP | not cast |  |  |  | - | 44 | 0 | 0 |  |
| Sella (`sella`) | 28 f, softened Cockney (London) | c04 | england 1.00 | 170 Hz | 3.6 w/s | - | 95 | 0 | 0 |  |
| Redcowl (`redcowl`) | 45 m, hard Scots | c04 | scotland 0.98 | 208 Hz | 3.5 w/s | - | 38 | 0 | 0 | pitch 208 Hz outside 65-120 |
| Snib (`snib`) | m, goblinish London | not cast |  |  |  | - | 14 | 0 | 0 |  |
| Grimtunnel (`grimtunnel`) | m, goblinish London | not cast |  |  |  | - | 2 | 0 | 0 |  |
| The babbling lampling (`lampling`) | m, goblinish | not cast |  |  |  | - | 2 | 0 | 0 |  |
| Jory Coyle (`jory`) | 17 m, Bristol | not cast |  |  |  | - | 14 | 0 | 0 |  |
| Ysolde Marrow, the Wayfinder (`ysolde`) | 55 f, Edinburgh | c10 | england 0.96 | 204 Hz | 3.2 w/s | - | 27 | 0 | 0 | cut off at the head; accent heard as england (0.96), want scotland |
| The Ford-Warden (`warden`) | m, inhuman | not cast |  |  |  | - | 2 | 0 | 0 |  |
| The dead Watchman (`watchman`) | 60 m, northern English | not cast |  |  |  | - | 0 | 0 | 0 |  |
| The bones (`bones`) | m, neutral | not cast |  |  |  | - | 0 | 0 | 0 |  |
| A Watchman at the gate (`guard`) | 35 m, northern English | not cast |  |  |  | - | 12 | 0 | 0 |  |
| Townswoman, middle-aged (`folk_f1`) | 45 f, northern English | not cast |  |  |  | - | 44 | 0 | 0 |  |
| Townswoman, young (`folk_f2`) | 25 f, West Country | not cast |  |  |  | - | 46 | 0 | 0 |  |
| Townsman, middle-aged (`folk_m1`) | 50 m, northern English | not cast |  |  |  | - | 45 | 0 | 0 |  |
| Townsman, old (`folk_m2`) | 70 m, West Country | not cast |  |  |  | - | 42 | 0 | 0 |  |
| A town girl (`folk_child_f`) | 8 f, northern English | not cast |  |  |  | - | 7 | 0 | 0 |  |
| A town boy (`folk_child_m`) | 8 m, northern English | not cast |  |  |  | - | 7 | 0 | 0 |  |
| A Watchwoman (`guard_f`) | 35 f, northern English | not cast |  |  |  | - | 9 | 0 | 0 |  |
| The survivor (a woman) (`heroine`) | 30 f, soft northern English | not cast |  |  |  | - | 0 | 0 | 0 |  |
| The survivor (a man) (`hero`) | 32 m, soft northern English | not cast |  |  |  | - | 0 | 0 | 0 |  |
<!-- /CAST TABLE -->

## Where the cast stands

- **Accents.** Every English part is heard as England by the accent model
  (Kokoro's stock British voices, a known reference, are heard the same
  way; its American voices as US, so the ear can be trusted). Whether a
  voice is specifically Yorkshire rather than Somerset, the ear cannot say,
  and VoxCPM2 most likely gives a general British accent with some
  regional colour, not a true Yorkshire or Cornish one.
- **Scots, Irish and Welsh cannot be cast locally.** Rav, Redcowl and
  Ysolde (Scots), Chid (Irish), Maeca (Welsh) and the Kerchief woman were
  auditioned 24 times each, and other wordings and models tried
  (`VO_RESEARCH.md`). A few takes are heard as Scots (Redcowl's chosen one,
  0.99; one of Maeca's, 0.91, which suits Ysolde better than Maeca) and one
  of Rav's auditions as Irish (0.99, a man of about thirty: a candidate for
  Chid). These are accidents of the seed, not control: the lines spoken
  from them may drift back to English. These six parts are where a human
  performer (or a paid generator) is most needed.
- **Pace.** VoxCPM2's designed voices read quickly (3 to 4.5 words a
  second); Vonnra's chosen take is the slowest (2.2) and Brannoc's (2.3),
  as they should be.
- **Brannoc** is the weakest English casting (naturalness 2.1, England
  0.77) and the most important to get right after Vonnra; his grief scenes
  are the game's heart.

## Notes for the writer

Lines that do not read aloud as written, and what the recordings do with
them. Nothing in `dialogue.json` was changed.

- **The survivor's name.** A typed name cannot be recorded. Where it is a
  vocative ("Late, {name}.", "{name}. Your chapter is written."), the voice
  leaves it out and the subtitle keeps it (19 lines). Two lines lose more
  than a word, and want a voiced alternative:
  - `vonnra.f_accuse`: her only answer to the accusation *is* the name.
    Recorded as "...Sit down. I have not finished reading.", the moment
    survives only on screen. Suggest a voiced form that does the same work
    without the name, or keep this line unvoiced and let the silence play.
  - `wayfinder.margin_name`: "{name}." is the act of writing it down; the
    voice starts at the narrator's aside.
- **Lines with a number from the world** ({day}, {gold}, {fact:...}) are
  not recorded; none in Act 1 at present.
- **The notice board** is read, not heard: unvoiced.
- **The `[explicit scene: ...]` slots** are unvoiced until written.
- **The survivor's replies** (choices) are not voiced in this pass; the
  heroine's and hero's voices are cast for when they are. Some choices are
  actions ("Kneel, and hold out an empty hand.") and should stay unvoiced
  when the rest are; a `voiced: false` flag on those choices would make
  that explicit.
- **Capitals for stress** ("I SAID it was wolves", "It WORKS") are
  recorded as stressed words, not spelt; the notice board's capitals are
  not read.
- **Quotations inside narration** go to their speaker where the speaker is
  there: the dead watchman's "Make it charge", the bones' "It was never
  locked from the outside", Jory's "Is my uncle—?". The watchman's belt-book
  is read by the narrator as written words.
- **"M. + J."** on the well is read "M and J".
