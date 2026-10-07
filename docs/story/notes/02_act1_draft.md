# Notes 02: the Act 1 draft, as the game has it

From the story editor (the third, reading fresh) to the writer, and to the
owner through the main session, 6 October 2026.

I read Act 1 as it stands in the data on `claude/vigilant-galileo-l6jqyx`
(the rewrite is `756628ab` and `e5d65111`):
- every node the rewrite added or changed, node by node against `74280668`;
- the five gate scenes, the overnight rules and the morning reports;
- the barks, the folk lines and the journal;
- the Waystation's burial and grave;
- the docs: `TREATMENT.md` §0, the bible's Act 1, `WRITING_PASS.md` §26 and
  `LOVE_SCENES.md`.

I read it against the letter and notes 01. I have not played it. Where a note
depends on what the screen does, it says so.

**The owner, in their words:**
- "we really want a powerful epic story with real emotional happenings.
  people being devastated, elated, or both. shocks and twists, stuff we
  figured out that was obvious."
- Brannoc's arc "needs to hit HARD. so hard."
- "when maeca kills halloway it should be a HOLY SHIT WHAT THE FUCK kinda
  thing."
- On Holloway's act: "its a decision we can make which makes it more
  horrifying".
- On the lie to Brannoc: "we can't get punished from gameplay perspective".

## The verdict

This is the best Act 1 the game has had, and most of it is the right thing in
the right place. The writer took nearly every note in 01:
- the confession's tell is cut, the confession is mid-act, and "tell Maeca"
  is on the trunk;
- the decoy is red, or a ledger;
- Holloway is clean of boots, and his act is (b);
- Rook's kind lie is written, with the ring on the nail;
- C07 puts the mercy before the knife;
- three people thank her for the ford, and Vonnra says both halves;
- the Watch's number, Tam's Pa, and the word written down are all in.

Three things in it would make a player stop:
- **C07**, now the best scene in the game by a distance;
- **the knocking**, Holloway's ledger syntax ("Lid down. Bar across. Sat on
  it.");
- **"...Did he."**, which on the re-read is the coldest line in the game.

The plants for "Ninety-two" are the best twist-work in the draft.

It is not at the bar yet, for one reason above the rest: **the act's heaviest
payloads still arrive the way the letter warned against.**
- Brannoc's held image, his hand round the last light, is a paragraph in the
  next morning's report. The player never walks the road.
- Act 2's end, the woman with the lamp, is given away at Act 1's end by its
  own ledger line.
- Holloway's first and costliest kindness, the coat, is not in the game. And
  nothing holds the order of love first, then knowledge.

None of these needs new invention. Each is one of three things: a scene to
play rather than report, a line to move, or a gate on a rule. Do them, and
Act 1 is ready for the owner.

## At a glance

### The owner's later decisions

| Decision | In the draft | See |
|---|---|---|
| Holloway's act is (b), the lid on the ladder | Yes: "Lamp in my eyes" in the confession; Maeca's line is Act 2's | Add one more fair plant (§6.1) |
| No boot detail reads as silly | Holloway is clean. Three small things are left | §6.2 |
| "Wick" replaced; the lamplings renamed | Yes: "Spark"; Stub and Old Gutter | One item affix still says "Spark" (§6.3) |
| Brannoc's arc hits "so hard" | C07 does. C14 is a report; C08 is optional | Item 1 |
| Maeca killing Holloway lands as "HOLY SHIT" | Act 1's plants are strong; one leak, and the order isn't held | Items 3 and 4 |
| Holloway rises at his gate on the fourth dusk | Planted | Settle what knocks (§6.6) |
| The lie to Brannoc carries no gameplay cost | Not quite: the truth answers raise his trust and respect, which lower his prices and open commissions | §6.7 |

### The twists against the six tests (letter §3.7)

