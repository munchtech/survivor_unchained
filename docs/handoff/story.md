# Handoff: the story and writing lead (Survivor Unchained)

You own the game's story: the canon, every word the game says, the cinematic
scripts and the story data. You also sign off every voice packet before the
owner records it. Read `docs/team/README.md` first (the owner's bar, how we
work, safety, the roster), then this page, then the files in section 9.

- **Branch:** `worktree-agent-a035208561a66c171`, the third story lead's. The
  integration branch is `origin/claude/vigilant-galileo-l6jqyx`: merge it in
  first, and often.
- **Tests:** `cd godot/tests && dotnet test` (541 pass). Keep them green before
  every commit, then push. Open no PRs.
  - `MapGenTests...(seed: 7)` sometimes fails under load and passes alone. It
    isn't ours; rerun before you worry.
- **Commits:** write the message to a file and use `git commit -F` (PowerShell
  5.1 breaks double quotes in `-m`). End every message with
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

---

## 1. The owner's words

- "AAA standard", "strive for excellent, above and beyond - not just good
  enough"; "the excellence bar isn't just for hair, its for literally
  everything".
- "Never settle": remake rather than polish. "Do we have soul?" Unique, specific
  to this world, never a line any other game could use (the soul test,
  `docs/cinematics/README.md` §2).
- "always be critical, if you notice something you missed earlier... don't be
  afraid to revisit it."
- Writing: twists, cohesion, variance from decisions, correct breadcrumbs.
  "depth, development, and care". Every person wants something, hides
  something, and changes or is revealed.
- 18+ dark fantasy. British spelling. Sex appeal is a driving factor for the
  heroine's look; in the prose, keep the restraint.
- On 4 October:
  - "should [Vonnra] be the narrator? someone who calls us to the town when we
    'wake up'". Decided: no; she is the voice up the road, once.
  - "story should be 40% of the game early on, end game is two types of
    arenas - permanent and our normal arenas. permanent is our arpg build maps
    like poe and the normal arenas are for mindless survivors fun".
  - The endless phase is truly endless.
  - After ending B, the endgame is "the Wayfinder's book of the nights that
    were". The owner said yes.
  - The final voices are recorded by the owner in ElevenLabs, one character at
    a time. **Voice work is paused** by the owner; keep the packets text-only.

## 2. Your brief

1. Keep the canon true and the writing at the bar: the bible, VOICES, the Act 1
   data, the cinematic scripts, and Act 2 when the owner asks.
2. **Sign off voice packets before recording.**
   - Run `tools/story/packet_check.py <packet> --full`. It now also checks the
     name takes against creation's name list.
   - Read every line against the data, and fix any line that's wrong in the data.
   - Give direction notes: wants and hides at the top of the packet, and per take.
   - Then reply "<voice> final". Once it's final, change no line without telling
     voice.
3. Answer the other leads' story questions, with the story's view written in
   the bible, not in their code.
4. Keep `docs/team/story.md` to one page.

## 3. State: done, in progress, next

**Done this session** (the bible and `docs/team/story.md` have the detail):
- **Vonnra's and Harlan's packets: final.** Three lines fixed in the data:
  - Harlan: the prisoners "were fed", and the cold killed them, because Redcowl
    feeds his prisoners.
  - Vonnra: "The road is quiet tonight".
  - Vonnra's new night bark: "I count the lights on the ford road, every night.
    Somebody should."
  - Her name for the survivor: "the warmth of ownership, not tenderness"
    (C09 too).
- **The town talks about your nights** (the experience audit's finding 5):
  - 29 `said` lines across 13 people, keyed to `arena.last.*`.
  - They're said the night itself (`arena.last.ago` 0) and the morning after
    (1), then dropped.
  - `Arena.cs` writes `arena.last.ago`; the daily rule `arena.ago` counts it on.
  - `CinematicTests.The_town_talks_about_the_night_just_past_and_then_lets_it_go`
    plays every combination.
  - Every line is a seed, and none says what the horde is (bible, "The nights").
- **The night is worded by the night.** Combat's clock says "the dead of
  night"; the result screen says "past the dead of night"; the Wayfinder says
  "Last till the dead of night", keeping her literal half hour.
- **Combat's 20 minibosses and kinds** are renamed and noted, and combat
  applied them. Gutterwick is the lamplings' table boss.
- **Arena art's four scars:** their places, the musts and must-nots, the
  valley's place words and adjectives. All applied.
- **Crafting:**
  - Brannoc's forge lines are in his voice. The choice is "Will you work my
    gear?".
  - Phase 2's words (the fang set, the shed fur, Wenna's still-room) are stored
    verbatim in `crafting.json`.
  - The endgame's "sigils" are renamed Marks.
