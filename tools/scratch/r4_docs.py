"""Round four: the soul sweep and the consistency fixes in the docs. Run from
the worktree root."""
import os

D = os.path.join(os.getcwd(), 'docs')


def edit(name, pairs):
    p = os.path.join(D, name)
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert s.count(a) == 1, (name, a[:90], s.count(a))
        s = s.replace(a, b)
    open(p, 'w', encoding='utf-8', newline='\n').write(s)


C = 'cinematics/'


def edit_done(name, pairs):
    p = os.path.join(D, name)
    t = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert b in t or b == '', (name, 'not applied', b[:60])


# ---------------------------------------------------------------- C01
edit_done(C + 'c01_drowned_fire.md', [
    ("Background left, beyond the firelight, the frost cracks across in a line, and a grey hand comes up through it (R1). She has not seen it.",
     "Background left, beyond the firelight, the frost goes dark in a patch, as if water were coming up through the ground, and a head comes up through it, hair streaming, the way a swimmer comes up (R1). They rise the way she did. She has not seen it."),
    ("then past it, at the bedroll, dry, its blanket folded. Line N1. A 1.5 s look at her background's item by the pack (see Variants), in the shot's last third. | 5.0 |",
     "then past it, at the bedroll, dry, its blanket folded. Line N1. She puts a hand inside her coat and takes out a folded letter, wet through, and opens it: the ink has run to blue water, and no word is left. She folds it and puts it back. (The letter that brought her home: her mother was failing. The water took it, as Vonnra will say.) A 1.5 s look at her background's item by the pack (see Variants), in the shot's last third. | 7.0 |"),
])

# ---------------------------------------------------------------- C02
edit_done(C + 'c02_none_cross.md', [
    ("Line W3. His eyes flare; all three posts flare with them (a frost nova at each); ice runs out from each post across the water.",
     "Line W3. The three posts' flames lean toward him, all at once, like grass in a wind: he is drinking them. Ice runs out from each post across the water."),
    ("W3 is the gate shutting: the whole body behind it.",
     "W3 is not a roar. It is the ford's rule, said as it has been said every night for two hundred years: the same tired register as \"Lie down.\", every word set down like a stone, no louder than W2."),
    ("| NONE. CROSS. AFTER DARK. | The gate shutting. Every word a stone. |",
     "| NONE. CROSS. AFTER DARK. | The ford's rule, not a threat. Tired; every word set down like a stone; no louder than \"Lie down.\" (The capitals are the subtitle's, not the performance's.) |"),
    ("W3: the posts flaring (the frost-nova sound), ice cracking across the water.",
     "W3: the posts' flames leaning toward him with a sound like a breath drawn in through teeth; ice cracking across the water."),
])

# ---------------------------------------------------------------- C03
edit_done(C + 'c03_heart_goes_down.md', [
    ("*(Devout: after the nod, she closes her hand over her heart and opens it toward him, palm out: the Order's sign for the dead. Chid makes the same sign at Nell's grave, C08.)*",
     "*(Devout: after the nod, she makes the Order's sign for the dead: finger and thumb closing slowly on the air, as a lamp-tender puts out a chapel lamp at morning. Chid makes the same sign at Nell's grave, C08.)*"),
])

# ---------------------------------------------------------------- C04
edit_done(C + 'c04_first_light.md', [
    ("the ford she died trying to cross, and her wet prints",
     "the ford she went down to for water at dusk, and her wet prints"),
    ("**She changes** from a thing\n  that burned to a woman who is cold.",
     "**She changes** from a thing\n  that felt nothing to a woman who can feel the cold."),
    ("the light comes down the trunks like water filling a glass. | 5.0 |",
     "the light comes down the trunks, and where it reaches the road, the blue in the iron by the verge goes pale and small. | 5.0 |"),
    ("Focus pulls from Rook's folded arms to the survivor stopping at the square's edge, looking round at the faces. Rook looks at her; then up, east, at the toll tower. | 4.0 |",
     "Focus pulls from Rook's folded arms to the survivor stopping at the square's edge, looking round at the faces. Rook looks at her; then up, east, at the toll tower. *(Hunter: Rook's look on her holds one beat longer before it goes to the tower, and her arms tighten. She knew this woman's mother. She says nothing, that morning or after: her third layer.)* | 4.0 |"),
])

