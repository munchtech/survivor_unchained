# Recording the voices in ElevenLabs

The final voices are recorded by the owner in ElevenLabs, one character at a
time, from these packets. Until a character is done, every line plays a local
placeholder (Maya1's performance turned into the cast voice by Seed-VC,
`tools/vo/placeholders.py`), marked as a placeholder in the game's index so
the final replaces it cleanly.

## One character, start to finish

1. **Wait for the story lead's sign-off.** Each packet is a draft until the
   story lead (agent a7622ae77d19e31dc) has checked every line and marked it
   final. Lines marked HOLD wait for an edit still under review.
2. **Cast the voice** (the packet's "Casting the voice"): Voice Design with
   the brief and the preview text, saved as `SU <name>`. Or pick from the
   Voice Library, if its licence allows commercial use. Never a real person.
3. **Record each line** in the packet's order with **Eleven v4**, at the
   packet's settings:
   - paste the text block (the square brackets are audio tags: acted, not
     spoken);
   - regenerate until the read matches the direction;
   - download the take and save it under the exact file name given, all into
     one folder (e.g. `~/Downloads/su_vo/`).

   The words must be the subtitle's, and the importer checks them.
4. **Bring them in:**

   ```sh
   python tools/vo/import_takes.py ~/Downloads/su_vo --voice <voice>
   ```

   For each take it:
   - matches the take to its line (and to its part, where a line is shared
     with the narrator);
   - checks the words with Whisper;
   - trims, de-clicks, places the take in its scene's room and levels it;
   - writes it into the game, replacing the placeholder.

   It then reports what it refused and why, and what that character still
   has to record. `--dry-run` shows the report only, and `--force` keeps a
   take whose words differ from the subtitle (for a deliberate
   change; tell the story lead).
5. **Listen in the game**, and send the next character's name to the voice
   agent.

The same files can be imported again at any time: a newer take of a line
replaces the older one.

## Order

By how much each voice is heard, and where the player meets it first:

1. **The narrator** ([packet](narrator.md)): the cinematic opening is his,
   and he is the most-heard voice in the game. Start with his first section
   (the Prologue, the first 20 or so lines): it sets the tone for everything
   after.
2. **Mother Rook** ([packet](rook.md)): the first conversation, and the hub
   the player returns to.
3. **Captain Holloway**, **Brannoc**, **Sella**, **Vonnra**, **Harlan**: the
   town's main parts, in the order the story meets them.
4. **Chid**, **Maeca**, **Ysolde**: held for the story editor's review (in
   progress).
5. The rest: Pell, Rav, Keegan, Wenna, Tam, Jory, Redcowl, the watch, the
   townsfolk, the creatures and the dead.

## The packets

<!-- PACKETS -->
| Character | Takes | Characters | Held |
|---|---|---|---|
| [The narrator](narrator.md) | 269 | 27,374 |  |
| [Sella](sella.md) | 95 | 9,821 |  |
| [Vonnra Ash-of-Morrow](vonnra.md) | 76 | 8,878 |  |
| [Captain Holloway](holloway.md) | 64 | 7,712 |  |
| [Harlan Coyle](harlan.md) | 63 | 7,141 |  |
| [Mother Rook](rook.md) | 45 | 6,073 |  |
| [Chid](chid.md) | 51 | 5,525 | 2 |
| [Rav Cutwell](rav.md) | 52 | 5,351 |  |
| [Maeca Barefoot](maeca.md) | 73 | 5,332 |  |
| [Dame Keegan Orme](keegan.md) | 44 | 4,924 | 1 |
| [Old Wenna](wenna.md) | 33 | 3,978 |  |
| [Redcowl](redcowl.md) | 40 | 3,806 |  |
| [Pell Varrow](pell.md) | 31 | 3,605 |  |
| [Ysolde Marrow, the Wayfinder](ysolde.md) | 26 | 3,142 |  |
| [Townswoman, young](folk_f2.md) | 47 | 3,056 |  |
| [Townsman, middle-aged](folk_m1.md) | 46 | 2,998 |  |
| [Townswoman, middle-aged](folk_f1.md) | 45 | 2,638 |  |
| [Townsman, old](folk_m2.md) | 43 | 2,470 |  |
| [Snib](snib.md) | 15 | 2,199 |  |
| [Brannoc](brannoc.md) | 49 | 2,197 |  |
| [Tam](tam.md) | 19 | 1,814 |  |
| [Jory Coyle](jory.md) | 14 | 877 |  |
| [A Watchman at the gate](guard.md) | 12 | 510 |  |
| [Grimtunnel](grimtunnel.md) | 7 | 442 |  |
| [The babbling lampling](lampling.md) | 2 | 421 |  |
| [A Watchwoman](guard_f.md) | 9 | 406 |  |
| [A town girl](folk_child_f.md) | 7 | 205 |  |
| [A town boy](folk_child_m.md) | 7 | 205 |  |
| [The Ford-Warden](warden.md) | 6 | 164 |  |
| [The dead Watchman](watchman.md) | 1 | 45 |  |
| [The Legion's dead, behind the door](barrow_lord.md) | 5 | 41 |  |
| [The bones](bones.md) | 1 | 37 |  |
| [The Ford-Warden, the man under him](warden_man.md) | 1 | 14 |  |
| [The Red Hand](red_hand.md) | 1 | 13 |  |
| [A Kerchief woman](kerchief_woman.md) | 1 | 11 |  |
<!-- /PACKETS -->

"Takes" counts every part the character speaks. A line shared with the
narrator is one take per part, named `<line id>.p<part>.wav`.

## Credits

ElevenLabs charges per character generated. At three tries a line, all of Act
1 is roughly 400,000 credits: two months of the Creator plan or one of Pro.
The narrator alone is about a quarter of that.

## The hymn at Nell's grave (open)

C08 (`docs/cinematics/c08_iron_marker.md`, "Lines", "Casting" and "Sound")
needs "Lie Down" sung:
- Chid's voice is flat and slows on each verse's turn;
- a ragged ring of voices joins each last line;
- Vonnra's low alto is in tune and word-perfect under it.

ElevenLabs' speech models do not sing reliably. It is held until the owner
chooses one of these:

- **Eleven Music** (on the paid plans, cleared for use in games) takes custom
  lyrics and an a-cappella brief. It can make the ring and an in-tune alto,
  but not in Vonnra's designed voice, and it is unlikely to sing flat on
  purpose.
  - Chid's part would then be recorded in his own ElevenLabs voice, half
    sung and half said ("a half-sung, half-said Chid is also true to him",
    C08), and laid over the ring.
  - Cheapest to try: one evening with the plan already paid for.
- **A singer we have the rights to** (the owner, or a hired session singer,
  with written consent) for Vonnra's alto, and the ring overdubbed. This is
  the surest way to get the alto right.
- **A licensed singing synthesiser** (for example Synthesizer V Studio with a
  commercial voicebank), from a written melody: four plain lines in a minor
  key, lifting on the last.
