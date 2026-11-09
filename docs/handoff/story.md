# Handoff: the story and writing lead (Survivor Unchained)

You are the writer (su-lead-max). You own the canon, every word the game says,
the story data and the cinematic scripts, and you sign off voice packets.

**For the next writer (P6 combat, 5 Nov):**
- A loss to Corvane in the door night's phase 1 now sets the new fact `corvane.carried`. It sets no `corvane.rose` (that still means he got up after she killed him) and no vault `shut`.
- `chid.carried_chid`'s first variant now keys on `corvane.rose` OR `corvane.carried` (the condition only; no text changed).
- Two unvoiced result-screen lines are the combat lead's drafts, in `logic/Play/Story/Corvane.cs` (`Doorway.WalkAway`, `Doorway.Carried`). Amend them at will:
  - the walk away: "You go back down the hill the way you came. Behind you the violet lamp does not move."
  - the phase-1 loss: "The last thing you know is violet light, held low, and being carried, carefully, a long way."

## Now (5 November, S1 the story rework, branch `story-s1`): Act 1 in data, beats 5-14 in; MR READY story-s1@88f52de28 (writer 3)

**The pick (the owner, 5 Nov:
"Go, defaults."):** ending B retired, three endings (she lies down / Corvane
lies down / she carries it home); the name is **Corvane**; Corvane killable
in Act 1 and getting up on screen; "He has never burned." retired; Holloway
risen as Ashford's commander waits for Act 2's brief. The proposal was
PROPOSAL READY story-s1@9fd41e6e0, editor PASS WITH FIXES applied.

**Writer 3 (Fable, 5 Nov): slice 2 steps (3)-(7) in, one commit each:** (3)
46194f681 beat 10 `scene_bed` + rule `holloway.bed`, beat 5 `ford.ditch` +
Holloway's three night barks; (4) c78179037 beat 9 `hollow.healed` /
`hollow.healed_clear` + Wenna `cb_clean`; (5) 25dd39fe2 beat 12 Tam's and
Wenna's `chain.two` variants; (6) dced34449 beat 13 journal
`vault.office_end` + beat 14 `toll.baking`; (7) ead3d777f `lines.py` run,
the two gone locks removed, 70 lines locked by prefix (583 locks, 0 broken;
`tests.test_lock tests.test_lines` OK), `StoryRewriteTests.
The_seven_chains_hold_in_act_one`, StoryLint seed `holloway.bed_seen`. The
story subset (StoryLint, StoryRewrite, Quest, Cinema, Verge, StoryNight) was
green at every step (110/0). Full suite: 1534/0/10 full at ead3d777f (its one failure, the missing speaker definitions, fixed at e6a19e9dc); after that the subset with ContentTests 115/0 at every commit; a full run started at MR, tail in scratch `tests_full2.txt`. Editor (8): PASS WITH FIXES, distance medium (Haiku at xhigh), applied at 91f72d8cf; its one FAIL finding was the built bark "It's right this morning" from before S1, not new text, left as built; not applied 2/5/6/15/18/19 with the reasons in that commit's message.
**Counts since dba76d016** (`tools/vo/locked.json` 527 -> 583): survived
word for word 498; re-locked 27 (15 for the name by writer 1; 12 rewritten or
re-indexed by writer 2: `chid.carried_chid.0-9`, `chid.cb_opened_vault.0`,
`chid.cb_vault2.0`); new voiced lines 58 (plus 5 dawn reports and 2 journal
pages, unvoiced); retired 2 (`dlg.cin_drowned_fire.prints.0`,
`say.93b63298edc0`). Voice re-records 0. Slice 1 DONE (dba76d016);
integration merged at e2bdeed4d and at d8b967a05 (writer 3; docs only incoming).

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
- *Beat 5, the quiet ford:* once rule `ford.ditch` (day >= 3, `prologue.done`;
  after `dawn.face`): "Nobody stood in the ditch on the Low Ford road last
  night, or the night before. The Watch has stopped sending a man down to
  look."; Holloway's `said` night barks (npcs.json, not once, days 2/3/4 by
  `day eq`, off when `chain.two`): "Eleven in. Nobody out." / "Eleven in.
  Second night." / "Eleven in. Nobody out. I've stopped writing it down."
