# Handoff: the story and writing lead (Survivor Unchained)

You own the game's story: the canon, every word the game says, the cinematic
scripts and the story data. You also sign off every voice packet before the
owner records it. Read `docs/team/README.md` first (the owner's bar, how we
work, safety, the roster), then this page, then the files in section 9.

- **Branch:** `worktree-agent-a7622ae77d19e31dc`. The integration branch is
  `origin/claude/vigilant-galileo-l6jqyx`: merge it in first, and often.
- **Tests:** `cd godot/tests && dotnet test` (519 pass). Keep them green before
  every commit, then push. Open no PRs.
- **Commits:** write the message to a file and use `git commit -F`.
  PowerShell 5.1 breaks double quotes in `-m`. End every message with
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

---

## 1. The owner's words

- "AAA standard", "strive for excellent, above and beyond - not just good
  enough"; "the excellence bar isn't just for hair, its for literally
  everything".
- "Never settle": remake rather than polish. "Do we have soul?" Unique, specific
  to this world, never a line any other game could use. This is the soul test
  (`docs/cinematics/README.md` §2).
- "always be critical, if you notice something you missed earlier... don't be
  afraid to revisit it."
- Writing: twists, cohesion, variance from decisions, correct breadcrumbs.
  "depth, development, and care". Every person wants something, hides
  something, and changes or is revealed.
- 18+ dark fantasy. British spelling. Sex appeal is a driving factor for the
  heroine's look; in the prose, keep the restraint.
- On 4 October:
  - "should [Vonnra] be the narrator? someone who calls us to the town when we
    'wake up'". Decided (section 4).
  - "story should be 40% of the game early on, end game is two types of
    arenas - permanent and our normal arenas. permanent is our arpg build maps
    like poe and the normal arenas are for mindless survivors fun". Written into
    the bible (section 4).
  - The endless phase is truly endless, with no Dawn at 60:00.
  - The final voices are recorded by the owner in ElevenLabs, one character at
    a time, from the voice lead's packets. You make every line final first.

## 2. Your brief

1. Keep the canon true and the writing at the bar: the bible, VOICES, the
   Act 1 data, the cinematic scripts, and Act 2 when the owner asks.
2. **Sign off voice packets before recording.** Read each packet
   (`docs/voice/elevenlabs/<voice>.md` on the voice lead's branch) line by line
   against the data. Fix any line that's wrong in the data. Give direction notes
   (wants, hides, beats). Then reply "<voice> final". Once it's final, change no
   line in it without telling the voice lead.
3. Answer the other leads' story questions (cinematics, combat, experience,
   UI), with the story's view written in the bible, not in their code.
4. Keep `docs/team/story.md` to one page.

## 3. State: done, in progress, next

**Done this session** (`docs/WRITING_PASS.md` §17 to §19 has every line):
- **The explorer's full run** found nothing. Keegan's supper and Wenna's mask by
  the cure are played end to end in `RouteTests`; the explorer never cures the
  stream.
- **The editorial's cheap seeds**, all in the data:
  - "gone to the Morrow";
  - Wenna's tallow;
  - Chid's flame "for keeping company";
  - the ember items' lore;
  - the carter wearing thin, counted by `player.deaths`, with "Which carter,
    Chid?";
  - the nemesis names;
  - the trait;
  - Maeca keeping "Ashford" (her plate is "Hunter, of the Hollow");
  - Keegan's kenning on "Ash-of-Morrow".
- **The town notices.**
  - `npcs.json` `said`: barks with `when`, `night` and `once`.
  - `ZoneRuntime.Wire`, `SaidNow`, `FirstTime` and `MarkSaid` drive them; the
    voice ids are `bark.<npc>.said.<i>`.
  - Every stale bark moved there, and each person has a line for how their
    thread ended.
- **The story editor's round five** is taken: phrase collisions fixed,
  Grimtunnel's "surface-m—", the echo habit cut, Brannoc's "Twelve, I made."
  said once.
- **Boss barks:** the Barrow Lord's plural Latin orders (Tenete, Iungite,
  Testudo) and Grimtunnel's going-down line. Grimtunnel's story title is now
  "Ever So Grateful".
- **Delivery directions are lower case** (a VOICES rule): the actor plays them,
  and the narrator never reads them.
- **The zone condition cache is concurrent.** It was a flaky-test race, about
  one run in three.
- **Creation names:** no suggested name spends a story name. The default is
  Wren.
