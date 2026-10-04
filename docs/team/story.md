# Story and writing: status

Owner of the canon, the words and the story data; signs off every voice packet
before recording. Agent a73ca9d35d0c487a9, branch `worktree-agent-a73ca9d35d0c487a9`
(successor to a035208561a66c171; handoff in `docs/handoff/story.md`).

## State

- **Canon:** `docs/STORY_BIBLE.md` (the truth, the pacing, who tells it, "The
  nights"); `docs/VOICES.md`; `docs/WRITING_PASS.md` §17 to §20 are the latest.
- **Act 1's data** is written and tested (`CinematicTests`, `RouteTests`,
  `StoryLint`, `VergeTests`). The seed, body-hours and signature checks are
  clean after the 4 October merges.
- **Done this session** (WRITING_PASS §20):
  - every story night ends on the narrator's own line, won and lost, in place
    of "The story goes on." (`ArenaSpec.EndWon`, `EndLost`);
  - the result screen's banner, "longest" line and table line reworded; the
    story night's hint no longer talks about "the story";
  - the Wayfinder's maps are named in the valley's words for their people
    ("The Lampless Howes", "The Hungry Gap", "The Praying Sump");
  - phase 3's crafter lines are in `crafting.json` ahead of the hooks: Vonnra's
    binding and marks, Snib's jars (inert until crafting adds the verbs);
  - the arena's own words: "Wolfbane gear, or gear of the Wolf"; "Ruled by the
    Pack-Mother"; "is down: the night is held"; "end it" (not "beat it");
    "Brought down by a Kerchief Footpad" (`Enemies.Called`).
  - Seen at 1920x1080: the table, a won table night, and a won and a lost story
    night's result. Not seen: a real fall's result (below).
  - the morning after each story night has its report (`rules.json`);
  - "alpha" is gone from the bounty notice, Holloway's locked choice and a deed,
    and `StoryLint` holds it out.
- **Voice is paused by the owner:** no placeholders; the final voices come from
  ElevenLabs later, one character at a time. Packets stay text-only (below).

## Key decisions (why)

- **Vonnra is not the narrator.** She is the one unnamed call up the road at
  the waking, subtitled "A voice up the road". The fortune opens on the same words.
- **Her free things are priced and then waived,** so they stay owed. Her
  crafting lines carry no `{name}` and no "traveller", so they hold either side
  of the fortune.
- **A night's last line never claims the dawn:** she comes back into the same
  night, and the town talks about it that night.
- **Every lost story night is a fall,** so its line is her coming to, and each
  one is a quiet seed of what she is.
- **No genre words in the valley's mouth,** maps included: no weeping or
  whispering places, no alpha or warlord.
- **Pacing (the owner's):** story about 40% early; story nights 20 minutes, the
  Wayfinder's maps 30; the endgame is the atlas (build maps) and the ember scars
  (survivors fun); after ending B they are the Wayfinder's book of the nights
  that were.

## Packet notes, text-only (for when voice resumes)

- **Final:** narrator, Rook, Holloway, Brannoc, Sella, Vonnra, Harlan.
- **Sella's final packet has changed lines,** which need new takes:
  `say_calling.2` ("Something on you's smouldering, love.") and
  `bark.sella.night.1` ("I've a bath going cold upstairs. Shame to waste it.").
- **Chid:** wants company, the shrine lit, and this one to stay up. Hides that
  he is Unchained and near two hundred; that he carries the survivor in (the
  carter is his lie); that he is "C."; that he was at the ford the night they
  rose. Takes 13 and 14: "..…" becomes "…". Bark day.1, "I should know.": older
  than he looks, and he doesn't notice saying it. Re-take `cb_nemesis_slain.0`.
- **Maeca:** wants the Pack cured and let be. Hides that the Pack saved her at
  Ashford, that the Kerchiefs are her old neighbours, that she is looking for
  whoever signed for the boots. Bark said.6's note is stale. Bark said.3:
  "'Listen.' very quiet; not a whisper." Re-take `driving.0` ("dog-wolf").
- **Ysolde:** wants the maps walked and the margins full. Hides that she sells
  the margins to Sallow for her brother Edric's keep. t_wayfinder's "My brother
  didn't." is the one lie in her part, practised smooth; the hurt goes in the
  corners. Re-take `places.0` ("Last till the dead of night").
- **New lines for every packet:** the night talk (`npcs.json` `said`, appended).
- **Changed, if the board is ever voiced:** `dlg.board.read.0` now ends "fifty
  for the old grey dog-wolf" (`tools/vo/manifest.json` still has the old text).

## Next

1. The result screen's new slots, when the experience successor sends UI's
   beats (the words for today's slots are in).
2. C14: Brannoc's dusk choice (`brannoc.road`), the `nell.burial` variant, the
   night's last lines and a RouteTests play, once combat builds the fight.
3. C01 to C04: the cinematics lead's line asks, when they come.
4. Crafting phase 3: wire-up questions only; the lines are written.
5. Act 2's text, when the owner asks.

## Blockers

None. The owner's open question: who sings the hymn at Nell's grave (C08).

## For other areas

- **Combat:** `Arenas.Again` now keeps `Spare` (a retaken Hollow fight was
  killing Greymuzzle while its `OnWin` said spared). Map names come from
  `MapOffers.Names`; text still goes through story.
- **Crafting:** `crafting.json` has `vonnra` (bind, mark, `terms.accused` for
  the tenth off) and `snib` (jar, steep), with `verbs: []`. Add the verbs and
  the lines play. Vonnra's role does not move: she binds at the Toll Tower.
- **Experience and UI:** the result screen's words for today's slots are done
  (WRITING_PASS §20). Send the new slots and I will fill them.
  - A story night's last line is the screen's closing beat: give it more than
    a body-size italic line at the foot.
  - Check: `--zone arena --time night --auto --die 14` left her fallen, with no
    result screen after 20 s of game time. It may be the harness.
- **Cinematics** (a3058a45eee41d695): agreed to strip lower-case directions
  from cinematic subtitles. C13's "(Not yet.)" and "(Go back.)" stay.
- **Arena art:** the table's map names now match each people's ground.
