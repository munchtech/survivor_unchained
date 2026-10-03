# Ideas to make it extraordinary

A menu, not a plan. Each idea says what it is, why it would work (the
craft principle, by `CRAFT_STUDY.md` section), what it needs, and its
**cost**:

| Mark | Cost | Means |
|---|---|---|
| **[Data]** | cheapest | Text only, in `godot/data/content/` or a string in a zone script; uses existing conditions. |
| **[Hook]** | small | A small code change in an existing system: a new condition, a field on `ArenaSpec`, a line fired at an existing event. |
| **[System]** | medium | A new mechanic or UI, or a change to how an existing one works. |
| **[Content]** | large | A new scene, arena, area or act beat, with its art and tests. |

The ideas are grouped: the nights (I-1 to I-8), the people (I-9 to
I-16), the world and its lore (I-17 to I-26), set pieces (I-27 to
I-32), and the big structural turns (I-33 to I-36). The two largest
ideas have their own files: `THE_EMBER_REVEAL.md` (what the ember is)
and `REALNESS_AND_EXTREMES.md` (the human underneath, and the heinous
turns). The top picks are marked ★.

---

## The nights: making the arenas carry story

The night arenas are where most of the play happens and where the story
is now absent (`EDITORIAL_LETTER.md` problem 1). These ideas run from a
string to a system.

### ★ I-1. Say what an arena is. [Data]

Nothing in the game says what an arena *is*. The Wayfinder sells maps
of "places the road forgets"; the ember scars "pull you in"; story fights
happen "by night" in the Hollow, the Roost and the Dig. Players will ask,
and the fiction has the best possible answer: **the survivor is a light
in the dark, and everything that has lost a light comes to it.** The
ember scars are where the chain is thin and the Morrow's light burns up
through the ground; stepping in, the survivor drinks it, and the dark
comes. The horde thickens by the minute because the ember grows by the
minute: the brighter the survivor burns, the more come. The boss at the
half hour is whatever rules the place, coming to see what is so bright.

It needs one line of narration at the start of the first arena (and of
the first arena of each act), in the narrator's register:

> *"The ember rises in you, and out in the dark, everything that has lost a light turns towards it."*

and the scar hint rewritten (`LINE_NOTES.md` §3.5). It makes the
genre's core loop (more power, more enemies) into the story's logic
(§8.10, harmony). If `THE_EMBER_REVEAL.md` is taken, it becomes
literal: the dead are coming for their own light.

### ★ I-2. The arenas are how Vonnra fattens the link. [Data, then Content in Act 3]

The bible needs an answer to "why didn't Vonnra use Chid?"
(`NOTES_BY_ACT.md` §0.3). Answer: **an Unchained who never burns goes
dim, and the chain needs a bright one.** Chid has not taken ember in two
hundred years. The survivor gets brighter every night they fight.

Then follow it: **the Wayfinder's other buyer is Vonnra.** Ysolde sells
the names of those who come back to Sallow (bible); she sells their
*maps* to Vonnra, who pays for the arenas to be found and drawn, so the
survivor will keep going into them. Every night the player chooses to
fight, they are being prepared. On the reread (or on Vonnra's Act 3
confession) the whole night loop turns sinister: the game's core
mechanic was the antagonist's plan. This is *Inscryption*'s move (the
mechanic is the theme; §8.11) and BioShock's ("would you kindly", §3),
without taking the player's choice away: they could always have stayed
in by night.

