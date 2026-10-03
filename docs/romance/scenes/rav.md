# Rav Cutwell: the scenes

Every beat of Rav's arc (`../ARCS.md` §4) as playable dialogue. Act 1's
`back_room` and `came_back` are also drafted as data in `../data/rav.json`.
The notation is `sella.md`'s.

Voice check: gravel and cant; "pal"; a doctor's frankness about bodies; a
half-drunk music. Funny about everything except his brother, whom he
**never names** (the one exception is spent: `cb_killed_redcowl`). Never
sentimental. Never says no to a drink (this arc proposes spending that
"never" once, at `sober`; see ARCS §8.1). Reaches for his mother when
something is unbearable, as Redcowl does.

---

## Act 1

### `rav.pain` *(existing, unchanged)*

**RAV** *(existing)*: Where? ...No, don't point, pal, we're in company. Come
round the back after closing and I'll take a look. Largely professionally.
Bring a bottle; it's an anaesthetic for one of us.

---

### `rav.back_room` **(new: round the back, after closing)**

**Offered on `hub`:** "(Go round the back after closing.)" `<show time night
and npc flag rav once:pain>` `<when rel rav trust >= 20>` `once:back_room`.
**Effects:** set `rav.back_room`; rel `rav` affection +5, trust +5.

**NARRATOR:** Behind the Crooked Flagon there's a lean-to with a lamp, a
scrubbed table, a shelf of jars (one of them moving), and a sail-needle
stuck in a cork like a trophy. Rav is sitting on the table with his feet on
a stool and two cups already poured.

**RAV:**
- `[when condition wounded]` There you are. You're bleeding on my floor, pal,
  which is at least honest. Up on the table. No, the *table*. Drop your
  trousers or don't; I'm going to need the leg either way.
- `[otherwise]` You came. (He looks faintly alarmed about it.) Right. Up on
  the table. Breathe in. Out. Don't flatter yourself, that's medical.

**NARRATOR:**
- `[wounded]` He cleans it with something that takes the skin off your
  thoughts, and stitches it with the sail-needle in small neat rows, talking
  the whole time: about leeches, about Holloway's feet, about a man in the
  Kerchiefs who sharpened his teeth for a joke. His hands are perfectly
  steady. He has had three cups.
- `[otherwise]` He looks at your eyes, and your tongue, and your hands,
  turning them over the way Sella does, but for different reasons. He
  listens at your back with his ear flat against it and tells you to cough.
  He's quiet for a moment.

**RAV:**
- `[wounded]` There. That'll scar like a love bite. Tell folk it was one.
- `[otherwise]` There's nothing wrong with you, pal. (He frowns at your
  wrist, then lets it go.) ...That's the worrying part. Nobody's got nothing
  wrong with them. Have a drink, before I find something.

Choices:
- "Is this the anaesthetic?" → `back_room_drink`
- "(Kiss him.)" → `back_room_kiss`
- "Thank you, Doctor." → `back_room_end`

### `rav.back_room_drink` **(new)**

**RAV:** For one of us. (He drinks his, then looks at yours.) Both of us,
evidently. ...Go home, pal. You've got a job up the Old Road and I've got a
bad habit of liking folk who've jobs up the Old Road.

→ end

### `rav.back_room_kiss` **(new: a refusal, kindly)**

**NARRATOR:** He lets you, for a moment. He tastes of the Flagon's piss and
something under it, cloves. Then he puts a hand flat on your chest and moves
you back a foot, gently, the way he'd move a patient.

**RAV:** Not yet, pal. Not three cups down, and not while you're still
needing things off me: keys, ways in, who's who up the Old Road. (He picks
up his cup.) Ask me again when you've stopped needing anything. I'll be
here. I'm always here. That's the other worrying part.

**Effects:** rel `rav` affection +5.

→ end

### `rav.back_room_end` **(new)**

**RAV:** "Doctor." (He snorts.) Get out of my surgery.

→ end

---

### `rav.came_back` **(new: the day after)**

**Entry:** npc flag `rav` `cb:killed_redcowl` set, and this is the next
visit after it (npc flag `came_back` not set). Before `hub`.
**Effects:** set `rav.came_back`; npc flag `came_back`; rel `rav` trust +15.

**NARRATOR:** He's at his table. He's sober, or near it. He's shaved.

**RAV:** You came back. (He looks at you for a long time.) Most folk
wouldn't. Most folk would drink at Rook's for a month and hope I'd died of
it. ...Sit. I'll not talk about it if you don't. I'm a doctor today. What's
wrong with you?

