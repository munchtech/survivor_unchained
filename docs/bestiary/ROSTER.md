# Roster: the peoples and their creatures

Every creature that holds an arena today, what it does and how dangerous it
is in practice, then what each people lacks and proposals to fill it. Every
proposal is written in the units `EnemyDef` already uses (level-1 values;
`Enemies.ScaleFor` raises health and damage with level) and says which
existing spec builds it, so `IMPLEMENTATION.md` can size it. Roles are those
of `ROLES.md`.

**How to read "in practice".** The numbers come from the probe
(`probe/RESULTS.md`): a level-4 warden body (170 health, 5 armour) with one
skill at rank 4, the deft bot, against a steady group of one kind at
creature level 5 (about minute 10 of a tier 2 arena) for 150 s. "Kills" is
kills a minute; "hurt" is damage taken as a percentage of 170 health a
minute (100 means a full health bar a minute: a warden with no healing would
fall in about a minute). Medians across the fourteen single-skill loadouts,
with the best and worst. Elites were measured one at a time with the bot
standing its ground (it does not kite a lone elite), so their "hurt" is the
cost of trading blows, not of a well-played fight.

## The arena's rules that every creature lives under

| Rule | Where | Value |
|---|---|---|
| Creature level | `ArenaRun.Level` | `tier × 2 − 1 + minute / 2.5` (+2 under the deep dark); past the half hour another level every 2 minutes, and health and damage climb by the minute on top |
| Health and damage by level | `Enemies.ScaleFor` | health `1 + 0.38 l + 0.035 l²`, damage `1 + 0.14 l` (l = level − 1). Level 13 (tier 1, minute 30): ×10.6 health, ×2.7 damage |
| How many at once | `ArenaRun.Target` | `(22 + 7.5 × minute) × pack size × (1 + 0.12 × (tier − 1))`, at most 320 (380 after the win) |
| Shooters and throwers at once | `ArenaRun.RangedCap` | `5 + minute / 3`, at most 16 (24 after the win) |
| Kinds join | `Denizens.Arena` | each kind has a minute it joins from; older kinds weigh more (`weight × (1 + (minute − from) / 8)`) |
| Champions | `ArenaRun.Group`, `Event` | 1.2% of any group's members (× the oath of champions, × (1 + minute / 12)); an escorted champion every fourth event, ×2 health again, with a chest |
| Heralds | `ArenaRun.Herald` | the people's champion kind at 10 and 20 minutes (every 5 after the win), ×(4 + tier) health (×1.6 at 20), ×1.2 damage, a chest |
| Grace after a blow | `Battle.HurtPlayerRaw` | 0.45 s, so at most ~2.2 blows a second land |

---

## The Pack

Wolves made sick by the Dig's slurry, and the boars of the Verge that run
with them (`STORY_BIBLE.md`: the Pack). Their question is **every side at
once**: they are fast, they surround, and their danger is arrival.

### Today

| Creature | Role | Joins | Health · Speed · Damage | Verbs | Kills · hurt (deft) | Best answered by | Worst against |
|---|---|---|---|---|---|---|---|
| Longtooth Wolf `wolf` | swarmer | 0 | 30 · 5.3 · 9, every 0.9 s | `Pack`: fans to a 4 m slot, then closes | 90 · 42 | Axe Gyre (154 kills), Blightfield, Dawnpulse (hurt 24) | Knifestorm, Verdant Lance (~50 kills) |
| Thicket Tusker `boar` | charger | 4 | 44 · 3.2 · 12, mass 2.5 | `Charge` 10 m, 0.9 s wind-up, 13 m/s; a tree stuns it | 26 · 44 | Motes, Arcweb; Rimeshard (hurt 24) | blades (hurt 76): melee stands in the lane |
| Blight-Sick Wolf `wolf_blighted` | exploder | 9 | 38 · 4.4 · 10 | `Burst` 2.4 m poison, 0.5 s fuse | 55 · 63 | Axe Gyre, Motes | Verdant Lance, Knifestorm |
| Greymuzzle `wolf_alpha` | champion, herald | – | 520 · 5.4 · 18, every 0.8 s, mass 5 | `Pack` + `Lunge` 9 m, 0.6 s wind-up | ~7 s with Gyre, ~23 s with a blade · hurt 180–400 | Rimeshard (freeze halves the hurt), Mirror Step | the slow single-target loadouts |

