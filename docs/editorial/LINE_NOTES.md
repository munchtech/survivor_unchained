# Line notes

Notes on the game's actual words: the prologue's narration, the dialogue,
the journal, item lore, the morning reports, the townsfolk, the notice
board and the barks. Each note quotes the line, says what is wrong or right
and why (the principle, and where useful the example from
`CRAFT_STUDY.md`), and offers one or more alternatives in the established
voice (`docs/VOICES.md`).

How to read them:

- **Fix.** Something is broken: a contradiction, a broken rule, a line that
  works against the story.
- **Tighten.** The line works, and could work harder.
- **Keep.** The line is right, and the reason it is right is worth knowing,
  so that nobody "improves" it later. These are as important as the fixes.

Alternatives are offers, not orders. Where there are several, the first is
the one I would take. Node references follow the house style
(`conversation.node` in `godot/data/content/dialogue.json` unless a file is
named).

A general verdict first, so the notes below are read in proportion: **the
line-level writing is already the strongest thing about this game.** The
voices are distinct enough that most lines could be attributed with the
names stripped off. The narrator mostly keeps its own rules. The morning
reports are as good as anything in the genre. Most of what follows is
small. The one thing here that is not small is note 1.

---

## 1. The keystone: what the lamps do (Fix, and the most important note in this file)

The Act 1 mystery is "who lit the lamps at the Low Ford?". Its logic has to
hold, because a player who works it out is reasoning from it. At the
moment the text says three incompatible things about the lamps:

| Where | Says |
|---|---|
| `keegan.warden` | "The lamps were never to keep the dark out. They were to keep the Warden asleep. If somebody lit them again, somebody wanted it awake." |
| `Prologue.cs`, the watchman's `learn` text | "The lamps at the ford feed the Warden." |
| `Prologue.cs`, the boss hint | "While the three lamps burn, the Warden shrugs off most of every blow." |
| `STORY_BIBLE.md` §1 | "The Watch burned it in the ford lamps to keep the Wardens asleep" and Vonnra "relit the lamps to wake the Warden". |

Keegan's line is a non sequitur as written: if lit lamps keep the Warden
asleep, relighting them puts it back to sleep. The prologue, meanwhile,
teaches the player with their own hands that lit lamps make the Warden
stronger. A careful player (the one this mystery is written for) will
notice, and will conclude either that the writers did not notice or that
Keegan is lying. Neither is wanted.

