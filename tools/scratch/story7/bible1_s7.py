"""The bible to the approved rewrite: Act 1's canon (TREATMENT.md §0)."""
import os
P = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a38d66ae66583ace1\docs\STORY_BIBLE.md"
s = open(P, encoding="utf-8").read()

def rep(old, new):
    global s
    assert old in s, old[:70]
    s = s.replace(old, new)

rep("""**The survivor's mother.** Whatever their background, the survivor was coming
home. Their mother lived in the valley (on a farm at the Verge's edge, for a
hunter, and Rook knew her; elsewhere in Thornhollow for the rest: the
background says where the survivor went, not where they came from). She is
buried in the Quiet Garden behind the shrine, a week before Nell, under a
plain wooden marker that nobody points out (C08); Rook, if she knew her, says
nothing. The letter that brought the survivor home is in her coat in C01, the
ink run to blue water. A letter
found the survivor on the road that she was failing, and they came as fast as
they could, and camped at the Low Ford at dusk a day short. She had died the
week before. The survivor does not know. She is in the Morrow. Hers is the face
that is not quite where they left it at dawn; hers is the name Chid asks for
and the name the survivor says over and over in Sella's bed; and at the bottom
of the stair she is saying the survivor's name, the way she did when they were
small and late in from the yard. (The player may name her at creation; if not,
the game never names her, and "Mam?" is enough.) They do not know they are dead. The town half suspects ("You were
cold when they brought you in... Then you weren't"); the old orders would know
at a glance; one person arranged it.""",
"""**The survivor's mother** (the approved rewrite, `docs/story/TREATMENT.md`
§0 and §3.3, §3.4). Whatever their background, the survivor was coming home.
Their mother lived in the valley. When she knew she was failing she came down
to the Waystation to be near the ford road, and took Rook's back room; she
paid in a ring (it hangs on the nail behind Rook's bar, among the keys). Her
hands were bad, so Rook wrote her last letter for her: *Come home by the Low
Ford. I'll be at the water with a lamp, so you'll see me.* That is the letter
in the survivor's coat in C01, its ink run to blue water. Rook, paid by Vonnra
to report the road, reported that a traveller was expected on it; Vonnra paid
her double, and kept the irons lit all that week for the traveller she had
been told to expect. Every evening the mother went down to the north bank with
a lamp. On the seventh she went to the water's edge, and the Warden took her:
the twenty-sixth line in the ledger, written in Vonnra's register as "Rook's
lodger." She rose with the drowned, and stood on the far bank facing up the
road her child would come by, holding a lamp that had gone out. On the first
night the survivor cut her down to reach the water (the prologue's path, every
player); the narrator says nothing at the water's edge. Chid buried her in the
Quiet Garden behind the shrine, under a plain marker with no name.
- **Her word.** At dusk, when the survivor was small, she put the lamp in the
  window and called from the door: "Lamp's lit, Spark. Stay where it reaches."
  (The Order's evening call, made small and kept in one family; the name is
  hers.) The first dawn quotes it; the dawns take it away, a piece at a time
  (day 3, "Her voice is going the way her face went. You still have the
  word."; Act 2, "Somebody used to call you something at dusk. One short
  word. It was yours."; then nothing). On day 3, at Chid's asking, the
  survivor writes it in her journal, so the player can see it in her own hand
  after it means nothing to her.
- **The kind lie.** On day 1, asked, Rook says: "She went in her sleep, pet. A
  week since." The back room "has been free a week". The earth on the grave is
  dark and has not settled (the one fair contradiction). Act 2's last scene
  turns it (C32, Rook's kitchen).
- **She is the narrator** (twist A, Act 3). When the survivor drowned, her
  light came back up muddled with one other: her mother's, a week down, who
  knew her and would not let go. The voice that has told the player
  everything, "You get up.", is hers. She says what happens and what can be
  seen, never what it means, because an Unchained who remembers too much
  stops: the survivor would have sat down in the road to wait for her. Every
  night's ember crowds her out (rule 5), so she says less from Act 2's turn
  on. At the bottom of the stair her voice leaves the player and goes down.
  (The player may name her at creation; if not, the game never names her, and
  "Mam?" is enough.)
They do not know they are dead. The town half suspects ("You were cold when
they brought you in... Then you weren't"); the old orders would know at a
glance; one person arranged it.""")

