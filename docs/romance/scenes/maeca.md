# Maeca Barefoot: the scenes

Every beat of Maeca's arc (`../ARCS.md` §2) as playable dialogue. The Act 1
beats are also drafted as data in `../data/maeca.json`. The notation is
`sella.md`'s (see the top of that file).

Voice check for every line here: few words; ground, tracks, weather,
animals; level, quiet, present tense; the Pack is "the Pack" or "them";
"Ashford" only ever in three words or fewer.

---

## Act 1

### `maeca.cb_knelt` **(new: the test, seen)**

**Entry:** `promise.pack` is set, she has met the survivor, npc flag
`cb:knelt` is not set. Before `invite`.
**Effects:** set npc flag `cb:knelt`; rel `maeca` respect +10.

**MAECA:** You went into the Hollow with nothing on your hands and knelt to
him. (She looks at your knees, which are still muddy.) He let you. ...He
doesn't let me, and he's known me ten years.

→ `hub`

---

### `maeca.invite` *(existing node, gate and choices extended)*

**Entry gate (add):** `not hasTag wolf_pelts`. (A survivor wearing the
Pack's skins is never invited; nothing says so. `first` already says what
she thinks of the cloak.)

**MAECA** *(existing)*: (She finishes her cup and stands.) I'm going out to
the Blind. The fire's big enough for two, if you can keep quiet. Most can't.

Choices:
- "I can keep quiet." → `blind_walk` **(changed from `blind`)**
- "Not tonight." → `hub` *(existing; no stat change)*

### `maeca.hub`: the Blind choice *(existing choice, retargeted)*

"Is the fire at the Blind still big enough for two?" → `blind_walk`
**(changed from `blind`)**. Its gate and lock text *(existing)* stay: "Not
tonight. Not like this."

---

### `maeca.blind_walk` **(new: the lead-in)**

**Reads:** `wolf.blood`, `maeca.blind_nights`, `beasts.outcome`,
npc flag `thanked`, `history broke_promise`.

- `[when wolf.blood]` → `blood` (below), instead of the walk.

**NARRATOR:**
- `[when maeca.blind_nights == 0]` She goes out by the east gate without a
  lamp, and you follow her along the Old Road past the wreck, by starlight
  and the white of the frost. She walks barefoot on ground that would cut
  you through your boots, and doesn't make a sound. Once she stops, and
  you stop, and somewhere off in the Hollow a wolf calls and is answered.
  "Him," she says. "And the bitch with the torn ear. Eating." She walks on.
- `[otherwise]` The Old Road, the wreck, the frost. You know the way now,
  and she lets you walk in front, which she has never done.

**NARRATOR:** The Hunters' Blind is a lean-to of hides against a fallen oak,
with a fire the size of a hat. She feeds it one stick at a time. She doesn't
talk. After a while she takes the crossbow off her back, and checks it, and
lays it down by her right hand, and turns and looks at you across the fire
as if you were a track she has been following for days.

