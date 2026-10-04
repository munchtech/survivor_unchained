# Story and writing: status

Owner of the canon, the words and the story data; signs off every voice packet
before recording. Branch: `worktree-agent-a035208561a66c171` (successor to
a7622ae77d19e31dc; handoff in `docs/handoff/story.md`).

## State

- **Canon:**
  - `docs/STORY_BIBLE.md`: the truth, the pacing, who tells it, and "The nights"
    (the scars' places, the minibosses' rules).
  - `docs/VOICES.md`: how everyone talks, and the voicing rules.
  - `docs/WRITING_PASS.md`: §17 to §19 are the latest.
- **Act 1's data** is written and tested (`CinematicTests`, `RouteTests`,
  `StoryLint`).
- **Voice packets:**
  - **Final:** narrator, Rook, Holloway, Brannoc, Sella, Vonnra, Harlan.
  - **Next:** Chid, Maeca, Ysolde, then the rest, in the voice README's order.

## Key decisions (why)

- **Vonnra is not the narrator.** She is an unnamed voice up the road at the
  waking, and the fortune opens on the same words.
- **Her name for the survivor is warm the way owning is warm,** not tender. One
  take serves the accusation, the door and every greeting after.
- **Her free things are priced and then waived,** so they stay owed. The vault
  is the one thing she never prices.
- **Redcowl fed his prisoners.** If they die, the cold killed them, not hunger
  (Harlan: "They were fed").
- **Early on, the story is 40%.** Story nights are 20 minutes, maps 30. The
  endgame has two kinds of arena: the atlas (other places, Ysolde's) and a
  night's scar (the four peoples' own ground).
- **The night's minibosses:**
  - the Legion speaks Latin;
  - nothing about the Kerchiefs says "Ashford";
  - only Grimtunnel is "Boss";
  - the ford has no bell;
  - no genre words.
- **Signature phrases are never shared.** Repetition for weight belongs to
  Chid and Keegan.
- **No genre words in the valley's mouth:** Greymuzzle is the old dog-wolf,
  never an "alpha" (Maeca's line, the bounty, the objective, his plate).

## Next

1. Finish Chid's and Maeca's packets, then read Ysolde's
   (`tools/story/packet_check.py`). Send the notes to the voice successor (see
   the roster). The read so far:
   - **Chid:** add Wants and Hides at the top.
     - Wants: company, the shrine lit, and this one to stay up.
     - Hides: he is Unchained and near two hundred; he carries the survivor in
       himself (the carter is his lie); "C."; he was at the ford the night they
       rose.
     - In takes 13 and 14, "..…" becomes "…".
     - Bark day.1's "I should know." is older than he looks, and he doesn't
       notice saying it.
     - The hymn stays on HOLD.
   - **Maeca:** add Wants and Hides at the top.
     - Wants: the Pack cured and let be.
     - Hides: the Pack saved her at Ashford; the Kerchiefs are her old
       neighbours; she is looking for whoever signed for the boots.
     - Bark said.6's note is stale (there is no second "Nothing.").
     - Bark said.3: "'Listen.' very quiet; not a whisper."
     - driving.0's "alpha" is now "dog-wolf" in the data, so re-take it.
     - The blind3_morning ruling (quiet) is already applied.
2. The town's lines about your nights, once the `arena.last.*` facts
   (`a33f58e…@e908434`) are on the integration branch.
3. Crafting's lines, when the crafting lead sends them.
4. C01 to C04: the cinematics lead's line asks.
5. C14's data, when story fights get an ally. Act 2, when the owner asks.

## Blockers

None. One question for the owner: who sings the hymn (C08). Decided on 4
October: after ending B, the endgame is "the Wayfinder's book of the nights
that were" (bible §8).

## For other areas

- **Combat:** I sent renames and notes for the minibosses, the Latin words
  ("Scuta!", "Signa!"), Gutterwick for the Ganger, and the table bosses'
  titles. The night-worded clock is optional on the maps ("The dead of night").
- **Arena art:** the four scars' musts, must-nots and place words are sent,
  and in the bible's "The nights".
- **Crafting:** "Will you work my gear?" (not "Can you"). The §10.4 seeds are
  approved, with their wording.
- **Voice:** three lines changed at 4de18a1. "Hushed" is "quiet" for Maeca's
  Blind morning and Redcowl's last words.
