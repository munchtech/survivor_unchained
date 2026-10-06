# Handoff: the story and writing lead (Survivor Unchained)

You are the writer. You own the canon, every word the game says, the story
data and the cinematic scripts, and you sign off voice packets. Read
`docs/team/README.md`, then this page, then `docs/team/story.md` (status and
the staging notes for cinematics).

- **Branch:** `worktree-agent-a38d66ae66583ace1` (the eighth lead). Merge
  `origin/claude/vigilant-galileo-l6jqyx` in first. Commit, push, open no PRs.
- **Tests:** `cd godot/tests && dotnet test` (774 pass). Run them before every
  commit.
- **Commits:** write the message to a file and use `git commit -F`. End it with
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Use British
  spelling.
- **Scripts:** the worktree guard refuses complex bash (heredocs into python,
  variables as commands). Put Python in the scratchpad
  (`.../scratchpad/story7/`) and run `python <abs path>`. In `lib_s7.py`:
  - `load` and `save` round-trip the content JSON (indent 1, CRLF);
  - `node`, `ch` and `v` build dialogue nodes.

  `showc_s7.py CONV [NODE...]` prints a conversation.

## 1. The owner's words

- "a powerful epic story with real emotional happenings. people being
  devastated, elated, or both. shocks and twists, stuff we figured out that was
  obvious."
- "when maeca kills halloway it should be a HOLY SHIT WHAT THE FUCK kinda
  thing."
- Brannoc "needs to hit HARD. so hard."
- On the lie to Brannoc: "we can't get punished from gameplay perspective - he
  just talks to us like he hates us or ignores us".
- On the Kiln Ford: "the harshest versions are what were aiming for."

## 2. The brief, and the decisions (all in `docs/story/TREATMENT.md` §0)

**The brief:** rewrite the approved treatment into the game, act by act:
1. Act 1;
2. Act 2: the rope with the player's hands on it, Holloway at his gate, and
   the woman with the lamp;
3. Act 3: the voice.

After each act, send the main session the key scenes (file paths and a short
summary). The main session starts a fresh editor for each act's draft, whose
notes land in `docs/story/notes/NN_*.md`. Apply the notes.

**The decisions:**
- All four twists.
- The narrator recast as a woman of about sixty, plain and dry.
- Her word for the survivor is "Spark" (not "Wick").
- The lamplings are renamed Stub and Old Gutter.
- Holloway's act is option (b): the lamp in his eyes.
- No boots on Holloway.
- The confession comes mid Act 1, and "tell Maeca" is on the trunk.
- Holloway rises at his gate on the fourth dusk.
- The nod is the game's first choice.
- The lamp-iron is her night lantern.
- The lie to Brannoc costs his warmth only. On that route the truth comes in
  Act 2, with the grey mare, after he sells the irons and the Kiln Ford is lit.
- Love scenes: both versions are on the page for the owner
  (`docs/story/LOVE_SCENES.md`), with the editor's warning beside them. He
  hasn't chosen yet.

## 3. Where things stand

**Act 1 is done (first pass, in the data).** `docs/WRITING_PASS.md` §26 lists
every scene, rule, fact and changed line. `godot/tests/StoryRewriteTests.cs`
holds the rules.

- **Scenes on the trunk.** `Journey.TakeScene` plays them, the overnight rules
  set `scene.morning` and `scene.dusk`, and `scene.now` opens a person's own
  conversation at a node. The scenes are:
  - the gate at dawn;
  - "She's in my count.";
  - the knocking (the confession);
  - "...Did he.";
  - her cup at the gate;
  - Brannoc's dusk call.
- **Brannoc's C07** is reordered, and the road is in `nell.burial_with`.
- **Rook's kind lie**, the grave, the mystery page Home, and Chid's
  `names_write`.
- **The fortune:** `f_ford` and `f_did`, and the readable ledger with line
  twenty-six as "Rook's lodger.".
- **The dawns:** `dawn.voice` and `dawn.word`.
- **"Barefoot" is gone everywhere**, including the voice tools.
- **The calling remarks** are de-duplicated.
- **The bible** has its Act 1 canon updated: §1 (the mother; what she did
  first), §3, §5 (Holloway, Maeca, Brannoc), the third layer, the extremes, and
  the seeds.

**Left in Act 1:**
- **The editor's notes on this draft.** Not started; the main session starts
  them.
- **The love scenes,** once the owner chooses:
  - if A, add `voiced: false` to the narrated nodes in the room;
  - if B, rewrite those nodes per `LOVE_SCENES.md`.
- **C04 B's coat line** ("That's his only coat.") needs a cinematic cue, so it
  waits for the cinematics lead. The other staging notes are on the status
  page.
- **Not yet seen in Godot.** Play the scenes at 1920x1080 when a Godot turn is
  free. The things to watch:
  - Holloway sitting in the south gateway at night (`Waystation.cs` routine,
    `Sit_Floor_Idle` at -3.0, 31.2);
  - the grave interactable;
  - the scenes' timing after the morning page.
