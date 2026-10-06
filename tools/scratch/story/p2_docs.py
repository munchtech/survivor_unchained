import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from sub import sub

V = "../docs/VOICES.md"
sub(V, """- The player's lines are short, plain and a little dry. They never make a
  speech.""", """- The player's lines are short, plain and a little dry. They never make a
  speech.
- The game is written for adults. Swearing, crude jokes and frank talk
  about sex belong to the mouths below that have them (Rav, Sella,
  Redcowl, the Flagon's regulars, the Watch on a bad night); Holloway
  swears rarely and it lands; Vonnra, Keegan, Chid and Tam never do.
  Violence is said in one plain line, where it lands, and not dwelt on.
  Intimate scenes are written in full before and after, with a cut-away
  for the moment itself and an `[explicit scene: ...]` slot for the
  owner's writer (`STORY_BIBLE.md`).""")

B = "../docs/STORY_BIBLE.md"
sub(B, """| 2 | `maeca.blind` | Maeca and the survivor, the Hunters' Blind in the Verge at night; wordless, wary, careful hands that become sure ones, frost outside, the Pack far off. |""",
    """| 2 | `maeca.blind` | Maeca and the survivor, the Hunters' Blind in the Verge at night; wordless, wary, careful hands that become sure ones, frost outside, the Pack far off. |
| 3 | `sella.free_night` | Sella and the survivor, the blue room, not for money for the first time; slower and less sure than her working nights, the patter dropping away; a door she bolts herself. |""")
sub(B, """  say upstairs reaches Vonnra (chapter two). *Reacts:* `sella.say_maeca`
  (when Maeca is your lover), `sella.say_woman`.""", """  say upstairs reaches Vonnra (chapter two). *Reacts:* `sella.say_maeca`
  (when Maeca is your lover), `sella.say_woman`. *Off the clock:* after three
  paid nights and enough warmth, one night she will not take the money
  (`sella.free`, `sella.free_night`), and in the morning warns you not to tell
  her anything you would not want Vonnra to hear. Fact: `sella.free`.""")
sub(B, """**Harlan, Pell and the crates**""", """**The ember's price**
- `Prologue.cs` dawn: the survivor reaches for their mother's face and it is
  not quite where they left it. `chid.names` (day three): "It always takes
  the names first. Then the faces." Chapter two should make this a cost
  the player chooses to pay (each night's ember a little more of the past).

**Vonnra's coin**
- `vonnra.coin`: an old-empire square coin she has never spent, that "will
  buy something that cannot be bought twice" (the survivor, in chapter
  three). Matches `brannoc.irons`' square coin. `vonnra.risen`: "you will
  find out who holds the note." `vonnra.hub` at night: she looks south to the
  ford.

**Harlan, Pell and the crates**""")
sub(B, """- `harlan.cb_sold_dig`: "I've sold worse, to worse.\"""", """- `harlan.cb_sold_dig`: "I've sold worse, to worse."
- `harlan.jory_now`: he told Jory the crates held salt. "He always believes me."
- `harlan.t_harlan`: Jory's mother (Harlan's sister) went with the fever year:
  the Coyle Company sells ember to the thing that killed her.
- `pell.t_pell`: Pell's sister kept the books in Ashford.""")
sub(B, """- `survivor.first`: "Grimtunnel brought it a heart.\"""", """- `survivor.first`: "Grimtunnel brought it a heart." `survivor.what`: Kell's
  lamp came back up on its own, still lit.
- `snib.pipelads`: the Dig's pipe-lads go blind, then deaf, then into the
  warm slurry. Grimtunnel's faith is paid for by his own.
- `rules.json` `jory.nights`: Ewan, the fourth cage, who did not last.
- `wayfinder.t_wayfinder`: her brother did not come out of a barrow in the
  Morrow hills; she draws it still.""")
sub(B, """History events
added: `farm_saved`, `broke_promise`, `bribed_snib`.""", """History events
added: `farm_saved`, `broke_promise`, `bribed_snib`. Second pass:
`aldo.buried`, `caravan.bodies` (each set a day after its death, for the
next morning's report), `sella.free`; per-person `t_<npc>` once-flags for
each character's one question about themselves.""")
print("docs ok")
