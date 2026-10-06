"""Bible: the canon decisions of round three (ember is the dead; oil and
ember; the body; the mother; third layers; kindnesses; extremes; the
cinematics seeds; Acts 2 and 3; romance). Run from the worktree root."""
import os

p = os.path.join(os.getcwd(), 'docs', 'STORY_BIBLE.md')
s = open(p, encoding='utf-8').read()


def rep(a, b):
    global s
    assert a in s, a[:90]
    assert s.count(a) == 1, ('not unique', a[:90])
    s = s.replace(a, b)


# ------------------------------------------------------------------ section 1
rep("""**Ember is the Morrow's light,** and its pain. It leaks up through the ground
as stone and dust. The Order burned it in its chapel lamps and called it the
morning ("the dark is only the part of the day that hasn't happened yet" was
never a metaphor: their morning was chained underneath them). The Watch burned
it in the ford lamps to keep the Wardens asleep. The Dig cooks it into slurry.
Everyone in the valley lives by it, and almost nobody knows what it is.""",
    """**Ember is the Morrow's light,** and its pain. It leaks up through the ground
as stone and dust. The Order burned it in its chapel lamps and called it the
morning ("the dark is only the part of the day that hasn't happened yet" was
never a metaphor: their morning was chained underneath them). The Dig cooks it
into slurry. Everyone in the valley lives by it, and almost nobody knows what
it is.

**What the Morrow is made of.** The Morrow is older than the empire, and it
eats the light of every death in the valley and keeps it. The Seventh Legion
did not chain a god: it chained a grave, and tapped it. **Ember is the held
dead, leaking up.** Every lamp in Thornhollow burns somebody's grandmother; the
survivor got up the Low Ford road on the first night by burning the drowned,
and one of the drowned was Nell. The rules, which never bend:
1. Whoever dies in the valley goes into the Morrow. Their light goes down; the
   body stays where it fell, and is quiet.
2. Near ember, in the dark, where the chain is thin, the light sometimes comes
   back up into the body. Almost always it comes up wrong, muddled with other
   lights, and the body rises mindless (the drowned in the ditch).
3. Killing a risen thing lets its light out, as ember. That is why the dead,
   the beasts that drank the slurry and everything in an ember scar drop it:
   they were full of it.
4. Burning ember spends it, and spent light goes back down. Nothing is ever let
   go: it goes round. That is the chain's real work, and why neither the Morrow
   nor its dead can rest.
5. An Unchained who burns ember is burning other people's light, and it crowds
   out their own. A vessel holds so much. This is why the survivor forgets: the
   names first, then the faces. Every night's ember is somebody else's memory
   pushing in.
Why one in a great many rises with their mind is **never said**. Chid hopes it
is because someone down there would not let go of them; the game neither
confirms nor denies it, and no rule depends on it. (It must never become a
law: a player would apply it backwards to Nell.)

Every faction is partly right, and that is how the reveal stays fair: the town
thinks ember is a mineral (it burns, it sells); the Order called it the morning
and burned it for company, not for seeing by ("the morning lies a little under,
and it will wake you where you slept"); the Watch kept it out of the ford lamps
for reasons it forgot; the Vigil knows the Unchained are made of it; the binders
think it is a chained beast's light and pain, and never asked where the beast's
light comes from; the lamplings give it their own dead on purpose ("Nobody's!
Nobody's lost!"). Twenty seeds of it are already in the shipped text
(`docs/editorial/THE_EMBER_REVEAL.md` §5); nobody says it until the bottom of
the stair.

**Oil and ember: the lamps.** The Order's lamps burned **ember**, and ember
feeds a Warden: the Wardens were made to keep the Morrow's crossings, and they
drink its light. When the Watch took the crossings it burned **oil** in the
ford lamps: light enough to cross by, and nothing in it for the Warden to drink,
so it slept. Then the Watch ran out of oil ("We've not had oil for those lamps
since my first winter"), and the ford went dark and stayed quiet. Last winter
somebody hung twelve new irons there, the kind made to hold ember (cages, not
oil-lamps: Brannoc's irons, his mark under the socket), and lit them with it.
That woke the Warden. Ford-lamp blue is ember burning in a Warden's iron; the
Watch's oil burned warm.""")

