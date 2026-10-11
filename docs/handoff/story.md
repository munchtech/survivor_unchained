# Handoff: the story and writing lead (Survivor Unchained)

You are the writer (su-lead-max). You own the canon, every word the game says,
the story data and the cinematic scripts, and you sign off voice packets.

## Where it stands (11 October, writer 14, branch `story/marker-and-locks`)

- Integration has everything to fd0b8a9b (merged as 01d0bd95).
- **Love scenes B, directed and guarded, unjudged** (05ae446d data, 708cf892
  directions, docs, guard; 795 tests pass):
  - Directions: `tools/vo/direction/love_b.json` (60 lines; built by
    `<scratch>\s17uild_b.py`, which holds every direction as a spec and
    asserts the acted words; edit the spec and rerun, not the json).
  - Writer 14's pass before the judge: `told_true` lost its two narrator asides
    (under the hides), "(the embers tick)", "Say stop and I stop.", "crouched"
    at the mouth of the Blind, rest_dark ends "Somebody ought to watch you.",
    "practice" (`<scratch>\s17ix1.py`, `fix2.py`).
  - `produce.fit`: a direction `gap` keeps silences up to that many seconds
    (the importer cut every pause to 1.6 s; B's "..." are 2-4 s).
  - The door, for good: `elevenlabs.py` `DOOR`/`behind_door` holds any
    narrator part behind the door, locked or not (the bolt excepted); the
    packet lists the bolt once under free_bolt's direction;
    `tools/vo/tests/test_door.py`; `StoryRewriteTests.The_narrator_stops_at_the_door`.
  - Docs: LOVE_SCENES (B as built, the rules, the sounds for cinematics and
    sound, A = fd0b8a9b as the fallback), TREATMENT, RERECORD (B's take list),
    VOICES (captions rule).
- **The editor-judge on B is running** (su-lead-max, spawned by writer 14; its
  verdict file: `<scratch>\s17erdict_b.md`). If it isn't there, re-spawn one
  with the same checklist (the brief is in writer 14's transcript; the
  checklist: the four conditions, voice, 18+ taste, the door and captions,
  directions, recordability, continuity).

## Next, in order

1. Apply the judge's fixes (data through `lib.py`; directions in
   `build_b.py`'s SPEC, rerun it), then `python <scratch>\s17\lock_b.py`
   (locks B and the room's other lines, re-locks free_stairs.0, trims
   HOLD_LINES to Keegan's kenning). Then `lines.py`, `elevenlabs.py`,
   `lock.py --check` (0 broken), `check_ids.py`, the voice tests
   (`python -m unittest tests.test_door tests.test_lock tests.test_lines` in
   tools/vo), `dotnet test`. Merge integration, push, SendMessage the main
   session to merge, with one line for the owner: what is now recordable
   from those scenes (Sella's room lines, Maeca's under the hides, the
   narrator's bolt; nothing else of the narrator's behind the door).
2. Act 2, per `git show 86b97737:docs/handoff/story.md` section 3. When
   `scene_still_plain` is built, add `not mother.chisel` to Chid's hub choice
   "The marker. It's come to me." (TREATMENT section 3.3). TOLL_SPEC waits for
   a code lead.

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
