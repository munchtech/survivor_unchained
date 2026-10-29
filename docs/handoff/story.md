# Handoff: the story and writing lead (Survivor Unchained)

You are the writer (su-lead-max). You own the canon, every word the game says,
the story data and the cinematic scripts, and you sign off voice packets.

## Now (29 October, Story 13, branch `story-wtf`): list done, MR1 sent, one page at the owner's gate

The owner's 28 October direction (romances out, the reveal, the WTF pass) and
his 28 October notes (reveal A with "where you left it" reworded; the C01
empty-bedroll opening) are all done or at his gate. Writer = Fable (xhigh); the
editor is a Haiku `su-lead-max` at xhigh that the writer keeps alive across the
pass and talks to directly (the owner: "the writer and editor may talk to each
other"); main hears only owner decisions, canon proposals, blockers, MR/HANDOFF.

**1. Romances out: DONE** (data 1dddf45e; follow-through a52d452c: tests, the
door machinery out of `tools/vo`, `love_b.json` -> `late_nights.json`, 39 gone
locks removed and 13 rewrites re-locked, bible §11 "Affection, not romance",
`LOVE_SCENES.md` retired to `docs/story/notes/history_love_scenes_b.md`).
**2. Reveal A: DONE** (60bcf83e). C04 `cin_first_light.face`: *"You try to call
up your mother's voice, and it is not there. Not faint: gone. Her face comes at
once: the line between her brows, the thread she bit instead of cutting."*;
`rules.json` `dawn.face` (was `dawn.voice`): *"Her face is going the way her
voice went. The brows first. You still have the word."*; the narrator never says
the call before C43 (`StoryRewriteTests.Her_mothers_voice_is_gone...`); the
docs follow (TREATMENT §2, §3.4; bible; C04 doc + shoot; act 3 outline;
`NARRATOR_REVEAL_OPTIONS.md` marked DECIDED). The editor's sweep of narrator
figures that don't resolve: greymuzzle.ally/again, sella.free_stairs, the Pell
rule. Kept on purpose: maeca.watch_only's frost line, sella.stairs' "Coins,
then your hand" (she leads a client to a paid room; up there is sleep). No
re-records: every narrator take is a placeholder; the stale C04 take is owed to
the next placeholder batch (GPU, `tools/vo/placeholders.py`).
**4. The C01 opening: DONE as a beat** (1fcf97d0): `docs/cinematics/c01_opening_beat.md`
for Cinematics 8 (bedroll, shadow, prints, rising, play; shots 2-3 out, 4-6
folded; the letter and the background item to C04 A; no data change).
**MR1 READY story-wtf@1fcf97d0** sent to main (tests 1285/0/10).

**3. The WTF pass: the page is written,** `docs/story/notes/story13_canon_proposals.md`
(the editor's scores 5-8; P1 Rook gives the word day one, `rook.mother_word`;
P2 the letter keeps "Come home by the Low Ford.", journal entry `home.letter`;
P3 the kill and the count split, C20 grin only, C20b the count). P1 and P2 are
DRAFTED IN THE DATA on the branch head and are NOT in MR1. The dropped-lamp
plant (`lamp_out`, text in `c04_first_light.md`) waits for Cinematics 8 to add
prop, node and cue together (`CinemaTests` fails a node without its cue). On the
owner's yes: commit stands, MR2; write P1 into the bible §1 (one sentence) and
P2 into §3.3's plants; write P3 into TREATMENT §4.5 step 7 ("Tolley's lips move,
and stop"), §4.6 (Maeca's "...He counted me." to C22) and §7's two Act 2 rows,
then have the editor read §4.5-4.6 once. On a no: `git revert` the P1/P2 commit
(the test change in `StoryRewriteTests` line 380 goes with it).
**Routed, unowned (tell main if not yet routed):** the toll (`TOLL_SPEC.md`) has
no data presence beyond `Journey.Day.RiseAgain`; the drowned woman lifting a
dead lamp at the ford isn't staged in `Prologue.cs`; the C04 A lamp prop +
`lamp_out` node + cue (Cinematics 8); the C04 A letter insert with the legible line.

The editor: agent `a16f8f7e8fda254d8` (budget raised to 260k; near it: spawn a
fresh one from `docs/handoff/story_editor.md` with the scoreboard pasted in).
Scratch: coordinator scratchpad `story13\` (`canon_edit.py`, the P1/P2/lamp
data edit, re-runnable only against 1fcf97d0); backed up to
`survivorsunchained_inputs\scratch_story13\` at handoff.

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