rep("""Ford road. Once in a great many deaths, one rises **with their mind**: an
**Unchained**. They burn at night, when the chain is weakest (the Legion's
sigils drink sunlight; the dark is when they starve), and at dawn the light
drains back into the ground and leaves them ordinary. That is the ember the
player grows each night and loses each dawn.""",
    """Ford road. Once in a great many deaths, one rises **with their mind**: an
**Unchained**. They burn at night, when the chain is weakest (the Legion's
sigils drink sunlight; the dark is when they starve), and at dawn the light
drains back into the ground and leaves them ordinary. That is the ember the
player grows each night and loses each dawn. **The body keeps the opposite
hours.** By night an Unchained is the river's: cold as stone, the heart slow
(it can stop for a count of seven and start again), and the breath does not
show in the cold, though it can be heard. At dawn, as the ember goes back into
the ground, the warmth comes into them all at once, like a lamp turned up: the
heart quick, the breath smoking (C04). Every lover notices it in their own
trade's words, and none of them knows what it means until Act 2.""")

rep("""had died. The title screen's hooded stranger by that fire is the survivor at
dusk, before the water; creation gives them a face. That night the Morrow's
light in them let them do what no living traveller had: kill the Warden.""",
    """had died. The title screen's hooded stranger by that fire is the survivor at
dusk, before the water (hood up, back to the camera: it must read as anyone);
creation gives them a face. That night the Morrow's light in them let them do
what no living traveller had: kill the Warden.

**The survivor's mother.** Whatever their background, the survivor was coming
home. Their mother lived in the valley (on a farm at the Verge's edge, for a
hunter, and Rook knew her; elsewhere in Thornhollow for the rest: the
background says where the survivor went, not where they came from). A letter
found the survivor on the road that she was failing, and they came as fast as
they could, and camped at the Low Ford at dusk a day short. She had died the
week before. The survivor does not know. She is in the Morrow. Hers is the face
that is not quite where they left it at dawn; hers is the name Chid asks for
and the name the survivor says over and over in Sella's bed; and at the bottom
of the stair she is saying the survivor's name, the way she did when they were
small and late in from the yard. (The player may name her at creation; if not,
the game never names her, and "Mam?" is enough.)""")

rep("""must drown a great many to get one. So last winter she had twelve lamp-irons
forged for the Low Ford, paid in the binders' square coin, relit the lamps to
wake the Warden, and sent travellers across after dark on toll work at double
pay.""",
    """must drown a great many to get one. So last winter she had twelve lamp-irons
forged for the Low Ford, paid in the binders' square coin, hung them, lit them
with ember to wake the Warden, and sent travellers across after dark on toll
work at double pay. She drowned twenty-six before the survivor, and wrote every
one of them down; the smith's girl was the twenty-fifth.""")

# ------------------------------------------------------------------ section 3
rep("""| Chid | A cheerful fool of a priest | An Unchained of the Order's day, near two hundred years old; "C." of the note in Ashe's trunk | Act 3 |""",
    """| Chid | A cheerful fool of a priest | An Unchained of the Order's day, near two hundred years old; "C." of the note in Ashe's trunk; goes to the ford when the lamps are lit, and was there the night the survivor rose | Act 3 |""")
rep("""| The Morrow | A thing praying under the Verge | Prays to be let die. The chain has kept it alive and harvested for two thousand years. | Act 3 |""",
    """| The Morrow | A thing praying under the Verge | Every death in the valley, held. It prays to be let die, which is its dead asking to be let go; close to, the praying is names. The chain has kept it alive and harvested for two thousand years. | Act 3 |
| Ember | A mineral; the morning; the Morrow's pain | The held dead, leaking up | Act 3 (seeded from the first night) |
| The survivor's mother | Someone the survivor cannot quite picture | Dead the week before the ford; in the Morrow | Act 3 (the bottom of the stair) |""")

# ------------------------------------------------------------------ section 4
rep("""| **The Watch** (Holloway) | Keeps the roads and the peace. | Founded to keep the ford lamps and the Wardens asleep, and to "keep it done".""",
    """| **The Watch** (Holloway) | Keeps the roads and the peace. | Founded to keep the ford lamps burning oil, never ember, so the Wardens slept, and to "keep it done".""")
