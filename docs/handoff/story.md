# Handoff: the story writer (Survivor Unchained)

You are taking over the game's story: the writing, the canon, the cinematic
scripts and the story data. Everything you need is in the repository; this
page is the map. Read it all, then read the files in section 11 before you
change anything.

- **Branch:** `worktree-agent-a69687764fdd5047c`. Last commit before this page:
  `2b5705a`. Main branch to merge from: `origin/claude/vigilant-galileo-l6jqyx`
  (the coordinator merges everyone's work there; merge it into yours when told).
- **Worktree:** `C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a69687764fdd5047c`
- **Tests:** `cd godot/tests && dotnet test`. 438 pass. Keep them green before
  every commit.
- **Commits:** on this branch, `git push -u origin HEAD`; never open a PR. Commit
  messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
  Commit and push often: API cut-offs happen, and a cut-off should never cost
  work.

---

## 1. The owner's bars (exact words, as relayed)

The owner talks to the coordinator; the coordinator relays. These are the
owner's words, in the order they came:

- "always remember, strive for excellent, above and beyond - not just good
  enough. AAA standard"; "the excellence bar isn't just for hair, its for
  literally everything".
- The writing brief: "really up our writing... twists, cohesion, variance based
  on decision making... hand off... to another agent to implement... no bugs...
  correct breadcrumbs... if stuff is found that is part of another quest...
  proper breadcrumbs to start it".
- "multiple ways ending at similar places - or completely different ones etc".
- "a note to our writer agent - ...the twists ...don't need to all happen in the
  act 1 - they will be for the whole game...". (The coordinator's version: write
  the full arc in `STORY_BIBLE.md`, make Act 1 seed toward it, and say in the
  spec which later beat each seed pays and when.)
- "always be critical, if... you notice something you missed earlier... don't be
  afraid to revisit it... rabit hole".
- "have our writer make some cinematic scripts to later be passed to another
  agent... full cinematic quality epicness".
- "also make sure they understand the importance of exceptional writing quality.
  depth, development, and care". The coordinator's expansion: every character
  on screen wants something, hides something, and changes or is revealed; arcs
  develop and pay off; dialogue earns its place, specific, with subtext, no
  clichés; let moments breathe; care for the details; read every scene back as a
  demanding editor would; quality over quantity.
- "pass along to the writer that they can edit, and spawn an editor to
  collaborate with...". The coordinator's terms: a demanding story editor, given
  the context; it works read-only or sends notes back; never both editing the
  same files; you keep the final say; "the goal is the best possible writing,
  not agreement".
- "Do we have soul?" Unique, one in a million. The coordinator's wording to me:
  "one game in a million, not one soulless game of many... a singular voice and
  point of view, specific to this world, these people and these consequences.
  Avoid anything that could be dropped into another dark-fantasy game
  unchanged. Make it part of what you and your editor test every scene against."
  It is now written into `docs/cinematics/README.md` section 2, "The soul test".
- "just another friendly reminder that 'how things are' or 'how we did this' can
  be limiting..."; "'I'll rewrite the whole fixer file cleanly instead of
  patching it again.' thats precisely the kind of thing i'm looking for".
- The owner's memory notes (in the coordinator's memory): never settle; the
  owner wants amazing, not improved; remake rather than skip.
- Adult 18+ dark fantasy. British spelling. The game is Godot 4.5.1 .NET/C#
  under `godot/`.

**Constraints.**
- Never commit or print API tokens or secrets.
- No paid cloud services.
- The GPU is shared: keep generation jobs reasonable. Local ComfyUI is at
  http://127.0.0.1:8188, driven by `tools/comfy/comfy.py`, with Krea 2, Qwen3-TTS
  and qwen3vl.
- Don't touch the art and hair pipeline (`tools/assets/`, `godot/art/`,
  `godot/shaders/`, `godot/src/Actors/`).
- Don't edit the root `src/` and `tests/` (the old web build).

---

## 2. Your brief, and every later message (in order)

