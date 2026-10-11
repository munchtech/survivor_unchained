# Handoff: the story and writing lead (Survivor Unchained)

You are the writer. You own the canon, every word the game says, the story
data and the cinematic scripts, and you sign off voice packets.

## Where it stands (the fourteenth lead, 11 October)

- **The sophistication pass (Act 1) is in** (commit e3ba91b3, branch
  `story/sophistication-pass`): Maeca never says "three days"; ledger line 26
  is "A woman. No name." and Vonnra's hand covers the toll's page (C09);
  `rook.mother2`'s answer "A week. I was a week on the road."; the gate scenes
  (`scene_in_my_count` has one crowd voice, `say`, folk_m1, saying the toll's
  truth: "every morning since you came, there's somebody up the street didn't
  wake"; Holloway walks through them; the (b) plant "Gray, all of them, and
  not a sound out of them."; "...Sit down. I'll tell you who."); the tic cut
  (hammer and Chid's quiet kept); boots thinned; Chid's "What do I cut?"
  (`chid.cut`, after she has stood at the marker; fact `mother.cut`, a seed);
  `decoy.north`; folk 112 (B's money) and 113 (Wat's mare); Sella's stalker
  line. Bible: rule 7 (the dead don't knock), Gale settled, §1, §6 seeds,
  §12. TREATMENT hygiene done (boot roll, line 26, the narrator's casting,
  day 3). LOVE_SCENES B loses "Boots.". Tests: `The_sophistication_pass_holds`.
- **TOLL_SPEC settled:** the gentle deaths varied (one "sat down ... and
  went", two chairs, two sleeps), "Which death." replaces "Detail:", Vonnra's
  close is now "...No charge, this once. Not to you." (also in TREATMENT §0
  and the bible), C09 text applied, the crowd line noted in §9. Ready for a
  combat or story-code lead.
- **The 30 narration lines are directed** (29 narrator in `narrator.json`, the
  gate guard's dusk call in `additions.json`).
- **Locks: 424** (was 162): every directed line of Holloway, Maeca, Chid and
  the narrator (with Rook and Brannoc mixes), the 30 above, and the guard's
  call. **Held, not locked:** the 46 undirected lines in
  `docs/voice/undirected_held.txt` (mostly the `scene_*` lines, Chid's
  carried/office, Holloway's roll) and the pass's edited lines (`maeca`
  blind_morning, told_true, blind_walk, blind; `scene_*`; `chid.cut*`;
  `vonnra.f_chart`, which also has Vonnra's voice).
- **The editor-judge** (su-lead-max) was judging the pass when this was
  written; see the status page for its verdict and what was applied.

## Next, in order

1. The judge passed the pass with four fixes, all applied (status page). Give Chid's marker a return in Act 2 or C32 for `mother.cut` `none`.
2. Direct the held lines (narrator plain and dry, VOICES.md), then lock them
   with `lock.py` (pass ids through Python: a shell `$(cat)` of a CRLF list
   locks nothing). Prefixes match by `startswith`: `dlg.x.hub.1` also locks
   `hub.10`; check the count.
3. Then Act 2, per `git show 86b97737:docs/handoff/story.md` §3. Optional:
   the marker's later text could show "MAM" (`Waystation.cs` `mother_grave`,
   a new narrator line).

## Branch and tools

- Branch `story/sophistication-pass` (from d05cd4f5). `cd godot/tests &&
  dotnet test` (792 pass, 8 skipped) before any commit touching data.
- Scripts in `C:\Users\munch\AppData\Local\Temp\claude\...\91211d34...\scratchpad\s14\`,
  backed up to `survivorsunchained_inputs\scratch_91211d34\s14\` (set `WT`):
  `showc.py`, `findt.py SUBSTR` (ids and lock state), `listc.py CONV`,
  `lsv.py VOICE`, `undir.py` (per voice: lines, directed, locked),
  `lockset.py HOLD...`, `adddir.py`, `rep.py`, `lib.py`.
- After edits: `lines.py`, `elevenlabs.py`, `lock.py --check`, `check_ids.py`.

## Gotchas

- A scene's banner is the scene's speaker entry (`npcs.json` speakers); a
  node `speaker` only picks the voice (`lines.py` NODE_VOICE) and the style.
- Morning reports are unvoiced. A capitalized parenthesis in a line is the
  narrator's. StoryLint: a fact written and not read must be in `Seeds`.

## The owner's words

- 11 October: "another pass of sophistication"; "we need a big twist nobody
  sees coming"; "I'm still missing a WHAT THE FUCK kinda moment".
- Before: "a powerful epic story with real emotional happenings"; Maeca
  killing Holloway "a HOLY SHIT WHAT THE FUCK kinda thing"; Brannoc "needs to
  hit HARD. so hard."; "the harshest versions are what were aiming for".
- Game text is American spelling. The tone is adult.

## Read first

This page; `docs/team/story.md`; `TREATMENT.md` §0 (the top block).
