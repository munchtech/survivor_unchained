# Skills and upgrades: the design

How Survivor Unchained's skills are found, offered, ranked, combined and
balanced, by day and by night; why each part is built the way it is; the
numbers it is held to; and how to measure it. The research behind it is
`SKILLS_RESEARCH.md` (cited here as R§n, its part-two sections). The code is
`godot/logic` (content in `Content/`, the draft in `Sim/LevelUp.cs`), the
harness that measures it is `godot/balance`, and the tests that hold it are
in `godot/tests`.

The owner's standing note was "I don't want to polish, I want to create
perfection". So every section ends with **Why this is the answer**: what the
alternatives were, what the research and the harness said, and why this
shape beat them. Where a part was rebuilt more than once, the section says
what the earlier version got wrong.

---

## 1. The whole in one page

- **Ten paths** (archetypes): Steel and Blood, the Hunt, the Pyre, the Long
  Winter, the Storm, Dawn's Light, the Grave, the Wild, the Host, the Weave.
  A path is a lean, not a lock: carrying two of its combat skills puts it on
  the build, and its cards then come a little more often and say why.
- **26 combat skills**, each with **two evolutions** (52), each evolution
  wanting one of one or two named passives at rank 8. **Nine unions** join
  two evolved skills into one, freeing a slot. **25 passives**, **22
  milestone blessings** (rules: statuses, duos, chains) and **16 great
  blessings** in four roles (power, ward, answer, quickening). **17
  discoveries**: hidden pairings that do more together.
- **The offer**: three cards a level (a fourth with luck or gear), weighted by
  rarity and leaned by the build; a short list of **guarantees** so no draft
  is a dud; **pity** for rare cards and for a waiting evolution; **surges**;
  three **rerolls**, two **banishes**, a **skip** that refunds ember, and
  **honing** once a skill is finished.
- **Day feeds night**: skills carried by day are **attuned** (offered first,
  a rank or two up); skills learned are **familiar** (a lean); the calling's
  paths lean the draft; **kindled gear** gives the ember a level, a redraw,
  a banishing, a fourth card, a fourth great choice, or stands in for a
  passive in a recipe; the **codex** records every evolution and union seen,
  and the **tome** lets the survivor keep up to three of the night's skills.
- **The curve**: the ember climbs to about level 50 in thirty minutes; the
  build completes in the last third; ordinary creatures soften as the night
  goes on so the build's growth shows; champions, heralds and the boss keep
  the steep curve and are the test.

---

## 2. Principles

Taken from the research (R§1–R§11) and from what the harness showed.

1. **Lean, never lock** (R§1). Every bias is a weight between ×1.3 and ×2,
   felt over a run and not on a card. Nothing is closed to anyone.
2. **Guarantee the floor, not the ceiling** (R§2). A few promises make sure
   a draft always has something useful; the rest is chance.
3. **The card that completes a plan comes because the plan is nearly
   complete** (R§1, R§2): evolutions, catalysts and unions are gated by
   investment, never by luck alone, and never missed once earned.
4. **Say why** (R§5). A card that is favoured says what favoured it; a skill
   says what it becomes and with what; a trap is named a trap.
5. **Every skill has a reason and at least two builds that want it.** Tested
   (`RecipeTests`).
6. **Every path has an answer to a champion and a way to survive one**
   (R§6). Tested (`BalanceTests`, `BlessingTests`).
7. **No single rule carries a build** (R§10.5): a blessing's rule may make a
   build sing; it may not outdo the weapons it rides on. Tested.
8. **The run carries the fantasy; the meta widens it** (R§7): what the day
   brings to the night changes the draft (attunement, kindling) more than it
   adds power, and the climb from rank 5 to the evolution is always the
   night's own.
9. **The horde melts; the champions test** (R§8, R§9, and the feel study's
   S-01): ordinary creatures die faster as the night goes on, while the
   creatures that matter keep their curve.

---

## 3. The paths (archetypes)