**MAECA:**
- `[when maeca.blind_nights == 0]` If you're going to talk after, don't.
- `[otherwise]` (She holds out her hand. That's all.)

Choices:
- `[first night]` "I won't." → `blind`
- `[later nights]` "(Take her hand.)" → by night count: `blind`, `blind2`
  (when `maeca.blind_nights == 1`) or `blind3` (when `>= 2` and npc flag
  `say:asked` is not set); otherwise `blind`
- "Then not tonight. I'll keep the fire." → `watch_only`
- "(Stop here. Go back to town.)" → `blind_leave`

### `maeca.blind_leave` **(new)**

**MAECA:** (She nods at the fire.) Mind the frost on the Old Road. It's
worse by the wreck.

→ end. No change.

### `maeca.blood` **(new: she refuses)**

**NARRATOR:** At the edge of the Hollow she stops, and sniffs, once, and
turns round.

**MAECA:** Not with that on you. (Flat, not angry.) Wash. River's that way.
...Or sleep, and come tomorrow. The night takes it off. It took it off me.

→ end. No change.

---

### `maeca.watch_only` **(new: the fire, and nothing else)**

**Effects:** rel `maeca` trust +10, affection +5; condition `rested` 1 day.
Does **not** add to `maeca.blind_nights`.

**NARRATOR:** You keep the fire. She keeps the dark. Some time after
midnight she comes in from the edge of the light and sits down with her back
against yours, and you can feel her breathing, slow, and listening. You
sleep like that, sitting up. In the morning the frost is on both your
shoulders and not between them.

**MAECA:** You kept quiet. (She stands, and stretches, and looks at the
Hollow, not you.) Most can't.

→ end

---

### `maeca.blind` *(existing node, extended; slot 2)*

**Effects** *(existing)*: set `maeca.lover`; rel affection +15, trust +10
(first night only; **new**: later nights affection +5); condition `warmed`
1 day; notice. **(New):** `maeca.blind_nights +1`; `night.spent`.

**NARRATOR:**
- `[when settings.intimacy == "full"]` `[explicit scene: Maeca and {name},
  the Hunters' Blind in the Verge at night, a lean-to of hides and a fire
  the size of a hat; wordless, wary, careful hands that become sure ones,
  frost outside and the Pack audible far off; her trust given like a held
  breath let go — to be written]` *(existing; see beat sheet)*
- `[when maeca.blind_nights == 0 and npc flag thanked and beasts.outcome
  == cured]` **(new: joyful)** Off in the Hollow the Pack is loud, a long
  tangle of voices, and she stops with her hands on your buckle and listens,
  and then she laughs: a short surprised sound, as if she'd trodden on
  something. "They're *eating*," she says, and pulls you down onto the
  hides. Her hands are hard and careful, the way they are with a snare, and
  then they're not careful. The fire goes down to embers. Neither of you
  feeds it. Later, under the hides, she sleeps like a hunter: lightly, one
  hand on the crossbow and the other on you.
- `[otherwise]` *(existing, extended)* She doesn't talk, and then neither of
  you needs to. She undoes your boots before anything else, and sets them
  side by side outside the hides, and that seems to be a decision. Her hands
  are hard and careful, the way they are with a snare: slow, listening, ready
  to stop. They become sure. Once, far off, the Pack calls, and she goes
  still against you until it's done. Later, under the hides, she sleeps
  like a hunter: lightly, one hand on the crossbow and the other on you.

Next → `blind_morning`

#### Beat sheet for slot 2: `maeca.blind`

- **Mood and pacing.** Almost wordless. Wary, then sure. Cold outside,
  warm under the hides, and the scene should keep both in it: frost on the
  hide wall, the fire too small, breath visible. Slow at the start, as she
  is with anything she doesn't yet know. Short lines, no dialogue to speak
  of; the narrator watches what hands do, as with Greymuzzle.
- **What she wants.** To be close to someone without owing them. To be the
  one choosing. To feel the cold kept off by someone who isn't dead or a
  wolf.
- **What she fears.** Being saved. Being talked at afterwards. The kind of
  closeness that ends in a cave mouth.
- **What the survivor wants.** Her, and the quiet she keeps.
- **Consent, on the page.** She sets the terms at the fire ("If you're going
  to talk after, don't") and the survivor accepts them. In the scene she
  leads, with a hunter's caution: she stops, listens, and goes on. The
  survivor has their own pauses, and she reads them like tracks and waits.
  Nothing is hurried past.
- **The emotional turn.** The Pack calls off in the Hollow and she goes
  still, listening, and the survivor goes still with her and waits until
  it's done. When she moves again, she isn't careful any more. That's the
  held breath let go.
- **Callbacks.** Barefoot (the boots set outside the hides, "a decision").
  The crossbow by her right hand. "The fire's big enough for two." "Most
  can't." Greymuzzle's voice in the Pack's. Snares: her hands.
- **Sex variants.** Same beats for either survivor.
- **Ends on.** Her asleep like a hunter, lightly, one hand on the crossbow
  and the other on the survivor; the fire down to embers; frost on the hides.

---

### `maeca.blind_morning` *(existing node, one variant added)*

**MAECA:**
- `[when npc flag told_ashford and maeca.blind_nights >= 3 and not
  maeca.heard_heart]` → this case is handled in `blind3_morning`; it never
  reaches here.
- `[when npc flag told_ashford]` *(existing)* (Grey light. She's already up,
  barefoot in the frost, listening.) Go on, then. The wood's awake, and so's
  Holloway, and he'll count us both.
- `[otherwise]` *(existing)* (Grey light. She's already up, barefoot in the
  frost, listening to the wood.) The Pack found me, after Ashford. Three
  days in a cave mouth with the garrison dead round me, and the old grey one
  came and lay down across the way in. Kept the cold off. Kept everything
  off. ...That's why. That's all of why. Don't make it a story.

Choices *(existing)*: "I won't." → end.

---

### `maeca.blind2` **(new: the second night; her feet)**

**Effects:** as `blind` (affection +5); set npc flag `say:feet`;
`maeca.blind_nights +1`.

**NARRATOR:** Afterwards, in the dark under the hides, she puts her feet
against your legs, and you flinch: they're cold as stones in a stream. She
starts to take them back.

Choices:
- "(Hold them.)" → `blind2_feet`
- "(Let her.)" → `blind2_let`

### `maeca.blind2_feet` **(new)**

**NARRATOR:** You take one in your hands. The sole is hard as boot leather,
and scarred: old white lines across the ball of the foot, a ridge along the
heel where something cut it to the bone a long time ago and it healed badly
in the cold. She lets you hold it. She lets you hold the other. She lies very
still, the way she lay still when the Pack called, and doesn't say anything,
and after a long time her feet are warm.

**MAECA:** (Into the dark, very low.) Nobody's held those.

**Effects:** rel `maeca` trust +10.

→ `blind_morning`

### `maeca.blind2_let` **(new)**

**NARRATOR:** She tucks them up under her instead, the way a dog curls its
nose under its tail, and goes to sleep. In the night, half awake, you feel
her put them back against you, slowly, as if she was trying it out.

→ `blind_morning`

---

### `maeca.blind3` **(new: the third night; her question)**

**Effects:** as `blind`; `maeca.blind_nights +1`; set npc flag `say:asked`.

**NARRATOR:** Later, with the fire down, she lies with her head on your
chest, listening the way she listens to the Hollow.

- `[when beasts.outcome == allied]` *(adds)* Outside, in the frost, you can
  hear them come: soft feet, a long way round, and then a sigh, and then
  another. The Pack, lying down round the Blind in the dark. She lifts her
  head. "They don't do that," she says. "Not for me. Not for anyone." She
  lies back down.

**MAECA:** You walk quiet. You came into my Hollow and knelt to him and he
let you. You never talk about before. (A pause.) What were you?

Choices (by background, shown only as the survivor's own; each → `told_true`):
- `[bg hunter]` "A hunter. Out of these woods, once."
- `[bg scholar]` "A clerk of dead men's letters, in a cloister cellar."
- `[bg outcast]` "Worse company than the Kerchiefs. I walked away."
- `[otherwise]` "I lit chapel lamps nobody came to see."
- "Not much. Nobody you'd have heard of." → `told_little`

### `maeca.told_true` **(new)**

**Effects:** set `maeca.heard_past`; rel `maeca` trust +10.

**MAECA:**
- `[bg hunter]` Thought so. You put your feet down like you're asking the
  ground first. (She almost smiles.) I'd have liked you, then. Probably
  would have shot you for poaching.
- `[bg scholar]` Letters. (She thinks about it.) Tracks for people who sit
  still. ...Read me something, one day. Not now.
- `[bg outcast]` Walking away's a skill. Most never learn it. They stay till
  it's too late, out of pride. (She means the garrison. She doesn't say so.)
- `[otherwise]` Lamps. Nobody coming. (A long breath.) I held a cave mouth
  for three days for nobody coming. We'd have got on.

→ `blind3_morning`

### `maeca.told_little` **(new)**

**MAECA:** (She doesn't push.) All right. (And it is.) ...Keep it, then. I
keep mine.

→ `blind3_morning`

### `maeca.blind3_morning` **(new)**

**Effects:** set `maeca.heard_heart`.

**NARRATOR:** Grey light. She's awake before you, as always, but she hasn't
got up. Her head is still on your chest. Her face is very still.

**MAECA:** Your heart's slow. (She doesn't lift her head.) Slow as a bear's
in January. It was going like a hare's last night. ...I've lain with my ear
to a lot of things to see if they'd live, {name}. (She gets up, then, and
goes out barefoot into the frost, and stands there listening to the wood
with her back to you.) Go on. Holloway'll count us.

- "Maeca—" → `blind3_m_no`
- "(Go.)" → end

### `maeca.blind3_m_no` **(new)**

**MAECA:** No. (Not unkind.) Don't make it a story. Not yet.

→ end

> **Note:** "I've lain with my ear to a lot of things to see if they'd live"
> is the closest Act 1 comes, and it says nothing; she's a soldier who held
> a cave mouth among the dying. It pays in Act 2 at `maeca.what`.

---

### `maeca.say_sella` **(new: a remark, once)**

**Entry:** `maeca.lover` and (`sella.nights >= 1`), npc flag `say:sella`
not set. Next → `hub`.

**MAECA:**
- `[when sella.free]` You go up Sella's stairs. (She doesn't look up from
  her cup.) Not for money, now. Rook talks. ...Is it her, or me, or both? I
  don't mind which. I mind not knowing.
  - "Both." → `say_sella_both`
  - "You." → `say_sella_you`
  - "I don't know yet." → `say_sella_dunno`
