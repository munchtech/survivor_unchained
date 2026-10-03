# Sella: the scenes

Every beat of Sella's arc (`../ARCS.md` §1) as playable dialogue. The Act 1
beats are also drafted as data in `../data/sella.json`.

**How to read these.** Each block is one dialogue node, named
`sella.<node>` as in `dialogue.json`.
- **SELLA:**, **NARRATOR:** and **YOU:** are the speakers. Stage directions
  are in parentheses inside the line, as the game writes them.
- `[when …]` before a line marks a variant, and the first one that holds is
  used. Conditions are written in short form (`sella.nights >= 2`,
  `sex female`, `trait risen_once`); the data files spell them out.
- Choices are listed as `→ node`. `{…}` holds the choice's effects, `<show …>`
  the condition for the choice to appear at all, `<when …>` the condition for
  it to be enabled, and `locked:` the reason shown when it is not.
- **Sets** and **Reads** list the facts each beat touches.
- Lines kept from the existing game are marked *(existing)*.

---

## Act 1

### `sella.price` *(existing, one choice added)*

**SELLA:** Fifteen gold, up front. For that you get the blue room, a bath
that's warm at least to start with, and me, until morning. Anything you'd
rather I didn't do, say so. Anything you'd rather I did, say that too.

- "15 gold, then. Lead the way." `<when gold >= 15>` locked: *You would
  need 15 gold* → `stairs`
- "15 gold. But I only want to sleep." `<when gold >= 15>` → `rest_night`
  **(new)**
- "Just the talk, for now." → `hub`

---

### `sella.stairs` **(new: the lead-in to the paid night)**

Speaker: narrator, then Sella. This is the existing `night` node's lead-in,
pulled out into its own node so there is a place to stop before the moment.

**Reads:** `sella.nights`, `trait risen_once`, calling, `sex`,
`history burned_roost`.
**Effects on entering:** `gold −15`.

**NARRATOR:**
- `[when the Roost burned and she has not yet said so (no cb:burned_roost)]`
  → goes to `refuse_roost` instead (below).
- `[when sella.nights == 0]` She takes the coins first and your hand second,
  and leads you up Rook's narrow stairs. They creak on the fourth step and
  the ninth, and she steps over both without looking.
- `[when sella.nights >= 3]` She doesn't take your hand any more; she takes
  your sleeve, the way you'd take a regular's. On the fourth step she looks
  back, to check you're stepping over it. You are.
- `[otherwise]` Coins, then your hand, then the stairs. Fourth step, ninth
  step. You're learning.

**SELLA:**
- `[when sella.nights == 0]` Mind the fourth. And the ninth. Rook says
  they're for the drunks. I say they're for the wives.
- `[when sella.nights >= 3]` You're getting good at my stairs, love. Careful.
  People'll think you live here.
- `[otherwise]` In you go. Bath's run. It's warm, I promise. For a bit.

**NARRATOR:** The blue room is blue because the lamp glass is, and
everything in it takes the colour: the quilt, the jug, the bath, her. She
tests the water with her elbow like somebody's mother, and then tips your
chin up with one finger like nobody's mother at all.

**NARRATOR** (by calling, as she undresses you):
- `[warden]` The buckles take an age. She undoes them as if she has done a
  great many, and laughs at the last one, which is stuck. "All that steel,
  and under it, look. A person."
- `[reaver]` She takes your hands, one and then the other, and turns them
  over, and looks at the knuckles. "Gently, upstairs. I mean it. I like this
  jug."
- `[arcanist]` She lays her palm flat on your chest and takes it away again,
  fast, then puts it back, slower. "You're warmer than the water. You know
  that? You're warmer than the water."
- `[stalker, or none]` She comes round behind you to start on the laces, and
  says into your ear, "There. Now you know what it's like," and you jump.
  She's delighted.

**NARRATOR** `[when trait risen_once, and npc flag sella say:cold_bath not yet set]`:
In the bath she slides her hands down your arms and stops. Under the warm
water you are cold: not chilled, cold, like something brought up from the
riverbed. She doesn't make a joke of it. She keeps her hands where they are
until you aren't. {set npc flag `sella` `say:cold_bath`}

**SELLA:** Right. Rules. Anything you'd rather I didn't, say so. Anything
you'd rather I did, say it louder; Rook's walls are thin, but she's deaf in
the left ear.
- `[when sex female, and npc flag sella say:woman set]` *(adds)* And don't
  be shy, love. I told you. You're not the first.

Choices:
- "(Pull her into the water.)" → `night`
- "(Kiss her.)" → `night`
- "Actually. Just sleep, tonight." → `rest_night_paid`
- "(Stop here.)" → `stop_paid`

---

### `sella.stop_paid` **(new)**

**Effects:** `gold +13`.

**SELLA:** (She sits back on her heels, and doesn't sulk, and doesn't ask
why.) Then I'll have the bath. It's paid for. (She counts thirteen coins
back into your palm and closes your fingers on them.) Two for the water.
That's Rook's rule, not mine. ...You'll come back when you want to. Or you
won't. Either's all right, love. Go on.