| Path | Identity | Combat skills | Callings |
|---|---|---|---|
| Steel and Blood | Blades close in; wounds that bleed; finishing what bleeds | Oathblade, Cleaver, Axe Gyre, Iron Palms, Reaving Arc, Knifestorm, Gale Chakram, Dawnpulse, (Butcher's Wheel) | reaver, warden |
| The Hunt | Thrown and shot, many at once; marks, wounds and sure strikes | Volley, Knifestorm, Gale Chakram, Judgement Disc, Firepot, Moonbrand, (Hail of Steel) | stalker, warden |
| The Pyre | Fire that bursts, spreads from the dying, and leaves the ground burning | Cinderfall, Firepot, Hallowed Ground, Thunderhead, Seeking Motes, Verdant Lance, (Frostfire Comet) | arcanist |
| The Long Winter | Chill until they freeze; the frozen take more, and shatter | Rimeshard, Hoarfrost, Gale Chakram, Blightfield, Thornbloom, Seeking Motes, Cleaver, (Frostfire Comet) | arcanist |
| The Storm | Lightning that leaps, forks and falls; the shocked take more | Arcweb, Thunderhead, Iron Palms, Seeking Motes, Rimeshard, Axe Gyre, (The Tempest) | arcanist, reaver |
| Dawn's Light | Holy rings and hallowed ground; the seared burn; light that mends and wards | Dawnpulse, Hallowed Ground, Judgement Disc, Verdant Lance, Oathblade, Hoarfrost, (Dawn's Judgement) | warden |
| The Grave | Shadow that drinks: wounds that mend you, rot, and the dead on your side | Umbral Bolt, Grave Tether, Reaving Arc, Blightfield, Gravecall, (Soul Lantern) | reaver, arcanist |
| The Wild | Brambles, blight and green fire: ground that holds them, poison that spreads | Thornbloom, Blightfield, Verdant Lance, Spirit Herd, Hallowed Ground, Volley, (Rotwood) | stalker |
| The Host | Spirit beasts and risen dead that fight for you, while brambles hold the rest | Gravecall, Spirit Herd, Reaving Arc, Thornbloom, (Barrow Host) | stalker, reaver |
| The Weave | Seeking motes and moonfire in volleys; spells fired over and over | Seeking Motes, Moonbrand, Umbral Bolt, Arcweb, Rimeshard, Grave Tether, (Starfall) | arcanist |

(Unions in brackets: found only by uniting two evolved halves.) Each path
also names its passives, milestone blessings, great blessings and capstones
(the evolutions that crown it): `Content/Paths.cs`.

