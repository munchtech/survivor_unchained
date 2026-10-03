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