1. **The Act 1 writing pass** (done before the cinematics; `docs/WRITING_PASS.md`):
   - improve the writing, twists, cohesion and decision variance;
   - breadcrumbs, and found-early handling;
   - lines written into the data;
   - `WRITING_PASS.md` as the implementer's spec; `STORY_BIBLE.md` and `VOICES.md`
     updated;
   - the full arc across all acts in the bible, with each Act 1 seed mapped to
     its payoff.
2. **The cinematics.**
   - Merge the main branch first.
   - Pick the moments across the whole arc: Act 1 fully, the rest outlined, with
     choice variants.
   - Write each as a buildable shooting script in `docs/cinematics/<id>.md`:
     trigger and facts; length; place, time, light and mood; a shot list (type,
     lens, move, framing, duration); blocking; performance; dialogue with VO line
     ids (new lines go in `dialogue.json`, per `VOICES.md`); music, sound and VFX;
     transitions, skip and subtitles.
   - Write for real-time Godot with our characters: face sliders and expressions,
     swinging hair, outfits by calling. The heroine is the customisable player
     of any calling, with calling beats.
   - `docs/cinematics/README.md` is the index and production brief.
   - Report the list, the Act 1 priorities, and what production needs that the
     game lacks.
3. **Owner on quality** (section 1); **owner on editing** (section 1); **free use
   of the PC**; **after a cut-off,** resume and commit often.
4. **Merge the editorial and romance material** (`docs/editorial/`,
   `docs/romance/`).
   - Treat it as suggestions, weighed with the editor, and integrated in our own
     voice and the bible's truth.
   - Romance is welcome where it fits the adult tone, and should be as well
     written and as consequential as everything else.
   - List decisions that are truly the owner's, with recommendations.
