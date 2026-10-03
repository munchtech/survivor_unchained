# Dame Keegan Orme: the scenes

Every beat of Keegan's arc (`../ARCS.md` §3) as playable dialogue. Act 1's
`supper` is also drafted as data in `../data/keegan.json`. The notation is
`sella.md`'s.

Voice check: on duty, no contractions. They slip when she forgets herself,
and in this arc they slip **only with the survivor**, more and more, until
there are none of her rules left. She cites the handbook by chapter and
names rhetorical figures. She never swears. In Act 1 she never says what
chapter four is about. In Act 2 she reads it aloud, once.

---

## Act 1

### `keegan.dinner` *(existing node, unchanged)*

**KEEGAN** *(existing)*: Chapter eleven. Fraternisation. I have not read it.
...That is a lie. I have read it four times. The answer is no. The answer is
very nearly no. Good day.

(affection +10, existing.)

---

### `keegan.supper` **(new: supper on the wall)**

**Offered on `hub`:** "It's late. Have you eaten?" `<show time night and npc
flag keegan once:dinner>` `<when rel keegan respect >= 30 and rel keegan
affection >= 15>` locked: *She is on duty. She is always on duty.*
`once:supper`.

**Effects:** set `keegan.supper`; rel `keegan` affection +10, trust +5.

**KEEGAN:** I have not. I am on watch. (She looks at the bread in her hand,
which she has evidently been holding for some time.) Chapter eleven,
paragraph six permits "a meal taken in company for the purposes of morale".
I have read it very carefully. It does not say whose morale. ...Sit. Not
there; that stone is the one the gate was built on, and it is older than
manners. Here.

**NARRATOR:** She breaks the bread and gives you the larger half without
seeming to decide to. There's a heel of cheese, and a flask that turns out
to be water, and the north road beyond the gate is black all the way to the
hills.

Choices:
- "Saint Wend's. Tell me about it." → `supper_wends`
- "How old are you, Keegan?" → `supper_age`
- "Your letters. They're not answering because they don't want to."
  → `supper_letters`
- "Read me some of the handbook." → `supper_read`
- "(Take her hand.)" → `supper_hand`
- "Goodnight, Dame Keegan." → `supper_end`

### `keegan.supper_wends` **(new)**

**KEEGAN:** Rhetoric, to the sons and daughters of people who could afford
it. I was very good. I was the youngest lecturer they had ever had, and they
told me so every morning, in case I forgot and became the oldest. (She
smiles at the road.) I taught them chiasmus. "Ask not what the Vigil can do
for you." They did not, and it did not. ...That was a joke. It was not a
good one. It's late.