rep("""**What the survivor did first.** Killing the Ford-Warden loosed its heart, one
of the seven, and Grimtunnel carried it down the hole. The prologue's victory
was the chain's first break. The tremors start there. Vonnra had meant the
heart to stay in the ford: "I am not angry. I am arranging.\"""",
"""**What the survivor did first.** Beaten, the Warden would have held his lamp out
of the water until the river ran dry, and risen again at dusk. He asked "Is it
morning?", and the survivor nodded, or said nothing (the game's first choice);
either way he let go. The lamp went into the water, the heart came up, and
Grimtunnel carried it down the hole. The prologue's victory, and her mercy,
were the chain's first break. The tremors start there. Vonnra had meant the
heart to stay in the ford: "I am not angry. I am arranging." At the fortune
she says both halves: "You stopped the drowning, traveller. You also did
this." (Act 1's twist.)""")

rep("""| Captain Holloway | A tired honest captain | Ashford's quartermaster who signed for boots that never came; holds a letter from the north asking for "the one from the ford" | Act 2 |
| Maeca Barefoot | A hunter with a theory | Last of the Ashford garrison; the Pack saved her; half the Kerchiefs are her old neighbours | Act 1 (the Pack, if her lover), Act 2 |""",
"""| Captain Holloway | A drunk who counts; the town's protector | Ashford's quartermaster, who held the shaft-head the night the ground went, and with the lamp in his eyes took the living on the ladder for the dead, and dropped the lid on ninety-one counted. His lid made the dead he feared. Holds a letter from Sallow asking for "the one from the ford", and his answer, "No.", never sent | Act 1 (what he did, to the player, at the gate), Act 2 (that it was a mistake, and who was under it) |
| Maeca | His kindest friend: she walks him home | Was on the ladder, the next hand up: number ninety-two. Three days below the lid; finished the wounded, and the boy; the Pack found her at a cave mouth. Has waited ten years | Act 2 (the rope) |""")
rep("""| The survivor's mother | Someone the survivor cannot quite picture | Dead the week before the ford; in the Morrow | Act 3 (the bottom of the stair) |""",
"""| The survivor's mother | Died in her sleep, a week before (Rook's kind lie) | Drowned at the Low Ford waiting with a lamp; rose; the survivor cut her down on the first night | Act 2's end (Rook's kitchen) |
| The narrator | The game's voice: nobody | The survivor's mother, in her child's light | Act 3 (the bottom of the stair) |""")

