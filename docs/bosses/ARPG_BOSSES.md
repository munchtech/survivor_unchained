# Day bosses: three for the story

By day there is no ember. The survivor fights with what they carry: a few
slotted skills at their learned rank, their art, the dash, their gear and
their character level (`HANDOFF.md`, `godot/logic/Rpg/SkillBook.cs`). There
is no horde to hide a boss in and no build to melt it, so a day boss is the
other kind of fight: one place, one opponent, a few helpers, and patterns
to read. The ARPG research (`RESEARCH.md` §4) says what works from a high
camera: the ground tells you everything, the arena is half the fight,
phases change the space as well as the moves, and the boss is a person with
a voice.

The day already has one boss of this kind, the Ford-Warden of the prologue
(`AUDIT.md` §3). These three are placed where the story has a fight it
does not yet stage, and each finishes with a choice the story already
records.

| | Boss | Act | Where | Decides |
|---|---|---|---|---|
| 1 | The Slurry Engine (and Snib) | 1 | The Dig's pump, the Verge | `dig.pump`: `broken` or `blown` |
| 2 | Dame Keegan Orme, at first light | 2 | The north gate | Keegan killed, or spared and disgraced (`STORY_BIBLE.md` §7.2) |
| 3 | The Keeper of the Silver Cages | 2 | Silverstair's cage hall | The cages freed, left or bargained over (§7.10) |

## Units

Day creatures use the same `EnemyDef` numbers as the arena, at the zone's
level (`Verge.Level()`), with no boss multiplier: a day boss is a big
`Health` on its own. As a yardstick, the Barrow Knight elite has 420 at
level 1 and the Ford-Warden 2,600 (with its ward taking most blows while the
lamps burn). Fight length targets: **2–3 minutes** at the zone's expected
level with the gear the act usually has, and no phase shorter than 25 s.
A day DPS probe does not exist yet; `IMPLEMENTATION.md` §6 suggests one, and
every health figure below is a starting point to be measured by it.

## 1. The Slurry Engine

*Act 1, the Verge, by day. Replaces "clear the crew, press Break" at the
Dig's pump (`Verge.cs:596-614`) when the survivor breaks it by force.*

**What it is.** The Dig's pump: a wheel-driven engine the lamplings built
out of a mill, three valves and a boiler of cooked ember, spewing slurry
down the outflow into the stream the wolves drink from. Snib stands on the
gantry and shouts. Grimtunnel is not here; he is down the hole with the
heart, and Snib would very much like him not to find out about any of this.

**The question.** *Can you take a machine apart while its crew puts it back
together?* A fight against a place, with breakable parts and adds that have
a job.

**The arena.** The pump-house yard, about 24 m across: the engine in the
north, the outflow channel running south through the middle (slurry:
violet, slows and poisons), two plank bridges over it, the gantry along the
east wall with Snib on it, crates and spoil heaps as cover.

**The engine.** `slurry_engine`, Stationary: Health 3,600 (the boiler),
Radius 3, armoured (× 0.25 taken) while any valve holds. Three valves
(`engine_valve`, 450 each, breakable parts on its face). The bar shows the
boiler and three valve pips.

**Phase 1, the Valves (three valves to none).**
- **The sweep**: the outflow nozzle swings across the yard on a slow arc
  (a cone telegraph 70°, 1.4 s), spraying slurry that leaves violet ground
  for 6 s. It sweeps toward wherever the survivor was 1 s ago.
- **The crew**: four lamplings at a time, and they do not attack first:
  they go to a broken valve and mend it (a channel of 6 s shown over the
  valve; interrupt it by hitting the mender). A mended valve comes back at
  half its health. Adds with a purpose, so killing them is a choice of
  priority, not a chore.