rep("""| **The Order of the Morning Light** (Chid) | A dead priesthood with one fool left. | Made the Wardens and worshipped the light they guarded. "Left" Thornhollow when the Vigil came for it for sheltering Unchained. Its last priest is one. |""",
    """| **The Order of the Morning Light** (Chid) | A dead priesthood with one fool left. | Made the Wardens and worshipped the light they guarded, knowing what it was: the morning under the ground that keeps the dead and will wake them. It burned ember for company, not for seeing by. "Left" Thornhollow when the Vigil came for it for sheltering Unchained. Its last priest in the valley is one; outside it, a few chapels still keep lamps nobody comes to see, without knowing why (the devout survivor was raised in one). Its evening call is "Lamps are lit. Stay where they reach."; at the end of a watch the keeper asks "Is it morning?" and is answered "Not yet." Its word for the dead is "Lie down." |""")

# ------------------------------------------------------------------ section 5 coda
rep("""- **Snib.** Exactly what he looks like. Survives everything, in every ending.

## 6. Act 1: The Waystation""",
    """- **Snib.** Exactly what he looks like. Survives everything, in every ending.

### Under the reasons: the third layer

Every named person has three reasons: the one they would give at a trial, the
one they tell themselves at night, and the small one underneath that a friend
of forty years would name after the funeral. The first two are in the entries
above. The third is here. It is almost never said: it shows as a detail the
player sees, as someone else's line, as a slip under stress, or once, in Act 3,
as the person's one exception to their "never". (`docs/editorial/REALNESS_AND_EXTREMES.md`
has the reasoning.)

| Who | Underneath | How it shows |
|---|---|---|
| Vonnra | Pride: she is the last of a line that kept the Legion's keys, and she cannot bear to be the one in whose time the chain broke. | "I am not angry. I am arranging." Her first feeling is for her arrangement. Act 3. |
| Rook | She knew. Not all of it, but she watched the carters go down the south road and not come back, and took double for the survivor and asked nothing, because the Last Lamp was failing and she would not be the woman who lost Ashe's inn. Her Act 2 turn is a woman deciding she can no longer pretend, not one learning. | "Don't look like that, pet." Act 2. |
| Holloway | The bible's own: he signed to cover his commander. Under it, nothing worse; the detail is that he still wears a garrison pair of boots. | His boots, seen, never mentioned. |
| Maeca | At Ashford she finished the wounded who could not be carried, and one of them was a boy she had been sleeping with. The Pack is the only thing that saw it and did not look away. | Her romance's "I've lain with my ear to a lot of things to see if they'd live." Never said. |
| Wenna | In the fever year there was not enough bitterroot, and she chose who got it; she was right about most, and wrong about Harlan's sister, whom she passed over for a man she liked better. She has never named the fever year's dead because one of the names is a decision. | Act 2's breakthrough, when she has to choose again. |
| Harlan | He likes being the man who brings salt to the valley; the B.E. paid for the new sign over Coyle Trading; he has never once thought of the pipe-lads. | The sign. Act 2. |
| Pell | He did not go up to Ashford after the Fall for his sister's books out of love; he went for her savings, and has counted ever since because counting is the only grief he can do. | Act 2, if asked the right way. |
| Redcowl | The ones nobody would pay for went in the ravine. He knows what happened to Ewan. | The fourth cage, empty, its door open (C06). |
| Rav | He chose which prisoners were worth treating at the Roost. "Half my patients die. The other half pay." was a joke, and a policy. | Act 2. |
| Sella | She sold Jessop: his bragging upstairs reached Vonnra through her, and that is how Vonnra knew she had a clerk who would do anything for silver. She does not know what it bought. If she learns it, it is the first thing about her work she is sorry for. | Act 2. |
| Jory | In the cage, when the Kerchiefs asked which of the four would make trouble, he pointed at Ewan. That is why he shouts the name in his sleep. | Act 2, from Redcowl or Rav, to the survivor only. |
| Keegan | She has done it before: in her first month, in the north, she returned a girl of fourteen who had drowned in a mill-race and got up. By the handbook, with the prayer. Then she was posted to a gate nobody uses. | Act 2, at the gate: "Once. She thanked me. They do, the first time. They're frightened." |
| Brannoc | He suspected whose square coin it was, and did not ask, because the irons paid well and Nell's boots had holes in them. The irons that drowned her bought the new boots she drowned in. | Act 2's major extreme (below). |
| Chid | He goes to the ford when the lamps are lit. He was there, in the reeds, the night the survivor rose, and every night before it. He could not have stopped it. He did not try. He wanted to see one get up. | One line in Act 3, if asked. |

Untouched, on purpose: Tam (nine, and right), Snib (no secret at all),
Greymuzzle (an animal), Grimtunnel (his sincerity is his whole horror), and the
dead (Nell, Wat, Corran), who are only what is said of them. Vonnra did not
choose Nell: she is more frightening as an administrator who did not look.

### Kindness from the wrong people

Each hard person does one kind thing, for no reason they could defend. None of
them redeems anyone; people are not a ledger, even in a valley that keeps one.
- **Pell** pays for Aldo's widow's journey up from Low Kiln, and charges
  Holloway for the cart.
- **Redcowl** sends the Penhales a ham when the ground opens, with no note,
  because his mother would have.
- **Vonnra** has paid the rent on Chid's shrine for forty years. He has no
  idea.
- **Holloway** wrote Corran down as a deserter, and has paid his widow the
  ration out of his own pay since.
- **Sallow** (Act 2) has kept Edric fed, warm and read to for twelve years,
  when it would have been cheaper to burn him.

### The extremes, rationed

One major turn an act, each a human choice, each planted at least twice, each
said in one line, each landing on the debt to the dead. Fixed points the story
never desecrates: Tam, Snib, Greymuzzle, and Rook's kitchen.

| Act | Major | Minor |
|---|---|---|
| 1 | None: Nell, as written | — |
| 2 | **Nell's boots** (Brannoc, above) | Keegan's mill-race; Wenna's choice; Jory and Ewan |
| 3 | **Ember is the dead**: the player burned Nell, and hears her say "Da" | Chid's one line; "The smith's girl was the twenty-fifth." |

Rejected, and why: Vonnra choosing Nell (a third motive on one death, and it
makes Nell a pawn); the survivor having taken toll work (it fights C01's
bedroll and flask, and takes the player's own character from them); Holloway
having sold the boots (two boot reveals in one act blur); Chid pulling the
survivor out and building the fire (the prints say she walked).

## 6. Act 1: The Waystation""")