Choices:
- "Nothing. I came to sit." → **RAV:** (A breath out through his nose.)
  Aye. Well. Sit, then. → `hub`
- "I'm sorry." → **RAV:** No. You're not, and you shouldn't be; he'd have
  said it was the job. Don't say it again, pal. I'll not be able to hear it
  twice. → `hub`

---

## Act 2

### `rav.bird` **(new: the little bird; Act 2 beat 7)**

**Entry:** after the Act 2 scene where Redcowl, come to the Waystation with
his army, tells the survivor about the little bird, laughing. Rav finds the
survivor that night.

- `[when redcowl.birds and not rav.bird]` (the survivor guessed it in Act 1
  and never told anyone):

**RAV:** He told you. Course he did; he tells everyone everything when he's
winning. (He sits down heavily.) Except he didn't tell you, did he. You
knew. Since the Roost. He says you guessed it off one line about a bird and
a seam, and you've sat at my bar every night since and never sold it. (He
stares at his cup.) In this valley. Do you know what that's worth, pal? No.
Neither do I. Nobody's ever priced it.

**Effects:** set `rav.bird` = `kept`; rel `rav` trust +25.
→ end

- `[otherwise]`:

**RAV:** So now you know. I gave him the night the wagons came. I took the
clerk's key off the clerk myself, and gave it you, and said I found it on a
stool. (He drinks.) I'm ashamed of all of it. I'd do it again tomorrow.
...Go and tell Holloway, if you're going to. I'll be here.