- `[otherwise]` You go up Sella's stairs. Rook talks. (A shrug.) She's honest
  about what she charges. That's more than most.

`say_sella_both`: **MAECA:** (A nod.) Good. Now I know. → `hub`. Rel trust +5.
`say_sella_you`: **MAECA:** (She looks at you, long, the way she looks at a
track that might be lying.) We'll see. → `hub`. *(If it's a lie, Act 2's
eve finds it out; ARCS §6.)*
`say_sella_dunno`: **MAECA:** That's an answer. → `hub`. Rel trust +5.

---

## Act 2

### The boots (Act 2 beat 4)

The survivor learns who signed (Holloway) from Pell's sister's letter, from
Holloway's confession, or from Redcowl. The Act 2 writer sets
`boots.known_by_survivor` (new) when they do. Then:

- If the survivor reaches Maeca **the same day** (before the next dawn), the
  `boots_tell` choice is open, and `maeca.boots` = `you`.
- If a dawn passes first, set `maeca.boots_hid` (ARCS §7). The choice is
  still open, but she reacts to the delay.
- If she learns first from someone else, the scene is `boots_heard`.

#### `maeca.boots_tell` **(new)**

Offered on `hub`: "Maeca. The boots. I know who signed for them."
`<show boots.known_by_survivor and not maeca.boots>`

