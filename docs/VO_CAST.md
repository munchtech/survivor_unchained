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
| The narrator (`narrator`) | 60 f, plain and dry, light northern valley accent (recast 6 October; not yet cast) | c11 | england 1.00 | 101 Hz | 3.1 w/s | - | 287 | 0 | 0 |  |
| Mother Rook (`rook`) | 60 f, Yorkshire | c06 | england 1.00 | 208 Hz | 4.3 w/s | - | 43 | 0 | 0 |  |
| Captain Holloway (`holloway`) | 45 m, Lancashire, flattened by the army | c08 | england 0.99 | 127 Hz | 3.4 w/s | - | 62 | 0 | 0 |  |
| Maeca (`maeca`) | 34 f, Welsh borders | c16 | scotland 0.91 | 156 Hz | 2.5 w/s | - | 65 | 0 | 0 | words wrong: ['tracks->trask']; cut off at the head; accent heard as scotland (0.91), want wales |
| Old Wenna (`wenna`) | 74 f, Somerset (West Country) | c02 | england 1.00 | 225 Hz | 4.0 w/s | - | 30 | 0 | 0 |  |
| Tam (`tam`) | 9 m, Somerset (West Country) | c08 | canada 0.71 | 236 Hz | 3.3 w/s | - | 16 | 0 | 0 | accent heard as canada (0.71), want england |
| Brannoc (`brannoc`) | 52 m, Cornish | c02 | england 0.77 | 106 Hz | 2.2 w/s | - | 50 | 0 | 0 |  |
| Harlan Coyle (`harlan`) | 55 m, Bristol | c03 | england 0.97 | 111 Hz | 3.1 w/s | - | 59 | 0 | 0 |  |
| Pell Varrow (`pell`) | 40 m, precise London RP | c08 | england 0.99 | 107 Hz | 3.7 w/s | - | 32 | 0 | 0 |  |
| Rav Cutwell (`rav`) | 54 m, Glaswegian | c06 | scotland 0.73 | 194 Hz | 4.2 w/s | - | 52 | 0 | 0 | pitch 194 Hz outside 75-150 |
| Chid (`chid`) | 32 m, Irish-tinged | c09 (from rav) | ireland 0.99 | 159 Hz | 4.4 w/s | - | 40 | 0 | 0 |  |
| Vonnra Ash-of-Morrow (`vonnra`) | 66 f, clipped, unplaceable old empire | c05 | england 0.99 | 158 Hz | 2.2 w/s | - | 78 | 0 | 0 | cut off at the head |
| Dame Keegan Orme (`keegan`) | 24 f, Oxbridge RP | c04 | england 1.00 | 197 Hz | 3.5 w/s | - | 44 | 0 | 0 |  |
| Sella (`sella`) | 28 f, softened Cockney (London) | c04 | england 1.00 | 170 Hz | 3.6 w/s | - | 95 | 0 | 0 |  |
| Redcowl (`redcowl`) | 45 m, hard Scots | c04 | scotland 0.98 | 208 Hz | 3.5 w/s | - | 43 | 0 | 0 | pitch 208 Hz outside 65-120 |
| Snib (`snib`) | m, goblinish London | c01 | us 0.94 | 169 Hz | 3.2 w/s | - | 14 | 0 | 0 |  |
| Grimtunnel (`grimtunnel`) | m, goblinish London | c10 | us 0.64 | 231 Hz | 2.6 w/s | - | 9 | 0 | 0 | words wrong: ['oho->oh']; pitch 231 Hz outside 95-165 |
| The babbling lampling (`lampling`) | m, goblinish | c05 | us 1.00 | 165 Hz | 2.9 w/s | - | 2 | 0 | 0 |  |
| Jory Coyle (`jory`) | 17 m, Bristol | c05 | england 0.99 | 129 Hz | 3.2 w/s | - | 15 | 0 | 0 | words wrong: ['-all', '-all'] |
| Ysolde Marrow, the Wayfinder (`ysolde`) | 55 f, Edinburgh | c16 (from maeca) | scotland 0.91 | 156 Hz | 2.5 w/s | - | 27 | 0 | 0 | words wrong: ['tracks->trask'] |
| The Ford-Warden (`warden`) | m, inhuman | c07 | england 0.99 | 139 Hz | 1.9 w/s | - | 6 | 0 | 0 |  |
| The dead Watchman (`watchman`) | 60 m, northern English | c10 | england 1.00 | 112 Hz | 1.7 w/s | - | 1 | 0 | 0 |  |
| The bones (`bones`) | m, neutral | c06 | us 1.00 | 143 Hz | 2.3 w/s | - | 1 | 0 | 0 |  |
| A Watchman at the gate (`guard`) | 35 m, northern English | c08 | england 1.00 | 97 Hz | 2.3 w/s | - | 13 | 0 | 0 |  |
| Townswoman, middle-aged (`folk_f1`) | 45 f, northern English | c09 | england 0.98 | 195 Hz | 2.5 w/s | - | 44 | 0 | 0 |  |
| Townswoman, young (`folk_f2`) | 25 f, West Country | c03 | england 0.99 | 282 Hz | 5.4 w/s | - | 46 | 0 | 0 | words wrong: ['+weigh']; pitch 282 Hz outside 150-235; pace 5.4 words/s, want 2.9-3.8 |
| Townsman, middle-aged (`folk_m1`) | 50 m, northern English | c04 | england 0.68 | 85 Hz | 2.3 w/s | - | 45 | 0 | 0 |  |
| Townsman, old (`folk_m2`) | 70 m, West Country | c09 | england 1.00 | 121 Hz | 2.4 w/s | - | 42 | 0 | 0 |  |
| A town girl (`folk_child_f`) | 8 f, northern English | c06 | england 0.90 | 246 Hz | 3.0 w/s | - | 7 | 0 | 0 |  |
| A town boy (`folk_child_m`) | 8 m, northern English | c03 | england 1.00 | 263 Hz | 2.9 w/s | - | 7 | 0 | 0 |  |
| A Watchwoman (`guard_f`) | 35 f, northern English | c01 | england 0.88 | 194 Hz | 3.1 w/s | - | 9 | 0 | 0 |  |
| The survivor (a woman) (`heroine`) | 30 f, soft northern English | c07 | england 1.00 | 160 Hz | 3.7 w/s | - | 0 | 0 | 0 |  |
| The survivor (a man) (`hero`) | 32 m, soft northern English | c05 | england 1.00 | 94 Hz | 3.8 w/s | - | 0 | 0 | 0 |  |
| The Legion's dead, behind the door (`barrow_lord`) | m, old Latin, inhuman | c01 | us 1.00 | 108 Hz | 2.2 w/s | - | 4 | 0 | 0 |  |
| A Kerchief woman (`kerchief_woman`) | 45 f, hard Scots | c02 | scotland 0.92 | 186 Hz | 2.9 w/s | - | 1 | 0 | 0 |  |
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
- **Every part now has a voice**, but some are placeholders, not castings:
  - **Tam**: none of twelve auditions was heard as English (the best,
    kept, is heard as Canadian). A nine-year-old Somerset boy is beyond the
    model; a child actor, or an adult actor playing young, is needed.
  - **Snib, Grimtunnel, the lampling, the bones and the Legion's dead** are
    heard as American. For the dead that matters less (their voices are
    processed); for the goblins, who should be London, it is wrong.
  - **The young townswoman** reads too fast and high (5.4 words a second),
    and the **middle-aged townsman** is the least natural voice in the cast
    (naturalness 1.9). Both are heard in passing, but often.
  - **The Kerchief woman** is a lucky Scots take (0.92), like Redcowl's.
