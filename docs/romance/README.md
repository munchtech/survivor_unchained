# Romance drafts

Drafts of the game's five romances (Sella, Maeca, Keegan, Rav and Ysolde)
for the main author to take into the game or leave out. Nothing here changes
the game: no content JSON, code or existing doc has been edited.

> **Status (round three of the cinematics edit).** Adopted. The Act 1 data for
> Sella, Maeca, Keegan and Rav is now in `godot/data/content/dialogue.json`,
> merged node by node (these drafts predate later live work, so do not drop
> them in whole again), with fixes: the body's hours are cold as the river
> all night and warm by breakfast, for every survivor (`STORY_BIBLE.md`
> section 1); no real-world oaths or quotations; Rav's count is seven. The
> scene files below are corrected to match and remain the Act 2 writer's
> source. `vonnra.f_past` now reads `sella.past_sold`.

## What's here, and the reading order

1. **`ARCS.md`**: start here. §0 sets out how love works in this valley
   (trust grows from what the survivor does, reveals and keeps back; each
   lover notices something about the survivor's body; every scene is chosen
   twice; the tones). §1–5 cover one person each: who they are in love, how
   trust and affection grow (with numbers), the beats in a table with gates
   and facts, how the player bends it (the scene's tone, refusals,
   heartbreak, the intrigue it carries), what it costs act by act, and the
   ends. §6 is how the arcs meet, §7 the full new-fact ledger, and §8 the
   calls the main author needs to make.
2. **`scenes/`**: every beat as playable script, in the game's voices. The
   notation is at the top of `sella.md`.
   - `sella.md`: Act 1 in full (the lead-in to the paid night, the rest
     night, the mornings, the bolt, the free night and its morning, her
     refusal after the Roost); Act 2 (the fortune's bill, "What are you?",
     the man with silver cuffs, the lie, the south road, the eve); the Act 3
     stair; epilogue lines.
   - `maeca.md`: Act 1 in full (the walk to the Blind, watch-only, her
     refusal with wolf blood on you, the first night, her feet, her
     question and your heart); Act 2 (the boots in every variant, the
     gate, Greymuzzle's death and the grieving night, "what you are", the
     eve); epilogue lines.
   - `keegan.md`: Act 1's supper on the wall; Act 2 (the question, chapter
     four read aloud, the line in the dust, the night on the north road,
     the armour going back on, Silverstair's oath, the eve); Act 3 outline.
   - `rav.md`: Act 1's back room and "came back"; Act 2 (the little bird,
     the pulse, the night, the one "no" to a drink, the red hat, the
     hanging, the eve).
   - `ysolde.md`: Act 2 only, as the bible requires (the confession, the
     twelfth drawing, the night, the margin rewritten, the eve, the
     leaving).
3. **`data/`**: data-ready drafts of every Act 1 beat, as **whole
   conversations** (`sella`, `maeca`, `keegan`, `rav`), built from the live
   `dialogue.json` with the changes applied. To try one, replace the same
   key in `dialogue.json` with the file's. Every existing line and node is
   kept. `check.py` reads the game's content with the drafts swapped in, the
   way `godot/tests/StoryLint.cs` does (reachability, explicit slots behind
   the setting with a cut-away, facts read but never written, unknown keys),
   and passes: `python3 docs/romance/data/check.py`. It is not a substitute
   for `dotnet test`, which this session could not run (no .NET here).

## The love scenes and the explicit slots