- **Snib's spanners**: Snib lobs a spanner every 5 s (a small circle, 0.9 s).
  He shouts in his own voice ("The VALVES! Not the— Snib will fix it. Snib
  will NOT fix it.").

**Phase 2, the Pressure (no valves left).**
- The boiler is bare and the engine **builds pressure**: a channel bar on
  the boss bar ("Pressure"), 30 s to full. Every 10 s it vents: a ring
  telegraph from the engine outward (radius 10, 1.5 s), scalding.
- **How it ends is the survivor's choice:**
  - **Break it**: bring the boiler to nothing before the pressure fills.
    The pump stops, the crew runs, and `dig.pump` is set to `broken`.
  - **Let it blow**: at full pressure the engine bursts (a circle of 12 m,
    a 3 s telegraph with Snib screaming "DOWN! Everyone DOWN!"). The
    survivor must be behind cover (a spoil heap, the gantry's foot) or out
    of the circle. The engine and the mouth of the Dig go together, and
    `dig.pump` is set to `blown`, with everything the story already does
    with that (Act 2's breakthrough moves to the sinkhole, `STORY_BIBLE.md`
    §7.1). The survivor who brought a blasting-ember charge can set it on
    the boiler in this phase to make the same choice sooner.

Both outcomes exist in the story already; the fight lets the player choose
between them with their feet, and makes the more drastic one the riskier
one to stand near.

**Snib.** Never fought. When the engine goes, he is on the gantry and then
he is not, and he turns up in Act 2 as he always does ("Snib survives
everything", `STORY_BIBLE.md` §3).

**Drops.** The Pump-Wheel Buckler (Named, `docs/items/ACQUISITION.md` §4),
ember shards, slurry; the journal's entry for the stream.

**Day tools.** Arts that interrupt (Shield Bash, Grapple Chain) stop a
mender; Bull Rush pushes a lampling into the slurry; area skills keep the
crew off the valves. Nothing here needs a strong build; it needs priorities.

## 2. Dame Keegan Orme, at first light

*Act 2, beat 2 ("Keegan's chapter four"): the branch where she stands at the
gate to return the survivor to the dark.*

**Who she is.** The last true knight of the Argent Vigil, probationary,
earnest, comic, and right about the survivor. Her handbook's chapter four is
"Of the Unchained, and Their Return to the Dark". She has asked the survivor
straight whether they died on the Low Ford road, and the answer (or the lie)
has brought her here.

**When.** The bible calls it a night duel. This design moves it to **first
light**, and makes that her choice: chapter four says an Unchained is
ordinary at dawn, and Keegan will not fight anyone at an advantage she did
not earn, nor give them one. "The handbook is very clear. One does not
return a thing to the dark while it is burning. One waits for the morning,
and then one asks it to step outside." It keeps the duel what it is (two
people, no horde, no ember) and keeps it in the day's rules. If the owner
prefers night, the same fight runs as a small no-horde arena with the
survivor's ember; see `README.md`, decision 6.

**The question.** *Can you read a person?* Her tells are her words.

**The arena.** The yard inside the north gate, 20 m by 14 m: the gate shut
behind her, two braziers going out as the light comes, a well, a cart. The
sun comes up over the east wall during the fight: the shadows shorten as
she weakens (the arena as her health bar, Hush's lesson in `RESEARCH.md`).

**Body.** `keegan_duel`: Health 2,400, Speed 4.0, Damage 24, Radius 0.55, a
sword and an argent heater shield (`Guard`, arc 120°, 0.85 against
projectiles from the front while she is not attacking). Human-sized.

**Phase 1, By the Book (100%–50%).** She names every move before she makes
it, in full, without contractions, and the name is the telegraph (shown as
a line of text over her as well as spoken, and the ground marked as usual):
- "Chapter four, the first figure: the Approach." She closes behind her
  shield at a walk; projectiles glance; she cannot be staggered from the
  front. Go round her.
- "The second figure: the Admonition." A shield bash, a 60° cone, 0.9 s,
  × 1.2 and a 1 s stun. Perfect-dodgeable.
- "The third figure: the Sentence." A two-handed overhead down a line 6 m
  long, 1.3 s, × 2. She is open for 1.5 s after it misses.
- "The fourth figure: the Censer." She throws silver ash in a circle
  (radius 3, 1.2 s) that is meant to burn an Unchained. The first time, at
  dawn, it does nothing at all, and she stops for two seconds and looks at
  it ("That is not— the handbook does not say what to do about that."). A
  free opening, and a sad joke. She does not throw it again.

**Phase 2, Off the Book (50%–15%).** She forgets herself, and the
contractions come (`VOICES.md`: "they slip out when she forgets herself,
which is the joke, and later the tell"). She stops announcing. The same
four moves, faster (wind-ups × 0.8, never under 0.7 s), chained in pairs,
with only the body to read: shield up before the Approach, the sword going
back before the Sentence. Her lines are no longer citations: "You could
have *lied* better. Why didn't you lie better?" "Don't you dare make this
easy." The phase teaches the player that they had learned the moves, not
the words.

**Phase 3, the Return (15%).** She goes down on one knee, shield across her.
The fight stops. Two prompts:
- **Finish it**: she does not resist. Keegan dead at the gate.
- **Spare her**: she stands, and takes off the Vigil's tabard. Disgraced
  (and in her own eyes, freed). The bible's branch.
A survivor who lowers their weapon (stops attacking for 4 s) during Phase 2
skips to this choice early, and she says so: "You stopped. Chapter four has
nothing on that either."

**Why it works.** It is the game's one fight against someone who is right
about you. The mechanics carry her character: the textbook becomes the
telegraph, losing her composure removes it, and the dawn makes her weapon
useless against a person who is, by day, only a person.

**Drops.** None, either way. If spared, she gives the survivor her handbook
later (Chapter Four, Named), and its lore line changes with the ending.

**Day tools.** Shield Bash interrupts the Sentence; Smoke Bomb breaks her
Approach (she stops to listen); Mark Prey works as on anyone; arts with
knockback do not move her while her shield is up.

## 3. The Keeper of the Silver Cages

*Act 2, beat 10, Silverstair: the chapterhouse's cage hall, by day.*

**Who he is.** Sir Aldous Fane, Lord-Exchequer Sallow's keeper of the
silver cages: a Vigil knight who stopped killing Unchained when Sallow
started paying for them, and keeps a ledger as Sallow does. Courteous; he
calls the caged "the stock". By day, the risen in the cages are only people,
grey and frightened; at dusk they burn, and that is when he sells them.

**The question.** *Will you fight around the people you came for?* A fight
in a hall full of hostages, with walls that move.

**The arena.** A long hall, 36 m by 18 m: three rows of silver cages
(colliders) running its length, with aisles between; levers on the west
wall that slide whole rows on rails; a gallery above the east wall; the
ledger on a lectern at the north end. Edric Marrow is in the last cage of
the middle row.

**Body.** `cage_keeper`: Health 3,000, Speed 3.6, Damage 26, Radius 0.6; a
crossbow with silver bolts, then a sword; two Vigil sergeants with censers
(`vigil_sergeant`, Health 380, Guard).

**Phase 1, Inventory (100%–60%).** He keeps to the gallery and the far
aisles:
- **Silver bolts**: a line telegraph down an aisle, 1.1 s, × 1.4. The aisles
  are lanes; standing in one is standing in his sights.
- **The levers**: every 15 s a sergeant throws a lever and a row of cages
  slides 4 m (its new place drawn on the floor 2 s ahead, violet: "this
  will be solid"). Caught in the way, the survivor is pushed and hurt.
  The hall rearranges itself, and his lanes with it.
- **Censers**: violet zones that slow, carried by the sergeants.

**Phase 2, Arrears (60%–25%).** He opens a row:
- The caged come out, driven by a sergeant with a goad: six to ten frightened
  people who stumble toward the survivor because the goad is behind them.
  They barely hurt (contact × 0.2) and they are in the way. **Hitting them
  counts**: the story keeps a tally, and the people of Silverstair who live
  remember (`STORY_BIBLE.md` §7.10's "free the cages" goes better). Kill the
  goad and they scatter for the doors; area skills that cannot choose their
  targets become a cost. The day's version of "the boss commands the
  horde", where the horde are victims.
- He fires over them.

**Phase 3, Paid in Silver (25%–0).** He comes down with the sword:
- **Strike from the Book**: a ring telegraph round the survivor (radius 5,
  1.4 s); inside it at the end, they are pulled to him and struck (× 1.6).
- **Sum**: a three-swing combo, 0.8 s each, the last a cone.
- At 10% he goes for Edric's cage with the key, to take his best stock out
  the back. Stop him in 8 s (he is slowed while carrying) or he gets out of
  the door, and the fight ends with Edric gone and the Keeper with him
  (Ysolde's thread in the bible's harder direction).

**Drops.** The Cage Key (Named, `docs/items/ACQUISITION.md` §4), which opens
every cage; Sallow's Silver Pen if the ledger is taken from the lectern;
argent scraps.

**Day tools.** Grapple Chain pulls him off the gallery; Vault and Blink cross
a sliding row; Time Slip freezes a row mid-slide; skills that pierce are a
liability in Phase 2 and an asset in Phase 1.

## What the three share

- Each has one mechanic that is the story's choice made in play (the pump
  broken or blown; Keegan killed or spared; Edric kept or lost).
- Each telegraphs on the ground as the arena does, and adds one channel
  the night cannot: a voice (Keegan), a crew's job (the menders), a hall that
  moves (the levers).
- None asks for a build. Each asks the survivor to look before they swing.
