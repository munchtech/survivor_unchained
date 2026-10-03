# Ysolde Marrow, the Wayfinder: the scenes

Every beat of Ysolde's arc (`../ARCS.md` §5) as playable dialogue. Her
conversation id is `wayfinder`. Her route is all Act 2, so it is drafted as
script only. Act 1 gets two small number changes (§Act 1). The notation is
`sella.md`'s.

Voice check: brisk, bookish, gallows humour; Edinburgh; contractions. She
talks of the dead as entries in a margin. Precise about maps, vague about who
buys her notes, until she confesses, and after that never vague again. She is
in her fifties; Edric, her brother, has been risen twelve years.

**The rule the route keeps:** "never while she is selling you" (bible §11).
Nothing in this file opens before `wayfinder.confessed`.

---

## Act 1 (numbers only)

- `wayfinder.margin_name` *(existing)*: add rel `wayfinder` affection +5.
  ("I'm a tidy woman." Being given a real name pleases her more than she
  shows.)
- `wayfinder.t_wayfinder` *(existing)*: add rel `wayfinder` trust +5.

Neither is a romance beat. They are the two things she will remember.

---

## Act 2

### `wayfinder.confess` **(new: back from Silverstair)**

**Entry:** after Silverstair (bible §7.10), the first visit to her table,
when the survivor has seen their entry in Sallow's ledger. Sets
`wayfinder.confessed`.

**NARRATOR:** Her table, her maps, her pen. She sees your face and puts the
pen down, cap on, which she never does mid-word.

**YSOLDE:** You've been to Silverstair. (Not a question.) You've read the
ledger. It's a lovely ledger; he has it bound in calf. And you've found
yourself in it, in a hand you know.
- `[wayfinder.name == given]` "{name}. From the Low Ford. Risen the night the
  Warden woke. Comes back more often than most." I wrote that. I was proud of
  "more often than most". It scans.
- `[wayfinder.name == nobody]` "Nobody. From the Low Ford. Risen the night
  the Warden woke." I thought that was funny, at the time.
- `[wayfinder.name == false]` "Lark. From the Low Ford." (She almost smiles.)
  He's had six men out looking for a Lark for a month. That's the one entry
  I'm not sorry for.

Choices:
- "You sold me." → `confess_sold`
- "(Say nothing. Wait.)" → `confess_wait`

### `wayfinder.confess_sold` **(new)**

**YSOLDE:** I did. (She doesn't look away.) Every name that came back off my
maps, for twelve years. Collectors, scholars, a gentleman in the north who
likes silver ink. That was the truth; I just didn't tell you what he
collected. (A breath.) My brother came out of the barrow in the Morrow hills.
I told you he didn't. He did. He came out, and he knew me, and the Vigil
came for him in a week. Edric. He's in a silver cage at Silverstair, and he
eats because I write. That's the whole entry. Margin's full.

Choices:
- "I've seen him. Cage nine." `<show the survivor saw Edric at Silverstair>`
  → **YSOLDE:** (Very still.) ...How did he look? (Then, before you can
  answer:) No. Tell me after. Tell me after you've decided what to do with
  me. → back
- "I forgive you." → `confess_forgive`
- "We're done, Ysolde." → `confess_cold`
- "Then you owe me. The way in, and the way out." → `confess_use`

### `wayfinder.confess_wait` **(new)**

**NARRATOR:** You say nothing. She waits too. She is better at it than most
people; she has sat at this table a long time. Then she picks up the pen,
uncaps it, and caps it again.

- `[when edric.freed]` **YSOLDE:** You opened the cages. (Her voice goes.) You
  opened them, and you knew whose hand had put you on his list, and you
  opened them anyway, and you've come here and said nothing. (She puts both
  hands flat on the map.) I sold you. I'd do it again for him. I'll never do
  it again. Both of those are true. ...There. That's the whole entry.
  → `confess_forgive` with trust +25 in place of +20 (forgiveness earned on
  both sides).
- `[otherwise]` → `confess_sold`

### `wayfinder.confess_forgive` **(new)**