# ------------------------------------------------------------------ section 6 seeds: the cinematics
rep("""**Below** (pays: Act 2, the breakthrough; Act 3)""",
    """**The cinematics** (`docs/cinematics/`; each script says what it plants and pays)
- C01: her own prints come up from the river and none go down; her breath is
  heard and does not show; the weed in her hair; the flask smells of the river.
  (Act 2, what you are.)
- C02: the Warden's "Lie down." (the Order's word for the dead, said to the
  living); the lamp lifted to her face, which a keeper does to look for breath;
  the new iron in an ancient gauntlet. (C08; Act 2; the lamps.)
- C03: "Is it morning?", and the survivor's nod, the first "yes" he was ever
  given (Act 3, Chid: his name was Tobin); the heart's light reaching for her;
  Grimtunnel's "You smell like downstairs" and "Downstairs'll be ever so
  grateful" (Act 3: "It isn't grateful"); the groan under the ground.
- C04: new prints up out of the river at dawn; her first breath smoking; the
  ember going "back into the ground" (Act 3: where the dead go); the mother's
  face; the lamp in the tower window burning in daylight; Rook's glance at it.
- C05: Greymuzzle's lip lifting at her smell; his look back at the den (C10).
- C06: "Them first."; the crates as a bench; the Ashford standard; the fourth
  cage, empty (Ewan).
- C07: the hammer as the town's clock; Nell's old holed boots on a nail by the
  rack (Act 2's major extreme).
- C08: the burial hymn "Lie Down" ("the morning lies a little under / and it
  will wake you where you slept": true, in Act 3); Vonnra in the ring, not
  bowing, looking at the survivor; Rook's lamp at the grave in daylight; the
  Order's sign.
- C09: the vistas on Vonnra's eyeline (her sight is a roof and a long memory);
  the breath in the lamplight; the struck ledger, twenty-six lines and one not
  struck (Act 3: "I wrote every one of them down"; C50); the tremor that stops
  her mid-sentence.
- C11: Redcowl's last words (Rav: "the leg held"); C12: "It went ever so
  QUIET!"; C13: "Nondum." and "Redi.", the Latin over the door, Jessop's back
  on the stair.
- C14: Wat and the carters risen round Brannoc's cart; Brannoc with his hammer
  outside the forge.

**Below** (pays: Act 2, the breakthrough; Act 3)""")

