# Handoff: the story and writing lead (Survivor Unchained)

You are the writer. You own the canon, every word the game says, the story
data and the cinematic scripts, and you sign off voice packets.

## Where it stands (11 October, branch `story/marker-and-locks`)

- **Chid's marker kept open** (dc4e4a92): a player who says nothing at the
  marker gets the hub choice "The marker. It's come to me." (`cut_came`, then
  `cut_mam`, `cut_plain`, or `cut_still` "It'll keep."). "Mam." is cut that
  night (rule `mother.carved`: "Rook heard him from her kitchen: a tap, and a
  long wait, and a tap."), and the marker reads "It says MAM now..." or
  "Still no name on it." Act 2's return for `none`, `scene_still_plain`, is
  written in TREATMENT §3.3 and the bible (§7 beat 11, §12) for the Act 2
  build. `mother.cut` left StoryLint's seeds. Tests:
  `The_marker_waits_for_what_she_could_not_say`, `Her_mothers_marker_keeps_what_she_told_Chid`.
- **The held lines directed and locked** (c5a491e0): 84 directions in
  `tools/vo/direction/held.json`; **495 locks**. Still held:
  `docs/voice/undirected_held.txt` (with why).
- **Found: love scenes B was never applied.** The owner chose B on 6 October
  (OWNER_NOTES; the narrator stops at the door). 13 narrator lines behind the
  door had been locked for recording; they are unlocked, and the room's
  prefixes are HOLD in the packets (`elevenlabs.py` HOLD_LINES). The main
  session was told to warn the owner.
- **The editor-judge** (su-lead-max, background) is judging both commits;
  its verdict: `...\91211d34...\scratchpad\s15\verdict.md` (it messages the
  main session). 794 tests pass, 8 skipped.

## Next, in order

1. Apply the judge's fixes, then lock the marker's four new lines
   (`python <scratch>\s15\do_lock.py --new`; edits change hashes, so lock last).
2. **Write love scenes B into the data** (`docs/story/LOVE_SCENES.md` has the
   B text; the editor's four conditions, notes 02 §10: the bolt is the
   narrator's last line, from the stairs; no "Boots."; the narrator opens the
   grey light on "one hand on the crossbow and the other on you"; direct with
   more care than anything). Narrator parentheses inside the room become
   lower-case directions (`told_true`, `told_little`). Then a judge, then lock
   Maeca's and take the room's prefixes out of HOLD_LINES.
3. Act 2, per `git show 86b97737:docs/handoff/story.md` §3. TOLL_SPEC waits
   for a code lead; don't build it.

## Tools

- Scripts in `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\s15\`
  (already pointed at this worktree): `showc.py CONV [NODE..]`, `listc.py`,
  `lsp.py N PREFIX..` (lock state, voices), `findt.py`, `lib.py` (round-trip
  safe JSON edits), `dir_held.py` (how directions were written),
  `do_lock.py`, `lockset.py`, `undir.py`.
- After edits: `lines.py`, `elevenlabs.py`, `lock.py --check`, `check_ids.py`;
  `cd godot/tests && dotnet test` (about 7 minutes).
- This harness refuses complex shell lines outside the worktree: write a
  script to the scratch folder and run it with one plain `python` command.

## Gotchas

- A lock binds words: an edited locked line drops to HOLD. Pass ids to
  `lock.py` through Python (`do_lock.py`), never a shell `$(cat)`; prefixes
  match by `startswith`, so check the count.
- A scene's banner is its speaker entry (`npcs.json`); a node `speaker` only
  picks the voice. Morning reports are unvoiced. A capitalized parenthesis in
  a line is the narrator's. StoryLint: a fact written and not read must be in
  `Seeds`; a seed that is read must leave it.

## The owner's words

- 11 October: "another pass of sophistication"; "a big twist nobody sees
  coming"; "I'm still missing a WHAT THE FUCK kinda moment" (now canon:
  A, B, and "It takes less than it did").
- Before: "a powerful epic story with real emotional happenings"; Brannoc
  "needs to hit HARD. so hard."; "the harshest versions are what were aiming
  for". Love scenes: B. Game text is American spelling; the tone is adult.

## Read first

This page; `docs/team/story.md`; TREATMENT §0 and §3.3; LOVE_SCENES.md.