**Effects:** set `wayfinder.forgiven` = `forgave`; rel `wayfinder` trust +20.

**YSOLDE:** (She looks at you as if you were a coastline she'd been drawing
wrong for years.) Well. That's a margin I don't have a word for. (She takes
a fresh sheet and writes something at the top of it, and turns it round to
show you. It says your name, and nothing under it.) I've stopped. The last
one I sent was a Lark. I'll send him Larks till the ink runs out, if you
like.

Choices:
- "Send him Larks." → set `wayfinder.double`; → **YSOLDE:** (A real smile,
  sharp as a nib.) Oh, I'll enjoy that. → end
- "Don't send him anything." → **YSOLDE:** Then I'll send him nothing, and
  he'll notice, and come. Let him. → end

### `wayfinder.confess_cold` **(new)**

**Effects:** set `wayfinder.forgiven` = `cold`. The route is closed. If
`edric.freed` is set later, `twelfth` may open once, slowly (§below).

**YSOLDE:** (She nods.) That's fair. That's the fairest thing anyone's said
at this table. (She uncaps the pen and goes back to her map, and her hand is
perfectly steady, and she doesn't draw anything.)

→ end

### `wayfinder.confess_use` **(new)**

**Effects:** set `wayfinder.forgiven` = `use`; rel `wayfinder` respect +15,
affection −10.

**YSOLDE:** I do. (Brisk, at once, almost relieved.) The way in is the
servants' stair on the east side; the Vigil don't count servants. The way out
is whatever's left. Here. (She draws it for you, fast and exact, on the back
of a map of somewhere else.) Debts I understand. It's the other thing I'm
bad at.

→ end. The route stays open, **guarded**.

---

### `wayfinder.refuse_selling` **(new: her refusal, before the confession)**

If anything before `confessed` tries to open the route (an Act 2 writer's
flirt option, a night at her rooms):

**YSOLDE:** Not while you're in my ledger. I've some rules. Not many. That's
one.

---

### `wayfinder.twelfth` **(new: the twelfth drawing)**

**Entry:** `edric.freed` and `wayfinder.forgiven` in (`forgave`, `use`;
`cold` only after a further visit). Once.

**NARRATOR:** Her rooms over the map table: one window, one bed, and every
surface covered in paper. On the table there's a drawing of a barrow mouth,
in ink, carefully. You've seen it before, or one like it. There are eleven
like it pinned to the wall.

