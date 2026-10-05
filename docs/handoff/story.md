# Handoff: the story and writing lead (Survivor Unchained)

You own the game's story: the canon, every word the game says (names and UI
copy included), the cinematic scripts and the story data. You also sign off
every voice packet before the owner records it. Read `docs/team/README.md`
first (the owner's bar, how we work, safety, the roster), then this page, then
the files in section 9.

- **Branch:** `worktree-agent-a73ca9d35d0c487a9`, the fourth story lead's.
  - The integration branch is `origin/claude/vigilant-galileo-l6jqyx`: merge it
    in first, and often.
  - Untracked art copies in your worktree can block a merge ("untracked files
    would be overwritten"). Delete only the untracked copies that the
    integration branch now tracks; see the gotchas.
- **Tests:** `cd godot/tests && dotnet test` (611 pass after the last merge).
  Keep them green before every commit, then push. Open no PRs.
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
- On 4 October:
  - Vonnra is not the narrator. She is the one unnamed call up the road at the
    waking, subtitled "A voice up the road".
  - "story should be 40% of the game early on, end game is two types of arenas -
    permanent and our normal arenas. permanent is our arpg build maps like poe
    and the normal arenas are for mindless survivors fun".
  - Story nights are 20 minutes and the Wayfinder's maps 30. The endless is
    truly endless. After ending B, the endgame is "the Wayfinder's book of the
    nights that were".
  - Voice work is paused: no placeholders. The final voices come from
    ElevenLabs, recorded by the owner one character at a time. Keep packet
    notes text-only.
  - **"Warmed" from the love scenes does nothing**: it only says the night
    happened (done).
  - **The hymn at Nell's grave (C08):** the owner makes it themselves in Suno.
  - Proposed, not yet approved: story fights "much more specialized and fun -
    smaller arena - and they don't need endless - they have proper arpg end
    bosses"; and time "passing" on its own, so that a player who never finds
    the inn's rest still moves on.

## 2. Your brief

1. Keep the canon true and the writing at the bar. That covers the bible,
   VOICES, the Act 1 data, the cinematic scripts, and Act 2 when the owner asks.
2. **Every word the game says is yours**, including the names and UI copy in
   other leads' code. Combat's handoff says text goes through story. Fix the
   words in place, keep the edits small, and tell the file's owner.
3. **Sign off voice packets before recording** (paused now):
   - run `tools/story/packet_check.py <packet> --full`;
   - read every line against the data;
   - give direction notes;
   - reply "<voice> final".
4. Answer the other leads' story questions. Write the story's view in the bible,
   not in their code.
5. Keep `docs/team/story.md` to one page.

## 3. State: done, in progress, next

**Done this session** (WRITING_PASS §20 and §21 have each line):
- **Every story night ends on the narrator's own line**, won and lost
  (`ArenaSpec.EndWon`/`EndLost`, set in `Verge.MakeStoryFights`).
  - The Hollow has a spared variant.
  - A rematch keeps the won line and drops the lost one. It now also keeps
    `Spare`, which fixes a bug where a retaken Hollow fight killed a Greymuzzle
    its `OnWin` spared.
  - No line claims the dawn: she comes back into the same night.
- **Morning reports for each story night** (`rules.json`): `hollow.killed`,
  `hollow.spared`, `roost.cairn`, `dig.quiet` and `vault.watched`.
- **The arena's words:**
  - "THE NIGHT IS HELD" and "Your longest night yet" on the result screen; a
    table night won says "The Wayfinder will want it for her margins.";
  - "Brought down by a Kerchief Footpad" (`Enemies.Called`);
  - "until the Pack-Mother comes" (`MapOffers.InSentence`);
  - "is down: the night is held", and "end it" in place of "beat it";
  - on the table, "Wolfbane gear, or gear of the Wolf".
- **Map names are in the valley's words, per people**, merged with arena art's
  places:
  - `ArenaPlaces.Names` are the place words; `ArenaPlaces.Adjectives` and
    `Moods` are the adjectives, each of which also sets the place's look;
  - `StoryLint` holds the place words;
  - gone: Weeping, Ashen, Moonless, Scorched, Fogbound, Crooked, and "Dig" as
    a place word.
- **No genre words:** "alpha" is gone from the bounty notice, a locked choice
  and a deed. `StoryLint` reads the content and the scripts' deeds, lines and
  announcements for alpha, warlord and ganger.
- **The legal blockers:**
  - The explicit-scene placeholders are out of the data. Every love scene fades
    to black for everyone, and `StoryLint` keeps it so (bible, "Intimate
    scenes: fade to black").
  - "Warmed" is flavour only (`Character.Kit`, the book, the notices), and
    `QuestTests` holds it.
- **Crafting phases 2 and 3:** all the lines are written and the crafting lead
  has wired them:
  - Vonnra's binding, including the caged-coal refusal "He makes a good cage";
  - the marks;
  - Snib's jars and the four outcomes of steeping;
  - the slurry affixes Fevered, of the Sump and Pipe-Lad's.
- **The banes learned by day, as conversation:** Maeca's fed fires
  (`maeca.fire`, fact `bane.fires`) and Chid's pole (`chid.legion`, fact
  `bane.pole`). Both facts are on StoryLint's seed list until combat's fights
  read them.
- **The new story fights' words** (WRITING_PASS §21), sent to combat:
  - the pull and the sights between beats for each fight;
  - Old Blue, the pickets, Redcowl's rally and "Mind where you swing.";
  - Snib, Grimtunnel, the Signifer.
- **Cinematic subtitles drop lower-case directions** (cinematics built it).
  C13's "(Not yet.)" and "(Go back.)" stay.

**Voice packets** (text-only while voice is paused):

| Voice | State |
|---|---|
| Narrator, Rook, Holloway, Brannoc, Sella, Vonnra, Harlan | **Final**, but see the changes below |
| Chid, Maeca, Ysolde | **Read.** The notes are on `docs/team/story.md` |
| All others | Not read |

Changes since the packets were made (the full list is on the status page):
- **Ids shifted by one** when the explicit slots came out:
  - `sella.night` .1–.3 became .0–.2;
  - `sella.free_night` .1–.2 became .0–.1;
  - `maeca.blind` .1–.2 became .0–.1.
- **Lines changed:**
  - Sella `say_calling.2`;
  - `bark.sella.night.1`;
  - the board's bounty notice;
  - every night-talk line (new);
  - Ysolde `places.0`, Maeca `driving.0`, Chid `cb_nemesis_slain.0`.
- **New lines:** Chid `legion` and Maeca `fire`.

**Next, in order:**
1. **The story fights and the day's clock**, when the owner approves
   experience's `docs/design/STORY_NIGHTS_AND_TIME.md` and combat's
   `docs/design/STORY_BOSSES.md`. I agreed both, with two fixes:
   - the vault fight stays at the head of the stair;
   - the crates can be blown only while they are in the yard (`be.crates`
     unset, or "redcowl").

   Then put in data:
   - the dusk call ("Lamps are lit. Stay where they reach.") and the night's
     line for each fight;
   - the rise lines ("You get up." / "You get up. It takes less than it did.");
   - the night-left-alone line ("You see the night out on your feet. At first
     light the warmth comes back into your hands.").

   The clock starts when the first trouble reaches the journal. Update the
   bible's Pacing share (about 49% days with 12-minute days).
2. **Vonnra's fortune gives the first chart** (from the UI design lead,
   through the coordinator). The atlas opens once she carries a chart.
   - **Wiring:** `Journey.GiveChart(Maps.Chart)`. Data's `give` takes item ids
     only, so it needs a small hook: a Change for a chart, or the fortune's end
     in code. Agree which with the UI lead (`a26f87c39952dcd9c`) and combat.
   - **The line:** the chart is in Ysolde's hand, so Vonnra bought it, a seed
     that she watches the Wayfinder's trade too.
     - It is priced, then waived, like all her gifts ("That would be ten gold.
       This once, no charge."), so it stays owed.
     - No `{name}`. Use "traveller" unless she was accused (`vonnra.accused`),
       in which case use neither.
     - It goes at the fortune's close, before she sends the survivor away.
   - Add a `CinematicTests` check that the chart arrives on every fortune
     route.
3. **The result screen's new slots**, when experience sends UI's beats. The
   words for today's slots are in.
4. **C14, "The Road Back"**, once combat builds the fight:
   - `brannoc.road` (the dusk choice "I'll show you." / "Not tonight.", setting
     `nell.road`);
   - the `nell.burial` variant for `nell.brought_home`;
   - its `EndWon`/`EndLost` pair;
   - a `RouteTests` play.

   Don't offer "I'll show you." before the fight exists.
5. **C01 to C04:** answer the cinematics lead's line asks when they come.
6. **Act 2's text**, when the owner asks (`docs/cinematics/act2_outline.md`,
   bible §7). Love scenes are written to the fade and no further.

## 4. Decisions, and why (all in the bible)

- **Vonnra is not the narrator.** Her sight is bought, the twist would land on
  day one, and her power is scarcity. Her free things are priced and then
  waived, so they stay owed. None of her crafting lines carries `{name}` or
  "traveller", so they hold either side of the fortune.
- **The base game is not explicit.** Explicit sex would put it in Steam's Adult
  Only category. Explicit scenes, if ever wanted, are a separate DLC, and that
  is the owner's call with the lawyer. **A love scene never earns a mechanical
  reward.**
- **A night's last line never claims the dawn.** She comes back into the same
  night, and the town talks about it that night (`arena.last.ago` 0).
- **Every lost story night is a fall,** so its line is her coming to: a quiet
  seed of what she is.
- **Map names say whose ground it is.** Each people has its own words, and each
  adjective makes a look.
- **The Barrow Lord won't stay down.** She lays him down, he rises within her
  reach, and "Redi." sends her home. That fits his title, *Who Would Not Lie
  Down*.
- **Greymuzzle's end becomes her choice** (with the new fights) when the
  promise holds. "Finish it" breaks the promise.
- Everything older still stands:
  - ember is the dead;
  - oil and ember;
  - the body keeps the opposite hours: cold and slow by night, warm at dawn,
    the breath smoking only at dawn;
  - Chid carries the survivor in after every death;
  - Grimtunnel never dies in an arena;
  - narration plays no feelings, and the narrator never lies;
  - the signatures;
  - the minibosses' five rules;
  - the night's talk plants and never says.

## 5. What failed, so you don't repeat it

- **Re-dumping a hand-formatted JSON** (`crafting.json`, `data/cinematics/*.json`)
  gives a huge diff: edit the text in place. `dialogue.json` and `rules.json`
  do round-trip: indent 1, `ensure_ascii=False`, CRLF, a trailing CRLF. Check
  the round trip before writing; my scripts did.
- **Complex bash is refused** by the worktree isolation check:
  - loops with variables;
  - `cd && git ...`;
  - `git` inside `$(...)`.

  Write a Python script in the scratchpad (unique names; I used a `_s3`
  suffix) and run it with a plain command.
- **`New-Item -ItemType Junction` on an existing junction** fails with "not
  empty". Never `Remove-Item -Recurse` the `godot/assets` junction: it points
  at the main checkout's real assets.
- **`--die N` with `--zone arena`** never fired before the first draft. With
  `--auto` she fell, and no result screen came in 20 s of game time. I flagged
  it to experience; it may be the harness.

## 6. Gotchas

- **Dialogue format** (`godot/logic/World/Dialogue.cs`):
  - effects apply before the text is chosen;
  - "is it relevant" goes in `show`, "can you do it yet" in `when`;
  - variants: the first match wins, and the last is unconditional;
  - **adding or removing a variant shifts the voice ids after it**, and a new
    hub choice shifts the `ply.` ids of the choices after it. Tell voice.
- **Barks:** `said` lines are appended at the end, because the voice id is the
  index. `once` lines play first. `night: true` means night only.
- **Parentheses:** lower case is a delivery direction, and cinematic subtitles
  strip it. A capitalised sentence is the narrator's. A `.before`/`.after`
  crafting slot is already narration: no parentheses.
- **{name}** cannot be recorded. Vonnra's is spliced; keep it out of barks and
  new Vonnra lines.
- **StoryLint:**
  - every fact read must be written somewhere;
  - every fact written must be read or listed as a seed (`bane.fires`,
    `bane.pole` and four `arena.last.*` are seeds now);
  - every node must be reachable;
  - no explicit slot; no genre word;
  - the table's place words.
- **Running the game from this worktree:** `godot/assets` is a junction to
  `C:\Users\munch\Desktop\survivorsunchained\public\assets` (skip-worktree
  set). `.godot` is copied from the main checkout. Untracked art was copied in
  from the main `godot/art`: never commit it. Before a merge,
  `story3/clear_copies_s3.py` in the scratchpad removes the copies the
  integration branch now tracks.
  - `story3/play_s3.py NAME -- --zone waystation --open maps` takes a picture.
  - Run `dotnet build SurvivorUnchained.csproj` first; a robocopy of `.godot`
    overwrites the built DLL.
  - **The owner is using the GPU: no Godot, no Blender, until the main session
    says otherwise.**
- **Checks in the scratchpad** (`story3/`; rewrite them if they're gone):
  - `seed_check_s3.py`: clean. The "nodes" it lists are facts, and the
    unmatched quotes are Act 3 payoffs;
  - `body_hours_s3.py`: clean;
  - `phrases_s3.py`, the signature map: clean;
  - `slots_s3.py`: lists explicit slots and intimacy reads; none now.

## 7. Collaborators (the roster in `docs/team/README.md` is the address list)

- **Experience** `ab406cf9ddd22b03b`: the story nights and clock proposal; the
  result screen's slots.
- **Combat** `a708da2c97bf85c95`: STORY_BOSSES.md. It has all your fight words
  and the three answers; C14's fight is in its queue.
- **Cinematics** `a3058a45eee41d695`: subtitles done; C01 to C04's line asks;
  C13's change from combat.
- **Crafting** `a7debf1459f14dfe7`: phases 2 and 3 wired with your lines.
- **Arena art** `a26767f7f9955cb56`: the place words and moods are merged.
- **Legal** `aab20546fe06daa89`: issues 6 and 7 resolved. Affection and trust
  from love scenes is lawyer question 7, so nothing for you.
- **Voice** `a501b387a90d78b4e`: paused. The packet notes wait on your status
  page.
- **The coordinator** (main session) relays the owner and merges branches.

## 8. Open questions for the owner

- None of the story's own. The story fights and the clock (experience's four
  choices) are with the owner.

## 9. Read these first

1. `docs/team/README.md`, then `docs/team/story.md`.
2. `docs/STORY_BIBLE.md`:
   - §1;
   - §2 (Pacing; Who tells it);
   - §3;
   - §5;
   - §6's seed list;
   - §8;
   - §9, "The nights" (the place words, the night talk, the minibosses' rules,
     the banes);
   - §11, "Intimate scenes: fade to black".
3. `docs/VOICES.md`: the rules at the top, then each person.
4. `docs/WRITING_PASS.md` §18 to §21.
5. `docs/design/STORY_NIGHTS_AND_TIME.md` and `docs/design/STORY_BOSSES.md`
   (on experience's and combat's branches until merged).
6. `docs/cinematics/README.md`, `c13_behind_the_door.md` and `c14_road_back.md`.
7. `godot/tests/StoryLint.cs`, `CinematicTests.cs` and `VergeTests.cs`.

HANDOFF READY: docs/handoff/story.md on worktree-agent-a73ca9d35d0c487a9@(see the commit that adds this page)
