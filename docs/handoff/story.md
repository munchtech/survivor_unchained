# Handoff: the story and writing lead (Survivor Unchained)

You are the writer. You own the canon, every word the game says, the story
data and the cinematic scripts, and you sign off voice packets.

## Where it stands (the twelfth lead, 11 October)

- **The canon now holds** A ("Not yet": Chid made you), B ("Count's right":
  Holloway knew) and option 1 of `docs/story/TWIST_WTF.md` ("It takes less
  than it did": every rise since the first costs a life in the valley; the
  ledger past line 27 is the player's own deaths). The owner chose 1 knowing
  that dying in the endless then costs a life. Option 3's "I made him too." may
  go into A's C42 Chid scene, at your call (not yet written). **None of the
  three is in `TREATMENT.md` §0 or the bible yet:** write them in when you
  next touch those (grep by section; never read either whole).
- **Step 1 done: the early lines are LOCKED FOR RECORDING.** 160 lines: the
  narrator's prologue and C01 to C04, Vonnra's far voice, the Warden's,
  Grimtunnel's, the dead Watchman's and the gate guard's prologue lines,
  Rook's and Brannoc's Act 1 lines with the narrator's parts inside them. A
  max editor-judge passed them after five fixes (applied: Brannoc "looks you
  over", not "looks at you properly", which `nell_risen` says later; the
  narrator's casting and two `[whispers]`; directions for 30 bare takes;
  `nell_with` false on the night path). I rejected one finding: the "He" in
  `warden_answer` is deliberate (the player has just heard the man's voice).
- **Seeds folded in (not locked; Chid and Holloway stay on hold):** A:
  `chid.first`'s look (both variants), the reeds line at dawn (locked, in
  `Prologue.Dawnbreak`), the day-2 report `chid.ford_burial` (rules.json).
  B: `scene_knocking.knows` (his eyes go to the step on "Pell."),
  `scene_his_cup` (he counts to ninety-one and starts again; drinks without
  looking). Option 1: C04's baker line stands word for word; "from nothing"
  cut from the dawn caption (under option 1 it was a lie).
- **Step 2 done: `docs/story/TOLL_SPEC.md`,** for a combat or story-code lead
  (the main session assigns it): the counter, the save's ledger, the baker
  and the scripted fall, the morning news (24 gentle, 16 with a cause, 4 Rook
  barks), the paid ones at night, C41, the endless line by ending, Flare
  saves (intended, never shown), tests. **Not yet judged:** give it a max
  judge before it goes to a builder.
- **Next, step 3: the sophistication pass** through the rest of Act 1, then
  Act 2 (the plan: `git show 86b97737:docs/handoff/story.md`, §3; the open
  work list: `docs/story/notes/02_act1_draft.md` §12). Then lock Holloway,
  Maeca, Chid and the rest of the narrator the same way.

## Branch and tools

- **Branch:** `story/voice-lock-toll` (from the integration branch at
  5c1d9b47). Commit, push, open no PRs. Tests: `cd godot/tests && dotnet
  test` (760 pass, 8 skipped). `python -m unittest discover -s tools/vo/tests`
  has one error on this machine (librosa missing), not ours.
- **Locks bind words, not ids** (new, `tools/vo/lock.py`, `locked.json`).
  Change a locked line and its packet shows HOLD until you re-lock it:
  `python tools/vo/lock.py --by "the story lead" --date YYYY-MM-DD --prefix
  dlg.rook. ...` (or `--where <file>`); `--list`, `--check`. Changed words
  under an owner's take go in `docs/voice/RERECORD.md`'s "Changed" tables.
  Then `python tools/vo/lines.py`, `elevenlabs.py`, `check_ids.py`.
- **Scripts** (the worktree guard refuses bash with computed values; run
  Python with literal paths): `lib.py` (round-trip-safe JSON edits),
  `showc.py CONV [NODE...]`, `lsv.py VOICE [substr...]` (a voice's lines,
  status and takes from the manifest), `sheet.py` (the locked takes as one
  sheet for a judge). Backed up in
  `C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_91211d34\s12\`;
  set `WT` to your worktree.

## Gotchas

- **The rise lines have no voice id.** `DayLines.Rise`, `RiseAgain`, `Dusk`,
  `DuskHeard` and the rest reach `G.Say` as constants, which `lines.py`
  doesn't read. "You get up. It takes less than it did." is the line the
  whole twist hangs on: get it voiced (TOLL_SPEC §8) before the narrator
  records Act 1.
- Morning reports (`rules.json` `report`) are unvoiced text; every matching
  report shows each morning.
- A capitalized parenthesis inside a line is the narrator's (a voiced part);
  lower-case directions are not.
- Old Oswin dies twice (TOLL_SPEC §9). `scene_gate_dawn.all`: Maeca "looks at
  the step he was asleep on", but he slept on the ground and she on the step.
- `holloway.knocking` must not fire once `holloway.confessed` is set. Scenes
  share one morning and one dusk slot. StoryLint: every fact read is written.

## The owner's words

- 11 October: "lets fire up the writer - we need a big twist nobody sees
  coming, maybe chid being evil? and another pass of sophistication. also I
  would like to get some of the early lines mostly settled so I can truly
  begin my elevenlabs voices"; "I'm still missing a WHAT THE FUCK kinda
  moment - those are just like 'ohhh yeahhh'".
- Before: "a powerful epic story with real emotional happenings. people being
  devastated, elated, or both. shocks and twists, stuff we figured out that
  was obvious."; "when maeca kills halloway it should be a HOLY SHIT WHAT THE
  FUCK kinda thing."; Brannoc "needs to hit HARD. so hard."; "the harshest
  versions are what were aiming for."
- Spelling in game text is American. The tone is adult.

## Read first

1. This page, then `docs/story/TWIST_WTF.md` §1 and `TWIST_OPTIONS.md` A and B.
2. `docs/story/TOLL_SPEC.md` if you work on the toll.
3. For step 3: notes 02 §12, then the conversations you edit (`showc.py`).