# ------------------------------------------------------------------ Act 2
rep("""**2. Keegan's chapter four.** She has watched for the signs (`keegan.saw_risen`,
the arcanist's burning, how often the survivor comes back). Act 2 brings her
to ask, straight: "Did you die on the Low Ford road?\"""",
    """**2. Keegan's chapter four.** She has watched for the signs (`keegan.saw_risen`,
her table of the survivor's breath on the wall at night, how often the survivor
comes back). Act 2 brings her to ask, straight: "Did you die on the Low Ford
road?" The survivor can ask back whether she has done this before: "Once. She
thanked me. They do, the first time. They're frightened." (The handbook's
text is in `docs/cinematics/act2_outline.md`, C21.)""")
rep("""**8. Brannoc's two irons and the second crossing.** A hooded buyer comes for
the last two irons, with square coin.
- `nell.told` `gone` or `risen`: he will not sell. He breaks them, and asks the
  survivor to sit up with him at the forge: the buyer wears the Toll Tower's
  violet (a new clerk, never Vonnra herself). No second crossing.""",
    """**8. Brannoc's two irons and the second crossing.** A hooded buyer comes for
the last two irons, with square coin.
- `nell.told` `gone` or `risen`: he will not sell. He breaks them, and asks the
  survivor to sit up with him at the forge: the buyer wears the Toll Tower's
  violet (a new clerk, never Vonnra herself). No second crossing. Then **Nell's
  boots** (Act 2's major extreme): Rook, afterwards, not to him, to the survivor:
  he bought the girl's new boots with the irons money, in square coin; the
  cobbler showed her. "I didn't think, pet. Nobody thought." Brannoc says
  nothing at all. He puts the two broken irons in the fire, then takes Nell's
  old holed boots down off the nail by the rack (they have hung there since
  C07, unremarked), and puts them in after, and stands and watches them burn.""")
rep("""**11. What you are (the act's turn).** The ledger, Keegan's chapter four, and
Chid, if the survivor goes to him, say it: the survivor died at the Low Ford
and rose with their mind. Every seed in section 6 lands here: "You were cold
when they brought you in", the far bank, the names going first, the mother's
face. Mechanically, from here the night's ember can be made to cost a memory
the player chooses.""",
    """**11. What you are (the act's turn).** The ledger, Keegan's chapter four, and
Chid, if the survivor goes to him, say it: the survivor died at the Low Ford
and rose with their mind. Every seed in section 6 lands here: "You were cold
when they brought you in", the far bank, the names going first, the mother's
face. Mechanically, from here the night's ember can be made to cost a memory
the player chooses, and when one goes, something else is briefly there in its
place at dawn: a line that is not the survivor's ("You cannot remember the name
of the street you grew up on. You can remember, very clearly, a grey mare who
would not take a bit in winter, and you have never owned a horse." / "Your
father's hands are gone. In their place: a hammer, and someone saying
'Mine.'"). The player can identify every one: Wat's mare, Nell's father. That is
the floor of Act 3's reveal, and a careful player stands on it by the act's
end. At Silverstair Edric says the rest of it, from a cage: "They bleed us for
the silver lamps. Every night. And every night I know someone else's mother."
(Rule 5 of the ember; section 1.)""")
rep("""survivor, Chid, the freed. Who holds the north gate is everything Act 2
decided (Holloway, Keegan, Maeca and the Pack, Redcowl's people or Rav's,
Brannoc).""",
    """survivor, Chid, the freed. Who holds the north gate is everything Act 2
decided (Holloway, Keegan, Maeca and the Pack, Redcowl's people or Rav's,
Brannoc). The night before is the eve (`romance.eve`, section 11): one night,
with one of the open romances, or alone, or on the wall.""")

