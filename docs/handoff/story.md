# Handoff: the story and writing lead (Survivor Unchained)

You own the game's story: the canon, every word the game says (names and UI
copy included), the cinematic scripts and the story data. You also sign off
every voice packet before the owner records it. Read `docs/team/README.md`
first (the owner's bar, how we work, safety, the roster), then this page, then
the files in section 9.

- **Branch:** `worktree-agent-a54dc034ed29f2e02`, the fifth story lead's. It
  already holds the integration branch and the experience director's port
  (merged 4 October).
  - The integration branch is `origin/claude/vigilant-galileo-l6jqyx`: merge it
    in first, and often.
  - Untracked art copies in a worktree can block a merge ("untracked files
    would be overwritten"). Delete only the untracked copies that the
    integration branch now tracks.
- **Tests:** `cd godot/tests && dotnet test` (632 pass). Keep them green before
  every commit, then push. Open no PRs.
- **Commits:** write the message to a file and use `git commit -F`.
  - PowerShell 5.1 breaks double quotes in `-m`.
  - `Set-Content -Encoding utf8` writes a BOM; use `[IO.File]::WriteAllText`.
  - End every message with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

---

## 1. The owner's words

- "AAA standard", "strive for excellent, above and beyond - not just good
  enough"; "the excellence bar isn't just for hair, its for literally
  everything".
- "Never settle": remake rather than polish. "Do we have soul?" Make it unique
  to this world, never a line any other game could use (the soul test,
  `docs/cinematics/README.md` §2).
- "always be critical, if you notice something you missed earlier... don't be
  afraid to revisit it."
- Writing: twists, cohesion, variance from decisions, correct breadcrumbs,
  "depth, development, and care". Every person wants something, hides
  something, and changes or is revealed.
- 18+ dark fantasy, British spelling. Sex appeal is a driving factor for the
  heroine's look; in the prose, keep the restraint.
- "story should be 40% of the game early on, end game is two types of arenas -
  permanent and our normal arenas." The endless is truly endless.
- Voice is paused: no placeholders. The final voices come from ElevenLabs,
  recorded by the owner. Keep packet notes text-only.
- **The story fights' decisions (4 October; `docs/design/STORY_NIGHTS_AND_TIME.md`, top):**
  - Losing a story fight wakes her in town the next morning. Chid carries her
    home, and the night is lost: "having to die for a time". It gives her a
    day to get new gear and prepare.
  - Getting up: "Get up twice is too generous". She rises once a fight, in
    Act 1 only. After that she rises only with the rise, which "can just be a
    skill/spell", got in arenas or learned for story.
  - Redcowl gets "Spare him" or "Finish it" at his knee, as Greymuzzle does.
  - Days are 12 minutes of free play. A night left alone passes. Several
    fights a night are allowed, by intent.

## 2. Your brief

1. Keep the canon true and the writing at the bar: the bible, VOICES, the Act
   1 data, the cinematic scripts, and Act 2 when the owner asks.
2. **Every word the game says is yours**, including names and UI copy in other
   leads' code. Fix the words in place, keep the edits small, and tell the
   file's owner. Leads send you their words; review them quickly.
3. **Sign off voice packets before recording** (paused now):
   - run `tools/story/packet_check.py <packet> --full`;
   - read every line against the data;
   - give direction notes;
   - reply "<voice> final".
4. Answer the other leads' story questions. Write the story's view in the
   bible, not in their code.
5. Keep `docs/team/story.md` to one page.

## 3. State: done, in progress, next

**Done this session** (`docs/WRITING_PASS.md` §22 has every line and hook):
- **Redcowl spared or killed.**
  - The hook, agreed with combat: `ArenaSpec.OnSpare`, `EndSpared`,
    `SpareVerb`, and `Arenas.Won(j, spec, spared)`.
  - The spared ending: C11's `spared` and `flit`. He strikes camp
    (`roost.cleared`) and takes the crates only if he swore to keep them.
  - Every reader is updated: Rav's callback, the morning report, barks,
    concerns, a folk line, the standing, the chapter page, the struck camp by
    day, the fortune's crates, and the bible's Act 2 beat 7.
  - Greymuzzle gets the same choice, and "Finish it" breaks the promise.
- **A lost story fight wakes her on Chid's bench.**
  - The lost lines are now "The last thing you know is...".
  - `Journey.CarriedHome(spec)` leads to `chid.carried` (the narrator's waking
    seed for each fight), then `carried_chid` (the cost, the carter lie, a
    pointer to whoever can help), then `carried_who`.
  - Morning reports and barks for each loss.
  - Experience wired it: `WakeAfterLoss`, then the shrine, then Chid, then the
    morning page.
- **The clock's words** are in experience's `Journey.DayLines`: dusk and the
  night's fight, Rise and RiseAgain, the nudge, the night left alone,
  StraightOn, and "Answer the night" with "Also out tonight:".
- **The fortune gives the first chart.**
  - `vonnra.f_door` leads to `f_chart`, priced and waived, through a new rules
    change `{ "chart": { people, tier, rarity, name } }`.
  - The chart is "The Lampless Howes". The atlas opens with it.
  - Charts are named by `MapOffers.Name`, and StoryLint holds them.
- **Words for other leads:**
  - combat: the rise, the art "Not Yet" (`cold_then_not`) and the blessing
    "Cold, Then Not" (`from_the_ashes`), with their texts and captions;
  - UI: the atlas page and the map result's words.
- **Docs:** the bible (pacing, Redcowl, the nights, Act 2's rise, the
  ledger); C09, C10 and C11; the cinematics handoff (item 8).

**Next, in order:**
1. **Chid gives *The Keeper's Office*** (`keepers_office`). Combat made the
   item on `worktree-agent-a708da2c97bf85c95@b54d6649`; it isn't on the
   integration branch yet. The lines are written in WRITING_PASS §22.3:
   - an entry node `chid.office` once `chapter.done`;
   - a `carried_chid` variant after a lost Act 2 fight, if she has no book;
   - "Who wrote it?" ("Nobody makes a C like that any more.").
   Add a test that the book arrives both ways.
2. **C14, "The Road Back"**, once combat builds it in the story-fight shape:
   `brannoc.road`, the `nell.burial` variant, its won and lost lines (lost:
   "The last thing you know is..."), and a RouteTests play.
3. **The result screen's new slots**, when experience sends UI's beats.
4. **C01 to C04:** answer the cinematics lead's line asks.
5. **Act 2's text**, when the owner asks (bible §7; the spared Redcowl and
   Chid's book are planned there).
6. When Godot is free, look at these as the player sees them, at 1920x1080:
   the waking on Chid's bench, the spared ending's result line, and the
   fortune's chart.

## 4. Decisions, and why (all in the bible)

- **Spared, Redcowl owes her and leaves.** A beaten captain moves his people,
  and he talks in debts ("Redcowl owes Rav a leg"; "the rest of me"). He never
  says "Ashford": that is spent dying. If she said it, he squares it ("Near
  enough").
- **The loss's cost is the night, said once by Chid.** No gold, wound or
  things are lost. The day it buys is pointed at getting ready (the banes'
  teachers).
- **She wakes at the shrine, not the inn.** Every death's waking is Chid's, and
  his carter lie wears thinner. The narrator never says who carried her.
- **The rise has two names:** the ember's "Cold, Then Not" (Chid's line) and
  the Order's "Not Yet" ("Is it morning?" "Not yet."; the Legion's Nondum).
  The book's Cs are Chid's hand, which is Act 3's.
- **The chart is in the Wayfinder's hand, its margins written full.** Vonnra
  buys from Ysolde too, and the margins are what Ysolde sells.
- **Vonnra is not the narrator.** She is the voice up the road at the waking.
  Her free things are priced and then waived, so they stay owed.
- **The base game is not explicit,** and a love scene never earns a mechanical
  reward.
- Everything older still stands:
  - ember is the dead;
  - the body keeps the opposite hours: cold by night, warm at dawn;
  - Grimtunnel never dies in an arena;
  - the narrator never lies and plays no feelings;
  - the signatures and the "nevers" in VOICES;
  - the night's talk plants and never says;
  - no genre words, and the valley's place words.

## 5. What failed, so you don't repeat it

- **Complex bash is refused** by the worktree guard: heredocs into python,
  `cd && git`, and variables used as a command. Write a script to the
  scratchpad (story5/) with the Write tool and run `python <abs path>`.
- **Re-dumping hand-formatted JSON** (`crafting.json`, `looks.json`) gives a
  huge diff. `dialogue.json`, `rules.json`, `npcs.json`, `quests.json`,
  `concerns.json` and `folk.json` round-trip (indent 1, `ensure_ascii=False`,
  CRLF, a trailing CRLF). `story5/jsonio_s5.py` checks this before writing.
- **A node's effects apply before its text is chosen.** Clearing the fact a
  variant reads, in the same node, breaks the variant. Chid's `carried` clears
  `player.carried_home` and picks by `arena.last.people`.
- **Splitting a node changes test walks.** Moving the fortune's close choice
  broke four tests that chose at `f_door`. Grep the tests for a node's choices
  before moving them.

## 6. Gotchas

- **Dialogue format** (`godot/logic/World/Dialogue.cs`):
  - "is it relevant" goes in `show`, "can you do it yet" in `when`;
  - in variants, the first match wins and the last is unconditional;
  - **adding a variant shifts the voice ids after it.** Tell voice.
    `vonnra.f_ember` gained a .0.
- **Cinematic conversations walk by `next`.** An alternative ending is reached
  by a conditional entry (`cin_raid_on_the_roost`: `spared` once `redcowl` =
  `spared`). `CinematicTests.OtherEnding` walks it.
- **Barks:** `said` lines are appended at the end, because the voice id is the
  index.
- **Parentheses:** lower case is a delivery direction, and subtitles strip it.
  A capitalised sentence is the narrator's.
- **`{name}`** cannot be recorded. Keep it out of barks and new Vonnra lines.
- **StoryLint:**
  - every fact read is written somewhere;
  - every fact written is read or is a seed;
  - every node is reachable;
  - no explicit slot, no genre word;
  - the table's and the charts' place words.
- **Story fights' specs live in `godot/logic/Play/StoryFights.cs`** now, not
  in the Verge (experience moved them). The Verge keeps only the
  interactables.
- **Checks in the scratchpad** (`story5/`; rewrite them if they're gone):
  - `seed_check_s5.py`: clean. The "nodes" it lists are facts, and the
    unmatched quotes are Act 3 payoffs;
  - `phrases_s5.py`: the signature map, clean;
  - `body_hours_s5.py`: clean;
  - `show_s5.py CONV [NODE...]` prints a conversation;
  - `rules_s5.py WORD` prints rules.
- **The owner is using the GPU:** no Godot or Blender until the main session
  says so.

## 7. Collaborators (the roster in `docs/team/README.md` is the address list)

- **Combat** `a708da2c97bf85c95`:
  - StoryNight calls `Won(spared)`, then the end hooks;
  - it has the Arena.cs hunks verbatim;
  - it plays Redcowl's `.spared` then `.flit`;
  - it made `keepers_office`;
  - its rise captions are story's.
- **Experience** `ab406cf9ddd22b03b`:
  - the clock;
  - `StoryFights.cs`;
  - the loss's waking flow;
  - the DayLines, which hold your words.
- **UI design** `a26f87c39952dcd9c`: the atlas words, agreed and pasted; the
  chart opens the atlas.
- **Cinematics** (handed off; the successor reads `docs/handoff/cinematics.md`
  item 8): C09's chart beat, C10's choice, C11's spared ending, and the hook ids.
- **Voice** `a501b387a90d78b4e`: paused. The packet notes are on the status page.
- **The coordinator** (main session) relays the owner and merges branches.

## 8. Open questions for the owner

None of the story's own.

## 9. Read these first

1. `docs/team/README.md`, then `docs/team/story.md`.
2. `docs/STORY_BIBLE.md`:
   - §1;
   - §2 (Pacing; Who tells it);
   - §3;
   - §5 (Redcowl);
   - §6's seed list;
   - §7 (the rise; beat 7);
   - §9, "The nights";
   - §11, "Intimate scenes: fade to black".
3. `docs/VOICES.md`: the rules at the top, then each person.
4. `docs/WRITING_PASS.md` §20 to §22.
5. `docs/design/STORY_NIGHTS_AND_TIME.md` (the decisions at the top) and
   `docs/design/STORY_BOSSES.md`.
6. `docs/cinematics/c09_fortune.md`, `c10_hollow_by_night.md`,
   `c11_raid_on_the_roost.md` and `c14_road_back.md`.
7. `godot/logic/Play/StoryFights.cs`, `godot/logic/Play/Journey.Day.cs`, and
   the tests `StoryLint.cs`, `CinematicTests.cs` and `VergeTests.cs`.