- **The owner's two questions** are decided and written up (section 4). The
  voice up the road is in C01's data, the prologue's captions, and two
  placeholder shots in `godot/data/cinematics/c01.json` for the cinematics lead.

**Voice packets:**

| Voice | State |
|---|---|
| Narrator | **Final** (plus two new C01 takes to add: `cin_drowned_fire.lamp`, and the call in Vonnra's packet) |
| Rook | **Final** |
| Holloway | **Final** (direction fixes applied) |
| Brannoc | **Final** (direction fixes applied) |
| Sella | **Final once** her eight split quotes carry her own direction and morning.0/1 are realigned; morning.0's hide is the sale to Vonnra (`sella.cold_sold`) |
| Vonnra | **Next: read it.** Voice branch `a501b387…@1fd50ad`, 102 takes. Check the realigned f_ember notes, the name-splice notes and the new direction for the name takes; add the C01 call (`far_voice`) |
| Harlan | **Next: read it.** `@1fd50ad`, 63 takes |
| All others | After Harlan, in the README's order |

**Next, in order:**
1. **Vonnra's packet, then Harlan's.** Method: `tools/story/packet_check.py
   <packet> --full`. Then read for:
   - wants and hides at the top;
   - the narrator's "plain" leaking into a character's split quotes;
   - stale notes quoting old words;
   - [whispers] that will go breathy.
2. **"The town talks about your nights."** The experience director is pushing
   `arena.last.*` facts:
   - people, won, fell, story, tier, minutes, past, day, longest, killer;
   - plus the counts `arena.nights` and `arena.fell`.

   Once those are on the integration branch, write gated, once-only "said"
   barks and callbacks, in voice:
   - Chid after a fall;
   - Rook after a night past the boss;
   - Maeca after a Pack night;
   - Rav after a Kerchief night;
   - the Wayfinder on a new longest;
   - Holloway after a boss.

   The target: after any night, someone says something.
   - The facts are pushed on `worktree-agent-a33f58e68e89e3ccf@e908434`, for
     the main session to merge. Start once they're on the integration branch.
   - StoryLint lists them as seeds. Take each off the `Seeds` list as a line
     reads it; the test enforces that.
   - `arena.nights` and `arena.fell` are counts the code already reads.
3. **Word the night's announcements by the night, not the clock.** Story
   nights are 20 minutes, so no "half hour". Combat (`ac4ec5bbd2763a0df`) is
   building the one clock and will send the strings. I suggested defaults to
   the experience director: "It is nearly here", "The night's end", "past its
   coming", "Halfway through the dark".
4. **C14's data** (`brannoc.road`, `nell.road`, `nell.brought_home`). This
   waits until story fights have an ally and the Low Ford road by night exists.
5. **Act 2's text** when the owner asks (`docs/cinematics/act2_outline.md`,
   bible §7).

## 4. Decisions, and why (all in the bible)

- **Vonnra is not the narrator. She is the voice up the road, once.** (Bible §2,
  "Who tells it".)
  - Why not the narrator:
    - her sight is bought, and the narrator knows what nobody could sell her;
    - a voice the player has heard for an hour gives the twist away on day one;
    - her power is scarcity;
    - a buyer's voice would ruin the private scenes;
    - the narrator never lies.
  - What we do: at the waking, an unnamed "A voice up the road" says "Come up,
    traveller. ...No charge, this once." The fortune opens on the same words.
- **Pacing** (bible §2, "Pacing"):
  - early on, the story is 40%: a day is about 20 minutes, a story night 20
    minutes, a Wayfinder map 30;
  - a story night ends on its story beat;
  - the endgame has two kinds of arena: permanent (the Wayfinder's atlas, the
    build game) and a night's scar (the survivors' game);
  - both exist after every ending. After B they are "the Wayfinder's book of
    the nights that were". That is recommended, and is the owner's call.
- **The endless hour is truly endless:** the dawn is on the other side of the
  open way out.
- **Chid carries the survivor in after every death;** the carter is his lie.
- **Signature phrases are never shared:** "Someone always does" is Vonnra's,
  "before you ask" is Maeca's, "Not there... Here." is Keegan's. Repetition for
  weight belongs to Chid and Keegan only.
- **Grimtunnel** never dies in an arena, and never finishes "surface-meat" at
  her after C03.
