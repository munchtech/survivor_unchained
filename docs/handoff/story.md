# Handoff: the story and writing lead (Survivor Unchained)

You are the writer (su-lead-max). You own the canon, every word the game says,
the story data and the cinematic scripts, and you sign off voice packets.

## Now (28 October, Story 12, branch `story-wtf`): item 1 half done, item 2 at the owner's gate

The owner (28 Oct, verbatim in the coordinator's `story_brief.md`): remove the love
scenes and romances (Sella stays who she is; she likes us), make the narrator-mother
reveal actually reveal, then the WTF pass. Writer = Fable (xhigh); the editor is a
Haiku `su-lead-max` at xhigh that the writer spawns (it sends notes, never rewrites).
**Spawn guard:** this writer's brief lacked `Spawning: allowed`, so no helper could
be spawned; the successor's brief must carry that line (or main sends it).

**1. Romances out, DATA DONE (1dddf45e), follow-through NOT done.**
`godot/data/content/dialogue.json`: 26 nodes removed, 29 rewritten (the list is in
the commit and in `docs/story/notes/story12_item1_followthrough.md`). Sella keeps the
blue room, her trade and the paid sleep (`rest_night` -> `stairs` -> `stairs_say` ->
`rest_bed` -> `rest_dark` -> `rest_morning`); her free night is now the night she
sits with you (`free_door` -> `free_sit`, new `free_what`, `free_m_who`); Maeca's
Blind is the watch night (`watch_only` -> `blind_dark`, nights 1-3 by the fire,
`maeca.blind_nights` replaces `maeca.lover` everywhere, incl. greymuzzle); the
triangle `say_sella*` is gone; Keegan's `dinner`/`supper_hand` and Rav's
`back_room_kiss` are gone. **Tests are RED until the follow-through lands:**
`docs/story/notes/story12_item1_followthrough.md` is the exact spec (tests, the door
machinery in `tools/vo/elevenlabs.py`, `import_takes.py`, `tests/test_door.py`,
direction prune + `love_b.json` rename, locks prune/re-lock, RERECORD, cast.json,
TREATMENT, the bible's §11 (replacement text included), cinematics docs, items docs,
LOVE_SCENES.md retired to `docs/story/notes/history_love_scenes_b.md`). Give it to
one `su-worker` (Sonnet, medium), review the diff, run `dotnet test`, commit.

**2. The reveal: options page written,** `docs/story/NARRATOR_REVEAL_OPTIONS.md`
(A, the flip, recommended; B, a false voice). Nothing of the narrator is recorded
(placeholders only; the C04 face take is already stale), so the change costs no
re-record. On the owner's pick: edit `cin_first_light.face`, `rules.json`
`dawn.voice`, `StoryRewriteTests.Her_mothers_word_is_Spark_and_the_dawns_take_it_away`,
TREATMENT §2 and §3.4 plants 3 and 6; re-lock; one note to Cinematics (C04 A7).

**3. The WTF pass: not started.** Plan: the editor scores eight beats (You did this;
Ninety-two; the woman with the lamp; the voice; It takes less than it did; Not yet;
Count's right; the act endings) on "would a player say WTF out loud", I sharpen the
low scorers at the line level, and bring at most three canon proposals as one page
via main. Read TWIST_WTF §1, TWIST_OPTIONS §A-B, TREATMENT §3 and §7 by section.

Scratch for this session: coordinator scratchpad `story12\` (dump.py prints every
conversation to `out\<conv>.txt`, `--full` for whole texts; `item1_edit.py` is the
data edit, re-runnable only against ddf7c6ee).

## Earlier (19 October, the storybook writer, branch `story-lore`): DONE, merged

The owner (18 Oct, OWNER_NOTES top two bullets): a storybook lore intro before
C01 that ends in drowning into the wake, and a tutorial that teaches ember plainly
with freeze-frame callouts. Both written, edited once and fixed. Docs only.
- **SB00 "Stay Where They Reach"** (`docs/story/storybook/sb00_stay_where_they_reach.md`):
  11 plates, about 89 s, 9 new lines (144 words). The teller is an old Watchman in
  the dead Watchman's voice (`watchman`, Corran), **not the narrator** (VOICES:
  present tense, never meaning, no winter's tale; her "Your bedroll..." stays the
  first narrated words). It plays between creation and C01; C01 starts at shot 1
  without its water sound (C01's "In" notes it). It reuses `cin_none_cross.call`.
- **Tutorial copy** (`docs/story/TUTORIAL_COPY.md`): the Ember explanation (7 lines
  across the night, "lends"/"until dawn"/"first light"), F1-F13 with stage,
  arrow target and kind (freeze or arrow only), and a `lore.ember` journal line.
- **Editor (max, a04bd222): PASS WITH FIXES, all applied.** The worst: the Warden's
  lamp never touches the water (P10), nobody goes in at the Legion's door (C13), no
  wader in P7, no reins girl in P8, no whole keeper. One deviation: L4 keeps
  "Where it lies thick" (ember makes the dead rise) and only un-stacks it. Its C43
  aside ("Dannet, over and over" in the Watchman's voice) was cut from the script;
  it's an idea for Act 3, not decided. Bible §1 now says the town tells the
  Legion's tale; C01's stale narrator casting line is fixed.
- **Next, not this writer's:** the storybook format and look (a `su-lead-max` lead),
  the illustrations, the score's motif (the evening call's tune), the Watchman's VO
  (lines.py, then lock), and the teaching pass (experience director + UI design).

## Where it stands (11 October, writer 15, branch `story/marker-and-locks`)

- **Love scenes B: the editor-judge's 15 fixes are in** (e3e33108; verdict
  `<scratch>\s17\verdict_b.md`), its six kept choices kept. Two more found on
  the way: `stairs_rules.1` (the first night's rules) and `rest_bed.0` (the
  paid sleep) were on the dark screen with daylight directions; both are
  directed for the dark room now (words unchanged).
- **Locked: the blue room and the Blind, whole** (566 locks, 0 broken):
  `lock_b.py` (B, the room's other lines, free_stairs re-locked) and
  `lock_rest.py` (stairs_rules.1, stairs_say.0-2, blind_morning.0).
  `HOLD_LINES` is down to Keegan's kenning. Recordable now: every Sella and
  Maeca line in those scenes, and the narrator's bolt (one take, which also
  serves free_sleep_bed). Nothing else of the narrator's behind the door is
  ever recordable.
- **The door guard, both holes closed:** `elevenlabs.py` `BOLT` (the exemption
  is the exact sentence, not the ids; a bolt line without segments is held);
  `tools/vo/tests/test_door.py` checks `lines.merge(lines.build())`, fails on
  a stale manifest.json and walks next/goto from the three roots;
  `StoryRewriteTests.The_narrator_stops_at_the_door` matches the bolt exactly
  and walks the graph against its hand list. Maeca's lines can't say
  "barefoot" again (`Maeca_is_just_Maeca`).
- **Fix-check judge: PASS WITH FIXES, all four applied** (520b2580, and the
  C# dedupe in e570648d; `<scratch>\s17\verdict_fixcheck.md`): RERECORD says
  the bolt is the narrator's one line behind the door; both door tests start
  from rest_bed too and assert the four ways in; `import_takes.py` refuses a
  narrator take behind the door; the C# aside rule is lines.py's.
- **Integration merged in** (f8d595f6), 795 tests pass, pushed; the main
  session is asked to merge.

## Next: Act 2

Nothing of Act 2 is in the data. Read before writing:
1. The plan: `git show 86b97737:docs/handoff/story.md`, section 3, "Act 2
   (next)" (C20, C20b, C22, C27-C28, C31, C32, the dawns after the turn).
2. TREATMENT §4.5-4.6 (C20, the kill, and its aftermath).
3. The approved twists, layered on that plan:
   - **B, "Count's right"** (TWIST_OPTIONS §B, 6 short beats): he saw her face
     under the lid. C20: he grins up at Maeca, "Count's right.", and climbs
     into her knife. C20b, the fourth dusk: close, the survivor hears him
     count "...Ninety. Ninety-one. ...Ninety-two." before he lifts his hands;
     "One in." C22: "92." with no name, and "Sorry."; taken to Maeca, the
     planned "He never counted me." becomes "...He counted me."
   - **A, "Not yet"** (TWIST_OPTIONS §A): its first beat is C32, Rook's
     kitchen ("Her hands were bad. Chid wrote it for her..."); the rest is
     Act 3.
   - **"It takes less than it did"** (TWIST_WTF §1): revealed at C41 (Act 3).
     In Act 2 its seeds go on: a morning after a rise gets a gentle death with
     no cause; other mornings get a cause. The code is TOLL_SPEC's (waits for
     a code lead).

How a scene plays: a trunk scene is a conversation (`scene_*` in
dialogue.json) that an overnight rule in rules.json sets as `scene.morning`
or `scene.dusk` (rules 62-66: `holloway.waited` to `maeca.cup`), and
`Journey.TakeScene` (Journey.Day.cs) plays it. C20 is "the night after the
fortune": key its rule to the fortune's fact. Not the writer's to build: the
hole as a story fight, the haul (a held input with no fail state, Ashford's
windlass turned round) and the cut (cinematics). Write the text and the shot
script, and brief those leads through the main session. Put Act 2's
conversations on HOLD in `HOLD_LINES` until the editor and the owner pass
them. With Act 2: the bible's §7 beats 3, 4 and 8, the boot rows in §9-10,
and §11's romance note. When `scene_still_plain` is built, add `not
mother.chisel` to Chid's hub choice "The marker. It's come to me."
(TREATMENT §3.3).

## Tools

- Scratch: `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\`
  (keep `s15`, `s16`, `s17`). `s15\showc.py CONV [NODE..]` prints nodes;
  `s15\lib.py` does round-trip-safe JSON edits (`load`, `save`,
  `replace_text`, which asserts the old text). `s17\build_b.py` holds B's
  directions as a SPEC (edit it and rerun; it asserts the acted words and
  moves old entries out of the other direction files); `s17\fix3.py` and
  `spec_fix*.py` are this session's edits.
- After any data or direction edit: `python tools/vo/lines.py`, then
  `elevenlabs.py`, `lock.py --check`, `check_ids.py`, the voice tests
  (`python -m unittest tests.test_door tests.test_lock tests.test_lines` in
  tools/vo; `test_import_takes` needs librosa, which isn't installed here) and
  `cd godot/tests && dotnet test` (about 4 minutes, 795 pass).

## Gotchas

- A lock binds words: an edited locked line drops to HOLD. Lock through
  Python (`lock.main`), and check the count (prefixes match by `startswith`).
- test_door fails on a stale manifest: run `lines.py` before the tests.
- Direction files load in sorted order and later ones win; a direction's
  `segments` replaces the line's (which is why test_door checks
  `merge(build())`).
- A capitalized parenthesis in a person's line is the narrator's; a
  lower-case one becomes an audio tag in that person's take. A narrator aside
  always opens "[quietly]"; the bolt is listed under free_bolt's own
  direction, so it's played level.
- StoryLint fails a fact read but never written (why the chisel guard waits).
- The context hook: B's fixes cost little; reading cost a lot. Act 2 needs
  the twists read first, by section.

## The owner's words

- "a powerful epic story with real emotional happenings"; Brannoc "needs to
  hit HARD. so hard."; "the harshest versions are what were aiming for";
  "WHAT THE FUCK kinda moment" (twists A, B, "It takes less than it did").
  Love scenes: B. American spelling; the owner is they/them; the tone is 18+.

## Read first

This page; the Act 2 plan (above, 1-3), by section; LOVE_SCENES.md only if
B comes back.
