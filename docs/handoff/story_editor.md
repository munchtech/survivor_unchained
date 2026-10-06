# Handoff: the story editor

You are the story editor for Survivor Unchained: a demanding developmental
and line editor who makes the writing land. You read the story lead's
drafts and send back notes. You never rewrite their scenes. Read
`docs/team/README.md` first, then `docs/team/RESUME.md`, then the Story
section of `docs/team/OWNER_NOTES.md`, then this page, then
`docs/story/EDITORIAL_LETTER.md`. The letter is the core of the job.

- **Branch:** `worktree-agent-ad7d2e659356b6dc5` (the second editor; the
  first was `worktree-agent-a8d7dfe2856df399e`). Merge
  `origin/claude/vigilant-galileo-l6jqyx` first, and often. Commit your
  notes to `docs/story/` and push. Open no PRs.
- **Tests:** `cd godot/tests && dotnet test` before every commit, even
  docs-only ones.
- **Commits:** write the message to a file and use `git commit -F`. End it
  with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- British spelling.

## 1. The owner's words

- "we need better writing", "we need emotional power"
- "a mind breaking twist dosn't exist at the moment, and gut wrenching stuff dosn't hit too hard"
- "we are pulling punches on really hitting things. twists should either twist a knife in or just make you feel gidd with a what the heck just happened. we don't really have either."
- "we really want a powerful epic story with real emotional happenings. people being devastated, elated, or both. shocks and twists, stuff we figured out that was obvious. the whole thing. its all very simple right now."
- Maeca: drop "Barefoot", "a little silly"; give her a real failing to hold against Holloway.
- Holloway "was a good man"; his act got them all killed; now a drunk trying to forget who still protects, "because he is a GOOD man".
- Brannoc made the thing that got his daughter killed: "needs to hit HARD. so hard."
- "when maeca kills halloway it should be a HOLY SHIT WHAT THE FUCK kinda thing."

## 2. Your brief

1. Hold the story lead's work to the bar: a beat is not done until it would
   make a player stop, swallow or laugh out loud. Say plainly when it isn't
   there yet.
2. For each draft send notes: what lands and what doesn't, and why; line
   cuts; and, for each twist, whether it truly re-reads what came before
   and whether its plants are fair but hidden. Use the six twist tests in
   the letter, §3.7, and the Holloway and Maeca tests in §3.6.
3. Give suggested lines only where a note needs one.
4. Be the hardest reader the treatment gets before it reaches the owner.

**Rules:** love scenes fade to black. Never "Ashford" in item names or lore
(StoryLint holds it). Hand off at about 500k tokens of context.

## 3. Done, in progress, next

- **Done:** `docs/story/EDITORIAL_LETTER.md`, committed and sent to the
  story lead. Its four root causes are below.
  1. Setups confess and payoffs whisper (invert it).
  2. Every devastation is on a branch (put one per act on the trunk).
  3. Nell carries all three acts' major turns, and Act 1's is "None" by the
     bible's own table.
  4. All the dying happened before the player arrived.

  The letter also covers Brannoc's knowing (never staged), Holloway and
  Maeca, the false-belief twist tests, the quiet act endings and the
  missing elation, the mother's missing face, line notes, and voices that
  blur.
- **Done:** `docs/story/notes/01_treatment.md`, notes on the writer's
  `TREATMENT.md`, `SAMPLE_SCENES.md` and `EMOTIONAL_PASS.md` (at
  `63b97e39`), ranked. Sent to the main session, which carries them and the
  owner's choices to the writer's successor (the writer, `a3047062bf0f80c54`,
  is paused near its limit).
- **Next:** note each beat draft of the rewrite as it comes, in
  `docs/story/notes/NN_<beat>.md`. Check first that the successor took
  notes 01's items 1 to 3, or that the owner overruled them.

## 4. Decisions, and why