**NARRATOR:** She's at her table in the Last Lamp. She puts the cup down
and puts both hands flat on either side of it.

**MAECA:**
- `[when maeca.boots_hid]` How long have you known?
- `[otherwise]` Say it.

Choices:
- `[when maeca.boots_hid]` "Since yesterday. I didn't know how." / "Days.
  I didn't know how." → `boots_late`
- `[otherwise]` "Holloway. He was the quartermaster. He signed them in full."
  → `boots_said`

#### `maeca.boots_said` **(new)**

**Effects:** set `maeca.boots` = `you`; rel `maeca` trust +25.

**NARRATOR:** She doesn't move. Across the room Holloway is at his own table
with his back to the wall, the way he always sits, and she doesn't look at
him. She looks at her hands.

**MAECA:** ...Good hand. Good ledger. (A long breath through her nose.) You
came straight here.

Choices:
- "Yes." → `boots_choose`
- "Don't kill him." → `boots_ask`

#### `maeca.boots_ask` **(new)**

**MAECA:** (She looks at you then, for the first time.)
- `[when rel maeca trust >= 50]` That's not yours to ask. (A pause.) You
  asked anyway. ...I heard you.
- `[otherwise]` That's not yours to ask.

→ `boots_choose`

#### `maeca.boots_choose` **(new: what she does)**

Not a player choice: the world decides (ARCS §2.4 table). The narrator plays
the result.

- **Hold the gate** (`trust >= 50`, told by you that day). **MAECA** gets up
  and crosses the room, barefoot, not quickly, and stands over Holloway's
  table until he looks up. Nobody in the room breathes. "You held the
  ledger," she says. "You can hold a spear. North gate. Beside me. Every
  night till it's done." He stands up. He doesn't say sorry; he never does.
  He goes to get his spear. Sets `maeca.fate` = `gate` (Act 2 writer's
  value).
  - With Greymuzzle dead: she adds, "Other side of the gate from me. I'll not
    look at you."
- **Leave with the Pack** (trust < 50, or told late). She gets up and goes
  out by the east gate, barefoot, and doesn't take her cup.
  - If `maeca.lover`: at the door, "I'm going to the deep wood. Come, or
    don't follow." Choices: "I'll come." (Act 2 writer: this ends the
    survivor's ability to hold the gate; better offered after the war) /
    "I can't. Not yet." → **MAECA:** "Then not yet." She goes.