- "Goodnight, Sella." → end

> **Why:** the player can stop at the last moment and nobody is hurt by it.
> She keeps two for the bath because she would; it keeps her a professional
> and keeps the scene from being a lesson.

---

### `sella.night` *(existing node, extended cut-away; slot 1)*

Speaker: narrator.
**Effects** *(existing)*: `sella.nights +1`; rel `sella` affection +8,
trust +4; condition `warmed` 1 day; notice. **(Move `gold −15` to
`stairs`.)** **(New):** set `night.spent` (optional system, ARCS §0.2).

**NARRATOR:**
- `[when settings.intimacy == "full"]` `[explicit scene: Sella and {name},
  the blue room at the top of Rook's stairs, by lamplight; warm, unhurried
  and funny, a professional who enjoys her work, tenderness showing at the
  edges and quickly put away; ends with her asleep across you and the sun
  up — to be written]` *(existing; see the beat sheet below)*
- `[when trait risen_once and sella.nights >= 1]` **(new: tender)** The
  water's gone cool by the time either of you notices, and she drags the
  quilt off the bed and onto the floor rather than walk three steps. She is
  slower tonight. She keeps a hand flat on you, the whole time, the way
  you'd keep a hand on a horse you'd been told was skittish, and when you
  look at her she says, "Don't," and kisses you so you can't. After, you lie
  on the floor of the blue room with the lamp turned down to a bead, and she
  doesn't get up to dress, and you don't ask why. You wake with her hair
  across your chest and the sun already up. She is dressed, and counting,
  and she counts it twice.
- `[when sella.nights >= 2]` **(new: the patter with gaps in it)** She
  laughs when the water slops over the side and again when you try to mop
  it with her shift. Then the lamp is down to a bead, and the blue room is a
  small warm place with the whole night outside it. She talks the way she
  always talks, low against your ear, telling you exactly what she means to
  do next, and then doing it, and she's good at it and likes it and makes no
  secret of either. But there are gaps, tonight. Places where she stops
  mid-sentence and doesn't finish, and you don't need her to. You wake with
  her hair across your chest and the sun already up. She is dressed, and
  counting.
- `[otherwise]` *(existing, slightly extended)* She takes the coins first
  and your hand second, and leads you up Rook's narrow stairs. The blue room
  smells of lavender and lamp oil, and the bath is warm, at least to begin
  with. She undoes your buckles as if she has done a great many of them,
  and laughs at the last one. After that the door is shut, and what happens
  behind it is slow, and warm, and funny, and nobody's business but yours:
  her hair coming down, her mouth at your ear, her hands everywhere they're
  welcome and nowhere they're not. For a few hours the road and the dead on
  it are a long way off. You wake with her hair across your chest and the
  sun already up. She is dressed, and counting.

> **Note for the data:** the existing `otherwise` text opens with the coins
> and the stairs. If `stairs` ships, cut that clause from the cut-away so it
> isn't said twice: start at "The blue room smells of lavender…".

Next → `morning`

#### Beat sheet for slot 1: `sella.night` (for the owner's writer)

- **Mood and pacing.** Unhurried. A craftswoman at her craft: she has done
  this hundreds of times and is still interested in it, and that interest
  is what makes it warm. The scene has the rhythm of a good evening's talk,
  with laughter in it, and it should be funny in the way real intimacy is
  funny (the stuck buckle, the jug, the bathwater on the floor). Long
  middle, no rush to the end. The lamp is turned down early; the light is
  blue and low.
- **What she wants.** To do good work, and to enjoy it, which she does. To
  find out who the survivor is by how they touch someone, because that is
  how she reads people, and because she'll be asked. To keep it light.
- **What she fears.** The edge where it stops being work. She approaches it
  once and backs off with a joke.
- **What the survivor wants.** Warmth after the road and the dead. To be
  somewhere the night isn't.