**Reading.** The Pack is the most even people: nothing it fields blocks a
whole kind of build, and its fodder is fast enough that area left behind
(fields, gyres) does most of the killing. Its danger is the wolves' 0.9 s
bite and the champion's lunge. Wolves resist nature by 20% and take 25% more
fire (`Enemies.Beast`), so fire is the Pack's soft counter and nature its
soft weakness for the survivor; both are mild.

**What it lacks.** Area denial (nothing makes the ground dangerous), an
orbiter (the obvious beast for it), and anything that rewards a priority
kill. The Pack-Mother, its herald and its escorted champion are all the same
creature, Greymuzzle (the boss session is looking at the first).

### Proposals

| Creature | Role | Health · Speed · Damage · Radius | Verbs, in today's specs | Telegraph and read | Lore |
|---|---|---|---|---|---|
| **Ridge-Runner** `wolf_runner` | orbiter, charger | 26 · 5.6 · 8 · 0.45; every 0.9 s | `Behavior.Orbit` (holds 6 m and circles) + `Lunge` (7 m, cooldown 5, wind-up 0.7, 0.35 s at 16 m/s). **Data only**: the lunge code runs before the behaviour switch, so any behaviour can lunge. | A lean, pale yearling, tail high; a yip as it plants. The lunge's red lane as today. | The young of the Pack run the ring while the old ones close. |
| **Slurry Sow** `boar_slurry` | area denial, heavy | 70 · 2.6 · 12 · 0.65; mass 3 | `Behavior.Chase` + `Trail` (every 0.6 s, 1.2 m, 3 s, 25% of its damage a second, nature). **Data only**: `TrailSpec` is written and unused. | A bloated sow with green-lit flanks; the trail glows the Dig's green (`zone_venom`). | A sow that drank at the Dig's outflow and carries it. The slurry is the Pack's sickness made visible (`STORY_BIBLE.md`). |
| **Old Howler** `wolf_howler` | buffer | 60 · 4.0 · 8 · 0.55 | Keeps 8 m back (`Behavior.Ranged` with no `Ranged` spec keeps distance) + **new** `AuraSpec` pulse: every 8 s, wolves within 8 m run 25% faster for 4 s. | Stops, lifts its head and howls (1 s); a ring of the Pack's grey on the ground; the hastened wolves' eyes glow. | The pack's caller. Kill it and the hunt loses its voice. |
| **Carrion Crows** `crow` | flyer, fodder | 8 · 6.0 · 4 · 0.3; in flocks of six | `Behavior.Orbit` + **new** `Flies` flag (ignores walls, cover and the flow field). | Black, small, a beat of wings; never more than two flocks at once. | Crows follow wolves; they eat what the Pack leaves. |