**How a path is reached.** `LevelUp.BuildPaths`: any path the build carries
two combat skills of, the two most invested first (ranks, evolutions, and
the path's passives and blessings held). From then on the path's cards are
leaned ×1.5 (skills and blessings) or ×1.3 (passives), and each says "On your
path: The Pyre". The calling's own paths lean its new skills ×1.3 from the
first draft, so a warden drifts toward steel and dawn without being held
there.

**Shapes and their weak matchups** (R§6). Each path is a shape (melee,
projectile, area, zone, summon, beam/chain) with a status, a defence and a
weak matchup: melee paths fear ranged packs and burst bosses, zone paths
fear fast flankers, projectile paths fear guarded fronts and swarms, summon
paths fear area damage that kills their allies. Every path holds an answer
(a great blessing or a capstone) to its weak matchup.

### Why this is the answer

The genre groups builds by shape and by status (R§6); ten paths cover the
shapes and the eight schools with two or three paths per calling, enough
that a calling's twentieth run is not its first (R§11), few enough that each
has a voice. Paths overlap on purpose (a crossover skill bridges two paths,
so a build can turn), but **a path's signature is its own**: the Weave lost
Cinderfall when the harness showed it had become the best of four schools
at once (the first and fifth most damaging skill in its builds were other
paths' cores), and the Weave fell from the top of every table to the pack.
The alternative, hard archetype classes chosen at the start (Death Must
Die's gods, a talent tree), was rejected: in a draft game the build should
be discovered in the run, and a lean with a reason shown on the card is
both discoverable and free.

---

## 4. Synergy families

### 4.1 Statuses: each with an offence and a defence

| Status | Applied by | It does | Its defence | Its deepening |
|---|---|---|---|---|
| Burn | Cinderfall, Firepot, Pyre of Faith, Cinderwake | Damage over time, stacks to five | **What burns strikes an Emberblood survivor 6% weaker a rank** | Kindling (spreads on death), Pyre Burst, Emberseekers |
| Chill / Frozen | Rimeshard, Hoarfrost, Chilling Presence, Hailwheel | Slows; five stacks freeze (not bosses) | Slowed and stopped creatures do not reach you | Deep Chill, Shatter, Frostbite (bleed ×3 on the frozen), Fracture |
| Bleed | Cleaver, Grave-Edge, A Thousand Cuts, Butcher's Wheel | Damage over time, more while moving; some bleeds stack | – (the steel path's defence is armour and Bloodthirst) | Blood Scent, Butcher's Mercy, Serration |
| Poison | Blightfield, Verdant Lance, Rotwood | Stacks to ten; at five, creatures slow | Poisoned creatures are slowed | Plague Bearer, Contagion, Venom |
| Shock | Arcweb, Thunderhead | The next blow takes 35% more | **Grounding** turns part of a blow to lightning | Static Charge (shock is not spent), Overload |
| Sear | Dawnpulse, Hallowed Ground, Judgement Disc | Holy takes 30% more; the dead burn | Warding Light, Iron Vow | Sanctify, Consecration |
| Mark | Moonbrand, Hunter's Mark, Deathcoil, Rootbind | Takes 30% more from everything | Rootbind holds what it marks | Death's Due, Lunar Brand |

### 4.2 Duos, discoveries and unions

- **Duos** are blessings that need two families at once (`Requirement.All`):
  Overload (shock and burn), Frostbite (chill and bleed), Fracture (chill and
  burn). They are offered only to a build that has both, so they are never a
  trap and always a reward for mixing.
- **Discoveries** (17) are hidden pairings of two combat skills that do more
  together (Frostfire Bolt, Shadowflame, Radiant Gyre...). They are found by
  carrying both; the codex records them; the hint is in the Book.
- **Unions** (9): two evolved skills become one, in one slot, at about nine
  tenths of the two together (the slot it frees makes up the rest).

| Union | Halves (both evolved) |
|---|---|
| Frostfire Comet | Cinderfall + Rimeshard |
| The Tempest | Arcweb + Thunderhead |
| Rotwood | Blightfield + Thornbloom |
| Butcher's Wheel | Axe Gyre + Cleaver |
| Hail of Steel | Volley + Knifestorm |
| Dawn's Judgement | Dawnpulse + Judgement Disc |
| The Barrow Host | Gravecall + Spirit Herd |
| Soul Lantern | Umbral Bolt + Grave Tether |
| Starfall | Seeking Motes + Moonbrand |

### Why this is the answer

A status that only adds damage makes every status the same choice with a
different colour. Giving each family a defensive face (chill slows, poison
slows, burn weakens, shock grounds, mark is held by roots) makes the status
a reason to build a path, not only a number, and gave the fragile paths a
ward that is theirs: the Pyre fell at the boss in a quarter to a half of
its runs until What-burns-strikes-weaker and From the Ashes, and its
deaths came almost entirely from runs that had neither. Duos follow Hades
(R§5: cross-family rewards with prerequisites, so the card appears because
the plan is there). Unions follow Vampire Survivors and HoloCure (R§4: a
slot freed is the late game's best reward), at 0.9 of the halves so that
uniting is always right for the slot and never a jump in power for its own
sake.

---

## 5. Evolutions

Every combat skill evolves at rank 8, into one of **two branches**, each
wanting one passive (or either of two) at any rank. Both earned: the
survivor chooses. An evolution costs nothing (a chest that brings one also
brings its other rewards), fires at once (the evolved skill's first volley
is the moment), and is never missed: an evolution earned is always among the
cards, and a skill at rank 7 or 8 waiting for its passive gets that passive
offered within two drafts (`CatalystPity`).

| Skill | School | Shape | Evolves into (with) |
|---|---|---|---|
| Oathblade | Physical | Slash | Oathkeeper (Ironhide); Grave-Edge (Serration) |
| Butcher's Cleaver | Physical | Slash | Whirlwind (Fleetfoot or Ferocity); Bonesplitter (Might) |
| Axe Gyre | Physical | Orbit | Gyrestorm (Ferocity); Reaver's Wheel (Serration) |
| Iron Palms | Physical | Palm | Temple Breaker (Evasion); Thunder Palm (Haste or Conduit) |
| Reaving Arc | Shadow | Nova | Rend and Mend (Recovery or Vitality); The Harrowing (Expanse or Kinship) |
| Volley | Physical | Spray | Arrowfall (Velocity); Predator's Volley (Precision) |
| Knifestorm | Physical | Ring | Steel Flurry (Fleetfoot); A Thousand Cuts (Serration) |
| Gale Chakram | Physical | Chakram | Razorgale (Serration); Hailwheel (Chilling Presence) |
| Judgement Disc | Holy | Bounce | Reckoning (Fortune or Precision); Aegis Wheel (Ironhide or Vitality) |
| Firepot | Fire | Aimed | Powder Keg (Might); Wildfire (Emberblood or Perennial) |
| Seeking Motes | Arcane | Aimed | Mote Cascade (Duplicity); Starseeker (Precision) |
| Moonbrand | Arcane | Aimed | Moonfall (Greed's Pull or Expanse); Lunar Brand (Fortune) |
| Cinderfall | Fire | Aimed | Fallen Star (Expanse); Living Flame (Perennial or Emberblood) |
| Rimeshard | Frost | Aimed | Deepwinter (Haste); Glacier Spear (Velocity) |
| Hoarfrost | Frost | Nova | Winter Ward (Warding Light); Absolute Zero (Chilling Presence) |
| Arcweb | Storm | Chain | Skybreak (Precision or Conduit); Tempest Coil (Expanse) |
| Thunderhead | Storm | Storm | Eye of the Storm (Conduit); Thunderclap (Might) |
| Umbral Bolt | Shadow | Aimed | Ruin Bolt (Might); Soul Siphon (Recovery) |
| Grave Tether | Shadow | Aimed | Tether of Anguish (Wisdom or Recovery); Deathcoil (Duplicity) |
| Gravecall | Shadow | Raise | Barrow Legion (Kinship); Bone Knights (Ironhide or Vitality) |
| Dawnpulse | Holy | Nova | Circle of Dawn (Vitality or Recovery); Sunbreak (Might) |
| Hallowed Ground | Holy | Zone | Sanctified Earth (Ironhide or Warding Light); Pyre of Faith (Searing Aura or Emberblood) |
| Blightfield | Shadow | Zone | Blighted Earth (Chilling Presence or Venom); Plaguebloom (Perennial) |
| Thornbloom | Nature | Zone | Everbloom (Thorns or Venom); Strangleroot (Chilling Presence) |
| Verdant Lance | Nature | Beam | Verdant Gaze (Evasion or Venom); Sunlance (Searing Aura) |
| Spirit Herd | Nature | Herd | The Great Herd (Perennial or Kinship); The Wild Hunt (Fleetfoot) |

**Evolutions that do what they say.** Each evolution's description is its
rule: Grave-Edge finishes what bleeds below a sixth, Lunar Brand throws the
mark on a death, Frostfire Comet's frozen explode. Where an evolution is
more than numbers it carries its own triggers (`Evolution.Triggers`),
credited to the skill so the harness can see what it does.

**After the evolution: honing.** A finished skill can be honed ten times,
+12% each, so the late draft still has depth when the slots are full (R§10.2,
autopilot).

### Why this is the answer

Branching beats destiny (R§5): a choice at the evolution is a second
decision on top of the recipe, and the same skill ends two ways across
runs. One passive per branch (not two, not a chest-only gate) keeps the
recipe readable on the card: "At rank 8, with Serration, it evolves." The
alternatives were Vampire Survivors' single destiny (one recipe per weapon:
less replay) and Rogue: Genesia's multi-ingredient recipes (unreadable
without a wiki). A minute gate (the feel study's S-10 suggests offering
evolutions only from the tenth minute) was measured and not needed: a build
that plans gets its first evolution at a median of about ten minutes, one
that does not at twenty, so the moment is earned and still centred in the
run; a gate would only tell a player who planned well to wait.

---

## 6. The offer

### 6.1 What a draft is

Each ember level owes a **skill draft**: three cards (`LevelUp.Draft`).

| Card | What it is |
|---|---|
| New combat skill | while fewer than six are carried |
| Rank | +1 rank in a skill or passive carried (to 8 for skills, to the passive's max) |
| Evolution | a skill at rank 8 with its passive held |
| Union | two evolved halves |
| New passive | while fewer than six are held |
| Hone | +12% for a finished skill, ten times at most |
| Heal, coin | only when nothing else can be offered |

**Great blessing drafts** come as the arena begins and at its fifteenth
minute (three cards, then four); **milestone blessing drafts** at ember
levels 5, 12, 21, 32, 45, 60 (each gap two more than the last).

### 6.2 Weights

A card's weight is its rarity weight times its leans times its novelty.

| Rarity | Common | Uncommon | Rare | Epic | Legendary |
|---|---|---|---|---|---|
| Weight | 10 | 6.5 | 3.6 | 1.7 | 0.7 |

| Lean | ×
|---|---|
| On the build's path (skill or blessing) | 1.5 |
| On the build's path (passive) | 1.3 |
| On the calling's paths (new skill) | 1.3 |
| Attuned (carried by day) | 2.0 |
| Familiar (learned by day) | 1.3 |
| Shown in the draft just rerolled | 0.15 |
| A trap (a passive that touches nothing the build has) | 0.3 |
| Rare pity: per skill draft without a rare card | × min(4, 1 + 0.3 × drafts) |

Luck raises the rare weights and deals a fourth card with chance
`1 − 1/Luck` (Vampire Survivors' rule).

### 6.3 Guarantees

In order, each filling a card only if the draft does not already hold one:

1. **An evolution earned** is always offered.
2. **An attuned skill** not yet taken is among the cards in the first four
   skill drafts.
3. **A rare card** after ten skill drafts without one (the pity's floor).
4. **A waiting evolution's passive** within two drafts.
5. **A new combat skill** while fewer than three are carried.
6. **A combat skill** in every draft.
7. **A card that ranks what you carry** once two skills are carried.

What a guarantee placed stays placed (a later guarantee never swaps it
out).

### 6.4 Surges

Any rank card may **surge**: two ranks at once, with chance
`max(0.05, 0.05 + 0.15 × (Luck − 1))`, shown on the card.

### 6.5 Reroll, banish, skip, hone

| Tool | How many | What it does |
|---|---|---|
| Reroll | 3, +1 a rank of Wisdom, +1 at each milestone, +1 from kindled gear; at most 9 held | Redraws, avoiding what was shown |
| Banish | 2, +1 at the fifteenth minute's great blessing, +1 from kindled gear | Removes a card for the rest of the arena, ranks included |
| Skip | always (not a blessing draft) | Refunds 40% of the ember of the level before |
| Hone | – | A finished skill's late depth |

### 6.6 Great blessings by role

| Role | What it is for | Great blessings |
|---|---|---|
| Power | more of what the build does | Momentum, Arcane Overflow, Glass Cannon, Duelist's Grace, Cinderwake, Stormborn, Spirit Companion |
| Ward | surviving the night | Bloodthirst, Iron Vow, **From the Ashes**, **Grounding** |
| Answer | felling a champion | Hunter's Mark, **Rootbind**, **Go for the Throat** |
| Quickening | tempo and economy | Restless Hands, Ember Tithe |

A great hand is **dealt by role**: a ward, a power, then an answer or a
quickening, then (the fourth card) anything. Every path lists a ward among
its great blessings; the slow champion-killers (the Wild, the Host, the
Grave, the Long Winter) list an answer.

The four new ones:

- **From the Ashes** (Pyre, Dawn): once a night a killing blow burns instead:
  rise at half health, and everything near catches fire. Rank 2: rise whole,
  the fire twice as wide. Rank 3: twice a night. The ember's own, lost at
  dawn.
- **Grounding** (Storm, Weave): a fifth of every blow is turned to lightning
  that leaps to three creatures near you. Rank 2: a third. Rank 3: six, and
  shocked.
- **Rootbind** (Wild, Long Winter): every 6 s roots hold the toughest thing
  near you for a second and it takes 40% more while held. Rank 2: the two
  toughest. Rank 3: every 4 s.
- **Go for the Throat** (Host, Grave): what fights for you goes for the
  toughest thing near you and strikes champions 40% harder. Rank 2: 20%
  faster. Rank 3: each champion felled calls a spirit wolf for the night.

### Why this is the answer

- **Weights and leans.** Rarity as frequency (not magnitude) keeps a rank
  card a rank card; leans between ×1.3 and ×2 are felt over a run and not on
  a card (R§1). The attuned lean is the largest because it is the day's
  promise to the night.
- **Guarantees, not a scripted draft.** Each guarantee answers a failure
  the genre is known for (R§10): dilution (a new skill until three, then
  always something that ranks what you carry), the evolution missed (always
  offered), the drought (rare floor, catalyst pity). An early version let
  the last guarantee swap out the card an earlier one placed; the harness
  found drafts with no rare for twenty levels. The "what a guarantee placed
  stays" rule and the rare floor fixed it, and `OfferTests` hold each
  promise over hundreds of seeded drafts.
- **Tools.** Three rerolls and two banishes, growing to the genre's
  comfortable ceiling across a run (R§3), are scarce enough to be decisions.
  The skip refunds ember because a skip that returns nothing is used only by
  experts (R§3). Banish removes ranks too, because a card banished that
  comes back as a rank feels like a lie.
- **Great hands dealt by role.** The harness showed what happens when a
  great hand is three random greats: a fragile path that is shown three
  powers has no way to survive the boss. Measured at tier 2 with each path's
  bot: the Pyre fell in 50% of runs; with From the Ashes taken, one run in
  fifteen fell. Dealing a ward into every hand gives every survivor the
  choice without taking the choice away. A role label is also how a new
  player reads four unfamiliar cards.

---

## 7. Slots

Six combat skills and six passives, as in Vampire Survivors and HoloCure:
thirty minutes of drafts (about fifty ember levels, plus seven blessing
drafts) is enough to fill both, take the six skills to rank 8 and evolve
three or four of them. A union frees a combat slot; honing is the depth
after the slots close.

### Why this is the answer

R§4: six and six is the genre's default because it matches the number of
level-ups in thirty minutes. Four slots (DRG, Megabonk) make evolutions
come sooner but leave the late draft empty; unlimited passives (Brotato)
make passives into stats. Measured: a planning bot completes its build at
about 23–28 minutes, leaving the last minutes for the power to show.

---

## 8. Day and night

| By day | What it does for the night |
|---|---|
| **Carrying** a skill (the day's slots) | **Attuned**: offered in the first four skill drafts, at rank 2 (rank 3 from character level 10), leaned ×2 |
| **Learning** a skill | **Familiar**: leaned ×1.3 |
| The **calling** | its paths lean new skills ×1.3; its first skill is taught by its paths |
| **Gear**: the weapon and worn skills | brings them in at their rank, **four at most** |
| **Gear**: statuses | leans the draft toward cards that use them |
| **Gear**: kindled affixes | see 8.1 |
| The **codex** | every evolution and union seen, with its recipe |
| The **tome** (after a night) | keep up to three of the night's skills to carry by day |

### 8.1 Gear and the ember: kindled affixes

From the items plan (`docs/items/SYSTEM.md` §6.4), built on the ember's
side. A kindled affix is a suffix on Rare gear and better, **one to an
item, two to a survivor** (a third does nothing), that shapes the night's
draft without owning it:

| Affix | In the ember |
|---|---|
| of the First Spark | the ember starts a level higher |
| of Second Thoughts | +1 reroll |
| of Refusal | +1 banish |
| of Many Roads | every skill draft shows a fourth card |
| of Omens | great blessings offer a fourth choice |
| of the Whetstone, of Rime, of the Censer, of the Wide Field, of the True Eye, of Mending, of the Ox, of the Evergreen, of the Adder, of the Pack, of the Lodestone, of Embers | counts as Serration, Chilling Presence, Searing Aura, Expanse, Precision, Recovery, Might, Perennial, Venom, Kinship, Conduit or Emberblood **in an evolution's recipe** (the passive slot stays free); the card says "your gear stands in" |

Gear never brings a blessing, an evolution or a rank past four: ranks five
to eight and the evolution are the ember's alone (`Inventory.GearRankCap`).

### Why this is the answer

The night must stay the night's (the ember is borrowed and lost at dawn),
but the day must matter to it, or the two halves are two games (R§7). The
research's best meta levers change the draft rather than the numbers (R§7:
rerolls, banish, a fourth card), so that is what crosses: attunement makes
the day's skill choice a night plan; kindling makes gear a way to plan an
evolution or widen the draft; the rank cap keeps a geared survivor from
starting at the end. The items plan and this design were folded into one
rule set: the kindled affixes are items' content and the ember's rules, and
the stand-in uses the draft's own recipe check (`LevelUp.Holds`) so every
place that reads a recipe (the card hint, the arsenal, the catalyst pity)
agrees.

---

## 9. The power curve

### 9.1 The ember's pace

`EmberNeed(n) = round(20 + 28n + 3.2n² + (n > 28 ? 8(n − 28)² : 0))`.
Measured at tier 1 (median of 144 runs):

PACE_TABLE

The first minute gives about six cards (five levels and the first great
blessing), then two or three a minute, under two late (R§9: between 0.5 and
3 a minute).

### 9.2 The horde

Creatures scale by level (`Enemies.ScaleFor`: health `1 + 0.38l + 0.035l²`,
damage `1 + 0.14l`); the arena's level rises a step every two and a half
minutes, two a tier. **Ordinary creatures soften as the night goes on**:
their health is divided by `1 + 0.08 × minute` (`ArenaRun.FodderEase`).
Champions, heralds and the boss keep the full curve. A field mown below
60% of its number refills twice as fast, in groups twice the size.

### 9.3 Champions, heralds, the boss

- **Champions**: any creature may come as a champion (three times the
  health, a level up), more often as the minutes pass.
- **Heralds** at ten and twenty minutes: a champion of champions carrying a
  chest.
- **The boss** at thirty: the people's ruler, `9 + 3 × tier` times its
  health, with an escort.

### Why this is the answer

The feel study measured what players of the genre describe (the power
fantasy is a slope: you start fleeing and end wading in) and found it
inverted: ordinary creatures took more blows to kill at minute thirty than
at five. The harness agreed (the median ordinary creature lived 0.45 s at
minute five and 0.9 s at twenty-five, at tier 2). Of the ways to turn it
round, scaling the player up further breaks every other number (bosses melt),
and slowing the horde's level curve also softens the champions that are the
test. Dividing only ordinary creatures' health by a gentle line keeps the
champions honest, turns the slope the right way, and the spawner that keeps
up turns the ease into volume. The study proposed 0.12 a minute; the harness
measured that as one-blow kills from the third minute and the arena's
lowest health at 90% all night (no threat until the boss), so the design
uses 0.08. The boss's health was raised by half at the same time: research
places a boss at thirty to ninety seconds (R§9), and the path bots were
killing it in ten to thirty.

---

## 10. Targets, and what was measured

TARGETS_TABLE

---

## 11. Diversity and replayability

- Ten paths, four callings, each calling two to four paths: about thirty
  calling-and-path pairs, each with a different start (the calling's art
  and first skill) and leaning differently.
- 52 evolutions in pairs: the same skill ends two ways.
- Nine unions and seventeen discoveries to find; the codex records them.
- Sixteen great blessings in four roles, two chosen a night: about 240
  pairs.
- Oaths and peoples change the horde (and lean the gear it drops).
- Measured: CARD_DIVERSITY

### Why this is the answer

R§11: the twentieth run stays fresh through different starts, rule changes
chosen at the start, conditions chosen by the player, a collection, and
branching. Each is here; the harness checks that none of them collapses into
one answer (no path above the others by the balance index, no blessing above
45% of a build's damage).

---

## 12. The harness

`godot/balance` is a console program that plays the real `godot/logic`
headless, at 60 ticks a second, with bots for hands:

- **Pilot** (`Harness/Pilot.cs`): gives ground when pressed, closes when its
  weapons are short, collects ember when it is quiet, dashes across a
  champion's lunge, uses its art on a crowd, drinks when low.
- **Pickers** (`Harness/Picker.cs`): `first`, `random`, `greedy` (scores
  each card by what it advances), `path:ID` (holds to a path), each with a
  reroll, banish and skip policy.
- **Commands** (from `godot/balance`, after `dotnet build -c Release`):

      dotnet bin/Release/net8.0/Balance.dll arena --callings all --policies greedy,random,first --seeds 12 --tier 1 --par 16 --out out/t1.jsonl
      dotnet bin/Release/net8.0/Balance.dll arena --callings all --policies paths --seeds 10 --tier 2 --out out/paths.jsonl
      dotnet bin/Release/net8.0/Balance.dll probe --callings all --policies paths --levels 29 --seeds 4 --builds
      dotnet bin/Release/net8.0/Balance.dll weapons --seeds 4 --out out/w.md
      dotnet bin/Release/net8.0/Balance.dll report --in out/t1.jsonl

  `arena` plays whole arenas and reports win and fall rates, ember pace,
  time to kill (fodder, champion, herald, boss), damage by source, card
  offer and take rates, evolutions and killers, by minute. `probe` drafts a
  build to an ember level and puts it through a standard crowd and
  champion. `weapons` measures every skill alone at rank 1, 4, 8 and evolved,
  and every union against its halves.
- **Scripts**: `tune_weapons.py`, `tune_blend.py` (probe and arena shares
  together), `tune_unions.py` (unions to 0.9 of their halves), `shares.py`.

**Tests that hold the design** (`cd godot/tests && dotnet test`):

| Test file | Holds |
|---|---|
| `OfferTests` | every guarantee over hundreds of seeded drafts; leans; pity; surge; reroll avoids; banish removes ranks; skip refund; great hands dealt by role |
| `RecipeTests` | every evolution recipe and union is reachable; every skill is on a path; every passive and blessing is wanted by two paths |
| `BalanceTests` | every path reaches its power (crowd ≥ 0.7 of the median, champion ≥ 0.25, toughness ≥ 0.55); none runs away (crowd ≤ 1.35, power index ≤ 1.9); no rule over 45% of a build's damage |
| `BlessingTests` | great blessings deepen; each new great does what it says; every path has a ward |
| `KindledTests` | two kindlings at most; stand-ins evolve at rank 8 and not before; a fourth card; a fourth great; the rank cap |

---

## 13. Before and after

BEFORE_AFTER

---

## 14. Open

OPEN_ITEMS