5. **The soul test** (section 1).
6. **The voice-prep notes** (`docs/voice/README.md` on `origin/claude/cloud-voice`,
   "For the writers"):
   - Vonnra's name in a recorded take;
   - three captions mixing the narrator and a speaker;
   - lines that break VOICES rules (Vonnra's near-yes, "He will not forget you",
     Jory saying "cage", Redcowl's line to a woman);
   - curfew lines heard by day.
   - Plus my recommendations on `docs/romance/ARCS.md` §8 and on the
     `docs/items/` decisions where they touch story.
7. **The story explorer's follow-ups** (the latest message, done; section 3):
   - merge the main branch (it has the explorer);
   - (a) Wenna's mask: unreachable for a survivor who cures the stream first;
   - (b) Keegan's supper: reachable, or allow-listed as Act 2;
   - (c) the ten `cin_*` conversations: their triggers exact in the README, and
     the ones that can live as plain dialogue triggers added now;
   - (d) `dig.pump = running` asked but never written;
   - and the story's view on `docs/bestiary/` and `docs/bosses/` (new outcomes
     from fights, Keegan's duel timing, Grimtunnel never dying in an arena).
8. **This handoff.**

---

## 3. What is done (by commit, newest first)

- `2b5705a` Every cinematic's trigger, exactly (README §9); the story's view of
  the nights (bible, "The nights: what a fight may change"); C10's let-go
  variant; C12's title; Keegan's duel at first light; WRITING_PASS §16 (the
  explorer's findings).
- `594e076` The explorer's findings in data and code:
  - **Wenna's mask:** affection 20 *or* the stream cleared, and not sold to Pell,
    with her own line for the curer.
  - **Keegan's supper:** respect 25 and affection 10.
  - **`dig.pump`** written as `running` at the first dawn (rule
    `dig.pump.running`).
  - **The cinematics' lines live now as captions and triggers:**
    - Prologue: C01's prints; C02's call and "Lie down."; C03's "Is it
      morning?" and Grimtunnel's faith; C04's "back into the ground".
    - Verge: "Them first." at the Roost, once.
    - Waystation: Nell's burial as a conversation on its morning, via
      `nell.burying`.
    - Redcowl's last words are the Roost raid's `OnWin`.
  - **Boss titles:** "Who Kept the Cold Off", "Finders Keepers".
- `6c1667c` The voice-prep fixes:
  - captions split;
  - Jory without "cage";
  - Vonnra's lines;
  - curfew lines night-only;
  - Vonnra's name spliced as its own take.
- `a9454df` Round four, the soul test:
  - stock gestures replaced;
  - C08 rewritten (Vonnra bowed, the one voice in tune);
  - C14 rewritten (the ford's posts broken; Chid at the gate);
  - C13's hand at the gate;
  - C41 Vonnra reads her ledger aloud;
  - the mother's letter in C01 and her grave in C08;
  - colour key (ember gold in an open lamp, blue only in an iron).
- `35bf204` VOICES: the "nevers" spent (Rav's one no, Chid's one plain line,
  Vonnra's one "No.").
- `d4341b3` The outlines take the canon:
  - Act 2: chapter four, the boots, Edric, memory swaps, the eve.
  - Act 3: C43 The Names, the coin, the endings and the nights, the last lamp.
- `d564573` C14 The Road Back, and the soul test in the README.
- `fe8d493` Act 1 scripts take the canon: C09's interruption, C06's fourth cage,
  C07's boots on the nail.
- `1bc34ac` Oil and ember in the shipped text (Keegan, the book, the prologue's
  journal); the fortune interrupted in the data.
- `f41126a`, `fdde382` The romance Act 1 data merged node by node with fixes; the
  scene files corrected for the Act 2 writer.
- `7ba8f45` The bible's canon (section 4 below).
- Earlier:
  - C01 to C13 written and revised over the editor's rounds one and two;
  - six storyboard frames (`docs/cinematics/boards/`);
  - the merges of the editorial, romance and implementation branches;
  - the Act 1 writing pass.

**Files you own:**
- `docs/STORY_BIBLE.md`, `docs/VOICES.md`, `docs/WRITING_PASS.md`;
- `docs/cinematics/` (README, C01 to C14, `act2_outline.md`, `act3_outline.md`,
  `boards/`);
- the story data in `godot/data/content/` (`dialogue.json`, `rules.json`,
  `folk.json`, `npcs.json`, `quests.json`, `items.json`);
- story text in `godot/logic/Play/Zones/` (`Prologue.cs`, `Waystation.cs`,
  `Verge.cs`: captions and outcomes only);
- `godot/tests/CinematicTests.cs`;
- the status lines in `docs/romance/`.

---

## 4. Decisions made, and why

All are written in the bible. The editor (section 9) argued each.

- **Ember is the dead.**
  - The Morrow keeps every death in the valley; ember is the held dead, leaking
    up. The survivor burned Nell on the first night.
  - Five fixed rules (bible §1). Why some rise with their minds is never said: as
    a rule, the player would apply it backwards to Nell.
  - Why: twenty seeds are already in the text; it makes every ending mean more;
    it is personal, not abstract.
- **Oil and ember.** The Watch burned oil (the Warden slept); Vonnra's new irons
  hold ember (it woke). Ember burns blue only in an iron, gold in an open lamp;
  oil burns yellower and smokier. Why: the lamps mystery's logic held nowhere
  else.
- **The body's hours.** An Unchained is cold as the river by night (the breath
  doesn't show; the heart slow, it can stop for a count of seven) and warm at
  dawn (the breath smokes). Every lover notices; none knows what it means until
  Act 2.
- **The survivor's mother.**
  - For every background, the survivor was coming home to her; she died the
    week before the ford.
  - She is buried in the Quiet Garden (a week-old marker in C08). Her letter,
    run to blue water, is in C01. Rook knew her if the survivor is a hunter, and
    says nothing.
  - At the bottom of the stair (C43) she says the survivor's name.
- **Counts.** Twelve irons forged, ten hung, two on Brannoc's rack.
  Twenty-six drowned before the survivor; Nell was the twenty-fifth; the
  survivor is the twenty-seventh, the first line not struck in Vonnra's ledger.
  Pell's deadline is nine days, Rav's pulse count seven, and Holloway has eleven
  men.
- **Extremes, one per act.**
  - Act 2: Nell's boots (Brannoc bought them with the irons money).
  - Act 3: ember is the dead (the player burned Nell, and hears "Da").
  - Rejected:
    - Vonnra choosing Nell (a third motive on one death, and it makes Nell a
      pawn);
    - the survivor having taken toll work (it fights C01 and takes the player's
      character from them);
    - Holloway selling the boots (two boot reveals in one act blur);
    - Chid pulling her out and building the fire (the prints say she walked).
  - Chid keeps one line in Act 3: "I go when the lamps are lit. I couldn't have
    stopped it. I didn't try. I wanted to see one get up."
- **Third layers of motive** for every named person, and the kindnesses from the
  wrong people (bible §5, end). Mostly never said.
- **Romance.**
  - Adopted: Sella, Maeca, Keegan's supper and Rav's back room are in Act 1's
    data; all five routes in Act 2 (Ysolde's only there).
  - Settled: `vonnra.f_past` reads `sella.past_sold`; the trust gate on Sella's
    free night; Rav's one refused drink at `sober`; Sella refuses once after the
    Roost burns.
  - Love scenes are not cinematics: each cut-away holds one object.
- **Cinematic choices.**
  - C09's vistas are on Vonnra's eyeline (her sight is a roof and a long
    memory), and the fortune is interrupted by the tremor.
  - C13 is a hand at the gate, not a kneel.
  - C41 is a ledger read aloud, not a villain's speech.
  - C14, The Road Back, gives the merciful route a night.
- **Keegan's duel at first light**, by her handbook's seventh article.
- **Grimtunnel never dies in an arena.**
- **The ending decides the nights.** After re-forging, the arenas stay. After
  breaking the chain, none. After taking the light, the survivor is the boss.
- **Vonnra's name** is written to stand alone at a pause, recorded as its own
  take, and spliced; the subtitle always carries it, never "traveller".

---

## 5. In progress, and its exact state

- **The story explorer's full run**, started to confirm (a) and (b). Command:
  `cd godot/tests && STORY_EXPLORE=full STORY_EXPLORE_OUT=<file> dotnet test --filter The_whole_story`
  (about 30 minutes). It was running in the background when this page was
  written. Its report would have gone to the scratchpad
  (`.../scratchpad/explore_full.md`), which you cannot rely on. **Rerun it.**
  - **Keegan's supper** should now show as reached: 25 and 10 is exactly its best
    before.
  - **Wenna's mask by the cure** may still be "unseen". The explorer's beam
    rarely reaches the cure (`beasts.outcome=cured` was unreached in the last
    run). That is the search, not the story: `RouteTests` play the cure end to
    end. If it reports, add it to `Accepted` in `StoryExplorerTests.cs` with that
    reason.
- Nothing else is half-made. The tree is clean and pushed.

---

## 6. What is next, in order

1. Rerun the explorer's full run (section 5), and settle anything it reports.
2. **Answer the voice agent's reads** (section 9) as they come. They are notes on
   lines; fix what is real, in the voice, and keep the tests green.
3. **The editorial's cheap Act 1 seeds** that are not yet in the data
   (`docs/editorial/THE_EMBER_REVEAL.md` §5, `IDEAS.md`, `LINE_NOTES.md`):
   - "gone to the Morrow" as the valley's idiom for dying (a folk line, Rook,
     Wenna refusing to say it);
   - Wenna: "I burn fat, child. Fat's honest. Fat was a pig.";
   - Chid's shrine flame, "for keeping company";
   - the ember shard's lore ("Hold it to your ear in a quiet room...");
   - Chid's death line wearing thin (I-10);
   - the town noticing settled threads (I-15);
   - Maeca's early "Ashford" (her voice rule);
   - the interface stating the twist (the `risen_once` trait's text; Problem 4);
   - the narrator and the tutorial sharing a line (LINE_NOTES 2.8).
   Each is a line or two. Hold each to the soul test and `VOICES.md`.
4. **C14's data:** the dusk node `brannoc.road` and the facts `nell.road` and
   `nell.brought_home`, once the systems agent gives story fights an ally and the
   Low Ford road at night (README §6, 11a to 13). Do not add the choice before the
   fight exists: "I'll show you" would lead nowhere.
5. **Act 2's text,** when the owner asks for it.
   - The outlines (`docs/cinematics/act2_outline.md`), the bible §7 and the
     romance scene files are the source.
   - Write the Act 2 cinematics up to the Act 1 standard as their content
     lands.
6. **Keep the editor in the loop** for anything large (section 9).

---

## 7. What was tried and failed (so you don't)

- **Worktree isolation refuses complex shell commands:**
  - heredocs with `git`;
  - `sed` with computed arguments;
  - pipelines naming git in odd forms.
  Write Python scripts to the scratchpad and run them as plain commands, with
  absolute paths. Use the Read and Grep tools instead of `sed -n` with
  variables.
- **C# single-line raw strings** (`$$"""..."""`) cannot hold a newline. Keep
  JSON inside them on one line.
- **CRLF.**
  - `Prologue.cs`, `Verge.cs` and `Waystation.cs` are CRLF in the working tree;
    anchors with bare `\n` miss.
  - Read and write them as bytes, normalise, and write back with the file's own
    endings.
  - The JSON content is written `indent=1, ensure_ascii=False`, CRLF
    (`newline='\r\n'`).
- **The romance data drafts** (`docs/romance/data/*.json`) were built on an older
  `dialogue.json`. Dropping them in whole deletes live work (C11's
  `rav.leg_held`, Maeca's guards). They are merged now; never paste them again.
- **The `Talk` test helper** used to advance only one narrated node; lead-ins have
  several. It now loops.
- **Krea's graph** wires width from the wrong selector output. Set
  `30:5.width=1536`, `30:5.height=640` for 2.39:1 boards. The prompt goes in
  `30:19.value`, the seed in `30:3.seed`, and `30:24.value=false`.
- **The editorial material** was written against an older bible: it thinks
  someone carried her to the fire, and it counts twelve drowned. Check anything
  you take from it against the bible.

---

## 8. Gotchas

**The dialogue format** (`godot/data/content/dialogue.json`; engine
`godot/logic/World/Dialogue.cs`):
- Conversations hold `npc`, `entry` (first match wins; the last entry must be
  unconditional) and `nodes`.
- A node holds `text`, which is a string or variants `[{when, text}]` (first
  match wins), plus `speaker`, `choices`, `effects` and `next`.
- **A node's effects apply before its text is chosen,** so a fact it sets cannot
  pick its own line. Set it on the choices instead.
- A choice holds `text`, `show` (hidden if false), `when` (locked if false and
  `locked` is given, else hidden), `locked`, `once`, `goto`, `action`, `end`,
  `effects` and `badge`.
- **Put "is it relevant" in `show`, and "can you do it yet" in `when`.** A
  `locked` reason shows whenever `when` fails, so it must never be shown for the
  wrong cause.
- Cond and Change are a small language:
  - facts (`fact`, `eq`, `gte`, `exists`), `history`, `npcFlag`, `rel`, `knows`,
    `hasItem`, `trait`, `archetype`, `bg`, `sex`, `time`, `day`, `quest`;
  - `set`, `add`, `quest`, `history` (with spread and reactions), `rel`, `give`,
    `take`, `gold`, `learn`, `later` (`{days, id, effect}`), `if`/`then`/`else`,
    `zone`.
- Narrator nodes use `speaker: "narrator"`.
- Each `cin_*` conversation (a cinematic's VO lines) needs a `speakers` entry in
  `npcs.json` with a glyph that exists in `glyphs.json`. One node per line, ending
  on a single `(Continue.)` end choice.

**Voice ids.** The scripts write them as `<conversation>.<node>#<variant>`; the
voice system files them as `dlg.<conversation>.<node>.<variant>`. A caption in
zone code is keyed by the hash of its words. No takes are recorded yet; once they
are, changing a line's words invalidates its take, and `VoiceTests` will say so.

**The tests.**
- `StoryLint.cs`:
  - every node is reachable;
  - every journal entry is defined and written;
  - every fact read is written, and every fact written is read or listed in
    `Seeds` (with a reason);
  - every item wanted is obtainable.
  - A fact read in zone code through `F("...")` under `godot/logic/` counts as
    read.
- `ContentTests.cs`: a conversation id must be a Person or a `speakers` entry;
  there are no dead ends.
- `CinematicTests.cs`: yours. It covers the cinematic lines, the canon and the
  voice rules.
- `RouteTests.cs` and `AuditTests.cs` play whole routes.
- `StoryExplorerTests.cs` and `docs/cloud/story-explorer.md`:
  - the explorer's quick run goes with every `dotnet test`;
  - the full run uses `STORY_EXPLORE=full` and takes about 30 minutes;
  - its `Accepted` list takes findings that are how the story is meant to be,
    each with a reason.
- **Fortunes are read only after dark:** test helpers set `TimeOfDay.Night`.

**`folk.json`** lines take `"night": true` (night only) or `false` (day only).

**The cinematics README** is the production brief. Its section 9 (triggers) and
section 6 (needs) are what the cinematics production agent builds from: keep
them true when you change a script.

---

## 9. Collaborators

- **The story editor** (agent `adf97e52f8dfede35`, ref `de8cfc`).
  - It has done four rounds and knows the bible, the scripts, the editorial and
    the romance.
  - Resume it with SendMessage to `adf97e52f8dfede35`. It is read-only and sends
    notes; you keep the final say.
  - Give it the context and the soul test. Ask for notes in priority order, with
    replacement lines in the voice.
- **The voice agent** (`a2da9a388ceb1b987`, "Cinematic voice-over production").
  **Expect its reads:** it will send notes on lines as it directs them.
  - Verify each against the data.
  - Fix what is real, in the voice.
  - Answer what is a choice.
  - Keep `VOICES.md` the authority.
- **The coordinator** (the main session) relays the owner and merges branches.
  Report to it briefly when a task is done.
- Other agents (not yours): skills and balance (`a09e0860794ed3e5c`), UI
  (`ad1a039caf3923eec`), animation (`a50313d92b0c7aba2`). The systems agent owns
  arenas, bosses and the bestiary; give it the story's view in the bible, not in
  its code.

---

## 10. Open questions for the owner (with my recommendation)

1. **Ember is the dead:** keep it (adopted).
2. **The survivor's mother for every background:** keep it. Whether the player
   names her at creation is a system to decide. If yes, her name is on the
   marker in C08.
3. **Act 3's major dark turn:** ember is the dead, with Chid's one line, not "Chid
   watched the drownings" in full.
4. **Which romances exist:** all five (Ysolde's in Act 2 only). The six explicit
   scenes behind `settings.intimacy` are left to the owner's writer, with beat
   sheets in `docs/romance/scenes/`.
5. **The concept art's register:** the prose's restraint, at least near the
   intimate scenes. Note that the owner has asked for strong sex appeal in the
   outfits; this is about tone in the writing, not the art direction.
6. **Endgame:** the ending decides the nights (section 4).
7. **Greymuzzle let go** (a fight outcome): accepted narrowly (bible, "The
   nights").
8. **Ysolde selling false names with the survivor's consent:** yes.

---

## 11. Read these first

1. This page.
2. `docs/STORY_BIBLE.md`: the canon; sections 1, 3, 5 (with its end:
   third layers, kindnesses, extremes), 7, 8, "The nights", 10 and 11.
3. `docs/VOICES.md`: how everyone talks, and the rules each may break once.
4. `docs/cinematics/README.md`: the brief, the soul test (§2), the visual
   language (§4), the needs (§6), the index (§7) and the triggers (§9).
5. `docs/cinematics/c09_fortune.md` and `c14_road_back.md`: the standard a
   script is held to.
6. `docs/WRITING_PASS.md`: Act 1's spec; §9 (seeds and payoffs) and §16 (the
   explorer's findings).
7. `docs/cinematics/act2_outline.md` and `act3_outline.md`.
8. `docs/editorial/EDITORIAL_LETTER.md` and `THE_EMBER_REVEAL.md`: the
   editorial thinking behind the canon.
9. `docs/romance/README.md` and `ARCS.md`.
10. `docs/cloud/story-explorer.md`.
11. `godot/tests/StoryLint.cs` and `godot/tests/CinematicTests.cs`.