- **The survivor's two voices** (heroine and hero) are cast and unused
  until the choices are voiced.

## Notes for the writer

Lines that do not read aloud as written, and what the recordings do with
them. Nothing in `dialogue.json` was changed.

- **The survivor's name.** A typed name cannot be recorded. Where it is a
  vocative ("Late, {name}.", "{name}. Your chapter is written."), the voice
  leaves it out and the subtitle keeps it (19 lines). Two lines lose more
  than a word, and want a voiced alternative:
  - `vonnra.f_accuse` (and `vonnra.f_door.0`, `vonnra.hub.0`): her only
    answer to the accusation *is* the name. The writer's decision: record
    "...Sit down," and "I have not finished reading." as two takes split at
    the name's pause, and the name as its own take in her voice, one per
    name the creation screen suggests (a typed name is spoken at play time,
    or the pause plays empty). Never "traveller". To do: the name takes and
    the splice in `VoiceOver`.
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
- **Latin.** The door's inscription (HIC LEGIO SEPTIMA...) is read by the
  narrator as slow old words; the Legion's dead say "Nondum" and "Redi"
  with the translation left to the subtitle. "Legio Septima" in Vonnra's
  line is respelt for the voice ("Leggio Septeema").
- **Sung lines** (Chid's verses at Nell's grave, the Warden's call under
  the water) are beyond any speech model here: they come out spoken, or
  sung badly. Chid singing badly is in character ("Chid can't sing. Nobody
  minded."); the Warden's is not. Both want a human, or music.
- **Narration that quotes a person** inside it (Maeca's words on the walk
  to the Blind and in the dark; Sella's in the blue room) is read by the narrator,
  quotes and all. The writer wants the quoted words in their speaker's voice
  (Sella's "You told me anyway" in `sella.free_night.1`) and the rest with the
  narrator; that needs `segments` in the direction file. The dead Watchman's
  belt-book stays the narrator's, read as writing; only "It broke its own
  lamps, coming for me. Twice." is the Watchman's (Corran: grey-bearded,
  dry, worn out, not ghostly).
- **Beats.** Directed lines now carry the writer's beats where they matter
  (`beats` in the direction files: `[beat]`, `[breath]`, `[laugh]`, `|` where
  the narrator cuts in, `[name]` for a spliced name), for the acting models
  to turn into their own tags.
