# Handoff: the story and writing lead (Survivor Unchained)

You are the writer (su-lead-max). You own the canon, every word the game says,
the story data and the cinematic scripts, and you sign off voice packets.

## Now (5 November, S1 the story rework, branch `story-s1`): Act 1 in data, beats 6/7/8/11 in; HANDOFF READY story-s1@4f554a619 (writer 2 at ~300k; this commit follows)

**The pick (the owner, 5 Nov:
"Go, defaults."):** ending B retired, three endings (she lies down / Corvane
lies down / she carries it home); the name is **Corvane**; Corvane killable
in Act 1 and getting up on screen; "He has never burned." retired; Holloway
risen as Ashford's commander waits for Act 2's brief. The proposal was
PROPOSAL READY story-s1@9fd41e6e0, editor PASS WITH FIXES applied.

**HANDOFF READY story-s1@4f554a619** (writer 2, Fable, at ~300k; the
owner's pick stands as the paragraph above has it). Slice 1 DONE
(dba76d016). **Slice 2, in data so far:** (1) beat 6 at 567a1477e; (2)
beats 7, 8 and 11 at 4f554a619. Integration merged at e2bdeed4d (the
junction removed and remade). The story test subset (StoryLint,
StoryRewrite, Quest, Cinema, Verge, StoryNight) was launched at the
handoff: its tail is in `scratchpad\story_s1\tests_story.txt` (backed up to
`survivorsunchained_inputs\scratch_story_s1\`); if it did not finish, run it
first. `tools/vo/lines.py` and the locks have NOT been run on the new lines
(step 7). Nothing is pushed since dba76d016 until this handoff's push.

**What is in, by node (so nothing is re-derived):**
- *Beat 6, Vonnra's tale* (`vonnra`): rule `vonnra.sends` (day >= 3,
  `prologue.done`, met, vault `seen`, not told) sets `vonnra.sent` with the
  violet-note report; her entry at dusk/night goes to `chains`; nodes
  `chains, keeper, bleed, ford_tale, burn, order, six, office, office_more,
  cost, why, dont, key, jessop_in, tale_end` (sets `vonnra.told`, journal
  `vault.vonnra_told`, rel +10/+10); by day the hub says "After dark";
  `vault` has two told-variants (key in hand / the dead man's hand). Her
  lie is the names only: every mechanism she gives is bible rule 1-5. She
  quotes the office's end and withholds its last sentence ("Let the one who
  got up go down, and carry it home"): the ledger's own words "Got up." are
  the office's subject, for the reader who puts them together (beat 13).
- *Beats 7-8, the door night* (`door_night`, a plain conversation, not
  `cin_`, so CinemaTests asks no cues; the P6 boss and the P9 C13 rework play
  its nodes): `go_home` -> `wrong` | `ask_her` -> `lie_down` ("(Raise your
  weapon.)" exits into the fight; "(Lower your weapon, and go.)" -> `go`, the
  night let go, he says he'll see her in the morning); `gets_up` (the
  narrator's one line, held on his body); `gone` (she turns back from the
  waking sigil); `heart` and `ranks` (C13's end: he stays down, the heart to
  her hand and out through it, the dead step back and stand). The singer
  under the stair is sound only: no node, by the editor's rule.
  `cin_behind_the_door.redi` (the hand at the gate) is retired when P9
  reworks the timeline; until then it stays, with its lock and cue.
- *Beat 11, the morning after:* `chid.cb_opened_vault` (the scar, the kettle,
  "Sit. The good stool."), `chid.cb_vault2` ("(He pours.) ...Don't." to
  "Which carter, Corvane?"), new `chid.cb_vault_up`; a `chid.carried_chid`
  variant when she fell that night (`corvane.rose`, "A carter, I expect.
  ...Don't ask me anything this morning. Please."); `vonnra.cb_opened_vault`
  ("What stood in the door?"), `vonnra.cb_vault2` ("His kind live off the
  leak. He will do that again."; "Two. Five, and the valley sleeps." on
  `chain.two`); `vonnra.cb_vault3` survives.
- *Facts:* rules `corvane.rose` (history `opened_vault` or quest vault
  `shut`) and `chain.two` (fact `vault.opened`, the fight's OnWin), read by
  the lines above. When P6 builds the boss it sets `corvane.rose` at the
  kill itself and must not set `shut` on a phase-1 loss.

**Next, in order (one commit each; the design is decided, write the words):**
(3) beat 10 `scene_bed`: a conversation like `scene_his_cup` (speakers
narrator / holloway / maeca), queued by a rule `holloway.bed` into
`scene.dusk` when `chain.two` and no `scene.dusk` exists; the narrator: the
south gate unbarred at dusk for the first time, his stool, no tally in his
hand; Holloway in his own counts: "Eleven in. Nobody out. Third night
running. ...I'd had it down I'd go on this stool. (He looks at the gatehouse
cot.) Might go in a bed."; Maeca fills his cup and says nothing; the scene
sets `holloway.bed_seen` (add it to StoryLint's `Seeds`: Act 2's rope reads
it). Never "Count's right." (the built gate-dawn line and bark keep theirs).
Beat 5: a once rule `ford.ditch` (day >= 3, `prologue.done`): "Nobody stood
in the ditch on the Low Ford road last night, or the night before. The Watch
has stopped sending a man down to look."; three Holloway `said` night barks
in `npcs.json` (`"night": true`) for days 2, 3, 4 ("Eleven in. Nobody out.",
"Eleven in. Second night.", "Eleven in. Nobody out. I've stopped writing it
down."), keyed `day` and not `chain.two`.
(4) beat 9: two once rules on `chain.two`, `hollow.healed` (not
`stream.clear`: the stream running clear and the scar on Wolf Hollow closed
over in a night, wolves drinking at it, the Dig's hill silent) and
`hollow.healed_clear` (`stream.clear` already: the scar only); Wenna's
callback `cb_clean` on `chain.two`: "It's clean. I don't know why it's
clean." (variant when she cleaned it herself, `beasts.outcome` cured: "It's
cleaner than I made it. I don't know why."). The C15 film is P9's (below).
(5) beat 12: `tam.again` variant on `chain.two`: "It knocked. Louder. Pa says
it's the ground settling. Things don't settle UP."; Wenna's hub variant on
`chain.two`: "I've the masks out again. Don't ask me why. I don't know why."
Both read `chain.two`; neither explains it.
(6) beat 13: `chid.office` gains a journal entry `vault.office_end` (the
page, in the keepers' words, the whole of it: "Is it morning? / Not yet. /
When the seven are loosed, and a lamp lit at dark still burns at first
light, it is morning. Let the one who got up go down, and carry it home.");
beat 14: a once rule `toll.baking` (`player.deaths` >= 1, `prologue.done`):
"Up the street, nobody is baking." (re-key it on `toll.rises` when the
toll's scripted fall is built, TOLL_SPEC section 3).
(7) `python tools/vo/lines.py`; lock through Python: prefixes
`dlg.vonnra.chains dlg.vonnra.keeper dlg.vonnra.bleed dlg.vonnra.ford_tale
dlg.vonnra.burn dlg.vonnra.order dlg.vonnra.six dlg.vonnra.office
dlg.vonnra.office_more dlg.vonnra.cost dlg.vonnra.why dlg.vonnra.dont
dlg.vonnra.key dlg.vonnra.jessop_in dlg.vonnra.tale_end dlg.door_night.
dlg.chid.cb_opened_vault dlg.chid.cb_vault2 dlg.chid.cb_vault_up
dlg.chid.carried_chid dlg.vonnra.cb_opened_vault dlg.vonnra.cb_vault2
dlg.vonnra.vault dlg.vonnra.hub` plus the new scene and rule lines (`say.`
ids: check `lines.py --report`); remove the two gone locks
(`dlg.cin_drowned_fire.prints.0`, `say.93b63298edc0`); `lock.py --check`
exit 0; `python -m unittest tests.test_lock tests.test_lines` in tools/vo;
tests in `StoryRewriteTests.cs`: the tale ends on `vonnra.told` and never
says "vessel"; `door_night.gets_up` is exactly "He gets up."; `scene_bed`
never says "Count's right."; StoryLint seeds. Full `dotnet test` before MR.
(8) a fresh Haiku `su-lead-max` editor at xhigh on `git diff dba76d016..HEAD`
(brief from `docs/handoff/story_editor.md` 1-2 and 4, PLAN.md as the canon,
the WTF question on beat 7); PASS WITH FIXES applied. (9) `MR READY
story-s1@<sha>` here and to main: the editor's verdict in two lines, the
counts (survived / rewritten / new / retired), re-locks, cost.

**Line items for other leads (PLAN section 6), each a paragraph a lead can
start from:**
- *P6, the combat lead: Corvane in the doorway.* Phase 1 of story night
  `vault_opened`, before the door opens: his kit (a keeper's lamp, violet
  glass; two hundred years of ember) on the existing NPC model; the door's
  forecourt is the arena. He stands in the way and does not strike first:
  `door_night.go_home` plays on arrival, `wrong`/`ask_her` by the player's
  choice, then `lie_down`; "(Raise your weapon.)" starts the fight, "(Lower
  your weapon, and go.)" lets the night go (`go`). On the kill: hold on his
  body, play `gets_up` (narrator), then the sigil wakes (C13's door shots) and
  when she turns back `gone`; no boss-phase bar, no second health bar. Set
  `corvane.rose` at the kill; a phase-1 loss sets no quest entry `shut`
  (he carries her home: `chid.carried_chid`'s `corvane.rose` variant). If his
  model can't carry a boss at the play camera, P3 remakes him with the
  Warden. ~0.3-0.5M.
- *P9, the cinematics lead: C13 reworked.* Two phases on the built pipeline:
  the doorway (above, with the P6 hooks) and the stair. The end changes:
  `redi` and the hand at the gate go; after `nondum` and the fight the
  Barrow Lord goes down and stays down (`door_night.heart`: the heart comes
  up violet to her hand, warm then not, and goes down through it; the stone
  is only a stone), then, far under the stair, the Warden's call in a
  woman's voice, sound only, no subtitle, no narrator line, then
  `door_night.ranks` (the dead step back and stand), then the reckoning
  (its words in `StoryFights.cs` line 133 change to: "The dead stand on the
  stair in their ranks, and let you go. The stone in your hand is cold."). Keep
  shot 4 (Jessop with the violet lantern, Act 3's plant). The `door_night`
  nodes may move into `cin_behind_the_door` when the cues exist; re-lock
  them then. ~80-120k.
- *P9: C15 "The Stream Runs Clear".* New, ~20 s, over the real Verge in its
  `stream.clear` state at dawn: the scar on Wolf Hollow closed, wolves
  drinking, the Dig's hill silent; Wenna's line from beat 9 over the last
  shot. Plays the morning `hollow.healed` fires. ~50-80k.

**Scratch (`scratchpad\story_s1\`, backed up to
`survivorsunchained_inputs\scratch_story_s1\`):** `lib.py` (round-trip-safe
load/save of the content JSON: dialogue.json is LF, rules/quests/npcs are
CRLF; `node`, `choice`, `set_text_variant`), `dumpc.py <dialogue.json> conv
[--nodes a,b]` (a compact text dump of a conversation), `beat6.py`,
`beat7.py` (the two scripts that made the commits, as the pattern for 3-6).
Node ids and `once` keys are per conversation and must not collide
(`vonnra.jessop` and `vonnra.ford` were taken: hence `jessop_in`,
`ford_tale`). Text variants are checked in order: the specific `when` first.

**Slice 1, DONE (a `su-worker`, commit dba76d016 on story-s1):** every
player-facing "Chid" -> "Corvane" with the id `chid` kept (dialogue.json 28
lines, rules.json 6, folk.json 5, quests.json 3, npcs.json 2,
archetypes.json 1, items.json 1, `tools/vo/cast.json` display name 1, two
test assertions in `VergeTests.cs` and `DayClockTests.cs`; one sentence each
in STORY_BIBLE sections 3 and 5, VOICES and VO_CAST); SB00's L2 "and bound it
there with seven chains, in the dark." in dialogue.json and the sb00 script;
15 locks re-locked, `locked.json` 527 before and after; suite 1534/0/10.
Left on purpose: C# comments and test method names still say Chid (not
player-facing); `cast.json` `ref_text` "I'm Chid" (the audio reference
script; change it only with a re-record). **Owed to the successor's lock
pass:** `lock.py --check` reports two locks "gone" that predate S1
(`dlg.cin_drowned_fire.prints.0`, `say.93b63298edc0`): remove them as retired
lines. The tools note in "Tools" below is stale: `tests.test_door` no longer
exists (it left with the romances); run `tests.test_lock tests.test_lines`.

**Slice 2's original step list** is superseded by the state and the next steps above.

Writer = Fable (S1, `docs/team/hook/S1_story_rework.md`); editor = a Haiku
`su-lead-max` at xhigh (agent `ad7c24ae2324594d3`, ~136k of its 150k used:
spawn a fresh one for the data pass, from `docs/handoff/story_editor.md`
sections 1-2 and 4, with PLAN.md as the canon).

**What is done:** `docs/story/PLAN.md`, the proposal: the owner's seven-chains
draft (`docs/story/REWORK_EMBER_WATCH.md`) put on the bible's existing
seven-link chain, hearts and keepers (renames and re-aims, not a new world);
what survives and what is retired item by item; the four acts at a paragraph
each with the WTF moments marked; Act 1 beat by beat (chains 1 and 2: the Low
Ford as built, the Barrow behind the Verge's sealed door) with every plant for
Acts 2-4; the cost and the pipelines. The editor's one pass: PASS WITH FIXES,
distance medium, all fixes applied (commit 9fd41e6e0's message lists them).
Nothing is in data yet.

**Waiting on the owner (PLAN section 7):** (1) ending B "Break the Chain"
retired for "Corvane takes her place"; (2) the name: Corvane (default),
Caedmon or Caddock; (3) Corvane killable in Act 1 and getting up on screen;
(4) "He has never burned." retired. "Not yet: Chid made you" is KEPT (he held
her hand not knowing what she was): nothing to decide. Holloway risen as the
Act 2 commander is proposed for Act 2's brief, not now.

**After the pick, Act 1 in data (PLAN section 4, beats 5-14):**
- `godot/data/content/dialogue.json`: the NPC id `chid` stays; the display
  name and every spoken "Chid" become the chosen name (a worker's job: list
  the lines first with a grep, since each changed line drops its lock to HOLD
  and must be re-locked unchanged in meaning); new conversations `vonnra`
  nodes for the tale (`chains`...), `scene_bed` (Holloway), Corvane's door
  barks and the morning after (`chid.rose`...), Tam's and Wenna's lines;
  `cb_vault2` and `chid.first` variants; `chid.office` shows the last page.
- `godot/data/content/rules.json`: the quiet-ford report, the stream report,
  "Up the street, nobody is baking."; `quests.json`: the office's page.
- Facts: `chain.two`, `corvane.rose`, `vonnra.told` (StoryLint: written and
  read); tests in `godot/tests/StoryRewriteTests.cs`, `StoryLint.cs`,
  `CinemaTests.cs`.
- Story night `vault_opened` gains phase 1 (Corvane) before the Barrow Lord;
  the C13 end changes (the heart lifted, the singer as sound only): cue data
  for the cinematics lead (P9), the boss for the combat lead (P6): both are
  line items in PLAN section 6 with owners, not the writer's.
- SB00 L2 (`sb_stay_where_they_reach.chained`): "and bound it there with seven
  chains, in the dark." (P10: the line only; the plate stands).
- Locks: `python tools/vo/lines.py`, then `lock.py` through Python (prefixes
  match by `startswith`); the count today is 527 (`tools/vo/locked.json`
  `lines`), not the brief's 424; ~495 should survive untouched.
- Tests green (`dotnet test godot/tests/Tests.csproj`) before `MR READY`.

**Scratch:** `scratchpad\story_s1\` (`dump.py` prints a conversation's
nodes as text; commit messages). Back it up to
`survivorsunchained_inputs\scratch_story_s1\` and clear only that subfolder.

**Gotchas:** read PLAN first, then TREATMENT section 0 (still the canon for
the town); `vonnra.f_did` and C09 stay word for word (the editor: the fortune
must not explain its own knife); never "Count's right." before the rope; the
narrator never says what it means ("He gets up." is the model); the junction
rule before any merge of integration (README, DANGER).

## Earlier (29 October, Story 13, branch `story-wtf`): list DONE, MR1 + MR2 sent

The owner's 28 October direction (romances out, the reveal, the WTF pass) and
his notes (reveal A with "where you left it" reworded; the C01 empty-bedroll
opening) are done. Writer = Fable (xhigh); the editor is a Haiku `su-lead-max`
at xhigh the writer keeps alive across a pass and talks to directly (the owner:
"the writer and editor may talk to each other"); main hears only owner
decisions, canon proposals, blockers, MR/HANDOFF.

**1. Romances out: DONE** (data 1dddf45e; follow-through a52d452c: tests, the
door machinery out of `tools/vo`, `love_b.json` -> `late_nights.json`, 39 gone
locks removed, 13 rewrites re-locked, bible section 11 "Affection, not romance",
`LOVE_SCENES.md` retired to `docs/story/notes/history_love_scenes_b.md`).
**2. Reveal A: DONE** (60bcf83e). C04 `cin_first_light.face`: *"You try to call
up your mother's voice, and it is not there. Not faint: gone. Her face comes at
once: the line between her brows, the thread she bit instead of cutting."*;
`rules.json` `dawn.face` (was `dawn.voice`): *"Her face is going the way her
voice went. The brows first. You still have the word."*; the narrator never says
the call before C43 (`StoryRewriteTests.Her_mothers_voice_is_gone...`); docs
follow (TREATMENT section 2 and 3.4; bible; C04 doc + shoot; act 3 outline;
`NARRATOR_REVEAL_OPTIONS.md` DECIDED). The editor's sweep of narrator figures
that don't resolve: greymuzzle.ally/again, sella.free_stairs, the Pell rule.
Kept on purpose: maeca.watch_only's frost line; sella.stairs "Coins, then your
hand" (a client led to a paid room; up there is sleep). No re-records: every
narrator take is a placeholder; the stale C04 take is owed to the next
placeholder batch (GPU, `tools/vo/placeholders.py`).
**3. The WTF pass: DONE, the owner said yes to all three** ("Yes to P1, P2 and
P3."; the page: `docs/story/notes/story13_canon_proposals.md`). P1 in data:
`rook.mother_word` (Rook gives the words and the name day one; mother2's choices
moved to it). P2 in data: journal `home.letter` ("Come home by the Low Ford.").
P3 in TREATMENT: section 4.5 step 7 (nobody says a number; "Tolley's lips move,
and stop"), section 7's Act 2 rows, section 0's Maeca line (C22). Bible section
1 and 3.3 carry P1 and P2. Act 2 is not in the data; the next writer builds C20
and C20b from the treatment as now written.
**4. The C01 opening: DONE as a beat** (1fcf97d0): `docs/cinematics/c01_opening_beat.md`
for Cinematics 8 (bedroll, shadow, prints, rising, play; shots 2-3 out, 4-6
folded; the letter and the background item to C04 A; no data change).
**MRs:** MR1 at 1fcf97d0 (items 1, 2, 4); MR2 at the branch head (P1, P2, P3,
the page, this handoff). Tests 1285/0/10 on both.

**Owed elsewhere (routed to main, 29 October):** the toll (`TOLL_SPEC.md`) has no
data presence beyond `Journey.Day.RiseAgain`: a combat/story-code slot; the
drowned woman lifting a dead lamp at the ford isn't staged in `Prologue.cs`;
Cinematics 8: the C04 A letter insert with its legible line, the lamp prop +
`cin_first_light.lamp_out` node + cue together (text in `c04_first_light.md`;
`CinemaTests` fails a node without its cue), C04 A7 holds on her face.

**Next for a writer, when a slot opens:** Act 2's data from TREATMENT sections
3.2, 3.3, 4 (C20, C20b, C22, C32) and Act 3's stair (C41-C43) with reveal A's
first-person lines; "Up the street, nobody is baking." and the morning news pool
once the toll is built. Read TREATMENT section 0 first: it overrules the rest.

The editor: agent `a16f8f7e8fda254d8` (near its 260k budget: spawn a fresh one
from `docs/handoff/story_editor.md` with the scoreboard from the canon page).
Scratch (`canon_edit.py`, `on_yes.py`) backed up to
`survivorsunchained_inputs\scratch_story13\`; the scratchpad subfolder cleared.

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