rep("""- **Captain Holloway.** *Face:* a tired, honest captain. *Secret:* he was the
  Ashford garrison's quartermaster. When the Fall came the Watch command turned
  the relief wagons back, and Holloway signed for the boots and supplies as
  delivered, to cover his commander. The garrison held the cave mouths
  barefoot and died. Maeca is the last of it. He also holds a letter from
  Sallow asking for "the one from the ford" (seen face down on his table in
  Act 1). *Arc:* Act 2 makes him choose between the letter's money (his men
  unpaid a year) and the survivor, and makes the boots come out. *Ends:* dies
  holding the north gate against the Vigil; hands the survivor over and is
  killed by Maeca; confesses, is forgiven by nobody, and keeps the gate anyway;
  hanged by Redcowl's people.
- **Maeca Barefoot.** *Face:* a hunter with a theory. *Secret:* the Pack saved
  her life after Ashford, which is why she has never hunted a wolf. Half the
  Kerchiefs are her old neighbours ("Fed some of them, once. Buried more.").
  *Arc:* the boots. *Ends:* leaves with the Pack into the deep wood; takes the
  Watch after Holloway; dies at the breakthrough's edge if the Pack is gone and
  she has nothing left to hold; the survivor's lover, at the end, if both live.""",
"""- **Captain Holloway** (the approved rewrite, `TREATMENT.md` §0 and §4). *Face:*
  a drunk who counts the Waystation in at the gate every night and will not bar
  it till the count is right ("Eleven of us, and the cat. I count the cat.").
  *Secret:* ten years ago he was the Ashford garrison's quartermaster. The night
  the lower town went into the ground, half the garrison held the cave mouths on
  the hill and half went down the main shaft on the ladders. He held the
  shaft-head: the windlass, the lamp, the iron lid. He counted them up with the
  lamp in his eyes. At ninety-one he looked down and saw the dead climbing under
  the last of the living, four hundred asleep behind him, and dropped the lid
  and barred it and sat on it. They knocked for three days. What he saw were
  the living from the lower workings, grey with slurry, too far gone to call
  out; three days in the dark near ember made them the dead he feared. He wrote
  the shaft party down with the hill party, "at the cave mouths", so the widows
  were paid, and has paid their shortfall out of his own pay since. He never
  learns it was a mistake; Maeca says it once, after. He also holds Sallow's
  letter asking for "the one from the ford", and his answer, "No.", written and
  never sent. *Arc:* the player loves him (four trunk scenes in Act 1), learns
  what he did from him, drunk, at the gate, and goes on loving him; at the top
  of Act 2 he goes down the hole at the Penhale farm drunk and shaking, counts
  them up the rope, laughs for the first time, and is hauled up by Maeca and
  the survivor; "Count's right."; she cuts the rope. *Fixed:* he dies at the
  rope on every road. He rises at his own gate on the fourth dusk, and the
  survivor lays him down. He never says sorry; it is written once in his
  daybook.
- **Maeca.** Just Maeca. *Face:* a hunter who tracks for the Watch ("before you
  ask. Not wolves."), paid out of Holloway's pocket; his kindest friend, who
  walks him home and buys his drink with his own money. *Secret:* she left her
  post at the cave mouths and went down the shaft after the boy she was sleeping
  with; she was on the ladder, the next hand up, number ninety-two, with her
  face in the shaft-head lamp, when the lid came down. Three days below: she
  finished the wounded before they could rise; on the third day she followed the
  air up an old wolf-run with the boy, and finished him at the cave mouth, and an
  old grey wolf lay down across the way in. The wet stone took two toes. Her
  three words about Ashford are "The cave mouths.": her post, and his report's
  lie. Half the Kerchiefs are her old neighbours ("Fed some of them, once.
  Buried more."). *Arc:* every kindness is true and is a hunter waiting; told of
  the lid, "...Did he."; at the rope, "Ninety-two." *Ends:* leaves with the Pack,
  if they will have her; takes the Watch, and counts them in at the war in his
  coat; dies at the breakthrough's edge.""")

rep("""  never showed a face; ten of twelve were collected. He suspects whose coin.
  *Arc:* his daughter Nell went south a fortnight before the survivor came up
  the road, with Wat the carter on toll work, and drowned at the ford, and rose
  in the ditch, and the survivor put her down. Whether the survivor tells him
  decides whether he forges the last two irons in Act 2 (and so whether a
  second crossing is woken), and whether in Act 3 he makes the cage the
  Warden's heart has to be carried in. *Ends:* breaks the last irons and hunts
  the coin; forges them and learns too late; makes the heart's cage; never
  works for the survivor again.""",
"""  never showed a face; ten of twelve were collected. He suspects whose coin. He
  is proud of them: the one thing he talks about unasked ("Irons on it. Mine.
  Ten. Best I've done."; "Girl's first new boots. Irons paid for 'em."; "Told
  her: walk where it's lit. Nothing on that road you can't see.").
  *Arc:* his daughter Nell went south a fortnight before the survivor came up
  the road, with Wat the carter on toll work, and drowned at the ford, and rose
  in the ditch, and the survivor put her down. From day 2 he asks, at dusk. On
  the truth he holds his own iron, from the Warden's fist, and knows: "She'd
  have thought I'd come for her." He puts out the last iron on the road with his
  bare hand, buries her, and works one-handed after; he beats the last two irons
  flat. On the lie ("I passed nobody", or "I didn't look") he goes on hoping
  through Act 1, forges and sells the last two irons in Act 2, the Kiln Ford is
  lit, and then Wat's grey mare comes up the south road with Nell's bundle, and
  he sees the iron at her belt: "That's mine. ...You passed nobody." **The lie
  costs his warmth, never play** (the owner): he works for her at the same
  prices, commissions and masterworks as on the truth road, and talks to her as
  if he hates her, or not at all. *Ends:* breaks the last irons and hunts the
  coin; forges them and learns too late; makes the heart's cage (on the lie
  road too, for what play needs, without a word to her).""")