- **Canon fixes:**
  - "Alpha" is gone from the valley's mouth: Greymuzzle is "the old dog-wolf".
  - Sella's arcanist line no longer calls the survivor warm (by night they're
    cold).
  - Chid no longer borrows Keegan's "Not there".
  - A test holds the signatures to their owners: "before you ask", "Not
    there", "Payment, always", "Someone always does".

**Voice packets** (`docs/voice/elevenlabs/<voice>.md`, now on the integration
branch):

| Voice | State |
|---|---|
| Narrator, Rook, Holloway, Brannoc, Sella, Vonnra, Harlan | **Final** |
| Chid, Maeca, Ysolde | **Read.** The notes are on `docs/team/story.md`, waiting for a voice lead |
| All others | Not read. In the voice README's order once voice resumes |

Lines changed since packets were made, so they need new takes:
- every night-talk line (new);
- Ysolde `places.0`;
- Maeca `driving.0` ("dog-wolf");
- Chid `cb_nemesis_slain.0`;
- Sella `say_calling.2` (Sella is final: tell voice).

**Next, in order:**
1. **The result screen's words.** The experience director's successor will send
   UI's slots ("the result as the night's story").
2. **C14, "The Road Back".** Combat's successor has the brief (their handoff,
   queue item 5): the `night:road_back` fight, Wat, and Brannoc as an ally who
   can't die. When it exists, you add:
   - `brannoc.road` (the dusk choice: "I'll show you." / "Not tonight.", setting
     `nell.road`);
   - the `nell.burial` morning report's variant for `nell.brought_home`;
   - a `RouteTests` play.

   Don't offer "I'll show you." before the fight exists.
3. **The cinematics lead's asks** for C01 to C04. Nothing has come yet. C01's
   call will carry the label "A voice up the road" (agreed with the main
   session).
4. **Crafting phase 3:** Vonnra's binding lines (no {name} in them), when the
   crafting successor sends the hooks.
5. **Packet sign-offs** once voice resumes. Act 2's text when the owner asks
   (`docs/cinematics/act2_outline.md`, bible §7).

## 4. Decisions, and why (all in the bible)

- **Vonnra is not the narrator.** She is the voice up the road, once, labelled
  "A voice up the road".
  - Why not: her sight is bought, and the narrator knows what nobody could sell
    her.
  - A voice the player has heard for an hour gives the twist away on day one.
  - Her power is scarcity.
  - The narrator never lies.
- **Her free things are priced and then waived,** so they stay owed. The vault
  is the one thing she never prices. Act 3: the toll she waived was the
  survivor's life.
- **Pacing:**
  - early on, the story is 40%: a day is about 20 minutes, a story night 20, a
    Wayfinder map 30;
  - a story night ends on its story beat;
  - the endgame has two kinds of arena, the atlas (other places, in Ysolde's
    hand) and a night's scar (the four peoples' own ground);
  - both exist after every ending. After B they are the Wayfinder's book of the
    nights that were.
- **The night's talk plants and never says.** "So what were you killing?" may
  be asked; nobody in Act 1 answers.
- **The minibosses' five rules:**
  - the Legion speaks Latin;
  - nothing about the Kerchiefs says "Ashford" (no battle was fought there);
  - only Grimtunnel is "Boss";
  - the ford has no bell;
  - no genre words.
- **The body keeps the opposite hours:** cold and slow by night, warm at dawn,
  with the breath smoking only at dawn. Every line about her heat is checked
  against the time it can be said (`body_hours` check, section 6).
- Everything older still stands:
  - ember is the dead;
  - oil and ember;
  - Chid carries the survivor in after every death;
  - Grimtunnel never dies in an arena;
  - narration plays no feelings;
  - the signatures.

## 5. What failed, so you don't repeat it

