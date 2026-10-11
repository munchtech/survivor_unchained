# Handoff: the story and writing lead (Survivor Unchained)

You are the writer. You own the canon, every word the game says, the story
data and the cinematic scripts, and you sign off voice packets.

## Where it stands (the thirteenth lead, 11 October)

- **Canon written in.** A ("Not yet": Chid made you), B ("Count's right":
  Holloway knew) and the toll ("It takes less than it did") are in
  `TREATMENT.md` §0 (with "How the three meet": Vonnra's twenty-six were the
  price; Chid put the one who would hold on in the water first; why one rises
  with a mind stays unsaid) and in the bible: rule 6 (a rising is paid for),
  §1 the mother's last evening, §3 rows (plus "Getting up"), §5 Chid, Vonnra,
  Holloway, Maeca and the third layers, §8 C41/C42/C43, the toll in the
  endless, §12 facts. The old labels "twist A/B" (the voice, the lamp) are
  renamed so nobody confuses them with the owner's A and B.
- **Voice ids for the unvoiced narration.** `tools/vo/lines.py` now reads
  `Journey.Day.cs` DayLines (12 lines: the dusk call is the gate guard's, the
  rest the narrator's) and the story fights' `Pull`/`Between`/`BetweenSight`
  (20 lines: Hollow, Roost, Dig, Vault), all said via `Game.Say` as
  `say.<hash>`. **"You get up." and "You get up. It takes less than it did."
  are directed and LOCKED** (162 locks). The other 30 have no direction yet
  and are on the narrator's HOLD: review, direct and lock them with the rest
  of the narrator.
- **TOLL_SPEC judged** (max judge, against TWIST_WTF option 1): see "TOLL_SPEC"
  below for what was applied.
- **Not done: the sophistication pass.** Analysed, not applied (my context ran
  out). The decided list is below; do it, then a max editor-judge, then lock
  Holloway, Maeca, Chid and the rest of the narrator.

## The sophistication pass: decided, to apply (Act 1, unlocked lines only)

Rook's and Brannoc's Act 1 lines are locked: never change their words. The
editor's open notes are `docs/story/notes/02_act1_draft.md` §2 to §11 (§12 is
the order). Use `showc.py` to see each node first.
1. **Maeca's "three days"** (§3): `maeca.blind_morning` "The Pack found me,
   after Ashford. A cave mouth, and a lad I'd been fond of dying in it.";
   `maeca.told_true` "...I held a cave mouth for nobody coming. ..."
2. **The ledger leak** (§2). Rook's side is locked (the room stays in the
   lie), so fix the ledger: `vonnra.f_chart` [0] and [1], line twenty-six
   "Rook's lodger." becomes "A woman. No name." (it rhymes with the unnamed
   marker; under A Chid knew her name and left it off). Ripple: bible §1, §0's
   lamp-twist bullet, TOLL_SPEC §6, the Act 3 plan. The survivor's choice in
   `rook.mother2` "I was a day short." becomes "A week. I was a week on the
   road." (Rook's locked reply still fits, and re-reads).
3. **The gate scenes** (§9): `scene_gate_dawn.all` "(Maeca looks at the ground
   he slept on, and then at him, and says nothing.)" (fixes the step slip and
   "very loudly"); `scene_in_my_count.crowd`: the threat in one crowd voice
   (no folk speaker exists in dialogue.json: check how Panels/Dialogue name a
   non-NPC speaker first); consider the toll seed there: the town's fear is
   that people go in their sleep since she came (true, and the player
   dismisses it); `.captain`: he walks through them and turns his back on her;
   `scene_knocking.home` "Can't. Somebody's still out. (He drinks.) ...Sit
   down. I'll tell you who."; `scene_knocking.saw` gains (b)'s plant: "Dead.
   Climbing. Grey, all of them, and not a sound out of them."; `scene_did_he`
   cut "which she never does".
4. **The narrator's tic** ("which she never does", "which he never is"...):
   keep the hammer and Chid's quiet, cut the rest (grep the data).
5. **Bible rules to settle:** the dead don't knock (§6.6: whatever knocks is
   alive; C20b's three dusks are the hole's silence); Gale (Holloway stops on
   "Gale. ...Gale.") is the lad Maeca followed down the shaft (§7).