- **What the survivor fears.** (Unspoken, and they don't know it.) The cold
  in them. The arcanist burns; everyone else is a little too warm in the
  dark, and Sella notices.
- **Consent, on the page.** She sets the rules aloud ("Anything you'd rather
  I didn't, say so") and keeps checking in, in her voice, as play: questions
  that are also offers. The survivor answers. Keep that call and answer in
  the scene; it is part of her craft.
- **The emotional turn.** Late, once, in a quiet moment: she stops being
  Sella-at-work for the space of a breath. She looks at the survivor's face
  as if she means to remember it, catches herself doing it, and turns it into
  a joke ("Don't look at me like that; you'll put the price up."). The
  tenderness shows at the edges and is put away quickly. Don't resolve it.
- **Callbacks.** The fourth step and the ninth. "Talk's free. The rest
  isn't." The bath "warm, at least to begin with". Rook's thin walls and her
  deaf left ear. The calling's line from the lead-in (the steel, the
  knuckles, the heat, the quiet feet). Variant: after a death, the cold under
  the warm water.
- **Sex variants.** For a man and for a woman survivor, write the same
  scene beats; she is equally at home with either, and the text should not
  make either the exception (see `say_woman`).
- **Ends on.** Her asleep across the survivor, her hair on their chest, the
  lamp burned out, and the sun up through blue glass. The cut to the
  morning: she is dressed, and counting.

---

### `sella.rest_night` and `sella.rest_night_paid` **(new: paid, and only sleep)**

`rest_night` comes from `price` (pay at the foot of the stairs);
`rest_night_paid` from `stairs` (already paid). Same text.
**Effects:** (`rest_night` only: `gold −15`); `sella.nights +1`; rel `sella`
affection +6, trust +8; condition `rested` 1 day (not `warmed`); set
npc flag `sella` `say:rest`.

**SELLA:** Sleep. (She looks at you as if you've asked her to recite
something in a foreign tongue.) You've paid fifteen gold to sleep.

**YOU:** Yes.

**SELLA:** ...Lie down, then. No. Boots off; Rook'll have my hide. Shift
over. I'm not sitting up all night in a chair. I've done that for worse
money.

**NARRATOR:** She lies down on top of the quilt with all her clothes on, and
you under it, and for a while she talks: about Rook, about Holloway's feet,
about a man from Low Kiln who wanted her to bark. You don't hear the end of
the man from Low Kiln. Some time in the night you half wake and she isn't
talking. She's lying on her side, watching you, the way you'd watch weather.

Next → `rest_morning`

### `sella.rest_morning` **(new)**

**SELLA:** Fifteen gold to watch you snore. Best money I ever made. (She's
already dressed. She doesn't count it.) Don't tell anyone. They'll all want
it, and then where will I be? Rich and bored.

- `[when trait risen_once and not sella.felt_cold]` *(adds, before)*
  (She's sitting on the edge of the bed with her hand flat on your chest.)
  You ran hot all night. Like lying next to a stove. And now look at you.
  Cold as the river. {set `sella.felt_cold`}

Choices: as `morning`.

---

### `sella.morning` *(existing node, more variants and choices)*

**SELLA:**
- `[when trait risen_once and not sella.felt_cold]` **(new)** (She's sitting
  on the edge of the bed, frowning, with her palm flat on your breastbone.)
  You ran hot all night, love. Like sleeping next to a stove. And now you're
  cold as the river. ...Rook's got a word for that. It's not a nice word.
  Get up and eat something. {set `sella.felt_cold`; if not `sella.free`, also
  set `sella.cold_sold`}
- `[when sella.nights >= 3]` *(existing)* You're getting to be a habit,
  {name}. I don't mind. Rook does; she says you're wearing out the stairs.
  Go on, the day's wasting, and somebody out there needs killing.
- `[when sella.nights == 2]` **(new)** Two nights. ...You make a noise in
  your sleep, you know. Like you're arguing with somebody. You lose. Every
  time.
- `[otherwise]` *(existing)* You snore, by the way. Not badly. Go on, then.
  Come back in one piece; the pieces are what I like.

Choices:
- "(Tell her where you come from.)" `once:past` → `past` *(existing)*
- "Did I talk in my sleep?" `once:sleeptalk` → `sleeptalk` *(existing)*
- "The bolt on the door. You never shoot it." `<show sella.nights >= 2>`
  `once:door` → `door` **(new)**
- "Sleep a little longer first." `action: rest` *(existing)*
- "Until next time." → end *(existing)*

---

### `sella.past` *(existing node, new effects)*

Text *(existing)* by background. New variant line, added in front when the
survivor already knows who buys:

- `[when npc flag sella once:buyers]` **(new, adds before the background
  line)** (She goes still when you start. You know who buys what's said up
  here. She knows you know. You tell her anyway.)

**Effects** *(existing)*: set `sella.heard_past`; affection +4.
**(New):**
- if `once:buyers`: set `sella.told_knowing`; rel `sella` trust +10.
- if not `sella.free`: set `sella.past_sold`. (Then `vonnra.f_past` reads
  `sella.past_sold` in place of `sella.heard_past`; see ARCS §8.3.)

**SELLA** **(new closing line, when `once:buyers`)**: ...You know where that
goes, love. You know exactly where. (She doesn't say anything else for a
while. Then:) Go on. Out. Before I start charging you for the sentiment.

---

### `sella.door` **(new: a confidence)**

**Gate:** `sella.nights >= 2`, from `morning`. **Effects:** rel `sella`
affection +5.

**SELLA:** That? It's Rook's. (She sits on the bed to do up her boots, and
doesn't look up.) Working nights it stays drawn back. Rook's got a key and a
cudgel, and if a man turns funny she's up those stairs before he's finished
turning. I've needed her twice in seven years. Once for a drover. Once for a
priest, and I'll not say which. ...So, no. I've never shot it. It's not my
door. Nothing in here's my door.

Choices:
- "Seven years. You must have been young." → `door_years`
- "Whose door would be yours?" → `door_south`
- "Until next time." → end

### `sella.door_years` **(new)**

**SELLA:** Twenty-two, and sure I was cleverer than everyone in the valley.
I was right about most of them. (She laughs, low.) I'm twenty-nine, love,
since you're doing sums. Seven years at the top of Rook's stairs, and I've
only fallen down them twice.

- "Whose door would be yours?" → `door_south`
- "Until next time." → end

### `sella.door_south` **(new)**

**SELLA:** I told you. A house in the south. A door that locks from the
inside. (She stands, and checks her hair in the jug, and doesn't look at
you.) And somebody who knocks.

- "Until next time." → end

---

### `sella.free` *(existing node, gate and choices changed)*

**Entry gate (change):** add rel `sella` trust ≥ 15 (ARCS §8.4).

**SELLA** *(existing)*: Put your purse away, {name}. Tonight I'm not
working. ...Don't look at me like that. Don't make it strange.

Choices:
- "Then lead the way." → `free_stairs` **(changed from `free_night`)**
- "Not tonight, Sella." → `free_decline` **(changed from `hub`)**

### `sella.free_decline` **(new)**

**Effects:** set `sella.free_declined`. No stat loss.

**SELLA:** Your loss, love. Literally; I'm worth a fortune. (She means it
lightly, and very nearly manages it.) ...No, it's all right. It is. I'll not
ask twice. I don't ask twice. (She pats your cheek, once, like a regular's.)
Go on. Rook's stew's still warm.

- "Goodnight, Sella." → end

### `sella.free_ask` **(new: the survivor asks, once)**

Offered on `hub`/`again`: "The other night. What you offered. Does it
stand?" `<show sella.free_declined and not sella.free and time night>`
`<when rel sella trust >= 15>` locked: *Not now. Not like this.*
`once:free_ask`.

**SELLA:** (She looks at you for a long moment, as if you were a coin she
was checking for clipping.) I said I'd not ask twice. I never said I'd not
answer. ...Come on, then. Before I think better of it. I'm thinking better
of it already. Come *on*.

→ `free_stairs`

---

### `sella.free_stairs` **(new: the lead-in to the free night)**

**NARRATOR:** She doesn't take your hand on the stairs, or your sleeve. She
goes up ahead of you, and on the fourth step she forgets to step over it,
and it creaks, loud as a shout, and she stops dead with one foot on it and
laughs at herself, and that's worse, somehow, than if she hadn't.

**NARRATOR:** In the blue room she turns the lamp up, not down. She stands
with her back against the door as if somebody might try it.

**SELLA:**
- `[when sella.told_knowing]` I keep thinking about you sitting on my bed
  telling me where you're from. Knowing who'd hear it by morning. (She
  shakes her head.) Nobody does that. Nobody's *ever* done that.
- `[otherwise]` I don't know how to do this one. ...That's a lie. I know
  how. I don't know how to do it like this.

Choices:
- "Then don't do anything. Come here." → `free_bolt`
- "Do you want to?" → `free_want`
- "We could just sleep." → `free_sleep`
- "(Stop here.)" → `free_stop`

### `sella.free_want` **(new)**

**SELLA:** Ask me that again and I'll cry, and I don't cry, so don't. (She
takes a breath.) Yes. ...Yes. There. Said it. Come here.

→ `free_bolt`

### `sella.free_stop` **(new)**

**SELLA:** (She lets out a breath she's been holding since the stairs.) All
right. (And it is; you can see it is.) All right. ...Sit with me, then.
Just sit. I've never just sat in here with anybody. Rook'd think we'd died.

**NARRATOR:** You sit on the bed with your backs to the wall, and she tells
you about the house in the south: which room faces the sun; the colour of
the door; the knock. Then she sends you down the stairs, and stands at the
top to watch you skip the fourth.

**Effects:** rel `sella` trust +10. Does **not** set `sella.free`. She may
offer again: clear npc flag `say:free`, with a `later` of 3 days.

→ end

> **Why:** if the survivor stops, she is relieved as well as sorry, and the
> scene lets both be true. She offers again in a few days. It isn't a test
> they've failed.

### `sella.free_sleep` **(new)**

**SELLA:** (She laughs, properly, the first time tonight.) You and your
sleeping. ...Yes. All right. Yes.

**NARRATOR:** She reaches behind her without looking and finds the bolt, and
shoots it. Then she gets into the bed in her shift, and you get in beside
her, and she lies with her back against you and pulls your arm over her
like a blanket. She's asleep before you are. She's still there when you
wake.

**Effects:** set `sella.free`; rel `sella` affection +10, trust +15;
condition `rested` 1 day.

→ `free_morning`

### `sella.free_bolt` **(new: the bolt)**

**NARRATOR:** She reaches behind her without looking and finds the bolt. It
sticks halfway; nobody has ever shot it. She has to turn round and put her
shoulder to it, swearing, and it goes home with a sound like a full stop.

**SELLA:** (Her back is still to you. Her forehead is against the door.)
...There.

→ `free_night`

---

### `sella.free_night` *(existing node, extended cut-away; slot 3)*

**Effects** *(existing)*: set `sella.free`; affection +10, trust +10;
`warmed` 1 day. **(New):** `night.spent`.

**NARRATOR:**
- `[when settings.intimacy == "full"]` `[explicit scene: Sella and {name},
  the blue room, not for money for the first time; slower and less sure than
  her working nights, the professional's patter dropping away, laughter and
  then none; a door she locks herself — to be written]` *(existing; see beat
  sheet)*
- `[when sella.told_knowing]` **(new)** She doesn't talk the way she talks
  for money. She doesn't talk at all, at first. She undresses you as if
  she's never done it before, which is absurd, and she knows it's absurd,
  and halfway through she laughs into your neck and can't stop. Then she
  does stop, and the laugh goes somewhere else. She's slower than on her
  working nights, and less sure, and once she stops altogether with her
  forehead against yours and just breathes, and you wait, and she goes on.
  The lamp burns down on its own. Nobody turns it. In the dark, much later,
  she says into your shoulder, "You told me anyway," and nothing else, and
  then she sleeps.
- `[otherwise]` *(existing, extended)* The blue room, and the lamp, and the
  bolt, which she shot herself, which she has never done. She doesn't talk
  the way she talks for money. For a while neither of you talks at all. She
  is slower than you have known her, and less sure, and there is a moment
  when she stops with her hands on your face and just looks, as if she is
  learning it, and doesn't make a joke of it. Later she lies awake, and you
  can feel her deciding something, and then she sleeps.

Next → `free_morning`

#### Beat sheet for slot 3: `sella.free_night`

- **Mood and pacing.** Slow, then slower. Unsure. The opposite of slot 1 in
  every craft sense: she has no routine for this and keeps reaching for
  one and dropping it. Long silences. Lamp up, not down: she wants to see,
  and to be seen, which she never allows on working nights. The bolt is
  shot and stays shot, and the scene should keep the door in view.
- **What she wants.** To have one night that is hers. To find out what it
  is like with nobody paying, which she half suspects is something she
  can't do.
- **What she fears.** That she can't. That the patter is all there is.
  That she'll want the knock. Being looked at with pity (she isn't, and
  the survivor should never pity her).
- **What the survivor wants.** Her, not the blue room.
- **What the survivor fears.** That this is a kindness she'll regret, or a
  sale they can't see.
- **Consent, on the page.** Twice, plainly. The survivor asks "Do you
  want to?" (or not; if not, she says it unasked, partway through: "I want
  this. Just so you know. I want it."). And once she stops, and the
  survivor waits, and she goes on. The scene shows that either of them
  could stop at any point.
- **The emotional turn.** The patter tries to start ("Now, love, what you
  want is—") and she hears herself and stops, and laughs, and the laugh
  turns into something that isn't a laugh. From there she is nobody's
  professional. If `sella.told_knowing`: she says "You told me anyway."
- **Callbacks.** The bolt (Rook's, never shot, sticking). The fourth step
  creaking because she forgot it. "Somebody who knocks." "Don't make it
  strange." The lamp left to burn down on its own.
- **Sex variants.** Same beats either way.
- **Ends on.** Her lying awake in the dark, deciding something; the
  survivor feeling her decide; her sleeping. Then the morning, when she's
  still there, which she never is.

---

### `sella.free_morning` *(existing node, choices added)*

**SELLA** *(existing)*: (She's still there when you wake, which she never
is.) Don't tell Rook; she'll want a third of nothing, on principle. ...And
don't tell me anything up here you'd not want Vonnra to hear. I mean that
kindly. It's the kindest thing I've said to anyone in a year.

Choices **(new)**:
- "Then I'll tell you things downstairs." → `free_m_downstairs`
- "Who'd you sell it to? If I did?" → `free_m_who`
- "(Kiss her.)" → `free_m_kiss`
- "Until next time." → end

### `sella.free_m_downstairs` **(new)**

**SELLA:** (She laughs.) Downstairs Rook hears everything and charges
nobody. You'd be better off with me. ...No. You wouldn't. That's the point,
love. Go on.

→ end

### `sella.free_m_who` **(new)**

**SELLA:** You know who. Everybody pays; she pays most. (She pulls the quilt
up to her chin.) I said *don't tell me*. I didn't say I'd sell it. ...I
didn't say I wouldn't, either. I don't know, {name}. That's the honest
answer, and I'm out of practice at those. Don't make me practise before
breakfast.

→ end

### `sella.free_m_kiss` **(new)**

**NARRATOR:** She lets you. Then she pushes you off by the face, gently, with
the flat of her hand. "Out. Before I get used to it." She's smiling. She
doesn't stop smiling until you're down the stairs, and you know that because
the ninth step creaks behind you: she came down two steps to watch you go,
and forgot it.

→ end

---

### `sella.refuse_roost` **(new: she refuses)**

**Gate:** the paid night is chosen while `history burned_roost` is set and
npc flag `sella` `cb:burned_roost` is not (so it plays once, the first time
she's seen you since). Comes from `stairs`, at the top of the stairs.
**Effects:** `gold +15` (all of it back). Sets npc flag `sella`
`cb:burned_roost` (so the existing `cb_burned_roost` line is folded in here).

**NARRATOR:** At the top of the stairs she stops with her hand on the door.

**SELLA:** They're saying you burned the Roost with folk still in it. (She
puts the coins back in your hand, all of them.) I don't judge, love. It's
bad for business. But I can smell it on you, and I'm not working with that
in the room. ...Come back when I can't.

- "...Goodnight, Sella." → end

---

### `sella.say_keegan` and `sella.say_rav` **(new: remarks, once each)**

Entries, after `say_maeca`. Each sets its own `say:` flag, next → `hub`.

`say_keegan` `<when keegan.supper>`:
**SELLA:** The knight's been asking Rook what you like for breakfast. In
full sentences, love. With a list. ...She's going to read you a chapter
after. You know that. You'll have to sit through the whole chapter.

`say_rav` `<when rav.back_room>`:
**SELLA:** You went round the back of the Flagon after closing. Rav's been
up my stairs twice in seven years, and both times to lance something. Be
kind to him. He's softer than he drinks.

---

## Act 2

These beats need Act 2 facts that don't exist yet; they're written for the
Act 2 writer and drafted here as script, not data.

### `sella.fortune` **(new: the bill)**

**Entry:** first visit after `chapter.done`, when `sella.past_sold` (or
`sella.cold_sold`) is set and npc flag `say:fortune` is not. Sets
`say:fortune`.

**NARRATOR:** She's waiting at the foot of Rook's stairs, which she never
does, with her arms folded, which she never does either.

**SELLA:** You've been up the Toll Tower. I can see it on you. (She doesn't
move out of the way.) Go on, then. Say it. You've earned saying it.

Choices:
- "You sold her my life." → `fortune_sold`
- "I knew you would. I told you anyway." `<show sella.told_knowing>` →
  `fortune_knew`
- "(Say nothing. Go past her, up the stairs.)" `<show not sella.free>` →
  `fortune_silent`

### `sella.fortune_sold` **(new)**

**SELLA:** I sold her what you told me. I told you I would, love. You asked
who buys, and I told you, and that's the only promise I ever made up those
stairs, and I kept it. (A beat.)
- `[when sella.free]` *(adds)* ...And then I stopped. The morning I didn't
  take your money. Didn't you hear me? I said it as plain as I say
  anything.
- `[otherwise]` *(adds)* I'm not sorry. You'd not believe me if I was.

Choices:
- "I heard you. It's done." → `fortune_forgave`
- "What would it cost to sell her something else?" → `fortune_hired`
- "We're finished, Sella." → `fortune_ended`

### `sella.fortune_knew` **(new)**

**SELLA:** (She unfolds her arms.) I know. I've been trying to work out why
for a week. ...Was it a test? It doesn't matter. I'd have failed it either
way, and you did it anyway. (Quieter.) Nobody's ever told me a thing they
knew I'd sell. Not once in seven years.

→ `fortune_forgave`

### `sella.fortune_forgave` **(new)**

**Effects:** set `sella.confronted` = `forgave`; rel `sella` trust +15.

**SELLA:** (She steps aside, finally.) Rook's put the kettle on. She's been
listening at the hatch this whole time, love; she always does. ...Come up.
Not for anything. Just come up.

→ end

### `sella.fortune_hired` **(new)**

**Effects:** set `sella.confronted` = `hired`; rel `sella` trust +5,
affection −5.

**SELLA:** Thirty, and you tell me what. (She nods, once, brisk, and the
warmth goes out of her face and something easier comes into it.) Business.
Fine. I like business. I know where I am in business.

→ end

### `sella.fortune_ended` **(new)**

**Effects:** set `sella.confronted` = `ended`; rel `sella` affection −20. No
further nights: `price` and `free` are locked while `ended`, with the
reason *She won't take your money now.*

**SELLA:** (She nods, once.) Fair. (And she means it; that's the worst of
it.) The bolt's back to being Rook's, then. ...Mind the fourth step on your
way out, love. It's the only advice I've ever given anybody for nothing.

→ end

### `sella.fortune_silent` **(new)**

Treated as `hired`'s mood without the deal: `sella.confronted` = `silent`.
She follows you up and says nothing either, and the night, if you buy one,
is a working night with nothing under it. (The Act 2 writer may fold this
into `hired`.)

---

### `sella.what` **(new: "What are you?")**

**Entry:** after Act 2's turn (bible §7.11; fact proposed as
`survivor.knows_risen`, set by the turn), the first visit at night, if
`sella.felt_cold` or `sella.sleeptalk`, and `sella.confronted` ≠ `ended`.

**SELLA:** Hot at night. Cold as the river by morning. A name in your sleep
you can't remember awake. (She's sitting on the edge of the bath, not
looking at you.) I've had a lot of people in that bed, love. I've never had
one who wasn't all there in the mornings. ...What are you?

