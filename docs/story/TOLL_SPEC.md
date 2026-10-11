# The toll: build spec ("It takes less than it did")

The writer (the twelfth lead), 11 October 2026, for a combat or story-code lead.
Judged 11 October (a max judge, against TWIST_WTF option 1): pass with fixes, applied.
The owner chose option 1 of `docs/story/TWIST_WTF.md` knowing that dying in the
endless then costs a life. The story is there; this page is only what to build.

**The rule.** The first rise cost twenty-six lives (the drowned in Vonnra's
ledger, lines 1 to 26; line 27 is "From the ford. Got up."). Every getting-up
since costs one life in the valley, from line 28 on. The one who paid dies
before the next light, is reported gently the next morning, and comes out to
the survivor's light the night after, and never strikes. Nobody says any of
this until C41. The game never states it as a law. How this fits canon A (Chid
made you) is in `TREATMENT.md` §0, "How the three meet".

## 1. What counts as a rise

| Getting up | Where in code | Paid? |
|---|---|---|
| Down in the prologue ("The ember will not let you go so easily.") | `Prologue.OnDeath` | **No.** The twenty-six paid for the whole first night. |
| Up again in a story fight ("You get up." / "...It takes less than it did.") | `StoryNight` rise, `Journey.RiseLine()` | Yes, each one |
| Up again in any fight by the in-fight rises, `Battle.cs` ~1338-1357: `p.Revives` ("Something answers for you: not yet. You get up.") and `p.Ashes` (the Cold, Then Not blessing: "You go cold. Then the ember catches.") | `Battle` | Yes, kind `fight`. In Acts 2 and 3 these are the only rises (`StoryNight.RisesFor` is 0 after `chapter.done`). |
| A table night lost | `ArenaRun.OnDeath` (`WakesInTown` false, `Arena.cs` ~100), back into the same night via `Game.LeaveArena` | Yes, kind `fight` |
| A story fight lost, carried home to Chid's bench | `Journey.CarriedHome` | Yes |
| Fallen by day, "a carter found you" | `Journey.Fell` (`Journey.cs` ~349, called from `Game.OnDeath`) | Yes |
| Down in the endless or a map (after the game's end) | the run's death | By ending (§7) |
| Down in a map run before an ending, if maps open that early | `MapRun.OnDeath` | Yes, kind `run` |

`player.deaths` is added in both `Fell` and `CarriedHome`.

A Flare cast at the edge that saves her (CLASSES.md §3.3, "A flare at the edge
burns brighter": below a quarter of health it mends 20%) is a rise avoided, so
a life kept. **That's intended,** and it's the best thing the mechanic could
mean: burning your own light at the edge spares someone else's. Never count
it, show it or say it, before C41 or after. A player who works it out has
earned it.

## 2. The counter and the ledger, in the save

- **`toll.rises`** (number): every paid rise, above. Don't reuse
  `player.deaths` (by day and carried home only) or `story.rises` (the rise
  line's own count, which stays as it is).
- **`toll.ledger`** (a list in the save), one entry per paid rise:
  `{ n, who, day, kind, place, came, burned }`. `n` is 28 for the first. `who`
  is a pool id (§4). `kind` is `fight`, `carried`, `fell` or `run`. `place` is
  the fight's or zone's name. `came` is set when they walk out to her light;
  `burned` when she kills them.
- **Who pays, in order:** the first is always **the baker** (`hester`). After
  her, the gentle pool in an order shuffled once from the save's seed, so a
  save's ledger never changes on reload. When the pool runs out (the endless),
  build names from the generator (§7).

## 3. The baker and the scripted fall

- C04's dawn line, already locked: "Somewhere up the street, someone is
  baking." That is Hester, alive.
- **Every player pays once in the first night.** The scripted fall runs only
  in the first `StoryNight` of Act 1 (the Verge's own night is an `ArenaRun`
  with no rise). It has its own path: no `p.Rose++`, no `B.Restore`. She gets
  up where she fell, at full health, with 2.5 s of invulnerability, and
  `RiseLine()` still runs ("You get up."). That is the first rise line, so the
  player hears the prologue's words and nothing strange.
- **Staged per fight,** not "a blow nothing can dodge": hollow, the Pack comes
  over her out of the dark, her lamp gutters, black for 1.5 s; roost, the
  bolt-volley off the ravine wall; dig, the gallery floor goes from under her;
  vault, the door's violet flare.
- **When:** as stage 1's goal is met; never in the boss phase or a cinematic.
  Run it only if `toll.rises` is 0 when the beat comes (a real fall earlier in
  the same fight was the baker's).
- **Seeds already in the game:** "Something answers for you: not yet." is in
  the game now and on a replay says exactly what happened.
- **The next morning,** before the overnight report, the narrator, voiced:
  **"Up the street, nobody is baking."** Then the news (§4, the first line).
- **That night** Hester comes out to the light (§5).
- **Optional, B's grace note:** Hester is Ancell's mother, the "His mam." of
  Holloway's roll (`holloway.roll`). After she dies, his roll says "Ancell.
  Nobody, now." Cheap, and devastating on a replay.

## 4. The morning news

**The slot.** From day 2, every morning's overnight report carries exactly
one death, wherever in the valley. The order: Chid's waking (if carried home),
then the baker line (her morning only), then the death FIRST, then
`report.Lines`, then the gossip (e.g. `Journey.Fell`'s "By breakfast, Holloway
had heard..."), then the flask. `Journey.cs` ~845 "A quiet night. Rook's bread
is hot, and nobody died." becomes "A quiet night. Rook's bread is hot." (the
builder changes it). A reload before the save undoes the rise and its payer.
Old saves start at `toll.rises` 0.

**Which death.** If anyone paid since the last dawn, the morning tells the
first of them, gently, with no cause given; the others go into the ledger
unreported. If nobody paid, it tells a death with a cause, from the second
list. One a morning, whatever happened, so the count never matches the
player's deaths and nobody can spot the pattern in Act 1. The town says it
aloud twice, and nobody believes it: one voice in the crowd at the gate
(`scene_in_my_count`, day 3 on: "And every morning since you came, there's
somebody up the street didn't wake."), and Rook once, as the season (below).

**Vary the gentle ones.** No cause, and no formula either: at most two of
them go "in a chair", two "in their sleep", and only the baker "sat down
... and went" (her words come back at C41). A new entry finds its own small
image, as these do.

The text is the report's own register, unvoiced (like the reports in
`rules.json`). Each gentle entry also has Vonnra's short form for the ledger
and the mark the paid one carries at night.

### The gentle ones (paid)

| id | Ledger (Vonnra's hand) | The news | Mark at night |
|---|---|---|---|
| hester | The baker. | Hester Ancell, who baked for the square, sat down at her trough before light and went. The first anyone knew of it was that there was no bread. | One of them is white to the elbows. |
| oswin | Oswin, at his dinner. | Old Oswin's gone to the Morrow, as he said every winter he would. They found him at his table, napkin still tucked in, plate wiped clean. | One of them has a napkin still tucked in at the neck. |
| sumner | The lamplighter. | Abel Sumner, the lamplighter, stopped for breath on the bottom rung of his ladder before light, and didn't start again. Half the square's lamps were still lit at noon. | One of them carries a lamplighter's pole, unlit. |
| garside | The carter, at the gate. | Will Garside, who carts for Harlan, was found sitting up on his cart at the east gate at first light, waiting for it to open. | One of them still has a carter's whip in its hand. |
| coombe | The Flagon's books. | Mistress Coombe, who kept the Flagon's books, went at her table with the pen in her hand. The last line was half a word. | One of them has a pen in its fist. |
| rigby | The egg woman. | Ma Rigby, who sold eggs at the south gate, went in her chair with the basket in her lap. Not one of them broken. | One of them is carrying a basket, very carefully. |
| sowerby | The layer-out. | Nan Sowerby, who laid out the dead for the town, went in her own bed. For the first time in forty years they had to send to Low Kiln for someone to lay her out. | One of them has its hands crossed on its chest, and keeps them there. |
| hobb | Hobb, the drover's boy. | Hobb, the drover's boy, went in his sleep in the loft over the Coyles' stable. He was fourteen. Nothing wrong with him at all. | One of them is a boy, barefoot. |
| hebble | Annis Hebble, knitting. | Annis Hebble's daughter found her by the window with the needles still in her hands. She'd dropped a stitch, and never picked it up. | One of them trails a skein of wool behind it. |
| dowd | The miller's widow. | Mercy Dowd, the miller's widow, didn't come to her door this morning. The cat had been crying at it since before light. | One of them is in a nightgown, and has one slipper on. |
| maud | Maud, who swept the shrine. | Maud, who swept the shrine for Chid, was found on the shrine step with her broom across her knees. Chid swept the step himself this morning. Twice. | One of them has a broom. |
| ashby | The thatcher. | Tom Ashby, the thatcher, took his bread up onto a roof ridge at first light, and never came down. They had to fetch him down on a rope. | One of them has a bundle of reed on its back. |
| carrow | The Widow Carrow. | The Widow Carrow's boy couldn't wake her this morning. Holloway paid for the box himself, and stood at the back. (Gate: Holloway alive. After him: "The Widow Carrow's boy couldn't wake her this morning. With the captain gone, Maeca paid for the box.") | One of them is holding a child's mitten. |
| hollis | The cooper's lad. | Bran Hollis, the cooper's lad, didn't wake on his wedding morning. The girl has been at the shrine since. | One of them is in its wedding shirt. |
| penhale | Gran Penhale. | Gran Penhale died in the night with the dog lying across her feet. It growled at the men who came for her. | One of them has a shawl over its head, the way the old women wear them. |
| kit | The ferryman. | Old Kit, who worked the ferry at the Low Ford till the irons were lit, went in his chair facing the river. | One of them has a boat-hook over its shoulder. |
| prout | The Watch's drummer. | Davey Prout, who drummed for the Watch when it had men enough to march, died in his bed with his sticks under the pillow. | One of them has drumsticks through its belt. |
| weller | The well-digger. | Joss Weller, the well-digger, was gone before he'd washed the clay off. His wife says he was only resting his eyes. | One of them is caked in clay to the knees. |
| agnes | The Coyles' cook. | Agnes, the Coyles' cook, laid the fire this morning and never lit it. Harlan says she's the first person to leave that house without asking him. | One of them has a ladle. |
| haig | Mother Haig. | Mother Haig, ninety if a day, has gone. Everyone says it was her time, and says it a little too quickly. | One of them is bent nearly double. |
| tolley | Jem Tolley, at the Flagon. | Jem Tolley put his head down on the Flagon's corner table with a full cup in front of him, and that was all. Rav says it's the first full cup he ever left. | One of them has a tankard hooked on one finger. |
| pip | The shepherd. | Pip, the Penhales' shepherd, went on the hill with his dog beside him. The dog brought the sheep home by itself. | One of them has a crook. |
| dorrie | Dorrie Hale. Four. | Little Dorrie Hale went in her sleep. She was four. Wenna sat with the mother all morning, and for once said nothing at all. | One of them is very small. |
| tull | The washerwoman. | Mother Tull, who did the Watch's washing, lay down for a minute after the copper was lit, and went. The copper boiled dry. | One of them has its sleeves rolled to the shoulder. |

Gate the entries that need someone alive: carrow (Holloway alive, see her text), agnes (Harlan alive). Hester is always first. Keep Dorrie out of the first ten draws. Two take
names from Holloway's roll on purpose (B): Hester is Ancell's mother ("Ancell.
His mam."), and the Widow Carrow is the wife Carrow left ("A wife, and one
coming."); he pays the widows, so he pays for her box.

### The ones with a cause (nobody paid)

Each may carry a `when` (the wolves only while the Pack is a danger, the
Kerchiefs while they raid, the Dig while it's open). When the list runs out,
use the generator (§7) with "the fever", "the cold", "a fall" or "the Dig".

1. A fever took the Lark twins' father in the night. Wenna says it's the river's fever, and to boil the water.
2. The frost got old Saul Pike, who would sleep in the lean-to whatever anyone said. Rook has put his blanket out to air, as if he might want it.
3. A drover went back out for a lost ewe after dark. They found him at the edge of the lamps, facing in.
4. Wolves had a peddler on the east road, a mile out. His tray came into town on the drover's cart. Not much else of him did. (the Pack)
5. A gallery came down in the Dig. The Watch got two out. The third is still under it, and Pell has already asked whose he was. (the Dig)
6. The Kerchiefs left a man hanging from the Old Road sign with a board on him: TOLL. He was one of theirs. (the Kerchiefs)
7. The cough took the last of the Ruddock grandparents. Ashford's cough, Rook says, ten years late.
8. A cart went over at the Narrows and into the stream, with the carter under it.
9. Smoke in the night at the tannery. Old Dace got the hides out and went back in for his money box.
10. The plank at the mill-race gave under the Prentice boy. Wenna got the water out of him, but not soon enough.
11. Meg Daw fell down the Flagon's cellar steps with a full cask in her arms. She held on to the cask.
12. The cold took a tinker in the ditch past the east gate. He had a bottle and no coat. Holloway gave the bottle to the Watch, and wrote down the man's name. (Holloway alive.)
13. A lampling bit through a digger's lamp-strap, and the lamp went down the shaft with him. (the Dig)
14. A fever in the lower street took the Marsh baby. Chid sang over it, and for once nobody laughed at him.
15. Somebody's horse kicked Ned Cobb in the head at the forge door. Brannoc carried him to Wenna, and came back and finished the shoe. (Brannoc at the forge.)
16. The ice on the mill-pond let a boy through. His brother got out.

### Rook (voiced; new barks, to be locked later)

Said when the player first passes her that morning:
- (the baker's morning) "Hester's gone, pet. Sat down at her trough. You'll have porridge, and like it."
- (any death morning, at most every third day) "Another one in the night,
  pet. Eat. It doesn't help, but it's hot."
- (once, from about day 6) "Bad winter for the old ones, pet. Chid's been
  sitting up with them, so nobody goes on their own."
- (a cause morning, causes 1 and 14 only) "Fever's in the lower street. Boil
  your water and don't kiss anybody."

## 5. The paid ones, at night

- **Which night:** the first night after they paid, in whatever night fight
  she plays (story fight, the Verge's night, a map). At most three a night;
  the rest wait for later nights. Set `came`.
- **What they do:** one of the risen, walking, never running, straight to her.
  No attack at all. At arm's length it stops in her light and lifts its face
  to her, the way the Warden lifts his lamp and the drowned woman at the
  water's edge lifted hers. It stays until something kills it (rules below). At
  the fight's end it falls where it stands. Her kill sets `burned`.
- **The look:** the common `risen` is a skeleton (`Enemies.cs` ~155,
  `skeleton_minion`) and can't lift a face or be floured. They need a
  fresh-dead villager body, greyed, eyes unlit (no ember of their own: theirs
  went to her), with one hand or shoulder prop per pool entry. For the first
  build, six silhouettes cover the pool: apron and floured arms; a tool over the shoulder (pole, boat-hook,
  crook, broom); a basket or ladle in the hands; a nightgown or shawl; a small
  one (a child); hands crossed on the chest. Map each pool entry to one and
  keep its narrator mark true to it.
- **Rules:** untouchable while it walks (her fire passes through). At arm's
  length it stops, lifts its face, and stays untouchable for 3 s, then burns
  like anything else. No collision, no ember, no loot; never counts toward a
  stage goal or kills. It survives `StoryNight.Clear()` on a stage change and
  on a rise (re-place it walking from the edge). It comes in a lull, from the
  edge away from the boss, and falls at the fight's end. `came` is set when it
  spawns; `burned` by any kill of hers (her fire, summons, companions) and
  stays false only if it stood till the fight ended.
- **The narrator,** voiced, once a night, when the first paid one comes into
  her light: the entry's mark, then **"It comes at you, and never strikes."**
  (Two parts: the mark, and the constant line. The baker's whole line reads
  "One of them is white to the elbows. It comes at you, and never strikes.")

## 6. The ledger page and C41

- **Act 1 (C09) shows only lines 1 to 27.** The page ends at "From the ford.
  Got up." Lines 28 on are on the next page, which is never shown before C41.
- **C41** (bottom of the stair). `docs/cinematics/act3_outline.md` has two
  versions; cover both. Accused: Vonnra reads at the first landing. Not
  accused: the survivor turns the page herself and Vonnra voices 28 as an
  admission. Keep the outline's "stops, because there is nothing after it yet"
  as a false ending: 3 s of silence, then the page turns. Voiced, one take per
  clause: **"Twenty-eight. The baker. She sat down at her trough before
  light, [clause]. She came out to your light, still floured. You burned
  her."** Clauses by the fight she got up in: hollow "the night you got up off
  the wolves' ground"; roost "the night you got up under the Roost"; dig "the
  night you got up in the Dig"; vault "the night you got up at the sealed
  door"; a table night "the night you got up in the Verge"; carried "the night
  Chid carried you home"; fell "after the day the carter found you". If not
  burned: "...still floured. She stood in your light till it was day." New,
  for a payer who hasn't come out yet: "She hasn't come out to you yet."
- **C09's text is in** (11 October, `vonnra.f_chart` [0] and [1]): "(The
  ledger lies open, her hand flat on the right-hand page, and from where you
  sit you can read the left. Twenty-six lines, every one struck through. The
  twenty-fifth: Nell, the smith's girl. With Wat. The twenty-sixth: A woman.
  No name. And under them a twenty-seventh, not struck: From the ford. Got
  up.)" Line twenty-six names nobody now; it never says Rook.
- Then the page fills with the rest of the save's lines in her hand (text,
  unvoiced, scrolling), in about 10 s whatever the count. Entries with
  `burned` true are ruled through like lines 1-26. Each pool entry needs
  `manner` (e.g. "Sat down on his ladder") and a pronoun. Template: "{n}.
  {short} {manner}, {clause}. {He} came to you. You burned {him}." using the
  clauses above (fight titles don't fit the sentence). The place and kind come
  from the entry.
- She reads the last one aloud. Voiced, per pool entry: "And the last of them.
  [ledger short form]" (one short take per entry). If the last name is a
  generated one (more than 25 paid), voice "And the last of them." alone.
- Then, voiced: **"Twenty-six for the first. One each, since. ...No charge,
  this once. Not to you."** (The writer's close, 11 October: it turns the
  game's first words, the far voice's "Come up, traveler. ...No charge, this
  once.", without explaining them. It replaces "I always tell people the
  price.")
- Minutes later a fall, and the narrator's line, unchanged: "You get up. It
  takes less than it did." Act 3 gives no rises, so this fall bypasses
  `RisesFor`; name its fight in the build. It is PAID: its ledger line is
  written, and that payer comes out in the next fight, the first one the
  player meets knowing what it is.

## 7. The endless, and the result line

- **After ending A** the toll stands. Every death in a run is paid, and they
  come out in the next run. The result screen gets one line: **"Paid tonight:
  Hobb, the drover's boy."** For more than one: "Paid tonight: Hobb, the
  drover's boy; the Widow Carrow; and four more." Nobody: no line.
- **After ending B** the risen die properly and nobody pays: a death ends the
  run, and there's no line.
- **After ending C** she takes the toll herself: the line is "Paid tonight:
  you.", and each death leaves her a scar (design it with the endings lead).
- **The generator** (once the pool is spent): a first name (about 40 plain
  valley names: Bet, Cuddy, Dace, Ebb, Gil, Hal, Ide, Lettice, Moll, Ned...)
  plus a descriptor (about 20: "the drover's boy", "the cooper's widow", "who
  kept bees at Low Kiln"...), never one already in the save's ledger, and
  never a name used in either list above (Dace and Ned collide), never a
  named character's or a name on Holloway's roll (Abbot, Ancell,
  Bede, Carrow, Dunning, Ede, Fenn, Gale), except where this page means it.

## 8. Voice

New lines, to record once built (none are in a packet yet):
- the narrator: "Up the street, nobody is baking."; the 24 marks; "It comes
  at you, and never strikes.";
- Rook: the four barks (§4), including the new ones;
- Vonnra: C41's lines (§6), the 24 short forms, the C41 clauses and "She
  hasn't come out to you yet."

The clock's `DayLines` and the story fights' pulls and sights now have ids
(`tools/vo/lines.py` `from_daylines`, `from_story_fights`). "You get up."
(`say.10bf2fd84dd3`) and "You get up. It takes less than it did."
(`say.c4c1c1ee88e3`) are LOCKED FOR RECORDING for the narrator.

## 9. Continuity found while writing this

- **Old Oswin dies twice.** `folk.json` (day 3 on): "Old Oswin's gone to the
  Morrow..."; `rules.json` `vault.shut`: "Old Oswin says he heard marching".
  Do NOT delete the folk line (folk ids are indices; it carries the idiom).
  Rewrite it in place: "Old Oswin says he'll be gone to the Morrow by spring.
  He's said it every winter for twenty years.", gated on Oswin not yet paid
  (re-take its .f and .m). The pool's `oswin` news then pays the idiom off.
  Keep `vault.shut`'s swap to "the Penhale boy" (he exists).
- **The crowd at the gate** (`scene_in_my_count`, `say`, voice `folk_m1`)
  says the town's fear: "every morning since you came, there's somebody up
  the street didn't wake." It is true once §4 is built (one death a morning
  from day 2; the scene is day 3 on). Until then it reads as superstition.
  Keep the scene after day 2 if its rule ever moves.
- No gentle death may come from anywhere but the toll, or the re-read leaks:
  check `folk.json` and `rules.json` for "in her sleep" and "in his chair".
  There are no others outside the toll. (Rook's "She went in her sleep, pet"
  about the mother is the kind lie, and stays.)

## 10. Tests

- the prologue's deaths don't count; every way of getting up in the §1 table
  counts once (the in-fight revives, a lost table night, a map run);
- the first paid one is always Hester, and a save's ledger is the same after a
  reload;
- one death a morning, whatever the night held; gentle only after a paid rise;
- the scripted fall happens only when `toll.rises` is 0, spends no rise and
  restores nothing;
- a paid one never deals damage, survives a stage change and is never hit
  while it walks; `burned` is set only by her kill;
- C41's fall is paid;
- C09 never shows line 28;
- the result line by ending (A, B, C, nobody).