6. **B's money and the decoy** (§6.5, §7): folk "Maeca pays the captain's
   slate..." becomes a B seed: "The captain pays Maeca out of his own pocket,
   and she spends it on his slate. Round and round." (edit in place: folk ids
   are indices); a third decoy for the player who settled Redcowl and Pell
   (the town says the north wants the captain gone); `decoy.rope` "Holloway
   laughed when he heard" becomes "said nothing, and drank."
7. **Boots** (§6.2): cut your boots from `maeca.blind`; `kerchief.raid` "took
   his boots" becomes his mule; LOVE_SCENES B loses "Boots."
8. **Chid, "What do I cut?"** `rook.mother_where` (locked) promises it: give
   Chid the beat after `mother.told` (her name if named at creation, "Mam" if
   not). Under A he knew her name all along.
9. **Folk:** append "Wat's grey mare won't take a bit in winter. He warms it
   in his armpit." (the lie route's mare). Sella's stalker `say_calling` from
   her trade (it twins Rook's).
10. **Hygiene:** `elevenlabs.py` calls the narrator "he"; the treatment body's
    boot roll (§4.1, §4.3, §4.6), "A woman with a lamp. North bank. Seventh
    evening." (§3.1), "low, warm and unhurried" (§3.4).
Then Act 2, per `git show 86b97737:docs/handoff/story.md` §3.

## TOLL_SPEC (judged; fixes applied)

A max judge passed it with fixes; all applied (303 lines): C41's line no
longer says "the night you first got up" (line 27 is the ford) and takes a
clause per fight; the §1 table adds the in-fight revives (`p.Revives`,
`p.Ashes`), a lost table night and map runs; the scripted fall has its own
path (no rise spent, no stage replayed) and a staged beat per fight; the paid
ones get a villager body and rules so they are seen; Rook's barks stop giving
the pattern away; the death leads the morning report; Oswin's folk line is
rewritten in place (gated), not deleted. **Left for you:** "went in his/her
chair" (5 of the 24) and "sat down ... and went" (4) still repeat; a stiff
"Detail:" lead-in in §4; Vonnra's optional close "...No charge, this once.
Not to you."; C09's ledger text goes in with item 2. Then it is ready for a
combat or story-code lead (the main session assigns it).

## Branch and tools

- **Branch:** `story-writer-successor` (from the integration branch at
  9cbc654c). Commit, push, open no PRs. `cd godot/tests && dotnet test` (771
  pass, 8 skipped) before any commit touching code or data;
  `python -m unittest discover -s tools/vo/tests` has one librosa error, not
  ours.
- **Locks** (`tools/vo/lock.py`, `locked.json`) bind words, not ids:
  `--prefix say.<hash>` locks one line. Then `lines.py`, `elevenlabs.py`,
  `lock.py --check`, `check_ids.py`.
- **Scripts** (the worktree guard refuses bash with computed values; run
  Python with literal paths), backed up in
  `C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_91211d34\s13\`
  (set `WT` to your worktree): `rep.py FILE PAIRS.json` (exact replacements,
  each must match once, CRLF-safe), `adddir.py NAME ENTRIES.json` (direction
  files, style-safe), `gaps.py DIR...` (sentence literals with no voice id),
  `showc.py`, `lsv.py`, `lib.py`, `sheet.py`.

## Gotchas

- `from_story_fights` skips a literal followed by `=>` or right after `(`
  (switch-arm keys like "rescued"); a sight passed as a call's first argument
  would be missed.
- Morning reports are unvoiced text. A capitalized parenthesis inside a line
  is the narrator's; lower-case directions are not.
- `holloway.knocking` must not fire once `holloway.confessed` is set. Scenes
  share one morning and one dusk slot. StoryLint: every fact read is written.

## The owner's words

- 11 October: "another pass of sophistication"; "we need a big twist nobody
  sees coming"; "I'm still missing a WHAT THE FUCK kinda moment".
- Before: "a powerful epic story with real emotional happenings"; Maeca
  killing Holloway "a HOLY SHIT WHAT THE FUCK kinda thing"; Brannoc "needs to
  hit HARD. so hard."; "the harshest versions are what were aiming for".
- Game text is American spelling. The tone is adult.

## Read first

1. This page; `TREATMENT.md` §0 (the top block); `TOLL_SPEC.md` if on the toll.
2. For the pass: notes 02 §2 to §11 by section, then each node in `showc.py`.

HANDOFF READY: docs/handoff/story.md on story-writer-successor@eea7d462