Choices:
- "Dead, I think. I drowned at the ford, and got up." → `what_told`
- "Tired." → `what_lied`

### `sella.what_told` **(new)**

**Effects:** set `sella.asked_what` = `told`; rel `sella` trust +20.

**SELLA:** (She doesn't laugh. She doesn't do anything at all for a long
moment.)
- `[when sella.free and sella.confronted != hired]` ...Well. You're the
  best-mannered dead I've ever had. (Then, much quieter:) Does it hurt?
- `[otherwise]` Don't tell me that. Not up here. Not when I— (She stops.)
  Too late. Christ. (She puts her face in her hands, and then takes it out
  again, composed.) Does it hurt?

Choices:
- "Only at dawn." → `what_dawn`
- "I don't know." → `what_dawn`

### `sella.what_dawn` **(new)**

**SELLA:** Then come here before it's dawn.

**NARRATOR:** She holds you the rest of the night, as if she could keep you
warm by main force. At first light she feels it go out of you, the heat,
all at once, like a lamp turned down, and she holds on anyway.

**Effects:** `night.spent`; condition `warmed` 1 day.

→ end

### `sella.what_lied` **(new)**

**Effects:** set `sella.asked_what` = `lied`.

**SELLA:** Tired. (She looks at you the way she looked at you the first
night, pricing you.) All right, love. Tired. ...I know a lie when I'm paid
for one. I just don't usually get them for free.