**YSOLDE:** Twelfth. (She doesn't look up from it.) Edric sat with me last
night and told me where the corners were. He remembered. I've been getting
them wrong for twelve years because I was drawing it from outside. (She turns
it round for you to see.) There. That's right. That's what it was.

Choices:
- "It's good." → `twelfth_good`
- "(Put your hand on her shoulder.)" → `twelfth_hand`

### `wayfinder.twelfth_good` **(new)**

**YSOLDE:** It's correct. (A pause.) It's good, too. (She laughs, short,
surprised.) I've not drawn anything for the pleasure of it in twelve years.
I'm out of practice. At a lot of things.

→ `twelfth_ask`

### `wayfinder.twelfth_hand` **(new)**

**NARRATOR:** She puts her own hand over yours, ink on her fingers, and
leaves it there.

→ `twelfth_ask`

### `wayfinder.twelfth_ask` **(new: the invitation)**

**YSOLDE:** I'm fifty-four. I've a brother back from the dead asleep in my
spare room and a lord in the north who'll want my head for a list of Larks.
I've not asked anyone to stay in a very long time. I'm not sure I remember
the form. (She looks at you over the drawing.)
- `[when wayfinder.name == false]` Stay, Lark?
- `[when wayfinder.name == nobody]` Stay, Nobody? (She stops.) No. That won't
  do now. Stay, {name}?
- `[otherwise]` Stay, {name}? (She says it as if she's surprised to hear it
  aloud; she's only ever written it.)

Choices:
- "Yes." `<when rel wayfinder affection >= 40 and rel wayfinder trust >= 30>`
  locked: *Not yet. You're both still counting.* → `night_lead`
- "Not tonight." → `twelfth_no`

### `wayfinder.twelfth_no` **(new: the survivor refuses)**

**NARRATOR:** She takes a scrap of paper and writes on it, and shows you. It
says *declined*, in a fine clerk's hand. Then she crosses it out, carefully,
with a single line, so it can still be read.

**YSOLDE:** There. Margin note. (Lightly.) It can stand till it can't.

→ end. No change. The invitation stays open (offered on `hub` as "Is the
offer in the margin still standing?").

---

### `wayfinder.night_lead` **(new: the lead-in)**

**NARRATOR:** She clears the bed of paper, all of it, maps and margins and
letters, in one sweep onto the floor, which is the least tidy thing you have
ever seen her do. She looks at the mess with interest.

**YSOLDE:** Twelve years I've kept that bed tidy for nobody. (She takes her
spectacles off, folds them, and sets them on the twelfth drawing.) I'll tell
you now, I'm a bit out of the habit. You'll have to be patient, or I'll have
to be rude. Possibly both. ...If you want to stop, say so. I'll not mind. I'll
mind, but I'll not *mind*.

Choices:
- "I'm sure." → `night`
- "(Stop here.)" → **YSOLDE:** (She laughs, not unkindly, at the paper on
  the floor.) Then help me pick that up, at least. (You do. It takes an hour.
  She talks the whole time about the places on the maps.) → end.

---

### `wayfinder.night` **(new; slot 6)**

**Effects:** set `wayfinder.lover`; rel `wayfinder` affection +15, trust +10;
condition `warmed` 1 day; `night.spent`.

**NARRATOR:**
- `[when settings.intimacy == "full"]` `[explicit scene: Ysolde and {name},
  her rooms over the map table, every surface paper and the bed swept clear
  of it, one window, Edric asleep through the wall; wry and out of practice,
  then glad; two people who had stopped expecting this; afterwards she draws
  the survivor in the margin of the twelfth drawing — to be written]`
- `[when romance.eve == wayfinder]` → see `eve_night`.
- `[when the war began at once after the cages and someone died]`
  **(grieving)** She doesn't joke tonight. She wants the lamp out, and the
  window open, and the cold coming in, and you. She holds on hard. When it's
  over she lies with her face to the wall and her hand behind her, holding
  yours, and says, "I couldn't draw anything today. Not a line," and then,
  "Thank you," and then sleeps.
- `[otherwise]` **(joyful)** She is out of practice, and says so, and is
  rude about it, and is wrong about being out of practice. There's a lot of
  laughing, most of it hers, short and surprised, as if it keeps catching
  her on the way past. Paper crackles under you both every time anyone
  moves. At one point she stops and says, "Hang on," and moves a map of the
  Kerchiefs' ravine out from under your back, and says, "I'll want that,"
  and you both lose a minute to laughing. Then the laughing goes somewhere
  quieter. Through the wall, Edric sleeps.

→ `morning`

#### Beat sheet for slot 6: `wayfinder.night`

- **Mood and pacing.** Wry, then glad. Two adults past the age of
  expecting it, comic about being out of practice and then not; neither
  hides their body or makes an issue of it. Paper everywhere, the noise of
  it. Edric through the wall: they're quiet for his sake and not very good at
  it. The pace is easy; she has nowhere to be for the first time in twelve
  years.
- **What she wants.** Something that isn't for Edric. To be a person and not
  a margin. To be forgiven in the body as well as in words.
- **What she fears.** That she has sold so many names she has none of her
  own. Being tender, which she's bad at, and being caught being bad at it.
- **What the survivor wants.** Her, and the plain fact of being known by
  someone who once wrote them down for money and now doesn't.
- **Consent, on the page.** She says "If you want to stop, say so" and means
  it, and asks again, in her brisk way, partway: "All right?" The survivor
  answers. She's rude, and kind, and checks.
- **The emotional turn.** The name. She says the survivor's name, the one she
  wrote in the margin (or "Lark"), for the first time aloud in the dark, and
  hears herself say it, and stops; it's the first time it hasn't been an
  entry. The joy turns quieter from there.
- **Callbacks.** The margin ("Name first; I'm a tidy woman"). The twelfth
  drawing, corners right at last. Edric. The spectacles, folded on the
  drawing. "Larks get up early and make a great deal of noise about it"
  (if Lark).
- **Sex variants.** Same beats either way.
- **Ends on.** Her, after, sitting up in the grey light with a pen,
  drawing the survivor asleep in the margin of the twelfth drawing, and
  writing nothing under it.

### `wayfinder.morning` **(new: the margin, rewritten)**

**NARRATOR:** Grey light. She's sitting up with the twelfth drawing on her
knee and a pen, and she's drawing you, asleep, in the margin. When she sees
you're awake she turns it round. It's very good. Under it, there's nothing
written at all.

**YSOLDE:** I couldn't think what to put. (She seems pleased about that.)
First time in my life.

Choices:
- `[wayfinder.name == false]` "My name's {name}. Not Lark." →
  **YSOLDE:** (She looks at you over the spectacles.) I know. I've known
  since the second week; Rook talks. (She caps the pen.) You'll always be a
  Lark to me. You get up early and you make a great deal of noise about it.
  → end
- "Write my name under it." → **YSOLDE:** No. (Gently.) I've written it
  enough. I'd rather say it. → end
- "(Kiss her.)" → **NARRATOR:** She gets ink on your jaw. She doesn't tell
  you. Rook does, at breakfast. → end

---

### `wayfinder.eve` **(new: the night before the gate)**

**Entry:** `romance.eve` = `wayfinder`.

**YSOLDE:** He'll come for me too, you know. Sallow. With a list of Larks in
his hand and a face like a creditor. (She's drawing the north gate, very
fast, every stone.) I've drawn every place in this valley except the one I'm
going to die in. Thought I'd better. ...Put that down. No, the pen. Come
here. I've finished.

Choices:
- "(Go to her.)" → `eve_night`
- "You're not going to die." → **YSOLDE:** No. Probably not. (She puts the
  pen down anyway.) Come here regardless. → `eve_night`
- "Sleep. I'll stay." → **NARRATOR:** She sleeps with the drawing of the
  gate on her chest, and you take it off her, carefully, and she doesn't
  wake. → end

### `wayfinder.eve_night` **(new; desperate variant of slot 6)**

**NARRATOR:**
- `[settings.intimacy == "full"]` `[explicit scene: Ysolde and {name}, her
  rooms the night before the war, a drawing of the north gate on the
  table, every stone; no jokes left; wanting to know the survivor the way
  she knows a place she's mapped — to be written]`
- `[otherwise]` No jokes tonight, or only one, at the very start. She goes
  over you the way she goes over a coastline, slow and exact, as if she'll
  be asked later to draw it from memory. Maybe she will. When it's done she
  lies with her ear on your chest and says, "Got it. Every corner," and
  sleeps.

---

### `wayfinder.leaving` **(new: the end)**

**Entry:** the ending, or Act 3, if Edric is free and both live.

**YSOLDE:** Edric wants to see the sea. He's never seen it; he was in a cage
for the twelve years he'd have spent getting round to it. (She's packing
maps, rolling them tight.) There are places out there nobody's forgotten
yet. Nobody's drawn them, either. ...I could use somebody who walks toward
trouble on purpose.

Choices:
- "I'll come." → `wayfinder.fate` = `left_together`
- "I can't. Not yet." → **YSOLDE:** Then I'll draw you a map back. It'll be
  correct. → `wayfinder.fate` = `left`

### Ends (epilogue lines)

- **Frees Edric and leaves the valley**, with the survivor: *Three people
  and a cart of paper on the coast road. One of them is drawing the sea, and
  can't get the corners right, and doesn't mind.*
- Without the survivor: *A map arrives at the Last Lamp once a year, of
  somewhere nobody's been. It's addressed to you. It's correct.*
- **Dies at Silverstair** (the double game found out): *Sallow's ledger has
  a last entry in her hand: "Lark." Under it, a drawing of the survivor
  asleep, very good, and nothing written at all.*
- **Keeps selling** (no romance): *The notes go on.*