# ---------------------------------------------------------------- C06
edit_done(C + 'c06_forty_one_mouths.md', [
    ("Redcowl looks at her for a long moment, then laughs: a big chest laugh, with nothing in his eyes.",
     "Redcowl looks at her for a long moment, then laughs, a big chest laugh, at the boy with the wooden sword, who is still pointing it at her, very seriously; then he looks back at her, and the laugh is gone."),
    ("on \"After!\" he crushes the tin cup.",
     "on \"After!\" he sets the tin cup down on the crate very carefully, as if it were full. (His brother's tell: Rav does the same with the news in C11.)"),
])

# ---------------------------------------------------------------- C09
edit(C + 'c09_fortune.md', [
    ("From under the town comes C03's groan, long and low, and down in the streets every dog starts barking at once.",
     "From under the town comes C03's groan, long and low, and behind Vonnra, down in the streets, every lamp in the town dips at once and comes back: every ember lamp. The braziers on the wall do not."),
    ("Then the groan stops, and the dogs one by one.",
     "Then the groan stops, and the town's lamps are steady again."),
    ("the\n    town's dogs; then their silence one by one; then the pad back,",
     "the\n    town below, very quiet; then the pad back,"),
    (" Some of the ink is old and brown, some is not.", ""),
])
# ---------------------------------------------------------------- C10
edit(C + 'c10_hollow_by_night.md', [
    ("Title: **GREYMUZZLE** / *The Old Alpha*.", "Title: **GREYMUZZLE** / *Who Kept the Cold Off*."),
])
# ---------------------------------------------------------------- C11
edit(C + 'c11_raid_on_the_roost.md', [
    ("edge, a child crying, once, and hushed.",
     "edge, the Roost's kitchen: a ladle knocks once on the rim of a pot, and stops."),
])
# ---------------------------------------------------------------- C13
edit(C + 'c13_behind_the_door.md', [
    ("**The Barrow Lord: arrival and the kneel.**", "**The Barrow Lord: arrival and the hand at the gate.**"),
    ("· door 12.5 s, arrival 8 s, kneel\n16 s ·", "· door 12.5 s, arrival 8 s, the\nhand 16 s ·"),
    ("""and the dead come on. When he falls he does not fall: he goes down on one knee
before her and bows his head, and says one more word, and the dead stop, and
crumble, and the way back up is open.""",
     """and the dead come on. When he falls he does not fall. He puts his hand flat on
her breastbone, as you would stop someone at a gate, and says one more word, and
pushes, once, and she steps back. Around them the dead step back onto the stair,
all together, and stand. They are not beaten. They are sending her home."""),
    ("**The kneel:** the boss's death", "**The hand:** the boss's death"),
    ("the kneel staged", "the hand staged"),
    ("## The kneel", "## The hand at the gate"),
    ("| 1 | MS | 50 | Static, low; `WorldRate` 0.2 on the blow | The blow. He does not fall. He goes down on one knee before her, sword point to the ground, and bows his head. Around them every one of the dead stops where it stands. | 4.0 |",
     "| 1 | MS | 50 | Static, low; `WorldRate` 0.2 on the blow | The blow. He does not fall. He steps in, inside her weapon, and puts his gauntlet flat on her breastbone, as you would stop someone at a gate. Around them every one of the dead stops where it stands. | 4.0 |"),
    ("| 2 | CU | 85 | Static, low, up at his bowed helm | Line B2. | 3.0 |",
     "| 2 | CU | 85 | Static, on the gauntlet on her breastbone, then tilting up to his helm | Line B2. He pushes, once, not hard: she steps back. | 3.0 |"),
    ("| 3 | LS | 28 | Static | The dead crumble where they stand, all together: bone, rust, dust on the wind. The Barrow Lord last. The way out stands open at the head of the stair. | 4.0 |",
     "| 3 | LS | 28 | Static | The dead step back onto the stair, all together, rank by rank, and stand at attention on its steps; the Barrow Lord last, two steps down, facing her. They are not beaten. They are letting her go. The way out stands open at the head of the stair. | 4.0 |"),
    ("""drill. The kneel is a salute, not a surrender: precise, one knee, sword point
down, head bowed to exactly the same depth an officer bows to a superior.""",
     """drill. The hand on her breastbone is a sentry's, not a priest's: the gesture
of a man who has turned back a great many travellers at a gate, and is turning
back one more. It is the only time he touches anyone. It is not unkind."""),
    ("*Kneel:* `eyes_wide` 0.3, `mouth_open` 0.1; she does not\nlower her weapon.",
     "*The hand:* `eyes_wide` 0.3, `mouth_open` 0.1; she takes the step back before she\nhas decided to."),
    ("Kneel: music cut\n  on the blow; silence when the dead stop (all the horde's sounds at once:\n  nothing); the crumbling (a long, dry rush); then,",
     "The hand: music cut\n  on the blow; silence when the dead stop (all the horde's sounds at once:\n  nothing); their armour as they step back onto the stair, all at once, one\n  sound; then,"),
    ("kneel (armour); the dust on the wind.", "gauntlet on her coat; the dead's step back, together."),
    ("on the dead; the crumble (bones to dust, a particle burst on every body); the\nviolet point far down the stair.",
     "on the dead; the violet point far down the stair."),
    ("- **Arrival, kneel:** as C10.", "- **Arrival, the hand:** as C10."),
    ("the horde told to stop and to crumble together; a kneel on one knee with a\nsword (a salute pose);",
     "the horde told to stop and to step back together onto a set (the stair) and\nstand; a hand laid flat on another's breastbone, and a push (a two-person pose);"),
])