→ end

---

### `sella.silver` **(new: the man with silver cuffs)**

**Entry:** Act 2, before Silverstair, the first visit after
`sella.asked_what` is set (or after any three Act 2 nights, if it never
is).

**Variant A**, `sella.free` and `sella.confronted` in (`forgave`, unset):
**SELLA:** A man came up my stairs last night. Silver ink on his cuffs, and
lovely manners. He didn't want me; he wanted you. What nights you come.
What you say. Whether you're warm. (She shrugs one shoulder.) Offered forty.
...I said I'd never heard of you. I've never turned down forty in my life.
Don't look at me like that. I said don't make it strange.
→ choices: "Thank you." / "(Kiss her.)" → end. Rel trust +10.

**Variant B**, otherwise:
**SELLA:** (She's at the foot of the stairs, and she doesn't move aside.)
Not tonight, love. (She doesn't say why. She doesn't look at you.) Not
tonight. Not— just not.
Sets `sella.sold_sallow`. → end.

**Later (Act 2 writer)**, after the ambush at the Last Lamp (Holloway's
letter, beat 3, the variant `sella.sold_sallow` opens):
**SELLA:** Forty. He paid forty. I've never been paid forty for anything in
my life. ...I'd have told you, if you'd been mine to tell. You weren't. You
made sure you weren't.