**The fix that costs least and pays most:** let there be two kinds of
light. The Order's lamps burned **ember**, and ember feeds a Warden (it is
the Morrow's own light, and the Wardens were made to keep it). The Watch,
founded to keep the crossings quiet, took the ember out and burned **oil**:
light enough for travellers, nothing for the Warden to drink, so it slept.
Then the Watch ran out of oil (Holloway: "We've not had oil for those lamps
since my first winter"), the ford went dark, and last winter somebody hung
twelve new irons there, the kind made to hold ember, and lit them with it.
That woke the Warden.

This one distinction repairs every line above, explains why Vonnra needed
*new irons* at all (an oil lamp will not hold ember; Brannoc's irons are
cages, and the Warden's lamp-iron is described as "the iron cage of the
lamp"), turns Holloway's oil line into a clue, and makes the boss mechanic
(break the lamps and it weakens) the story's own logic.

Alternatives for `keegan.warden`:

> "...Who told you that? The Watch kept those lamps after the Vigil, and the Vigil after the Order. They burned oil in them. Only oil. Light enough to cross by, and nothing in it for the Warden to drink. If somebody hung ember in them again, somebody wanted it awake. Do not repeat that. I am probationary."

> "...Who told you that? Oil. The lamps at the ford were to burn oil, and nothing else; it is in the handbook, with a drawing. Oil keeps it sleeping. Ember wakes it. If somebody lit them with ember, somebody wanted it awake. Do not repeat that. I am probationary."

And the prologue's `learn` text, which is what the journal remembers:

> "The lamps at the ford burn ember, and the Warden drinks it."

Then the dead watchman's third line can carry it in his own words:

> "Lamps at the Low Ford lit again, and not by us. Not oil. It is the wrong colour."

(The ember lamps would burn the cold blue the prologue already shows, so
"the wrong colour" is a clue the player can see as well as read.) The
bible §1 needs the same change; that is for the author.

---

## 2. The prologue (`godot/logic/Play/Zones/Prologue.cs`)

**2.1 The first line of the game. (Tighten.)**

> "The fire has burned low. Out in the dark, the ground is moving."

It is good, and it is wasted. The game's central secret is that the
survivor drowned at the ford at dusk and was carried back to this fire.
The first line is the most reread line in any story; in a twist-built
story it is the first place a returning player looks. (*The Sixth Sense*
plants its whole reveal in the first scene. Gene Wolfe's Severian tells
you on the first page that he is writing from a throne, and you do not
notice.) One sensory fact, never explained, makes the reread pay:

> "You wake by a fire that has burned low. Your clothes are wet through, and you do not remember the rain. Out in the dark, the ground is moving."

> "The fire has burned low. Your boots are full of water. Out in the dark, the ground is moving."

> "The fire has burned low, and you are cold to the bone, colder than the night is. Out in the dark, the ground is moving."

(The first is best: it gives the player a question they do not know is a
question. The narrator's rule, "never what it means", is kept.)

**2.2 The watchman. (Keep, with one cut.)**

> "A Watchman, grey-bearded and a long time dead, sitting against the post as if he had only stopped for breath. Something has had his eyes. In his belt-book, three lines in a hand that worsens as it goes..."

Keep all of it. "Something has had his eyes" is one plain image, the
narrator's rule exactly. "A hand that worsens as it goes" does the work of
a paragraph. The three lines are a short story. See note 1 for the third.

> "...and for you alone, the dead man's jaw moves: 'It shatters its own lamps when it charges. Make it charge.'"

The devout perk is lovely: the dead speak a little to you. But the dead
man is reading out the boss mechanic in the second person, and `VOICES.md`
says nobody explains a mechanic. Let him say what he saw; the player will
do the rest:

> "...and for you alone, the dead man's jaw moves: 'It broke its own lamps, coming for me. Twice.'"

> "...'When it runs, it runs through its own light.'"

**2.3 The ambush, and Nell. (Keep.)**

> "A wagon on its side, and the ditch beside it full of the drowned. One of them is still holding the reins. They were waiting."
>
> "The last of them falls back into the ditch and stays there. The one with the reins was a girl, twelve at most: red hair under the weed, and new boots."

This is the best-built moment in Act 1. The player kills her as one of a
horde; the second line, after the fight, turns her into a person; Brannoc's
scene days later turns her into his daughter, and the player realises they
have been carrying her death since the first night. It is a three-stage
recognition (Aristotle's *anagnorisis*, done in a ditch). Do not add a word
to it. Do not let the second line fire if the player is killed and
retries; it should be said once.

Only the ambiguity of "They were waiting" is worth checking: waiting for
what? For the survivor (the dead know their own)? For the night? For
nothing? If it is meant to be "they were waiting for you", the line is
doing secret work, and it is good. If it means "they ambushed you", it is
a little flat; "They are still waiting for someone to cross." would be a
better plant.

**2.4 The Warden's two barks. (Tighten.)**

> "NONE CROSS AFTER DARK." / "RISE, YOU WHO DROWNED HERE."

Both are right for a guardian made to say one thing. But the Warden is the
only creature in the game that has *met the survivor before*: it drowned
them a few hours ago. One line from it on recognising them would be the
fairest clue in the game and the most chilling thing on a second playing:

> On first sight: "NONE CROSS AFTER DARK." On the survivor's approach to the water: "AGAIN?"

> Or, at the break: "YOU CROSSED. YOU CROSSED, AND YOU ARE STILL CROSSING."

The first is better: one word, ambiguous at the time (again, another
traveller?), unmistakable afterwards.

**2.5 Grimtunnel at the ford. (Fix: the believer has no seed.)**

> "Oho! A Warden's heart, still warm! Nobody's, is it? Nobody's!"
> "Finders keepers, surface-meat. The Deep Dig thanks you!"

`STORY_BIBLE.md` makes Grimtunnel a believer carrying a god its heart.
Nothing he says in Act 1 suggests faith. It suggests a magpie. When Act 3
reveals the believer, it will feel like a retcon, because there is nothing
to recognise. (Recognition needs a prior image. Martin's Red Wedding works
because the guest-right and the Frey grudge were put on the table early.)
Keep the comedy and slip one capital letter into it:

> "Oho! A Warden's heart, still warm! Nobody's, is it? Nobody's! ...No. No, not nobody's. HIS."
> "Finders keepers, surface-meat. Down it goes. Down to Him!"

and on his spare lamp's lore (see §6) a line of devotion scratched on the
casing.

**2.6 The dawn. (Keep.)**

> "You try to call up your mother's face, and find it is not quite where you left it."

The best single line in the game, and the most important plant. It does
three jobs: it says the ember costs something; it seeds the Act 2 reveal
(the names go first, then the faces); and it gives the survivor, who
otherwise has no personal stake in Act 1, the beginning of one. Keep it
exactly. See `EDITORIAL_LETTER.md` problem 2 for building on it.

**2.7 Dying in the prologue. (Keep.)**

> "The ember will not let you go so easily."

It is literally true, and the player will not know that until Act 2.
Exactly the kind of line a twist-built story needs.

**2.8 The tutorial voice in the narrator's mouth. (Tighten.)**

> "The dead are climbing out of the ground around your fire. Keep moving — your weapon strikes on its own."
> "Follow the road. The dead keep coming; let them come to your weapons, and keep your feet moving."

The first sentence is the narrator; the second is the interface. When the
two share a line the narrator's authority leaks (it starts sounding like a
manual). Split them: narration in the narrator's panel, instruction in the
hint panel the game already has (`SetHint`, `Tip`). And the em dash is
the only one in the narrator's lines; the house punctuation is the colon.

> Narrator: "The dead are climbing out of the ground around your fire." Hint: "Keep moving. Your weapon strikes on its own."

---

## 3. The Waystation and the Verge (zone scripts)

**3.1 The sinkhole. (Fix: the narrator is being cute.)**

> `Verge.cs`: "At the bottom of the pit lies something pale and segmented, bigger than a house, and — probably — dead."
> `quests.json` `below/sinkhole`: "...bigger than a house. Dead. Probably."

`VOICES.md`: the narrator is "never theatrical, never cute". "Probably",
in dashes, is a wink at the player, and it is the wink that lets the
player off the hook. The horror of the thing is that the narrator, who
never lies, cannot say. Let the narrator not say:

> "At the bottom of the pit lies something pale and segmented, bigger than a house. It does not move. You watch it long enough to be sure, and you are not."

> Journal: "At the bottom of the sinkhole: something pale, eyeless and segmented, bigger than a house. It does not move."

The second is better in the journal precisely because it does not say
"dead". Keegan also has "Something moved out there. Probably." (night
bark). One "probably" is a joke; two is a tic. Keep hers; she is the
comic one.

**3.2 The prayer. (Keep.)**

> "Under the silence you hear it, for as long as a held breath: slow, patient, enormous. Not breathing. Praying."

Perfect, and it is the game's thesis in four words. Keep it, and keep it
for the faith background only: it is better as something not everyone
hears.

**3.3 The vault. (Tighten.)**

> Door: "A door of black stone, smooth as glass, and a violet sigil you cannot read. It hums against your teeth."
> Fragment (`items.json`): "Black stone, cut in a shape that fits the sealed door. It hums against your teeth."

The image is good and it is used twice. Give it to the door; give the
fragment its own:

> "Black stone, cut in a shape that fits the sealed door. It is warmer than your hand, and it stays warmer."

> "The skull turns, very slightly, toward you. 'It was never locked from the outside.'"

Keep: the best line in the vault, and fair to the Act 3 truth.

**3.4 The story arenas' prompts. (Fix: the interface talks about "the story".)**

> Hint: "An ember arena: the story remembers how it goes"
> After a story arena (`src/Ui/ArenaResult.cs`): "The story goes on." / "The story goes on without the win. The Wayfinder will let you take this fight again."

These are the interface talking about the game as a story, and they arrive
at exactly the moments where the fiction should be strongest: before and
after the biggest fights in Act 1. "The story goes on" after killing
Greymuzzle in his own Hollow is the flattest line in the game. (Compare
*Hades*, where the return from every run, won or lost, is a written scene;
see `CRAFT_STUDY.md` §8.) The hint wants to say "this one counts":

> Hint: "After dark, the ember will take you in. What happens there will be remembered."
> Hint: "By night. Whatever happens in there stays happened."

And the result line wants to be a line about *this* fight. Per story
arena, won and lost (a data change: two strings each on `ArenaSpec`):

| Arena | Won | Lost |
|---|---|---|
| The Hollow by Night | "The Hollow is quiet. You stand in it until the sun comes up, because nothing else will." | "You come to on the Old Road at dawn with the Pack's smell on you. They let you live. That is the worse of it." |
| Raid on the Roost | "The red hat is in the mud. The cages are open, or burning. The ravine smells of both." | "The Kerchiefs drag you to the road and leave you on it. Redcowl wants it known that he could have done otherwise." |
| The Dig Boils Over | "Nothing more comes up. Below you, a long way down, something settles, like a sleeper turning back over." | "They go back down at first light, carrying their own, and the pump is still turning." |
| Behind the Sealed Door | "The dead walk you back up the stair and let you out. They did not do that for the last one." | "The dead walk you back up the stair and put you out, the way you would put out a cat." |

(The Sealed Door's won line is a fair, deniable clue to what the survivor
is: the dead let you out; the bootprints say Jessop never came out. See
`NOTES_BY_ACT.md`, Act 1, "the vault".)

**3.5 The ember scars' hint. (Tighten.)**

> "After dark the ember burns through the ground here and there, marked red on your map. Step into one and it pulls you in: an arena, until you win or fall."

Fine as a tip. One clause of fiction would answer a question every player
will have ("what *is* an arena?"); see `EDITORIAL_LETTER.md` problem 1 and
`IDEAS.md` I-1:

> "After dark the ember burns up through the ground here and there, marked red on your map, the way a wound shows through a bandage. Step into one and it takes you in, until you win or fall."

**3.6 The pump, the Roost, the cages. (Keep.)**

> "When the dust comes down, the hillside is a wound. Small shapes crawl out of it with their lamps still lit. Some of them are on fire. Most of them do not crawl far."
> "The fire takes the tents, and then the cages. There is screaming, and the smell, and hands through the bars; and then there is only the fire."
> "A woman who will not stop saying thank you."

This is what `VOICES.md` means by violence said in one plain line and not
dwelt on. The cost lands because the narrator refuses to linger. Keep all
three.

**3.7 The well. (A question.)**

> "The water is a long way down, and clean. Somebody has scratched 'M. + J.' into the stone."

Lovely, if it is a seed. Whose? Maeca and someone before Ashford? If it is
nobody's, it is still good texture; if it is somebody's, decide whose and
let one person in the game react to it once.

**3.8 The Quiet Garden note. (Keep.)**

> "Keep the lights lit. — C."

Keep. Five words, re-readable three ways by Act 3 (the Watch's lamps; the
chain's light; Chid himself).

---

## 4. Death and the nemesis (`godot/logic/Play/Journey.cs`, `chid.woke`)

**4.1 The carter. (Fix: the same white lie, forever.)**

> `chid.woke`: "A carter found you on the Old Road and brought you in..."

Every time the survivor dies, a carter found them on the Old Road. The
first time, it is fine. The third time, it is a lie the player can see,
and right now nobody notices it. This is the cheapest gift in the game: a
repeated line that *changes* is the essence of *Hades*' and *Darkest
Dungeon*'s writing (`CRAFT_STUDY.md` §8, §9). Let Chid's story wear thin
as deaths mount (fact: `Ch.Stats.Deaths`):

> First death: as now.
> Second: "A carter found you. The same carter, as it happens. He's starting to think you're doing it on purpose."
> Third: "A carter brought you in. (He isn't looking at you.) Well. Someone did. Somebody always does."
> Fourth and after, with the choice "Which carter, Chid?": "...You know, I didn't ask his name. I should ask his name. Sit down. Not there. There."

And in the Verge, with no carter anywhere near, it is worth a single folk
line: "No carts on the Old Road since the wolves. So who's been bringing
that one in?"

**4.2 The nemesis names. (Fix: two collisions.)**

> `NemesisName`: Kerchief: "Red Wat", ...; Undead: "the Drowned Watchman".

"Wat" is the drowned carter: the one name the town says with grief ("Wat
went. Wat's not back."). A Kerchief nemesis called Red Wat makes the
player wonder whether Wat became a bandit, and spends the name. "The
Drowned Watchman" points at Corran, who was not drowned and whose death
the story handles with care. Change both:

> Kerchief: "Red Hob", "Knuckles Marro", "Sly Dell". Undead: "the Unburied", "the Drowned Teamster" or "the Ditch-Walker".

**4.3 "Who Took Your Light". (Keep.)** The title is the best thing in the
nemesis system: it says ember is a light, and that losing it is personal.

**4.4 The trait. (Fix: the interface says the twist.)**

> `archetypes.json` `risen_once`: "You have died and come back. The dead are quieter around you: +10% resistance to shadow."

The story bible's first rule is that no one says an answer before its act.
The interface has just said Act 2's answer, flatly, in Act 1. (The player
can believe Chid's shrine brought them back; that is the misdirection the
game is built on, and this line removes it.) Let the trait describe what
happened, not what it means:

> "You fell, and got up again. The dead are quieter around you: +10% resistance to shadow."

> "Chid's shrine, or something, would not let you lie. The dead are quieter around you: +10% resistance to shadow."

---

## 5. Dialogue, person by person

### Mother Rook

**`rook.first`** (Keep.) "Chid came in babbling about blue lights going
out at the crossing, and here you are, bleeding on my step." This is a
superb plant, and possibly an unintended one. *Chid was watching the
ford that night.* Why? It should be answered in Act 3 (`IDEAS.md` I-9).
Do not cut it.

**`rook.ford2`** (Keep.) "Nothing. She paid me double. She's never paid
me double for anything." Three short sentences, the third the twist of
the knife. Rook's voice exactly.

**`rook.t_rook`** (Keep.) "It's a good chair; that's the only reason." The
voice rule ("kindness said sideways", "never cries") made into a line.

**`rook.c`** (Keep.) "never heard him called owt else": the one dialect
word, used where it matters. Note that it implies Rook knew Ashe in life,
which pins the Watch's founding inside living memory (see
`NOTES_BY_ACT.md`, "the timeline").

### Captain Holloway

**`holloway.defied`** (Tighten.)

> "Out of my sight. And if I see you near my gate with a blade out, you'll find out how the cells feel on a cold night, and how the cell-rats feel about fresh meat."

The rats are a writer's flourish; Holloway counts. His threats should be
inventory:

> "Out of my sight. Next time I see a blade out near my gate, it's the cells. There's one blanket down there, and I know who's got it."

**`holloway.liar`** (Keep.) "...why you shouldn't spend the night in the
fucking cells." `VOICES.md` says Holloway swears rarely and it lands. This
is the one place, and it lands. Do not add a second.

**Night bark** (Fix.)

> "Every night I bury somebody's son. Go home."

It is out of voice (Holloway never makes a speech, and this is a speech
in eight words) and out of fact: the Watch buries one man in Act 1, Aldo,
and only if the wolves come. A captain who counts would count:

> "Eleven on the roll. I say them over before I sleep. Go home."
> "Two on the walls. One on each gate. That's the lot. Go to bed."

**`holloway.post`** (Keep.) "(He says nothing for long enough that you
think he hasn't heard.)" and "an apology he can't hear". This is Holloway
at his best, and it pays Act 2 (he owes the survivor Corran).

### Maeca Barefoot

**`maeca.first`, default** (Fix: she breaks her own rule on meeting you.)

> "...Maeca Barefoot, of the Ashford garrison. What's left of it."

`VOICES.md`: Maeca "never talks about Ashford except in three words or
fewer". Here she volunteers it to a stranger, before the boots, before
Redcowl's refusal to hear it, before Holloway's silence. It spends the
word the whole thread is built to make heavy. Her nameplate already says
"Last of the Ashford Garrison" (`npcs.json`); let the plate say it, and
her mouth not:

> "Another blade for Holloway's bounty? The wolves aren't the problem. They're what the problem looks like from the road. Maeca. Barefoot, before you ask."

(and consider changing the nameplate title to "Hunter, of the Verge", so
that the word Ashford is first *earned* in conversation).

**`maeca.barefoot`** (Keep.) "Boots were signed for. They never came. You
learn to hear the ground through your feet. I prefer it now." The best
backstory in four sentences in the game. The last sentence is the scar
turned into pride; nobody pities her, least of all her.

**`maeca.blind_morning`** (Keep.) "That's why. That's all of why. Don't
make it a story." The character telling the writer not to milk it: right.

### Old Wenna

**`wenna.fever`** (Keep.) "Same smell as your bottle, child. Same smell
exactly. ...I've roots on the boil." The change of subject is the voice
rule ("never names the fever year's dead") in action.

**`wenna.t_wenna`** (Keep.) The husband lost at cards is the right size of
joke for a woman who will, later, nurse people dying in green air.

### Tam

**`tam.tock`** (Keep.) The whole line is the voice sheet made flesh: run-on
"and"s, "Pa says", the exact thing in order, the wrong word for the
important part ("knocks", "like somebody wanting to come in"). It is also
the best monster-under-the-floor line in the game. Do not let anyone
tidy the grammar.

**`tam.cb_grey2`** (Keep.) "Pa says you have to, sometimes. Pa says a lot
of things." A nine-year-old's moral judgement in eleven words.

### Brannoc

**`brannoc.nell` and its branches** (Keep, nearly every word.)

The scene is the emotional summit of Act 1 and it is built on the voice's
one rule: the hammer. "(The hammer stops.)" is louder than any line of
dialogue in the game, which is exactly what `VOICES.md` promised. The
choices are well judged: the truth is two steps ("A girl had the reins",
then *how*), so the player has to choose to say the worse thing. "It was
quick" can be a lie, and the game does not tell the player whether it
was, which is right. Two small things:

- Brannoc's opening question runs to ten fragments, against a voice of
  "two sentences at the most". It is the one scene where the rule should
  bend, and it does bend; but trim one fragment so the bending is visible
  rather than habitual. "Going to her aunt at Low Kiln." can go: the
  aunt is said again in `nell_lie` ("Aunt'll feed her up"), where it
  hurts more.
- `nell_lie`: "Low Kiln, then. Good. (And again.) Aunt'll feed her up.
  She's thin." Keep. A lie that makes him happy is the cruellest outcome
  in Act 1, and the game lets the player sit in it without comment.

**`brannoc.mark`** (Keep.) "Keep it. It's done what it was for." He forged
the cage of the lamp that drowned his daughter, and he does not know it
yet. On the reread, the line is unbearable. That is the definition of a
fair twist: the second reading is a different line.

**Barks** (Tighten.) "Hit a man with this and he stays hit." and "Mind the
sparks." are small talk, and the voice sheet says Brannoc never makes
small talk. Every bark should be iron:

> "Two on the rack. Leave them." (keep; it is a seed)
> "Iron's cold. Come back when it isn't."
> "Steel or fur."

and after Nell is buried, the day barks should go (he says nothing at
all) and the night bark become: "Forge is lit. Don't come in."

### Harlan Coyle

**`harlan.first`, the day-counting variants** (Keep the idea; trim the
text.) "Four days. He's never four days late." then five, then six: the
patter repeating with a different number each day is excellent, and the
apology ("Forgive me. I say that to everyone.") is the crack in it. But
four near-identical 300-character greetings are heavy on screen. Cut the
middle clause in all but the first:

> Day 2+: "Harlan Coyle. You'll have seen my notice. Three wagons, and a boy called Jory. Five days. He's never five days late. ...Forgive me. I say that to everyone."

**`harlan.knew`** (Keep.) "He didn't know. ...He didn't know. I did." The
crack in the patter opening all the way, once.

**`harlan.be_dig`** (Keep.) "I don't ask the salt what it's for, friend."
The line the whole Coyle thread is built on.

### Pell Varrow

**`pell.t_pell`** (Keep.) "(He straightens a pen that was straight.)" The
best stage direction in the game. And the sister's "dreadful sense of
humour" gives a dead woman a personality in four words.

**`pell.why`** (Keep.) "I'm not a good man. I'm a careful one." This is
the line that makes Pell a villain who believes he is right. It is earned,
because the player has just learned he paid to keep blasting ember out of
the Dig's hands.

**`pell.say_woman`** (Tighten, or cut.)

> "I find women drive the harder bargain. I've a theory it's because you're used to being underpaid. Do prove me right; it's so rare that I am wrong."

As Pell's condescension it is in character, but it reads like the writer
winking at the player over Pell's head, and it is the least specific of
his lines. Pell notices *money*. Give him something only Pell would see:

> "You've mended that strap yourself. Twice. I do like a woman who knows what a new one costs."

### Rav Cutwell

**`rav.first`, "Doctor McBreathless"** (Cut.) It is the only whimsical
proper noun in the game (it comes from the beta design table), it is
unexplained, and it pulls toward Pratchett. Rav's cant is gravel, not
whimsy. If the Watch must have a name for him, make it a Watch name:
"Doctor Cutwell, if you're bleeding. Cutthroat, if you're the Watch."

**`rav.cb_killed_redcowl`** (Keep.) "Dunstan. That was his name, before
the hat. Our mother's idea; he hated it." The one exception to his rule,
spent where it is the scene. Keep the rule sacred so that this stays the
only time.

**`rav.t_rav`** (Keep.) "the man who sharpened his teeth for a joke and
then couldn't stop" is a whole Kerchief camp in one image.

### Chid

**`chid.names`** (Keep, and watch the date.) "It always takes the names
first. Then the faces." It is the closest Act 1 comes to saying the
twist, and the bible intends it. Keep it on day three or later; it should
come after the dawn line in the prologue has had time to be forgotten.

**`chid.below`** (A question.) "The Order used to say the dark's only
light that hasn't been found yet. I never liked that one. It sounds like
a threat." Meanwhile the rite (`chid.relight`, the night bark) says "the
dark is only the part of the day that hasn't happened yet". Two versions
of the Order's creed. If deliberate (the official creed, and its older,
truer, darker form that Chid "never liked"), it is a superb plant for the
Morrow, and should be kept exactly. If not, make it deliberate: it is.

**`chid.long`** (Keep.) "Lovely woman. Terrible bread." Chid at his most
Chid. The joke is also the clue.

**`chid.note`** (Keep.) "Cuthbert. Cressida. There was a Cormac, once,
who— (He stops.)" The interrupted list is how a man who never says his
age says his age.

**`chid.cb_nell`** (Keep.) "She was very light. ...Sit down a minute. Not
there. There." The comic tic ("Not there. There.") returning at a
graveside, where it stops being funny, is how repetition earns its keep.
Note that it is also used in `chid.cb_nemesis_slain`. Two uses is right:
once to make it a joke, once to break it. Do not use it a third time.

### Vonnra Ash-of-Morrow

**`vonnra.vault`** (Fix: a promise she breaks three times.)

> "Not for any price. That is the only thing I will ever say to you without charging for it."

Then `vonnra.ford` ("This once, no charge"), `vonnra.coin` ("That was
free"), and `vonnra.fortune` ("No charge, this once"). Vonnra is the
character whose words must be exact; she never answers yes or no, and the
fun of her is parsing her. A broken "only" makes her sloppy. Either drop
"only", or keep it and make the contradiction a *tell* the player can
use. Better, because it is in character:

> "Not for any price. That is the first thing I have said to you without charging for it. Note it."

and let the free things be counted: by the fortune, a player who has had
four free things from her is owed something, and she knows it ("No charge,
this once. That is the fourth once. I am aware.").

**`vonnra.f_self`, the risen variant** (Tighten.)

> "And you. You have already died on this road. Most people only get to do that the once. Something did not want you to stay down, and I would very much like to know what."

"get to do that the once" is a contraction-free sentence with a
contraction's casualness, and "I would very much like to know" says what
she wants, which her voice never does. On the reread it is a lie (she
knows exactly what), which is good, but let the lie be one of omission,
in her register:

> "And you. You have died on this road already. Most do it the once. Something would not let you lie down. (She is looking at your hand very hard.) I see that. I do not see what."

**`vonnra.f_past`, fallback** (Keep.) "The water took it, or you left it on
the far bank. Most do." The single best clue in the game: it is true
twice, literally (the survivor drowned) and as fortune-teller's
vagueness, and "Most do" tells you she has seen this before. It is the
model for every other plant.

**`vonnra.risen`** (Keep.) "...you will find out who holds the note." A
debt metaphor from a woman whose only verb is payment, which turns out to
be the plot.

**`vonnra.cb_core_stolen`** (Keep.) "I am not angry. I am arranging."

**`vonnra.cb_opened_vault`** (Tighten: the best clue in Act 1 goes
unremarked.) The survivor has just walked through the Legion's door and
come back out, which a living man (Jessop) could not. Vonnra knows
exactly what that means. Her line should betray that she knows, without
saying it:

> "You opened it. ...And came back up the stair. (She looks at you the way she has never looked at anyone who paid her.) Do not sit, traveller. I would rather you stood. I would like to see all of you."

### Dame Keegan Orme

**`keegan.say_risen`** (Keep.) "You look extremely well. ...I've got to
go and read something." The contraction slipping out is a voice rule used
as a plot clue. It is the cleverest thing in `VOICES.md`, delivered.

**`keegan.prof`** (Keep.) "That was litotes. You're welcome." (and notice
"You're": she is not on duty with children.)

**`keegan.warden`**: see note 1.

**`keegan.cb_opened_vault`** (Keep.) "It is the word 'don't', in several
sizes."

### Sella

**`sella.night`** (Keep.) "She is dressed, and counting." The last three
words of the scene tell the player that the intimacy was also work, and
also, maybe, more than work; and on the reread they say she is counting
what you told her. Superb.

**`sella.sleeptalk`** (Keep.) "Didn't catch it. I don't think you did
either."

**`sella.t_sella`** (Keep.) "a door that locks from the inside, and
somebody who knocks." And the free night's "the bolt, which she shoots
herself, which she has never done" pays it. That is a promise and payoff
inside Act 1, in two lines.

### Redcowl

**Bark** (Tighten.)

> "Last man who lied to me, I nailed his tongue to a cart and let the horse decide."

It is a good bandit line and the wrong man's. Redcowl is the bandit who
feeds his prisoners before his own people; a story about torture he
actually did works against the character the Act 2 army depends on. Keep
it as theatre and let him undercut it, which is also funnier:

> "Last man who lied to me, I nailed his tongue to a cart and let the horse decide. ...Ha! I didn't. But you'll tell it, and that's the same."

**`redcowl.ashford`** (Keep.) "(The laugh goes out of him like a lamp.)"
The simile is from the world (lamps everywhere) and it is the one simile
in the scene, so it lands.

**`redcowl.crates_keep`** (Keep.) "Guarding crates. My mother'd laugh
herself sick." Paired with Rav's "Our mother's idea": the family rhyme
`VOICES.md` describes, done quietly enough that a player will feel it
before they see it.

### Snib, the lampling, the Wayfinder

**`snib.poison`** (Keep.) "the heart is hungry, the heart wants DOWN" is
the best seed for Grimtunnel's faith in Act 1. See 2.5: Grimtunnel
himself should echo it.

**`snib.pipelads`** (Keep.) "Snib was a pipe-lad. Snib got promoted." The
comic character's one dark line, which earns him "survives everything".

**`survivor.what`** (Keep.) "Kell's lamp came back up on its own, still
lit." The lamp coming back without its bearer is the sort of image
FromSoftware would put on an item; consider making Kell's lamp a
findable item (`IDEAS.md`).

**`wayfinder.places`** (Tighten.)

> "Half an hour, give or take, and it only gets worse. The ember in you starts from nothing in there, same as every night. Last the half hour and whatever rules the place comes out to see who's been killing its people. Kill it and the way out opens where it fell..."

This is a tutorial in a character's mouth. It is the one place where that
is defensible (she sells the maps), but it is where `VOICES.md`'s
"nobody explains a mechanic" is most visibly bent. Keep the facts, give
them a cartographer's indifference, and cut the last instruction (the
interface already says it):

> "Half an hour, give or take, and worse by the minute. Whatever you carried in, you start from nothing; the place doesn't care what you were. Last the half hour and whatever owns it comes to look at you. Most people I draw, I draw from about there."

**`wayfinder.drawn`** (Keep.) "I buy what they remember before the drink
takes it."

**`wayfinder.t_wayfinder`** (Keep.) "My brother didn't [come out]." A lie
(he came out risen, and the Vigil took him), told as grief. On the reread
it is both. That is the right kind of lie for a character with a secret.

---

## 6. Items (`items.json`)

**6.1 Weapons and armour mostly have no lore.** The starting weapons are
the first things a player inspects, and they have mechanical
descriptions only. Item lore is the cheapest worldbuilding channel the
game has (FromSoftware's entire world is told in it; `CRAFT_STUDY.md` §7),
and it reaches players who skip dialogue. One line each, in the
narrator's register, tying the object to the valley:

| Item | Offered lore |
|---|---|
| Watch Buckler | "The Watch's lamp, painted on the boss and worn to the wood. Every recruit was told it had been to Ashford. Every one." |
| Butcher's Cleaver | "From the slaughter-yard behind the Last Lamp. Rook says she'll want it back. She says it the way she says most things." |
| Pair of Gyre Axes | "Kerchief-made: the heads are old Ashford wood-axes, reground. Somebody kept the maker's mark." |
| Apprentice's Wand | "Willow, and a thread of ember-wire at the core. The motes find their own way. Nobody has ever asked where they go after." |
| Ember Staff | "Ash wood, cored with cooked ember. The grain remembers being warm, and wants to be again." |
| Rime Rod | "Cold iron from the bottom of the Low Ford. It has never once been warm." |
| Hunter's Crossbow | "Ashford pattern. The garrison's armourer stamped each stock with a date. This one's is ten years ago, in the spring." |
| Knife Belt | "Nine sheaths, nine knives, and a tenth sheath for the one that didn't come back." |
| Old Watch Shield | Its description says "Carries the Watch's faded torch." The Watch kept *lamps*: make its device a lamp. "Carries the Watch's lamp, faded to a smudge. Forty of them, once." |

**6.2 Ember itself is never described as what it is.** Ember is the
Morrow's light and its pain (bible §1). The items that hold it say only
that it is a stone with light in it. The ember items are where a
FromSoftware writer would put the horror, deniably, for the player who
reads:

> Ember Shard: "A stone that kept some of its light. Hold it to your ear in a quiet room and the room is not quite quiet."

> Blasting Ember: "A crate-charge of unstable ember. Something could be blown open with this. Or up. It is warm, and it is warmer when you are afraid."

> Ember Slurry: "Warm, faintly glowing sludge scraped from a pipe. It smells like a chapel lamp. It smells, a little, like a wound."

**6.3 Grimtunnel's Spare Lamp** (Tighten: the believer's seed, see 2.5.)

> "He dropped it going down the hole at the Low Ford. It is still warm, and it is still his, and he will want it back."

Keep, and add one line that is scratched on the casing:

> "...Scratched round the rim, in lampling letters, over and over: DOWN TO HIM. DOWN TO HIM. DOWN TO HIM."

**6.4 The Warden's Lamp-Iron** (Keep, with note 1.) "Under the socket, cut
clean and new, a smith's mark: a hammer struck through a B." This is a
model clue: concrete, visible, and it points at a person without saying
what he did. With note 1's fix, add: "The cage is made to hold ember, not
oil."

**6.5 Small fixes.**

- Grave Tether downside: "The Order of Morning Light" lacks "the";
  elsewhere it is "the Order of the Morning Light".
- Storm-Carved Totem: "The Karrash" appear nowhere else. That is fine (an
  unexplained proper noun is the iceberg's tip; Tolkien's "Elbereth",
  Erikson's everything), as long as it is never contradicted. Add the
  Karrash, the Collegium, the Glass-sworn, the Low Cloister and Saint
  Wend's to a world glossary so that the next writer neither contradicts
  nor duplicates them.
- Pilgrim's Ember-Lantern: "Lit from the last lamp in the Chapel of the
  Morning Light." Rook's lamp over the door is also from the chapel ("My
  mother carried it up from the chapel the year the Order left"). Decide:
  is the devout's lantern lit *from Rook's lamp*? If so, Rook should
  notice (she does, in `rook.lamp`: "You've one too, I see."), and the
  lore could say so: "Lit, the year you took your vows, from the lamp over
  an inn door in the north."

---

## 7. The journal (`quests.json`)

**7.1 The quest outcomes are flatter than the entries.** The entries are
written; some of the outcomes (which the chapter page shows as the last
word on a thread) are placeholders:

| Outcome | Now | Offered |
|---|---|---|
| `caravan.lost` | "The cargo is gone." | "The Coyle cargo went up with the Roost. Harlan has stopped saying what was in it." |
| `caravan.with_kerchiefs` | "The Kerchiefs kept what they took." | "The Kerchiefs kept what they took, and sold it down the south road, and ate." |
| `caravan.kept` | "The cargo is yours. The Coyle Company knows that too." | (keep: it is good) |
| `beasts.ignored` | "Nobody dealt with it. The wolves came closer every night." | "Nobody dealt with it, so the wolves did. They came closer every night, and then they came in." |

**7.2 `prologue` outcome.** "You crossed the Low Ford at dawn." Did they?
The fight is at the ford and the road goes north; if the survivor never
crosses the water, "crossed" is wrong, and if they do, it is worth saying
what crossing means now: "You crossed the Low Ford at dawn, which nobody
has done alive in a year." (True on the surface: the Warden drowned
everyone. True underneath: the survivor was not alive.)

**7.3 The lamps summary** (Keep.) "Somebody relit the lamps at the Low
Ford, and the Warden woke and drowned whoever crossed after dark." Fair,
complete, and it contains the answer to Act 2: the survivor crossed after
dark.

---

## 8. The morning reports (`rules.json`)

These are the best prose in the game. They are the place where the
narrator's restraint pays most, because the player reads them at the
quietest moment of the loop (waking) and they report the consequences of
the player's own actions without judgement. Three examples to keep as
the house standard:

> "The Watch says the lamplings were carrying their own out of the hillside all night: small, and burned, some still holding their lamps lit. One of them sat by the pile and counted them. It got to forty and started again."

> "Jory Coyle woke the inn twice in the night, shouting for a man called Ewan. Rook sat with him until it was light. Ewan was in the fourth cage, he says. There isn't a fourth cage any more."

> "Holloway read the words himself and got two of them wrong, and nobody corrected him. His wife is coming up from Low Kiln. Somebody will have to tell her about the leg."

The pattern: the event in one clause; one concrete, slightly wrong detail
(the counting, the wrong words, the leg); and an ending that hands the
weight to someone who is not the survivor. Every new report should be
held to it.

One fix:

> rule 31: "...He was back before the gate shut, with something under his apron in the cart..."

"Under his apron in the cart" is a confusing image (is it under the apron,
or in the cart?). Brannoc took a blanket; use it:

> "...He was back before the gate shut, with the blanket over something in the cart, and Chid walked out past the guards to meet him."

---

## 9. The townsfolk (`folk.json`) and the notice board

**9.1 Keep** (some of the best world texture in the game):

> "You smell like the dead. No offence. Everybody does, lately."
> "Chid's not aged a day since my mam was a girl. Says it's clean living. Have you SEEN where he lives?"
> "Brannoc's stopping carters off the south road, asking after a red-haired girl. Nobody's had the heart to say they've not seen her."
> "Harlan stood at the graves the whole afternoon. Didn't say a word. Didn't take his hat off, either. Forgot he had it on."

**9.2 The board's "R."** (Fix.)

> "Did anyone else feel that? — R."

"R." is the initial in Pell's ledger that the caravan quest turns on
(`ledger_read`: "Who is 'R.'?"). A second "R." on the board, by someone
else, is either a red herring (in which case it should be meant and
followed) or an accident. A player hunting for R. will read it. Sign it
with anything else: "— T." (Tam's handwriting would be a joy: "Did
ANYONE ELSE feel that. — Tam, age 9").

**9.3 The board's cat** (Keep.) "Has anyone seen my cat? Grey. Answers to
nothing. M." and then "She was in the grain store the whole time." A
trouble that resolves itself, in a town where nothing else does. That is
what comic relief is for.

**9.4 `concerns.json` vonnra[3]** (Fix.) "Keeps the toll, reads the
cards..." She reads palms (`vonnra.fortune`: "Give me your hand"). Make
it "reads palms" or, better, "reads hands".

---

## 10. Barks (`npcs.json`): the system note

The barks are well voiced and almost entirely static. Each person has
three or four day lines and three or four night lines, and with a few
exceptions (Brannoc's "Two on the rack") they do not change with the
world. In *Darkest Dungeon* and *Hades* the bark is the cheapest form of
reactivity (`CRAFT_STUDY.md` §8–9): the town noticing what the player did
without a conversation. The data already has the facts. Proposed rule
for every named person: **at least one day bark and one night bark per
settled thread that touches them**, gated like the dialogue's `cb_`
lines. Examples in voice:

| Who | When | Bark |
|---|---|---|
| Brannoc | `nell.buried` | (none, by day: he says nothing at all.) Night: "Forge is lit. Don't come in." |
| Brannoc | `nell.told` `lie` | "Low Kiln's three days. She'll be there by now." |
| Harlan | `jory.knows_be` | "Mister Coyle, he calls me. In my own shop." |
| Maeca | `beasts.outcome` `cured` | "Hear that? They're hunting again. Deer." |
| Holloway | `holloway.post_told` | "Corran had the post before me. Did I say that? I said that." |
| Chid | a death | "You're up! Up's good. Up's very good." (and after the third: "Up again.") |
| Vonnra | `vonnra.accused` | "{name}." (only the name; nothing else, ever, as a bark) |
| Rook | `caravan.survivors` `dead` | "Harlan's not eating. I've sent bread. He's sent it back." |
| Keegan | `keegan.saw_risen` | "Chapter four. Chapter four. ...Good morning." |
| Sella | `sella.free` | "Don't say anything up there you'd not say to Vonnra. I mean it nicely." |

One more rule worth adding to `VOICES.md`: **a bark is never more than
twelve words.** Most already are not; Rav's "Pox, piles, a pike-wound or
a broken heart: I've a cure for three of them and a drink for the
fourth." is lovely and is the length of a short speech. Give it to him as
dialogue (`rav.hub`) and keep his barks short.

---

## 11. A short checklist for the next writer

Drawn from the patterns above. Every new line should pass all of them:

1. **Does anyone say an answer before its act?** (Bible, rule one.) Watch
   the interface (trait text, hints, result screens) as closely as the
   people; note 4.4 is the interface breaking it.
2. **Does the narrator name a feeling, explain a meaning or wink?** ("—
   probably —" is a wink.)
3. **Is a character's "never" broken?** If so, is this the one written
   exception, and is it the scene? (Maeca's Ashford is broken on
   meeting; Brannoc's thanks is broken where it should be.)
4. **Does this line repeat an image already used?** ("Hums against your
   teeth" twice; "Probably" twice; "Not there. There." used up.)
5. **Does a name, an initial or a colour collide with a clue?** ("Red
   Wat"; the board's "R."; violet is the Toll Tower's colour, so nothing
   else in the valley may be violet.)
6. **If the line repeats on every visit, does it ever change?** (Chid's
   carter; the barks.)
7. **On the second playing, does this line mean something else?** If it
   could, and does not, it is a missed plant. (The first line of the
   game; the Warden's barks.)