# ---------------------------------------------------------------- Act 2 outline
edit(C + 'act2_outline.md', [
    ("the barn's floor sagging; the ground opening\n  like a mouth; the farm going down (or not);",
     "the barn's floor sagging; then, in Tam's words, \"The\n  knocking stops. Then the floor isn't there.\"; the farm going down (or not);"),
    ("Three.\n  It cannot abide running water. The knight shall not converse with it beyond\n  what is needful.\"",
     "Three.\n  It shuns the lamp, and will not come where the lamps are lit. The knight shall\n  not converse with it beyond what is needful.\""),
    ("- **The wrong sign.** Three is false, and Keegan knows it: the one she is\n  reading it to came up out of a river.",
     "- **The wrong sign.** Three is false, and Keegan knows it: the one she is\n  reading it to has stood in her gate lamp every night for three weeks, and\n  walked up the Low Ford road between the lamps."),
])

# ---------------------------------------------------------------- Act 3 outline
edit(C + 'act3_outline.md', [
    ("""- **Variants.** *Accused:* she tells it unasked, in her own words, in order, and
  calls the survivor by name throughout: the only long speech she makes in the
  game. *Not accused:* she admits each piece only as the survivor lays it down
  (dialogue), and calls her "traveller" until the end.""",
     """- **How she tells it: she reads it.** Not a speech. She sits on the landing,
  opens the ledger from C09, and reads the entries aloud, in order, as she read
  the palm: a name, a date, a crossing. Wat. A woman from Low Kiln. A pedlar with
  no name, "the pedlar". At twenty-five she reads "Nell, the smith's girl" in
  exactly the voice she used for twenty-four. At twenty-seven she reads the
  survivor's name (or "the one from the ford"), and stops, because there is
  nothing after it yet.
- **Variants.** *Accused:* she reads it unasked, at the first landing, and calls
  the survivor by name after. *Not accused:* the survivor finds the ledger on
  the stair among the pieces and reads it herself (the page as an insert, C09's
  page, now legible), and Vonnra admits each entry only as it is laid down,
  calling her "traveller" until the end."""),
    ("""- **Key lines.** "I drowned twenty-six people to find you. I wrote every one of
  them down." (The plain verb, after a whole game of "arranged": that is her
  change.) Then, later, unasked, in the middle of something else: "The smith's
  girl was the twenty-fifth." And silence: no music, nobody moves, and the
  survivor does the arithmetic (she came after the twenty-sixth). The ledger in
  C09 is the page these lines land on.""",
     """- **Key lines.** "I drowned twenty-six people to find you. I wrote every one of
  them down." (The plain verb, after a whole game of "arranged": that is her
  change.) Then she opens the book. "The smith's girl was the twenty-fifth" is not
  a line any more: it is the twenty-fifth entry, read in the same voice as the
  others, and the silence after it is the player's. The ledger in C09 is the page
  these entries are read from."""),
    ("(then she climbs the stair, alive and cold, breathing smoke).",
     "(then she climbs the stair, alive, and shivering, breathing smoke)."),
    ("the way the dogs did in C09,", "the way the town's lamps did in C09,"),
])