---

### `sella.lie_ask` **(new: Act 2 beat 9)**

Offered on `hub`: "I need Vonnra to hear something that isn't true."
`<show sella.confronted != ended>`.

**SELLA:**
- `[when sella.free and sella.confronted in (forgave, unset)]` For you?
  Nothing. ...Don't tell anyone. I've a reputation.
- `[otherwise]` Thirty. And it's cheap at that, because she'll know. In the
  end. She always does.

Choices (each sets `sella.lied` = `true` and `sella.lie` to its value;
the paid variant also `gold −30`, `<when gold >= 30>`):
- "That I won't go down with her. Whatever she asks." → `lie_done`
  {`sella.lie` = `refuse`}
- "That I've left the valley." → `lie_done` {`sella.lie` = `gone`}
- "That my name is Lark." `<show wayfinder.name == false>` → `lie_done`
  {`sella.lie` = `lark`}
- "Never mind." → `hub`

### `sella.lie_done` **(new)**

**SELLA:** Done. She'll have it by supper. (She's quiet a moment.) She'll
thank me for it, you know. She always thanks me. Very still, and very
polite. ...It's the thanks I mind.

→ end

---

### `sella.cart` **(new: the south road; Act 2 beat 8)**

**Entry:** `sella.lied`, and Vonnra's clerk has called (Act 2 tick), and
`kiln.lit` (or the bible's alternative: the cart comes regardless; it only
kills her if the Kiln Ford is lit).

