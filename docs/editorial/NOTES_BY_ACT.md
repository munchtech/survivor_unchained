# Developmental notes, act by act

The detailed companion to `EDITORIAL_LETTER.md`. The letter says what
matters most and in what order; this file goes through the story act by
act and thread by thread: arcs, twists (is each one planted, fair,
surprising, inevitable?), pacing, stakes, choices and their
consequences, villains' motives, and what to cut, deepen or set up.

Everything here is diagnosis first. Where I offer a fix it is one option
among several, and the author's intention outranks it. Craft references
point at `CRAFT_STUDY.md` by section (§). Line-level fixes are in
`LINE_NOTES.md`; larger new material is in `IDEAS.md` (I-numbers) and
`THE_EMBER_REVEAL.md`.

Sources read: `docs/STORY_BIBLE.md`, `VOICES.md`, `WRITING_PASS.md`,
`HANDOFF.md`, `BETA_DESIGN.md`, `RC_PLAN.md`, `docs/concepts/`, all of
`godot/data/content/` (dialogue, quests, npcs, folk, concerns, items,
rules, archetypes), the zone scripts in `godot/logic/Play/Zones/`, the
arena code (`godot/logic/Arena/Arena.cs`, `src/Ui/ArenaResult.cs`),
death and the nemesis (`godot/logic/Play/Journey.cs`) and
`godot/logic/World/Chapter.cs`.

---

## Part 0. The whole: what the story is underneath

### 0.1 The controlling idea the story already has (and does not yet know it has)

A developmental editor's first job is to say what a book is about, in
one sentence, so the author can confirm it or correct it (Story Grid's
"controlling idea"; Perkins' Gatsby letter begins by saying what the
book *is*; §13). Here is mine, built from what is actually in the text
rather than from the bible's three questions:

> **Everyone in this valley is keeping the lights on with a debt to the dead that they cannot pay.**

Look at the cast through that sentence and nearly every major person is
defined by a dead person they owe:

| Person | The dead they owe | How they "keep the lights on" |
|---|---|---|
| Holloway | Ashford's barefoot garrison (he signed for the boots) | Counts the gate; keeps eleven men alive; holds a letter that would pay them |
| Maeca | the same garrison; she is what is left of it | Hunts, refuses wolves, drinks |
| Brannoc | Nell | Forged the irons; works iron dawn to dark |
| Harlan | his sister, dead in the fever year | Sells the Dig the ember that killed her, to keep the Company alive |
| Pell | his sister, who kept Ashford's books | Counts. "Somebody ought to know what things cost." |
| Redcowl and Rav | Ashford, their mother | Feeds forty-one mouths; drinks; never says the name |
| Rook | her mother, Ashe, Mister Rook | Lights the hearth from a dead captain's lamp; keeps the chair |
| Wenna | the fever year's dead, never named | Makes things "that stop you dying" |
| Chid | the whole Order of the Morning Light | Keeps a dead shrine lit for two hundred years |
| Vonnra | her line, her grandmother (the unspent coin) | Lights the ford lamps; drowns the carters |
| Keegan | the Vigil that will not answer her letters | Guards a gate for an order that has abandoned her |
| Ysolde | Edric | Sells the names of the living to feed the dead |
| The lamplings | their own dead, carried out burned | Count them, to forty, and start again |
| **The survivor** | **themselves, and the first night's drowned (Nell)** | **Burns ember** |

This is a remarkable unity, and it was not imposed: it grew out of
writing each person truthfully. It is the reason the town feels like a
town and not a quest hub. It also tells the author what the three
endings are *about*. The bible frames them around the Morrow. This table
says they are about the same choice every NPC has already made in small:
keep paying (A, re-forge), stop paying and let the debt go (B, break),
or take the debt into yourself (C, take the light). And it shows that
the motif the game uses most (counting: Holloway's gate, Pell's ledger,
Rook's beds, Harlan's days, Vonnra's "payment, always", the lamplings'
forty) is the theme in miniature.

**Recommendation:** adopt this, or something like it, as the controlling
idea in the bible, above the three questions. It answers "what will you
do with it?" (the third question) with something the player has watched
a dozen people do. `THE_EMBER_REVEAL.md` is this idea made literal.

### 0.2 The three questions

The bible's spine is three questions, one per act: *What are you?* (Act
2), *Who made you, and why?* (Act 3), *What will you do with it?* (the
ending). It is a clean spine. Three notes on it:

