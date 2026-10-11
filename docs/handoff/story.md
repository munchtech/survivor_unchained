# Handoff: the story and writing lead (Survivor Unchained)

You are the writer (su-lead-max). You own the canon, every word the game says,
the story data and the cinematic scripts, and you sign off voice packets.

## Where it stands (12 October, branch `story/marker-and-locks`)

- **Merge requested at fd0b8a9b** (judged): Chid's marker kept open (TREATMENT
  §3.3), the held lines directed and locked, judge s15's fixes (the mornings
  after are behind the door; rule `mother.carved` guarded; "Plain. ...I know
  who's in it."), the fix-check judge's doc edits. 498 locks; 794 tests pass.
  Verdicts: scratchpad `s15\verdict.md`, `s16\verdict_fix.md`.
- **On top, unjudged WIP: love scenes B in the data** (the owner chose B on 6
  October; the four conditions are in `docs/story/notes/02_act1_draft.md` §10).
  Script: `<scratch>\s16\b_apply.py` (read its header). Don't let it merge
  before a judge passes it. Everything behind the door is still HOLD
  (`elevenlabs.py` HOLD_LINES room prefixes), so nothing in it can be recorded.
  - On black (the night itself), directions are **captions only**: what is
    heard ("(water poured)", "(the hides rustle)") and how she says it. Visual
    stage directions there would be the narrator's prose by another name (the
    editor's warning). The mornings are lit: the narrator's parentheses became
    lower-case directions (the ruling).
  - Condition 1: the narrator's last line is the bolt, heard from the stairs:
    `free_bolt` (narrator node, "Behind the door, the bolt sticks halfway...",
    then Sella's "...There.") and the same sentence as an aside opening
    `free_sleep_bed` (one shared take). `free_stairs` lost its two in-room
    sentences (its lock is broken on purpose: re-lock it after the judge).
    "Lamp stays up tonight." (Sella, `free_door`) keeps the lamp image.
  - Condition 3: `maeca.blind_morning` variant 1 opens "(Gray light. She's
    already up, barefoot in the frost at the mouth of the Blind, listening to
    the wood: one hand on the crossbow and the other on you.)".
  - `rest_night` (downstairs, from `price`) keeps the narrator; the room's
    `rest_night_paid` has "(as if it's a word in a foreign tongue) Sleep."
  - New words to judge: Sella's "It's the lamp glass. Everyone asks." ("before you ask" is Maeca's signature: a test guards it),
    "Blue room again. Same jug, same quilt. ...Same me.", "I've undone a few
    of these, love.", "Give me your hands. ...Look at these knuckles.", "You
    jumped.", "Not chilled, love. Cold. Under warm water.", "The house. In the
    south. ...Kitchen faces the sun..."; Maeca's "They've settled. Sleep." and
    "...Mm. Keep still. ...They're only feet."

## Next, in order

1. **B's directions** (condition 4: more care than anything; RERECORD's note:
   low and close, nearly a whisper, never breathy; each "..." two to four
   seconds; a laugh that sounds made is cut). Write one file,
   `tools/vo/direction/love_b.json`, and **move** each changed id's entry out
   of `additions.json`, `imported.json`, `narrator.json` and `sella.json`
   (files load in sorted order and later ones win; keep `hides`; drop stale
   `beats` and `quote`, except `free_bolt` needs a `quote` for "...There.").
   Lines with captions or physical directions need a `segments` override,
   `[{"voice": "sella", "text": <the auto segment's words>, "acted": <same
   words with only vocal tags: [laughs], [exhales], [whispers], [long pause],
   [softly]>}]`; get the words from `lines.segments()` and assert they match.
   A mid-sentence `{name}` is dropped from takes. Ids: `python
   <scratch>\s15\lsp.py 60 dlg.sella. dlg.maeca.` against `git diff fd0b8a9b`.
2. **Docs:** LOVE_SCENES.md (B applied; its B blocks to match the data; the
   captions rule; A kept as condition 4's fallback); TREATMENT §3.4 item 5
   (about line 414, still says "plays as unvoiced text") and its mentions near
   lines 135 and 918; RERECORD.md's "New, only if the owner chooses the
   lovers' own lines" becomes B's take list for Sella and Maeca.
3. A fresh su-lead-max editor-judge on B (the diff from fd0b8a9b, the four
   conditions, the directions).
4. After it passes: lock B (Sella's and Maeca's room and morning lines, the
   bolt line, `free_stairs.0`), take the room prefixes out of HOLD_LINES,
   rerun the tools and `dotnet test`, then ask the main session to merge.
5. Act 2, per `git show 86b97737:docs/handoff/story.md` §3. When
   `scene_still_plain` is built, add `not mother.chisel` to Chid's hub choice
   "The marker. It's come to me." (TREATMENT §3.3). TOLL_SPEC waits for a
   code lead.

## Tools

- Scratch scripts: `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\`
  `s15\` (`showc.py CONV [NODE..]`, `lsp.py N PREFIX..`, `lib.py`
  round-trip-safe JSON edits, `do_lock.py`) and `s16\` (`b_apply.py`,
  `olddir.py` and `fulldir.py` for directions, `holds.py` the judge's hold
  check).
- After edits: `python tools/vo/lines.py`, `elevenlabs.py`, `lock.py
  --check`, `check_ids.py`; `cd godot/tests && dotnet test` (about 7 min).

## Gotchas

- A lock binds words: an edited locked line drops to HOLD. Lock through
  Python (`do_lock.py`), check the count (prefixes match by `startswith`).
- A capitalized parenthesis in a person's line is the narrator's; a
  lower-case one becomes an audio tag in that person's take.
- StoryLint fails a fact read but never written (why the chisel guard waits).
- The context hook warns from 80%: B's data cost little, the reading cost a lot.

## The owner's words

- "a powerful epic story with real emotional happenings"; Brannoc "needs to
  hit HARD. so hard."; "the harshest versions are what were aiming for";
  "WHAT THE FUCK kinda moment" (twists A, B, "It takes less than it did").
  Love scenes: B. American spelling; the owner is they/them; the tone is 18+.

## Read first

This page; `docs/story/notes/02_act1_draft.md` §10; LOVE_SCENES.md; the B
diff (`git diff fd0b8a9b -- godot/data/content/dialogue.json`).