**NARRATOR:** She's in the yard with a carpet bag and her good cloak, the
blue one, and a face like she's about to be funny.

**SELLA:** Vonnra's had her clerk round. Very polite. Asked after my health.
Asked twice. (She hefts the bag.) I'm taking the toll cart south in the
morning. Don't look like that, love. I've always wanted to see the south.
I've a house to find.

Choices:
- "Not the south road. The Kiln Ford's lit." `<show kiln.lit and the
  survivor knows it (kiln.known)>` `<when rel sella trust >= 30>` locked:
  *She'd need to trust you more than she trusts the road.* → `cart_stay`
- "Then go. With my blessing." → `cart_go`
- "Come north. With me." `<show sella.free and keegan.route != north (any
  companion slot free)>` → `cart_north` *(Act 2 writer's call: a companion
  Sella is not in the bible. If not wanted, drop this.)*

### `sella.cart_stay` **(new)**

**SELLA:** Lit. (The bag goes down.) By whom? No. Don't tell me. I can guess
who. I can guess everything, up those stairs. (She laughs, badly.) So I sit
here and wait for her clerk to come back.

**NARRATOR:** Rook comes out into the yard, takes the bag off the ground and
carries it back inside without a word. Sella watches her go.

**SELLA:** ...Well. That's that decided, then.

