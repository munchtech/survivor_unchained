# Story and writing: status

Owner of the canon, the words and the story data; signs off every voice packet
before recording. Handoff: `docs/handoff/story.md` (ready for a successor).
Branch: `worktree-agent-a7622ae77d19e31dc`.

## State

- **Canon:**
  - `docs/STORY_BIBLE.md`: the truth, the pacing, and who tells it.
  - `docs/VOICES.md`: how everyone talks, including the rules for voicing.
  - `docs/WRITING_PASS.md`: §17 to §19 are the latest.
  - `docs/cinematics/`: C01 to C14 are written; Acts 2 and 3 are outlined.
- **Act 1's data** is written and tested (`CinematicTests`, `RouteTests`,
  `StoryLint`). The explorer's full run is clean.
- **Voice packets:**
  - **Final:** the narrator, Rook, Holloway, Brannoc.
  - **Sella:** final once her split quotes carry her own direction.
  - **To read:** Vonnra (with the C01 call), then Harlan.

## Key decisions (why)

- **Vonnra is not the narrator.** She is an unnamed voice up the road at the
  waking, and the fortune opens on the same words. Narrating everything would
  give her a sight she only buys, spend the twist on day one and her scarcity,
  and put a buyer's voice over the private scenes.
- **Early on, the story is 40%.** A story night is 20 minutes, and a
  Wayfinder map 30. The endgame has two kinds of arena, permanent (the atlas)
  and a night's scar, and both exist after every ending.
- **The endless hour is truly endless** (the owner's decision).
- **Bosses speak as themselves.** Grimtunnel never dies, and never finishes
  "surface-meat" at her after C03. The Barrow Lord gives plural Latin orders.
- **Barks that stop being true are conditional** (`said`), not deleted. The
  town notices.
- **Signature phrases are never shared.** Repetition for weight belongs to
  Chid and Keegan.

## Next

1. Read and sign off Vonnra's packet, then Harlan's (`tools/story/packet_check.py`).
2. Write the town's lines about your nights, once the experience director's
   `arena.last.*` facts land.
3. Word the night's announcements by the night, not the clock, from combat's
   list.
4. C14's data, when story fights get an ally. Act 2, when the owner asks.

## Blockers

None. Two questions for the owner: who sings the hymn (C08), and whether the
endgame after ending B is "the Wayfinder's book".

## For other areas

- **Voice:** C01 has two new takes. `cin_drowned_fire.lamp` is the narrator's,
  and `cin_drowned_fire.call` (speaker `far_voice`, "A voice up the road") is
  Vonnra's, far off. The suggested names changed, so regenerate the 24 name
  takes.
- **Cinematics:** C01's shots 8a and 8b are placeholders for you to frame.
- **Combat and experience:** story nights are 20 minutes. Announcements must
  never say "half hour" on them.
- **UI:**
  - I changed `Front.cs`'s suggested names and the default name (Wren); no
    name the story has spent.
  - Maeca's plate reads "Hunter, of the Hollow".
- **Art:** Wenna's shop burns tallow, never ember.
