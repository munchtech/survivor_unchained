# Story and writing: status

Owner of the canon, the words and the story data; signs off every voice packet
before recording. Branch: `worktree-agent-a035208561a66c171` (successor to
a7622ae77d19e31dc; handoff in `docs/handoff/story.md`).

## State

- **Canon:**
  - `docs/STORY_BIBLE.md`: the truth, the pacing, who tells it, and "The nights"
    (the scars' places, the town's talk about your nights, the minibosses'
    rules).
  - `docs/VOICES.md`: how everyone talks, and the voicing rules.
  - `docs/WRITING_PASS.md`: §17 to §19 are the latest.
- **Act 1's data** is written and tested (`CinematicTests`, `RouteTests`,
  `StoryLint`).
- **The town talks about your nights:** 29 `said` lines across 13 people, each
  a seed. They're said that night (`arena.last.ago` 0) and the morning after
  (1), then dropped. `CinematicTests` proves that someone speaks after every
  kind of night.
- **Voice packets** (the owner has paused voice work; packets stay text-only):
  - **Final:** narrator, Rook, Holloway, Brannoc, Sella, Vonnra, Harlan.
  - **Read, with notes waiting for a voice lead** (below): Chid, Maeca,
    Ysolde.
- **Crafting:** Brannoc's forge lines are in his voice. Phase 2's lines (the
  fang, the shed fur, Wenna's still-room) are with the crafting lead.

## Key decisions (why)

- **Vonnra is not the narrator.** She is the voice up the road at the waking:
  labelled "A voice up the road", never the narrator's italics. The fortune
  opens on the same words.
- **Her name for the survivor is warm the way owning is warm,** not tender.
  **Her free things are priced and then waived,** so they stay owed.
- **Redcowl fed his prisoners.** If they die, the cold killed them.
- **The night's talk plants and never says.** The question "So what were you
  killing?" may be asked; nobody in Act 1 answers it.
- **No genre words in the valley's mouth:** Greymuzzle is the old dog-wolf;
  there is no alpha, warlord or ganger.
- **The night is worded by the night:** "the dead of night", everywhere but
  the Wayfinder's own half hour.
- **After ending B,** the endgame is the Wayfinder's book of the nights that
  were (the owner's decision).

## Notes waiting for a voice lead (packets text-only)

- **Chid:**
  - Wants: company, the shrine lit, and this one to stay up.
  - Hides: he is Unchained and near two hundred; he carries the survivor in (the
    carter is his lie); he is "C."; he was at the ford the night they rose.
  - Takes 13 and 14: "..…" becomes "…".
  - Bark day.1, "I should know.": older than he looks, and he doesn't notice
    saying it.
- **Maeca:**
  - Wants: the Pack cured and let be.
  - Hides: the Pack saved her at Ashford; the Kerchiefs are her old
    neighbours; she is looking for whoever signed for the boots.
  - Bark said.6's note is stale.
  - Bark said.3: "'Listen.' very quiet; not a whisper."
  - Re-take driving.0: "alpha" is now "dog-wolf".
- **Ysolde:**
  - Wants: the maps walked and the margins full.
  - Hides: she sells the margins (who comes back) to Sallow, for her brother
    Edric's keep. He came out of the barrow risen, and the Vigil cages him.
  - t_wayfinder: "My brother didn't." is the one lie in her part, practised
    smooth. The hurt goes in the corners.
  - Re-take places.0, which now says "Last till the dead of night".
- **New lines for every packet:** the night talk (npcs.json `said`, appended).
- **Changed lines in packets:**
  - Chid `cb_nemesis_slain.0` (no longer Keegan's "Not there").
  - Sella `say_calling.2`, "Something on you's smouldering, love." Sella's
    packet is final, so tell voice.

## Act 1 pass (done)

- Every quoted phrase in the bible's seed list is in the game's text.
- Every line about her body heat holds at the time it can be said.
- The signatures stay their owners'; a test holds them.

## Next

1. The result screen's words, when the experience successor sends UI's slots.
2. C14: `brannoc.road`, the `nell.burial` variant and a RouteTests play, once
   combat's successor builds the fight (combat handoff, queue item 5).
3. C01 to C04: the cinematics lead's line asks, when they come.
4. Crafting phase 3: Vonnra's binding lines. Act 2, when the owner asks.

## Blockers

None. One question for the owner: who sings the hymn (C08).

## For other areas

- **Main session:** C01's call should carry the label "A voice up the road".
- **Crafting:** call the endgame's "sigils" Marks; the sigil is the Legion's.
- **Experience:** your `arena.last.*` facts are read now. `arena.last.ago` is
  new (Arena.cs, plus the daily rule `arena.ago`).
- **Combat and arena art:** the renames and the scars' places are in, as sent.