- *Beat 9, the stream runs clear:* two once rules right after `chain.two` in
  rules.json (rules read live facts in file order, so they fire the same dawn
  chain.two is set): `hollow.healed_clear` first (chain.two and `stream.clear`
  already: the scar only; sets `hollow.healed` = "scar"), then `hollow.healed`
  (chain.two and not `stream.clear`: the stream clear, the scar closed, wolves
  drinking in daylight, the Dig's hill silent; sets `stream.clear` so the
  Verge, Tam's `happy` and Wenna's craft gate agree with the words, and
  `hollow.healed` = "chain"). Wenna `cb_clean` (entry on chain.two, once by
  npcFlag `cb:clean`, then hub): cured "It's cleaner than I made it. I don't
  know why." / `hollow.healed` "scar" "It's cleaner than it was. I don't know
  why." / else "It's clean. I don't know why it's clean."
- *Beat 10, Holloway's bed:* `scene_bed` (narrator `gate` -> holloway `count`
  -> narrator `cup`, one exit "(Leave them be.)"; sets `holloway.bed_seen`,
  seeded in StoryLint for Act 2's rope); rule `holloway.bed` (after
  `hollow.healed`): chain.two and no `scene.dusk` -> `scene.dusk` =
  `scene_bed` (it waits for a free dusk like `maeca.cup`). Maeca comes
  without her crossbow (Act 2's plant) and says nothing.
- *Beat 12:* `tam.again` front variant on chain.two ("It knocked. Louder. Pa
  says it's the ground settling. Things don't settle UP."); `wenna.hub` front
  variant on chain.two ("I've the masks out again. Don't ask me why. I don't
  know why."). Neither explains it.
- *Beat 13:* `chid.office` (he gives the book) adds journal `vault.office_end`:
  the whole page in the keepers' words, with the sentence Vonnra withheld.
  *Beat 14:* once rule `toll.baking` (`player.deaths` >= 1, `prologue.done`;
  after `dawn.word`): "Up the street, nobody is baking." `player.deaths`
  counts real falls only (Journey.cs: a zone fall, a lost story night), never
  the prologue's drowning. Re-key it on `toll.rises` when TOLL_SPEC 3's
  scripted fall is built.
- Rule reports and journal pages are not voiced lines (`lines.py` lists
  dialogue and barks only), so they carry no locks.

**Next, in order:** (8) the editor pass: a fresh Haiku `su-lead-max` at
xhigh on the slice (brief `scratchpad\story_s1\editor_brief.md`, the lines
as text in `editor_pack.txt`, PLAN.md as the canon, the WTF question on beat
7); PASS WITH FIXES applied as one commit, the touched lines re-locked
(`lock.py --prefix`, then `--check` exit 0). **The spawn guard
(`tools/hooks/spawn_guard.py`) denies every spawn by a `su-lead-max` writer
whose own spawn prompt lacks the literal line `Spawning: allowed`** (it reads
the transcript's first message only, never a brief file it points at):
writer 3 was spawned on a pointer and could spawn nothing; the coordinator
spawned the editor from the brief file, with the verdict sent to the writer
by SendMessage. A successor's spawn prompt must carry the line itself. (9)
merge `origin/claude/vigilant-galileo-l6jqyx` under the junction rule (`cmd
/c rmdir godot\assets`, merge, remake the junction to this worktree's own
`public\assets`, `git update-index --assume-unchanged godot/assets`), the
suite green, push, `MR READY story-s1@<sha>` here and to main with the
editor's verdict in two lines, the counts above, the re-lock count and the
cost.

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
  shot. Plays the morning the fact `hollow.healed` appears ("chain": the
  stream cleared with the scar; "scar": the stream ran clear already, the scar
  only), set by the dawn rules `hollow.healed` / `hollow.healed_clear`; the
  words over the last shot are Wenna's `cb_clean` variants. ~50-80k.

**Scratch (`scratchpad\story_s1\` of the session that runs you, backed up
to `survivorsunchained_inputs\scratch_story_s1\`; restore the subfolder if
the scratchpad was cleared):** `lib.py` (round-trip-safe load/save of the
content JSON: dialogue.json is LF, rules/quests/npcs are CRLF, npcs.json has
no trailing newline and lib keeps it that way; `node`, `choice`,
`set_text_variant`), `dumpc.py <dialogue.json> conv [--nodes a,b]` (a compact
text dump of a conversation), `beat6.py`, `beat7.py` (writer 2), `beat10.py`,
`beat9.py`, `beat12.py`, `beat13.py` (writer 3: steps 3-6, the pattern for
any later beat), `editor_pack.txt` + `editor_brief.md` (step 8),
`handoff_edit.py`, `tests_full.txt` (the full suite's tail). Node ids and
`once` keys are per conversation and must not collide (`vonnra.jessop` and
`vonnra.ford` were taken: hence `jessop_in`, `ford_tale`). Text variants are
checked in order: the specific `when` first (a front variant re-indexes the
ids under it: re-lock the node's prefix).

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


Older blocks: history/story.md (grep by keyword, never read whole).