rep("""| Holloway | The bible's own: he signed to cover his commander. Under it, nothing worse; the detail is that he still wears a garrison pair of boots. | His boots, seen, never mentioned. |
| Maeca | At Ashford she finished the wounded who could not be carried, and one of them was a boy she had been sleeping with. The Pack is the only thing that saw it and did not look away. | Her romance's "I've lain with my ear to a lot of things to see if they'd live." Never said. |""",
"""| Holloway | He saw what he was afraid of. The lamp was in his eyes, and he had the time it takes to breathe in, and he chose the four hundred; but he was also afraid, and the dead were what fear sees. | The roll at night: who each man left behind ("Abbot. Two bairns."). |
| Maeca | Below the lid she finished the wounded before they could rise, and the last of them was the boy she had gone down for. She has never decided whether she keeps Holloway alive or keeps him. | Her romance's "I've lain with my ear to a lot of things to see if they'd live." Never said. |""")

rep("""| Act | Major | Minor |
|---|---|---|
| 1 | None: Nell, as written | — |
| 2 | **Nell's boots** (Brannoc, above) | Keegan's mill-race; Wenna's choice; Jory and Ewan |
| 3 | **Ember is the dead**: the player burned Nell, and hears her say "Da" | Chid's one line; "The smith's girl was the twenty-fifth." |""",
"""Retired by the approved rewrite (the editor: "each said in one line" was the
punch pulled in writing). Each act now has one devastation on the trunk,
landed in full view, one twist, one elation and one laugh in its darkest
stretch (`TREATMENT.md` §1):

| Act | Devastation | Twist | Minor |
|---|---|---|---|
| 1 | **Brannoc knows**, his iron in his hands | **"You did this."** | Holloway's lid, told at the gate |
| 2 | **Maeca cuts Holloway's rope** | **"Ninety-two."**, then **the woman with the lamp** | Keegan's mill-race; Wenna's choice; Harlan; what you are |
| 3 | Her mother, found and lost; Chid at dawn | **The voice** | "Da", once, an echo |""")

rep("""**Ashford, the boots** (pays: Act 2, Holloway's letter and the boots)
- `maeca.barefoot`, `maeca.signed`: boots signed for, never came; "Somebody
  with a good hand and a ledger." Maeca never says "Ashford" on meeting, and
  her plate says "Hunter, of the Hollow": the player hears the word from Rook
  (`rook.valley`: "Don't ask Holloway about it. Don't ask Maeca."), Wenna and
  Holloway first, and puts her boots and his count together themselves.
- `holloway.maeca`, `holloway.ashford`: "I counted boots for the Ashford
  garrison, once, and I was good at it."
- `pell.t_pell`: his sister wrote the week before the Fall that the garrison's
  boots "had come in short, and somebody had signed for them full". Where that
  letter is in Act 2 depends on Pell's fate.""",
"""**Ashford, the lid** (pays: Act 2, the rope; `TREATMENT.md` §4)
- `maeca.watch`: Holloway pays her out of his own pocket; she buys his drink
  with it. `maeca.ashford`: "The cave mouths." (her post; his report's lie).
- `holloway.ashford` (sober): "That's the report." `holloway.roll` (night):
  "Abbot. Two bairns. Ancell. His mam." `scene_knocking` (the first dusk after
  the tremor, from day 4): the whole of it, in ledger syntax, with "Lamp in my
  eyes." Fact `holloway.confessed`; his night bark "Ninety-one up."
- `scene_gate_dawn`: Maeca's loaded crossbow across her knees over the sleeping
  man, read as care; "That's your last." `scene_did_he`: "...Did he." (fact
  `maeca.told_lid`). `scene_his_cup`: she fills his cup and sits with him.
- The decoy: `decoy.rope` (a Kerchief: "a rope with the captain's name on it")
  or `decoy.ledger` (Pell writing down every drink). `pell.t_pell`: the lid was
  "barred from the top. Somebody barred it. I know who."
- `sallow.rider`: a rider from the north, an hour in the Watch House; the
  letter face down (`holloway.letter`). Act 2: his answer, "No.\"""")

open(P, "w", encoding="utf-8").write(s)
print("ok")
