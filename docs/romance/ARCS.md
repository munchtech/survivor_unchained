# The romances: arcs

How love goes in Survivor Unchained, person by person: how it grows, what it
costs, how the player's choices bend it, and the facts that carry it. The
scenes themselves are in `scenes/`, and the data drafts are in `data/`.
Everything here rests on `STORY_BIBLE.md` (sections 5, 7, 8 and 11) and is
spoken in the voices of `VOICES.md`. Where this document needs something the
bible does not yet have, it says so and marks it **(new)**.

---

## 0. What the romances are for

**Romance carries the intrigue.** In this valley nobody's bed is private.
Sella sells what is said in hers. Maeca's is a hunter's blind on the edge of
the Pack's ground. Keegan's handbook has a chapter about her lover. Rav's
brother is the bandit on the Old Road, and Ysolde writes her lovers' names
down for money. Every arc here moves a thread of the main story. A romance
the player skips leaves a hole in what they know.

**Trust grows from what the survivor does and says, never from gifts.**
Nobody here can be bought with a present. Sella can be bought, of course, but
that is the point of her, and it is the one thing her arc is about getting
past. The axes grow from three things:

1. **What the survivor does in the story**: curing the wolves or killing
   them, burning the Roost, telling Brannoc the truth, accusing Vonnra.
   Lovers hear about all of it, and each of them weighs it differently.
2. **What the survivor reveals**: their past, their sleep, their deaths,
   and in Act 2, what they are. Every lover asks something about the
   survivor once. Answering truthfully costs something, because in this
   valley someone is always listening, and that is what makes the answer
   count.
3. **What the survivor keeps back**: who signed for the boots, who gave
   Redcowl the night, who sold their name. A secret kept from a lover is a
   debt. It always comes due in Act 2, and the arc turns on whether the
   survivor paid it before it came due.

**Each lover finds out something about the survivor's body.** The survivor
is dead and does not know it. Whoever lies beside them at night and wakes
beside them at dawn is the first person who could tell. Each lover notices a
different sign, in their own trade's terms, and none of them knows what it
means until Act 2 (beat 11, "What you are"):

| Lover | What they notice | When | Fact | Lands |
|---|---|---|---|---|
| Sella | You run hot at night and you're cold as the river by morning; you say a name in your sleep (`sella.sleeptalk`, existing) | Act 1, the morning after a paid night | `sella.felt_cold` **(new)** | Act 2: what she can sell, and who to (§1.6) |
| Maeca | The Pack lies down round the Blind when you're in it; at dawn your heart is slow "as a bear's in January" | Act 1, the Blind | `maeca.heard_heart` **(new)** | Act 2: she already knew, so the turn does not break her |
| Keegan | The signs of chapter four, one by one | Act 1 (`keegan.saw_risen`, existing) and Act 2 | `keegan.asked` **(new)** | Act 2 beat 2: the question |
| Rav | A doctor's two fingers on your wrist in the dark: no pulse for a count of eleven, then a pulse | Act 2, the back room | `rav.felt_pulse` **(new)** | Act 2 beat 11: he says it in a doctor's words |
| Ysolde | Nothing. She knew before anyone, and wrote it down and sold it | Act 2, Silverstair | `wayfinder.confessed` **(new)** | Act 2 beat 10 |

None of them says "Unchained" in Act 1. They talk round it, as the voices
rule says.

**Every intimate moment is chosen twice, by both people.** Every love scene
has the same shape:

1. **An invitation** that either person can decline. Declining is never
   punished with a stat loss. Some scenes reward it, because the other
   person notices the care.
2. **A lead-in** written in full: the walk there, the room, what is said,
   the first touch. Inside the lead-in there is always one more choice, the
   last place to stop ("(Stop here.)" / "Not like this."). The other person
   has that choice too. Several scenes are written so that **they** stop it,
   on nights that are wrong for them (§1.5, §2.5, §3.5), and the scene treats
   that as a kindness, not a failure.
3. **The moment**: the cut-away, which is sensual and close and ends before
   the act itself. Beside it sits the `[explicit scene: ...]` slot behind
   `settings.intimacy == "full"`, and in the scene files a beat sheet for
   the owner's writer.
4. **The aftermath**, written in full: lying awake, what is said in the
   dark, the morning. **The arc moves in the aftermath.** Facts are set
   there, and confidences are given there.