- **Restraint is for setups and aftermaths, never for the blow.** Today
  the house rule "never say it" mutes the payoffs, and the setups are
  near-confessions (`holloway.ashford`, `harlan.knew`, `vonnra.f_self`).
- **Every secret gets one job:** twist (the player must not know) or irony
  (the player knows and a character doesn't). Chid works best as irony.
  Harlan and the Holloway and Maeca thread must be twists.
- **Maeca's killing of Holloway must be:**
  - on the trunk, not optional;
  - in front of the player, fast, with no speech before;
  - at the moment of most love for Holloway;
  - and in Act 1 she must be kind to him, never visibly aggrieved.
- **Brannoc:** the player must be in the room when he knows. Put his iron
  in his hands, plant his pride, and bring the boots into Act 1 as irony.
- **Notes 01, the main calls:**
  - the confession's option "Did anyone come out from under it?" is the
    loudest tell for Maeca; cut it;
  - move the confession to mid-Act 1, and put "tell Maeca" on the trunk as a
    false forgiveness;
  - put the player's hands on the rope (a held haul with no fail state);
  - cut boots from Holloway (the roll's boot sizes; "Every pair"). Nell's new
    boots are the only boot image left;
  - offer the owner Holloway's call as wrong but defensible ("the lamp in his
    eyes"), since the owner's word was "poor judgement call";
  - give twist B a false belief (Rook's kind lie on day 1), and quieten the
    readable ledger;
  - cast the narrator plain, and make her thin across the game, so C43 turns
    twice.
- **The owner's §10 answers** (in `OWNER_NOTES.md`) are folded into notes
  01. The lie to Brannoc costs the relationship, not his trade, and the
  notes list what that unsettles in the treatment and in crafting.
- **I praised and protected:** the romances, C07, C14's images, the comedy
  (Snib, Keegan, Chid, Sella), ember-is-the-dead, C09's eyeline rule, and
  "Them first."

## 5. Gotchas

- `dialogue.json` is 494 KB; don't read it raw. The scratchpad script
  `scratchpad/ed/dump.py` (in the session's scratchpad; rewrite it if it's
  gone) prints each conversation as text, with short condition tags, to
  `scratchpad/ed/out/<conv>.txt`. That is about 240 KB in all; read only
  the speakers you need.
- An earlier editorial study is in `docs/editorial/`, dated 3 October. It
  praised the restraint ("should not gain a word"); the owner now says it
  doesn't hit. The letter says why both can be true: restraint multiplies
  feeling and cannot create it.
- The bible still says "Maeca Barefoot" and calls the boots Act 2's spine.
  Treat the treatment, once the owner chooses, as superseding those parts.
- The writer's self-critique list (one blow too many in Act 2; the one-night
  window; the voice twist's guessability; Brannoc's beats crowding) came by
  message, not in a file. Notes 01 answers each (items 6, 1b, 4 and 7).
- "Ashford" is fine in dialogue, but never in item names or lore.

## 6. Collaborators

- **Story lead (the writer):** `a3047062bf0f80c54`, paused near its limit;
  its successor starts from `docs/handoff/story.md`. Sends drafts, gets
  notes.
- **Story and writing, the earlier lead:** `a7ba8903f4c8261b1`
  (`docs/team/story.md`).
- **Cinematics:** `aece7b87e89b13f19`. C23 and C27 should wait on the
  treatment.
- **The main session** relays the owner.

## 7. Read these first

1. `docs/story/EDITORIAL_LETTER.md`
2. `docs/team/OWNER_NOTES.md`, the Story section
3. `docs/STORY_BIBLE.md`: §1, §3, §5 (with "The extremes, rationed") and §7
   beats 3, 4 and 8
4. `docs/cinematics/c07_hammer_stops.md`, `c14_road_back.md`,
   `c09_fortune.md` and `act2_outline.md` (C22, C23, C27, C31)
5. `docs/story/TREATMENT.md`, `SAMPLE_SCENES.md`, and
   `docs/story/notes/01_treatment.md`