**Effects:** set `sella.fate` = `kept`.

→ end

### `sella.cart_go` **(new)**

**SELLA:** (She kisses your cheek, quick, a regular's kiss.) Somebody'll
knock, one day. Mind it's you.

**Effects:** set `sella.fate` = `risen` if `kiln.lit`, else `south`.

→ end

> **What follows (Act 2 writer):** with `kiln.lit` the cart is found at the
> Kiln Ford. No driver. The blue cloak is on the far bank. She is the second
> Unchained. Her first scene risen is in Act 3 (below).

---

### `sella.eve` **(new: the night before the gate)**

**Entry:** `romance.eve` = `sella`.

**NARRATOR:** The whole town is awake. Rook has lit every lamp she owns and
is refusing to say why. Sella is at the top of the stairs before you are,
holding the door.

**SELLA:** No money. Don't even reach for it. (She pulls you in and shoots
the bolt; it doesn't stick now, she's oiled it.) I've been making jokes all
day. I've made forty. I'm out. ...I've got nothing funny left, {name}. So
you'll have to have me without.

Choices:
- "(Kiss her.)" → `eve_night`
- "Lie down with me. Just that." → `eve_sleep`
- "(Stop here.)" → `eve_stop`

`eve_stop`: **SELLA:** (She nods, hard.) Then stay till it's light. You can
do that much. → `eve_sleep`.

`eve_sleep`: **NARRATOR:** She lies with her back to you and your arm across
her, the way she did once before, and doesn't sleep, and neither do you.
At first light she says, "Go on, then," and doesn't let go for a while. →
end.

### `sella.eve_night` **(new; a tone variant of slot 3)**

**NARRATOR:**
- `[settings.intimacy == "full"]` `[explicit scene: Sella and {name}, the
  blue room, the night before the war at the north gate; no money, no jokes
  left; the bolt oiled so it doesn't stick; urgent and then very slow, as if
  slowing down could make the night longer — to be written]`
- `[otherwise]` She has no jokes left, and it turns out she doesn't need
  them. She is fierce, at first, holding on as if somebody's going to come
  through the door, and then she isn't fierce at all, and it goes slow,
  slower than anything, as if slowing down could stretch the night. Once
  she says your name, just that, and it sounds like a question, and you
  answer it. Neither of you sleeps. At first light she says, "Go on, then,"
  and doesn't let go for a while.

**Beat sheet (eve variant):** urgency first: she wants to stop time and
knows she can't. The turn is when she slows deliberately, as if by choice
she could make the hours longer. Callbacks: the bolt (oiled now; she did
that herself, earlier, for this); "somebody who knocks"; the first night's
"come back in one piece; the pieces are what I like". Ends on: first light
through blue glass, "Go on, then", and her not letting go.

---

## Act 3 (outline)

### On the stair, if she rose (`sella.fate` = `risen`)

She is where the Legion's dead let the Morrow's light pass. She knows the
survivor at once.

**SELLA:** So this is it. (She holds up her hands and looks at them, at the
light in them.) You might have said it was cold. ...You did say. "Only at
dawn." You lying sod.

If `sella.asked_what` = `told`: she holds the survivor's hand on the stair,
and both their hands are lit, and she says, "Well. Now we're both warm at
night," and laughs, and it's her real laugh.

The ending's choices about the second Unchained (bible §8) are hers here:
- **Ending A, she is chosen to lie down in the chain:** she says, "Somebody
  knocks, and it's this," and goes. No pleading. One line back: "Mind the
  fourth step."
- **The coin, given to her:** she climbs back into daylight an ordinary
  mortal. Epilogue: the house in the south.

### Epilogue lines

- `sella.fate` = `south` or the coin: *A house in the south, with a door
  that locks from the inside. Somebody knocks on it most evenings.* With
  the survivor living and her lover: *It's you.*
- `kept`: *The blue room kept its lamp lit through the war. Rook took a
  third of nothing, on principle.*
- `ended` / gone: *She left by the north road the day it opened. Nobody in
  the valley ever sold her anything again.*