Choices:
- "I'm not going to tell Holloway." → set `rav.bird` = `kept`; trust +15. →
  **RAV:** ...Huh. (That's all.)
- "(Say nothing.)" → no change.

**If the survivor tells Holloway** (Act 2 writer: a choice on `holloway`):
set `rav.bird` = `told`. Rav's next greeting, for good:
**RAV:** (He buys you a drink, sets it down in front of you, and moves to a
different stool.) → end.

---

### `rav.back_room2` **(new: the lead-in; the pulse)**

**Offered on `hub`:** "(Go round the back after closing.)" again, Act 2,
`<show rav.back_room and rav.bird != told>` `<when rel rav affection >= 30 and
rel rav trust >= 40>` locked: *He'd buy you a drink. That's all, yet.*

**Variant: too drunk.** The first time it's chosen, if `not npc flag
said:remember`:

**NARRATOR:** He's on his fifth. You can tell because he's singing, and
he only sings on his fifth.

**RAV:** You came back round. (He tries to stand up and thinks better of
it.) No. Not like this, pal. I'd like to remember it. (A pause, horrified.)
...Christ, did I say that out loud.

Sets npc flag `said:remember`. → end. (The next time, it goes on.)

**Variant: his brother is dead by the survivor's hand** (`history
killed_redcowl`), before anything else:

**RAV:** Before you sit down. (He's sober. He has been all day; you can see
what it cost.) I know what you did. I'm not asking you to be sorry. I'm
asking you not to talk about him. Not in here. Not tonight. Can you do that?

Choices:
- "I can." → on
- "No. Not like this." → **RAV:** Aye. Fair. (He pours two, and pushes one
  across, and that's the night.) → end. No change.

**Main text:**

**NARRATOR:** The lean-to, the lamp, the jar that moves. He doesn't make you
get on the table this time. He sits on it himself and you stand between his
knees, and he talks, the way he always talks: nonsense, cant, a story about
a bishop and a goat. He takes your hand while he's talking, the way he'd
take any patient's, and turns it over, and his two fingers settle on the
inside of your wrist, out of habit.

**NARRATOR:** He stops talking.

**NARRATOR:** You can see him counting. His lips move. Four. Seven. Nine.
Nothing under his fingers. Eleven. Then there it is, a single slow beat,
like somebody knocking on a door very far away, and then another, faster,
and then your pulse is going like a hare's.

**RAV:** (Very quietly, in a voice you've never heard him use, the bedside
voice under the cant.) ...Your heart stopped, pal. (He doesn't let go.) For
a count of eleven. And now it's going again. (He looks up at you.) Christ.

Choices:
- "(Let him hold it.)" → `back_room2_hold`
- "(Pull your wrist away.)" → `back_room2_pull`

### `rav.back_room2_pull` **(new)**

**NARRATOR:** He lets you go at once. He doesn't say anything about it, then
or after. He picks up his cup and puts it down again without drinking.

**RAV:** Right. (Lightly.) Doctor's finished. ...You can stay, if you want.
You can go. Both's allowed.

Choices:
- "(Stay.)" → `night`
- "(Go.)" → end

### `rav.back_room2_hold` **(new)**

**Effects:** set `rav.felt_pulse`; rel `rav` trust +10.

**NARRATOR:** He holds it. He holds it a long time, counting under his
breath, until he's sure it isn't going to stop again. Then he lifts your
wrist and puts his mouth to the place his fingers were.

**RAV:** I'm not going to ask. (Against your skin.) I'm a doctor. I know when
not to ask. ...Stay.

Choices:
- "(Stay.)" → `night`
- "(Not tonight.)" → **RAV:** (He lets go.) Aye. Fair. Mind the step. → end.

---

### `rav.night` **(new; slot 5)**

**Effects:** set `rav.lover`; rel `rav` affection +15, trust +10; condition
`warmed` 1 day; `night.spent`.

**NARRATOR:**
- `[when settings.intimacy == "full"]` `[explicit scene: Rav and {name},
  the back room of the Crooked Flagon after closing, a lamp, a scrubbed
  table, the jars on the shelf; funny and frank until his fingers find the
  survivor's wrist; then the first silence in his life, and he stays in it
  — to be written]`
- `[when history killed_redcowl]` **(grieving)** He doesn't talk. That's
  the first strange thing, and the second is how gentle a man can be who
  sews legs back on with a sail-needle. He keeps the lamp lit. Once, in the
  middle of it, he stops, and puts his forehead down on your shoulder and
  stays there, breathing, and you hold the back of his head, and he lets
  you, and then he goes on. You don't talk about anyone. Afterwards he lies
  on his back on the floor of the lean-to, on a blanket that smells of
  camphor, with your wrist in his hand. Every so often, all night, you feel
  him check.
- `[otherwise]` He talks for a while, out of habit: frank, filthy, funny,
  a doctor's running commentary on what he's going to do and why it's good
  for you. Then he doesn't talk at all, and that turns out to be the
  frankest thing he's ever done. He's slow, and sure, and his hands know
  exactly where everything is, and he laughs once, low, against your neck,
  at nothing. Afterwards he lies on his back on the floor of the lean-to,
  on a blanket that smells of camphor, with your wrist in his hand. Every so
  often, all night, you feel him check.

→ `sober`

#### Beat sheet for slot 5: `rav.night`

- **Mood and pacing.** Funny first: his patter is a doctor's, frank about
  bodies, and the comedy is his way of being kind. The middle goes quiet,
  and stays quiet; for a man who has never once stopped talking, silence is
  the intimacy. Unhurried, practised, warm. An older man's body and an
  older man's lack of vanity about it; the scene should not hide his age.
- **What he wants.** To stop counting, for one night. Not to want anything,
  and failing that, to want this.
- **What he fears.** Being sober with someone. Sentiment. That the heart
  under his fingers will stop again, and that he's falling for someone who
  isn't entirely alive.
- **What the survivor wants.** Him, and the quiet he finds.
- **Consent, on the page.** He states it plainly at the start, a doctor's
  consent ("Tell me if anything's no. I'll stop. I'm fifty-three, pal; I'm good at stopping. I've
  stopped drinking four times."), and means it. He checks in, in his voice,
  as part of the patter, and the patter stopping isn't a lapse: he's
  listening instead.
- **The emotional turn.** His fingers find the survivor's wrist again in
  the middle of it, out of habit, and he counts, and it's racing, and he
  laughs into their neck with relief, and from then on he doesn't talk.
  (Grieving variant: the forehead on the shoulder.)
- **Callbacks.** "Drop your trousers or don't." The sail-needle. The jar
  that moves. "Largely professionally." "I'd like to remember it." The
  count of eleven.
- **Sex variants.** Same beats either way. Rav is an equal-opportunity
  doctor and says so ("I've seen everything. Twice. Under worse lamps.").
- **Ends on.** Him on his back on the camphor blanket, the survivor's wrist
  in his hand, checking, all night.

### `rav.sober` **(new: the morning; the one "no" to a drink)**

**NARRATOR:** Morning, grey through the cracks of the lean-to. He's sitting
on the table, dressed, with the bottle in one hand and a cup in the other.
He pours. He looks at it.

**RAV:** No. (He puts the cup down.) ...No, I'll keep this one.

> **The exception.** "Never says no to a drink" (VOICES.md). If the author
> spends it here, nothing else may. If not, write it as: he pours it, and
> holds it, and is still holding it when the survivor leaves.

Choices:
- "Keep what?" → **RAV:** You know what. Don't make me say it sober, pal;
  I've a reputation. → end
- "(Kiss him.)" → **NARRATOR:** He tastes of nothing at all, for once. → end

---

### `rav.hat` **(new: the red hat; Act 2 beat 7, Redcowl dead)**

**Entry:** the Act 2 scene where Rav goes to the Roost and takes the hat.
The romance beat inside it.

**NARRATOR:** The Roost's fire. Forty-one faces. The red hat on a stump in
the middle of them, where it was put the night they heard. Rav picks it up,
turns it in his hands, and puts it on. It fits.

**RAV:** Our mother'd have laughed herself sick. (Nobody laughs. He looks
round at them, and at you.)
- `[when rav.lover or rel rav affection >= 40]` I'm taking them to the north
  gate. All of them. To stand beside the one who put him in the ground.
  (He says it to the Kerchiefs, not you.) Anybody wants to argue, argue with
  me, and I'll stitch you up after. ...There's a place at this fire for you,
  pal. If you want it. You don't have to want it.
- `[otherwise]` The Roost'll look after its own. Same as ever. (To you,
  quieter:) Go on home, pal. This isn't your fire.

**Effects:** set `rav.hat`; with the first variant, the Kerchiefs fight
beside the survivor at the north gate (bible §7.7).

---

### `rav.hanging` **(new: hanged for the tip-off)**

**Entry:** Act 2, when the Watch learns who gave Redcowl the date (Harlan
exposed and wanting someone hanged for Jory's cage; or `rav.bird` = `told`).

**HOLLOWAY:** (Act 2 writer.) Somebody gave the Kerchiefs the night. I need a
name for the rope.

Choices (the romance's):
- "I did. I sold the date." `<show rav.lover>` → `hang_took`
- "He's a doctor. You need him more than a rope." → (Act 2 writer: a
  respect check on Holloway)
- "(Say nothing.)" → the bible's end: Rav hangs.

### `rav.hang_took` **(new)**

**NARRATOR:** (Holloway looks at you a long time. He doesn't believe you, and
he writes it down anyway; it's a name, and it's a short list in a town this
size.) Later, in the cells, Rav comes down the stairs with a bottle.

**RAV:** You stupid— (He's white with fury. His hands are shaking, and they
never shake.) You stupid, stupid— Who asked you? Who *asked* you? (He sits
down on the floor outside the bars, hard.) ...Our mother'd have liked you.
God help you. (He uncorks the bottle with his teeth, and passes it through
the bars, and doesn't take any himself.)

> The Act 2 writer decides what it costs the survivor (a night in the cells;
> a fine; Holloway's respect). Rav does not hang.

**If Rav hangs** and the survivor was his lover: the night before, in the
cells. Not a love scene. He spends it making them laugh, and tells the
bishop-and-goat story to the end for the first time. At the end: "There.
Now somebody knows how it finishes."

---

### `rav.eve` **(new: the night before the gate)**

**Entry:** `romance.eve` = `rav`.

**RAV:** (In the lean-to, sober, the hat on the table if he has it.)
Tomorrow I'm going to be stitching people up on a wall till my hands give
out. Tonight I'd like my hands for something else. (A pause.) That was
nearly sentimental. Strike it out.

Choices:
- "(Take his hands.)" → `eve_night`
- "Sleep. You'll need your hands." → **RAV:** Aye. Doctor's orders. Mine.
  (He sleeps with his head on your chest, and wakes once, and checks your
  wrist, and sleeps again.) → end

### `rav.eve_night` **(new; desperate variant of slot 5)**

**NARRATOR:**
- `[settings.intimacy == "full"]` `[explicit scene: Rav and {name}, the
  back room the night before the war, the red hat on the table if he took
  it; sober, unhurried on purpose, a doctor memorising a body he means to
  patch tomorrow — to be written]`
- `[otherwise]` He's sober, and slow, and it's on purpose. He goes over you
  as if he were learning you by heart, every old scar, every new one,
  frank and tender, telling you which ones he'd have stitched better. You
  laugh. He doesn't stop. Afterwards he says, "There. Now I'll know where
  everything goes, if I've to put it back," and he isn't joking, and he
  isn't sentimental, and he's both.

---

### Ends, as lover

- **Stays the town's doctor**: *A second glass on the Flagon's bar that
  nobody else may use. He pours it every night, and doesn't drink it, and
  nobody asks.*
- **Takes the red hat**: *The doctor leads the Kerchiefs. There's a place at
  the Roost's fire for you, if you want it.*
- **Hanged for the tip-off**: *Somebody knows how the story of the bishop
  and the goat finishes. It's you.*