# ------------------------------------------------------------------ Act 3
rep("""**Vonnra's truth.** With `vonnra.accused`, she tells it at the top of the
stair, in her own words and her own time: she owes the survivor for having
seen her. Without it, the survivor finds the pieces on the stair and she
admits only what they hold. The whole of it: the Ashford Fall; the failing
chain; the irons and the square coin; the carters' notice and the drowned
(Wat, Nell); the caravan she let go; Jessop sent through the door; the
survivor made.""",
    """**Vonnra's truth.** With `vonnra.accused`, she tells it at the top of the
stair, in her own words and her own time: she owes the survivor for having
seen her. Without it, the survivor finds the pieces on the stair and she
admits only what they hold. The whole of it: the Ashford Fall; the failing
chain; the irons and the square coin; the carters' notice and the drowned
(Wat, Nell); the caravan she let go; Jessop sent through the door; the
survivor made. "I drowned twenty-six people to find you. I wrote every one of
them down." The plain verb, after a game of "arranged", is her change. Later,
unasked: "The smith's girl was the twenty-fifth." Her truth is a chained beast,
a failing chain and a necessary cruelty, and she believes it. The player, by
now, holds more than she does. Why not Chid, an Unchained across the square for
two hundred years? A link has to hold the dead, and the survivor fills with
them every night she burns; Chid has never burned. She says it once, as a clerk
explains a fee.""")
rep("""**Chid's truth.** He is Unchained, from the Order's day. He wrote the note to
Ashe. If the chain is re-forged tight, every Unchained goes back to the dark,
him included. He has known all along and wants the survivor to choose without
thinking of him; he is the one person who never asked anything of them.""",
    """**Chid's truth.** He is Unchained, from the Order's day. He wrote the note to
Ashe. If the chain is re-forged tight, every Unchained goes back to the dark,
him included. He has known all along and wants the survivor to choose without
thinking of him; he is the one person who never asked anything of them. He
knew the Warden: Brother Tobin, the Order's keeper of the Low Crossing, who
asked every night at the end of the watch whether it was morning and was told
"Not yet". If the survivor tells him she nodded, he says, "You told him yes.
...Good. Somebody should have." And if she asks who else knew what the lamps
were for, his one line, the gentlest man in the valley's worst thing, said
plainly: "I go when the lamps are lit. I couldn't have stopped it. I didn't
try. I wanted to see one get up.\"""")
rep("""**What the Morrow prays for.** To be let die. The chain has kept it alive and
harvested for two thousand years; ember is its pain.""",
    """**What the Morrow prays for.** To be let die. The chain has kept it alive and
harvested for two thousand years; ember is its pain. **At the bottom of the
stair the survivor hears it properly**, being of its light, and it is not one
voice and it is not praying: it is a great many voices saying names. Aldo, in a
woman's voice. Ewan, in a boy's. Corran; Dannet, over and over. Very near, a
girl says "Da", the way you say a word you have not said for a while, to see
if it still works. Grimtunnel, holding the heart up: "You hear Him? All of them,
He's got, every one that ever went down. Nobody's! Nobody's lost! He keeps them
ALL." Then, out of all of it, the survivor's mother, saying their name; and
for once her face is exactly where they left it. Vonnra, who hears none of it
(only the Morrow's own light can), asks what it is saying: two thousand years,
and it has never said anything to her family. If the survivor tells her, she
breaks her rule, once, both halves of it: "...No. (A long time.) I wanted the
lamps to stay lit. That is all I ever wanted. I wanted it to be morning." If
Brannoc made the heart's cage, he is on the stair, and has heard his daughter,
and says nothing: he looks at the survivor's hands for a long time, the way he
looks at iron to see what is in it, and picks up the cage. Nobody says "you
burned her". The player says it. (`docs/cinematics/act3_outline.md`, C45.)""")
rep("""**The inner door and the coin.** The dead at the inner door take a toll: one
square coin of the Legion, stamped VII. Vonnra's grandmother's. It buys one
thing that cannot be bought twice: one Unchained back up into the light, alive
and unlit, an ordinary mortal.""",
    """**The inner door and the coin.** The dead at the inner door take a toll: one
square coin of the Legion, stamped VII. Vonnra's grandmother's. It buys one
thing that cannot be bought twice: one Unchained back up into the light, alive
and unlit, an ordinary mortal. (It was her grandmother's own way home, and
never spent; giving it away is giving her grandmother away.)""")
rep("""- **A. Re-forge the chain** (Vonnra's way). An Unchained lies down in the chain
  as the new link, forever. The valley keeps its lamps and its ember.""",
    """- **A. Re-forge the chain** (Vonnra's way). An Unchained lies down in the chain
  as the new link, forever. The valley keeps its lamps and its ember, and goes
  on burning its dead for light, knowing it: the "good" ending is the most
  compromised one.""")