1. **All three are about the survivor's identity, and the survivor has no
   want.** The questions are asked *of* the survivor by the plot. The
   survivor never asks anything for themselves (`VOICES.md`: "short,
   plain, a little dry; never make a speech"). That is right for their
   voice and wrong for their role. A protagonist without a want is a
   camera (Stein's triage question: is the protagonist strong enough?;
   §2, §13). See `EDITORIAL_LETTER.md` problem 2 and §0.4 below.
2. **The first question is the genre's most guessable.** A player who
   respawns at a shrine every time they die, in a game called *Survivor
   Unchained*, about the risen dead, will guess "I am one of the risen"
   within hours (*Planescape*, *Dark Souls*, *Dead Cells* and *The Sixth
   Sense* have all trained them). The game's own text nearly says it in
   Act 1 (`risen_once`: "You have died and come back"; Vonnra's "You
   have already died on this road"; folk: "Chid says you died. You look
   well on it"). That is not a flaw if the design embraces it: let the
   *player* know before the *survivor* does, and make Act 2's drama
   Keegan's duty and the cost (Hitchcock's bomb under the table: fifteen
   minutes of suspense instead of fifteen seconds of surprise; §3). It
   is a flaw if Act 2 stages "what you are" as a revelation and expects
   a gasp. Stage it as a confrontation instead (see Act 2, beat 11).
3. **The second question is the best one** (Vonnra made you, by drowning
   a dozen carters), and it is answered by Act 1 for an attentive
   player. That is by design (the accusation), and it means Act 3 must
   carry a *further* turn on Vonnra or it arrives already spent (see
   Act 3, "Vonnra's truth").

### 0.3 The timeline, and the questions players will ask

A story built on implied history needs a private timeline the author
never breaks (Tolkien's and Martin's iceberg is a *consistent* iceberg;
§6). Reconstructed from the text, with problems marked:

| When | What | Source | Problem |
|---|---|---|---|
| ~2,000 years ago | The Seventh Legion finds the Morrow, chains it with seven links, each anchored in a heart; the Legion's dead hold the inner door | bible §1, §8 | |
| unknown | The binders' line keeps the sigil-keys and the square coin | bible §4 | Who kept the hearts between the Legion and the Order? (The binders, presumably. Say so.) |
| unknown, > 200 years ago | The Order of the Morning Light makes the Wardens, one per heart, and burns ember in its chapel lamps | bible §4; `chid.warden` "Before me, certainly" | The Wardens are "made by the Order", but the hearts are the Legion's. Were the hearts unguarded for 1,800 years? Or were the Wardens the Legion's, and the Order only *kept* them? Decide. |
| ~200 years ago | Chid rises, Unchained, "of the Order's day" | bible §5 | |
| ~60 to 80 years ago | The Vigil comes for the Order for sheltering Unchained; the Order "leaves"; Rook's mother carries the lamp up from the chapel | bible §4; `rook.lamp` | Rook is 60. Her mother carried the lamp "the year the Order left", and folk say "Chid's not aged a day since my mam was a girl". Consistent if the Order left about 70 years ago. |
| ~60 to 80 years ago | Ashe, "captain of the first Watch", closes the north road "with forty lamps and walked back through it with one"; the Vigil buries him | `rook.firstlamp`, `keegan.ashe` | Rook: "never heard him called owt else" implies she knew Ashe in life. Then the Watch is under a century old. Keegan says the Vigil kept the lamps "before the Watch was the Watch". Fine, if so. |
| ~12 years ago | Edric comes out of a barrow in the Morrow hills, risen with his mind; the Vigil takes him | bible §5 | |
| 10 years ago | The Ashford Fall; the boots signed for in full; the garrison dies barefoot | bible §1, §5 | |
| 9 years ago | The fever year | bible §1 | |
| Holloway's first winter as captain | The Watch runs out of oil for the ford lamps | `holloway.post2` | |
| Last winter | Twelve irons forged; ten collected; the ford lamps relit; the Warden wakes; carters drowned | bible §1 | See `LINE_NOTES.md` note 1: what the lamps *do* contradicts itself. |
| A fortnight before the survivor | Nell and Wat drown | `brannoc.nell` | |
| Day 0, dusk | The survivor drowns at the ford, "was carried back to the south bank", wakes by a dying fire | bible §1 | **By whom?** Nobody in the text says. |

Four questions every attentive player will ask, which the bible should
answer (privately, at least) before Act 2 is written:

1. **What do the lamps do?** Lit lamps "keep the Warden asleep" (Keegan),
   "feed the Warden" (the prologue) and were relit "to wake" it
   (bible). This is the logical keystone of the Act 1 mystery and it
   does not hold. The fix (oil keeps it asleep; ember wakes it) is in
   `LINE_NOTES.md` note 1, and it is the most important single
   correction in this pass.
2. **Why didn't Vonnra use Chid?** Vonnra needs an Unchained "to walk
   down through the Legion's dead and bind them in as the new link". An
   Unchained has lived in her town for two hundred years, tending a
   shrine across the square. Either she does not know (then why does
   Rook's gossip, the folk line "not aged a day", not tell her, who
   buys every rumour in the valley?), or she knows and he refused, or
   he is unfit. The bible needs an answer, and the best answer is one
   that turns the night arenas into story: **an Unchained who never
   burns goes dim, and the chain needs a bright one.** Chid has not
   taken ember in two hundred years; he could not light a candle with
   what is left in him. The survivor burns brighter every night they
   fight. Vonnra is not just waiting for the survivor; she is *fattening
   the link*, and she buys the Wayfinder's maps (see `IDEAS.md` I-2).
3. **Who carried the survivor back to the fire?** The bible says the
   survivor "was carried back to the south bank". There is a beautiful
   accidental answer already in the text: Rook's first line, "Chid came
   in babbling about blue lights going out at the crossing". Chid was
   at the ford that night. Chid pulled the survivor out, built the fire,
   sat with the body, saw it begin to wake, and left before they opened
   their eyes, because he knows what it is to wake as one of them and
   wanted the survivor to have one ordinary morning first. That gives
   Act 3's "Chid's truth" a scene the player has already lived through
   from the other side (`IDEAS.md` I-9).
4. **Why does a devout survivor exist if the Order left seventy years
   ago?** The devout background says "The Order of the Morning Light
   raised you to tend lamps in chapels no one visits anymore." So the
   Order survives somewhere. Chid, "a priest of a dead order", should
   react to that (he would be overjoyed, or frightened: the Vigil came
   for the Order). And a **hunter** grew up "following tracks through
   Thornhollow", so a hunter survivor is local, and nobody in the
   Waystation recognises them. Both backgrounds promise a personal tie
   the game never pays. See §0.4.

### 0.4 The survivor: give them a want

The survivor's personal story in Act 1 is one line at dawn ("You try to
call up your mother's face, and find it is not quite where you left
it") and Sella's sleep-talk. That line is the best seed in the game, and
it is not yet a spine.

What the survivor needs is not dialogue (their voice is right) but a
**want the player can feel through play**. The cheapest one, already
half built: **the survivor wants their memory back**, and the game takes
it from them a little every night. Concretely:

- Each background carries **one person**, named in creation, whom the
  survivor was going to or coming from when they took the ford at dusk:
  the hunter's mother at a farm in the Verge; the scholar's
  correspondent; the outcast's debt; the devout's last abbot. (One line
  each in `archetypes.json`; the player can rename them.) This is the
  person whose face goes first.
- In Act 1 the survivor can ask after them (Rook, the Wayfinder's
  margins). In Act 2, the memory mechanic takes them piece by piece. In
  Act 3, if `THE_EMBER_REVEAL.md` is taken, the survivor hears them in
  the Morrow.

This one person converts the third question ("What will you do with
it?") from an abstract choice about a god into a question about whether
to let someone go. It is the move *Planescape* makes with Deionarra and
*The Witcher 3* makes with Ciri (§10): the cosmic ending is decided by a
single relationship.

### 0.5 The day and the night: what the play says

This is `EDITORIAL_LETTER.md` problem 1, and the most important
structural note in the review. In brief, for reference below:

- The four Act 1 story arenas are **the violent routes** (hunt the Pack,
  raid the Roost, hold the Dig, open the vault). A player who cures the
  wolves, bargains for the cages and moves the pump plays no story arena
  in Act 1 at all, only the ember scars, which have no story.
- Each arena is thirty minutes long and contains **no story text**: no
  boss line, no voice, no change from the scar arenas but the boss's
  name. Redcowl, a talker, dies silent as an "enforcer". Greymuzzle, the
  noblest creature in the game, is a thirty-minute boss with a health
  bar.
- The result screen says "The story goes on."

So the night is where the player spends most of their hours and where
the story is absent. That is the dissonance to fix (Hocking's term;
§8). The fixes run from cheap (boss lines; per-arena dawn text; the
outcome screen) to structural (a story arena for every route, not only
the violent one). See `IDEAS.md` I-1 to I-8.

---

## Part 1. The Prologue: The Low Ford

### What it is

One night, a tutorial that never stops to be one (the header comment in
`Prologue.cs` says so, and it is true): wake, rise, the road, the ambush,
the post, the barrow, the ford, the Warden, the heart stolen, dawn. It
teaches every system as an event. That is a hard thing to do and it is
done.

### What works

- **Nell.** The ambush at the wagon, and the line after it, is the
  best-built moment in Act 1 (`LINE_NOTES.md` §2.3). The player kills a
  twelve-year-old as one of a horde and is told who she was only after.
  Days later Brannoc asks. That is a three-stage recognition, and the
  player's own hands are in it, which no novel can do.
- **The watchman's belt-book.** Three lines in a worsening hand open the
  Act 1 mystery and give a dead man a personality.
- **The dawn.** The ember going out "and everything it gave you goes
  with it" is the game's central mechanic explained as loss. "You try
  to call up your mother's face" makes it personal.
- **Grimtunnel taking the heart.** The victory immediately turns into
  the first break in the chain. Winning causes the problem: a
  consequence-first structure (Excalibur's Mordred, §12; the Red
  Wedding's "we did this").

### What doesn't, yet

1. **No sensory trace of the drowning.** The survivor drowned at dusk and
   wakes by a fire. Nothing on screen says wet, cold or water. The whole
   Act 2 reveal rests on this night, and its first scene has no plant.
   One line fixes it (`LINE_NOTES.md` §2.1).
2. **The Warden does not recognise them.** It drowned them hours earlier.
   One word ("AGAIN?") is the fairest clue available (`LINE_NOTES.md`
   §2.4).
3. **Grimtunnel is a magpie, not a believer.** The bible's Act 3 turns on
   his faith. Plant it (`LINE_NOTES.md` §2.5).
4. **The logic of the lamps** (`LINE_NOTES.md` note 1). The boss fight
   teaches "lit lamps make it strong". Keegan says "lit lamps keep it
   asleep". The player's hands and the mystery's clue disagree.
5. **"Dying here is forgiven ... the only place in the game where that is
   true."** The design comment is right about the mechanics and wrong
   about the fiction: the survivor is Unchained, so in the fiction dying
   is forgiven everywhere, always. That is the whole secret. "The ember
   will not let you go so easily" is a perfect line *because* it will
   go on being true. Keep the line; let it come back once, at the first
   day death, from Chid's mouth (`IDEAS.md` I-10).

### Pacing

The prologue is the right length for a tutorial and slightly long for a
first impression. The first ten minutes need one strong *story* image
before the systems pile up. The ambush and Nell are that image; they
come at stage four. Consider moving one image forward: the dead
watchman's corpse visible from the start, at the edge of the firelight,
before the player knows what they are looking at.

---

## Part 2. Act 1: The Waystation

### 2.1 Shape and pacing

Two troubles (wolves, caravan), three mysteries (door, below, lamps),
one finale (the fortune), days 1 to about 7. Clocks run: the caravan's
prisoners starve after four days; the wolves escalate by day (a farm
raided on day 5, Aldo dead on day 7). This is good design. Clocks make
the day loop a set of real choices about time, which is what *Pentiment*
does with its days (§10): you cannot see everything, so what you looked
at is your character.

The **found-early principle** in `WRITING_PASS.md` §3 (a thing found
before its quest starts its story instead of ending it, and the person
it belongs to reacts to a survivor who arrives knowing) is exactly
right and rarely done this thoroughly. It is Larian's "weird Dungeon
Master" principle (§10) applied at the scale of a small town.

What the act lacks is a **night climax**. Every big beat is a night
arena, says the brief, and the act ends with a conversation (the
fortune). See 2.8.

### 2.2 The Beast Problem

**What works.** Five theories, five witnesses (Holloway "bolder", Maeca
"running", Harlan "attacking caravans", Wenna "never like this", Tam
"something's killing them"), and each is partly true. That is the
iceberg principle applied to a quest's opening (§6): the truth is
assembled, not told. Six approaches, including doing nothing, and doing
nothing has a body count (Aldo). Greymuzzle is written entirely through
the narrator watching what he does, and the restraint makes him the most
dignified character in the game.

**Notes.**

- **The villain is a pump.** The cause is the Dig's slurry and the
  culprit, Grimtunnel, is off-stage. That is fine for a mystery and thin
  for a night: the only story arena is "Hunt the Pack", the route where
  the player kills the victims. Give the cure route its own night, the
  night the slurry stops: the Dig boils over, and the Pack (if allied)
  or Maeca (if her respect is high) holds the stream with the survivor
  (`IDEAS.md` I-3). That makes the merciful route the one with the best
  arena, which is the right message for this game.
- **Greymuzzle's promise.** Kneeling to him and then killing his wolves
  is the act's sharpest moral trap, and the game remembers it in four
  places (Maeca, the fortune, Greymuzzle's back turned, Holloway). This
  is the "remember the unforgivable" principle (§9, Majewski's critique
  of refillable meters). Keep it exactly.
- **Holloway's arc** inside Act 1 (bounty, then "I was wrong about
  them", then "I'll not pay men to put down sick dogs") is small and
  complete. It sets up his Act 2 choice without spending it.
- **Pell sells the cure.** The "exploited" route (Pell moves the pipe for
  forty) is a lovely piece of moral comedy, and Wenna's "I'll charge you
  double, and I'll enjoy it" is its whole consequence. Consider one
  Act 2 echo: Pell owns the hole in the ground; Pell's numbers are
  *more* exact on this route.

### 2.3 The Missing Caravan

**What works.** This is the best-plotted thread in the game. A merchant's
grief that is real and a guilt that is real; a villain (Pell) who is
doing the wrong thing for the right reason; a bandit (Redcowl) who feeds
his prisoners before his own people; a clerk (Jessop) who is the hinge
of three plots; a boy (Jory) who does not know; six crates whose fate
decides how wide the ground opens in Act 2. Every person in it believes
they are right, and every one of them is partly right (§2: villains
who believe they are right).

**Notes.**

- **The six crates are the act's real moral choice, and the player cannot
  see that.** Who gets the B.E. (Redcowl keeps it; Harlan sells it on;
  it burns) decides the width of the Act 2 breakthrough, whether a farm
  goes into the ground "at once, Ashford again", and whether the Kerchiefs
  bring powder to the war. In Act 1 it feels like a side choice. Delayed
  consequence is a strength (the Bloody Baron's Whispering Hillock; §10),
  but a delayed consequence needs a *felt weight* at the moment of
  choosing, or the later cost reads as arbitrary. One line does it: at
  `redcowl.crates_dig`, Redcowl looks at the hill and says what the
  player has not yet put together ("Six crates of that, in that hill. You
  know what it did to Ashford? No. You don't. Nobody does. I do."). The
  player then chooses knowing it matters, without knowing how.
- **The found-early web is very large.** `WRITING_PASS.md` lists sixteen
  test scenarios for the caravan alone. That is admirable engineering
  and a warning for Acts 2 and 3: this level of reactivity per thread
  is not sustainable across twelve Act 2 beats (see Part 3, "scope").
- **Jessop** is planted from five directions (Rook, Rav, Sella, Jory,
  Vonnra, the bootprints), each from a different angle (money, a round
  bought, pillow talk, the violet, the ledger, the toll-token). That is
  the model for a fair hidden fact: many partial testimonies, none
  conclusive (Wolfe, Erikson; §3, §6). The Act 3 payoff (Jessop on the
  stair, risen and held, saying "the road is shut") is one of the best
  images in the bible.
- **Pell's ledger margin**, "tell Holloway where they camp, after", is a
  perfect clue: it convicts him of the robbery and also proves he
  wanted the crates in the Watch's hands, not the Dig's. The player who
  thinks about it understands Pell before Pell explains himself.
- **Redcowl's death in the raid is silent.** He is the second-best talker
  in the game and he dies as a boss called "enforcer" with a name plate.
  He should have last words, and they should depend on what the
  survivor has said to him: "Ashford" said, the crates kept, the little
  bird guessed (`IDEAS.md` I-4).

### 2.4 The Lamps at the Low Ford

**What works.** A mystery quest with no outcome, only entries, that the
journal assembles and the player solves ("never stated; assembled",
`STORY_BIBLE.md` §6). The accusation at the fortune, gated on having
enough pieces, is the act's real climax for a thinking player. Vonnra's
response, saying their name instead of yes or no, is one of the best
character moments in the game. And Sella's pillow talk quoted back at
the fortune, "(She is not looking at your palm.)", is the first twist
that pays inside Act 1, and it is fair, surprising and inevitable at
once: the player *told* Sella; the player *knows* Vonnra buys Sella's
talk; the player still feels the floor go.

**Notes.**

- **The logic** (Part 0.3, question 1): fix first.
- **How guessable is Vonnra?** Count the arrows pointing at her in Act 1:
  Rook paid double; the carters' notice signed "V."; the square coin at
  her throat matching Brannoc's square coin on the anvil; her clerk;
  her violet; her "Sooner than I had thought"; "the lamps lit for you";
  "not often the second thing happens"; she misses nothing through the
  east gate and yet "never saw" the caravan. That is nine. A careful
  player will have her by day 4. **That is fine, because Act 1 is built
  to be solved**: the accusation is the reward. But it changes Act 3.
  The bible lists Vonnra's secret as coming out in Act 3. For many
  players it will have come out in Act 1, in their own mouth. Act 3
  must therefore carry a turn on Vonnra the player *cannot* have
  assembled. Candidates in Part 4.
- **The accusation's reward is invisible.** Saying it to her face sets
  `vonnra.accused` (respect +25, trust -15) and changes her address.
  The player is not shown that they won something. One sensory change
  that lasts would make it felt: from then on Vonnra's lamp is lit
  whenever the survivor passes the Toll Tower at night, and she is
  watching *them*, not the road.

### 2.5 The Sealed Vault and the Thing Below

**The vault arena spends the door.** In Act 1 a survivor with the
fragment can open the Legion's door after dark, fight a thirty-minute
arena "Behind the Sealed Door", and "the Seventh Legion's dead let you
out again". In Act 3 the descent through that door is the climax. Two
problems and one opportunity:

- If the player has been through the door in Act 1, the Act 3 door is not
  a threshold. Keep the Act 1 arena to **the first landing** and make
  the stair below it *visibly* continue down past where the dead stand
  in the way: "Behind it: a stair going down, older than the door. The
  dead stand on it in rows, all the way down, and they do not move
  aside." That makes Act 1's victory a glimpse, not a visit.
- The arena's boss is "The Barrow Lord, Of the Seventh Legion", a barrow
  knight model. The Legion's dead are the most important dead in the
  story (they hold the inner door; they part for the Morrow's own
  light). Their first appearance should not be a recoloured barrow
  knight. Give the Legion's dead one visual rule (they never attack
  first; they stand; they bar) and one line.
- **The opportunity:** the dead *let the survivor out*. Jessop, alive,
  went in and did not come out (the bootprints). The survivor, dead,
  went in and came out. That is the fairest Act 1 clue to "what you are"
  in the game, and nothing in the text points at it. Vonnra, who knows
  exactly what it means, should be shaken by it (`LINE_NOTES.md` §5,
  Vonnra), and the arena's won line should say it (`LINE_NOTES.md`
  §3.4).

**The Thing Below** is exactly the right size: a pale thing at the
bottom of a pit, a babbling lampling, a map that says DOWN, and a prayer
heard for a held breath. Fix the narrator's "probably"
(`LINE_NOTES.md` §3.1). Tam's knocking under the farm is the best horror
seed in the game; keep it a child's report that nobody believes.

### 2.6 Nell

The emotional summit of Act 1 and the best-written scene in the game
(`LINE_NOTES.md` §5, Brannoc). Its consequences are the strongest delayed
consequences in the bible: the truth buries her and stops the second
crossing; a lie sends Brannoc to the gate to ask strangers, and in Act 2
lights the Kiln Ford, makes a second Unchained, and costs the survivor
the heart's cage in Act 3. That is consequence that is personal, delayed,
and moves across acts, which is the whole craft of the Bloody Baron in
one smith (§10).

Two notes:

- **`WRITING_PASS.md` §14 asks the owner to confirm the tone.** My
  reading: it is right. A child's death, the player's own doing, told to
  her father, written in one plain line and never dwelt on. That is the
  `VOICES.md` rule for violence, and the restraint is what makes it
  bearable and devastating at once (Hobb's method; §5). Do not soften
  it, and do not add to it.
- **The lie should cost the liar.** `nell.told` `lie` makes Brannoc happy
  ("Aunt'll feed her up"), and the cost comes in Act 2. That is good.
  Consider one Act 1 echo so the lie is felt as a weight before it is
  punished: a morning report on the third day after it, "Brannoc has
  started a small thing on the anvil, too fine for a horseshoe. He says
  it is for Low Kiln." (A gift for her.) It costs one rule.

### 2.7 The romances

**Sella** is the best-designed romance in the game because the romance
*is* the intrigue: what the survivor says upstairs reaches Vonnra, and
the fortune proves it. Her free night ("the bolt, which she shoots
herself, which she has never done") pays her one stated want inside Act
1. This is a model of what `STORY_BIBLE.md` §11 calls "romance carries
the intrigue".

**Maeca**'s romance is earned (respect, affection, the Pack settled), and
its morning gives the player her Ashford secret in her own fewest words.
Good.

Two cautions for Act 2:

- **Sella's Act 2 arc punishes her for helping.** If she lies to Vonnra
  for the survivor, she flees south, drowns at the Kiln Ford and rises.
  The sex worker who helps the hero and is destroyed for it is an old
  pattern (the helper "fridged" to motivate the protagonist). The bible
  can keep the event and change its meaning by giving Sella the choice:
  she knows the road is Vonnra's, she takes it anyway, and if she rises
  whole she has, at last, "a door that locks from the inside" (the
  Unchained cannot be bought by anyone). Agency, not punishment.
- **The concept art and the prose are in two registers.** The prose is
  restrained, frosty, grounded (barefoot hunters, wolf pelts, a smith's
  apron). The calling concept sheets (`docs/concepts/survivor_concepts.jpg`)
  are high-glamour fantasy costume: plunging robes, bare midriffs in
  plate. That is a legitimate genre register (Frazetta; Diablo IV's
  marketing), and it is not the register of this writing. A player
  meets the art first. It is worth an explicit decision about which
  register the game is in, because the dissonance will be felt in the
  intimate scenes most of all, where the prose is at its most careful.

### 2.8 The fortune (the act's ending)

**What works.** The fortune is a reckoning scene: Vonnra reads back what
the player did, by thread, in her voice, with judgement ("You went
looking for the cause and not the culprit. Most people never learn the
difference."). It is the game's version of the Fallout ending slides,
delivered by a character with an agenda. The accusation inside it is the
one place the player can act.

**Notes.**

- **It is a recap at a climax.** Nine pages, each a summary. A recap
  is the weakest dramatic form (no value shift; Story Grid's test, §13),
  and the act's other climaxes all happened earlier, off this stage.
  The fortune needs a *turn of its own*. Options, cheapest first:
  1. Vonnra's last page is not a reading but a request: "Before the next
     chapter, I would like you to do one thing for me. I will pay." (She
     sends the survivor to the ford at night, to see a lamp she says is
     out. The survivor finds it lit. Act 2 opens there.)
  2. The fortune is interrupted: the cups rattle (rule 41), the ground
     turns over, and Vonnra stops reading in the middle of a word and
     looks north-east, at the hill. For the first time she does not
     finish.
  3. The act ends at night, not at the table: after the fortune, the
     act's final arena (`IDEAS.md` I-5, "The Night the Ground Turned
     Over") with the people the player helped present in it.
- **Length.** Nine pages of one-to-two sentences is fine on paper and
  long on screen. The two pages that change the player (the past quoted
  back; the accusation) should get the longest pauses. Consider cutting
  `f_pell` into `f_caravan` and `f_ember` into `f_below`.

### 2.9 Act 1's antagonists

Act 1 has no antagonist on stage. Pell is a careful man in a shop;
Redcowl is a host; Grimtunnel went down a hole in the prologue; Vonnra is
a toll-keeper. That is right for a mystery act about circumstance (the
antagonist is the valley's economy; Tufekci's "sociological"
storytelling, §12). It is a problem for the *nights*, where an arena's
boss is the face of the act. The fix is not a new villain but voices
for the bosses the act already has (Greymuzzle as narration, Redcowl's
last words, Grimtunnel roused; `IDEAS.md` I-4), and Grimtunnel heard
*below*, now and then, in the scars: the player should know by Act 1's
end that someone down there is happy.

---

## Part 3. Act 2: The North Road

Not yet built. These notes are on the bible's twelve beats (§7).

### 3.1 The overall shape

**Strengths.** Act 2 is where Act 1's choices land, and the bible has
mapped every fact to its beat (the consequence ledger, §10). That is
rare discipline. The act's turn ("what you are") is surrounded by
sociological pressure: the Watch's arrears, Sallow's money, Keegan's
duty, the Kerchiefs as the only army. That is the right way to stage a
personal revelation: as a thing institutions want to buy (§12, Tufekci).

**The main problem: too much.** Twelve beats; three new major characters
(Sallow, Edric, the second Unchained); a new location (Silverstair); a
war; a breakthrough; two of the game's three strongest Act 1 seeds (the
boots, Nell's irons) paying off; plus romances. Counting the variants
each beat already has in the bible, Act 2 has well over a hundred
outcome combinations before Act 3 multiplies them. *Baldur's Gate 3*'s
writers kept spreadsheets of companion combinations that took "a small
army" (§10); this team is not an army. And the night arenas, where most
of the play is, are not yet assigned to the beats at all.

**Recommendation: cut Act 2 to six beats, each a night**, and fold the
rest into day scenes and morning reports:

| Keep as a night beat | Fold in |
|---|---|
| **1. The breakthrough** (the farm, the width, who holds the edge) | Wenna's mask; Tam's family brought in; the Watch's powder |
| **2. The boots** (Holloway, Maeca, Pell's letter): the night Maeca learns | Holloway's letter (beat 3) becomes the same night's other half: whether he burns it |
| **3. The second crossing** (Brannoc's irons; the Kiln Ford lit or not; the second Unchained) | Sella's lies (beat 9); Jory on the south road |
| **4. Keegan's chapter four** (the duel at the gate, or not) | "What you are" (beat 11) lands here, in Keegan's mouth, not in a ledger |
| **5. Silverstair** (the cages, Sallow, Edric) | the army (beat 7) as the force that gets the survivor there |
| **6. The war at the gate** | Harlan exposed (beat 5) and Pell's numbers (beat 6) as day scenes before it |

Six nights, each with a boss who speaks, each changed by Act 1 facts,
each with day scenes before and after. The ledger survives intact; the
act gets a shape a player can feel.

### 3.2 Beat by beat (on the bible as written)

**1. The breakthrough.** Strong, because its width is the sum of the
player's Act 1 choices (crates, pump) and its cost lands on a family the
player has met (Tam, his Pa). This is Excalibur's "the land and the king
are one" turned into arithmetic (§12): the ground opens as wide as the
survivor let it. **Set up** in Act 1 that the width will be legible:
Pell's numbers should be readable in Act 2 as *the player's* numbers
("six crates; a pump running nine more days").

**2. Keegan's chapter four.** The best beat in the act. A comic
character's comedy turns out to have been the cover for a tragedy
(chapter four is about you; the contraction was the tell). This is the
Planescape move (§10): a companion whose question is the protagonist.
**Deepen:** Keegan's three outcomes are a duel, stepping aside, or
writing to the chapterhouse. The strongest version of her scene is one
where she *wins the argument* and still chooses: she should state the
Vigil's case (the chain must be tight; every Unchained is a link coming
loose; she has read chapter four four times) better than the survivor
can answer it (Thulsa Doom's "flesh" speech, §12: the villain argues the
theme better than the hero). Then the player's choice matters.

**3. Holloway's letter.** Good, and it should merge with the boots (see
3.1): the night Holloway decides what to do with Sallow's money is the
night the boots come out. One night, one man, two debts.

**4. The boots.** The strongest *sociological* thread in the game:
Holloway signed for boots that never came, to cover his commander; the
garrison held the cave mouths barefoot and died; Maeca is the last of it;
Pell's sister wrote that it was funny. Three people hold three pieces;
who holds the letter depends on Pell's fate. **Twist audit:** planted
(Maeca's name, her "Somebody with a good hand and a ledger", Holloway's
"I counted boots for the Ashford garrison, once, and I was good at it",
Pell's sister), fair (all three pieces are in Act 1), surprising (the
player meets Holloway as the town's most honest man), inevitable (his
voice sheet is "a quartermaster who was made a captain"; he goes quiet
at Ashford). It is a model twist. **One caution:** Holloway's line "I
counted boots for the Ashford garrison, once, and I was good at it" is
very nearly a confession in Act 1. It is the right line; it means the
reveal is *dramatic irony* for attentive players, and the Act 2 scene
should be written for a player who already knows and is waiting to see
whether Maeca finds out (Hitchcock's bomb, §3).

**5. Harlan exposed.** Good, and small. Fold into the day.

**6. Pell's numbers.** Pell knows which night the chain gives. That is a
**deadline** for the whole act, and the bible underuses it. Make the
numbers a visible clock (the day count in the journal: "Pell says the
ground goes on the twentieth night") so that Act 2 has the same time
pressure Act 1's caravan clock gave it. *Pentiment*'s days (§10).

**7. The army.** Redcowl's people as the army is the act's best
reversal of an Act 1 assumption (the bandits are the only ones who will
fight). Rav taking the hat if his brother died is right. Fold the army's
arrival into the Silverstair night.

**8. Brannoc's irons and the second crossing.** Superb delayed
consequence (see Act 1, Nell). **Watch:** a hooded buyer "in the Toll
Tower's violet (a new clerk, never Vonnra herself)". Good: Vonnra never
dirties her hands on screen. Keep it.

**9. Sella's lies.** See 2.7: give her agency.

**10. Silverstair.** The cages are a strong image (the Vigil turned from
killing the risen to buying them; a war in the south fought by soldiers
who rise every night). Sallow is the act's antagonist and he is a good
type (the collector; courteous, unhurried, apologises and means none of
it). **The risk:** he is a new face at the act's peak. Act 1 plants him
lightly (silver ink; "a gentleman in the north who likes silver ink";
"Some of them keep ledgers"; the seal on Holloway's letter). Add one
direct encounter before Silverstair: a letter *to the survivor*, in
silver ink, courteous, offering terms (`IDEAS.md` I-12). Villains who
write are frightening in proportion to how polite they are.

**11. What you are.** The bible lands it through "the ledger, Keegan's
chapter four, and Chid". A ledger entry is recognition by a token, the
weakest kind in Aristotle's ranking (a letter, a birthmark; §3). And
three sources at once is a dump (Perkins to Fitzgerald: let it come
"bit by bit"; §13). Recommendations:
- Land it once, in a person: **Keegan**, at the gate, asking "Did you die
  on the Low Ford road?", and the player choosing the answer.
- Let the *player* have known for an act. The game can even say so:
  Keegan, "You knew. You have known for weeks. I can see it in how you
  stand."
- Let the ledger be the *aftermath*: at Silverstair the survivor reads
  their own entry in Ysolde's hand. A confirmation, and a betrayal
  (Ysolde sold them), not a revelation.
- Start the memory-cost mechanic **at the reveal**, so that the moment
  the survivor knows what they are is the moment the ember starts
  costing them who they were. That is the act's turn made into play
  (§8: harmony).

**12. The war at the gate.** The act's climax and the natural biggest
arena in the game so far. Everyone the player helped is there
(Holloway, Keegan, Maeca and the Pack, Redcowl's or Rav's people,
Brannoc). **This is the arena that should carry the most voices**: allies'
barks by name, deaths announced as they happen, the boss a Vigil
champion who speaks (`IDEAS.md` I-6). The "Come down with me" that ends
the act is a perfect last line.

### 3.3 Act 2's antagonist and the shape of opposition across the game

Act 1: circumstance. Act 2: Sallow. Act 3: nobody (the Morrow, a
choice). Grimtunnel recurs as comic menace. The game has no single
opposing will from beginning to end, which is defensible (Erikson and
Cook have none; §2), but the night arenas each need a face, and Act 3
needs a final boss.

The opposing will that *does* run from the first night to the last is
**Vonnra's**. She made the survivor; she arranges every act's
conditions; she wants the survivor to lie down in the chain forever. She
is the game's antagonist in the way Kreia is in *Knights of the Old
Republic II* or Flemeth in *Dragon Age* (§10): an ally with an agenda
the player cannot override. The bible already knows this (she "binds the
survivor" in one ending). Make it structural: **Vonnra is the force the
player is working against, who is also, every act, the person they need.**
That makes her Act 3 truth a confrontation and not a briefing.

---

## Part 4. Act 3: The Morrow

### 4.1 Vonnra's truth

The bible has two modes: in her own words if accused, assembled from the
stair if not. Good. **The problem** (2.4): for many players her truth
was said in Act 1. Act 3 must turn her once more. Options, any of which
the player cannot assemble in Act 1:

1. **She went first.** Before the carters, Vonnra walked into the ford
   herself, at night, with the lamps lit. The Warden would not take her:
   it knows the binders' blood and stood aside. She tried three times.
   That is why she needed others. (It makes her both more monstrous and
   more pitiable, and it gives the ending in which she drowns herself
   at the ford a history: she has stood in that water before.)
2. **She chose Ashford.** Ten years ago the binders' duty was to tighten
   the chain at Ashford, and she did not, because it would have meant
   sending someone down (her clerk? her daughter?). Ashford is her
   failure, and the boots, the fever year, Maeca, Redcowl's forty-one
   mouths are her debt. Everyone in the valley owes the dead; she owes
   all of them.
3. **Jessop was her son.** The clerk she sent through the door "to see if
   a living man could pass" was hers. "Clerks go south, traveller. It is
   the direction they fall in." becomes unbearable on the reread.
4. **She does not know what ember is.** If `THE_EMBER_REVEAL.md` is
   taken, her truth is sincerely wrong, and the player knows more than
   she does at the bottom of the stair.

(1) and (4) are the strongest and are compatible.

### 4.2 The stair and Jessop

Jessop on the stair, risen, held by the Legion's dead, saying "the road
is shut" over and over, with Varrow silver and a toll token in his purse,
is the best single image in Act 3. It pays five Act 1 seeds at once. It
needs nothing.

### 4.3 The heart and Brannoc's cage

The heart burns whoever carries it; an Unchained can carry it at the
price of names; Brannoc's cage lets it be carried, but only if he knows
about Nell and stood with the survivor. This is the best payoff in the
bible: **the smith who forged the irons that drowned his daughter forges
the cage that carries the heart back**, and only if the survivor told him
the truth about her. It is the Mordred principle reversed (§12): the
consequence of the protagonist's earliest choice comes back as grace.
Protect it from scope cuts above everything else in Act 3.

### 4.4 Chid's truth

Planted with care: "not aged a day", "Rook's mother brought me bread",
the "C.", "Nobody's made a C like that in... well. Ages.", "Morning
comes. It always has. I should know.", "It's been a long time since I
saw anyone do that." It is fair and it is guessable, and that is right:
Chid's truth should be dramatic irony (the player suspects for two acts;
the scene is about him *saying* it). **Deepen:** give Chid one scene the
player has already lived through from the other side (the fire at the
ford, Part 0.3, question 3; `IDEAS.md` I-9). And answer why Vonnra did
not use him (Part 0.3, question 2).

### 4.5 The coin

"Buys one thing that cannot be bought twice: one Unchained back up into
the light, alive and unlit." Planted in Act 1 (`vonnra.coin`) with
exactly the right vagueness. Its use in the endings (keep it; give it to
Chid so he ages at last; to Edric; to the second Unchained) is a fine
final choice because it is small and personal inside a cosmic one. Keep.

### 4.6 What the Morrow prays for

"To be let die." Planted from the first act ("Not breathing. Praying.").
This is the bible's best idea: the valley's light is a chained thing's
pain (Le Guin's Omelas; §5). Two notes:

- **It is abstract.** A vast pale thing that suffers is pitiable at a
  distance. Nobody the player has met is in it. `THE_EMBER_REVEAL.md`
  makes it personal: the Morrow is the valley's dead.
- **The player should hear it before deciding.** At the moment the
  Morrow's wish matters, the player needs to *meet* it, not be told
  about it. The Green Knight lets Gawain see the whole cost of the wrong
  choice before he makes the right one (§12). The Morrow's prayer,
  heard clearly at the bottom of the stair, is that vision.

### 4.7 The endings

| Ending | Theme reading | Strength | Risk |
|---|---|---|---|
| A. Re-forge | Keep paying the debt | Variants carry people the player loves (Chid; Vonnra drowning herself to take the survivor's place) | Reads as the "safe" ending; the cost (every other Unchained dark at dawn, Sallow's army included) is told, not felt |
| B. Break | Let the debt go | Mercy, with the world's light as its price; "a world without its light, and without its cage" | The survivor dies unless they keep the coin, which makes the coin the obvious choice and the ending's sacrifice optional |
| C. Take the light | Take the debt into yourself | A new god; Keegan kneels or dies trying; Grimtunnel worships | Its gate (refused Vonnra, lied to or escaped the Vigil, holds the heart) reads as an achievement checklist, not a character's arc |

Notes:

1. **All three are defensible.** That is the hardest thing to achieve in
   an ending set, and the bible has done it. None is the "good" one.
   This is the *Pentiment* standard (§10): no right answer.
2. **They echo *Dark Souls*.** Link the fire, let it fade, take it for
   yourself. Players will see it. The difference this game can claim is
   that its fire *speaks*, and its fuel has names. Lean into that
   (`THE_EMBER_REVEAL.md` §9) and the echo becomes a conversation with
   the genre instead of a debt to it.
3. **Make the choice a scene, not a menu.** The Season 8 lesson (§12): a
   destination foreshadowed is not the same as a choice dramatised. The
   player must make the choice *under pressure, with the alternative
   visible*: Vonnra on one side, Chid on the other, the Morrow's voices
   below, the heart in their hands burning their names.
4. **Ending C's gate should be a want, not a checklist.** The survivor who
   takes the light should be the one who has, all game, *taken*: kept
   the strongbox, sold the cure, burned the most ember, refused every
   offer. Track a single fact ("what the survivor took") across the game
   and let C be the end of that road.
5. **The post-game.** The arenas offer "endless play after the win". The
   endings should decide whether the arenas still exist (`THE_EMBER_REVEAL.md`
   §10.4). After B there is no ember. That is the most powerful
   ludonarrative choice available to the game.

### 4.8 The final night

The bible does not say what the last arena is. Every big beat is a night
arena; the ending must be too. Options:

- **The descent.** The stair as a thirty-minute arena that goes *down*
  (Diablo I's structure, §4.6: each level a step deeper; the geography is
  the plot), with the Legion's dead parting or barring by what the
  survivor is carrying.
- **The boss is the choice.** Who stands in front of the heart depends on
  the player's path: Vonnra (if refused), Keegan (if she came north to
  return them to the dark), Grimtunnel transformed by the heart, or the
  survivor's own light (the *Planescape* move: the final antagonist is a
  severed part of the hero; §10).

---

## Part 5. Characters: arcs at a glance

| Person | Arc as written | Note |
|---|---|---|
| Survivor | None in Act 1; the three questions after | Needs a want (Part 0.4) |
| Vonnra | Arranger → seen → (end) | The game's real antagonist-ally; needs an Act 3 turn the player cannot assemble (4.1) |
| Chid | Fool → the oldest, gentlest person in the valley | Answer the Chid problem; give him the fire at the ford |
| Keegan | Comic → tragic | Best arc in the cast; let her win the argument |
| Holloway | Honest captain → the man who signed for the boots | Merge letter and boots into one night |
| Maeca | Hunter → the last of Ashford | Fix her Act 1 Ashford slip (`LINE_NOTES.md` §5) |
| Brannoc | Smith → the father who forged the irons → (the cage) | Protect the cage payoff |
| Harlan | Grieving uncle → the seller | Small and complete; fold Act 2 into day |
| Jory | Boy in a cage → knows | His "Mister Coyle" in the shop is the whole arc in two words |
| Pell | Villain → careful man → (the numbers) | Use his numbers as Act 2's clock |
| Redcowl | Bandit → Ashford's levy → (the army) | Give him last words if he dies |
| Rav | Doctor → brother → (the hat) | Keep "Dunstan" as the only time |
| Rook | Innkeeper → paid by Vonnra → turns | Her turn in Act 2 should cost her the money she needs |
| Wenna | Herbalist → the fever year again | Her Act 2 is the act's emotional centre if the breakthrough is wide |
| Tam | Boy nobody believes → right | Never let him be wrong |
| Sella | Professional → informant → (the road) | Give her agency in Act 2 (2.7) |
| Ysolde | Cartographer → seller of names → (Edric) | Her deal should be visible from the survivor's side once in Act 1 |
| Sallow | (Act 2) | Plant with a letter to the survivor |
| Grimtunnel | Thief → believer | Plant the faith in the prologue |
| Snib | Exactly what he looks like | Never let him know anything. He survives everything. |

---

## Part 6. Motifs and recurring images

The game already has a strong motif system. Name it, so that new writing
keeps to it:

- **Lamps.** The Last Lamp, the shrine lamp, the ford lamps, the
  lamplings' head-lamps, Kell's lamp coming back up alone, Ashe's lamp,
  the Pilgrim's lantern, "Keep the lights lit." Rule: every lamp is a
  promise or a debt.
- **Counting.** Holloway's gate and eleven men; Pell's ledger; Rook's
  beds; Harlan's days; the lampling counting to forty; Vonnra's
  "payment, always"; the Wayfinder's margins; Sallow's ledger. Rule:
  people count what they owe.
- **Boots and feet.** Maeca barefoot; Nell's new boots; Jessop's
  bootprints going in; "Pity about the boots." Rule: boots are who got
  sent, and who didn't come back.
- **Hands.** Vonnra reads the hand (and is not looking at it); Brannoc's
  hammer; the bones' hand holding the sigil; "hands through the bars".
  Rule: hands are what people do; faces are who they are (and the ember
  takes faces).
- **Names.** "It always takes the names first." Rav will not say his
  brother's; Redcowl will not say Ashford; Vonnra says the survivor's
  only when seen; the Wayfinder writes them down and sells them. Rule:
  a name said is a debt acknowledged.
- **Colours.** Red is Ashford's (and the Kerchiefs'); violet is the Toll
  Tower's (and Vonnra's ink); silver is the Vigil's (Sallow's ink, the
  cages); cold blue is ember at the ford. Rule: nothing else in the
  valley may be violet or silver. Keep a colour sheet.

---

## Part 7. What to cut, deepen and set up

**Cut**

- Act 2 to six night beats (3.1).
- `risen_once`'s description, which says the Act 2 answer
  (`LINE_NOTES.md` §4.4).
- "Doctor McBreathless" (`LINE_NOTES.md` §5).
- The narrator's "probably" (`LINE_NOTES.md` §3.1).
- One of the two "hums against your teeth" (`LINE_NOTES.md` §3.3).

**Deepen**

- The night arenas: voices, outcomes, a story arena per route (`IDEAS.md`
  I-1 to I-8).
- Keegan's case for the Vigil (3.2).
- Vonnra's Act 3 turn (4.1).
- Chid's answer and his night at the ford (Part 0.3).
- The Morrow, made personal (`THE_EMBER_REVEAL.md`).

**Set up (in Act 1, now, while it is cheap)**

- The drowning, in the first line of the game.
- What the lamps do (oil and ember).
- Grimtunnel's faith.
- The survivor's one named person (Part 0.4).
- The weight of the crates (2.3).
- The Legion's dead as a visual rule, at the vault (2.5).
- Sallow, by a letter (3.2).
- The idiom "gone to the Morrow" (`THE_EMBER_REVEAL.md` §5).