| Twist | False belief | Re-reads | Fair but hidden | Obvious after | Cost | Own hands |
|---|---|---|---|---|---|---|
| "You did this" (Act 1) | Built: three thank her | Yes, seven | Yes | Yes | None in Act 1 (item 5) | Yes, the nod |
| "Ninety-two" (Act 2) | Strong | Yes, twelve (five on the trunk) | One leak (item 3) | Yes | The highest | Act 2's haul |
| The woman with the lamp (Act 2's end) | Named, then broken at Act 1's end (item 2) | Yes | No: the ledger | Yes | The highest | Its prologue plant isn't built |
| The voice (Act 3) | Strong | Yes | Yes: the best hidden | Yes | Act 3 | Acts 2 and 3 |

### The beats against the bar (would it make a player stop, swallow or laugh?)

| Beat | Now | What it needs |
|---|---|---|
| C07, his iron in his hands | Stop, then swallow | Its sound (item 1) |
| C14, his hand round the light | Nothing: it is reported | Item 1 |
| C08, the burial | Swallow ("She was very light."), for those who go | Bring it to her (item 1) |
| The road dark, the hammer slow | Swallow | Nothing |
| The gate at dawn | A smile; a chill on the re-read | One cut (§9) |
| "She's in my count." and the empty cup | Swallow, and a smile | A voice in the crowd (§9) |
| The knocking | Stop | One funnel line; one more plant |
| "...Did he." and her cup | Cold, and on the re-read the coldest line in the game | "Ninety-one" heard (item 4) |
| Rook's kind lie | Swallow ("You came, pet.") | The trunk, and one line (item 2) |
| The dawns; Chid's "names" | A quiet ache; devastating on the re-read | Nothing. Protect them. |
| The fortune: "You did this" | A "huh", not a knife | Item 5 |
| The ledger | A shock: the wrong one | Item 2 |
| The lie: "Aunt'll feed her up. She's thin." | Swallow | Nothing |
| Jory home: "Three in!" | A smile, nearly a laugh | It is on a branch (§8) |

---

## 1. Play the road (C14), and bring the burial to her

**What's there.** C07 now ends like this:
- "Forge is shut.";
- "You know the place.";
- "I'll show you.";
- "(Go with him.)", and the panel closes.

The next thing the player gets is the morning report `nell.burial_with`, in
the past tense: "you walked down the Low Ford road with him... closed his
bare hand round the light until it went out." Nothing plays between the two.
No code calls `cin_road_back`, and C14 is not one of the built cinematics
(those are C01 to C04 B).

**Why it costs the most.** This is the act's devastation in its held form,
the image the owner's "so hard" is about, and the player is *told* they were
there. It is the letter's first root cause in its purest form: the payoff
whispered, and after the fact. (Until it plays, check in Godot whether
Brannoc is still standing at his anvil when the panel closes on "He goes
out".)

**Direction.**
- **Play it now as a dusk scene,** the way the gate scenes play:
  - present tense, the narrator plain;
  - the walk between his irons, and he doesn't look up;
  - the last iron, over the ditch;
  - his hand closes round the light; the hiss; no line over it;
  - held long enough to be uncomfortable;
  - then the ditch, and the one word `cin_road_back` already holds:
    "...Wat." (That conversation is orphaned now. It belongs here.)
  - then the boots out of the blanket's end.
- **Then the cinematic,** when cinematics resumes. This is the Act 1 shot
  that most needs pictures.
- **Cut the morning report to the burial:** "They are burying her this
  morning..." The road isn't news to someone who walked it.
- **"Not tonight":** the treatment has her watch from the wall, his lantern
  going down the blue road and one blue light going out. Play that too, as a
  short scene. The report can stay as the town's telling for a player who
  wasn't in town.
- **Bring the burial to her.** C08 is an interactable in the Quiet Garden
  ("Stand with them"), there for one morning. A player who doesn't walk there
  misses:
  - Chid's hymn, and "She was very light.";
  - Rook's lamp left on the grave, the empty hook her bark mentions.

  On the truth routes, make it a morning scene on the trunk, like the others.
- **C07's sound.** Even as a conversation, give it three cues: the hammer
  stopping mid-stroke, the forge ticking, and no music. It costs little and
  doubles the scene.

## 2. The ledger gives the woman with the lamp away

**What's there.**
- Rook's kind lie (`rook.mother2`): "She went in her sleep, pet. A week
  since." Then (`mother_room`): "Back room's yours, if you want it. It's been
  free a week."
- At the fortune the ledger is readable: "The twenty-fifth: Nell, the
  smith's girl. With Wat. The twenty-sixth: Rook's lodger. And under them a
  twenty-seventh, not struck: From the ford. Got up."

**Why it fails.** Notes 01 offered "Rook's lodger." because the player
wouldn't know her mother had lodged at the Last Lamp. The draft tells them so,
in the same breath as the lie: dead a week, and the back room free a week.

So at the end of Act 1 the player reads "Rook's lodger." struck through,
between the smith's girl and themselves. That says two things: their mother
drowned at the ford, and Rook lied. A careful player has the rest before Act 2
opens (the drowned woman at the water's edge), and C32 then confirms instead
of turning. The false belief the lie was written to build is undone two acts
early.

**Two smaller leaks in the same scene:**
- **"I was a day short."** The survivor's option contradicts "A week since."
  and the bible ("her mother's, a week down"). Rook's answer, "(Something
  goes across her face, and is put away.)", then reads as a flinch at the
  truth. Players will take it as a slip or a tell.
- **Rook looks at the tower twice:** in C04 B (built), and again in
  `rook.mother` ("out of the window at the tower"). One look is a plant. Two,
  with the second at the word "mother", is a pointer.

**And the lie isn't on the trunk.** It is a hub choice ("I've come home. My
mother sent for me."). A player who only rests at the Last Lamp never hears
it. They never have the false belief, and they never once look for the mother
they came home for (the hole notes 01 named).

**Direction (the writer's to choose):**
- **Put the lie on the trunk:** in Rook's first meeting, or as a morning
  scene on day 1 or 2.
- **Separate the room from the lie.** Either:
  - the lie places the death elsewhere ("at home, in her own bed; Chid
    brought her down"), and "Rook's lodger." is innocent again; or
  - the room stays in the lie, and line twenty-six stops pointing at Rook.
    The quietest version: the ink on twenty-six has run, as the letter's has.
    That plants without pointing.
- **Give the survivor an answer the lie allows.** "A week. I was a week on
  the road." keeps Rook's flinch, and the flinch re-reads.
- **Keep one look at the tower:** C04 B's.

## 3. "Three days" is Holloway's number

**What's there.** The confession: "Lid down. Bar across. Sat on it. ... Three
days, they knocked." On the lover route Maeca says two more things:
- the first morning at the Blind (`blind_morning`): "The Pack found me, after
  Ashford. Three days, and then a cave mouth, and a lad I'd been fond of
  dying in it.";
- the lamp-lighter's answer (`told_true`): "I held a cave mouth three days
  for nobody coming."

**Why it leaks.** A player who hears both has the twist. She was somewhere
for three days and then came out at a cave mouth; the people under the lid
knocked for three days; and Pell has already said the lid was barred from the
top.

It leaks on the route the letter called the strongest version, the lover's.
So it costs most where the beat could hit hardest. VOICES.md's own rule is
that Maeca says three words about Ashford and nothing else. The lover may
hear more, but never the number.

**Direction.** Maeca never says "three days" in Act 1.
- "The Pack found me, after Ashford. A cave mouth, and a lad I'd been fond of
  dying in it." still re-reads (a cave mouth is where she came out, not where
  she stood), and it is innocent the first time (it was her post).
- The same for `told_true`: "I held a cave mouth for nobody coming."

## 4. Love before knowledge: the coat, and the order of the beats

**The player doesn't yet love him enough, in what ships.** The letter's test
is three or more on-screen acts of protection, each costing him something,
one of them while he is drunk and failing. What plays today:
- **the gate at dawn:** a vigil, drunk and asleep at an open gate. It costs
  him nothing the player can see.
- **"She's in my count.":** drunk, alone, his own men standing back. This one
  costs him, and it is the best of the Holloway scenes.
- **the coat** (his only coat, the first morning): not built. It waits on
  C04 B.

So in the data there is one act of protection with a cost. The rest of his
warmth is good: the cat, the dog, "it'll take you all morning", the empty
cup passed over. But that is charm, and charm makes a player like him, not
love him.

**Direction.**
- **Get the coat into the game before Act 1 ships,** by the quickest route:
  - a line and a narrator caption in C04 B; or
  - a stand-in in `scene_gate_dawn`: his coat round her the first morning,
    and the guard: "That's his only coat."

  Then let it pay as the status page plans: on his stool, then on him, then
  on Maeca at the war.
- **Give the gate at dawn a cost the player sees.** He held the gate open all
  night, for one traveller, in a valley where the dead walk. Let that cost
  him something in the morning: a word from Keegan, a sheep gone, his men's
  look. Small, specific, his.

**The order isn't held.** The rules allow three bad orders:
- **The knocking before "She's in my count".** The knocking needs only day 3.
  The count scene needs a night fight the night before and a free morning.
  So a player can learn what he did before they've seen him stand for them.
- **The fortune before the knocking,** for a fast player who settles both
  quests by day 2 (`chapter.ready` checks only the quests).
- **"...Did he." and the cup after the fortune.**

When Act 2 starts "the night after the fortune", C20 can then come before the
cup, and the false forgiveness never happens.

**Direction.**
- Gate the knocking on the count scene having played, or on a fact it sets.
- Gate the fortune's note on the cup (`holloway.cup_seen`).
- Gate C20 on the cup too, when Act 2 is built.

**Put "ninety-one" in the ear, on the trunk.** Today the number is said in
the confession once. It is also in a folk line and a night bark that the
player may or may not pass. For "Ninety-two." to land as one sound, the
player should have heard him stop at ninety-one more than once, and once near
her.

The cup scene already has him "counting". Let the player hear it:
"...Ninety. Ninety-one." He stops there; she comes down the street and fills
his cup. On the re-read, she fills the cup of the man who stopped one short
of her.

## 5. "You did this" needs a cost in Act 1

**What's there.**
- **The pride is built:** Holloway's "...Thank you.", Sella's tavern drinking
  to her, and the carter on his box.
- **The rhyme is built:** "You stopped the drowning, traveller. You also did
  this."
- **The consequences she names:** "The ground has turned over every night
  since. The Dig digs faster. The Penhale boy's floor knocks."

**Why it's a "huh", not a knife.** Those consequences are weather. Nothing
the player loves has paid for the tremors yet. So the twist re-reads the
prologue but takes nothing, and the cost lands only in Act 2 (the hole). Act 1
ends on a mechanism.

**Direction.** The cost is already in the act; the fortune just doesn't say
it. The knocking scene opens with the ground turning over under the square,
and that is the night Holloway hears knocking from under. Let Vonnra's list
end on him, in her register (what can be seen from a tower):

> "...The Penhale boy's floor knocks. The captain sits at his gate and
> listens to the ground."

Then the player hears that their finest hour is why the man they love can't
sleep, and the rope in Act 2 is the bill.

---

## 6. The owner's checks, one by one

### 6.1 Holloway's act is (b): the lid on the ladder

**It's in.** "Me at the top. Lamp. Windlass. Lid. Counting them up. Lamp in
my eyes." It reads as atmosphere, which is right.

**It is one plant, though,** and (b)'s turn in Act 2 has to feel obvious
afterwards. Give the confession one more detail that is true of both: the dead,
and the living too far gone to call out (the treatment's own words). For
example: "Dead. Climbing. Grey, all of them, and not a sound out of them."
The player hears horror. After Maeca's line, they hear slurry and silence.

### 6.2 No boot detail reads as silly

- **Holloway: clean.** The roll is "Abbot. Two bairns. Ancell. His mam." It
  has no sizes and no "Every pair", and there are no boots in the
  confession. Nobody dies of footwear.
- **Nell's boots: keep.** They are the irony the Brannoc beat needs, and they
  are never a cause.
- **Maeca's romance: thin it.** It has five footwear beats:
  - her boots off at the fire, and her bare feet on the ground;
  - your boots set side by side outside the hides;
  - "hard as boot leather";
  - barefoot in the frost, twice.

  By density they redraw "Barefoot". And in `LOVE_SCENES.md` version B, her
  first word in one of her first nights is "Boots." Keep the two that work:
  her bare feet on the ground, listening; and "Nobody's held those." Cut your
  boots from `maeca.blind`, and "Boots." from B.
- **The morning report `kerchief.raid`:** "took his boots". Make it his mule.
- **The treatment's body still has the old roll:**
  - §4.1, "every soldier's boot size";
  - §4.3 item 4, "Abbot, nines... Garrison. Boot sizes.";
  - §4.6, "with boot sizes".

  §0 overrides them, but the owner reads the body. Strike them.

### 6.3 "Wick" replaced; the lamplings renamed

**Done.** "Lamp's lit, Spark." is in C04 and the journal. Stub and Old Gutter
are in `Enemies.cs`, `Dig.cs` and `Journey.cs`. Read aloud, "Spark" is short,
dry and a child's name; it was the right call over "Flame".

**One thing competes:** the item affix "of the First Spark" (`Items.cs`).
Rename it, so the word is hers alone.

### 6.4 Brannoc's arc hits "so hard"

**C07 does.** It is the best scene in the game, and it is on the trunk (at
dusk, from day 2):
- the mercy before the knife;
- the iron at her belt, and his thumb finding the mark without looking;
- "Knew my mark before she knew her letters.";
- "She'd have thought I'd come for her.";
- the bar going grey, then "Forge is shut."

The pride plants are cruel in the right way ("Nothing on that road you can't
see."), and so is the bark after the truth ("Twelve, I made."). What stops the
arc hitting "so hard" is item 1: the held image after C07 is reported, and the
burial is optional.

**One gate.** The dusk call needs `met: brannoc`. A player who hasn't been to
the forge by day 2 waits; one who never goes never gets C07. Let the dusk call
be his first meeting if they haven't met (he calls the stranger over), so no
road misses it.

### 6.5 Maeca killing Holloway lands as "HOLY SHIT"

**Act 1's job here is the false belief and the plants, and the draft does it
well.**
- She sits over him with a loaded crossbow, and the player reads care.
- She walks him home, and won't let him pay her double.
- "...Did he."
- She fills his cup.

Fix item 3 (the leak) and item 4 (the order and the coat). Then three smaller
things:
- **`scene_did_he`:** "(She's waiting for you at the well, which she never
  does.)" Cut "which she never does". It tells the player her behaviour is
  unusual, on the one morning it must look like a friend's worry.
- **The folk line** "Maeca pays the captain's slate at the Flagon. Every week.
  He thinks it's the Watch." contradicts Holloway's own "She takes it every
  week, and buys my drink with it." A careful player who catches it will look
  at her. Pick one.
- **The decoy has a hole.** `decoy.rope` needs Redcowl unresolved, and
  `decoy.ledger` needs Pell unresolved. A thorough player who settled both
  gets no decoy, and that player is the one most likely to look at the kind
  friend. Give that route a third decoy. Sallow's rider is already there: let
  the town say the north wants the captain gone.

### 6.6 Holloway rises at his gate on the fourth dusk

**The plants are in:** "Three days, they knocked."; "Somebody's still out.
...Always somebody still out."; and him at the gate every night.

**Settle one world rule before Act 2 is written: do the dead knock?** Tam's
floor says something knocks "like somebody wanting to come in".
- **If the dead knock,** his three days of knocking can only have been the
  dead, and (b) can't turn it.
- **If they don't,** Maeca's one line in Act 2 turns the knocking itself: the
  living knocked, for three days, while he sat on the lid.

I'd take the second. It makes the confession's last image the worst thing in
the game on the re-read. Then C20b's three dusks should be the hole's
silence, not its knocking.

### 6.7 The lie to Brannoc carries no gameplay cost

**The words are right.** On the lie route he goes on hoping: "Aunt'll feed
her up. She's thin."; "Low Kiln's three days. She'll be there by now."; and
the carters he stops at the gate.

**The numbers are not.** The truth answers in `nell_ditch` raise his trust
(+15 or +25) and respect (+5 or +15). The lie and "didn't look" raise
nothing. That matters in two places:
- trust 30 takes a tenth off his prices (`Journey.PriceMod`);
- respect 20 opens two commissions and his first easier terms
  (`crafting.json`).

So the truth route reaches his discount and his patterns sooner. It is a
small but real gameplay difference, and the owner ruled it out ("prices,
commissions... as on the truth route"). Give all three answers the same
standing effect, or keep his warmth in facts that only the words read.
Telling him also raises Rook's affection, which feeds her prices; the same
fix applies.

---

## 7. The Holloway and Maeca tests (letter §3.6)

| Test | Act 1 now |
|---|---|
| 1. The player loves Holloway | Not yet: one costly act on screen, one vigil, and the coat unbuilt (item 4) |
| 2. A good man's decision | Yes. "Four hundred behind me, asleep. Bairns." A player would drop the lid. Under (b) it becomes horrifying, not just. |
| 3. Maeca's motive planted but hidden | Yes, apart from one leak (item 3) and three nudges (§6.5) |
| 4. In front of the player, fast, at the worst moment | Act 2's. Protect his first laugh: the decoy report says "Holloway laughed when he heard". A reported laugh isn't heard, but the reader remembers it. Consider "said nothing, and drank." |
| 5. Inevitable afterwards | Yes: twelve plants, five of them on the trunk (listed below) |
| 6. Not optional | The Act 1 scenes are on the trunk, once item 4's gates are in |
| 7. Worse if she is the lover | It can be, once "three days" goes |

**The twelve plants for test 5:**
- on the trunk: the crossbow across her knees; "Somebody waits up for him.";
  "That's your last."; "...Did he."; the cup;
- in her hub: "The cave mouths."; "Men are easier..."; "I walk the captain
  home"; "I don't let him";
- on branches: "I've never once saved anything."; "I've lain with my ear to a
  lot of things..."; "Holloway'll count us."

**"Gale. ...Gale."** in the roll is the best seed in his conversations, and
nothing pays it yet. Decide now who Gale was. If Gale is the lad she followed
down the shaft, then the romance's "a lad I'd been fond of" and the one name
he stops on are the same boy. The daybook can show it in Act 2 without a
word.

## 8. What lands, and why (protect these)

- **C07,** as above. Keep every word of it.
- **The gate at dawn:** the plant every player sees, read as care.
- **"She's in my count."** "He stands there until the last of them has gone
  home, and then he sits down where he stood." Then: "You sit. After a while
  he passes you the cup. There's nothing in it. Neither of you says so."
  These are the best lines in the new scenes.
- **The confession's ledger syntax:** "Lid down. Bar across. Sat on it.";
  "Both numbers are right. That's the trouble with counting."; "Widows get
  paid for the cave mouths." Drink loosens his grammar before it loosens his
  secrets, as the letter asked.
- **"...Did he."** on all three answers.
- **The lie route's knife:** "Aunt'll feed her up. She's thin."; and, from the
  folk, "Nobody's had the heart to say they've not seen her."
- **Rook:** "You came, pet. That's the part that counts."; the ring turned on
  the nail "without looking at it"; and "Chid brought her down", which
  re-reads.
- **The dawns:** "Her voice is going the way her face went. You still have
  the word." On the re-read, the narrator is reporting her own voice going.
  Nothing in the game is better hidden.
- **Chid:** "Your mother's name. ...No, don't tell me. You had to think."
  And, after the burial: "She was very light."
- **The calling remarks,** rewritten from each trade: "The Watch walks like a
  dropped tray."; "I've stitched men who sat like that. Mostly in the back.";
  "...Halt. Belatedly."
- **The comedy:** the cat counted; the dog; "it'll take you all morning";
  "Pa says the moles can knock on somebody else's bloody floor. I'm not to
  say bloody."

**The elation is on a branch.** Jory's "Three in!" plays only if the
teamsters are freed. That is earned, and fine. But the treatment promises
that choices "bend how each lands, never whether", and that isn't true of the
elation. Either say so in the treatment, or give the failed route a smaller
lift.

## 9. Line notes

| Where | Line | Note |
|---|---|---|
| `scene_gate_dawn.all` | "(...and says nothing at all, very loudly.)" | A capitalised parenthesis is the narrator's, and she is "never cute" (VOICES). Cut "very loudly"; the look does the work. |
| `scene_in_my_count.crowd` | "Somebody says it out loud: every night you go out into the dark..." | The threat is reported. Give it to one voice in the crowd. The narrator keeps "They are between you and the street, and they are not moving." |
| `scene_in_my_count.captain` | "...he stops in the gateway between you and them." | Make the movement the picture: he walks through them, and turns his back on her. |
| `scene_knocking.home` | "...You want to know about Ashford. Everybody does. Sit, then." | It doesn't follow from "Go home." Suggest: "Can't. Somebody's still out. (He drinks.) ...Sit down. I'll tell you who." |
| `scene_knocking.saw` | "Dead. Climbing." | Add the (b) plant (§6.1). |
| `scene_did_he.well` | "which she never does" | Cut (§6.5). |
| `scene_his_cup.cup` | "counting" | Let the player hear "ninety-one" (item 4). |
| `rook.mother` | "...out of the window at the tower..." | Cut; C04 B has the look (item 2). |
| `rook.mother2` | "I was a day short." | Contradicts "A week since." (item 2). |
| `rook.mother_where` | "you can tell Chid what to cut" | A promise nothing keeps. Either give the beat (Chid: "What do I cut?"; her name if the player named her at creation, "Mam" if not), or cut the clause. The beat would be worth having. |
| `vonnra.f_chart` | "The twenty-sixth: Rook's lodger." | Item 2. |
| `vonnra.f_did` | The list of consequences | Item 5. |
| `brannoc.nell_risen` | "(He looks at you then. Properly, for the first time.)" | His first meeting already has "He looks at you properly." Cut "for the first time", or cut it there. |
| `maeca.blind_morning`, `maeca.told_true` | "Three days" | Item 3. |
| `maeca.blind` | "She undoes your boots before anything else..." | §6.2. |
| folk: "Maeca pays the captain's slate" | | §6.5. |
| `decoy.rope` (report) | "Holloway laughed when he heard" | §7, test 4. |
| `kerchief.raid` (report) | "took his boots" | §6.2. |
| `nell.burial_with` (report) | The walk | Item 1: cut it to the burial once the walk plays. |
| `sella.say_calling` (stalker) | "You came up behind me without a sound." | Still twins Rook's "without the door making a sound", in the same house. Rewrite Sella's from her trade. |
| The narrator's tic | "which she never does", "which he never is", "which they never do", "which nobody has seen her do", "which she has never done", "You have never seen him put the hammer down." | Six in one act, and it is turning into a formula for "this matters". Keep the hammer and Chid's quiet; cut the rest. |
| `cin_road_back` | "You know the place." / "...Wat." | Orphaned: nothing plays it. "...Wat." belongs in the played road (item 1). |
| Wat | | The grey mare is mentioned once (C07), yet the lie route's Act 2 knife is the mare coming up the road alone. The treatment's folk line isn't in ("Wat's grey mare won't take a bit in winter. He warms it in his armpit."). Put it in. |

## 10. The love scenes: B is stronger

B, the lovers' own lines, is stronger, for three reasons.
- **It keeps twist A whole.** Under A the narrator's prose is still in the
  room, only unvoiced. On the re-read, the summit invites "Mum was
  watching?", and in an 18+ game that line will be quoted. B has no narration
  behind the door at all.
- **It's the better writing.** The romances' best lines were always the
  lovers' own, and B adds more:
  - "Nobody's paying me to hurry.";
  - "Seven years, love, and I can't undo a lace. Don't you laugh.";
  - "No talking. I talk for money.";
  - "How are you colder than my feet."

  A summarises the night; B is in it.
- **It has the stronger sex appeal,** which the owner counts as a driving
  factor. A voice close in the dark is more intimate than a paragraph about
  one, and it still fades at the moment itself.

**Four conditions:**
1. **The bolt is the door.** In B, the bolt's image ("like the last coin put
   down on a counter") becomes a sound direction that no player can read, and
   it is the best line in either version. Let it be the narrator's last line
   before the door, told from the stairs: she hears the bolt go home, and
   then she is silent. That is twist A's plant made audible: the player hears
   her stop at the door.
2. **Cut "Boots."** as Maeca's first word in B, and the boots from A (§6.2).
3. **Keep "one hand on the crossbow and the other on you".** B loses it, and
   it is a plant for the rope. The grey light at the Blind is outside the
   door, so let the narrator open the morning on it.
4. **B lives or dies on the takes.** Intimate, laughing, whispered lines are
   the hardest thing to make sound natural with generated voices. Cast and
   direct these with more care than anything else in the game, and keep A as
   the fallback if a take can't be made to sound like a person.

## 11. Hygiene

- **`TREATMENT.md`:** strike the old body text that §0 overrides. The owner
  reads the body. It still has:
  - the boot roll (§4.1, §4.3, §4.6);
  - "A woman with a lamp. North bank. Seventh evening." (§3.1);
  - "low, warm and unhurried, a winter's tale" (§3.4);
  - "from day 4" (§0), where the data uses day 3.
- **`tools/vo/elevenlabs.py`** still calls the narrator "he" ("How he reads",
  "his direction"). The packets the owner records from should say "she".
- **`docs/cinematics/act2_outline.md`** still has "Every pair." It is due for
  a rewrite with Act 2.

## 12. Order of work

1. **The two leaks:** "three days" out of Maeca's mouth (item 3); then the
   lodger line, and the lie it rests on, put on the trunk (item 2). About an
   hour's work, and it protects both of Act 2's twists.
2. **Play the road** (item 1), and bring the burial to her.
3. **The order** (item 4): gate the knocking on the count scene, and the
   fortune (and later C20) on the cup. Put "ninety-one" in the cup scene.
4. **The coat,** by the quickest route; and a cost for the gate at dawn
   (item 4).
5. **Vonnra's last consequence** (item 5), the (b) plant (§6.1), and what
   knocks (§6.6).
6. **The rest:** the lie's standing effects (§6.7), the boots (§6.2), then
   the line notes and hygiene.

— The story editor