Seeds: one line from Ysolde when asked who funds the table ("Someone in
violet ink pays for the drawing. Someone in silver pays for the names.
Between them I eat."); Vonnra's night bark "The dark is also a customer."
(already there, and perfect). Pays: Act 3.

### ★ I-3. A story arena for every route, not only the violent one. [Content]

In Act 1 the four story arenas are the violent routes (hunt the Pack,
raid the Roost, hold the Dig, open the vault). A merciful player plays
none of them. Give each thread a night on its peaceful route too, so
that the game's best fights reward the choices it wants to honour:

| Thread | Violent route (exists) | Merciful route (new) |
|---|---|---|
| The Beast Problem | The Hollow by Night (kill Greymuzzle) | **The Night the Slurry Stopped**: after the pump is moved or broken, the Dig boils up once in rage, and the survivor holds the stream's edge, with the Pack (if allied) or Maeca (if her respect is high) fighting beside them. Boss: Grimtunnel's lieutenant. Won: "The stream runs clear by morning. The Pack drinks from it while you watch." |
| The Missing Caravan | Raid on the Roost | **The Watch Comes to the Roost**: if Redcowl bargained, Holloway (or Pell's hired men, if Pell is not exposed) comes for the Kerchiefs by night, and the survivor holds the ravine for the people in red. Boss: Pell's captain. It makes the bargain cost something, and it is the seed of the Kerchiefs as Act 2's army. |
| The Sealed Vault | Behind the Sealed Door | (one is enough) |
| The Lamps | none | **The Ford, Relit**: see I-5. |

The rule: **every settled thread has a night**, and the night the player
gets depends on how they settled it. The arena is the thread's climax,
not a punishment for choosing violence.

### ★ I-4. Bosses who speak, and remember. [Hook + Data]

A story arena's boss is the face of a thread, and none of them says a
word. *Hades*' Meg remembers last night (§8.2). Add an `Intro`, a
`Taunt` (fired at half health) and a `Last` line to `ArenaSpec`, each a
small list gated by facts, shown as the barks the game already draws
(`Ev.Bark` with a `Speaker`):

**Greymuzzle** never speaks (`VOICES.md`): give his lines to the
narrator.
> Intro: *"He comes out of the rocks alone, as he did the first time. He knows you."* (if `greymuzzle_met`) / *"He comes out of the rocks alone. He has been waiting for you, or for someone like you."*
> Last: *"He lies down among his sick, and puts his head on the nearest of them, and does not get up."*

**Redcowl** (raid on the Roost):
> Intro: "Ha! At night. With the lamp-light behind you. That's how they took Ashford, you know. Ha. No, you don't know." (if `redcowl.ashford_said`: "...You know.")
> Taunt: "Forty-one mouths! You're killing them in their sleep for a merchant's box!"
> Last (if `be.crates` is `redcowl`): "Keep the crates from the hill. Promise me that. You owe me that." / (if `redcowl.birds`): "Tell the little bird... no. Don't tell him anything." / (default): "My mother'd laugh."

**Grimtunnel** roused (the Dig boils over):
> Intro: "SURFACE-MEAT! In HIS hill! With HIS heart's light in you!"
> Last: "...He'll keep me. He keeps everyone. You'll see. You'll SEE."

**The Legion's dead** (behind the sealed door): no boss line; one
narrated line when the champion falls, *"The rest of them step back onto
the stair, all together, and stand. They are not beaten. They are
letting you go."*

Cost: a few fields and fifteen or twenty lines. It is the single
cheapest way to put the story into the nights.

### ★ I-5. Act 1's last night: the Ford, Relit. [Content]

Act 1 ends with a conversation (the fortune). Every big beat is a night;
the act's last beat should be one. After the fortune, at dusk, the
narrator: *"From the south road, a long way off: a blue light where the
ford is."* Someone has hung a lamp on the Low Ford again. The survivor
goes back to the place they woke, at night, with the ember in them, and
fights the drowned at the water, and finds the lamp lit with ember in a
new iron, Brannoc's mark under the socket, and a square coin left on the
stone beside it (Vonnra's, or a clerk's in violet; she is testing
whether they will come). Boss: whatever rises from the water (a second
Warden half woken, or the drowned carters risen together, Wat at their
head, his grey mare's harness still on him).

It closes Act 1 where the game began; it turns the Lamps mystery from
entries into a fight; it opens Act 2's Kiln Ford thread (the last two
irons); and, if Brannoc was told the truth, he is there at the edge of
the light with his hammer, which is the first time the player sees him
outside the forge.

### I-6. The war at the gate carries every voice. [Content]

Act 2's climax (bible beat 12) should be the arena with the most people
in it. Allied NPCs present by Act 1 and 2 facts fight as allies and
bark by name: Holloway counts ("Nine. Eight. Hold, damn you."); Maeca
says nothing and the narrator says where she is; Keegan cites chapter
and verse; Redcowl laughs; Rav swears; Brannoc hammers. When one falls,
a toast says so, once, plainly ("Holloway is down."). Their survival is
the arena's real score: the epilogue reads it.

### ★ I-7. Every story arena ends with a dawn. [Data, with a Hook]

Replace "The story goes on." with a line per arena per outcome, in the
morning-report register (the game's best prose; `LINE_NOTES.md` §3.4 and
§8 have drafts). Two strings on `ArenaSpec` (`DawnWon`, `DawnLost`), and
`ArenaResult` reads them. Then make the next morning's report pick up
the night (a rule per story arena) so the town has heard.

### ★ I-8. The Wayfinder's margins: a voice across runs. [Data, then Hook]

*Hades* gives the run loop a character who comments on how you died
(§8.2). The Wayfinder already writes the survivor down in her margins
(`wayfinder.margin`). Make her the arenas' Hypnos: a pool of short
lines at her table, gated by arena facts (`arena.won`, `arena.best`,
deaths in arenas, the longest run, the last people faced, a story arena
won or lost), one per visit, priority-ordered, never repeated until the
pool is spent (§8.3, §8.4):

> "Eleven minutes at the Scar in the Ruts. I've written 'eleven' and then crossed it out and written 'brave'. Don't make me cross that out."
> "You lasted past the half hour and *stayed*. I've a margin for people who stay. It's short."
> "That's the third time the lamp-people have had you. I'm starting to think you like them."
> (after the first story arena lost) "Lost the Hollow. You'll go back. They always go back. ...I'll draw it again."

And the margin she writes the survivor into grows: visible at her table,
in her hand, run by run, as a journal page the player can read (*"Nobody,
of the Low Ford. Comes back more often than most."*). In Act 2 the same
page is in Sallow's ledger. The player has watched it being written.

---

## The people

### ★ I-9. Chid at the fire. [Data, then Content in Act 3]

The bible says the survivor "was carried back to the south bank" and does
not say by whom. Rook's first line says "Chid came in babbling about blue
lights going out at the crossing". Chid was there. He pulled the survivor
out, built the fire, sat with the body until it began to breathe, and
left before they woke. In Act 3 ("Who built the fire?") he says so. If
`REALNESS_AND_EXTREMES.md` §2.2 is taken, he was there every night, and
that is the heinous version.

Seed now, cheaply: the prologue's fire was built by someone who knew how
(a ring of river stones, the kind the Order used); a folk line ("Chid's
cloak was wet to the shoulder the morning the traveller came up the
road. He said he'd fallen in the trough."); and the death line (I-10).

### I-10. Chid's carter wears thin. [Data]

Every death: "A carter found you on the Old Road." Let it change with
the number of deaths until the player can ask "Which carter, Chid?" and
he cannot say (drafts in `LINE_NOTES.md` §4.1). It is the repeated line
that changes, the oldest trick in run-based writing (§8.2, §9.4), and it
is a fair clue to I-9.

### ★ I-11. The survivor's person. [Data, then System]

Each background names one person the survivor was going to or coming
from on the night of the ford (the hunter's mother on a farm in the
Verge; the scholar's correspondent at the Low Cloister; the outcast's
creditor; the devout's abbot). One line in `archetypes.json`, nameable at
creation. This person's face is the one that "is not quite where you
left it" at dawn. In Act 1 the survivor can ask after them (Rook knows
of the farm; the Wayfinder has drawn the Cloister road). In Act 2 the
memory mechanic takes them piece by piece. In Act 3 the survivor hears
them (`THE_EMBER_REVEAL.md` §7). It gives the protagonist a want the
player feels through play (`NOTES_BY_ACT.md` §0.4).

### I-12. Sallow writes first. [Data]

Act 2's antagonist should reach the survivor before Silverstair. A
letter under the door, in silver ink, in Act 1's last days or Act 2's
first: courteous, unhurried, an offer.

> *"I have the honour of a page about you, in a hand I trust. It says you come back more often than most. I should very much like to meet someone who comes back. I keep a warm house, and a fair account, and I have never yet failed to pay what I owe. Should the north road open to you, you will find me at Silverstair, and you will find that I have already written your name down. — O. S."*

If the Wayfinder wrote them as Nobody, the letter is addressed "To
Nobody, of the Low Ford", which is funny, and then not. Menace through
courtesy (§2.5); the villain seen first in his own hand.

### I-13. Keegan wins the argument. [Content, Act 2]

At the gate, before any duel, Keegan states the Vigil's case, and states
it better than the survivor can answer it: every Unchained is a link
coming loose; the valley's ground opens a little more for every one that
walks; the Vigil's work was a mercy; she has done it before
(`REALNESS_AND_EXTREMES.md` §2.6). Then she chooses. A villain (or here,
an antagonist friend) who argues the theme better than the hero is what
makes the climax answer an argument rather than a health bar (§12.8).

### I-14. Brannoc walks out of the forge once. [Data]

Brannoc never leaves the forge in Act 1 except in a morning report (the
burial). Give the player one sight of him elsewhere: at the Quiet Garden
at dusk, after Nell is buried, standing by the iron marker with his
hammer in his hand, not using it. The narrator: *"He doesn't look round.
He knows the sound of your boots by now."* One interactable, one line.

### I-15. The town notices: barks for every settled thread. [Data]

See `LINE_NOTES.md` §10: at least one day and one night bark per person
per settled thread that touches them. The data exists. It is the
cheapest reactivity in the game (§9), and the one players feel most
(Kasavin's "haircut", §8.2).

### I-16. Rook keeps a book too. [Data]

Everyone in the valley counts. Rook counts beds. Give her a slate behind
the bar with the names of everyone staying, chalked, and let the player
read it: the survivor's name on it on the first night (or "the one off
the ford"); Jory's name in the good room; and one name, at the top,
never rubbed out, in an older hand: *Ashe*. Then, if Nell is buried,
Rook chalks *Nell* under it, and says nothing about it. A ledger of the
dead in a kitchen.

---

## The world and its lore

### ★ I-17. Item lore for everything the player starts with. [Data]

The starting weapons and armour have no lore, and ember itself is never
described as what it is. Drafts are in `LINE_NOTES.md` §6. The rule:
two to five sentences, one concrete detail that ties the object to the
valley, one hint never resolved in the same item (§7.2). Cost: perhaps
forty lines.

### I-18. One story told across a set. [Data]

FromSoftware's armour sets carry a character's arc (§7.3). The Ashford
garrison is the natural set: the Ashford-pattern crossbow (stamped with
the spring of the Fall), a garrison buckler, a pair of boots that
never fit anyone (found in the Watch's store, unused: see
`REALNESS_AND_EXTREMES.md` §2.4), and the garrison's roll, found in a
cave mouth in Act 2, with Maeca's name and a line through every other.
Collecting them is reading the boots thread before Act 2 says it.

### I-19. Kell's lamp. [Data]

The babbling lampling: "Kell went down to see. Kell's lamp came back up
on its own, still lit." Make it findable at the sinkhole by night: a
head-lamp on a snapped strap, still lit, that will not go out. Lore:
*"Kell's. It came back up without him. It has not gone out, and it is
warmer than it should be, and when you hold it to your ear you think
you hear somebody counting."* A FromSoftware item waiting to be picked
up (§7.1).

### I-20. The Legion's own voice. [Data]

The Seventh Legion appears only in one inscription. Give it a second
voice, deniably: a Legion bronze found in the vault's first landing,
stamped VII, with a few words in old-empire script that a scholar can
read: *"WE STAND THE DOOR. WE ARE PAID IN NOTHING. WE ARE NOT
RELIEVED."* (It sets up the coin as their only wage, and the dead
standing on the stair as soldiers still on watch.)

### I-21. The Order's two creeds. [Data]

Keep both versions of the Order's motto (`LINE_NOTES.md` §5, Chid) and
make the second one findable, carved on the underside of the shrine's
lamp-bracket where only someone mending it would see: *"THE DARK IS ONLY
LIGHT THAT HAS NOT YET BEEN FOUND."* The Order knew where its light came
from. Chid "never liked that one".

### ★ I-22. "Gone to the Morrow." [Data]

The valley's idiom for dying is the god's name, and nobody notices,
because who listens to an idiom. A handful of folk lines and one from
Rook, Wenna refusing to say it, Keegan noticing "Ash-of-Morrow" is "a
peculiar surname; a kenning, almost". The clue in the most visible place
there is (§3.15). Needed for `THE_EMBER_REVEAL.md`; useful without it.

### I-23. A colour sheet, and a glossary. [Data, documentation]

Violet is the Toll Tower's; silver is the Vigil's; red is Ashford's;
cold blue is ember at the ford. Nothing else in the valley may wear
them. And a glossary of every proper noun (the Karrash, the Collegium,
the Glass-sworn, Saint Wend's, Low Kiln, the Low Cloister), with what
is known and what must never be said. A copy-editor's style sheet for a
world (§13).

### I-24. The square coins in circulation. [Data]

The binders' square coin appears at Vonnra's throat and on Brannoc's
anvil. Let the player find one more, somewhere it should not be: in a
dead carter's purse in the ditch in the prologue; in Jessop's (Act 3).
Each is the same coin, stamped VII. By Act 3 the player knows a square
coin on a body means Vonnra paid for that death.

### I-25. The Watch's charter. [Content, Act 2]

The bible says the Watch's charter is "lost, or burned". Find it, in Act
2, in Holloway's strongbox or the Quiet Garden trunk: three articles in
an old hand. *Keep the ford lamps in oil. Keep the black door shut. Put
down the dead who rise, and do not ask them their names.* Holloway reads
it and goes quiet. The third article is the survivor.

### I-26. The nemesis is one of the drowned. [Hook]

The nemesis system ("...Who Took Your Light") names what killed you. If
the survivor dies to the drowned in the Low Ford ditch or the Verge, let
the nemesis be one of the carters, named by the town: *"Wat, Who Took
Your Light"*, with his grey mare's harness. Then killing him is putting
down Wat, and Brannoc, if told, can be told this too. (It also fixes the
"Red Wat" collision in `LINE_NOTES.md` §4.2 by giving the name its
proper owner.)

---

## Set pieces

### ★ I-27. The first night again, from the other side. [Content, Act 3]

In Act 3, Chid tells how he found the survivor (I-9), and the game plays
it: a short, ember-less sequence in which the player controls Chid,
wading into the ford at dusk with the lamps lit blue, finding the body,
dragging it to the bank, building the fire with river stones, and
sitting with it until it breathes. The player knows exactly whose body
it is. Then the camera holds on the fire as it burns low, and the
prologue's first line plays over it: *"The fire has burned low."* The
game's first scene, recontextualised by the player's own hands. (*The
Green Knight*'s vision; *Arcane*'s "we saw Vi come back"; §12.)

### I-28. The fortune, interrupted. [Data]

`NOTES_BY_ACT.md` §2.8: the fortune is a recap. At its last page,
before "Close the book", the cups rattle (rule 41 already exists), the
lamp gutters, and Vonnra stops in the middle of a word and looks
north-east at the hill. *"(She does not finish the sentence. In
forty years nobody has seen her not finish a sentence.)"* A turn of its
own, for one line.

### I-29. Brannoc's burial, played. [Content]

The burial is a morning report (rule 31), and it is one of the best
things in the game. Consider letting the player be there: the Quiet
Garden at first light, Chid singing badly, Brannoc with the iron marker,
half the town come uninvited, Rook at the back. No choices. The player
can stand, or leave. Brannoc does not look at them, unless they stay to
the end, when he nods once.

### I-30. The heart burns names. [System, Act 3]

The bible: carried without Brannoc's cage, the heart burns whoever
carries it, and an Unchained can bear it "at the price of names". Make
it literal in the interface: while the heart is carried, names in the
journal and the people page blur, one by one, from the least known to
the most, and do not come back. The player watches their own record of
the game unwrite itself. The survivor's person (I-11) goes last.
(Bloodborne's insight in reverse: knowledge as the cost, §7.5.)

### I-31. Dawn release. [Data]

Every dawn the ember drains "back into the ground". After the ember
reveal, the dawn after a night of heavy burning gets one line, at most
once an act: *"The light goes out of you at sunrise and down into the
grass, and for a moment the whole hillside is lit from underneath, the
way a face is lit by a lamp held below it. Then it is morning."*

### I-32. The last lamp. [Content, epilogue]

The epilogue (one page per person and place, bible §8) ends on the Last
Lamp. In A, Rook lights it, and the survivor (if alive) hears a name in
it. In B, she lights a tallow candle. In C, it lights itself. One image,
three endings.

---

## The big structural turns

### ★ I-33. Act 2 in six nights. [Content, structure]

`NOTES_BY_ACT.md` §3.1: cut the twelve beats to six, each a night arena
with a speaking boss and day scenes before and after: the breakthrough;
the boots (with Holloway's letter); the second crossing (with Sella and
Jory); chapter four (with "what you are"); Silverstair (with the army);
the war at the gate. The consequence ledger survives whole; the act gets
a shape the player can feel, and a scope the team can build.

### ★ I-34. The ending decides whether the arenas still exist. [Hook]

After the last night, the arenas' "endless play" continues. Let the
ending decide: after B (the chain broken, no ember) the scars never open
again, and the survivor (if alive, with the coin) is an ordinary person
in a dark valley; after A, they open, and the player knows what they
are; after C, they open and the survivor is the boss in every one, and
the hordes are the valley's own people coming for their light. The
story's last choice decides whether its best mechanic still exists
(§8.10, the strongest possible harmony).

### I-35. Pell's numbers as Act 2's clock. [Hook]

Pell knows which night the chain gives (bible beat 6). Make it a visible
clock in the journal ("Pell says the ground goes on the twentieth
night"), recalculated by what the player does (pump, crates, the second
crossing). Act 2 gets *Pentiment*'s days (§4.7): you cannot do
everything; what you do is who you are.

### I-36. A memory mechanic that begins in Act 1, gently. [System]

The bible plans that after Act 2's turn "the night's ember can be made to
cost a memory the player chooses". Begin it in Act 1, invisibly: after
each night the survivor burns past a threshold, the dawn line has one
small wrongness (a word for something they should know that does not
come; the colour of a door at home). Never mechanical, never explained.
When Act 2 makes the cost explicit, the player realises it has been
happening all along. (Planted as a sensation before it is a rule: §3.10.)

---

## If I could only do five

1. **I-4, bosses who speak** [Hook + Data]: the nights get faces this week.
2. **I-7, every story arena ends with a dawn** [Data]: the nights get endings.
3. **I-1 and I-2, what an arena is, and who profits** [Data]: the night
   loop becomes the plot.
4. **I-11, the survivor's person** [Data, then System]: the protagonist
   gets a want.
5. **`LINE_NOTES.md` note 1, oil and ember** [Data]: the Act 1 mystery's
   logic holds.

And the one large thing worth the cost: **I-3, a night for every
route**, so that the game's best fights reward the choices it most wants
to honour.
