# Handoff: the story and writing lead (Survivor Unchained)

You are the writer (su-lead-max). You own the canon, every word the game says,
the story data and the cinematic scripts, and you sign off voice packets.

## Paused here (11 October, writer 16, branch `story/act2`): the owner paused Act 2

**Act 2, slice 1 is WIP: written into the data, unjudged, on HOLD.** Nothing
else of Act 2 is started. 817 tests pass; 566 locks ok, 0 broken.

What slice 1 is (C20, C20b, C22: the Holloway arc, twist B's reveal):
- `scene_it_stopped` (Act 2's first morning, rule `act2.stopped`): Tam, "It
  stopped like when you hold your breath to listen." Walking him home sets
  `tam.brought` (the dog won't get on the cart).
- `scene_ground_opens` (that dusk): the farm's lamps "like someone carrying
  them down a stair"; Tam ("Pa's in the kitchen." / "Pa went back for the
  dog."); Holloway counts who's down ("Posted them. Boy said it knocked."),
  "No. ...No. I'm going.", puts his coat round Tam; Maeca at the post: "Go on.
  I've got him." Going down sets `hole.down`.
- `scene_count_right` (the next morning, rule `hole.morning`): "Up. Go on. I'm
  last."; Maeca's hand; "Four."; Penhale's "And you took your bloody time,
  Captain!"; his laugh, "...I did." (the confession's "I did."); two "(Haul.)"
  choices with a red kerchief in the trees (the decoy); "Count's right."; one
  stroke; the rope through your hands; "Ninety-two." Lover: "You were up."
  Maeca's (b): "The ones under me weren't dead."; the Pack walks away (if
  cured/allied and Greymuzzle lives); Tam: "It started the night the ford
  went dark."; Tolley counts "...Ten." (he doesn't count himself, as the
  captain never did; "...Nine." if `wolves.at_gate`); the town's choice sets
  `maeca.after` held / stood ("She's in my count.") / gone; Tam in the coat.
  Sets `holloway.dead`.
- `scene_barred` (three dusks, `holloway.dusks` 1-3): quiet, not knocking
  (bible rule 7); the stool with the coat Tam brought back.
- `scene_one_in` (the fourth dusk, rule `holloway.risen`): he stands outside
  the barred gate; Tolley: "Captain never once barred it on anybody." /
  "...Somebody's still out."; Chid on the wall "standing very still" (A's
  seed); close, "...Ninety. Ninety-one. ...Ninety-two."; "One in." from Maeca
  (stood: she takes his coat and puts it on) or Tolley. Sets `holloway.laid`.
- `scene_his_table` (the next morning, rule `holloway.table`): Tolley counts
  the mourners in; Sallow's letter (fourteen months' arrears "on delivery of
  the one from the Low Ford") and "No." never sent; the daybook: the toll's
  seed (a death a morning since the ford went dark, each with its cause, and
  "Beside some there's only a dash."), the dogs ("Corran" crossed out hardest;
  "Dog." stands), "91 up. Lid down.", the names, "92." "Sorry." Then to Maeca
  ("...He counted me."), to Redcowl ("So that's the man kept my bairns
  alive... Oh, Mam."), or burned; `daybook.to` (a StoryLint seed).
- Maeca's hub after the rope (`maeca.k_*`, only while she's in town): "I was
  at the top."; Ashford is now "The ladder."
- Also: speakers `tolley` (voice `guard`, the gate guard who said "Dawn
  arrivals") and `penhale` (new cast voice); `Waystation.cs` Present hides
  Holloway after the rope and Maeca if held or gone; HOLD_LINES holds all of
  it (`elevenlabs.py`, `A2`).

**To finish slice 1:** a fresh su-lead-max editor-judge on the six scenes and
`k_` hub (against TWIST_OPTIONS §B, TREATMENT §4.5-4.6, bible rule 7, VOICES);
apply its fixes; direct every line (none are directed; Holloway's risen count
wants the dead fx); lock; drop the `A2` holds; `dotnet test`; merge.

**Gaps for other leads (brief them through the main session):** the hole as a
story fight between the two C20 scenes (today the night between is an
ordinary night); the haul (held input) at `haul`/`haul2`; the cut (cinematic)
at `cut`/`run`; "Lay him down" may become a one-foe fight in the road. Not
written yet: the gallows for `held`; a sweep of lines that assume Holloway
alive (folk barks, other hubs); TOLL_SPEC's carrow and cause 12 gate on
`holloway.dead`.

**Act 2 still to write** (plan: `git show 86b97737:docs/handoff/story.md` §3;
TREATMENT §3.3, §5, §7; `docs/cinematics/act2_outline.md` is pre-rewrite):
C27-C28 (Brannoc: "Tell her no." and Nell's boots; the lie route's grey mare,
"That's mine. ...You passed nobody.", his cold hub keyed to a new fact; seed
`brannoc.knew_iron`); C30 and the dawns after the turn (seed `mother.word`);
`scene_still_plain` (TREATMENT §3.3; add `not mother.chisel` to Chid's "The
marker. It's come to me."); C31 (Maeca in his coat counts them in; "the
eleven"); C32 (A's first beat: "Her hands were bad. Chid wrote it for her";
the narrator silent); C21, C24-C26, C29; the bible's §7 beats 3, 4 and 8,
§9-10's boot rows, §11.

## Tools

- Scratch: `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\`
  (keep `s15`-`s18`). `s18\build_c20.py` builds slice 1 and is rerunnable
  (edit the text there and rerun); `s18\showc.py CONV [NODE..]` prints nodes;
  `s18\lib.py` does round-trip-safe JSON edits. Their `WT` path is this
  worktree (`agent-a6bea546976448116`): repoint it if that's gone.
- After any data or direction edit: `python tools/vo/lines.py`, then
  `elevenlabs.py`, `lock.py --check`, `check_ids.py`, the voice tests
  (`python -m unittest tests.test_door tests.test_lock tests.test_lines` in
  tools/vo) and `cd godot/tests && dotnet test` (about 6 minutes, 817 pass).

## Gotchas

- A new scene id needs a `speakers` entry in npcs.json (ContentTests).
- A node's effects apply before its text is chosen (`scene_barred` checks the
  count after its own `add`). Variants fall back to the last one.
- Branch a speaker by choices with exclusive `show`s (`ninety`, `laid`).
- A lock binds words: an edited locked line drops to HOLD. Lock through
  Python (`lock.main`), and check the count.
- test_door fails on a stale manifest: run `lines.py` before the tests.
- A capitalized parenthesis in a person's line is the narrator's; a
  lower-case one becomes an audio tag in that person's take.
- StoryLint fails a fact read but never written, or written but never read
  (unless it's in `Seeds`).
- The context hook: onboarding Act 2 cost about 230k. Read only the sections
  above, and write in one build script.

## The owner's words

- "a powerful epic story with real emotional happenings"; Brannoc "needs to
  hit HARD. so hard."; "the harshest versions are what were aiming for";
  "WHAT THE FUCK kinda moment" (twists A, B, "It takes less than it did").
  Love scenes: B. American spelling; the owner is they/them; the tone is 18+.