rep("""  ages at last), to Edric, or to the second Unchained. A world without its
  light, and without its cage.""",
    """  ages at last), to Edric, or to the second Unchained. A world without its
  light, and without its cage: the dead are let go, two thousand years of
  them, the survivor's mother among them, and the survivor has her face back
  for exactly as long as it takes. Rook lights a tallow candle.""")
rep("""  up themselves, the first Unchained who stays lit by day. A new god in the
  valley, and a new thing to fear. Keegan kneels or dies trying; Grimtunnel
  worships; Snib survives.""",
    """  up themselves, the first Unchained who stays lit by day. A new god in the
  valley, made of the valley's dead, with two thousand years of names in them
  and their own somewhere among them. Keegan kneels or dies trying; Grimtunnel
  worships, and is right; Snib survives.

**The ending decides the nights.** After A the ember scars still open, and the
player knows what they are. After B there is no more ember, and the scars never
open again: the last thing the mercy ending costs is the power the player used
all game. After C they open, and the survivor is the boss in every one.""")
rep("""**The epilogue.** A page per person and place, worked out from the world, the
way `Chapter.cs` writes Act 1's: who lived, who rules the gate, what the
Penhale farm became, who keeps the Last Lamp lit.""",
    """**The epilogue.** A page per person and place, worked out from the world, the
way `Chapter.cs` writes Act 1's: who lived, who rules the gate, what the
Penhale farm became, who keeps the Last Lamp lit. It ends on the Last Lamp: in
A Rook lights it, and the survivor (if alive) hears a name in it; in B, a
tallow candle; in C it lights itself.""")

# ------------------------------------------------------------------ Romance
rep("""- **Keegan** (teased, not opened). `keegan.dinner`: chapter eleven,
  fraternisation, read four times. An Act 2 route, and a tragedy if it is
  followed: chapter four is about you.
- **Act 2 routes:** Rav (wry, drunk, grieving his brother; if he takes the hat,
  the route goes with him to the Roost); Ysolde (after Edric, if he is freed;
  never while she is selling you).""",
    """- **Keegan** (teased, not opened). `keegan.dinner`: chapter eleven,
  fraternisation, read four times. An Act 2 route, and a tragedy if it is
  followed: chapter four is about you.
- **Act 2 routes:** Rav (wry, drunk, grieving his brother; if he takes the hat,
  the route goes with him to the Roost); Ysolde (after Edric, if he is freed;
  never while she is selling you).

**The romance drafts** (`docs/romance/`) are adopted, with the fixes in
round three of the cinematics edit: the Act 1 beats of Sella (the stairs and
their last place to stop, the paid night of sleep, the bolt, the free night's
trust gate), Maeca (the walk, watch-only, the refusal with wolf blood on you,
her feet, her question, the heart counted at dawn), Keegan (the supper on the
wall) and Rav (the back room; "came back") are in the data; the Act 2 and 3
beats, all five routes, Ysolde's only in Act 2, are for the Act 2 writer.
What every lover notices is **the body's hours** (section 1): cold as the river
all night, warm by breakfast; the heart a bear's in January by night and a
hare's at dawn. Sella says it first ("Rook's got a word for that. It's not a
nice word."); nobody names it before Act 2. What the survivor tells Sella of
their past reaches Vonnra only while Sella is still selling them
(`sella.past_sold`, set before the free night); the fortune reads that, not
`sella.heard_past`. Rav's "never says no to a drink" is spent once, at his
morning after (`rav.sober`). Love scenes are not cinematics: each cut-away
holds one object instead (Sella's bolt going home; Maeca's boots side by side
outside the hides; Keegan's armour laid out in order; two cups at Rav's, one
full; Ysolde's spectacles folded on the twelfth drawing).""")
rep("""| 3 | `sella.free_night` | Sella and the survivor, the blue room, not for money for the first time; slower and less sure than her working nights, the patter dropping away; a door she bolts herself. |""",
    """| 3 | `sella.free_night` | Sella and the survivor, the blue room, not for money for the first time; slower and less sure than her working nights, the patter dropping away; a door she bolts herself. |
| 4 | `keegan.night` (Act 2) | Keegan and the survivor, a roadside chapel on the north road, the armour coming off a buckle at a time. |
| 5 | `rav.night` (Act 2) | Rav and the survivor, the back room of the Crooked Flagon after closing; funny until his fingers find the survivor's wrist. |
| 6 | `wayfinder.night` (Act 2) | Ysolde and the survivor, her rooms over the map table; she draws them after. |""")
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
