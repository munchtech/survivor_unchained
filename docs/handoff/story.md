# Handoff: the story and writing lead (Survivor Unchained)

You are the writer. You own the canon, every word the game says, the story
data and the cinematic scripts, and you sign off voice packets.

- **Now (the eleventh lead, 11 October):** the WTF twist's three options are in
  `docs/story/TWIST_WTF.md`, judged by a max editor and revised. Recommended:
  1, "It takes less than it did" (every rise since the first was paid for by a
  death in the valley; the paid one comes out to your light the next night;
  Vonnra's ledger runs on by the player's own count; the baker of C04's warm
  line is twenty-eight). 2, "The Morrow" (the night's dead include those still
  to come; breaks rules 1 to 3 and 5). 3, "You all write the same thing" (the
  Warden was Chid's first; low shock). **Waiting on the owner's choice** via the
  main session. Every option leaves the prologue narrator lines, C02 to C04 and
  `far_voice` word for word: lock those first. Step 2 is unchanged (below).
  "I made him too." can go into A's C42 whichever option wins.
- **Branch:** `claude/story-wtf-twist` (the eleventh lead; it holds only
  TWIST_WTF.md and these pages). Merge `origin/claude/vigilant-galileo-l6jqyx`
  first. Commit, push, open no PRs. Tests: `cd godot/tests && dotnet test`
  (760 pass, 8 skipped) before every commit. Commit messages go in a file
  (`git commit -F`) and end with `Co-Authored-By: Claude Opus 5.5
  <noreply@anthropic.com>`.
- **Budget warning:** onboarding as the brief listed it (README, this page,
  the status page, the whole treatment, the editorial letter, the bible's
  sections) cost the tenth lead about 250k of a 300k budget. Don't repeat it.
  `docs/story/TWIST_OPTIONS.md` holds the canon the next steps need. Read the
  bible and the treatment only by grepped section, and only for a step that
  needs them.
- **Scripts:** the worktree guard refuses bash with computed values, so write
  Python in your scratchpad and run it with literal paths. Copy `lib.py`
  (round-trip-safe load and save of the content JSON; `node`, `ch`, `v`,
  `replace_text`) and `showc.py` (`showc.py CONV [NODE...]` prints a
  conversation; `showc.py ?` lists them) from
  `C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_91211d34\s10\`,
  and set `WT` and `C` to your worktree.

## The owner's words

- Today (11 October), verbatim: "lets fire up the writer - we need a big twist
  nobody sees coming, maybe chid being evil? and another pass of
  sophistication. also I would like to get some of the early lines mostly
  settled so I can truly begin my elevenlabs voices"
- Before: "a powerful epic story with real emotional happenings. people being
  devastated, elated, or both. shocks and twists, stuff we figured out that
  was obvious."; "when maeca kills halloway it should be a HOLY SHIT WHAT THE
  FUCK kinda thing."; Brannoc "needs to hit HARD. so hard."; "the harshest
  versions are what were aiming for."
- Spelling is American (OWNER_NOTES, 11 October). The data already is
  ("traveler", "gray"). The tone is adult.

## The brief (from the coordinator, 11 October)

1. **The twist first.** `docs/story/TWIST_OPTIONS.md` (merged at 0d688b27).
   **The owner chose A and B together:** A, "Not yet": Chid made you. B,
   "Count's right": Holloway knew. C is dropped. Both are canon now; write
   them into TREATMENT §0 and the bible when you touch them.

   **The owner still wants more:** "I'm still missing a WHAT THE FUCK kinda
   moment - those are just like 'ohhh yeahhh'". A and B are clicks: they
   explain something the player half-wondered about. What he wants overturns
   something the player never thought to question (the premise: who "you"
   are, who has been speaking, what the nights are, what the player has been
   doing). It must be a twist of the whole game, not a person's secret. It
   needs:
   - the editor's six tests (`EDITORIAL_LETTER.md` §3.7);
   - to keep A, B and the four approved twists standing;
   - to be planted from the prologue.

   The person twists set aside in TWIST_OPTIONS ("Considered") are the wrong
   kind. Propose one or two to the coordinator before step 2.

   **This gates the voice work.** A premise twist will almost certainly touch
   the narrator's prologue lines. Lock only what it can't touch, or settle it
   first.
2. **Settle the early lines for voicing** (the Prologue and the opening of
   Act 1):
   - plant the chosen twist's seeds (the tables in TWIST_OPTIONS);
   - the sophistication pass: subtext over statement, each voice distinct, no
     line that explains what the scene shows;
   - love-scene B only if it falls in this stretch (check
     `docs/story/LOVE_SCENES.md`: Sella's paid night opens on night one).

   Then mark the lines **LOCKED FOR RECORDING**, character by character.
   Bring `docs/voice/RERECORD.md` and the packets (`python
   tools/vo/elevenlabs.py`) up to date for exactly those lines, and lift
   their HOLD (`HOLD_LINES` in `tools/vo/elevenlabs.py`). Don't hand-edit
   the packets. Then run `python tools/vo/check_ids.py`.
3. **Before anything is called locked:** a fresh `su-lead-max` story editor,
   in the foreground, with "Context budget: 150k". Give it the locked lines,
   the twist choice, the owner's words and a checklist. Fix what it finds.
4. **Then** the sophistication pass through the rest of Act 1, and Act 2.
   Act 2's plan is the eighth lead's: `git show 86b97737:docs/handoff/story.md`,
   §3 "Act 2 (next)". Notes 02 (`docs/story/notes/02_act1_draft.md` §12) is
   the editor's open work list on Act 1.

Report to the coordinator (SendMessage `main`) when the early lines are
locked. Hand off by 300k.

## What step 2 covers, and what was found

- **Untouched by every option** (do these first):
  - the narrator's prologue lines (`godot/logic/Play/Zones/Prologue.cs`
    `G.Say`, about 18 of them);
  - C01 `cin_drowned_fire`, C02 `cin_none_cross`, C03 `cin_heart_goes_down`,
    `warden_answer`, C04 `cin_first_light`;
  - Vonnra's `far_voice`;
  - Rook's day-one lines (`rook.first` and on);
  - Brannoc's first meeting and barks.
- **Touched by A:**
  - `chid.first` gains one direction;
  - the day-2 report that Chid buried a woman from the ford ("Nobody's
    claimed her.") is **not in the data yet**, so write it;
  - the prologue's reeds beat is staging, plus an optional narrator line.

  Chid's other Act 1 lines are already the seeds; keep their words.
- **Touched by B:** `scene_knocking` (Holloway looks to the step on "Pell."),
  his roll (stops at ninety-one), `scene_his_cup` (a direction).
- **Not built in the prologue yet:** the drowned woman with the dead lamp at
  the water's edge (combat and experience).
- **C01's letter** is cinematic shot 6, unvoiced: "no word is left".

## Voice gotchas

- **Zone-code lines** (the prologue's narrator) are keyed by a hash of their
  words (`VoiceLines.Said`, `say.<hash>`, in `tools/vo/manifest.json`). A
  reworded line gets a new id: regenerate the manifest (`tools/vo/lines.py`),
  and `check_ids.py` must pass.
- **Dialogue ids** are `dlg.<npc>.<node>.<variant>`. Adding a variant shifts
  the ids after it.
- **A changed line with an old placeholder take** loses its entry in
  `godot/data/vo/index.json`, or `VoiceTests` fails. The previous drop
  script is `vo_drop_s7.py` in `survivorsunchained_inputs\scratch_f1b9be14\story7\`.
- **Parentheses:** a capitalized parenthesis inside a line is voiced by the
  narrator. Lower-case directions are not.

## Story gotchas (from the eighth lead, still true)

- A node's effects apply before its text is chosen.
- Scenes share one morning slot and one dusk slot: check the slot is empty.
- StoryLint: every fact read is written; every fact written is read or listed
  as a seed.
- `holloway.knocking` must not fire once `holloway.confessed` is set.

## Read first

1. `docs/story/TWIST_OPTIONS.md`.
2. `docs/team/story.md`.
3. The brief's step 1 above: A and B approved, and a bigger, whole-game twist
   still wanted.
4. `docs/voice/RERECORD.md` and `tools/vo/README.md` ("The route since
   October").
5. Only then the conversations you edit (`showc.py`), and `TREATMENT.md` §0
   if a decision is in doubt.

HANDOFF READY: docs/handoff/story.md on claude/story-wtf-twist (the latest commit)