#### `maeca.boots_late` **(new: the debt come due)**

**Effects:** set `maeca.boots` = `you`; rel `maeca` trust −40, affection −20.

**MAECA:** (Very quietly.) You lay in my blind and you knew. (She stands.)
...No. Don't. You'll say something true, and I'll have to hear it.

**NARRATOR:** She goes out barefoot by the east gate. She doesn't take her
cup, and she doesn't look at Holloway, and the whole room watches her not
look at him.

→ Her end is **leave with the Pack**. `maeca.lover` stays set (the bible's
"the survivor's lover at the end, if both live" is still possible), but the
Blind is shut until after the war: the hub choice's lock reads *She won't
have you at the Blind.*

#### `maeca.boots_heard` **(new: she heard from someone else)**

- **From Holloway** (he confessed): she leaves with the Pack, unless the
  Pack is gone and Greymuzzle dead, in which case → **the gate** (below).
- **From Redcowl** (the Kerchiefs come for Holloway at the worst moment):
  she kills him at the gate, unless the survivor is her lover and stands
  between.

**The gate** (Act 2 writer's scene; the romance lines):

**NARRATOR:** She has the crossbow up. Holloway has his hands empty at his
sides and isn't asking for anything.

Choices (if `maeca.lover`):
- "(Step between them.)" → **MAECA:** "Move." / YOU: "No." / **MAECA:** (A
  long time. The bow doesn't waver. Then it does.) "...You're in my light."
  She lowers it and walks away, east, and doesn't come back to the Blind.
  Holloway lives. `maeca.fate` = `left`; the romance ends unless Act 3 opens
  it again (Act 2 writer's call).
- "(Let her.)" → the bible's end: Maeca kills Holloway.

---

### `maeca.grey_dies` **(new: Greymuzzle, of age; Act 2's end)**

**Entry:** Greymuzzle alive at Act 2's end (bible §9), `maeca.lover`.

**MAECA:** (At the east gate, at dusk, barefoot, holding her boots in one
hand, which she never carries.) He's lying down. In the Hollow. He's not
getting up. ...Come.

**NARRATOR** (in the Hollow): The old grey wolf is lying across the mouth
of a hollow in a bank, where the frost doesn't reach, the way he lay across
a cave mouth once. The Pack is all round him in the dark, not close. Maeca
kneels. She doesn't touch him; you've never seen her touch him. He lifts
his head and looks at her, and then past her at you, and puts it down.

- `[when promise.pack and beasts.outcome == allied]` *(adds)* When it's done
  the Pack gets up, all at once, and goes to you, not her. They lie down
  round your feet. She watches it. "They've chosen," she says. "...They
  chose right."

→ `blind_grief`

### `maeca.blind_grief` **(new: the grieving night)**

**NARRATOR:** At the Blind she lights the fire and doesn't feed it. The
Pack starts singing for him, out in the Hollow: one voice, and then all of
them, going on and on.

**MAECA:** Stay awake with me. (Not a question.) Till they stop.

Choices:
- "(Stay awake with her.)" → `blind_grief_wake`

### `maeca.blind_grief_wake` **(new)**

**NARRATOR:** You sit with her. They don't stop for a long time. Some time
in it she turns and takes your face in both hands, hard, and looks at you,
and it's a question.

Choices:
- "(Yes.)" → `blind_grief_night`
- "(Hold her. Only that.)" → `blind_grief_hold`

> The question is hers, and the answer the survivor's. A survivor who only
> holds her isn't refusing anything; she asked for something, and they gave
> her what she needed.

### `maeca.blind_grief_night` **(new; grieving variant of slot 2)**

**NARRATOR:**
- `[settings.intimacy == "full"]` `[explicit scene: Maeca and {name}, the
  Hunters' Blind the night Greymuzzle died, the Pack singing for him in the
  Hollow the whole time; grief that wants a body to hold on to; not careful
  tonight, and then very careful; she doesn't cry, and then does, once, and
  doesn't stop holding on — to be written]`
- `[otherwise]` She isn't careful tonight. She holds on as if the ground
  might go out from under her, and the Pack sings through all of it,
  through the hides, through her. Once she makes a sound you've never heard
  from her and puts her face into your neck so you won't see it. Then she's
  careful again, very careful, as if you were the thing that might break.
  When the singing stops, she's asleep. Both her hands are on you. Neither
  is on the crossbow.

→ `grief_morning`

#### Beat sheet (grieving variant)

Grief wanting a body to hold on to: urgent, wordless, not tender at first.
The turn: she breaks once, hides it, and from then on she is careful with
the survivor, as if they're the one who might go. The Pack's singing runs
through the whole scene and stops at its end. Callbacks: the cave mouth,
"Kept the cold off. Kept everything off", the crossbow (not touched
tonight). Ends on: both her hands on the survivor, neither on the crossbow,
silence in the Hollow.

### `maeca.blind_grief_hold` **(new)**

**NARRATOR:** You hold her. She lets you. She doesn't cry. The singing goes
on and on, and some time in it she sleeps sitting up against you, and her
feet, when you feel for them, are cold, and you hold those too.

→ `grief_morning`

### `maeca.grief_morning` **(new)**

**MAECA:** (Grey light. She's up, barefoot in the frost.) Ten years he kept
the cold off. (She doesn't turn round.) ...Your turn.

→ end. Rel `maeca` affection +10, trust +10.

---

### `maeca.what` **(new: Act 2 beat 11)**

**Entry:** `survivor.knows_risen`; `maeca.lover`.

- `[when maeca.heard_heart]`
  **MAECA:** I know. (Before you've said anything.) A hare at night and a
  bear at dawn. And the Pack lay down for you. They lie down for their own.
  ...I lay three days in a cave with dead men, {name}. I know what they
  smell like. You smell like the river, at dawn. I've known since the third
  night.
  - "You never said." → **MAECA:** You never asked. (A pause.) I've loved
    worse things than a dead one. Lain three days with a wolf's breath on
    my neck. → end. Rel trust +15.
- `[otherwise]`
  **MAECA:** (She listens to you say it all, without moving.) ...Dead. (She
  looks at your feet, then your face.) You walk well for it. → end.

---

### `maeca.eve` **(new: the night before the gate)**

**Entry:** `romance.eve` = `maeca`.

**NARRATOR:** She doesn't go to the Blind. She takes you up onto the north
wall, where the Watch's fire is, and sends the two men on it down for an
hour with a look. She checks your crossbow, or your blade. Then your boots,
both of them, the laces. Then you.

**MAECA:** Boots are good. (She tugs a lace.) Somebody signed for those,
and they came. ...Here. Now. Before the light.

Choices:
- "(Yes.)" → `eve_night`
- "(Hold her. Watch the road.)" → `eve_watch`

### `maeca.eve_night` **(new; desperate variant of slot 2)**

**NARRATOR:**
- `[settings.intimacy == "full"]` `[explicit scene: Maeca and {name}, the
  north wall the night before the war, in the lee of the Watch's fire, the
  road north dark; desperate and practical, her hands quick and certain
  now; she keeps one ear on the road the whole time — to be written]`
- `[otherwise]` It's quick, and certain, and not at all careful, against
  the wall in the lee of the fire with your cloak under you both and the
  road north dark beyond the battlements. She keeps one ear on the road the
  whole time. You can feel her doing it. Afterwards she lies with her head
  on your chest, listening to your heart race and then slow, and says,
  "Hare," and then, later, "Bear," and that's all.

`eve_watch`: **NARRATOR:** You stand the watch together, her back against
your chest, your cloak round you both, looking at the road. She talks more
than she's ever talked: about deer, about frost, about the colour the sky
goes before snow. None of it about tomorrow.

→ end

#### Beat sheet (eve variant)

Desperate and practical: she does it the way she'd check a snare before a
storm. Quick hands, no hesitation; she's chosen. The turn: in the quiet
after, her head on the survivor's chest, she names their heart, "Hare",
then "Bear", knowing what the second means now. Callbacks: boots that
came; the wall where the Watch counts; the road north. Ends on: "Bear," and
nothing else.

---

### Ends (epilogue lines)

- **Leaves with the Pack**, lover, both living, trust high: *Two people at a
  fire the size of a hat, in the deep wood, and the Pack lying down round it.
  One of them wears boots.*
- **Takes the Watch**, lover: *Barefoot on the north wall. A pair of boots
  under her bed she won't wear and won't give back.*
- **The survivor's lover, at the end**: *She hunts deer. Never wolves. She
  talks after, sometimes, now.*
- **The survivor gone dark at dawn** (ending B without the coin): *The Blind,
  with one person in it, and the Pack lying down round it anyway.*