> *(The slip is "It's". She doesn't notice. Nor should the player be told.)*

→ back to `supper` choices (each `once`)

### `keegan.supper_age` **(new)**

**KEEGAN:** Twenty-six. The handbook says that is old for a probationer. The
handbook says a great many things. Some of them are true. (She looks at you
sidelong.) How old are you? No. Do not answer. I should only write it down.

→ back

### `keegan.supper_letters` **(new: the hard true thing)**

**Effects:** rel `keegan` trust +10, affection −5.

**NARRATOR:** She doesn't answer for so long that you think she won't.

**KEEGAN:** That is a possibility I have considered. (Very precisely.) I have
considered it every month for two years, on the day the post does not come.
I have written it down and crossed it out. That was an example of
correctio. ...Thank you for saying it. Nobody else will. They think I am
funny. I am funny. I am also not a fool.

→ back

### `keegan.supper_read` **(new: kindness about the handbook)**

**Effects:** rel `keegan` affection +5.

**KEEGAN:** (She is very obviously delighted, and very obviously trying not
to be.) Chapter nine. On bathing. "The knight shall wash at need, and not
for pleasure, the body being a lamp and not a garden." I have underlined
"garden". In protest. (She turns pages.) Chapter twelve. On the care of the
blade. That one is beautiful, actually. Shall I—? (She reads you chapter
twelve, all of it, by the light of the gate lamp, and it is beautiful,
actually.) ...You did not fall asleep. Nobody has ever not fallen asleep.

Choices (added after this, once):
- "Read me chapter four." → `supper_ch4`

### `keegan.supper_ch4` **(new)**

**KEEGAN:** (She closes the book.) No.

**NARRATOR:** She says it gently, and then she doesn't say anything else for
a while, and her hand stays flat on the cover.

→ back

### `keegan.supper_hand` **(new: a refusal, kindly)**

**NARRATOR:** You put your hand over hers on the stone. She lets it stay
there for a count of three.

**KEEGAN:** I am on duty. (She takes her hand back. Then, without looking,
she puts it back, under yours, for another count of three.) ...That was
anaphora. Doing the same thing twice for emphasis. Goodnight.

→ end

### `keegan.supper_end` **(new)**

**KEEGAN:** Goodnight. (As you go:) It was good for morale. Mine. I checked.

→ end

---

### `keegan.say_risen` *(existing, unchanged)*

The sign (`keegan.saw_risen`). "...I've got to go and read something." In
this arc it is the first contraction the player can hear her notice herself
making.

---

## Act 2

### `keegan.ask` **(new: chapter four; Act 2 beat 2)**

**Entry:** Act 2 beat 2. If `keegan.supper` is set, she asks it on the wall
at night, alone; otherwise at the gate by day, in front of the Watch (the
Act 2 writer's main scene). The romance text is the private version.

**NARRATOR:** She's sitting on the old stone, the one the gate was built on,
which she told you never to sit on. She has the handbook open in her lap.
She doesn't stand up when you come.

**KEEGAN:** I am going to ask you something, and I am going to ask it
plainly, because chapter four is very clear that I should ask it at sword's
length and I find I do not want to. (She closes the book on her finger.)
Did you die on the Low Ford road?

Choices:
- "I think so. I don't remember it." → `ask_truth`
- "No." → `ask_lie`
- "(Say nothing.)" → `ask_silence`

### `keegan.ask_truth` **(new)**

**Effects:** set `keegan.asked` = `truth`; rel `keegan` trust +30.

**KEEGAN:** (She lets out a long breath.) Thank you. (She looks at the book,
not at you.) I knew. I have known since they carried you into the shrine
under a sheet and you walked out of it. I hoped. Hope is a figure of speech.
It is called... I cannot remember what it is called. I have been a lecturer
in rhetoric for seven years and I cannot remember what it's called.

- `[when rel keegan trust >= 40]` → `ch4_read`
- `[otherwise]` *(adds)* I must think. I am going to write to the
  chapterhouse. (A pause.) I am going to write to them, and then I am going to
  come north a day behind you, to supervise. → end; `keegan.route` = `behind`.

### `keegan.ch4_read` **(new: chapter four, read aloud)**

**Effects:** set `keegan.ch4_read`; `keegan.route` = `north`.

**KEEGAN:** Sit down. Not on that. Here. (She opens the book.) I am going to
read you chapter four. I have never read it aloud. It is not long. I think
you have a right to hear it, and I think I have a duty to read it, and I am
not certain those are the same thing.

**NARRATOR:** She reads by the gate lamp, in her lecturer's voice, every
word in its place.

**KEEGAN:** "Of the Unchained, and Their Return to the Dark. One. The
Unchained is the likeness of the one who died, and walks in their shoes, and
knows their friends. The knight shall not be deceived by this. Two. It burns
at night and is ordinary by day, and it comes back from death more often
than the living do. Three. The knight shall not converse with it beyond what
is needful. ..." (She stops. She reads three again, to herself, and goes on.)
"Seven. The return shall be made at dawn, when it is weakest, with a blade
the knight has kept clean. Eight. The knight shall make the return kindly,
for it was a person once. Nine." (She stops.)

Choices:
- "What's nine?" → `ch4_nine`
- "(Wait.)" → `ch4_nine`

### `keegan.ch4_nine` **(new)**

**KEEGAN:** "Nine. The knight shall not grieve." (She looks at the page for a
long time. Then she folds the corner of it down, carefully, the way you mark
a place you mean to come back to.) I am not going to tear it out. It is a
library book. ...I'm coming north with you. Not for you. With you. I would
like that to be clear. It's not clear. I know it isn't.

- "It's clear enough." → end
- "Keegan. You don't have to." → **KEEGAN:** I have read chapter four. I know
  exactly what I do not have to do. → end

### `keegan.ask_lie` **(new)**

**Effects:** set `keegan.asked` = `lie`; rel `keegan` trust −30.

**KEEGAN:** (She looks at you for a long time.) No. (She writes something in
the margin of the handbook. You can't see what.) Very well. Then you may
pass, and I shall stay at my gate, and we shall both be what we say we are.
Good night.

→ end. The romance is closed until Silverstair, where she reads the truth in
Sallow's ledger in Ysolde's hand, and then it is closed for good:

**At the gate (the night duel, Act 2 writer)**, if the survivor spares her:
**KEEGAN:** (On her knees, the sword gone.) Do not call me Keegan. Call me
Dame Orme. (She tries to stand and can't, quite.) I should like to have been
somebody's Dame. Once. Properly. Go on.

### `keegan.ask_silence` **(new)**

**Effects:** set `keegan.asked` = `silence`; rel `keegan` trust −5.

**KEEGAN:** (She waits. Then she nods, once.) Silence is an answer. Chapter
two. "Aposiopesis: the breaking off of speech, that says more than speech."
...I know what it says. (She stands.) I'm coming north. A day behind you. To
supervise. (She goes. She says "I'm" and doesn't notice.)

→ end. `keegan.route` = `behind`. The route can open on the road
(`north_camp` with trust ≥ 40).

---

### `keegan.north_camp` **(new: the road north)**

**Entry:** `keegan.route` in (`north`, `behind`), Act 2, a night camp on the
north road. Plays once; `once:camp`.

**NARRATOR:** A roadside chapel with half a roof, older than the Vigil, the
lamp-niche over its altar cold. She has unrolled her blanket on one side of
the nave and laid yours on the other, as far apart as the walls allow, and
she has drawn a line in the dust between them with the point of her sword.

**KEEGAN:** That is a line. (She sits on her side of it, cross-legged, in
full armour, as if that were comfortable.) It is a symbolic line. Chapter
eleven does not cover symbolic lines, and so I am covering them.

Choices:
- "Does chapter eleven cover anything useful?" → `camp_eleven`
- "(Cross the line.)" `<when rel keegan affection >= 40 and rel keegan trust
  >= 50 and keegan.ch4_read>` locked: *Not yet. She drew it for a reason.* →
  `camp_cross`
- "Goodnight, Keegan." → `camp_night_alone`

### `keegan.camp_eleven` **(new)**

**KEEGAN:** It covers dinner, drink, dancing, the exchange of tokens, and
"the closer acquaintance". It forbids all of them to a knight of the Vigil on
campaign. (A pause.) I have looked, very carefully, and there is nothing in
chapter eleven about a knight who is no longer certain she is of the Vigil.
I have decided to regard that as an oversight.

→ back to `north_camp` choices

### `keegan.camp_night_alone` **(new)**

**NARRATOR:** She lies down on her side of the line in her armour. In the
night you hear her say, very quietly, to the roof, "That was cowardice. It
has no figure. It doesn't need one." → end.

### `keegan.camp_cross` **(new: the lead-in)**

**NARRATOR:** You step over the line. She watches you do it, and doesn't
stop you, and doesn't move.

**KEEGAN:** You have crossed the line. (Her voice isn't quite level.) I drew
it to see whether you would. I didn't know which I— (She hears it. She shuts
her eyes.) I did not know which I wanted.

**NARRATOR:** She starts on the armour herself: gauntlets first, then the
vambraces, laid side by side on the flagstones with a care that is almost
funny and then isn't. She gets as far as the first buckle of the cuirass and
stops, hands on it.

**KEEGAN:** If I am wrong about everything, I would like to be wrong about
this on purpose. (She looks up.) Are you sure? You may say no. I would like
it to be said that you could say no. I would like— are you *sure*?

Choices:
- "I'm sure. Are you?" → `camp_sure`
- "No. Not tonight." → `camp_no`

### `keegan.camp_no` **(new: the survivor refuses, kindly)**

**KEEGAN:** (A long breath out, of great relief and some disappointment, in
about equal measure.) Oh, thank God. (She laughs, which surprises her.)
I mean— no. I mean thank you. Both.

**NARRATOR:** She sleeps in her cuirass on your side of the line, with the
gauntlets and vambraces lined up between you like a third person who has
been told to behave. → end. Rel `keegan` trust +10. The scene may be
offered again on a later night.

### `keegan.camp_sure` **(new)**

**KEEGAN:** (She thinks about it. She actually thinks about it, visibly,
like a lecturer marshalling a point.) Yes. (Then, with enormous relief at
having found the word:) *Yes.* Help me with this buckle; it was made by a
man who hated women.

→ `night`

---

### `keegan.night` **(new; slot 4)**

**Effects:** set `keegan.lover`; rel `keegan` affection +15, trust +10;
condition `warmed` 1 day; `night.spent`.

**NARRATOR:**
- `[when settings.intimacy == "full"]` `[explicit scene: Keegan and {name},
  a roofless roadside chapel on the north road at night, a cold lamp-niche
  over the altar and the north sky through the roof; the armour coming off a
  buckle at a time and laid out in order; earnest and nervous, then not; she
  cites chapter eleven once and then stops citing anything; her contractions
  slipping one by one until there are none of her rules left — to be
  written]`
- `[when romance.eve == keegan]` → see `eve_night` below.
- `[otherwise]` The armour comes off a buckle at a time and is laid out on
  the flagstones in order, cuirass, tassets, greaves, as if for inspection;
  she won't be hurried about it, and then, at the last buckle, she will. Under
  it she is long and pale and bruised in neat bands where the straps sit, and
  she watches your face as you see that, ready to be embarrassed, and isn't.
  She's earnest about all of it at first, the way she's earnest about
  everything, and asks you things in a lecturer's voice that comes out not
  at all like a lecturer's, and laughs at herself, and then stops asking.
  The north sky goes over through the hole in the roof. Somewhere in the
  night she says, against your mouth, "I don't— I can't remember a single
  rule," and she sounds delighted.

→ `night_morning`

#### Beat sheet for slot 4: `keegan.night`

- **Mood and pacing.** Earnest, then nervous, then neither. Comic at the
  edges (the armour, the buckle "made by a man who hated women", the line in
  the dust), never at her expense. A long, ordered undressing that is half
  ritual and half stalling, then a point where she stops stalling. After
  that it should be warm, and surprising to her, and the comedy goes.
- **What she wants.** To choose something for herself, on purpose, against
  a book she has lived by. To be touched as a person and not as a probationer.
- **What she fears.** Being wrong. Being right (chapter four). Being funny,
  when she doesn't want to be. Being bad at this, which she is not.
- **What the survivor wants.** Her, without the bracket.
- **What the survivor fears.** That they are what chapter four says, and that
  she'll remember it at dawn.
- **Consent, on the page.** She asks "Are you sure?" and the survivor says
  yes and asks her the same, and she says yes as a decision, not a lapse.
  Inside the scene she keeps asking, in lecturer's grammar going to pieces,
  and the asking is part of what is tender about it.
- **The emotional turn.** The contractions. On duty she has none. She starts
  the scene with none. One slips; she notices. Another; she doesn't. By the
  end she has no rules left and says so, and is delighted. That is the turn.
- **Callbacks.** Chapter eleven, paragraph six ("for the purposes of
  morale"). The line in the dust. The bath she's never allowed (chapter
  nine, "a lamp and not a garden"; if a callback is wanted: "Garden," she
  says, at some point, and laughs). Her neat strap-bruises. The lamp-niche,
  cold, over the altar; chapter four's "at dawn, when it is weakest".
- **Sex variants.** Same beats either way. If the survivor is a woman, she
  may cite chapter eleven's total silence on the subject, as an oversight.
- **Ends on.** Before dawn, awake, her ear against the survivor's chest,
  waiting to hear whether the heat goes out of them at first light, because
  she has read chapter four and knows the hour. It does. She holds on.

### `keegan.night_morning` **(new: the armour back on)**

**NARRATOR:** First light. She's awake; she has been for a while. Her ear is
on your chest. You feel the heat go out of you, all at once, like a lamp
turned down, and you feel her feel it. She doesn't move.

**KEEGAN:** (Very quietly.) "At dawn, when it is weakest." (She lifts her
head.) It's just a sentence. It's only a sentence. I've marked worse
sentences in red.

**NARRATOR:** She gets up and starts putting the armour back on, in order,
and as each piece goes on, her voice changes. You can hear it happen.

**KEEGAN:** (Greaves.) I don't regret it. (Tassets.) I don't— I do not regret
it. (Cuirass. She does the buckle that was made by a man who hated women
without any help at all.) I do not regret it, and I would like that entered
in the record. ...Good morning. It is a good morning. Is it not.

Choices:
- "It is." → end
- "Say it like you said it last night." → **KEEGAN:** (She goes pink to
  the ears.) I'm on duty. (A pause.) ...I'm. Oh, for— Good *morning*. →
  end

---

### `keegan.oath` **(new: Silverstair; Act 2 beat 10)**

**Entry:** `keegan.lover`, at Silverstair, in Sallow's presence (Act 2
writer's scene). The romance beat inside it:

**NARRATOR:** Sallow is courteous. He has a sword on a cushion, the
Lord-Exchequer's own, and a page in the ledger with her name on it, and a
space where the bracket goes.

**SALLOW:** Dame Keegan. Kneel, and I'll strike it out myself. "Probationary".
Gone. Confirmed, at last, by the hand of the order you've served so
faithfully, for so little. All I ask in return is the one from the ford.
I do apologise. It's a small thing.

**NARRATOR:** She looks at the sword. She looks at it for a long time. It is
the thing she has wanted most in the world, for as long as you have known
her. Then she turns her back on it, and on him, and kneels in front of you.

**KEEGAN:** You do it. (She bows her head.) With whatever you carry. It
doesn't matter what. Chapter four says I should not ask this of you. I have
read chapter four. ...Please.

Choices:
- "(Touch her shoulder with your blade.) Dame Keegan." → `oath_done`
- "Get up. You don't need anyone's blade." → `oath_up`

### `keegan.oath_done` **(new)**

**Effects:** set `keegan.oath` = `broke`; rel `keegan` affection +15.

**NARRATOR:** Your blade touches one shoulder, then the other. She stands up.
She doesn't look at Sallow at all.

**KEEGAN:** (To you, with no bracket in it anywhere.) Dame Keegan. (Then, to
the room:) Of the Argent Vigil. As it was meant to be.

→ (the Act 2 writer's scene goes on)

### `keegan.oath_up` **(new)**

**Effects:** set `keegan.oath` = `broke`; rel `keegan` respect +15.

**KEEGAN:** (She stays on her knees a moment longer. Then she gets up, by
herself.) No. I don't. (She sounds surprised.) Chapter one. "A knight is made
by what she keeps." I have kept quite a lot. ...Let's go.

---

### `keegan.eve` **(new: the night before the gate)**

**Entry:** `romance.eve` = `keegan`.

**KEEGAN:** I have not slept in two days. I am going to stand at a gate
tomorrow against the order I swore to, beside the one person chapter four
says I should be standing against, and I haven't slept in two days, and I
don't want to sleep now. (She takes off a gauntlet.) I don't want to waste
it.

Choices:
- "(Take the other gauntlet.)" → `eve_night`
- "Sleep. I'll watch." → `eve_watch`

### `keegan.eve_night` **(new; desperate variant of slot 4)**

**NARRATOR:**
- `[settings.intimacy == "full"]` `[explicit scene: Keegan and {name}, the
  gatehouse room over the north gate the night before Sallow's people come;
  no ceremony this time, the armour shed in a heap; desperate and wakeful,
  neither wants to sleep and waste it; at the end she lies awake reciting
  something under her breath, and it isn't the handbook — to be written]`
- `[otherwise]` No ceremony tonight. The armour comes off in a heap on the
  floor of the gatehouse, and she kicks a greave across the room and
  doesn't go after it. She is fierce, and wakeful, and won't let either of
  you sleep. Near dawn she lies with her ear on your chest, waiting, and
  murmuring something under her breath, over and over. It isn't the
  handbook. It's your name.

`eve_watch`: **NARRATOR:** She lies down with her head in your lap, in full
armour, which is absurd, and is asleep in four breaths. She doesn't wake
until the horns. → end.

---

## Act 3 (outline)

### On the stair

She walks down beside the survivor with a lamp, through the Legion's dead,
who part for the survivor's light and not for hers. They let her through
anyway, because she's holding the survivor's hand. She notices this, and
says, "Chapter four says nothing about this either. I'm going to write a
chapter."

### Ends, as lover

- **Re-founds the Vigil**: its handbook has a new chapter four: "Of the
  Unchained, and Their Keeping." The survivor's name is the first word of it.
- **Dies at the gate**: the eve was hers, so the scene before it is the
  last. The epilogue: *Dame Keegan of the Argent Vigil. No bracket.*
- **Ending A, the survivor in the chain**: she stands at the top of the
  stair with a lamp, for the rest of her life. *The Vigil, as it was meant to
  be.*
- **Ending B, the survivor gone dark at dawn**: she has read chapter four
  enough times to know the hour, and holds on through it.
- **Ending C, the new god**: she kneels, and it's the worst moment of her
  life. The survivor can say "Get up." She gets up, and leaves the valley, and
  writes a new chapter four, and it is about them.
