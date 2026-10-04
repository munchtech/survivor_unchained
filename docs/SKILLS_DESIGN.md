# Skills and upgrades: the design

How Survivor Unchained's skills are found, offered, ranked, combined and
balanced, by day and by night; why each part is built the way it is; the
numbers it is held to; and how to measure it. The research behind it is
`SKILLS_RESEARCH.md` (cited here as R§n, its part-two sections). The code is
`godot/logic` (content in `Content/`, the draft in `Sim/LevelUp.cs`), the
tool that measures it is `godot/balance`, and the tests that hold it are in
`godot/tests`.

The owner's standing notes were "I don't want to polish, I want to create
perfection", and "do we have soul?": one game in a million, not one
soulless game of many. So every section ends with **Why this is the
answer**: what the alternatives were, what the research and the harness
said, and why this shape beat them. Section 2 answers the second note on
its own.

---

## 1. The whole in one page

- **Ten paths** (archetypes): Steel and Blood, the Hunt, the Pyre, the Long
  Winter, the Storm, Dawn's Light, the Grave, the Wild, the Host, the Weave.
  A path is a lean, not a lock: carrying two of its combat skills puts it on
  the build, and its cards then come a little more often and say why.
- **26 combat skills**, each with **two evolutions** (52), each evolution
  wanting one of one or two named passives at rank 8. **Nine unions** join
  two evolved skills into one, freeing a slot. **25 passives**, things and
  habits of the valley (Legion Bronze, Morrow Pippins, the Ford's Cold).
  **22 milestone blessings** (rules: statuses, duos, chains) and **20 great
  blessings** in four roles (power, ward, answer, quickening), four of them
  a calling's own. **17 discoveries**: hidden pairings that do more together.
- **The offer**: three cards a level (a fourth with luck or gear), weighted by
  rarity and leaned by the build; a short list of **guarantees** so no draft
  is a dud; **pity** for rare cards and for a waiting evolution; **surges**;
  three **rerolls**, two **banishes**, a **skip** that refunds ember, and
  **honing** once a skill is finished. Great blessings come at **Dusk** and
  **Midnight**, dealt by role so every hand holds a ward.
- **Day feeds night**: skills carried by day are **banked** (the ember
  sleeps in them through the day; the night offers them first, a rank or two
  up); skills learned are **familiar**; the calling's paths lean the draft;
  **kindled gear** gives the ember a level, a redraw, a banishing, a fourth
  card, a fourth great choice, or stands in for a passive in a recipe; the
  **codex** records every evolution and union seen, and the **tome** lets the
  survivor keep up to three of the night's skills for the day.
- **The curve**: the ember climbs to about level 50 in thirty minutes; the
  build completes in the last third; ordinary creatures soften as the night
  goes on so the build's growth shows; champions, heralds and the boss keep
  the steep curve and are the test. A tier is three creature levels, the
  survivor's own pace, so a night at their tier is fair and one above it hard.

---

## 2. Soul: why this is the valley's draft and no other game's

The genre's weakest games are a spreadsheet of "+10% damage" with a fantasy
skin. The test the owner set is whether the skills could belong to any
other world. What makes these belong to this one:

1. **The ember is the mechanic.** In the story the ember is a light that
   leaks out of the ground, sleeps in the survivor by day and burns at night,
   and drains away at dawn. The draft is built on exactly that: the ember
   level is the night's power and is lost at dawn (every blessing, every
   rank, every rising of Cold, Then Not); what was carried by day is
   **banked**, sleeping in the survivor until the night wakes it a rank or two
   up; the stones are gathered (Lampling's Scoop, Toll-Runner's Boots) and
   can flood (Ember Flood fires everything at once); a gear's kindling feeds
   the ember without owning it. A player learns the world's central fact by
   playing the draft.
