# Story and writing: status

Owner of the canon, the words and the story data. Handoff: `docs/handoff/story.md`.
Branch: `worktree-agent-a7622ae77d19e31dc`.

## State

- **Canon:** `docs/STORY_BIBLE.md` (the truth, all three acts), `docs/VOICES.md` (how
  everyone talks), `docs/WRITING_PASS.md` (Act 1's spec; §17 is the latest pass),
  `docs/cinematics/` (C01 to C14 written; Acts 2 and 3 outlined).
- **Act 1's data** is written and tested (`godot/data/content/`, `CinematicTests`,
  `StoryLint`, the story explorer).
- **Last pass (§17), merged at `faabea9`:**
  - the editorial's cheap seeds;
  - conditional barks (`npcs.json` `said`);
  - the voice director's first notes;
  - the bosses' barks.
- **The explorer's full run** found nothing. Keegan's supper and Wenna's mask by the
  cure are played end to end in `RouteTests`.
- **In progress:**
  - the story editor's review of §17's new lines;
  - the voice director's next batch.

## Key decisions (why)

- **Bosses speak as themselves, the table bosses too.** The Barrow Lord's orders
  are one Latin word each; Grimtunnel goes down the hole delighted, never
  beaten. The bible's rule, and Grimtunnel is at the bottom of the stair in Act 3.
- **The Barrow Lord is "laid down".** That is the Order's word for the dead; the
  arena teaches it with the hands before the story says it.
- **The endless hour is truly endless (the owner's decision).** The dawn is on the
  other side of the open way out; inside, the night holds while she stays. Nobody
  explains it.
- **The ending decides the nights.** After re-forging, the arenas stay; after
  breaking the chain, there are none; after taking the light, the survivor is the
  boss.
- **Chid carries the survivor in after every death.** "A carter" is his lie, and it
  wears thin. It is a fair clue to what he is.
- **Barks that stop being true are conditional, not deleted.** The town should
  notice what the survivor did; stale barks were bugs.
- **A bare "she says" is cut from narration,** so the subtitle and the voice agree.
  Tags that carry manner stay.
- **Final voices are recorded by the owner in ElevenLabs, one character at a time,**
  from the voice agent's packets. Every line in a packet must be final before it is
  recorded: a changed word means a new take.

## Next

1. The story editor's notes on §17: fix what is right, before any packet locks.
2. The voice director's reads and packets, character by character: direction notes,
   then the lines marked final.
3. C14's data (`brannoc.road`) once story fights get an ally and the Low Ford road
   by night.
4. Act 2's text when the owner asks.
5. Teaching the explorer to cure the stream would improve its reach (a systems
   job).

## Blockers

None.

## For other areas

- **Voice:** see `WRITING_PASS.md` §17 for changed ids. Send each character's packet
  before the owner records it. I read it against the data, mark it final, and after
  that change no line without telling you. The hymn (C08) must be sung: Vonnra's
  in-tune alto is the clue.
- **Combat:**
  - I changed the words of four boss barks in `ArenaBosses.cs`.
  - Keep new boss lines to `VOICES.md`.
  - There is no Dawn at 60:00 (the owner's decision), and the story agrees.
- **Art:** Wenna's shop burns tallow, never ember. Maeca's plate reads "Hunter, of
  the Hollow".