> **Superseded, 4 October.** The base game is not explicit (the legal lead,
> `docs/legal/LEGAL_BRIEF.md` issue 6; the bible, "Intimate scenes: fade to
> black"). No `[explicit scene: ...]` slot goes into the game's data. When
> these drafts are taken into `dialogue.json`, drop every slot and keep the
> cut-away. `StoryLint` fails if one lands. The beat sheets stay here as notes.

Every love scene has a full lead-in with a last place to stop, a cut-away
moment (sensual, close, ending before the act), and a full aftermath, where
the arc moves. Each also has an `[explicit scene: ...]` slot behind
`settings.intimacy == "full"` and, in the scene file, a **beat sheet** for
the owner's writer: mood and pacing, what each wants and fears, consent on
the page, the emotional turn, callbacks, sex variants, and the line or image
it ends on. The slots hold placeholders only; no explicit prose is written
here.

| Slot | Node | Status |
|---|---|---|
| 1 | `sella.night` | bible's; beat sheet in `scenes/sella.md` |
| 2 | `maeca.blind` | bible's; beat sheet in `scenes/maeca.md` |
| 3 | `sella.free_night` | bible's; beat sheet in `scenes/sella.md` |
| 4 | `keegan.night` | **new**, Act 2 |
| 5 | `rav.night` | **new**, Act 2 |
| 6 | `wayfinder.night` | **new**, Act 2 |
| — | `*.eve_night`, `maeca.blind_grief_night` | tone variants of each person's slot, each with its own placeholder and a short beat sheet |

## New facts and systems

The full list, with writers and readers, is `ARCS.md` §7. In short:

**Act 1 (in the data drafts):** `sella.told_knowing`, `sella.felt_cold`,
`sella.cold_sold`, `sella.past_sold`, `sella.free_declined`,
`maeca.blind_nights`, `maeca.heard_past`, `maeca.heard_heart`,
`keegan.supper`, `rav.back_room`, `rav.came_back`, and npc once-flags
(`say:door`, `say:feet`, `say:asked`, `cb:knelt`, `say:sella`, `say:keegan`,
`say:rav`, `say:cold_bath`, `say:rest`, `came_back`).

**Act 2 and 3 (for the Act 2 writer):** `survivor.knows_risen`,
`sella.confronted`, `sella.asked_what`, `sella.sold_sallow`, `sella.lied`,
`sella.lie`, `sella.fate`, `kiln.lit`, `kiln.known`,
`boots.known_by_survivor`, `maeca.boots`, `maeca.boots_hid`, `maeca.fate`,
`keegan.asked`, `keegan.ch4_read`, `keegan.route`, `keegan.lover`,
`keegan.oath`, `rav.bird`, `rav.felt_pulse`, `rav.lover`, `rav.hat`,
`wayfinder.confessed`, `wayfinder.forgiven`, `wayfinder.double`,
`wayfinder.lover`, `wayfinder.fate`, `edric.freed`, `romance.eve`.

**Systems:**
- **The eve** (`romance.eve`): one night, chosen among the open romances, at
  Act 2 beat 12. A hook in the war beat.
- **One bed a night** (`night.spent`, cleared at dawn): optional; left out
  of the data until something clears it.
- **Asking about a condition** (`{"condition":"wounded"}`): optional; only
  Rav's back-room variant needs it.
- **The settings fact** `settings.intimacy`: the lead's, as before.

**Changes to existing data** (all in the drafts):
- `sella.free` needs trust ≥ 15 as well as three nights and affection ≥ 25,
  so the bolt can't be bought.
- `sella.night` no longer takes the money; `sella.stairs` (the new lead-in)
  does. The cut-away no longer retells the stairs.
- `sella.past` sets `sella.past_sold` only before the free night. **One
  change outside the drafts is needed for that to matter:** `vonnra.f_past`
  should read `sella.past_sold` instead of `sella.heard_past` (four
  variants, one word each).
- `maeca.invite` is not offered to a survivor wearing wolf pelts; the Blind
  refuses wolf blood (`wolf.blood > 0`) with a line rather than silently.
- `maeca.blind` gives the big affection and trust only on the first night
  (+5 affection after), and counts nights.
- `maeca.cb_burned_roost` now costs respect −15.

**Where the data differs in shape from the scene files** (the game applies
a node's effects before choosing its text, so a fact a node sets can't also
pick that node's line):
- Sella's `felt_cold` is set by the morning's choices, not the morning node.
- Sella's lead-in is four nodes (`stairs`, `stairs_say`, `stairs_room`,
  `stairs_rules`), and the roost refusal is a second "Lead the way" choice
  on `price`.
- Maeca's second and third nights are one node, `blind_dark`, whose text
  and choices follow `maeca.blind_nights`, in place of `blind2`/`blind3`.
- The Sella draft reads `keegan.supper` and `rav.back_room`, so ship it with
  the Keegan and Rav drafts, or drop `say_keegan` and `say_rav`.

## A note for the main author

Every arc is built on the bible rather than beside it. Romance carries the
intrigue (§11): each one moves a main thread.
- **Sella** carries Vonnra's bought sight (§6 seeds; the fortune quotes the
  pillow talk), Act 2 beat 9's lie and beat 8's south road. Her drowning at
  the Kiln Ford can be prevented by a lover who knows, which gives the
  "second Unchained" a face.
- **Maeca** carries the boots (§7.4). The romance decides which of her three
  ends she reaches: a survivor who tells her straight away, and is trusted,
  turns a killing into a held gate.
- **Keegan** carries chapter four (§7.2) as the tragedy the bible names.
  Silverstair's offer of confirmation is the point of the arc.
- **Rav** carries the tip-off and the hat (§7.7).
- **Ysolde** carries Sallow's ledger (§7.10), and the route never opens while
  she is selling the survivor.

The one thing this adds to the bible's design is the **body**. Every lover
notices, in their own trade's words, that the survivor runs hot at night
and goes cold or slow at dawn. None of them can say what it means in Act 1,
and each pays off at Act 2's turn. Nothing is said out loud before its act
(bible §3).

Three voice rules are in play, and §8 of `ARCS.md` names them. Rav's "never
says no to a drink" has no exception yet; the drafts propose spending it on
his morning after. Maeca says "Ashford" only in three words or fewer. Keegan
keeps her contractions back except with the survivor. Rav's "Dunstan" is
already spent and is not used again.

Everyone is an adult and the text says so: Sella is twenty-nine, Keegan
twenty-six, Rav fifty-three, Ysolde fifty-four, and Maeca a grown soldier of
a garrison that fell ten years ago. Every intimate moment can be stopped by
either person, and several scenes are written so that the other person
stops it. Sella's paid nights are on her terms (she sets the rules aloud,
and she can refuse and give the money back), and her free night is her own
choice, made twice.