- **Narration in voice:** the narrator plays no feelings (pauses and volume
  only), whispers four times, never whispers in love scenes, and never says a
  person's quoted words.

Everything from before this session still stands: ember is the dead, oil and
ember, the body's hours, the mother, the counts, one extreme per act. See the
bible §1 and §5.

## 5. What failed, so you don't repeat it

- **Rewriting a hand-formatted JSON file** (`data/cinematics/*.json`) with
  `json.dumps` produced a 1,100-line diff. Insert text in the file's own layout
  instead. The content JSON (`godot/data/content/*.json`) does round-trip:
  indent 1, `ensure_ascii=False`, CRLF, a trailing CRLF.
- **Shared scratchpad:** other agents share it and overwrote my `show.py`.
  Give your scripts unique names.
- **Complex bash in this worktree** gets refused by the isolation check. Write
  a Python script and run it with a plain command.
- **The story explorer's full run** can't prove deep routes; its beam never
  cures the stream. Prove a deep route with a `RouteTests` play instead.

## 6. Gotchas

- **Dialogue format** (`godot/logic/World/Dialogue.cs`):
  - a node's effects apply before its text is chosen;
  - "is it relevant" goes in `show`, and "can you do it yet" in `when`;
  - variants: first match wins, and the last must be unconditional.
  - **Adding a variant shifts its voice id** (`dlg.<conv>.<node>.<i>`), so tell
    the voice lead.
- **New folk lines go at the end** of `folk.json`: a folk line's voice id is its
  index.
- **Parentheses inside a person's line:**
  - lower case is a delivery direction ("(quietly)");
  - a capitalised sentence is the narrator's ("(He looks at his hands.)");
  - in a narrator node, a quote belongs to the conversation's person, unless
    it is written words.
- **{name}** cannot be recorded. Takes drop it, and the subtitle keeps it.
  Vonnra's name is spliced from 24 name takes.
- **The cinematics lead's `CinemaTests`** check that a timeline says every line
  of its conversation in order. A new `cin_*` node needs a cue in
  `godot/data/cinematics/cNN.json` (tell the cinematics lead).
- **StoryLint:**
  - every fact read must be written somewhere, including the C# JSON in zone
    code;
  - every fact written must be read, or be listed as a seed;
  - every node must be reachable.
- **Fortunes are read only after dark:** tests set `TimeOfDay.Night`.

## 7. Collaborators (the roster in `docs/team/README.md` is the address list)

- **Voice lead** `a501b387a90d78b4e`: the packets, the importer, the name splice.
- **Cinematics lead** `af7a79bc783cca7bc`: C01 to C04 shooting scripts and
  timelines. They are framing C01's 8a/8b (an L-cut, the lamp a far gold
  point).
- **Experience director** `a33f58e68e89e3ccf`: pacing, and the `arena.last.*`
  facts.
- **Combat** `ac4ec5bbd2763a0df`: the night clock, bosses, and the strings that
  need wording.
- **Story editor** `adf97e52f8dfede35`: read-only. Five rounds done. It couldn't
  be resumed at the end ("worktree unverifiable"); retry, or spawn a fresh
  editor with the context. Keegan's kenning line ("Ash-of-Morrow... a kenning,
  almost") has had no editor's read yet.
- **The coordinator** (main session): relays the owner and merges branches.

## 8. Open questions for the owner

1. The hymn at Nell's grave (C08) must be sung. Who sings it: Eleven Music, a
   singer we have the rights to, or a licensed synth? See the voice README.
2. After ending B, are the endgame nights the Wayfinder's book of the nights
   that were? (Recommended; bible §8.)

## 9. Read these first

1. `docs/team/README.md`, then `docs/team/story.md`.
2. `docs/STORY_BIBLE.md`: §1, §2 (Pacing; Who tells it), §3, §5, "The nights", §8
   and §9.
3. `docs/VOICES.md`: the rules at the top, then each person.
4. `docs/WRITING_PASS.md` §16 to §19.
5. `docs/cinematics/README.md` (the soul test, the triggers),
   `c01_drowned_fire.md` and `c09_fortune.md`.
6. `docs/voice/elevenlabs/README.md` on the voice lead's branch, and
   `tools/story/packet_check.py`.
7. `godot/tests/CinematicTests.cs` and `godot/tests/StoryLint.cs`.

HANDOFF READY: docs/handoff/story.md on worktree-agent-a7622ae77d19e31dc@(see the commit that adds this page)