**Champion and herald.** Keep Greymuzzle as the herald (he is the story's).
Make the escorted champion the Pack's *strongest kind in the field* with a
Sign (`COUNTERS.md` §4) rather than another Greymuzzle, so the Pack's
champions vary.

**The Pack's arena, proposed.** `[(wolf 5, 0), (wolf_runner 2, 3),
(boar 2, 5), (crow 1.5, 8), (wolf_blighted 3, 10), (boar_slurry 1.5, 14),
(wolf_howler 0.4, 18)]`.

---

## The Risen

The dead of the Low Ford, raised by the ember in them (`STORY_BIBLE.md`:
the risen). Their question is **what do you kill first?**: they are slow,
they come in ranks, and they bring the game's guard, its archer and its
raiser together.

### Today

| Creature | Role | Joins | Health · Speed · Damage | Verbs | Kills · hurt (deft) | Best answered by | Worst against |
|---|---|---|---|---|---|---|---|
| Risen `risen` | fodder | 0 | 20 · 2.7 · 8 | `Chase`; rises helpless for 1.1 s | 73 · 28 | Motes (106), Arcweb; Hallowed Ground (hurt 4) | blades (~42) |
| Risen Bowman `risen_archer` | ranged | 3 | 22 · 2.5 · 7 | `Ranged` 9 m, every 2.8 s, bolt 11 m/s; strafes | 32 · 93 | Motes, Arcweb | the self-centred area (Dawnpulse, Hallowed Ground: **0 kills with the plain bot**) and blades |
| Risen Shieldman `risen_warrior` | guard | 7 | 46 · 2.4 · 11, mass 1.6 | `Guard` 1.4 rad, 75% off projectiles from the front | 26 · 14 | Arcweb, Hallowed Ground, Dawnpulse, Gyre (~38) | Knifestorm (4), Rimeshard (10), Volley (13) |
| Grave-Caller `grave_caller` | raiser, caster | 13 | 34 · 2.2 · 9 | `Caster`: frost orb (10 m, every 3.4 s, slows 0.6 for 1.4 s) + `Raise` (every 7 s, 2 risen within 7 m, 1.5 s cast) | (with risen) 70 · 44 | Motes, Arcweb | blades, Blightfield (hurt 67) |
| Barrow Knight `barrow_knight` | champion, herald | – | 420 · 2.6 · 22, every 1.1 s, mass 5 | `Chase` + `Lunge` 8 m, 0.75 s wind-up, 17 m/s | ~5 s with Dawnpulse, ~25 s with Rimeshard · hurt 85–440 | Dawnpulse (holy: the dead take 50% more), Rimeshard (hurt 84) | blades (hurt 437) |

**Reading.** The Risen are the people whose answers vary most by build, and
that is their character. The shieldman nearly stops projectile builds
(Knifestorm kills four a minute against Arcweb's 38); the bowmen stop the
self-centred area builds unless the survivor walks out to them; holy and
fire soft-counter all of them (`Enemies.Undead`: holy −50%, fire −15%,
frost +25%, shadow +35%). The **mix of shieldmen in front of bowmen** (the
"ford" mix) is the worst pairing the probe found for a single-school build:
hurt 84 for a median loadout, 58–95 across all of them.

**What it lacks.** A splitter (the dead are the natural one), a buffer (the
ford's lamps are in the story already), and area denial.

### Proposals

| Creature | Role | Health · Speed · Damage · Radius | Verbs, in today's specs | Telegraph and read | Lore |
|---|---|---|---|---|---|
| **Bone-Heap** `bone_heap` | splitter, heavy | 70 · 2.0 · 12 · 0.75; mass 2.5 | `Chase` + `Split` (into 3 `risen`). **Data only**: `SplitSpec` and `KillEnemy`'s split are written. Young must not split again (they are risen). | A mound of several dead moving as one; bones fall from it as it is hit; it comes apart into three. | The ford's dead were buried together, and they get up together. |
| **Ford-Lamp** `ford_lamp` | buffer (stationary) | 60 · 0 · 0 · 0.5; family Construct | `Behavior.Stationary` + **new** `AuraSpec` ward: the dead within 6 m take 40% less from everything. | A lit iron lamp on a post, blue-white; a ring of its light on the ground; the warded dead shine at the edges. Dies with a hiss and the ring goes out. | The lamps of the crossing fed the Ford-Warden (its note in `Enemies.cs`). The dead still gather to them. |
| **Drowned** `drowned` | area denial | 50 · 2.0 · 10 · 0.55 | `Chase` + `Trail` (every 0.8 s, 1.3 m, 3.5 s, 20%, frost) and **small new**: a trail's ground chills (a `Slow` on enemy ground zones; `GroundZone.Slow` exists for the survivor's own). | Wet, weed-hung, leaves pale frost where it walks. | The Low Ford keeps what it drowns. |
| **Bell-Ringer** `risen_bell` | buffer | 40 · 2.2 · 6 · 0.5 | `Behavior.Caster` without a missile + **new** `AuraSpec` pulse: every 10 s the dead within 9 m rise faster (the 1.1 s rising halved) and move 20% faster for 4 s. | A risen with a hand-bell; you hear it before you see it. | The Watch rang the ford bell at dusk. One of them still does. |

**Champion and herald.** The barrow knight is right for the role. The
probe's one warning: with a slow single-target build a lone knight trades
blows at 4× a health bar a minute, so it must stay a *kiting* fight (it is
slower than the survivor: 2.6 against 5) and never be given the oath of the
hunt's speed and a Swift Sign at once (see `HORDES.md`, forbidden pairs).

**The Risen's arena, proposed.** `[(risen 5, 0), (risen_archer 2, 3),
(risen_bell 0.4, 5), (risen_warrior 3, 7), (bone_heap 1.5, 10),
(grave_caller 0.6, 13), (drowned 1.2, 16), (ford_lamp 0.25, 20)]`.

---

## The Lamplings

The empire's lamp-tenders gone feral, digging toward the light
(`STORY_BIBLE.md`: the Dig). Their question is **watch the ground**: they
come up beside you, and their throwers burn where you stand. They are also
the thinnest people: two kinds.

### Today

| Creature | Role | Joins | Health · Speed · Damage | Verbs | Kills · hurt (deft) | Best answered by | Worst against |
|---|---|---|---|---|---|---|---|
| Lampling Tunneler `lampling` | burrower, fodder | 0 | 16 · 3.6 · 7 | `Tunneler`: under when more than 6 m off, up within 2.4 m with a 0.55 s ring, 1.2× blow | 106 · 10 | Axe Gyre (280: they surface into it), Motes | blades and Knifestorm still kill ~45; nothing struggles |
| Lampling Sapper `lampling_sapper` | lobber, exploder | 5 | 24 · 2.9 · 8 | `Ranged.Lob` firepot (8 m, every 4.4 s, 1.6 m ground for 3 s) + `Burst` 2.2 m, 1.2×, 0.6 s fuse, burns | 26 · 66 | Motes (83), Arcweb, Blightfield (hurt 51) | blades: a deft player who stays off the burning ground kills **2–4 a minute** with a cleaver |
| Grimtunnel, Roused `grimtunnel_roused` | boss (and champion stand-in) | – | 460 · 3.3 · 16 | `Chase` + firepot lob 11 m | ~7–31 s · hurt 190–295 | Rimeshard, Gyre | Cinderfall (fire: he resists 50%) |

**Reading.** The tunneler is the easiest creature in the game (hurt 10 a
minute); it is fodder that teaches the ground. The sapper is the hardest
rank-and-file creature for melee: it stays at range, burns where the
survivor must stand to reach it, and bursts when it dies. Lamplings resist
fire (30% and 50%) and take 30% more from frost.

**Two problems.** The people's **champion and herald is the sapper**
(`Denizens.Champion = "lampling_sapper"`), so the herald at minute 10 is a
thrower with ×6 health that keeps its distance and strafes: the kiting
enemy the genre's players name as tedium (`RESEARCH.md`, themes). And with
two kinds the Lamplings ask two questions for thirty minutes.

### Proposals

| Creature | Role | Health · Speed · Damage · Radius | Verbs, in today's specs | Telegraph and read | Lore |
|---|---|---|---|---|---|
| **Wick** `lampling_wick` | swarmer | 10 · 4.6 · 5 · 0.32 | `Behavior.Pack`. **Data only.** | Small, quick, a candle-stub on the head that streaks as it runs. | The youngest of the Dig. Sent up first, because they run fastest. |
| **Blasting-Cart** `blast_cart` | charger, exploder, the new champion | 90 · 2.4 · 14 · 0.75; mass 4 | `Charge` (10 m, cooldown 6, wind-up 1.1, 1.2 s at 11 m/s) + `Burst` (2.8 m, 1.5×, 0.8 s fuse, fire, burns). **Data only**; a cart that hits a tree is stunned like a tusker. | Two lamplings shoving a cart stencilled "B.E."; the fuse spits as it winds up; the lane in red. | Coyle's blasting ember, carried up the Kerchiefs' road (`STORY_BIBLE.md`: the Coyle Company). |
| **Lamp-Pole** `lamp_pole` | emplacement (ranged, stationary) | 80 · 0 · 7 · 0.5; family Construct | `Behavior.Stationary` + `Ranged` (10 m, every 3.2 s, 9 m/s, fire, `Count = 3`, `Spread = 0.3`). **Data only**: `Count` and `Spread` are written and unused. Counts against the ranged cap. | A pole of three lit lamps, turning to face you. | The Dig lights its tunnels on poles; they bring them up with them. |
| **Glimmer-Thief** `lampling_thief` | thief | 30 · 5.2 · 0 · 0.38 | **New** `Behavior.Flee` and a `Steal` verb: runs to the nearest ember stones on the ground and swallows them (up to 20), then flees and burrows away after 20 s; killed, it gives them back ×1.5 with gold. | Glows brighter with each stone; a chiming laugh; a gold outline from across the arena. | Lamplings dig toward light the way moths fly at it (`lampling`'s note). Ember stones are light. |

**Champion and herald.** Make the **Blasting-Cart** the Lamplings'
champion and herald (melee, charges, explodes when it dies: a fight to
read, not a thrower to chase). The roused Grimtunnel stays the boss.

**The Lamplings' arena, proposed.** `[(lampling 5, 0), (lampling_wick 3, 2),
(lampling_sapper 2.5, 5), (lampling_thief 0.15, 6), (lamp_pole 0.3, 9),
(blast_cart 1, 12)]`.

---

## The Kerchiefs

What is left of Ashford's levy and its families, robbing the road to feed
forty-one mouths (`STORY_BIBLE.md`: the Kerchiefs). Their question is **can
you get round?**: a shield wall with throwers behind it.

### Today

| Creature | Role | Joins | Health · Speed · Damage | Verbs | Kills · hurt (deft) | Best answered by | Worst against |
|---|---|---|---|---|---|---|---|
| Kerchief Footpad `footpad` | fodder | 0 | 36 · 4.2 · 10 | `Chase` (fast) | 69 · 59 | Axe Gyre, Blightfield | Knifestorm, Verdant Lance |
| Kerchief Pillager `pillager` | lobber | 4 | 30 · 3.4 · 9 | `Ranged.Lob` firepot (9 m, every 4.2 s, 1.7 m ground for 3.5 s) | 19 · 73 | Arcweb (58), Motes | blades and Hallowed Ground: **1 a minute** for a deft player |
| Kerchief Bruiser `bruiser` | guard, heavy | 9 | 90 · 3.0 · 15, mass 3 | `Guard` 1.6 rad, 80% off projectiles | 14 · 43 | Blightfield (35), Arcweb, Gyre | Knifestorm (**0**), Rimeshard (6), Volley (6) |
| Kerchief Enforcer `enforcer` | champion, herald | – | 480 · 3.4 · 22, mass 5 | `Chase` + `Lunge` 8.5 m, 0.7 s | ~6–21 s · hurt 140–500 | Rimeshard, Mirror Step | blades |

**Reading.** The Kerchiefs are the hardest people today for single-school
builds and the hardest of all for projectile builds: the probe's
**shield-wall mix** (bruisers in front of pillagers) hurt a warden 160% a
minute for the median loadout, three times the Pack's hunt. The champion
bruiser (×3 health behind an 80% guard) took **56 s** to kill with Volley,
**91 s** with Knifestorm and 99 s with Rimeshard: a single creature a
relaxed projectile player cannot finish in the time it takes to walk past.
That is the one place in the roster where a counter is closer to a wall
than a slope (`COUNTERS.md` §2 proposes the fix).

The Kerchiefs have no resistances (`Enemies.Kerchief` is empty): their
counter-play is all positional.

### Proposals

| Creature | Role | Health · Speed · Damage · Radius | Verbs, in today's specs | Telegraph and read | Lore |
|---|---|---|---|---|---|
| **Levy Crossbow** `levy_crossbow` | ranged (volley) | 28 · 3.0 · 7 · 0.48 | `Behavior.Ranged` + `Ranged` (10 m, every 3.6 s, 12 m/s, physical, `Count = 3`, `Spread = 0.22`). **Data only.** | A red-capped crossbowman who kneels to shoot (0.4 s); three bolts in a fan, gaps between them wide enough to stand in. | Ashford's levy kept its crossbows when it lost everything else. |
| **Goodwife** `kerchief_goodwife` | healer | 32 · 2.8 · 6 · 0.45 | `Behavior.Caster` + **new** `MendSpec`: every 6 s, a 1.2 s cast (interruptible, like `Raise`), then three wounded Kerchiefs within 7 m mend 15% of their health. Never herself. | A woman in an apron with a satchel; a green ring as she casts; "Hold still". | She patched them up after Ashford and has not stopped since. |
| **Levy Drummer** `kerchief_drummer` | buffer | 45 · 2.6 · 6 · 0.5 | Keeps back (`Behavior.Ranged`, no missile) + **new** `AuraSpec`: Kerchiefs within 8 m are 20% faster and strike 15% more often. | A drum on a strap and a red banner on a pole; the drumbeat is heard across the arena and stops when it dies. | The levy marched to a drum. They still do, to rob a wagon. |
| **Cutpurse** `cutpurse` | thief (gold) | 30 · 5.4 · 4 · 0.45 | **New** `Flee` + `Steal`: a blow that lands on the survivor takes gold (never ember or items) and it runs; killed within 20 s, it drops what it took twice over. | Small, fast, bag on the back; a gold glint and a jeer. | The Kerchiefs rob the living second; this one never got the order right. |

**Champion and herald.** The enforcer is right. A Kerchief champion should
never be a bruiser *and* bear the Shielded Sign (forbidden pair).

**The Kerchiefs' arena, proposed.** `[(footpad 5, 0), (pillager 2.5, 4),
(cutpurse 0.2, 5), (levy_crossbow 1.5, 7), (bruiser 2, 9),
(kerchief_goodwife 0.4, 12), (kerchief_drummer 0.3, 16)]`.

---

## Contested ground: two peoples at war

`Battle.DefaultWar` already sets the Pack at war with the Kerchiefs, the
Lamplings and the dead, and the dead with everyone. Rival creatures fight
each other (`Ai.Strike`: real damage, no credit, and it draws attention), and
a creature killed by a rival still drops its ember. So an arena held by
**two peoples at once** is mostly data: a `Denizens` whose arena list draws
from both, spawned on opposite sides.

This is the sweatiest opt-in in the document and almost free: a player who
reads it pulls the wolves into the Kerchiefs' shield wall and lets them
fight. A relaxed player sees a busier arena that is, if anything, easier
(half the horde is busy). Propose it as a table offer from tier 3
("Contested: the Pack and the Kerchiefs"), with a rule that a contested
arena's boss is the stronger people's, and gear that leans to both banes.

## Later peoples

The second and third acts bring new peoples (`STORY_BIBLE.md`: the Fevered,
the Vigil's knights, the Legion's dead below). Whatever they are, the
taxonomy says what each should bring that the first four do not, so the
roster grows by questions, not only by skins:

| People (act) | Roles to lead with | The question it should add |
|---|---|---|
| the Fevered (2) | healers turned plague-spreaders, exploders, area denial | "Can you fight where you cannot heal?" (a people-shaped oath of the blight) |
| the Vigil (2) | guards in formation, chargers, a holy caster | "Can you break a line?" Holy-resistant, so the warden's holy loses its edge against them |
| the Legion's dead (3) | armoured phalanx, splitters, a buffer standard | "Do you have weight?" High armour, the iron oath as their nature |

---

## Tuning notes on today's creatures

Small changes the probe suggests, independent of the proposals:

1. **Lamplings' champion and herald → a melee creature** (the Blasting-Cart,
   or until it exists the tunneler as champion). A thrower herald with ×6
   health is a chase.
2. **Champion guards: 60% instead of 80% off projectiles.** A champion
   bruiser is the one creature a relaxed projectile build cannot finish in a
   minute; at 60% the Volley's time to kill falls to about 30 s, still a clear
   lesson in flanking.
3. **Grave-Caller: raised risen give no ember.** Raising is then pure cost,
   never a farm (it is not a farm today only because the caller is rare).
4. **Sapper's burst: 1.0× instead of 1.2× damage**, and its firepot every
   5 s. Melee builds today take two to four times the probe's median hurt
   from sappers; the burst after a fight won at range is the sting.
5. **Bowman: keep.** It is the reason a Dawnpulse player has to walk; the
   deft bot that does walk kills them as fast as anyone.
6. **Wolves: keep.** The Pack is the best-balanced people.