- **Bible sections still to rewrite:**
  - §7 Act 2: beat 3 (the letter), beat 4 ("The boots", which becomes the
    rope) and beat 8 (Brannoc's lie route with the mare);
  - §9 and §10's boot rows;
  - §11's romance note.

  Do these with Act 2.

**Act 2 (next).** Nothing is in the data yet. The plan, from the treatment §4
and the editor's notes:
- **C20 (the ground opens).** Holloway goes down drunk and shaking. He counts
  them up the rope: "One. Two." Tam's Pa: "And you took your bloody time,
  CAPTAIN!" Then his first laugh. **The haul** is a held input with no fail
  state: the survivor and Maeca, Ashford's windlass turned round. He hangs a
  body-length below the lip, lit from above, and grins: "Count's right." Maeca
  has made the rope fast round the post. One stroke at the post; the rope goes
  slack in her hands and runs over the lip. No music. "Ninety-two." Only then
  the choices:
  - lover: "You were up.";
  - otherwise she looks at you, and says nothing.

  Then Maeca's one line of (b): "The ones under me weren't dead. Not when he
  shut it." Then Tam: "It started the night the ford went dark." Tolley:
  "...Ten." The town holds her, guards her, or lets her go.
- **C20b.** Three dusks with the gate barred and his stool empty, and the hole
  knocking. On the fourth dusk he is at his gate, lips moving: "...Always
  somebody still out." She lays him down. Whoever opens the gate says "One in."
- **C22 (his table).** Sallow's letter, and his "No.", never sent. The
  daybook:
  - "91 up. Lid down.";
  - the names below the lid, with who each left;
  - "Sorry." once;
  - a page of dog names, crossed out ("Corran" hardest; "Dog." not crossed
    out).

  Lean the route toward taking it to Maeca: "He never counted me."
- **C27 and C28, the lie route.** He sells the irons and the Kiln Ford is lit.
  Then the grey mare comes up the south road: "That's mine. ...You passed
  nobody." From then on he is cold or silent at the forge, and play is
  unchanged. Write his hub variants keyed to a new fact set by that scene.
- **C31.** Build it as a reversal. Maeca wears his coat and counts them in.
- **C32 (Rook's kitchen).** The ring is on the table. "I'll be at the water
  with a lamp." "That week the ford was lit every night. For you." "She was
  your mam, pet." The insert is the player's own blow at the water's edge.
  **The narrator is silent:** no narrator nodes, and no capitalised
  parenthesis (those are voiced by the narrator); lower-case directions only.
  Then Vonnra: "Come down with me."
- **The dawns after Act 2's turn:** "Somebody used to call you something at
  dusk. One short word. It was yours." Then they stop, and the narrator says
  less.
- **Put the Act 2 conversations on HOLD** in `tools/vo/elevenlabs.py`
  (`HOLD_LINES`) until the editor and the owner pass them.

**Act 3 (after).** The voice (§3.4):
- Vonnra reads line twenty-six ("Rook's lodger.") in the same voice as the
  others.
- At C43, "Lamp's lit, Spark." starts where the narrator has always been, then
  goes down into the pale thing.
- "There you are." "I came up with you." "You'd have sat down in the road and
  waited for me."
- The second turn: her voice got quieter because of the player's ember.
- The endings settle her voice: A, "You lie down. I'm here."; B, "It's
  morning, Spark. Go on."; C, her voice drowned out.
- Chid at dawn: "Is it morning?"

## 4. Voice

- `docs/voice/RERECORD.md` lists every changed or new line by character. The
  packets mark changed lines **RE-RECORD**, read from its "Changed" tables
  (`tools/vo/elevenlabs.py rerecord()`). Regenerate with
  `python tools/vo/elevenlabs.py`; it needs `soundfile`, which is installed.
- **Sella and Rook are ready.** Sella's packet had been behind the data: one
  line reworded on 4 October, two takes to rename, two new barks.
- **On HOLD:** Holloway, Brannoc, Maeca, Vonnra, Harlan and the narrator. Write
  their RERECORD sections when you sign them off.
- A changed line with an old placeholder take must lose its index entry
  (`scratchpad/story7/vo_drop_s7.py`), or `VoiceTests` fails.

## 5. Gotchas

- A node's effects apply before its text is chosen.
- Adding a variant shifts the voice ids after it, so tell voice.
- Scenes share one morning slot and one dusk slot, and queue: a rule that sets
  `scene.*` must check that the slot is empty.
- StoryLint: every fact read is written somewhere, and every fact written is
  read or listed as a seed. `brannoc.knew_iron` and `mother.word` are seeds
  for Act 2.
- `holloway.knocking` must not fire once `holloway.confessed` is set.
- The editor's notes are at `docs/story/notes/01_treatment.md`. The letter is
  `docs/story/EDITORIAL_LETTER.md`.

## 6. Read first

1. `docs/story/TREATMENT.md`: §0, then §3 and §4.
2. `docs/story/notes/01_treatment.md`.
3. `docs/WRITING_PASS.md` §26.
4. `docs/team/story.md`.
5. `docs/story/LOVE_SCENES.md`.
6. `docs/voice/RERECORD.md`.
7. `godot/tests/StoryRewriteTests.cs`.
8. `docs/cinematics/act2_outline.md` (to be rewritten to the treatment).