**All five are adults, and the text says so.** Sella is twenty-nine and has
kept the blue room since she was twenty-two ("Seven years at the top of
Rook's stairs and I've only fallen down them twice."). Maeca is in her
thirties; she was a grown soldier of the Ashford garrison ten years ago.
Keegan is twenty-six, and was a lecturer at Saint Wend's before she took the
oath. Rav is in his fifties. Ysolde is in her fifties, with a brother twelve
years risen.

**Any survivor, any lover.** All five arcs are open to a survivor of either
sex. Lines that change by sex are written as variants, the way
`sella.say_woman` and `redcowl`'s "lad"/"lass" are. Nobody in this valley
treats it as remarkable more than once.

---

## 0.1 The tones of a love scene

Each love scene can be played in more than one mood, and the mood is decided
by the world, not by a menu. The scene files mark each variant with the
condition that picks it:

| Tone | What decides it | Who has it |
|---|---|---|
| **Tender** | The default once trust is high | All |
| **Funny** | Sella's working nights; Rav always, until he isn't | Sella, Rav |
| **Guarded** | Something kept back that the other person can feel: a secret not yet told, a lie told | Sella (`sella.confronted` = `hired`), Maeca (`maeca.boots_hid`), Keegan (`keegan.asked` = `silence`) |
| **Grieving** | A death the night belongs to: Greymuzzle's, Redcowl's, Edric's freedom costing someone | Maeca, Rav, Ysolde |
| **Desperate** | The eve of the war at the north gate (Act 2 beat 12) | Whoever the survivor spends `romance.eve` with |
| **Joyful** | Something won: the cure, the cages opened, a confession forgiven | Maeca (first night after the cure), Ysolde, Sella (the free night when she has been forgiven) |

---

## 0.2 Systems this needs

The flags and counters below are ordinary facts and per-person flags in the
language the game already speaks. Only the items marked **System** need code.

- **System: the intimacy setting.** `settings.intimacy` (already read, never
  written; the lead wires the setting). Nothing new.
- **System: the eve (new).** At Act 2 beat 12, the night before Sallow's
  people reach the north gate, the game offers one night, and only one,
  among the survivor's open romances. This is a plain choice on a narrator
  node that lists each lover whose route is open, plus "Alone" and "On the
  wall". It sets `romance.eve` to the person's id (or `alone`, or `wall`).
  It needs a hook in the Act 2 flow where the war beat begins.
- **System: lover count at the ending (new, small).** The epilogue page
  (`Chapter.cs` style) reads each `<person>.lover` and `<person>.fate`. No
  new mechanism, only new readers.
- **System: a once-per-night lockout (new, small).** A night spent in one
  bed closes the other beds until dawn. Today nothing stops a survivor from
  taking Sella's room and then walking to the Blind in the same night. The
  simplest fix: every love scene sets `night.spent` = `true`, the dawn tick
  clears it, and every invitation's `when` adds
  `{"not":{"fact":"night.spent","eq":true}}`. Each love scene already ends
  in the morning, so in practice this only matters for scenes that end
  early. Flagged, not required.
- **The Keegan companion route** (Act 2 beat 2, "she steps aside and comes
  north") is the bible's own Act 2 system. The romance only reads it
  (`keegan.route` = `north`).

All new facts are listed with their writers and readers in §7.

---

## 1. Sella

### 1.1 Who she is, in love

Twenty-nine, the blue room at the top of Rook's stairs for seven years, and
very good at what she does. Frank, funny, warm, and the warmth is also work.
She is not ashamed of her work and she is not sorry for it. Her secret is not
the sex; it is the selling. What is said in her bed goes to whoever pays most,
and Vonnra pays most.

**What she wants:** a house in the south with a door that locks from the
inside, and somebody who knocks (`t_sella`). It is an exact picture. Every
door she has had has been somebody else's to open. On working nights her
bolt stays drawn back, because Rook's rule is that Rook can always come in if
a customer turns ugly. The bolt she shoots on the free night (`free_night`,
existing) is the first door she has ever locked from the inside for herself.
Her arc is the bolt.

**What she fears:** being a person to someone who is paying for her. Being
made a story ("Don't make it strange", existing). Wanting the knock.

**The tension her arc runs on:** she will sell you, and she tells you so
(`buyers`). Every confidence the survivor gives her is given to Vonnra too.
The arc is the survivor learning that and deciding what to do with it, and
Sella deciding, without saying so, to stop.

### 1.2 How trust and affection grow

| What | Axis | Where |
|---|---|---|
| Asking about Rook (`rook`) | affection +5 | existing |
| A paid night (`night`) | affection +8, trust +4 | existing |
| Paying for the night and asking only to sleep (`rest_night`) | affection +6, trust +8 | **new**: the one thing nobody pays her for |
| Telling her your past (`past`) | affection +4 | existing |
| Telling her your past **after** she has told you who buys it (`past`, with `once:buyers`) | trust +10 more; `sella.told_knowing` | **new**: the survivor chose to give Vonnra their life rather than keep it from Sella |
| Asking about the bolt (`door`, after two nights) | affection +5 | **new** |
| The free night (`free_night`) | affection +10, trust +10 | existing |
| After the fortune: forgiving her (`fortune_forgave`) | trust +15 | **new** |
| After the fortune: hiring her to lie (`fortune_hired`) | trust +5, affection −5 | **new** |
| After the fortune: ending it (`fortune_ended`) | affection −20; no more nights | **new** |
| Act 2: telling her what you are (`what_told`) | trust +20 | **new** |
| Freeing Jory (`cb_freed_teamsters`), sparing the Roost | none (she says what she heard) | existing |
| Burning the Roost | none; she says she heard, and she "doesn't judge" | existing |

Gifts do nothing. Gold buys nights, and nights build affection slowly. The
free night needs trust as well as affection **(new gate)**: today it is
`sella.nights >= 3` and affection ≥ 25. The proposal adds trust ≥ 15, which
three nights and either the Rook question, the rest night, or the past told
knowingly will reach. A survivor who only ever pays and never talks never
gets the bolt shot. That is the arc's point.

### 1.3 The beats

| # | Beat | When | Node(s) | Gate | Sets |
|---|---|---|---|---|---|
| 1 | **Meeting** | Any time | `first` (existing) | none | |
| 2 | **The price** | Any time | `price` → `night` / `rest_night` | 15 gold | `sella.nights` +1 |
| 3 | **Friction: who buys** | After `rook` | `buyers` (existing) | `once:rook` | |
| 4 | **Mornings** | After each paid night | `morning` (extended: variants by night count, by a death, by `felt_cold`) | | `sella.felt_cold`, `sella.heard_past`, `sella.sleeptalk`, `sella.told_knowing` |
| 5 | **A confidence: the bolt** | After two nights | `door` | `sella.nights >= 2` | `say:door` |
| 6 | **The test: the offer** | Night, three nights, warmth | `free` (existing), `free_decline`, `free_ask` (new) | aff ≥ 25, trust ≥ 15 (new) | `sella.free_declined` |
| 7 | **The turning point: off the clock** | | `free_night`, `free_morning` (extended) | | `sella.free` |
| 8 | **The fortune and the bill** | Act 2's first days, if the fortune quoted her | `fortune` → `forgave` / `hired` / `ended` | `chapter.done`, `sella.heard_past` | `sella.confronted` |
| 9 | **What are you?** | Act 2, after beat 11 | `what` → `what_told` / `what_lied` | `sella.felt_cold` or `sella.sleeptalk` | `sella.asked_what` |
| 10 | **The man with silver cuffs** | Act 2, before Silverstair | `silver` | `sella.asked_what` set | `sella.sold_sallow` |
| 11 | **The lie** | Act 2 beat 9 | `lie_ask` → `lie_free` / `lie_paid` | the survivor asks her | `sella.lied` |
| 12 | **The south road** | Act 2, if the Kiln Ford is lit | `cart` → `cart_stay` / `cart_go` | `sella.lied`, `kiln.lit` (Act 2) | `sella.fate` |
| 13 | **The eve** | Act 2 beat 12 | `eve` | `romance.eve` = `sella` | |
| 14 | **The end** | Epilogue | | `sella.fate` | |

### 1.4 How the player bends it

**The tone of the love scene.**
- **Paid nights** are warm, unhurried and funny. That is the bible's slot,
  `sella.night`. The first night is all patter. By the third the patter has
  gaps in it. The night after a death (`trait` `risen_once`, the first night
  after it) is the first tender one: she finds you cold under the warm water
  of the bath and does not make a joke of it.
- **The rest night** has no sex in it. She is professionally baffled, then
  something else. ("Fifteen gold to watch you snore. Best money I ever
  made. Don't tell anyone; they'll all want it.")
- **The free night** (slot `sella.free_night`) is slow, less sure, and has
  no patter. Its mood depends on what came before it. If the survivor told
  her their past knowing who buys it (`sella.told_knowing`), she is moved and
  hides it badly. If they never told her anything, she is the one who talks,
  for once.
- **Act 2 nights** after `fortune_forgave` are joyful: she laughs in bed and
  means it. After `fortune_hired` they are guarded. She is working again,
  for you, and you both know it, and the scene says so in one line.
- **The eve** is desperate, or as near as Sella gets. She makes jokes until
  she can't.

**Refusals, on both sides, with dignity.**
- The survivor can decline the free night (`free_decline`). She takes it
  lightly ("Your loss, love. Literally; I'm worth a fortune.") and does not
  offer again. The survivor may ask, once, on a later night (`free_ask`), and
  if her trust has held she says yes, and the night is the same night.
- The survivor can end it after the fortune (`fortune_ended`). She does not
  plead. Her last line is about the bolt.
- **Sella refuses** in two places. On a night when the survivor has just
  burned the Roost (`history` `burned_roost`, `cb:burned_roost` that same
  day) she takes the money and then gives it back at the top of the stairs:
  "Not tonight. I can smell it on you. Come back when you can't." On a
  night when she has already sold the survivor to the man with silver cuffs
  (`sella.sold_sallow`), she will not take them upstairs at all. She will
  not be paid by someone she has sold. She does not say why. The survivor
  learns why later (§1.6).

**Heartbreak and betrayal: what Sella carries to Vonnra.**
Everything said upstairs goes to Vonnra until the free night, and the
fortune proves it (`vonnra.f_past`). After the free night she stops selling
the survivor, and says so in the only way she can, by warning them
(`free_morning`). She keeps selling everyone else. The bill comes after the
fortune (beat 8): the survivor has heard their own life in Vonnra's mouth.

What she carries to Vonnra depends on when the survivor told her things:

| Told her | Before the free night | After the free night |
|---|---|---|
| Their past (`sella.heard_past`) | Sold. The fortune quotes it. | Not sold. The fortune falls back to "Of before the ford, I see very little." **(change: `vonnra.f_past` checks `sella.past_sold`, new; see §7)** |
| That they run cold at dawn (`sella.felt_cold`) | Sold. Vonnra knows the survivor is what she made, sooner. **(Act 3: `vonnra.knew_early`, a line on the stair)** | Kept. |
| Their sleep-name (`sella.sleeptalk`) | Sold. | Kept. |

So the free night has a cost the player may not see coming: everything said
**before** it has already been sold. Beat 8 is where that lands.

The worst case is not Vonnra. In Act 2 a man with silver ink on his cuffs
comes up Rook's stairs for Sallow (beat 10). If the survivor ended it with
her, or never got her off the clock, she sells him the survivor: the nights
they come, that they run cold, the name they say. Sallow's men then know
which bed the survivor sleeps in, and the ambush in Act 2 beat 3 (Holloway's
letter) can happen **at the Last Lamp** instead of the north gate **(new
variant, flagged for the Act 2 writer)**. If she is off the clock, she sends
him away and tells the survivor ("I've never turned down forty in my life.
...Don't look at me like that. I said don't make it strange.").

**How the romance carries the intrigue.**
- Act 1: the pillow talk is the first Act 1 twist that pays off inside Act 1
  (bible §6). Vonnra's sight is bought.
- Act 2 beat 9: "Pay her to lie to Vonnra." If she is your lover off the
  clock (`sella.free` and `sella.confronted` ≠ `ended`) she does it for
  nothing ("Don't tell anyone. I've a reputation."). Otherwise it costs 30
  gold. Either way Vonnra knows, in the end. The survivor chooses what she
  feeds Vonnra: that they will not go down the stair; that they have left
  the valley; or a name (the survivor's false name from the Wayfinder's
  margin, if they gave one: "Lark").
- Act 2 beat 8: if the Kiln Ford is lit (Brannoc forged the last irons,
  `nell.told` `lie` or `evaded`), Sella, having lied, runs south on a toll
  cart, and drowns there and rises. **The romance can change this.** A
  survivor who knows the Kiln Ford is lit (`kiln.lit`, Act 2) and is her
  lover can tell her not to take the south road (`cart_stay`). She hides at
  the Last Lamp instead, and Rook keeps her (Rook's own turn in Act 2). A
  survivor who is not her lover, or who does not know, cannot stop her. The
  second Unchained is then Sella, and she is what the survivor is. That is
  the arc's tragedy.

### 1.5 What it costs, act by act

- **Act 1:** gold, and the survivor's past sold to Vonnra.
- **Act 2:** the bill at the fortune; the man with silver cuffs; the lie and
  what it costs her; the south road.
- **Act 3:** if Sella rose at the Kiln Ford, she is the "second Unchained"
  of ending A and B. She can be chosen to lie down in the chain, or given
  the coin. A survivor who was her lover makes that choice about someone
  who once shot a bolt for them. Her scene on the stair (Act 3, outlined in
  `scenes/sella.md`) is the arc's last love scene, and it has no sex in it.

### 1.6 Ends

| End | How | Epilogue |
|---|---|---|
| **The house in the south** | She lives; the survivor gives or pays her the way (Act 2 or the ending) | A door that locks from the inside. Somebody knocks. If `sella.lover_end` (the survivor lived and chose her): it is the survivor. Otherwise "somebody", and she lets them in. |
| **Risen at the Kiln Ford** | `sella.lied`, `kiln.lit`, not `cart_stay` | The second Unchained. Ending A or B decides her. |
| **Kept at the Last Lamp** | `cart_stay` | She keeps the blue room through the war. Rook takes a third of nothing, on principle. |
| **Gone south, alone** | `fortune_ended`, or no lie asked | She goes the day the north road opens, by the north road, and is never sold anything again. |

---

## 2. Maeca Barefoot

### 2.1 Who she is, in love

In her thirties, the last of the Ashford garrison. She held a cave mouth
barefoot because somebody signed for boots that never came, and lived three
days among the dead because an old wolf lay down across the way in. A hunter
who has never hunted a wolf. Few words, all about ground and weather and
animals. She does not talk about Ashford except in three words or fewer.

**What she wants:** the Pack well. Quiet. Someone who can keep quiet beside
her ("Most can't.").

**What she fears:** being saved again, and owing it. Losing Greymuzzle, who
is old. The name at the bottom of the boot ledger, and what she will do when
she reads it.

**Her arc is the boots.** The romance is the survivor coming close enough to
be the one who knows, and then choosing what to do with knowing.

### 2.2 How trust and affection grow

Maeca's respect is earned in the Beast Problem. Her affection is earned in
the Blind. Her trust is earned by the survivor telling her things she would
rather not hear.

| What | Axis | Where |
|---|---|---|
| Reading the tracks (`tracks`) | respect +20, trust +10 | existing |
| The truth about the slurry (`truth`) | respect +20, trust +15 | existing |
| The cure (`thanks`) | affection +10 | existing |
| Kneeling to Greymuzzle with no wolf blood | respect +10 **(new: reaction line `cb_knelt`)** | new |
| Going to the Blind and keeping watch only (`watch_only`) | trust +10, affection +5 | **new** |
| A night at the Blind (`blind`) | affection +15, trust +10 | existing (first night); later nights affection +5 |
| Answering her question about you truthfully (`asked_you` → `told_true`) | trust +10 | **new** |
| Telling her yourself who signed for the boots (Act 2) | trust +25 | **new** |
| Hiding it, and her finding out (Act 2) | trust −40, affection −20 | **new** |
| Wearing wolf pelts | respect −10 on meeting (existing `first` variant); the Blind is shut to you until they're gone | **new gate** |
| Burning the Roost | respect −15 (`cb_burned_roost`; **new number**) | existing line |
| Killing Greymuzzle; slaughtering the Pack; breaking the promise | the route closes for good (`gone`, `cold`, `cb_broke_promise`) | existing |

### 2.3 The beats

| # | Beat | When | Node(s) | Gate | Sets |
|---|---|---|---|---|---|
| 1 | **Meeting** | Act 1 | `first` (existing) | | |
| 2 | **Friction: the bounty** | If the survivor hunts | `first` pelts variant; `cold` | | |
| 3 | **A confidence: barefoot** | | `barefoot`, `signed` (existing) | | |
| 4 | **The test: Greymuzzle** | The Beast Problem | (Greymuzzle scenes; new `cb_knelt`) | `promise.pack` | |
| 5 | **The invitation** | Night, respect ≥ 30, affection ≥ 10, Pack cured or allied | `invite` (existing), extended | | `invited` |
| 6 | **The first night** | | `blind` (existing, extended lead-in), `blind_morning` (existing) | not `wolf.blood`; not wearing pelts | `maeca.lover`, `told_ashford` |
| 7 | **Watch only** | Any Blind night | `watch_only` | | |
| 8 | **The second night: her feet** | `maeca.blind_nights >= 1` | `blind2` | | `say:feet` |
| 9 | **The third night: her question** | `maeca.blind_nights >= 2` | `blind3` → `told_true` / `told_little` | | `maeca.heard_past`, `maeca.heard_heart` |
| 10 | **Sella** | If both | `say_sella` | `maeca.lover`, `sella.free` | |
| 11 | **The boots** (Act 2 beat 4) | When the letter surfaces | `boots_*` | | `maeca.boots` |
| 12 | **Greymuzzle's death** | Act 2's end, if he lives (bible §9) | `grey_dies`, `blind_grief` | `maeca.lover` | |
| 13 | **What you are** | Act 2 beat 11 | `what` | | |
| 14 | **The eve** | Act 2 beat 12 | `eve` | `romance.eve` = `maeca` | |
| 15 | **The end** | Epilogue | | | `maeca.fate` |

### 2.4 How the player bends it

**The tone of the love scene.**
- **The first night at the Blind** is wordless and wary, careful hands that
  become sure ones (the bible's slot `maeca.blind`). If the cure happened
  within the last two days (`stream.clear` set recently, `thanks` seen
  today), it is also **joyful**, the only time she laughs in bed: the Pack
  is loud in the Hollow and she can hear them eating.
- **Later nights** are quieter and surer. The second has her feet in it
  (beat 8): she lets the survivor see the soles, hard as boot leather and
  scarred. If the survivor holds them to warm them, she lets them. That is
  the whole scene, and it is the most intimate thing she does.
- **If the survivor knows about the boots and has not told her** (Act 2,
  `maeca.boots_hid`), every Blind night is **guarded**. She feels it. "You're
  somewhere else. ...Come back, or go."
- **Greymuzzle's death** gives the **grieving** night (`blind_grief`). She
  does not cry. She asks the survivor to stay awake with her and listen to
  the Pack sing for him. It may or may not become a love scene; she
  decides, and the scene gives her the choice, not the survivor.
- **The eve** is desperate and practical: she checks the survivor's
  crossbow, then their boots, then them.

**Refusals, on both sides.**
- Maeca refuses a survivor with wolf blood on them (`wolf.blood`): "Not with
  that on you. Wash. The river's that way." The survivor can come back after
  dawn has washed it (the existing rule).
- She refuses a survivor in wolf pelts: the invitation simply doesn't come.
- The survivor can say "Not tonight" (existing) or choose `watch_only` at
  the Blind: sit up, keep the fire, sleep back to back. She respects it more
  than the night, and says so in five words.
- Inside the lead-in she stops it once, on the first night, to say one
  thing: "If you're going to talk after, don't." The survivor can say "I
  won't" or "Then not tonight." Both are kept.

**Heartbreak and betrayal: Maeca and Greymuzzle.**
- **The survivor kills Greymuzzle:** the route ends at once and for good
  (`gone`, existing: "You went to his house. In the dark. After I told you
  what he was to me."). The bible: "*Costs:* everything, if Greymuzzle
  dies." No apology works. There is no node for one.
- **Greymuzzle dies of age** at Act 2's end (bible §9): the grief beat.
  If the survivor sat with him (`promise.pack` kept), she brings them to the
  place he lay down. If the Pack is `allied`, they follow the survivor now.
  She has to watch that: "They've chosen. ...They chose right."
- **The Pack slaughtered:** the route never opens (`cold`).

**Heartbreak and betrayal: who signed for the boots.**
This is the arc. In Act 2 the survivor can come to know that Holloway signed
for the boots: from Pell's sister's letter, from Holloway's own confession,
or from Redcowl. The bible (§7.4) gives Maeca three ends: she kills Holloway
at the gate; she leaves with the Pack; she makes him hold the gate beside
her. The romance decides which:

| How she learns | Her trust in the survivor | Greymuzzle | She |
|---|---|---|---|
| From the survivor, the day they learned it (`maeca.boots` = `you`) | ≥ 50 | alive | **makes him hold the gate beside her.** "He held the ledger. He can hold a spear." |
| From the survivor, the day they learned it | ≥ 50 | dead | **makes him hold the gate**, and stands on the other side of it, so she doesn't have to look at him |
| From the survivor, the day they learned it | < 50 | any | **leaves with the Pack**, and asks the survivor to come (lover) or not to follow (not) |
| From the survivor, days after they learned it (`maeca.boots_hid` then told) | any | any | **leaves with the Pack.** The romance ends with the line "You lay in my blind and you knew." |
| From Holloway | any | alive | **leaves with the Pack** |
| From Holloway or Redcowl | any | dead, or the Pack gone | **kills Holloway at the gate.** If the survivor is her lover and there, they can stand between. She does not go through them. She walks away, and does not come back to the Blind. |

The survivor who tells her straight away, and is trusted, turns a killing
into a held gate. That is the romance carrying the intrigue.

### 2.5 What it costs, act by act

- **Act 1:** her trust is shut to anyone who hunted the Pack for gold.
- **Act 2:** the boots: the survivor carries the worst news of her life, and
  the arc is whether they bring it to her or let it find her.
- **Act 3:** if both live, the bible makes her the survivor's lover at the
  end. If the survivor goes dark at dawn (ending B without the coin), her
  epilogue is the Blind with one person in it, and the Pack lying down round
  it anyway.

### 2.6 Ends

| End | Romance variant |
|---|---|
| **Leaves with the Pack into the deep wood** | If lover and trusted: she asks the survivor to come. They may. Epilogue: two people at a fire the size of a hat. |
| **Takes the Watch after Holloway** | If lover: barefoot on the wall, and the survivor's boots under her bed, because she won't wear them and won't give them back. |
| **Dies at the breakthrough's edge** | If the Pack is gone and she has nothing left to hold. A lover can be "something left to hold": with `maeca.lover` and trust ≥ 60, this end is closed **(new rule, flagged)**. |
| **The survivor's lover, at the end, if both live** | The bible's end, and the arc's |

---

## 3. Dame Keegan Orme

### 3.1 Who she is, in love

Twenty-six, a lecturer in rhetoric at Saint Wend's before she took the oath,
probationary knight of a Vigil that has stopped answering her letters. The
last true knight of it, and she doesn't know that. Earnest, comic, sincere.
She speaks with no contractions while on duty, and they slip when she forgets
herself.

**Chapter four of her handbook is about the survivor.** "Of the Unchained, and
Their Return to the Dark." She has seen the signs (`keegan.saw_risen`), and
she is very much hoping she is wrong. **The romance is the tragedy the bible
names:** to love the survivor she has to break her oath, and if she keeps it
she has to kill them.

**What she wants:** to be confirmed: to kneel, and have a knight she respects
touch her shoulder with a sword and say "Dame Keegan" without the bracket
(`t_keegan`). And a bath.

**What she fears:** being right about you.

**The voice is the arc.** With the survivor, and only with them, her
contractions slip more and more, until in bed she has none of her rules left.
On the morning after, she puts them back on with her armour, a word at a
time, and the player can hear her do it.

### 3.2 How trust and affection grow

| What | Axis | Where |
|---|---|---|
| The Ford-Warden's lamps (`warden`) | respect +15, trust +10 | existing |
| Ashe (`ashe`) | respect +10 | existing |
| Dinner (`dinner`) | affection +10 | existing |
| Supper on the wall (`supper`, Act 1, new) | affection +10, trust +5 | **new** |
| Bringing her the Vigil's absence plainly ("They're not answering because they don't want to.") | trust +10, affection −5 | **new, in `supper`** |
| Being kind about the handbook | affection +5 | **new, in `supper`** |
| Act 2: telling her the truth when she asks "Did you die on the Low Ford road?" | trust +30 | **new**, the route's gate |
| Lying to her then | trust −30, and the route closes when she finds out (Silverstair's ledger) | **new** |
| Saying nothing (`silence`) | trust −5; she reads silence as yes, which it is | **new** |

### 3.3 The beats

| # | Beat | When | Node(s) | Gate | Sets |
|---|---|---|---|---|---|
| 1 | **Meeting** | Act 1 | `first` (existing) | | |
| 2 | **The tease** | Act 1 | `dinner` (existing) | respect ≥ 10 | |
| 3 | **Supper on the wall** | Act 1, night, after `dinner` | `supper` (new) | respect ≥ 30, affection ≥ 15, `once:dinner` | `keegan.supper` |
| 4 | **The sign** | Act 1, after a death | `say_risen` (existing) | `risen_once` | `keegan.saw_risen` |
| 5 | **The question** | Act 2 beat 2 | `ask` → `ask_truth` / `ask_lie` / `ask_silence` | | `keegan.asked` |
| 6 | **Chapter four, read aloud** | Act 2, if `truth` and trust ≥ 40 | `ch4_read` | | `keegan.ch4_read` |
| 7 | **The road north** | Act 2, if she steps aside (`keegan.route` = `north`) | `north_camp` | | |
| 8 | **The night on the north road** | Act 2, affection ≥ 40, trust ≥ 50, `keegan.ch4_read` | `night` (a new explicit slot, §3.4) | | `keegan.lover` |
| 9 | **Silverstair: the oath** | Act 2 beat 10 | `oath` | `keegan.lover` | `keegan.oath` |
| 10 | **The eve** | Act 2 beat 12 | `eve` | `romance.eve` = `keegan` | |
| 11 | **The stair** | Act 3 | `stair` (outlined) | | |
| 12 | **The end** | Epilogue | | | `keegan.fate` |

### 3.4 How the player bends it

**The tone of the love scene.** Keegan's one love scene (`keegan.night`, a
fourth explicit slot, **new**) is earnest and nervous, then not. She cites
chapter eleven, paragraph six, in the lead-in, and then stops citing
anything. Its mood is set by the question:

- `keegan.asked` = `truth` and chapter four read together: **tender**, and
  tragic in its last line: she is holding something the handbook tells her
  to put down.
- If the night is the eve (`romance.eve` = `keegan`), it is **desperate**:
  she is going to stand at a gate tomorrow against the order she swore to,
  and she hasn't slept in two days.

There is no **guarded** version. Keegan doesn't go to bed with someone she
suspects of lying to her. If the survivor lied (`ask_lie`), the route is
closed until she learns otherwise, and when she does, it is closed for good.

**Refusals, with dignity on both sides.**
- `dinner` is her first refusal, and the comic one ("The answer is very
  nearly no.").
- In `supper` the survivor may take her hand, or not. If they do, she lets
  it be held for a count of three and then says, "I am on duty," and takes
  it back, and doesn't let go of it for another count of three.
- In the north road night, she stops it once, armour half off, to ask a
  real question: "If I am wrong about everything, I would like to be wrong
  about this on purpose. Are you sure?" The survivor can say no, and she
  says, with great relief and some disappointment, "Oh, thank God," and they
  sleep with her armour between them like a third person.
- The survivor can refuse her altogether. Act 2's companion route still
  works without the romance.

**Heartbreak and betrayal: chapter four.**
In Act 2 beat 2 she asks it straight: "Did you die on the Low Ford road?"

| Answer | Respect/trust | She |
|---|---|---|
| **The truth** ("I think so.") with trust ≥ 40 | trust +30 | Steps aside and comes north (the companion route). Reads chapter four aloud with the survivor that night (`ch4_read`), then folds the page down rather than tearing it out: "It is a library book." |
| **The truth** with trust < 40 | trust +30 | Lets them pass and writes to the chapterhouse (the bible's third outcome), then follows them north a day behind, "to supervise". The romance can still open, slowly, on the road. |
| **A lie** | trust −30 | Lets them pass, and finds the truth at Silverstair in Ysolde's hand in Sallow's ledger. She stands at the gate to return the survivor to the dark: the night duel. If the survivor spares her, she is disgraced, and her last line to them is "Do not call me Keegan. Call me Dame Orme. I should like to have been somebody's Dame once." |
| **Silence** | trust −5 | Reads it as yes. Behaves as for the truth, one notch colder. |

**How the romance carries the intrigue.** Her letters go unanswered because
she is a loose end. A lover of the survivor is the loosest end the Vigil
has, and at Silverstair Sallow says so: he offers her confirmation, the
sword on her shoulder and "Dame Keegan" without the bracket, if she hands
over the survivor (`oath`). It is everything she wants, from the one man
she should not take it from. A lover who told her the truth can watch her
refuse it. She asks the survivor to do it instead, with whatever blade they
carry, there on the chapterhouse floor (`keegan.oath` = `broke`). It is the
only confirmation she ever gets, and it is from an Unchained, which is
against chapter four, and she doesn't care.

### 3.5 What it costs

- **Act 2:** her order, her confirmation, and her letters.
- **Act 3:** in ending A, if the survivor lies down in the chain, she stands
  at the top of the stair with a lamp for the rest of her life ("the Vigil
  as it was meant to be"). In ending B, the survivor goes dark at dawn unless
  they hold the coin, and she has read chapter four enough times to know the
  hour. In ending C, the bible says "Keegan kneels or dies trying." As the
  survivor's lover she kneels, and it is the worst moment of her life,
  because she kneels to a lord and not to a lover, and the survivor can tell
  her to get up. If they do, she gets up and leaves the valley, and writes a
  new chapter four.

### 3.6 Ends (as lover)

Re-founds the Vigil, with the survivor's name in its first chapter; stands
at the gate and dies there (the eve was hers, so the scene before it is the
last); kneels; leaves.

---

## 4. Rav Cutwell

### 4.1 Who he is, in love

In his fifties, Glaswegian, a doctor who was a Kerchief and is a doctor who
drinks. Wry, frank about bodies, never sentimental, never says no to a drink.
Never names his brother (he spends that once, `rav.cb_killed_redcowl`).

His secret: Redcowl is his brother, Dunstan. He gave him the night the Coyle
wagons would come, and he took the clerk's key himself. "Ashamed of all of
it, and will do it again."

**What he wants:** not to want anything. Another drink. His brother not to
be dead, or not to be the reason someone else is.

**What he fears:** being sober with someone.

**Rav's route is the bible's**: wry, drunk, grieving his brother; if he takes
the hat, the route goes with him to the Roost.

### 4.2 Two routes, by Redcowl

**A. Redcowl lives.** Act 2 beat 7: the Kerchiefs come to the Waystation as
the army, and Redcowl tells the survivor about the little bird, laughing. If
the survivor guessed it in Act 1 (`redcowl.birds`) and kept it from the
Watch, Rav learns that in the same scene, from his brother. That is the
route's turn: someone held his secret and didn't sell it, in a valley where
everything is sold.

**B. Redcowl is dead, by the survivor's hand.** (`history` `killed_redcowl`.)
"Come back tomorrow. I'll be a doctor again tomorrow." If the survivor comes
back the next day (`rav.came_back`, **new**), he's a doctor again, and the
route can open slowly. If he takes the hat, it goes with him to the Roost:
he leads the Kerchiefs, and his regard for the survivor decides whether the
army fights beside them. The romance with the brother's killer is the
hardest one in the game, and it is meant to be. Its love scene, if it comes,
is **grieving**.

### 4.3 How trust and affection grow

| What | Axis | Where |
|---|---|---|
| Getting into the Roost on his word (`roost`) | trust +10 | existing |
| "Doctor, I've a pain." (`pain`) | affection +5 | existing |
| Going round the back after closing (`back_room`, Act 1, new) | affection +5, trust +5 | **new** |
| Tricking Redcowl into running (`cb_tricked_redcowl`) | affection +5 | existing |
| Keeping the little bird from the Watch (Act 2, `redcowl.birds` and never told Holloway) | trust +25 | **new** |
| Telling Holloway (Act 2, `rav.bird_told`, **new**) | the route closes, and Rav can hang for it | **new** |
| Coming back the day after his brother died (`came_back`) | trust +15 | **new** |
| Letting him take your pulse and not lying about it | trust +10 | **new**, in `back_room2` |

### 4.4 The beats

| # | Beat | When | Node(s) | Gate | Sets |
|---|---|---|---|---|---|
| 1 | **Meeting** | Act 1 | `first` | | |
| 2 | **The flirt** | Act 1, night | `pain` (existing) | trust ≥ 20 | |
| 3 | **The back room** | Act 1, night, after `pain` | `back_room` (new) | `once:pain` | `rav.back_room` |
| 4 | **"Dunstan"** | Act 1, if Redcowl dies | `cb_killed_redcowl` (existing), `came_back` (new) | | `rav.came_back` |
| 5 | **The little bird** | Act 2 beat 7 | `bird` → `bird_kept` / `bird_told` | | `rav.bird` |
| 6 | **The pulse** | Act 2, night, affection ≥ 30, trust ≥ 40 | `back_room2` | | `rav.felt_pulse` |
| 7 | **The night** | | `night` (a fifth explicit slot, **new**) | | `rav.lover` |
| 8 | **Sober** | The morning after | `sober` (the one "no" to a drink: **spends Rav's second exception; author's call, §8**) | | |
| 9 | **The hat** | Act 2, if Redcowl dead | `hat` | | `rav.hat` |
| 10 | **The eve** | Act 2 beat 12 | `eve` | `romance.eve` = `rav` | |
| 11 | **The end** | | | | `rav.fate` |

### 4.5 How the player bends it

**Tone.** Funny, until the pulse. In the back room he talks the whole way
through, doctor's patter ("Breathe in. Out. Don't flatter yourself, that's
medical."). Then he takes the survivor's wrist in the dark, and for a count
of eleven there is nothing there, and then there is. He stops talking. The
cut-away is the first thing in the game Rav does in silence. If Redcowl died
by the survivor's hand, the night is **grieving**: he says, before it, "I
know what you did. I'm not asking you to be sorry. I'm asking you not to
talk about him." The survivor can agree, or decline the night. Declining
is not an insult. He says "Aye. Fair." and pours two.

**Refusals.**
- Rav refuses a survivor who told Holloway about the little bird. He doesn't
  make a scene of it. He buys them a drink and moves to a different stool.
- He refuses if he's drunk past the fifth cup: "Not like this, pal. I'd like
  to remember it. ...Christ, did I say that out loud." This is a scene beat,
  not a stat check (night, `rav.drunk`, from the tavern's evening clock, or
  simply a variant on the first try at `back_room2`).
- The survivor can stop at the pulse. If they pull their wrist away he lets
  it go and says nothing about it, and does not bring it up until Act 2's
  turn.

**Betrayal: the little bird.** The tip-off can hang him (bible §5: "hanged
for the tip-off"). If Harlan, exposed, wants someone hanged for Jory's cage,
and the Watch learns who gave the date, the survivor can speak for Rav,
take it on themselves ("I sold the date"), or say nothing. A lover who takes
it on themselves is the only way he hears what someone is willing to pay
for him. He is furious. It is the closest the route comes to sentiment, and
he hides it in the fury.

**Intrigue.** Rav carries the Kerchiefs. If he takes the hat, the doctor
leads the army, and the romance decides whether it fights beside the
survivor at the north gate: the bible's "his regard for the survivor (`rav`
affection after `cb_killed_redcowl`)". The proposal makes that `rav.lover`
or affection ≥ 40.

### 4.6 Ends

Stays the town's doctor (and, if lover, keeps a second glass on the bar that
nobody else may use); takes the red hat (the survivor's place at the Roost
fire, if they want it); hanged for the tip-off (if lover, the survivor's last
scene with him is the night before, in the cells, and it is not a love
scene; he spends it making them laugh).

---

## 5. Ysolde Marrow, the Wayfinder

### 5.1 Who she is, in love

In her fifties, from Edinburgh, a cartographer of the places the road
forgets. Brisk, bookish, gallows humour. She talks of the dead as entries in
a margin. She writes down who comes back from her maps and sells the list to
Sallow, to keep her brother Edric fed in his silver cage. Edric came out of a
barrow in the Morrow hills twelve years ago, risen with his mind. She has
drawn that barrow eleven times and still cannot get the corners right.

**The route is closed while she is selling the survivor.** The bible: "never
while she is selling you". It opens only after Silverstair, after Edric
(beat 10), after a confession.

**What she wants:** Edric out. Then, to her surprise, something for herself.

**What she fears:** that she has sold so many names she has none of her own
left.

### 5.2 How trust and affection grow

| What | Axis | Where |
|---|---|---|
| The margin: how she writes you down (`margin`) | affection +5 if `given`; the route remembers which | existing node, new number |
| Asking whether she goes in herself (`t_wayfinder`) | trust +5 | existing node, new number |
| Act 2: confronting her with the ledger, and the words you choose (`confess`) | see below | **new** |
| Freeing the cages, Edric among them (`edric.freed`) | affection +30 | **new** (Act 2 fact) |
| Walking her and Edric to the valley's edge | trust +20 | **new** |

### 5.3 The beats

| # | Beat | When | Node(s) | Gate | Sets |
|---|---|---|---|---|---|
| 1 | **Meeting, the margin** | Act 1 | `first`, `margin` (existing) | | `wayfinder.name` |
| 2 | **The barrow** | Act 1 | `t_wayfinder` (existing) | | |
| 3 | **Silverstair: the entry** | Act 2 beat 10 | (the bible's ledger) | | |
| 4 | **The confession** | Act 2, back from Silverstair | `confess` → `confess_forgive` / `confess_cold` / `confess_use` | | `wayfinder.confessed`, `wayfinder.forgiven` |
| 5 | **The cages** | Act 2 beat 10 | | | `edric.freed` |
| 6 | **The twelfth drawing** | After Edric is freed | `twelfth` | `edric.freed`, `wayfinder.forgiven` | |
| 7 | **The night** | | `night` (a sixth explicit slot, **new**) | affection ≥ 40, trust ≥ 30 | `wayfinder.lover` |
| 8 | **The margin, rewritten** | The morning after | `morning` | | |
| 9 | **The eve** | | `eve` | `romance.eve` = `wayfinder` | |
| 10 | **The leaving** | Act 3 or the ending | `leaving` | | `wayfinder.fate` |

### 5.4 How the player bends it

**The confession.** Back from Silverstair, the survivor has seen their own
entry in her hand. They choose how to put it to her:
- **"You sold me."** She does not deny it. She tells them about Edric, in
  margin language. Then: forgive her (`confess_forgive`, trust +20), go cold
  (`confess_cold`, route closed until Edric is freed, then it can open once,
  slowly), or use it ("Then you owe me the way in.", `confess_use`, respect
  +15, affection −10; the route stays open but it is now **guarded**).
- **Say nothing, and see if she does.** If the survivor freed the cages, she
  confesses unasked within a day, and that counts as forgiveness earned on
  both sides (trust +25).

**The name.** How she wrote the survivor down in Act 1 is how she says their
name in bed:
- `given`: their name. She has written it so many times that saying it
  aloud surprises her.
- `nobody`: "Nobody." She laughs at herself, then stops: "No. That won't do
  now."
- `false`: "Lark." It sticks. The survivor can tell her their real name,
  once, the morning after, or let her keep Lark.

**Tone.** **Joyful** if Edric is free and she has been forgiven: two people
who had stopped expecting this, wry about it, and then not wry. **Grieving**
if freeing the cages cost someone (the bible's war comes at once). She takes
the survivor to bed the night after the dead are buried, because she can't
stand to draw anything.

**Refusals.**
- She refuses while she is still selling: "Not while you're in my ledger.
  I've some rules. Not many. That's one."
- The survivor can refuse her; she writes "declined" in a margin and shows
  them, which is her joke, and then crosses it out, which is not.

**Intrigue.** Her notes are how Sallow found the survivor, and her
confession is how the survivor learns how much he knows. `wayfinder.name` =
`false` means Sallow has spent a month looking for a Lark. As her lover the
survivor can ask her to keep selling him Larks: a double game. She does it
until Sallow's man comes to the table, and then the arc needs the survivor
at Silverstair before she does (`wayfinder.double`, **new**; the bible's
"dies at Silverstair" end comes from here).

### 5.5 Ends

Frees Edric with the survivor and leaves the valley (as lover: she asks the
survivor to come and draw the places nobody has forgotten yet); dies at
Silverstair (the double game, found out); keeps selling (only if the
survivor went cold and the cages stayed shut; no romance).

---

## 6. When the arcs meet

- **Sella and anyone.** Sella's working nights are work. Nobody else's arc
  treats them as betrayal. Maeca: "She's honest about what she charges.
  That's more than most." (`maeca.say_sella`). Keegan has read a chapter on
  it, and is very red. Rav knew before you did ("you can hear the bed from
  the cellar"). The **free** night is different: it is the one thing in
  Sella's arc that isn't paid for, and a lover will ask about it once,
  straight, in Act 2. The survivor can answer honestly ("Yes, both.") and
  each person takes it in their own way (scene files). Lying about it is the
  only way it costs anything.
- **Sella on others.** `say_maeca` (existing). `say_keegan` (new): "The
  knight? Love. She's going to read you a chapter after." `say_rav` (new):
  "Rav's been up my stairs twice in seven years, and both times to lance
  something. Treat him kindly. He's softer than he drinks."
- **The eve** (`romance.eve`) is the one night that is exclusive. Whoever
  the survivor doesn't choose notices, and each gets one line the morning
  of the battle (scene files). None of them is cruel.
- **The epilogue** honours every route that reached its night, and names one
  as the survivor's, which is whoever they spent the eve with if that person
  lived; otherwise whichever living lover's trust is highest.

---

## 7. The fact ledger (new)

Existing facts the romances read are in `STORY_BIBLE.md` §10 and §12. The
facts below are new. "Writer" is the node that sets the fact; "Readers" are
the nodes or beats that read it.

### Act 1 (could ship with the Act 1 data now)

| Fact / flag | Values | Writer | Readers |
|---|---|---|---|
| `sella.told_knowing` | `true` | `sella.past` (when `once:buyers` is set) | `sella.free_night` tone; `sella.fortune` |
| `sella.felt_cold` | `true` | `sella.morning` (variant after `risen_once`) | `sella.what`; Act 2 beat 10 (`silver`) |
| `sella.past_sold` | `true` | `sella.past` (if `sella.free` is not yet set) | `vonnra.f_past` (**change**: read this instead of `sella.heard_past`, so the free night protects what follows) |
| `sella.free_declined` | `true` | `sella.free_decline` | `sella.free_ask` |
| `sella.nights` | number (existing) | `night`, `rest_night` | existing |
| npc flag `sella` `say:door` | | `sella.door` | |
| `maeca.blind_nights` | number | `maeca.blind`, every visit | `blind2`, `blind3` |
| `maeca.heard_past` | `true` | `maeca.told_true` | Act 2 |
| `maeca.heard_heart` | `true` | `maeca.blind3` | Act 2 beat 11 (`maeca.what`) |
| npc flag `maeca` `say:feet` | | `maeca.blind2` | |
| npc flag `maeca` `say:sella` | | `maeca.say_sella` | |
| `keegan.supper` | `true` | `keegan.supper` | Act 2 beat 2 (her question comes in private) |
| `rav.back_room` | `true` | `rav.back_room` | Act 2 `back_room2` |
| `rav.came_back` | `true` | `rav.came_back` | Act 2 route B |
| `night.spent` | `true`, cleared at dawn | every love scene | every invitation (**System**, optional) |

### Act 2 and 3 (for the Act 2 writer)

| Fact | Values | Writer | Readers |
|---|---|---|---|
| `sella.confronted` | `forgave`, `hired`, `ended` | `sella.fortune` | every Act 2 Sella scene |
| `sella.asked_what` | `told`, `lied` | `sella.what` | `silver` |
| `sella.sold_sallow` | `true` | `sella.silver` (if not off the clock) | Holloway's letter ambush (beat 3) variant at the Last Lamp |
| `sella.lied` | `true` | `sella.lie_*` | beats 8, 9 |
| `sella.fate` | `south`, `risen`, `kept`, `gone` | `sella.cart_*`, the ending | epilogue; Act 3 second Unchained |
| `kiln.lit` | `true` | Act 2 beat 8 (Brannoc sells the irons) | `sella.cart` |
| `maeca.boots` | `you`, `holloway`, `redcowl`, `pell` | Act 2 beat 4 | Maeca's end |
| `maeca.boots_hid` | `true` | when the survivor learns and leaves without telling her (a day's tick) | Blind nights' tone; her end |
| `maeca.fate` | per the bible | | epilogue |
| `keegan.asked` | `truth`, `lie`, `silence` | Act 2 beat 2 | the route |
| `keegan.ch4_read` | `true` | `keegan.ch4_read` | `keegan.night` |
| `keegan.lover` | `true` | `keegan.night` | |
| `keegan.oath` | `broke`, `kept` | `keegan.oath` (Silverstair) | the endings |
| `rav.bird` | `kept`, `told` | Act 2 beat 7 | the route; the hanging |
| `rav.felt_pulse` | `true` | `rav.back_room2` | beat 11 |
| `rav.lover` | `true` | `rav.night` | the army; epilogue |
| `wayfinder.confessed`, `wayfinder.forgiven` | `true`; `forgave`, `cold`, `use` | `wayfinder.confess` | the route |
| `edric.freed` | `true` | Act 2 beat 10 | the route |
| `wayfinder.double` | `true` | `wayfinder.morning` | Silverstair |
| `wayfinder.lover` | `true` | `wayfinder.night` | |
| `romance.eve` | an npc id, `alone`, `wall` | the eve (**System**) | the war; the epilogue |

### New explicit slots

The bible names three. The romances add three, each written the same way:
a cut-away, and a slot behind `settings.intimacy == "full"` that StoryLint's
`Every_explicit_slot_waits_behind_the_setting_with_a_cut_away_beside_it`
already checks.

| Slot | Node | Who, where, tone |
|---|---|---|
| 4 | `keegan.night` | Keegan and the survivor, a roadside chapel on the north road, the armour coming off a buckle at a time; earnest, nervous, then not; the contractions slipping |
| 5 | `rav.night` | Rav and the survivor, the back room of the Crooked Flagon after closing; funny until his fingers find the survivor's wrist; then the first silence in his life |
| 6 | `wayfinder.night` | Ysolde and the survivor, her rooms over the map table, every surface paper; wry, then glad; she draws them after |

(The Act 2 eves are variants of each person's slot, not new slots. They are
written as tone variants inside the same node.)

---

## 8. Notes and calls for the main author

1. **Voice exceptions.** Rav's "never says no to a drink" has no written
   exception yet. The proposal spends it on the morning after his night
   (`rav.sober`): "No. ...No, I'll keep this one." If you'd rather keep that
   exception for something else (his brother's grave; the hat), the morning
   still works with him pouring it and not drinking it.
2. **Maeca's Ashford rule.** Every new Maeca line keeps "Ashford" to three
   words or fewer. The boots scenes talk about the cave mouth and the feet,
   never the town.
3. **`vonnra.f_past`.** The proposal changes its reader from
   `sella.heard_past` to `sella.past_sold`, so a past told after the free
   night is not quoted. That is a one-word change in `dialogue.json` and a
   new effect in `sella.past`. Without it, the free morning's warning has
   nothing behind it.
4. **The free night's new trust gate** (trust ≥ 15). It is reachable with
   three paid nights plus any one of: the Rook question, a rest night, or the
   past told knowingly. Without a gate, Sella's bolt can be bought, which is
   the one thing it must not be.
5. **Sella's refusal after the Roost** reads `cb:burned_roost` set "today".
   The world has no "today" marker per flag. Either set a fact with a
   one-day `later` that clears it (the `later` change exists), or drop the
   "today" and let her refuse once, the first night after she hears.
6. **Keegan's slot is in Act 2**, on the north road, because the bible makes
   her an Act 2 route. Act 1 only gets `supper`.
7. **Ysolde's route and the bible's "never while she is selling you."** The
   double game (§5.4) has her keep selling *false* names with the survivor's
   consent. That honours the rule's spirit (she is no longer selling *you*).
   Your call.