2. **The survivor's own nature, told by a blessing.** Act 1 only hints that
   the survivor died at the ford ("you were cold when they brought you in;
   then you weren't"). **Cold, Then Not** is the ward that lets you rise once
   a night, and **the Ford's Cold** is the aura that never left you. Neither
   says the answer; both are true.
3. **The valley's things, not stats.** Every passive is a thing or habit of
   the valley that does what it says: Watch Mail from the Watch's unpaid
   stores, which counts blows as the Watch counts everything; Bitterroot that
   the hunters chew and that draws poison; Ember-Slurry, the Dig's poison in
   the stream; Night-Eyes that see the far ones in the dark; Wolf-Tooth that
   takes the wounded as the Pack does; the Wayfinder's Chart that gives a
   redraw. Where a plain number was all a passive was, it gained a small rule
   of its own (section 6).
4. **The callings fight their own way.** Each calling has a great blessing no
   one else is offered: the warden **Holds the Crossing** (standing still,
   harder and faster: the Wardens held crossings), the reaver is **Blood Up**
   (stronger below a third of health), the arcanist's spells are given a
   **Second Reading**, the stalker strikes true from **the Hunters' Blind**.
5. **Paths are the valley's ways of fighting.** Each says who fights like
   that (the Watch and the old empire for Steel; the Kerchiefs and the
   Verge's hunters for the Hunt; the Order of the Morning Light for Dawn;
   the barrow for the Grave; the Pack and the risen for the Host).
6. **Discoveries speak in the valley's voice.** Their hints are folk wisdom
   and road talk ("Old wives on the ford road say a fire lit on ice burns
   twice"; "The Kerchiefs fletch with something that glows. Nobody on the
   road asks what"); one is named for a secret place (the Moon Grove).
7. **The night has hours.** The first great blessing comes at Dusk, the
   second at Midnight; the boss is what rules the people, at the hour before
   dawn.
8. **Statuses have two faces.** Each family hurts, and each protects:
   chill slows, poison slows, what burns strikes an Emberblood survivor
   weaker, lightning grounds a blow, roots hold the toughest. A status is a
   way of fighting, not a colour on a number.

Every name and line is safe for Act 1: none says what the ember is, what
the survivor is, or what lies under the Verge (`STORY_BIBLE.md` §3).

### Why this is the answer

A theme laid over generic mechanics is noticed once; mechanics that are the
theme are felt every draft. The alternative (keep generic names, write lore
elsewhere) would have left the most repeated choice in the game, the draft,
as the one place the world is absent.

---

## 3. Principles

Taken from the research (R§1–R§11) and from what the harness showed.

1. **Lean, never lock** (R§1). Every bias is a weight between ×1.3 and ×2,
   felt over a run and not on a card. Nothing is closed to anyone except a
   calling's own great blessing.
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
   brings to the night changes the draft more than it adds power, and the
   climb from rank 5 to the evolution is always the night's own.
9. **The horde melts; the champions test** (R§8, R§9, the feel study's S-01).
10. **Every mechanic belongs to the world** (section 2).

---

## 4. The paths (archetypes)

| Path | Identity | Who fights this way | Combat skills (union) | Callings |
|---|---|---|---|---|
| Steel and Blood | Blades close in; wounds that bleed; finishing what bleeds | The Watch's way, and the old empire's before it | Oathblade, Cleaver, Axe Gyre, Iron Palms, Reaving Arc, Knifestorm, Gale Chakram, Dawnpulse (Butcher's Wheel) | reaver, warden |
| The Hunt | Thrown and shot, many at once; marks, wounds and sure strikes | As the Kerchiefs take the road and the hunters keep the Verge | Volley, Knifestorm, Gale Chakram, Judgement Disc, Firepot, Moonbrand (Hail of Steel) | stalker, warden |
| The Pyre | Fire that bursts, spreads from the dying, and leaves the ground burning | Ember burns: the first thing anyone in the valley learns | Cinderfall, Firepot, Hallowed Ground, Thunderhead, Seeking Motes, Verdant Lance (Frostfire Comet) | arcanist |
| The Long Winter | Chill until they freeze; the frozen take more, and shatter | The ford's cold, carried inland | Rimeshard, Hoarfrost, Gale Chakram, Blightfield, Thornbloom, Seeking Motes, Cleaver (Frostfire Comet) | arcanist |
| The Storm | Lightning that leaps, forks and falls; the shocked take more | The storms off the hills that split the oaks | Arcweb, Thunderhead, Iron Palms, Seeking Motes, Rimeshard, Axe Gyre (The Tempest) | arcanist, reaver |
| Dawn's Light | Holy rings and hallowed ground; the seared burn; light that mends and wards | The Order of the Morning Light, and its one fool of a priest | Dawnpulse, Hallowed Ground, Judgement Disc, Verdant Lance, Oathblade, Hoarfrost (Dawn's Judgement) | warden |
| The Grave | Shadow that drinks: wounds that mend you, rot, and the dead on your side | What the barrow keeps, and what it lets go of | Umbral Bolt, Grave Tether, Reaving Arc, Blightfield, Gravecall (Soul Lantern) | reaver, arcanist |
| The Wild | Brambles, blight and green fire: ground that holds them, poison that spreads | The Verge's brambles, its green water and its sick wolves | Thornbloom, Blightfield, Verdant Lance, Spirit Herd, Hallowed Ground, Volley (Rotwood) | stalker |
| The Host | Spirit beasts and risen dead that fight for you, while brambles hold the rest | The Pack, the risen, the brambles | Gravecall, Spirit Herd, Reaving Arc, Thornbloom (Barrow Host) | stalker, reaver |
| The Weave | Seeking motes and moonfire in volleys; spells fired over and over | Moonlight and shadow, sent to find their own way | Seeking Motes, Moonbrand, Umbral Bolt, Arcweb, Rimeshard, Grave Tether (Starfall) | arcanist |

Each path also names its passives, milestone blessings, great blessings and
capstones: `Content/Paths.cs` (with `Lore`, the "who fights this way").

**How a path is reached.** `LevelUp.BuildPaths`: any path the build carries
two combat skills of, the two most invested first. Its cards are then leaned
×1.5 (skills and blessings) or ×1.3 (passives) and each says "On your path:
The Pyre"; the draft's header says "Walking the Weave and the Pyre". The
calling's own paths lean its new skills ×1.3 from the first draft.

**Shapes and their weak matchups** (R§6). Each path is a shape with a status,
a defence and a weak matchup: melee fears ranged packs and burst bosses,
zones fear fast flankers, projectiles fear guarded fronts and swarms, summons
fear area damage. Every path holds a ward and an answer among its great
blessings (section 8.6).

### Why this is the answer

The genre groups builds by shape and by status (R§6); ten paths cover the
shapes and the eight schools with two to five paths per calling, enough
that a calling's twentieth run is not its first (R§11), few enough that each
has a voice. Paths overlap on purpose (a crossover skill lets a build turn),
but **a path's signature is its own**: the Weave lost Cinderfall when the
harness showed it had become the best of four schools at once, and fell
from the top of every table into the pack. Hard classes chosen at the start
(Death Must Die's gods, a talent tree) were rejected: in a draft game the
build should be discovered in the run.

---

## 5. Synergy families

### 5.1 Statuses: each with an offence and a defence

| Status | Applied by | It does | Its defence | Its deepening |
|---|---|---|---|---|
| Burn | Cinderfall, Firepot, Pyre of Faith, Cinderwake | Damage over time, stacks to five | What burns strikes an **Emberblood** survivor 6% weaker a rank | Kindling, Pyre Burst, Emberseekers |
| Chill, Frozen | Rimeshard, Hoarfrost, the Ford's Cold, Hailwheel | Slows; five stacks freeze (not bosses) | Slowed and stopped creatures do not reach you | Deep Chill, Shatter, Frostbite, Fracture |
| Bleed | Cleaver, Grave-Edge, A Thousand Cuts, Butcher's Wheel | Damage over time, more while moving; some bleeds stack | (Steel's ward is Bloodthirst and Watch Mail) | Blood Scent, Butcher's Mercy, Whetstone |
| Poison | Blightfield, Verdant Lance, Rotwood | Stacks to ten; at five, creatures slow | Poisoned creatures are slowed; Bitterroot draws it out of you | Plague Bearer, Contagion, Ember-Slurry |
| Shock | Arcweb, Thunderhead | The next blow takes 35% more | **Grounding** turns part of a blow to lightning | Static Charge, Overload |
| Sear | Dawnpulse, Hallowed Ground, Judgement Disc | Holy takes 30% more; the dead burn | Warding Light, Iron Vow | Sanctify, Consecration |
| Mark | Moonbrand, Hunter's Mark, Deathcoil, Rootbind | Takes 30% more from everything | **Rootbind** holds what it marks | Death's Due, Lunar Brand |

### 5.2 Duos, discoveries, unions

- **Duos** need two families at once (`Requirement.All`): Overload (shock and
  burn), Frostbite (chill and bleed), Fracture (chill and burn). Offered only
  to a build that has both, so never a trap and always a reward for mixing.
- **Discoveries** (17): two combat skills that do more together, found by
  carrying both, recorded in the codex, hinted in the Book in the valley's
  voice.
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

A status that only adds damage makes every status the same choice in a
different colour. A defensive face makes a status a reason to walk a path,
and gave the fragile paths a ward that is theirs. Duos follow Hades (R§5:
cross-family rewards behind prerequisites). Unions follow Vampire Survivors
and HoloCure (R§4: a freed slot is the late game's best reward), at 0.9 of
the halves so uniting is always right for the slot and never a jump in power
for its own sake; `tune_unions.py` holds each union there with the harness's
union stage.

---

## 6. Passives: the valley's things

| Passive (id) | What it is, and does |
|---|---|
| Legion Bronze (`might`) | Old-empire bronze, green at the edges and still the hardest thing in the valley: +10% damage with everything, and your blows land 10% heavier. |
| Trimmed Wick (`haste`) | A wick trimmed short burns quick: every weapon fires 8% more often. |
| Toll-Runner's Boots (`fleetfoot`) | Worn thin on the toll road: +10% movement speed, and on the run ember comes to you from 10% farther. |
| Lampling's Scoop (`greed`) | Ember, gold and draughts fly to you from 1.2 m farther, and every stone holds 4% more ember. The Dig will want it back. |
| Morrow Pippins (`vitality`) | A pocketful of the valley's apples: +25 maximum health, and a heal when taken. |
| Watch Mail (`ironhide`) | From the Watch's stores, never paid for: +3 armour, and it counts: every tenth blow that reaches you glances off. |
| Night-Eyes (`precision`) | You see the weak places better in the dark: +7% critical strike chance, and 3% more against anything beyond six paces. |
| Wolf-Tooth (`ferocity`) | It bites deeper than it should: +25% critical strike damage, and the wounded (below half) feel 12% more of it. |
| Ford Lamp (`expanse`) | Light thrown wide, like the lamps at the ford: +12% area. Novas, fields, orbits, storms and auras are bigger; chains, beams and blades reach farther. |
| Second Shadow (`duplicity`) | Everything you send out has a shadow that flies beside it: +1 projectile. |
| Crossroads Penny (`fortune`) | Left at the crossroads, and picked up again: +10% luck. A fourth card more often, rarer cards, ranks that surge, better drops. |
| Wayfinder's Chart (`wisdom`) | Every road on it, and some that aren't there yet: +6% ember from every stone, and a redraw with every rank. |
| Bitterroot (`recovery`) | Chewed slowly, as the hunters do: +0.6 health regenerated per second, and burning or poison on you wears off twice as fast. |
| Grey Fletching (`velocity`) | Goose-grey and cut close: projectiles fly 12% faster and land 5% harder. |
| Evergreen (`perennial`) | +10% duration: fields, gyres, beasts and ground effects last longer. |
| Fen Step (`evasion`) | Light on soft ground: +7% chance to avoid a blow entirely, and a blow avoided leaves you 20% quicker for a moment. |
| Bramble Coat (`thorns`) | Struck, you burst with thorns: everything close takes a blow that grows with the ember, and what struck you takes a fifth of its blow back. |
| Whetstone (`serration`) | Critical strikes open a wound that bleeds 30% of the blow over 3 s. |
| The Ford's Cold (`chilling`) | The cold of the ford never quite left you: creatures near you are slowed, more as they come closer. |
| Morning Light (`searing`) | A holy light sears everything near you twice a second. |
| Emberblood (`emberblood`) | +10% fire damage; what you set burning burns 15% longer, and strikes you 6% weaker. |
| Conduit (`conduit`) | +10% storm damage, and the shocked take 6% more from the blow that finds them. |
| Ember-Slurry (`venom`) | What the Dig pours into the stream: damage over time (burning, bleeding, poison, searing) is 12% stronger, and every status takes hold 10% more often. |
| Pack-Bond (`kinship`) | What fights for you strikes 15% harder and is 15% tougher. |
| Warding Light (`warding`) | Blocks one blow completely, then recharges (12 / 9 / 6 s). |

The plain stat passives (Trimmed Wick, Ford Lamp, Second Shadow, Grey
Fletching, Evergreen, Crossroads Penny) stay plain on purpose: they are the
genre's Spinach and Candelabrador, the clean multipliers a build is planned
around, and each is a catalyst. The rest carry a rule.

### Why this is the answer

Every passive is a catalyst for at least one evolution and wanted by two
paths (tested), so none is a dead pick (R§10.3). The riders are small (a
tenth of blows, a few per cent of crit) so the catalyst roles and the path
balance hold; where a rider moved a path past its bounds (Night-Eyes doubled
crit at range, and the Storm's crowd damage ran 59% over the median), the
balance tests caught it and it was cut to 3% a rank.

---

## 7. Evolutions

Every combat skill evolves at rank 8 into one of **two branches**, each
wanting one passive (or either of two) at any rank. With both earned, the
survivor chooses. An evolution costs nothing, fires at once (its first volley
is the moment), and is never missed: an evolution earned is always among the
cards, and a skill at rank 7 or 8 waiting for its passive is offered that
passive within two drafts. A finished skill can be **honed** ten times, +12%
each, so the late draft still has depth.

| Skill | School | Shape | Evolves into (with) |
|---|---|---|---|
| Oathblade | Physical | Slash | Oathkeeper (Watch Mail); Grave-Edge (Whetstone) |
| Butcher's Cleaver | Physical | Slash | Whirlwind (Toll-Runner's Boots or Wolf-Tooth); Bonesplitter (Legion Bronze) |
| Axe Gyre | Physical | Orbit | Gyrestorm (Wolf-Tooth); Reaver's Wheel (Whetstone) |
| Iron Palms | Physical | Palm | Temple Breaker (Fen Step); Thunder Palm (Trimmed Wick or Conduit) |
| Reaving Arc | Shadow | Nova | Rend and Mend (Bitterroot or Morrow Pippins); The Harrowing (Ford Lamp or Pack-Bond) |
| Volley | Physical | Spray | Arrowfall (Grey Fletching); Predator's Volley (Night-Eyes) |
| Knifestorm | Physical | Ring | Steel Flurry (Toll-Runner's Boots); A Thousand Cuts (Whetstone) |
| Gale Chakram | Physical | Chakram | Razorgale (Whetstone); Hailwheel (The Ford's Cold) |
| Judgement Disc | Holy | Bounce | Reckoning (Crossroads Penny or Night-Eyes); Aegis Wheel (Watch Mail or Morrow Pippins) |
| Firepot | Fire | Aimed | Powder Keg (Legion Bronze); Wildfire (Emberblood or Evergreen) |
| Seeking Motes | Arcane | Aimed | Fen Lights (Second Shadow); Starseeker (Night-Eyes) |
| Moonbrand | Arcane | Aimed | Moonfall (Lampling's Scoop or Ford Lamp); Lunar Brand (Crossroads Penny) |
| Cinderfall | Fire | Aimed | Fallen Star (Ford Lamp); Living Flame (Evergreen or Emberblood) |
| Rimeshard | Frost | Aimed | Deepwinter (Trimmed Wick); Ford Ice (Grey Fletching) |
| Hoarfrost | Frost | Nova | Winter Ward (Warding Light); Absolute Zero (The Ford's Cold) |
| Arcweb | Storm | Chain | Skybreak (Night-Eyes or Conduit); Tempest Coil (Ford Lamp) |
| Thunderhead | Storm | Storm | Split Oak (Conduit); Thunderclap (Legion Bronze) |
| Umbral Bolt | Shadow | Aimed | Ruin Bolt (Legion Bronze); Soul Siphon (Bitterroot) |
| Grave Tether | Shadow | Aimed | Tether of Anguish (Wayfinder's Chart or Bitterroot); Deathcoil (Second Shadow) |
| Gravecall | Shadow | Raise | Barrow Legion (Pack-Bond); Bone Knights (Watch Mail or Morrow Pippins) |
| Dawnpulse | Holy | Nova | Circle of Dawn (Morrow Pippins or Bitterroot); Sunbreak (Legion Bronze) |
| Hallowed Ground | Holy | Zone | Sanctified Earth (Watch Mail or Warding Light); Pyre of Faith (Morning Light or Emberblood) |
| Blightfield | Shadow | Zone | Blighted Earth (The Ford's Cold or Ember-Slurry); Plaguebloom (Evergreen) |
| Thornbloom | Nature | Zone | Everbloom (Bramble Coat or Ember-Slurry); Strangleroot (The Ford's Cold) |
| Verdant Lance | Nature | Beam | Verdant Gaze (Fen Step or Ember-Slurry); Sunlance (Morning Light) |
| Spirit Herd | Nature | Herd | The Great Herd (Evergreen or Pack-Bond); The Wild Hunt (Toll-Runner's Boots) |

Each evolution's description is its rule (Grave-Edge finishes what bleeds
below a sixth; Lunar Brand throws the mark on a death); where an evolution is
more than numbers it carries its own triggers, credited to the skill.

### Why this is the answer

Branching beats destiny (R§5): a second decision on top of the recipe, and
the same skill ends two ways across runs. One passive per branch keeps the
recipe readable on the card ("Evolves: Grave-Edge with Whetstone"). Vampire
Survivors' single destiny gives less replay; Rogue: Genesia's
multi-ingredient recipes need a wiki. A minute gate (the feel study's S-10)
was measured and not needed: a build that plans gets its first evolution at
a median of seven to ten minutes (sooner at the higher tiers, where banked
skills come in higher), one that does not at seventeen to twenty; the moment
is earned and still in the run's first half, where the feel study wants it.

---

## 8. The offer

### 8.1 What a draft is

Each ember level owes a **skill draft** of three cards (`LevelUp.Draft`): a
new combat skill (while fewer than six), a rank in one carried, an evolution
or a union when earned, a new passive (while fewer than six) or a rank in
one, a hone; a heal or coin only when nothing else can be offered. **Great
blessing drafts** come at Dusk (three cards) and Midnight (four); **milestone
blessing drafts** at ember levels 5, 12, 21, 32, 45, 60.

### 8.2 Weights

A card's weight is its rarity weight times its leans times its novelty.

| Rarity | Common | Uncommon | Rare | Epic | Legendary |
|---|---|---|---|---|---|
| Weight | 10 | 6.5 | 3.6 | 1.7 | 0.7 |

| Lean | × |
|---|---|
| On the build's path (skill or blessing) | 1.5 |
| On the build's path (passive) | 1.3 |
| On the calling's paths (new skill) | 1.3 |
| Banked (carried by day) | 2.0 |
| Familiar (learned by day) | 1.3 |
| A great blessing on the path, or the calling's own | 1.5 |
| Shown in the draft just rerolled | 0.15 |
| A trap (a passive that touches nothing the build has) | 0.3 |
| Rare pity, per skill draft without a rare card | min(4, 1 + 0.3 × drafts) |

Luck raises rare weights and deals a fourth card with chance `1 − 1/Luck`
(Vampire Survivors' rule); Many Roads deals it always.

### 8.3 Guarantees

In order, each filling a card only if the draft does not already hold one,
and what a guarantee placed stays placed:

1. **An evolution earned** is always offered.
2. **A banked skill** not yet taken is among the cards in the first four
   skill drafts.
3. **A rare card** after ten skill drafts without one.
4. **A waiting evolution's passive** within two drafts.
5. **A new combat skill** while fewer than three are carried.
6. **A combat skill** in every draft.
7. **A card that ranks what you carry** once two skills are carried.

### 8.4 Surges

Any rank card may **surge**, two ranks at once, with chance
`max(0.05, 0.05 + 0.15 × (Luck − 1))`, said on the card.

### 8.5 Reroll, banish, skip, hone

| Tool | How many | What it does |
|---|---|---|
| Reroll (X) | 3, +1 a rank of the Wayfinder's Chart, +1 at each milestone, +1 from kindled gear; at most 9 held | Redraws, avoiding what was shown |
| Banish (B) | 2, +1 at Midnight's great blessing, +1 from kindled gear | Removes a card for the rest of the night, ranks included |
| Skip (V, R3) | any skill draft | Refunds 40% of the ember of the level before |
| Hone | – | +12% for a finished skill, ten times |

### 8.6 Great blessings by role

| Role | For | Great blessings |
|---|---|---|
| Power | more of what the build does | The Long Road, Ember Flood, Burn Bright, Duelist's Grace, Cinderwake, Stormborn, Spirit Companion; the callings' own (Hold the Crossing, Blood Up, Second Reading, the Hunters' Blind) |
| Ward | surviving the night | Bloodthirst, Iron Vow, Cold, Then Not, Grounding |
| Answer | felling a champion | Hunter's Mark, Rootbind, Go for the Throat |
| Quickening | tempo and economy | Restless Hands, Ember Tithe |

A great hand is **dealt by role**: a ward, a power, then an answer or a
quickening, then (Midnight's fourth card, or Omens) anything. The card says
its role ("GREAT BLESSING · WARD"). Every path lists a ward; the slow
champion-killers list an answer. **The calling's own great comes once a
night**: as Dusk's power card half the time, otherwise at Midnight.

| New great | What it does | Ranks 2, 3 |
|---|---|---|
| **Cold, Then Not** (Pyre, Dawn) | Once a night a killing blow does not kill: you go cold, then the ember catches; rise at half health and everything near burns | Rise whole, fire twice as wide; twice a night |
| **Grounding** (Storm, Weave) | A fifth of every blow is turned to lightning that leaps to three near you | A third; six, and shocked |
| **Rootbind** (Wild, Long Winter) | Every 6 s roots hold the toughest near you for a second; held, it takes 40% more | The two toughest; every 4 s |
| **Go for the Throat** (Host, Grave) | What fights for you goes for the toughest near you and strikes champions 40% harder | 20% faster; a champion felled calls a wolf for the night |
| **Hold the Crossing** (warden) | Standing still: +6 armour, weapons fire 20% faster | +10 and 25%; mend 3 a second while holding |
| **Blood Up** (reaver) | Below a third of health, blows land 40% harder and kills mend 1% | 60%; kills mend 2% |
| **Second Reading** (arcanist) | Every 8 s everything you carry fires at once | Every 6 s; every 4 s |
| **The Hunters' Blind** (stalker) | Half your blows on anything unhurt strike true | All of them; +25% critical damage |

### Why this is the answer

- **Weights and leans.** Rarity as frequency keeps a rank card a rank card;
  leans between ×1.3 and ×2 are felt over a run and not on a card (R§1). The
  banked lean is the largest because it is the day's promise to the night.
- **Guarantees, not a scripted draft.** Each answers a failure the genre is
  known for (R§10): dilution, the evolution missed, the drought. An early
  version let the last guarantee swap out an earlier one's card and the
  harness found twenty levels without a rare; the stays-placed rule and the
  rare floor fixed it, and `OfferTests` hold each promise over hundreds of
  seeded drafts.
- **Tools.** Scarce enough to be decisions, plentiful enough to be used
  (R§3). The skip refunds ember because a skip that returns nothing is used
  only by experts. Banish removes ranks too, because a banished card that
  comes back as a rank feels like a lie.
- **Great hands dealt by role.** With three random greats, a fragile path
  shown three powers had no way to survive the boss: the Pyre fell in half
  its runs at tier 2, and with Cold, Then Not taken one run in fifteen
  fell. A ward in every hand gives every survivor the choice without taking
  the choice away, and a role label is how a new player reads four
  unfamiliar cards.
- **A calling's own great.** Hades' aspects and Vampire Survivors'
  characters give a run's start an identity (R§11); here the calling already
  has its art and first skill, and its own great blessing makes the first
  choice of the night its own too, without locking any path away.

---

## 9. Slots

Six combat skills and six passives, as in Vampire Survivors and HoloCure:
thirty minutes of drafts (about fifty ember levels, plus seven blessing
drafts) fills both, takes the six skills to rank 8 and evolves three or
four. A union frees a combat slot; honing is the depth after the slots close.

### Why this is the answer

R§4: six and six matches the number of level-ups in thirty minutes. Four
slots (DRG, Megabonk) bring evolutions sooner but leave the late draft
empty; unlimited passives (Brotato) turn passives into stats. Measured: a
planning bot completes its build at about 22 to 28 minutes.

---

## 10. Day and night

| By day | What it does for the night |
|---|---|
| **Carrying** a skill (the day's slots) | **Banked**: offered in the first four skill drafts, at rank 2 (rank 3 from level 10), leaned ×2 |
| **Learning** a skill | **Familiar**: leaned ×1.3 |
| The **calling** | its paths lean new skills ×1.3; its own great blessing |
| **Gear**: the weapon and worn skills | brought in at their rank, **four at most** |
| **Gear**: statuses | lean the draft toward cards that use them |
| **Gear**: kindled affixes | section 10.1 |
| The **codex** | every evolution and union seen, with its recipe |
| The **tome** (after a night) | keep up to three of the night's skills for the day |

### 10.1 Gear and the ember: kindled affixes

From the items plan (`docs/items/SYSTEM.md` §6.4), built on the ember's
side. A kindled affix is a suffix on Rare gear and better, **one to an item,
two to a survivor** (a third does nothing), that shapes the draft without
owning it:

| Affix | In the ember |
|---|---|
| of the First Spark | the ember starts a level higher |
| of Second Thoughts | +1 reroll |
| of Refusal | +1 banish |
| of Many Roads | every skill draft shows a fourth card |
| of Omens | great blessings offer a fourth choice |
| of the Whetstone, of Rime, of the Censer, of the Wide Field, of the True Eye, of Mending, of the Ox, of the Evergreen, of the Adder, of the Pack, of the Lodestone, of Embers | counts as Whetstone, the Ford's Cold, Morning Light, Ford Lamp, Night-Eyes, Bitterroot, Legion Bronze, Evergreen, Ember-Slurry, Pack-Bond, Conduit or Emberblood **in an evolution's recipe** (the passive slot stays free); the card says "your gear stands in" |

A stand-in rolls twice as often when it stands in for what the survivor's
carried skills evolve with: the gear found by day knows the night it is for.
Gear never brings a blessing, an evolution or a rank past four
(`Inventory.GearRankCap`).

### Why this is the answer

The night must stay the night's, but the day must matter to it or the two
halves are two games (R§7). The best meta levers change the draft rather
than the numbers (R§7), so that is what crosses: banking makes the day's
skill choice a night plan; kindling makes gear a way to plan an evolution or
widen the draft; the rank cap keeps a geared survivor from starting at the
end. The items plan and this design are one rule set: the kindled affixes
are item content and the ember's rules, and the stand-in uses the draft's
own recipe check (`LevelUp.Holds`), so every place that reads a recipe (the
card, the arsenal, the catalyst pity) agrees.

---

## 11. The power curve

### 11.1 The ember's pace

`EmberNeed(n) = round(20 + 28n + 3.2n² + (n > 28 ? 8(n − 28)² : 0))`.

Measured at tier 1 (median of 144 runs):

| Minute | 1 | 2 | 3 | 5 | 10 | 15 | 20 | 25 | 30 |
|---|---|---|---|---|---|---|---|---|---|
| Ember level | 6 | 9 | 11 | 15 | 24 | 31 | 38 | 45 | 50 |
| Drafts that minute | 7 | 3 | 3 | 2 | 2 | 2 | 2 | 2 | 2 |

Cards a minute over a whole night: 1.95. `Harness/Targets.EmberByMinute`
holds this pace, so a probe at an ember level meets the horde of the minute
it is usually reached.

About six cards in the first minute (five levels and Dusk's great blessing),
then two or three a minute, under two late (R§9: between 0.5 and 3 a minute).

### 11.2 The horde, the champions, the boss

- Creatures scale by level (`Enemies.ScaleFor`: health `1 + 0.38l + 0.035l²`,
  damage `1 + 0.14l`). The arena's level is **three a tier** (`3t − 2`: 1, 4,
  7, the survivor's own pace by tier), plus a step every two and a half
  minutes, plus the oaths'. A tier also brings 15% more of the horde.
  **Dusk**: the tier's levels (and an oath's) come in over the first three
  minutes, so a night is not lost before the ember has given anything to
  choose (measured: most falls before the boss came in the first eight
  minutes, under two oaths at full strength from minute zero).
- **Ordinary creatures soften as the night goes on**: health divided by
  `1 + 0.08 × minute` (`ArenaRun.FodderEase`). A field mown below 60% of its
  number refills twice as fast, in groups twice the size.
- **Champions**: any creature may come as one (three times the health, a
  level up), more often as the minutes pass. **Heralds** at ten and twenty
  minutes carry chests. **The boss** at thirty has `10 + 4 × tier` times its
  health, with an escort.

### Why this is the answer

The feel study found the power fantasy inverted (ordinary creatures took
more blows at minute thirty than at five), and the harness agreed. Scaling
the player further breaks every other number; slowing the level curve
softens the champions that are the test. Dividing only ordinary creatures'
health by a gentle line turns the slope round while the champions stay
honest. The study proposed 0.12 a minute; the harness measured that as
one-blow kills from the third minute and no threat at all until the boss, so
the design uses 0.08.

The tier ladder was measured with competent hands at the story's pace and
the oaths the table swears: at two creature levels a tier, every tier from
one to six was won nine times in ten, so pushing higher meant nothing. At
three, a tier at the survivor's level is a fair night and each tier above it
is a real step (section 12). The boss's health was raised twice: research
places a boss at thirty to ninety seconds (R§9), and the path bots were
killing it in ten to thirty.

---

## 12. Targets, and what was measured

All measured by the harness (section 15) with the deft hands, the survivor
at the story's level for the tier (1, 4, 7), and the oaths the table
swears (none or one at tier 1, two at tiers 2 and 3).

| Measure | Target | Measured |
|---|---|---|
| Win at the survivor's tier (planning drafts: greedy, first) | tier 1 ≥ 95%, tiers 2–3 ≥ 85% | tier 1: 96%, 96%; tier 2: 96%, 94%; tier 3: 92%, 88% |
| Win drafting at random | below planning drafts, so the draft matters | tier 1 98% (tier 1 forgives any draft: not met, and meant to be gentle), tier 2 85%, tier 3 90%; random drafts take half as long again or longer over the boss (49 / 77 / 81 s against 35 / 36 / 48 s) and evolve half as often |
| A tier above the survivor's level (level 10: tier 3 is the band's top) | each tier above a real step; three above mostly lost | tier 3: 92% won; tier 4: 79% (16% fell before the boss); tier 5: 80% (18%); tier 6: 49% (41%) |
| Every path at tier 2, its own bot | ≥ 80% | 82% (the Host) to 100% (the Hunt, the Long Winter, the Storm, the Weave) |
| Boss fight, median | 30–90 s (R§9) | tier 1: 42 s, tier 2: 57 s, tier 3: 57 s; by path at tier 2: 20 s (the Hunt, the Weave) to 78 s (Dawn) |
| Herald fight, median | under the boss's | 26 / 44 / 58 s |
| Ordinary creature's time to kill, minutes 5 / 15 / 25 (tier 2) | falls through the night | 0.45 / 0.23 / 0.13 s (it rose, 0.43 / 0.69 / 0.95 s, before) |
| Champion's time to kill, minute 15 | seconds | 1.2 to 2.0 s |
| First evolution, median | earned: about ten minutes when planned | greedy 7–10 min, first 10–15, random 17–20 |
| Evolutions a night | three or four when planned | 3.6–4.2 planned, 1.8–2.0 at random |
| Build complete (six skills evolved) | the last third | 22–28 min |
| Cards a minute | 0.5–3 (R§9) | 7 in the first, then 2–3, 1.95 over the night |
| Largest share of a build's damage by one skill (mean where carried) | no skill carries the game | 21% (Judgement Disc; 39% before) |
| Largest share by one rule (probes) | ≤ 45% | 31% (Shatter, after its chain was paced) |
| Path probes at the fifteenth minute's ember (`BalanceTests`) | crowd 0.7–1.35 of the median, champion ≥ 0.25, toughness ≥ 0.55, power index ≤ 1.9 | crowd 1106–1823 (0.75–1.23), champion 177–1045, toughness 184–430: within every bound |
| Great blessings, first choice (small samples) | none a trap | 78% (Hold the Crossing, 9 runs) to 100% won |

---

## 13. Diversity and replayability

- Ten paths, four callings, two to five paths each: about thirty calling and
  path pairs, each with its own start and lean, and each calling with its own
  great blessing.
- 52 evolutions in pairs; nine unions and seventeen discoveries to find, kept
  in the codex.
- Twenty great blessings in four roles, two a night.
- Eleven oaths and four peoples change the horde.
- Measured: no path runs away (balance index within 1.9 of the median, crowd
  within 1.35), none falls short (crowd ≥ 0.7, champion ≥ 0.25, toughness ≥
  0.55), no rule carries more than 45% of a build; at tier 2 every path wins
  82% to 100% of its nights.

### Why this is the answer

R§11: the twentieth run stays fresh through different starts, rule changes
chosen at the start, conditions chosen by the player, a collection, and
branching. Each is here, and the harness checks none collapses into one
answer.

---

## 14. Decisions the items plan left open

The items plan (`docs/items/IMPLEMENTATION.md`) left five decisions to the
owner of systems. Settled here, with the reasoning.

1. **Level cap: 30** (`Character.MaxLevel`, done). Reached near the end of
   Act 3. Day skill ranks reach 8 at level 22, so the last levels are
   attributes and gear's demands; past 30 the open axes are gear and the
   arena's depth, never the character. An open level (a paragon climb)
   buries gear and the ember both (R§7; the items research's Diablo lesson):
   the night's power must stay the ember's.
2. **Skill ranks and the Edge.** Gear brings a skill in at **rank four at
   most** (`Inventory.GearRankCap`, done): the smith starts it, the ember
   finishes it. **The Edge** (a weapon's "more" damage to its kind) applies
   in full **by day**, where the day's power curve needs it, and **at night
   is capped at +25% and turned into a ×1.25 lean** toward its kind's cards.
   An uncapped Edge of up to ×2.8 at night would make one kind mandatory and
   undo the paths' balance (held within ×1.35); a lean keeps the gear's
   pull without its numbers. (For when the Edge is built: read `Battle.Night`.)
3. **Cosmetics: the survivor's armour by tier.** The figure follows the
   gear's weight and tier, by showing more of her existing pieces and a
   material-tier shader (rags, leather and mail, plate, Legion lacquer,
   Heartwrought); heavier gear covers more, as the world's tone (plain, worn,
   practical) asks. Looks are not tied to power: the tailor gives any look
   unlocked at any tier, so a player who wants her lighter or bolder keeps
   their armour's numbers. No new pieces are modelled until the tier shader
   is in.
4. **Calling bias (smart loot): 40%** of bases favour the calling's best
   attribute, as proposed. That is a ×2 lean against each other attribute,
   the same strength as the draft's strongest lean (banked skills), so the
   two halves lean alike. Affixes take no calling bias, but kindled stand-ins
   lean ×2 toward what the survivor's carried skills evolve with (done), so
   gear follows the build the player chose, not the class they started.
5. **Endgame: yes, the Depths and the echoes, after the ending.** The genre's
   long tail lives in its difficulty ladder and player-chosen conditions
   (R§11: Vampire Survivors' Hyper and Inverse, Brotato's danger, our oaths);
   the tier ladder above already makes a tier a real step, and the endless
   minutes past the half hour already exist. The story ends first, with its
   epilogue; the Depths open after, as deeper tiers with stacked oaths and the
   story's named foes as echoes. How each ending frames them is the story's
   to write (some endings may end the ember; then the Depths are nights
   remembered).

---

## 15. The harness: one balance tool

`godot/balance` plays the real `godot/logic` headless at 60 ticks a second,
with bots for hands. The balance lab's sweep (`godot/tests/BalanceLab.cs`,
`BALANCE_LAB=arena`) runs the same arenas through the same engine and
report; its day-story walk (`BALANCE_LAB=story`) is the lab's own.

- **Hands** (`Harness/Pilot.cs`): give ground when pressed, close when the
  weapons are short, collect ember when quiet, dash across a champion's
  lunge, **give ground round a champion at arm's length** (without it the bot
  stood in a boss's combo and fell, making fragile ranged builds look worse
  than they are), use the art on a crowd, drink when low. **Deft** hands
  (`--bot deft`, from the lab) also step off a lunge's line, out from under
  a lobbed pot and off burning ground, and close on throwers. **Both read the
  bosses** (`Play/Bosses/BossSense.cs`, section 16.2); `--bossread 0` gives
  the hands as they were.
- **Pickers** (`Harness/Picker.cs`): `first`, `random`, `greedy`, `path:ID`
  (or `paths`), each with a reroll, banish and skip policy.
- **Commands** (from `godot/balance`, after `dotnet build -c Release`):

      dotnet bin/Release/net8.0/Balance.dll arena --callings all --policies greedy,random,first --seeds 12 --tiers 1,2,3 --level tier --oaths table --bot deft --out out/t.jsonl --csv out/csv
      dotnet bin/Release/net8.0/Balance.dll arena --policies paths --seeds 10 --tier 2 --level tier --oaths table --bot deft --out out/paths.jsonl
      dotnet bin/Release/net8.0/Balance.dll probe --policies paths --levels 29 --seeds 4 --builds
      dotnet bin/Release/net8.0/Balance.dll weapons --seeds 4 --out out/w.md
      ARENA_TRACE="warden/path:pyre/t2/kerchiefs/s308/w1@29.9" dotnet bin/Release/net8.0/Balance.dll arena ...   (the blows of one run)

  `arena` reports win and fall rates (by policy, calling, people, tier,
  oath, level), when losses come and what was left of the boss, the ember
  pace, time to kill (fodder, champion, herald, boss), damage by source,
  card offer and take rates with the fair comparison (runs that took a card
  by minute fifteen against those that had not), evolutions and killers.
  `probe` drafts a build to an ember level and puts it through a standard
  crowd and champion. `weapons` measures every skill alone at rank 1, 4, 8
  and evolved, and every union against its halves.
- **Scripts**: `tune_weapons.py`, `tune_blend.py`, `tune_unions.py`,
  `shares.py`.

**Tests that hold the design** (`cd godot/tests && dotnet test`):

| Test file | Holds |
|---|---|
| `OfferTests` | every guarantee over hundreds of seeded drafts; leans; pity; surge; reroll avoids; banish removes ranks; skip refund; great hands by role |
| `RecipeTests` | every recipe and union reachable; every skill on a path; every passive and blessing wanted by two paths |
| `BalanceTests` | every path reaches its power; none runs away; no rule over 45% of a build's damage (six probes a path at the fifteenth minute's ember; they run alone, after the rest) |
| `BlessingTests` | great blessings deepen; each new great, each calling's own (offered to it alone, once a night) and each rider does what it says; every path has a ward |
| `KindledTests` | two kindlings at most; stand-ins at rank 8 and not before; a fourth card; a fourth great; the rank cap |
| `DecisionTests` | level thirty |

---

## 16. Enemies, bosses and the long night

The night's other half: what the survivor fights. The bestiary and the bosses
were studied by two cloud sessions (`docs/bestiary/`, `docs/bosses/`); this
section is what was built from them, and the decisions they left open.

### 16.1 The bosses

**The contract** (`Play/Bosses/ArenaBoss.cs`): three phases, each a gate that
ends at its health mark or a 60 s ceiling and never before its floor (15, 20,
15 s); damage past a mark is the **Break**, shown as one number as the phase
turns; a soft enrage at three minutes (moves a quarter quicker, the horde back
to full) and a hard one at five (its signature on a loop); crowd control fills
a **stagger bar** instead of locking it; a **weakness** school breaks its
channel. Each boss asks one question in its own people's terms:

| Boss | Its question | Its tell of soul |
|---|---|---|
| The Pack-Mother (Greymuzzle in his Hollow) | She herds you: go through the wolves, never the gap | the moon-howl that fire breaks; the last of the Pack round you |
| The Barrow Lord | Walls of men: read the formation | orders in the old empire's tongue; he will not lie down until stood over |
| The Ganger (Grimtunnel on his own night) | The ground is the enemy | one lamp for three verbs (his three, and he goes back down the hole) |
| The Red Hand | What is your build without its best piece? | the Toll takes a weapon; the thief carries it; storm makes him drop it |

**On screen** (checked frame by frame with `--on boss`, and `--marks`, a
gallery of every telegraph round the survivor):

- Each boss wears its own body (`boss_pack`, `boss_dead`, `boss_lamplings`,
  `boss_kerchiefs`): its people's champion's, half again as big, named, so it
  glows; its flash under a build's hits softened so it stays itself.
- **The telegraph language**: amber for a blow (a disc that fills to its
  moment, a lane, a cone, a band whose inside is clear), violet hatching for
  ground that stays bad, pale blue dashes for ground to stand on, a grey hard
  edge for ground that will be solid. The move's name is said over the boss
  for as long as its mark stands; the BREAK is said alone, high and gold.
- The arrival: a sign two minutes out from its bearing, the camera turned to
  it, its weakness named, and **the people make way**: the crowd past the
  share it is held at falls back into the dark and is let go out of sight.
- The stagger bar has its own groove under the health from the first second.

**Health to the contract** (90–120 s at par, about 50 s at the least for an
absurd build, an enrage for a weak one), measured with deft hands at tiers
1–3 and the table's oaths: the Pack-Mother 69 → 84 s and the Red Hand 72 →
84 s (both then raised a further tenth), the Barrow Lord 80 → 86 s, the
Ganger 92 → 98 s. Health per boss: Pack-Mother `30 + 5t`, Barrow Lord
`13 + 2.2t`, the Ganger and Grimtunnel `18 + 3t`, the Red Hand `21 + 3.5t`,
times its people's champion's.

### Why this is the answer

The cloud probe found bosses living 16–20 s and Grimtunnel kited forever;
health alone drags slow builds past two minutes while fast ones still skip
the fight. Gates with floors give every build the whole fight, show a strong
build off as a Break instead of skipping the boss, and let enrages pace a
weak one. The bodies and the language came from looking: before them the
Red Hand was the size of a footpad, the move names vanished in a frame
under the build's damage numbers, the stagger bar was clipped out of sight,
and a band's safe inside was painted as danger. **The game's boss scripts
did not run at all** (its battle copied the zone's hooks before the boss
came); the tests shared the zone's hooks and passed. A test now runs a boss
through the game's own wiring.

### 16.2 The bots read the bosses

`BossSense` is what anyone does after dying to a boss once: it steps out of
a marked blow by its shape (walking to where it will not be when the blow
lands, dashing in time when walking will not do), leaves ground about to
close, stands over the Barrow Lord, runs down the thief, closes on
Grimtunnel while a lamp flares. A relaxed player reacts in 0.45 s and misses
one marked blow in five; a practised one 0.25 s and one in twenty. The
game's `--auto` uses the same sense, so pictures show a fight fought.

| Plain hands, 192 runs | Before | Reading the bosses |
|---|---|---|
| The Barrow Lord won | 21% | 90% |
| Blows landed / marked, all bosses | 310 / 4473 | 3 / 3107 (before the misses) |
| Won (greedy / random) | 70% / 71% | 92% / 87% |

### Why this is the answer

A sweep measures the bot as much as the game. The old hands never laid the
Barrow Lord down and lost to him four times in five; they stood in every
lane. Balancing to that would have softened a fight a person wins on the
second try. One sense shared by every bot, with a human's reaction and
misses, makes the numbers the game's.

### 16.3 The long night

The owner: **"endless is truly endless - just keep ramping up till its
impossible (or not if the users get better and better and finding ways to
win haha)"**. No Dawn: past the win the night goes on until the survivor
falls or takes the way out. It climbs on three lines at once
(`Play/Zones/ArenaRun.cs`, "the long night"):

- **The horde hardens** by the minute (`ArenaRun.Hardening`): health
  `1 + 0.1m + 0.006m²`, blows `1 + 0.035m`, smoothly for the first hour past
  the half hour; from then on both compound by 3% a minute, so by two hours
  past nothing stands. A little quicker too, to a ceiling of 15% (pace a
  player can still read and outrun). No minute is a tenth harder than the
  last: a slope, never a cliff.
- **The dark swears an oath** every five minutes: one more of the table's
  oaths, named as it comes with what answers it, listed with the run's own,
  paying what it pays at the table. First the questions of where to stand
  (embers, champions, ruin, the vigil), then pace and number (the hunt, the
  swarm), last those that grind (winter, iron, blight, the deep); never the
  moonless, since the night must stay readable. Out of oaths, it deepens,
  two levels a time.
- **What rules the people comes again** every quarter hour, its sign a
  minute before: its own fight, a third more health and a quarter more bite
  each time, its chest a card richer; heralds in between.

Fair throughout: the crowd's number, its throwers and every telegraph keep
their caps; nothing kills without a mark; every new pressure is announced.

| Deft hands, tier 2, story level, table oaths (won runs) | Before | After |
|---|---|---|
| Minutes past the half hour: median (p10–p90) | 21 (9–40) | 21 (11–38), with the dark's oaths and the returns |
| Furthest | 62 | 53 (the first version, returns as walls: 39) |
| What ended them | heralds and the Kerchiefs' bruisers first, then lamplings | the horde, spread across the peoples (lamplings first); no return a wall |

### Why this is the answer

Before, the endless phase was one line: everything harder by the minute.
It killed every run (polynomials do), but the only thing that changed was
how long things took to die. The genre's best endless modes add questions
as they go (Halls of Torment's breaking Vault, Hades' heat); our oaths are
already that, each with its rule, its answers and its pay, so the dark
taking them is the world's own escalation, readable because the player has
met each one at the table. The returns give the long night set pieces and
a rhythm. The first version made the first return a wall (the night's
hardening and its levels on top of the boss's own: the sweep's runs fell to
it more than to anything) and swore the winter's crawl and iron skin early;
returns now grow by a rule a player can learn, and the oaths that grind come
last. The compounding waits an hour so the long tail belongs to great
builds and great hands; after it, nothing holds for ever, as asked.

### 16.4 The charge director

The owner: **"in our charge mechanic once quite a few overlapping constantly.
periods of that are exciting, non stop can be a little weird."** Each tusker
and lunger used to run its lane as soon as its own cooldown was up, so a thick
field became a lattice of red lanes that never stopped.

`Sim/Charges.cs` (`Battle.Charges`) decides when a non-boss creature may
start a run. Ai asks it before any wind-up.

- **Waves:** each wave lasts 5–9 s and allows `2 + tier / 2` runs at once
  (at most 4). Runs start 0.7 s apart, so each lane is read before the next.
- **Lulls:** 3–6 s between waves, with no run started.
- **Spikes:** one every 40–55 s, or every 18–26 s while the night builds into
  a landmark (`ArenaPacing.Building`). Each comes after the people's tell:
  - the Pack: a howl;
  - the dead: a drum;
  - the Lamplings: fuses;
  - the Kerchiefs: a whistle.

  The tell sounds 1.3 s ahead. Then for 3.5 s more than twice the wave's
  number may run, in a ripple 0.12 s apart, and a lull follows.
- **The night's shape:**
  - a people's own turn opens a spike;
  - breathers, the hush and a herald's duel are calm;
  - a boss allows one crowd run at a time and no spikes;
  - the long night adds one run a wave per ten minutes, up to three.
- **Refusals and exemptions:**
  - a refused creature walks on and asks again within a second;
  - champions keep a small allowance of their own;
  - bosses are never asked.
- **The same director caps the horde's other marks:**
  - 8 tunnellers under the ground;
  - 8 death bursts fusing;
  - 24 patches of the horde's burning ground, the oldest going out first.

It keeps its own random stream, so it moves no other dice.

| The Pack, tier 2, deft hands, 24 runs | Before | After |
|---|---|---|
| Charges a minute (minutes 6–30) | 123–184 | 42–59 |
| Most at once | 15–22 | 5–7 (in spikes) |
| Seconds a minute with three or more lanes | 24–31 | 7–12 |

### 16.5 Decisions the studies left open

Recorded here because this area owns them; the story's are the bible's
("The nights") and are followed.

- **Fight length**: 90–120 s at par, by gates; built (16.1).
- **Clear or thin the horde for the boss**: clear 8 m round its entrance, hold
  the rest at 40%, and make way at the arrival; full at the soft enrage.
- **A boss that takes ember takes no cards**: the bar and the level step
  back; the build stays (the Mithrix lesson).
- **The endless hour's end**: none (the owner); 16.3.
- **Grimtunnel never dies in an arena** (the bible): he goes back down the
  hole, delighted; a table's Lamplings field **the Ganger**, never him or his
  name.
- **Keegan's duel at first light** (the bible): a day fight without ember;
  not an arena, so not built here.
- **New outcomes from fights**: **Greymuzzle let go** is built narrowly, as
  the bible has it: only if she knelt and promised and the stream already
  runs clean, he goes down, gets up and goes to his sick (`greymuzzle` =
  `spared`, Maeca's regard up; the story lead owns the words). The crates,
  the pump and Edric use values that already exist, when their fights do.
- **Banes**: learned by day, recorded once seen, never hidden for good; the
  weakness is named on arrival.
- **The Silver Penitent**: yes, last, behind a flag (not started).
- **Oaths on bosses**: lightly, one visible change each (the iron oath
  halves the stagger bar's filling: `MapRules.StaggerTaken`); the horde
  carries the rest. Not yet built.
- **Enemy hazards hurt the horde** at half, the horde's own hazards only, not
  an oath's ground: not yet built.
- **Signs**: none at tier 1 before minute ten, one at tiers 1–3, two from
  tier 4, three on late heralds: not yet built.
- **Contested ground** (two peoples at war): from Act 2, as the bible has it,
  and a candidate for the long night's deeper hours.
- **Thieves**: ember stones on the ground only, never what is held; a
  carrier, in the lamplings' words. The Red Hand's Toll is a boss's verb, and
  recoverable.
- **Weight as a number** beside the words, for planners: yes, not yet built.
- **Mirror Step** stays strong against the crowd; champions and bosses see
  through it (built).
- **The Lamplings' champion** is the digger until the Blasting-Cart has art.
- **An oath's ember**: every oath that promised more ember paid none (the dead
  left the same stones under any oath); `MapRules.EmberGain` pays it now.

---

## 17. Before and after

"Before" is the game as this work found it, measured by the harness's first
bot (plain hands, level 1, no oaths); "after" is the finished design. The
last rows are the same measure, before and after.

| | Before | After |
|---|---|---|
| Tier 1 won (first / greedy / random), plain hands, level 1, no oaths | 94% / 88% / 91% | 92% / 94% / 96% (against a boss with half again the health, the hands now giving ground to it) |
| Tier 2 won (greedy / random), plain hands, level 1, no oaths | 88% / 71% | 94% / 92% (a tier is now three creature levels, not two) |
| Tier 2 at the story's level and the table's oaths, deft hands (greedy / random) | not measurable (no oaths, no levels, no deft hands in the harness) | 96% / 85% |
| A tier above the survivor's (deft, level 10, table oaths: tiers 4, 5, 6) | 86%, 81%, 62% before the ladder changed | 79%, 80%, 49% |
| Paths at tier 2, their own bot | 58% (the Wild) to 100% | 82% to 100% |
| Path probes: crowd spread / champion spread | ×2.0 / ×6.9 (level 35) | ×1.65 / ×5.9 (the fifteenth minute's ember), every path inside the bounds |
| One skill's mean share of the builds that carry it | 39% (Judgement Disc) | 21% |
| Ember at minutes 1 / 15 / 30 | 7 / 37 / 53 | 6 / 31 / 50 |
| Ordinary creature's time to kill at minutes 5 / 15 / 25, tier 2 | 0.43 / 0.69 / 0.95 s (rising) | 0.45 / 0.23 / 0.13 s (falling) |
| Boss fight | not measured; bots killed it in 10–30 s once measured | 42–57 s by tier |
| Great blessings | 12, random hands | 20 in four roles, hands dealt by role, a calling's own once a night |
| Passives | stat names (Might, Haste, Precision...) | 25 things of the valley, most with a rule of their own |
| Day to night | the weapon only | banked skills, familiar skills, the calling's paths, kindled gear, the codex, the tome |
| Rare drought in the draft | up to twenty levels | at most ten |
| Boss scripts in the game | none ran (hooks copied before the boss came) | all four, and Grimtunnel's and Greymuzzle's nights |
| Boss fight, deft hands, tiers 1–3 (Pack / Barrow / Ganger / Red Hand) | 69 / 80 / 92 / 72 s | 84 / 86 / 98 / 84 s, then the Pack and the Red Hand a tenth more |
| The Barrow Lord won, plain hands | 21% (never laid down) | 90% (the hands read the bosses) |
| The long night (deft, tier 2): minutes past the half hour, median (p10–p90), furthest | 21 (9–40), 62; one line of hardening | 21 (11–38), 53; the dark's oaths, returns, heralds |
| An oath's ember | never paid | paid (`MapRules.EmberGain`) |

---

## 18. Open

- **The middle of the night is safe.** Lowest health is about 90% from minute
  ten to the boss; the threat is champions, heralds and the boss. The feel
  study's floods and breathers (S-12) would put pressure back mid-run, and
  its boss ceremony (S-11) would make the boss the peak; both are arena
  pacing beyond the spawner that keeps up, and are not built.
- **The boss-killers kill the boss fast.** The Hunt and the Weave fell the
  tier-2 boss in about 20 s, under research's 30 s. That is their identity;
  if the boss is to be the peak for them too, give it a phase (S-11), not
  more health (which would drag Dawn and the Wild past 90 s).
- **Most falls at tier 3 come before minute fifteen**, even with Dusk. A
  softer first quarter hour at the higher tiers is the next lever if
  playtests agree.
- **The Edge is not built.** When it is, apply section 14's night cap and
  lean (`Battle.Night`).
- **Icons.** The new great blessings and the callings' own reuse existing
  glyphs (embers, static, thorn, howl, aegis, drain, arcane, mark); they
  should have their own in the UI art manifest.
- **Small samples.** The callings' own greats were first choices in 9 runs
  each; a dedicated sweep (each calling, many seeds) should confirm them.
  Cinderwake and Burn Bright have each sat lowest in one sweep or another:
  watch them.
- **The Grave's crowd** is the lowest in the probes (0.75 of the median),
  though it wins 92% of its arenas; a small lift to Umbral Bolt is the
  obvious one.
- **Probes and arenas measure crowds differently**: the probe's crowd is the
  level's full strength (a yardstick that does not saturate), the arena's is
  softened by the minute.
- **The day story's balance** (the balance lab's walk of the Verge) was not
  part of this work.