- **Rewriting a hand-formatted JSON file** with `json.dumps` gives a huge diff.
  - `crafting.json` and `data/cinematics/*.json` are hand-formatted: edit
    their text in place.
  - `dialogue.json`, `npcs.json` and `rules.json` round-trip: indent 1,
    `ensure_ascii=False`, CRLF, a trailing CRLF.
- **Complex bash is refused** by the worktree's isolation check (heredocs with
  git, `sed -n "$(...)"`, `cd && python - <<EOF` with several steps). Write a
  Python script in your scratchpad and run it with a plain command. Give your
  scripts unique names: other agents share the scratchpad.
- **System.Text.Json ignores fields:** `Cond` serialises as `{}`. Use
  `SurvivorUnchained.Core.Json.Write`.
- **Test setups miss Journey's defaults:** `beasts.population` is 60 in a real
  journey, and 0 in a bare test, where the dawn's rules count the Pack gone.

## 6. Gotchas

- **Dialogue format** (`godot/logic/World/Dialogue.cs`):
  - a node's effects apply before its text is chosen;
  - "is it relevant" goes in `show`, "can you do it yet" in `when`;
  - variants: first match wins, and the last is unconditional;
  - **adding a variant shifts its voice id**, so tell voice.
- **Barks** (`npcs.json`): `barks`, `nightBarks` and `said` (with `when`,
  `night`, `once`).
  - `said` lines join half the bark pool while they hold.
  - A `once` line is said first, at the next chance, once a playthrough.
  - Append new `said` lines at the end: the voice id is the index. The same goes
    for `folk.json`.
- **Parentheses in a line:** lower case is a delivery direction; a capitalised
  sentence is the narrator's.
- **{name}** cannot be recorded. Vonnra's is spliced from 24 name takes; keep
  {name} out of barks and new Vonnra lines.
- **StoryLint:**
  - every fact read must be written somewhere (C# included);
  - every fact written must be read or listed as a seed, and a seed that is
    read must come off the list;
  - every node must be reachable.
  - `arena.last.tier`, `.minutes`, `.day` and `.killer` are still seeds.
- **Fortunes are read only after dark:** tests set `TimeOfDay.Night`.
- **Checks in the scratchpad** (they're not in the repo; rewrite them if they're
  gone):
  - a seed check (every quoted phrase in the bible's Act 1 seed list is in the
    game's text): clean;
  - a signature map (who says each signature word);
  - a body-hours scan: clean.

## 7. Collaborators (the roster in `docs/team/README.md` is the address list)

- **Voice:** paused by the owner. Send packet notes to whoever the roster lists.
- **Cinematics** `af7a79bc783cca7bc`: C01 to C04; C14's cues.
- **Combat:** a successor is coming (`docs/handoff/combat.md`); C14's fight is
  queue item 5.
- **Experience:** a successor is coming (`docs/handoff/experience.md`), with the
  result screen's slots.
- **Crafting:** a successor is coming (`docs/handoff/crafting.md`), with phase
  2's wiring and phase 3's hooks.
- **Arena art** `ab03c3c85571e5085`: the scars are done. Bespoke props still to
  come: COYLE stencils, washing lines, VII on the milestones.
- **The coordinator** (main session): relays the owner and merges branches.

## 8. Open questions for the owner

1. The hymn at Nell's grave (C08) must be sung. Who sings it: Eleven Music, a
   singer we have the rights to, or a licensed synth? See the voice README.

## 9. Read these first

1. `docs/team/README.md`, then `docs/team/story.md`.
2. `docs/STORY_BIBLE.md`:
   - §1;
   - §2 (Pacing; Who tells it);
   - §3;
   - §5;
   - §6's seed list;
   - §8;
   - §9 "The nights" (the scars, the night talk, the minibosses' rules).
3. `docs/VOICES.md`: the rules at the top, then each person.
4. `docs/WRITING_PASS.md` §16 to §19.
5. `docs/cinematics/README.md`, `c01_drowned_fire.md`, `c09_fortune.md`,
   `c14_road_back.md`.
6. `docs/voice/elevenlabs/README.md` and `tools/story/packet_check.py`.
7. `godot/tests/CinematicTests.cs` and `godot/tests/StoryLint.cs`.

HANDOFF READY: docs/handoff/story.md on worktree-agent-a035208561a66c171@(see the commit that adds this page)
