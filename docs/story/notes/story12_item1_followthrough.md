# Worker brief: Story 12 item 1, the mechanical follow-through of the romance removal

Context budget: 150k
Item: romance removal follow-through
You report to the writer (Story 12) that spawned you: return a short written report (what changed per file, test counts, lock counts, anything you could not do and why). Do NOT commit; stage nothing; leave the working tree edited for the writer to review and commit. Do not create worktrees. Work only in `C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\story-wtf` (branch story-wtf). Use absolute paths. American spelling in any game-facing text.

## What already happened (commit 1dddf45e)
The writer removed the romance routes and love scenes from `godot/data/content/dialogue.json`:
- sella: nodes `stairs_room`, `stairs_rules`, `stop_paid`, `night`, `morning`, `rest_night_paid`, `free_stop`, `free_want`, `free_sleep`, `free_sleep_bed`, `free_bolt`, `free_night`, `free_morning`, `free_m_downstairs`, `free_m_kiss` are GONE. `price` now offers only "15 gold. But I only want to sleep." (-> `rest_night`, or `refuse_roost` on the Roost variant) and "Just the talk, for now.". `rest_night` ("Yes.") -> `stairs` (narrator, no gold effect now) -> `stairs_say` -> `rest_bed` -> `rest_dark` -> `rest_morning`. Her free night: `free` -> `free_stairs` -> `free_door` (2 variants, choices "(Sit with her.)" -> `free_sit`, "Sella. What is this?" -> `free_what` (NEW) -> `free_sit`); `free_sit` sets `sella.free` and offers "Who'd you sell it to? If I did?" -> `free_m_who`. `say_maeca` entry is keyed to `maeca.blind_nights >= 1`.
- maeca: nodes `blind`, `blind2_feet`, `blind2_let`, `watch_morning`, `say_sella`, `say_sella_both`, `say_sella_you`, `say_sella_dunno` are GONE (and the `say_sella` entry). `blind_ask` choices: "I won't." (first night) / "(Feed the fire.)" (later) -> `watch_only`; "(Go back to town.)" -> `blind_leave`. `watch_only` (narrator, 2 variants) adds `maeca.blind_nights`, gives `rested`, -> `blind_dark` (4 variants, by the fire) -> "(Sleep.)" -> `blind_morning`, or the told_* answers -> `blind3_morning`. The fact `maeca.lover` no longer exists anywhere; `maeca.blind_nights` replaces it (greymuzzle.show's variant too).
- keegan: `dinner` and `supper_hand` GONE; the hub choice "Does the handbook say anything about dinner?" is gone; "It's late. Have you eaten?" shows at night, gated on respect >= 25 only; "(Take her hand.)" is gone from every supper node.
- rav: `back_room_kiss` GONE, "(Kiss him.)" gone; the back-room lock text is "He'd buy you a drink. That's all."

Your job is everything that still refers to the old shape: tests, the voice tools, the directions and locks, and the docs. Exact edits follow. Where a line number is given it is approximate (the file may have shifted by a few lines): find the quoted text.

## A. Tests (godot/tests)
1. `StoryRewriteTests.cs`: delete the whole method `The_narrator_stops_at_the_door` with its `/// <summary>` block. In `Maeca_is_just_Maeca`, change the comment phrase "bare on the ground at the fire, held in the dark (notes 02 section 6.2)" to "bare on the ground at the fire (notes 02 section 6.2)". Remove a `using` only if it becomes unused and the compiler warns.
2. `QuestTests.cs`, `A_night_with_Sella_is_paid_up_front_and_leaves_you_warmed` (about line 190): rename to `A_night_in_the_blue_room_is_paid_up_front_and_is_only_sleep`. Body: `s.Ch.Gold = 20; Talk(Convo("sella"), s.C, "how much", "only want to sleep", "Yes");` then `Assert.Equal(5, s.Ch.Gold)`; assert `s.Ch.Conditions` contains `ConditionId.Rested` and contains no `ConditionId.Warmed`; `Assert.Equal(1, s.World.Fact("sella.nights").Number)`. Delete the Warmed stat-equality block and the whole "stop here" block (`stop` variable). Keep the poor-gold check but with the choice text "only want to sleep" instead of "15 gold, then". Comment: "Paid at the foot of the stairs; the only thing to buy up them is the room and the sleep."
3. `QuestTests.cs`, `Maeca_asks_once_the_Pack_is_settled_and_the_scene_cuts_away_unless_asked_not_to` (about line 437): rename to `Maeca_asks_once_the_Pack_is_settled_and_the_Blind_is_a_watch_night`. After `var p = Talk(Convo("maeca"), s.C, "keep quiet", "I won't");` assert `p!.Node.Id == "watch_only"`, `p.Text` contains "frost is on both your shoulders", `s.World.Fact("maeca.blind_nights").Number == 1`, `Assert.False(s.World.Fact("maeca.lover").Truthy)`, conditions contain `Rested` and no `Warmed`. Delete the `settings.intimacy` line and the "[explicit" asserts. Second night: `p = Talk(Convo("maeca"), s.C, "big enough for two", "Feed the fire");` assert `p!.Node.Id == "watch_only"`, `p.Text` contains "sooner than she did the first time", `blind_nights == 2`. (Talk returns the node the choice lands on, after its effects, without following `next`; it does follow `next` chains to reach the next choice node.)
4. `RouteTests.cs`, `Keegan_sups_with_whoever_read_the_watchmans_book_and_found_Ashe` (about line 659): delete `p.Talk("keegan", "dinner");` and the following `Assert.DoesNotContain(p.Offered("keegan"), c => c.Contains("Have you eaten"));`. In the comment, "the dinner she refuses, and back after dark" -> "and back after dark".
5. `BreadcrumbTests.cs` (about line 329): `Talk(Convo("sella"), f.C, "how much", "15 gold, then", "kiss her", "where you come from")` -> `Talk(Convo("sella"), f.C, "how much", "only want to sleep", "Yes", "where you come from")`.
6. `CinematicTests.cs` (about line 174): `m.World.Facts["maeca.lover"] = true;` -> set `maeca.blind_nights` to 1, stored the way other tests store numeric facts (look at how `sella.nights` or any numeric fact is assigned elsewhere in the tests, and match the type).
7. Grep `godot/tests` for `maeca.lover`, `kiss her`, `take her hand`, `15 gold, then`, `stop here`, `free_bolt`, `Warmed`, `"dinner"`, `blind2`, `watch_morning`, `say_sella`, `settings.intimacy`; fix any other hit in the same spirit and list each in the report. `ConditionId.Warmed` stays in the enum and in SelfScreen (unused now): do not touch C# source outside tests.

## B. tools/vo
8. `tools/vo/elevenlabs.py`: remove the "Behind the door" block (the comment starting "# Behind the door (docs/story/LOVE_SCENES.md", `DOOR`, `DOOR_BOLT`, `BOLT`, `DOOR_WHY`, `behind_door`, and the branch in the hold-reason function that returns `DOOR_WHY`), the `and not behind_door(...)` at about line 285, the comment at about 292 about the bolt, and the `behind_door` uses at about 378-380. `tools/vo/import_takes.py`: remove the three `E.behind_door` uses (the refusal at ~91-92, the conditions at ~104 and ~197) so the code behaves as if `behind_door` were always False. Everything else identical.
9. Delete `tools/vo/tests/test_door.py`. In `tools/vo/README.md` (and `docs/voice/README.md` if it exists) remove any sentence about the door rule / the narrator never recorded behind the door.
10. `git mv tools/vo/direction/love_b.json tools/vo/direction/late_nights.json`. Run `python tools/vo/lines.py` (regenerates `tools/vo/manifest.json`), then `python tools/vo/check_ids.py`. Prune from every direction file (`late_nights.json`, `additions.json`, `sella.json`, `maeca.json`, `keegan.json`, `rav.json`) the entries whose ids no longer exist; keep entries for surviving ids. Repeat until check_ids is clean. Then update the `note` of the surviving entries whose staging changed, in short plain prose: `dlg.sella.free_door.0/.1` (lamp up; she sits on the bed and pats the quilt; not a dark room), `dlg.sella.free_sit.0` (the two of them sitting; the lamp burning down; she sends you down), `dlg.sella.free_m_who.0` (at the door, her shawl up), `dlg.maeca.blind_dark.*` (by the fire, back to back, never under hides), `dlg.maeca.blind3_morning.0` (back to back, not head on chest), `dlg.maeca.blind_morning.1` (she woke you with a hand on you; you kept quiet), `dlg.maeca.blind_ask.*`, `dlg.maeca.watch_only.*`. Any file-level `_doc`/about key that says "love scenes" or "B" -> "the blue room and the Blind (28 October: no romance)".
11. Locks: `python tools/vo/lock.py --list`. Locks whose id is gone (removed nodes) must be removed from `tools/vo/locked.json` (read `lock.py` for a prune/unlock path; if there is none, remove them with a small Python script through the module's own load/save). Locks that are BROKEN because the writer changed the words (sella `free_door`, `free_sit`, `free_m_who`, `say_keegan`, `refuse_roost`; maeca `blind_ask`, `blind_dark`, `blind_morning`, `blind3_morning`, `blind3_m_no`, `gone`, `watch_only`; greymuzzle `show`) are deliberate rewrites: re-lock them with lock.py's lock path. Report counts before and after; `python tools/vo/lock.py --check` must exit 0.
12. `tools/vo/cast.json`, the sella entry's "hides" text: replace the part "every intimate scene has a buyer listening, until she stops (sella.free)" with "every night in the blue room has a buyer listening, until the one night she sits with you for nothing (sella.free)". Keep the rest of the sentence.
13. `cd tools/vo && python -m unittest tests.test_lock tests.test_lines` must pass (test_import_takes needs librosa, skip it).

## C. Docs
14. `docs/voice/RERECORD.md`: replace the whole paragraph that starts "**Locked for recording (11 October, later): the love scenes, B, after their judge.**" with:
"**28 October: the love scenes and the romance routes are removed (the owner).** Sella's blue room keeps the stairs, the paid sleep and its mornings; her free night is now the night she sits with you (`free_door`, `free_what`, `free_sit`, `free_m_who`). Maeca's Blind keeps the walk, the fire, the watch nights (`watch_only`, `blind_dark`) and the gray lights. The nodes `sella.stairs_room`, `stairs_rules`, `night`, `morning`, `stop_paid`, `rest_night_paid`, `free_night`, `free_bolt`, `free_sleep`, `free_sleep_bed`, `free_want`, `free_stop`, `free_morning`, `free_m_downstairs`, `free_m_kiss`, `maeca.blind`, `blind2_feet`, `blind2_let`, `watch_morning`, `say_sella*`, `keegan.dinner`, `supper_hand` and `rav.back_room_kiss` are gone; any take saved for them is unused. The door rule (the narrator never recorded behind the door) is retired with them."
In the Sella section's "Renamed only" table, append " (removed 28 October)" to the Why cell of the two rows (`night.1.p1`, `free_night.1.p1`). Find the subsection about "The love scenes (B)" and prefix its first paragraph with "**Removed 28 October; history only.** ".
15. `git mv docs/story/LOVE_SCENES.md docs/story/notes/history_love_scenes_b.md`, then prepend exactly:
"# RETIRED (28 October 2026): the love scenes, B

The owner removed the love-scene options and the romance routes (OWNER_NOTES, 28 October). Sella stays who she is and likes the survivor; her free night is now the night she sits with you (`sella.free_door`, `free_what`, `free_sit`). Maeca's Blind is the watch night (`watch_only`, `blind_dark`, the gray lights). Nothing below is in the game. Kept as the history of B.

---

" (then the old content unchanged).
16. `docs/romance/README.md`: prepend "**RETIRED 28 October 2026:** the romance routes and love scenes are out of the game (the owner). Affection stays: Sella's free night, Maeca's watch nights, Keegan's supper, Rav's surgery. This folder is history.\n\n".
17. `docs/story/TREATMENT.md`:
   - The bullet "- **Love scenes: B, the lovers' own lines** (the owner, 6 October; `LOVE_SCENES.md`): the narrator stops at the door, and silent narration in the room can't read as her mother having been there. A is the fallback." -> "- **Love scenes and romance routes: removed** (the owner, 28 October). Sella keeps her warmth and her free night (she sits with you); Maeca's Blind is a watch night; Keegan's supper and Rav's surgery are friendship. `docs/story/notes/history_love_scenes_b.md` is the history."
   - In §3.4 "The plants", delete plant 5 ("**The narrator never enters a bedroom.** ... Players read it as a rating choice.") and renumber 6-9 to 5-8.
   - "(If she is the survivor's lover, it is the hand she has held.)" -> "(If the survivor has kept her fire at the Blind, it is the hand that woke them there.)"
   - "If she is the survivor's lover and the survivor says her name, Maeca looks at her: "You were up."" -> "If the survivor has kept her fire and says her name, Maeca looks at her: "You were up.""
   - "7. **Worse if she is the lover:** the same scene; the hand that pulled her up cut his rope; "You were up."" -> "7. **Worse if the survivor kept her fire:** the same scene; the hand that pulled her up cut his rope; "You were up.""
   - "the love scenes as the lovers' own lines (B);" -> "the blue room and the Blind as affection, not romance (28 October);"
   - "3. Love scenes: B, the lovers' own lines (6 October; `LOVE_SCENES.md`)." -> "3. Love scenes: B (6 October); then removed with every romance route (28 October)."
18. `docs/STORY_BIBLE.md`:
   - "Every lover notices it in their own trade's words, and none of them knows what it means until Act 2." -> "Everyone who sleeps near the survivor notices it in their own trade's words (Sella's hand on a cold chest, Maeca's back against yours, Rav's ear at your back), and none of them knows what it means until Act 2."
   - In "Who tells it" item 1: "the survivor's own mind ("your mother's face... not quite where you left it"), Maeca's lips against your chest, the Blind, Sella's free night." -> "the survivor's own mind ("your mother's face... not quite where you left it"), the Blind, Sella's free night."
   - Table row: "Act 1 (the fortune quotes your pillow talk)" -> "Act 1 (the fortune quotes what you told her in the blue room)".
   - "and the lover's "a lad I'd been fond of"" -> "and her "a lad I'd been fond of"".
   - "the fortune quotes what the survivor said in Sella's bed." -> "the fortune quotes what the survivor told Sella in the blue room."
   - "spares the survivor and is disgraced; the survivor's lover, as a tragedy, if Act 2 opens that route." -> "spares the survivor and is disgraced."
   - "A lover with a motive, though not a cruel one:" -> "A friend with a motive, though not a cruel one:".
   - "Her romance's "I've lain with my ear to a lot of things to see if they'd live." Never said." -> "Her watch night's "I've lain with my ear to a lot of things to see if they'd live." Never said."
   - "- `maeca.blind_morning` (romance): the Pack saved her after Ashford." -> "- `maeca.blind_morning` (the first watch night): the Pack saved her after Ashford."
   - "The night before is the eve (`romance.eve`, section 11): one night, with one of the open romances, or alone, or on the wall." -> "The night before is the eve: one night, alone, or on the wall with whoever stands there (no romance: section 11)."
   - Endings table row "| Maeca | Leaves with the Pack; takes the Watch; dies at the edge; the survivor's | `maeca.lover`, the Pack, the boots |" -> "| Maeca | Leaves with the Pack; takes the Watch; dies at the edge | `maeca.blind_nights`, the Pack |".
   - Replace the whole of "## 11. Romance" (from that heading through the end of "### Intimate scenes: fade to black", i.e. everything before "## 12. Facts the story keeps") with the text in the block below, verbatim.
19. `docs/cinematics/act2_outline.md`: "the romance's private reading, `keegan.ch4_read`" -> "her private reading, `keegan.ch4_read`"; replace the whole "- **The eve.** ..." bullet (through the sentence that cites "Love scenes") with "- **The eve.** The night before is one night, alone or on the wall with whoever stands there. Not a cinematic." `docs/cinematics/act3_outline.md`: "Keegan, a lover" -> "Keegan". `docs/cinematics/c05_kneeling.md`: "and, for her lover, Maeca's" -> "and, after a night at Maeca's fire, Maeca's" (read the sentence; keep it grammatical); "`maeca.lover`" -> "`maeca.blind_nights`"; "(Maeca's lover: he moves" -> "(After a night at Maeca's fire: he moves"; "with its variant for Maeca's lover" -> "with its variant for a night at Maeca's fire". `docs/cinematics/README.md`: replace the paragraph starting "**Love scenes are not cinematics.**" with "**There are no love scenes** (the owner, 28 October): the romance routes are out of the game; `docs/romance/` is history."
20. `docs/items/ACQUISITION.md` (two places) and `docs/items/CATALOGUE.md`: "Maeca's Last Arrow" is keyed on `maeca.lover`; change the key to `maeca.heard_heart` and the wording "only if she becomes the survivor's lover" -> "only if the survivor kept her fire at the Blind three nights (`maeca.heard_heart`)", "Maeca, if she is the survivor's lover" -> "Maeca, if the survivor kept her fire".
21. `docs/art/MODELS_TO_MAKE.md`: "a romance from the first night" -> "the blue room from the first night"; "A romance lead whose figure is part of her trade" -> "A lead whose figure is part of her trade"; "65 lines; romance; C23" -> "65 lines; C23"; "romance in Act 2" -> delete that phrase (keep the cell's other text and separators valid).
22. `docs/handoff/story_editor.md`: "**Rules:** love scenes fade to black." -> "**Rules:** no romance routes and no love scenes (the owner, 28 October); affection stays."; "I praised and protected: the romances," -> "I praised and protected: the romances (since removed, 28 October),".
23. Leave `docs/handoff/story.md`, `docs/team/*`, `docs/editorial/*`, `docs/legal/*` alone.

## The bible §11 replacement text (verbatim)
```
## 11. Affection, not romance

The owner removed every romance route and love scene on 28 October 2026
("remove the love scene options and relationships - though sella for example
won't change the way she is - she does like us"). Affection and loyalty stay;
no route leads to a bed, and no fact says "lover". The history of the cut
scenes is `docs/story/notes/history_love_scenes_b.md` and `docs/romance/`.

- **Sella** is exactly who she was: the blue room's professional ("Talk's
  free. The rest isn't."), who sells what is said upstairs, Vonnra above all.
  The survivor never buys her: "How much for the night?" leads to the room and
  the sleep (`sella.rest_night`: "You've paid fifteen gold to sleep."), the
  climb (`stairs`, `stairs_say`), the dark (`rest_dark`: "Somebody ought to
  watch you.") and the morning, where she feels the cold in you
  (`sella.felt_cold`, sold on as `sella.cold_sold` while she still sells you)
  and may hear where you come from (`sella.past`, `sella.past_sold`). After
  three paid sleeps and enough warmth she gives the one thing she never sells:
  a night off the clock in which she sits with you (`free`, `free_stairs`,
  `free_door`, `free_what`, `free_sit`: the green door in the south, and
  "Don't tell me anything up here you'd not want Vonnra to hear"). Fact:
  `sella.free` (she has stopped selling you). She likes the survivor; nobody
  says so.
- **Maeca** asks the survivor out to the Hunters' Blind once the Pack's
  trouble is settled (`maeca.invite`; then the hub on any night). Every night
  there is a watch night (`watch_only`): the survivor keeps the fire, she keeps
  the dark, and after midnight she sits down with her back against theirs.
  Night 1's gray light is the Pack after Ashford ("Don't make it a story.");
  night 2 is her feet, two toes short, and "Holloway doesn't know that";
  night 3 is her question across the fire ("What were you?", `told_true`,
  `maeca.heard_past`) and the heart she counted through her back
  (`blind3_morning`, `maeca.heard_heart`). Fact: `maeca.blind_nights`.
  Greymuzzle smells her fire on you (`greymuzzle.show`); Sella reads more into
  her humming than there is (`sella.say_maeca`).
- **Keegan**'s supper on the wall (`keegan.supper`, "a meal taken in company
  for the purposes of morale") is friendship: the bread, Saint Wend's, the
  letters, the handbook read aloud, and chapter four closed. No hand.
- **Rav**'s back room is his surgery (`rav.back_room`): he examines you, finds
  you cold and nothing wrong, and sends you home. No kiss.

What everyone who sleeps near the survivor notices is **the body's hours**
(section 1): cold as the river all night, warm by breakfast; the heart a
bear's in January by night and a hare's at dawn. Sella says it first ("Rook's
got a word for that. It's not a nice word."); nobody names it before Act 2.
What the survivor tells Sella of their past reaches Vonnra only while Sella is
still selling them (`sella.past_sold`, set before her free night); the fortune
reads that, not `sella.heard_past`.

### Intimate scenes: none

There are no intimate scenes in the game (28 October). The base game was
never explicit (`docs/legal/LEGAL_BRIEF.md` issue 6) and is now not even
suggestive: nothing is keyed to `settings.intimacy`, `StoryLint` still fails
any explicit slot, and the condition `warmed` has no source (it stays in the
enum, unused). The Act 2 scene notes in `docs/romance/scenes/` are history.
```

## D. Acceptance (run all; report the numbers)
- `cd godot/tests && dotnet test` (about 4 minutes; no GPU turn needed): all pass, 0 failed. Report the passed/failed/skipped counts and any test you had to change beyond the list above.
- `python tools/vo/lines.py && python tools/vo/check_ids.py && python tools/vo/lock.py --check`: clean, exit 0.
- `cd tools/vo && python -m unittest tests.test_lock tests.test_lines`: pass.
- `git status --short` shows only the files above (plus `tools/vo/manifest.json` and the renamed files). No commit.
- Report: per file one line of what changed; the lock counts (gone removed, broken re-locked, total ok); the direction entries pruned (count) and renoted (ids); anything skipped and why.
