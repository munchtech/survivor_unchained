# The toll: build spec ("It takes less than it did")

The writer (the twelfth lead), 11 October 2026, for a combat or story-code lead.
The owner chose option 1 of `docs/story/TWIST_WTF.md` knowing that dying in the
endless then costs a life. The story is there; this page is only what to build.

**The rule.** The first rise cost twenty-six lives (the drowned in Vonnra's
ledger, lines 1 to 26; line 27 is "From the ford. Got up."). Every getting-up
since costs one life in the valley, from line 28 on. The one who paid dies
before the next light, is reported gently the next morning, and comes out to
the survivor's light the night after, and never strikes. Nobody says any of
this until C41. The game never states it as a law.

## 1. What counts as a rise

| Getting up | Where in code | Paid? |
|---|---|---|
| Down in the prologue ("The ember will not let you go so easily.") | `Prologue.OnDeath` | **No.** The twenty-six paid for the whole first night. |
| Up again in a story fight ("You get up." / "...It takes less than it did.") | `StoryNight` rise, `Journey.RiseLine()` | Yes, each one |
| A story fight lost, carried home to Chid's bench | `Journey.CarriedHome` | Yes |
| Fallen by day, "a carter found you" | `Journey` fall handler (`player.deaths`) | Yes |
| Down in the endless or a map (after the game's end) | the run's death | By ending (§7) |

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
- **Every player pays once in the first night.** When the first night fight
  of Act 1 starts (a story fight, or the Verge's own night) with `toll.rises`
  at 0, script one fall at its first big beat: a blow nothing can dodge (the
  pack's rush, the Roost's bolt-volley, the ground giving way: whatever the
  fight has). She goes down and gets up: "You get up." It's the first rise
  line, so the player hears the prologue's words and nothing strange. If she
  has already died that day or night, skip the scripted fall: that rise was
  the baker's.
- **The next morning,** before the overnight report, the narrator, voiced:
  **"Up the street, nobody is baking."** Then the news (§4, the first line).
- **That night** Hester comes out to the light (§5).
- **Optional, B's grace note:** Hester is Ancell's mother, the "His mam." of
  Holloway's roll (`holloway.roll`). After she dies, his roll says "Ancell.
  Nobody, now." Cheap, and devastating on a replay.

## 4. The morning news

**The slot.** From day 2, every morning's overnight report ends with exactly
one death, wherever in the valley. If anyone paid since the last dawn, it's
the first of them, told gently: in a chair, in their sleep, no cause given. The
others are written in the ledger and not reported. If nobody paid, it's a death
with a cause, from the second list. One a morning, whatever happened, so the
count never matches the player's deaths and nobody can spot the pattern in
Act 1. The town remarks on it once, through Rook, as the season.

The text is the report's own register, unvoiced (like the reports in
`rules.json`). Each gentle entry also has Vonnra's short form for the ledger
and the mark the paid one carries at night.

### The gentle ones (paid)

| id | Ledger (Vonnra's hand) | The news | Mark at night |
|---|---|---|---|
| hester | The baker. | Hester Ancell, who baked for the square, sat down at her trough before light and went. The first anyone knew of it was that there was no bread. | One of them is white to the elbows. |
| oswin | Oswin, at his dinner. | Old Oswin's gone to the Morrow. Sat down in his chair after his dinner and went. | One of them has a napkin still tucked in at the neck. |
| sumner | The lamplighter. | Abel Sumner, the lamplighter, sat down on the bottom rung of his ladder before light and went. Half the square's lamps were still lit at noon. | One of them carries a lamplighter's pole, unlit. |
| garside | The carter, at the gate. | Will Garside, who carts for Harlan, was found sitting up on his cart at the east gate at first light, waiting for it to open. | One of them still has a carter's whip in its hand. |
| coombe | The Flagon's books. | Mistress Coombe, who kept the Flagon's books, went at her table with the pen in her hand. The last line was half a word. | One of them has ink to the knuckles. |
| rigby | The egg woman. | Ma Rigby, who sold eggs at the south gate, went in her chair with the basket in her lap. Not one of them broken. | One of them is carrying a basket, very carefully. |
| sowerby | The layer-out. | Nan Sowerby, who laid out the dead for the town, went in her own bed. For the first time in forty years they had to send to Low Kiln for someone to lay her out. | One of them has its hands crossed on its chest, and keeps them there. |
| hobb | Hobb, the drover's boy. | Hobb, the drover's boy, went in his sleep in the Penhales' hayloft. He was fourteen. Nothing wrong with him at all. | One of them is a boy, barefoot. |
| hebble | Annis Hebble, knitting. | Annis Hebble went in her chair by the window with her knitting in her lap. Her daughter says she'd dropped a stitch and never picked it up. | One of them has wool caught round its fingers. |
| dowd | The miller's widow. | Mercy Dowd, the miller's widow, went in her sleep. The cat had been crying at her door since before light. | One of them is in a nightgown, and has one slipper on. |
| maud | Maud, who swept the shrine. | Maud, who swept the shrine for Chid, went in her sleep. Chid has swept it himself every morning since, twice. | One of them has a broom. |
| ashby | The thatcher. | Tom Ashby, the thatcher, sat down on a roof ridge at first light to eat his bread, and went. They had to bring him down on a rope. | One of them has a bundle of reed on its back. |
| carrow | The Widow Carrow. | The Widow Carrow went in her sleep. Holloway paid for the box himself, and stood at the back. | One of them has a child's mitten pinned to its coat. |
| hollis | The cooper's lad. | Bran Hollis, the cooper's lad, went in his sleep the night before his wedding. The girl has been at the shrine since. | One of them has a ribbon tied round its wrist. |
| penhale | Gran Penhale. | Gran Penhale went in her bed. The dog was lying across her feet, and growled at the men who came for her. | One of them has a shawl over its head, the way the old women wear them. |
| kit | The ferryman. | Old Kit, who hasn't had a ferry to work since the irons went up, went in his chair facing the river. | One of them has a boat-hook over its shoulder. |
| prout | The Watch's drummer. | Davey Prout, the Watch's drummer when there was a Watch to drum for, went in his sleep with his sticks under the pillow. | One of them has drumsticks through its belt. |
| weller | The well-digger. | Joss Weller, the well-digger, went in his sleep with his boots on. | One of them is caked in clay to the knees. |
| agnes | The Coyles' cook. | Agnes, the Coyles' cook, went in her sleep. Harlan says she's the first person to leave that house without asking him. | One of them has a ladle. |
| haig | Mother Haig. | Mother Haig, ninety if a day, went in her chair. Everyone says it was her time, and says it a little too quickly. | One of them is bent nearly double. |
| tolley | Jem Tolley, at the Flagon. | Jem Tolley went in his chair at the Flagon with a full cup in front of him. Rav says it's the first full cup he ever left. | One of them has a tankard hooked on one finger. |
| pip | The shepherd. | Pip, the Penhales' shepherd, went on the hill with his dog beside him. The dog brought the sheep home by itself. | One of them has a crook. |
| dorrie | Dorrie Hale. Four. | Little Dorrie Hale went in her sleep. She was four. Wenna sat with the mother all morning and said nothing, which is the most anyone has ever seen Wenna do. | One of them is very small. |
| tull | The washerwoman. | Mother Tull, who did the Watch's washing, lay down for a minute after the copper was lit, and went. The copper boiled dry. | One of them has its sleeves rolled to the shoulder. |

Hester is always first. Keep Dorrie out of the first ten draws. Two take
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
4. Wolves had a peddler on the east road, a mile out. His tray came into town on the drover's cart; his boots didn't. (the Pack)
5. A gallery came down in the Dig. The Watch got two out. The third is still under it, and Pell has already asked whose he was. (the Dig)
6. The Kerchiefs left a man hanging from the Old Road sign with a board on him: TOLL. He was one of theirs. (the Kerchiefs)
7. The cough took the last of the Ruddock grandparents. Ashford's cough, Rook says, ten years late.
8. A cart went over at the Narrows and into the stream, with the carter under it.
9. Smoke in the night at the tannery. Old Dace got the hides out and went back in for his money box.
10. The plank at the mill-race gave under the Prentice boy. Wenna got the water out of him, but not soon enough.
11. Meg Daw fell down the Flagon's cellar steps with a full cask in her arms. She held on to the cask.
12. The cold took a tinker in the ditch past the east gate. He had a bottle and no coat. Holloway gave the bottle to the Watch, and wrote down the man's name.
13. A lampling bit through a digger's lamp-strap, and the lamp went down the shaft with him. (the Dig)
14. A fever in the lower street took the Marsh baby. Chid sang over it, and for once nobody laughed at him.
15. Somebody's horse kicked Ned Varley in the head at the forge door. Brannoc carried him to Wenna, and came back and finished the shoe.
16. The ice on the mill-pond let a boy through. His brother got out.

### Rook (voiced; new barks, to be locked later)

Said when the player first passes her that morning:
- (the baker's morning) "Hester's gone, pet. Sat down at her trough. You'll have porridge, and like it."
- (any gentle morning) "Somebody else went in their sleep. Eat. It doesn't help, but it's hot."
- (once, from about day 6) "People are going faster than they used to, pet. Chid says it's the time of year. He says that every time of year."
- (a cause morning) "Fever's in the lower street. Boil your water and don't kiss anybody."

## 5. The paid ones, at night

- **Which night:** the first night after they paid, in whatever night fight
  she plays (story fight, the Verge's night, a map). At most three a night;
  the rest wait for later nights. Set `came`.
- **What they do:** one of the risen, walking, never running, straight to her.
  No attack at all. At arm's length it stops in her light and lifts its face
  to her, the way the Warden lifts his lamp and the drowned woman at the
  water's edge lifted hers. It stays until something kills it. At dawn it
  falls where it stands. Her kill sets `burned`.
- **The look:** the common risen, unlit (no ember of their own: theirs went to
  her), with the mark's prop. For the first build, six silhouettes cover the
  pool: apron and floured arms; a tool over the shoulder (pole, boat-hook,
  crook, broom); a basket or ladle in the hands; a nightgown or shawl; a small
  one (a child); hands crossed on the chest. Map each pool entry to one and
  keep its narrator mark true to it.
- **The narrator,** voiced, once a night, when the first paid one comes into
  her light: the entry's mark, then **"It comes at you, and never strikes."**
  (Two parts: the mark, and the constant line. The baker's whole line reads
  "One of them is white to the elbows. It comes at you, and never strikes.")

## 6. The ledger page and C41

- **Act 1 (C09) shows only lines 1 to 27.** The page ends at "From the ford.
  Got up." Lines 28 on are on the next page, which is never shown before C41.
- **C41** (bottom of the stair). Vonnra reads to 27 as planned, and turns the
  page. Voiced, fixed: **"Twenty-eight. The baker. She sat down at her trough
  before light, the night you first got up. She came out to you the next
  night, still floured. You burned her."** (If `burned` is false: "...still
  floured. She stood in your light till it was day.")
- Then the page fills with the rest of the save's lines in her hand (text,
  unvoiced, scrolling): "29. The lamplighter. Sat down on his ladder, the
  night you were carried home from Wolf Hollow. He came to you. You burned
  him." The place and kind come from the entry.
- She reads the last one aloud. Voiced, per pool entry: "And the last of them.
  [ledger short form]" (one short take per entry).
- Then, voiced: **"Twenty-six for the first. One each, since. ...No charge,
  this once. I always tell people the price."**
- Minutes later the scripted fall, and the narrator's line, unchanged: "You
  get up. It takes less than it did."

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
  never a named character's or a name on Holloway's roll (Abbot, Ancell,
  Bede, Carrow, Dunning, Ede, Fenn, Gale), except where this page means it.

## 8. Voice

New lines, to record once built (none are in a packet yet):
- the narrator: "Up the street, nobody is baking."; the 24 marks; "It comes
  at you, and never strikes.";
- Rook: the four barks (§4);
- Vonnra: C41's lines (§6) and the 24 short forms.

**The rise lines have no voice id today.** `DayLines.Rise` and `RiseAgain`
(`Journey.Day.cs`) reach `G.Say` as constants, which `tools/vo/lines.py`
doesn't read, so "You get up. It takes less than it did.", the line the whole
twist hangs on, isn't in the manifest and can't be recorded. The same for
`Dusk`, `DuskHeard`, `Tonight`, `Nudge`, `NightOut` and `StraightOn`. Teach
`lines.py` to read `DayLines` (or say them through `VoiceLines.Said` with a
literal) before the narrator records Act 1.

## 9. Continuity found while writing this

- **Old Oswin dies twice.** `folk.json` (day 3 on): "Old Oswin's gone to the
  Morrow..."; `rules.json` `vault.shut`: "Old Oswin says he heard marching".
  Fix: the folk line goes (his death is the pool's `oswin`, gentle, so paid),
  and `vault.shut` hears the marching through "the Penhale boy".
- No gentle death may come from anywhere but the toll, or the re-read leaks:
  check `folk.json` and `rules.json` for "in her sleep" and "in his chair".
  (Rook's "She went in her sleep, pet" about the mother is the kind lie, and
  stays.)

## 10. Tests

- the prologue's deaths don't count; every other kind counts once;
- the first paid one is always Hester, and a save's ledger is the same after a
  reload;
- one death a morning, whatever the night held; gentle only after a paid rise;
- the scripted fall happens only when `toll.rises` is 0;
- a paid one never deals damage, and `burned` is set only by her kill;
- C09 never shows line 28;
- the result line by ending (A, B, C, nobody).
