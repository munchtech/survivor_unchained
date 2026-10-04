# Story and writing: status

Owner of the canon, the words and the story data. Handoff: `docs/handoff/story.md`.
Branch: `worktree-agent-a7622ae77d19e31dc`.

## State

- **Canon:** `docs/STORY_BIBLE.md` (the truth, all three acts), `docs/VOICES.md` (how
  everyone talks), `docs/WRITING_PASS.md` (Act 1's spec; §17 is the latest pass),
  `docs/cinematics/` (C01 to C14 written; Acts 2 and 3 outlined).
- **Act 1's data** is written and tested (`godot/data/content/`, `CinematicTests`,
  `StoryLint`, the story explorer).
- **This session's pass (§17):**
  - the editorial's cheap seeds, all now in the data: "gone to the Morrow",
    Wenna's tallow, Chid's flame, the ember lore, the carter wearing thin,
    the nemesis names, the trait, Maeca keeping Ashford, the tutorial line;
  - the town noticing settled threads, as conditional barks (`npcs.json`
    `said`);
  - the voice director's first notes;
  - the arena bosses' barks brought to the bible.
- **The explorer's full run** (16 survivors, 30 minutes) found nothing.
  - Its search never reaches Keegan's supper or Wenna's mask by the cure: it
    never cures the stream.
  - Both are now played end to end in `RouteTests`.
  - Nothing was added to `Accepted`, because neither is a finding.

## Key decisions (why)

- **Bosses speak as themselves, the table bosses too.** The Barrow Lord's orders
  are one Latin word each; Grimtunnel goes down the hole delighted, never
  beaten. The bible's rule, and Grimtunnel is at the bottom of the stair in Act 3.
- **The Barrow Lord is "laid down".** That is the Order's word for the dead; the
  arena teaches it with the hands before the story says it.
- **The ending decides the nights,** and an endless hour ends at dawn if it ends
  at all. The world's rule is that the ember drains at sunrise; whether it ends
  is the owner's call.
- **Chid carries the survivor in after every death.** "A carter" is his lie, and
  it wears thin. It is a fair clue to what he is.
- **Barks that stop being true are conditional, not deleted.** The town should
  notice what the survivor did; stale barks were bugs.
- **A bare "she says" is cut from narration,** so the subtitle and the voice
  agree. Tags that carry manner stay.

## Next

1. The voice director's next batch: Vonnra's first meeting and the fortune, then
   Harlan and Jory, then the opening narrator.
2. C14's data (`brannoc.road`) once story fights get an ally and the Low Ford road
   by night.
3. Act 2's text when the owner asks.
4. Teaching the explorer to cure the stream would improve its reach (a systems
   job; ask the main session).

## Blockers

None.

## For other areas

- **Voice:** the changed line ids are in `WRITING_PASS.md` §17.
  - `chid.woke` and `chid.cb_nell` have new variants, so their variant indices
    moved.
  - Every `bark.<npc>.said.<i>` is new, and the moved barks left the day and
    night lists, so those indices moved too.
  - `folk.25` and `folk.97` are reworded; `folk.107` to `folk.109` are new.
  - `tools/vo/lines.py` reads `said`.
  - The hymn (C08) must be sung: Vonnra's in-tune alto is the clue.
- **Combat:**
  - I changed four boss barks' words, and only the words, in `ArenaBosses.cs`:
    the Barrow Lord's "Sta!" and "Iunge!", and Grimtunnel's going-down line.
    Keep new boss lines to `VOICES.md`.
  - A Dawn at 60:00 has the story's blessing.
- **Art:** Wenna's shop burns tallow, never ember. Maeca's plate now reads
  "Hunter, of the Hollow".