# ---------------------------------------------------------------- README: the colour key
edit(C + 'README.md', [
    ("""- **ford-lamp blue** (`#8ac8ff`, steady, cold): ember burning in a Warden's
  iron (Brannoc's new irons on the Low Ford road; the Wardens; the chain). The
  Watch's oil, when it had any, burned warm, like any lamp: a warm lamp at the
  ford means nothing is drinking from it;""",
     """- **ford-lamp blue** (`#8ac8ff`, steady, cold): ember burning in a Warden's
  iron, and only there (Brannoc's new irons on the Low Ford road; the Wardens;
  the chain). In an open lamp ember burns gold, small and very steady: Rook's
  Order lamp, Vonnra's lamp on the tower, the town's lamps. Oil, when anyone has
  it, burns yellower and smokier than either (Brannoc's lantern in C14). Sella's
  blue room is indigo glass over a warm flame, never `#8ac8ff`;""")
])

# ---------------------------------------------------------------- the bible
edit('STORY_BIBLE.md', [
    ("""Last winter
somebody hung twelve new irons there, the kind made to hold ember (cages, not
oil-lamps: Brannoc's irons, his mark under the socket), and lit them with it.
That woke the Warden. Ford-lamp blue is ember burning in a Warden's iron; the
Watch's oil burned warm.""",
     """Last winter
somebody hung ten new irons along the road and at the ford, the kind made to hold
ember (cages, not oil-lamps: Brannoc's irons, his mark under the socket; twelve
were forged and two are still on his rack), and lit them with it. That woke the
Warden. Ember burns blue only in an iron; in an open lamp it burns gold and very
steady; oil burns yellower and smokier. The ford's own three posts the Warden
broke in the fight; the road's irons are still burning when Brannoc walks down
it (C14)."""),
    ("""Their mother lived in the valley (on a farm at the Verge's edge, for a
hunter, and Rook knew her; elsewhere in Thornhollow for the rest: the
background says where the survivor went, not where they came from).""",
     """Their mother lived in the valley (on a farm at the Verge's edge, for a
hunter, and Rook knew her; elsewhere in Thornhollow for the rest: the
background says where the survivor went, not where they came from). She is
buried in the Quiet Garden behind the shrine, a week before Nell, under a
plain wooden marker that nobody points out (C08); Rook, if she knew her, says
nothing. The letter that brought the survivor home is in her coat in C01, the
ink run to blue water."""),
    ("""- `chid.long`: Rook's mother brought him bread. `chid.warden`: "Before me,
  certainly, which is a long time." """,
     """- `chid.long`: Rook's mother brought him bread. `chid.warden`: "Before me,
  certainly, which is a long time." (His "I think" there is Chid hiding: he knew
  the Warden, Brother Tobin, Act 3.) """),
])

edit('WRITING_PASS.md', [
    ("burial[[Next dawn: he fetches her, Chid meets the cart, they bury her by Ashe: nell.buried]]",
     "burial[[That dusk he goes down the road for her, alone or with the survivor (C14); at sunrise Chid meets him at the gate; they bury her by Ashe: nell.buried]]"),
])
print('ok')
