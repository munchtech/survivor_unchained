# Roles: what each kind of creature asks

A role is a question the horde puts to the survivor. Two hundred creatures
that all ask "can you outrun me?" are one creature two hundred times; the
comment at the head of `godot/logic/Content/Enemies.cs` already says so, and
this file takes it further. Each role below says what it asks, how the
relaxed player survives it with no special effort, how the sweaty player
turns it to their advantage, and what the engine already has to build it.

The rule that runs through all of it: **every role must be survivable by
moving and letting the build work, and exploitable by reading it.** A role
that only a counter-pick can survive is a build check, and build checks in a
game where the build is drafted at random are traps (`RESEARCH.md`, "build
checks and skill checks").

## The one number that shapes every role

`Battle.HurtPlayerRaw` gives the survivor 0.45 s of grace after every blow
that lands ("the Survivors contract"). However many creatures touch them, at
most about **2.2 blows a second** get through. Two things follow, and they
decide which roles are dangerous:

1. **A crowd's danger is the size of its biggest blow, not its numbers.**
   Fourteen risen hitting for 8 deal no more than one risen hitting for 8,
   2.2 times a second. A barrow knight's lunge (22 × 1.5 = 33 at level 1) is
   worth four risen blows in the same window.
2. **Fodder is harmless alone and deadly only as a wall.** The crowd kills by
   blocking, not by biting: it closes the ways out, so the big blows (lunges,
   pots, bursts) cannot be stepped away from.

So the dangerous roles are the ones that deliver **big single blows**
(chargers, exploders, lobbers, elites) and the ones that **take away
movement** (walls of fodder, slows, area denial, orbiters). The probe agrees
(`probe/RESULTS.md`): fourteen risen cost a warden about 20–30% of their
health a minute; one barrow knight at the same level costs 150–450%.

## The roles at a glance

| Role | It asks | Today | Engine verbs | Simple player survives by | Sweaty player exploits by |
|---|---|---|---|---|---|
| Fodder | "Can you keep up?" | risen, lampling, footpad | `Chase` | letting the weapons mow | herding it into a ball for area to eat |
| Swarmer | "Can you hold every side?" | wolf (`Pack`) | `Pack` slots | moving in one direction | turning on the pack as it closes |
| Charger | "Are you on the line?" | boar (`Charge`), elites (`Lunge`) | `LungeSpec`, telegraph lane | stepping sideways when the red lane shows | baiting charges into trees (stun + 12% health) |
| Ranged | "Will you come to me?" | risen bowman | `Ranged`, strafe | out-healing chip damage | diving the shooters; Bulwark turns bolts back |
| Lobber (area denial) | "Can you keep moving?" | pillager, sapper | `Ranged.Lob`, `GroundSpec` | never standing still | herding the horde onto its own fire |
| Guard | "Can you get round?" | shieldman, bruiser | `Guard` arc | area and melee skills ignore it | flanking, freezing or stunning to open it |
| Summoner / raiser | "Will you kill the source?" | grave-caller | `RaiseSpec`, cast ring | out-damaging the stream | interrupting the cast, burning graves out of reach |
| Splitter | "Can you finish what you start?" | none yet | `SplitSpec` | area eats the young | killing it where the young land in fire |
| Burrower | "Do you watch the ground?" | lampling tunneler | `Tunneler`, surfacing ring | moving away from rings | standing on the ring with a nova primed |
| Aura / buffer | "Who do you kill first?" | none yet | (new: `AuraSpec`) | ignoring it (soft) | sniping the carrier; the escort routs |
| Healer / mender | "Can you burst?" | none yet | (new: `MendSpec`) | out-damaging the mend | killing the mender, or interrupting it |
| Exploder | "Are you too close when it dies?" | blight-sick wolf, sapper | `BurstSpec` fuse ring | ranged weapons kill it away | dragging it into the crowd before it dies |
| Flyer / orbiter | "Can you stop circling?" | none yet | `Orbit` (unused) | out-ranging it with homing | cutting across its ring |
| Armoured / heavy | "Do you have weight?" | bruiser (mass 3), elites | `Mass`, `Resists` | slower kill, but no special danger | crits, marks, statuses, the iron oath's answer |
| Thief / fleer | "Will you give chase?" | none yet | `Flee` (unused) | ignoring it, losing nothing | the chase pays a purse |
| Champion / herald | "Can you do two things at once?" | any, ×3 health; heralds ×(4+tier) | `Elite`, chest | a long fight, kited | the Sign it bears, read and answered |

The rest of this file takes each in turn.

---

## Fodder

**It asks:** keep killing. **Today:** risen (20 health, 2.7 speed, 8 damage),
lampling tunneler (16, 3.6, 7), footpad (36, 4.2, 10).

Fodder is the ember: it is what is killed for ember stones and what makes
the build feel strong. It must die fast, and faster as the night goes on
(the feel audit measured the opposite: ordinary creatures take ~1.5 blows at
minute 5 and ~4 at minute 30, `docs/feel/AUDIT.md` §9; its S-01 fix should
land before anything here is tuned).

- **Simple:** moves and lets the weapons work. Fodder's blows are the
  smallest in the game, and the grace window caps them.
- **Sweaty:** herds it. Walking a slow arc pulls fodder into a tight ball
  behind the survivor, and a single nova, field or cleave then eats a dozen
  at once. The flow field (`Battle.Flow`) makes every chaser converge on the
  same path, so herding works with the engine, not against it.
- **Design rules:** never give fodder a verb that makes it worth reading
  individually (that is a different role). Vary it by speed and toughness
  only. A people's fodder should be its slowest thing, so a wall forms
  behind the faster roles rather than in front of them.

## Swarmer

**It asks:** can you hold every side? **Today:** the Longtooth Wolf
(`Behavior.Pack`: fans to a slot 4 m round the survivor, then closes; 5.3
speed; attacks every 0.9 s).

Swarmers are fodder with a plan. Their danger is that they arrive together
and from all sides, which turns the grace window against the survivor: there
is always another wolf ready when it ends.

- **Simple:** keep moving in one direction. A pack that has fanned out has
  to re-form, and the survivor outruns the slots on the far side.
- **Sweaty:** turn and fight as the ring closes. The moment before contact,
  every wolf is 4 m away at once: one nova or Dawnpulse (radius 3.75) or a
  Whirlwind takes them all. War Cry's fear breaks the ring entirely.
- **Design rules:** keep swarmers soft (they are dangerous by arrival, not
  by health) and fast. Never combine a swarmer's slots with a ranged attack.

## Charger

**It asks:** are you on the line? **Today:** the Thicket Tusker (`Charge`:
range 10, 0.9 s wind-up, runs 13 m/s for 1 s; a charge that ends in a tree
stuns it 1.8 s and costs it 12% of its health), and the lunges of the
elites (barrow knight, Greymuzzle, enforcer: 0.6–0.75 s wind-ups, 17–19 m/s).

Chargers are the game's best-designed creatures today. The lane is drawn on
the ground as a hostile red line for the whole wind-up (`Ev.Telegraph`
`Shape = Line`), the blow is 1.5× contact damage, and slipping it in a dash's
first 0.18 s is a **perfect dodge**: the dash comes back, the air cracks and
the next strikes are sure (`Battle.PerfectDodge`).

- **Simple:** step sideways when the red lane appears. A charge that misses
  leaves the charger recovering for 0.55 s.
- **Sweaty:** stand in front of a tree. A tusker that charges into it is
  stunned and hurt for free; a lunge slipped with a dash is a perfect dodge
  and, with Duelist's Grace, fires every weapon at once.
- **Design rules:** a charge's wind-up must never be shorter than 0.6 s at
  any tier (the deft bot dodges 0.75 s lunges reliably; humans need more
  than the bot). Never let two chargers' lanes cross the survivor in the
  same 0.5 s unless they come from one champion's escort (read as one
  event). The oath of the hunt makes them faster (×1.2), never their
  wind-ups shorter.

## Ranged

**It asks:** will you come to me? **Today:** the Risen Bowman (range 9,
every 2.8 s, a bone bolt at 11 m/s for 7). The arena caps throwers and
shooters at `5 + minute / 3` (16, 24 after the win), a good rule: hundreds
of shooters are "weather, not a fight" (`ArenaRun.RangedCap`).

Ranged creatures keep 55–85% of their range and **strafe** when the survivor
stands to shoot them (`Ai.Update`, `Behavior.Ranged`). Their bolts are slow
enough to sidestep (11 m/s from 9 m is 0.8 s).

- **Simple:** chip damage, out-healed. One bowman's 7 every 2.8 s is 2.5 a
  second; Recovery at rank 4 gives 2.4.
- **Sweaty:** dives them (the deft bot's rule: when nothing presses, close on
  the nearest thrower) or turns their bolts: Bulwark sends arrows and bolts
  back at whoever loosed them, a hard counter that is also a choice of art.
- **Design rules:** ranged creatures should be soft (they die to anything
  that reaches them) and the cap should stay. Their bolts must read as
  hostile red against every school's effects (`docs/feel/SUGGESTIONS.md`
  S-19). Avoid ranged creatures that flee as the survivor approaches: kiting
  enemies are the genre's most-named tedium (`RESEARCH.md`).

## Lobber (area denial)

**It asks:** can you keep moving? **Today:** the Kerchief Pillager (firepots
every 4.2 s that leave 1.7 m of burning ground for 3.5 s) and the Lampling
Sapper (every 4.4 s, 1.6 m for 3 s, and it bursts when it dies). Lobs lead
the survivor by 0.45 s and are marked on the ground for their whole flight.

Area denial is the counterweight to "stand in the middle and let the build
work". It is the only role that punishes stillness itself, which makes it
essential to a survivors game: without it, the dominant strategy is to stop
moving.

- **Simple:** never stand still. A moving survivor is past the landing point
  before the pot lands; the lead is 0.45 s, the pot's flight about 1 s.
- **Sweaty:** herds the horde onto the fire. Enemy ground fire hurts only the
  survivor today (`SpawnZone(Side.Enemy, ...)`); making it hurt the horde too
  would give area denial a second edge (see `IMPLEMENTATION.md`, item 9).
- **Design rules:** ground lasts no longer than 3.5 s at any tier; burning
  ground under the survivor must be visible through the survivor's own
  effects (S-19). Lobbers share the ranged cap.

## Guard

**It asks:** can you get round? **Today:** the Risen Shieldman (a 1.4 rad
arc, 75% off projectiles from the front) and the Kerchief Bruiser (1.6 rad,
80%). The guard is open while it is stunned or frozen.

The guard is the game's one genuine **hard counter**, and it counters a
whole category of build: anything tagged `Projectile`. Area, nova, zone,
melee, chain, beam and summon damage ignore it entirely. The probe measures
the gap (`COUNTERS.md`): a Volley build kills bruisers at about a fifth of
the rate an Arcweb build does, and a Knifestorm build not at all.

- **Simple:** draft anything that is not a projectile, or be patient: a
  guard's front is only the side facing the survivor, and the crowd turns
  it. The relaxed player is not stuck; they are slower.
- **Sweaty:** flanks (a dash past the shield and the next volley is in its
  back), freezes it (Rimeshard's chill opens the guard while frozen),
  stuns it (Shield Bash, Grapple), or brings a bouncing disc whose ricochets
  come in from the side.
- **Design rules:** never fill a whole arena with guards. A people with a
  guard must also field things a projectile build can kill, so a projectile
  survivor has a job while the guards are slow to fall (the Kerchiefs do:
  footpads and pillagers). Keep the reduction at 75–80%, never 100%
  (immunity is a wall, not a puzzle).

## Summoner / raiser

**It asks:** will you kill the source? **Today:** the Grave-Caller (every
7 s, if a grave lies within 7 m, a 1.5 s cast marked with a ring and "Rise...",
then two fallen get up as fresh risen). Any blow that freezes it, and arts
that interrupt, stop the cast and push the next one back 3 s
(`Battle.Interrupt`).

Raisers are the purest priority-target puzzle: ignoring one does not kill
the survivor, it makes the fight longer and denser. They are also the role
most at risk of being **tedium** (the same dead killed twice gives no ember:
raised risen drop it again only if the design wants them to).

- **Simple:** out-damages the stream. Two risen every 7 s is less than any
  build kills; the caller's frost orbs (slow 0.6 for 1.4 s) are the real
  nuisance.
- **Sweaty:** interrupts the cast (Shield Bash, War Cry, Time Slip, Grapple
  all `Interrupts`), or simply moves the fight: graves only rise within 7 m
  of the caller, so a survivor who drags the horde away from the corpses
  starves it.
- **Design rules:** a raiser must cast in sight, with its ring, and never
  raise elites. Cap raised creatures per caller (two a cast is right).
  Raised creatures should give ember once only, so raising is never farmed.

## Splitter

**It asks:** can you finish what you start? **Today:** none, though
`SplitSpec` exists and `Battle.KillEnemy` already spawns the young.

Splitters punish single-target builds and reward area. They are cheap to
make (data only) and read well if the young are visibly smaller and the
parent visibly swollen.

- **Simple:** area weapons eat the young; a single-target survivor takes
  longer but is in no danger (the young are fodder).
- **Sweaty:** kills the parent where the young will land in fire or on
  hallowed ground, or freezes it before the killing blow (Shatter's frost
  spray chills the young as they appear).
- **Design rules:** young never split again. The parent's health plus its
  young's should be no more than 1.6× a fodder of the same tier, so killing
  a splitter is never a bad trade. See the Bone-Heap in `ROSTER.md`.

## Burrower

**It asks:** do you watch the ground? **Today:** the Lampling Tunneler goes
under when the survivor is more than 6 m away, travels at 1.8× its speed, and
surfaces within 2.4 m with a 0.55 s ring; surfacing beside the survivor hits
for 1.2× and is a telegraphed blow (so it can be perfectly dodged).

Burrowers deny the "kite at a distance" answer: distance is what makes them
dive. They are untargetable while under (`Battle` keeps them out of the
spatial grid), which is fine as long as the time under is short and the
surfacing is loud.

- **Simple:** keeps moving; most surfacings land behind a moving survivor.
- **Sweaty:** stands still on purpose with a nova or a Bonesplitter primed,
  lets them surface in a ring, and takes them all as they rise (the
  surfacing state is targetable, and the 0.55 s ring is the window).
- **Design rules:** never more than about eight burrowers underground at
  once (the ground becomes noise); each surfacing ring must be readable at
  minute 25 density.

## Aura / buffer

**It asks:** who do you kill first? **Today:** none. Needs a small new spec
(`AuraSpec`: a radius and a stat for allies inside it).

Buffers are the role that turns a crowd into a formation. Doom Eternal's
lesson applies: a buffer must be **visible as the reason** the crowd is
strong (a banner, a lamp, a drum), so killing it is a decision with a
visible payoff (`RESEARCH.md`, Doom Eternal).

- **Simple:** ignores it. A buffed crowd is a harder crowd, not a lethal one,
  if buffs stay modest (+25–30% speed or damage, never health).
- **Sweaty:** kills the carrier first (Mark Prey and Hunter's Mark already
  seek the strongest; a buffer should count as "strongest" for seeking);
  the escort routs when it dies (see the Signs in `COUNTERS.md`).
- **Design rules:** one buffer's aura on screen per kind; auras never stack
  with themselves; the buffed glow in the buffer's colour.

## Healer / mender

**It asks:** can you burst? **Today:** none. Needs `MendSpec` (a heal pulse
on allies in a radius, every N seconds, with a cast that can be interrupted).

Healers are the most-hated support role in the genre when they make fights
long and the healer hard to reach (`RESEARCH.md`: Brotato's "Buffer" and
healers, Diablo's shamans). Here they must be cheap to kill and loud.

- **Simple:** out-damages the heal. A mender restores 15% of an ally's health
  every 6 s, far less than any build's area does.
- **Sweaty:** interrupts the cast, or kills the healer first; the mend's cast
  ring is the window.
- **Design rules:** a healer heals others, never itself; heals are a
  percentage, so they matter on champions and not on fodder; at most two on
  screen.

## Exploder

**It asks:** are you too close when it dies? **Today:** the Blight-Sick Wolf
(dies into a 2.4 m poison burst after a 0.5 s fuse) and the Lampling Sapper
(2.2 m, 1.2× damage, 0.6 s fuse, burns). Under the oath of ruin any death may
burst (22%, 1.8 m, 0.7 s fuse).

Exploders are the genre's sharpest double edge. On-death effects are among
the most complained-of mechanics in ARPGs when they are invisible or
instant (Diablo III's Molten and Arcane death effects, Path of Exile's
"volatile" deaths: `RESEARCH.md`). Here every burst is a telegraphed ring
with a fuse, which is the fix.

- **Simple:** ranged weapons kill exploders before they arrive, and the fuse
  is long enough to walk out of.
- **Sweaty:** lets it run into the crowd and dies it there. Today the burst
  hurts only the survivor (`StrikeSpec ... Side.Enemy`); a burst that also
  hurts the horde (as Fracture's and Pyre Burst's do for the survivor's
  side) turns every exploder into a tool (`IMPLEMENTATION.md`, item 9).
- **Design rules:** fuse at least 0.5 s, ring always drawn; an exploder's
  burst never chains into another exploder's (no surprise cascades);
  bursts never follow a death from a damage-over-time the survivor cannot
  see ticking.

## Flyer / orbiter

**It asks:** can you stop circling? **Today:** none, though `Behavior.Orbit`
is written (holds a 6 m ring round the target and walks it at 0.9 rad/s) and
used by nothing.

Orbiters deny the commonest relaxed answer, "walk in a big circle", because
they circle with you. A flyer variant ignores walls and cover.

- **Simple:** homing and area weapons find them; their blows are small.
- **Sweaty:** cuts across the ring (they hold a radius, so moving through
  the centre makes them reposition), or uses the ring: an orbiter is always
  6 m away, which is exactly a Dawnpulse's reach with Expanse.
- **Design rules:** orbiters must be soft and few (four to six); they never
  shoot while orbiting (that is a ranged kiter, which is tedium).

## Armoured / heavy

**It asks:** do you have weight? **Today:** the bruiser (90 health, mass 3),
and every elite (mass 5, resists by family). Knockback divides by mass, and
elites take a third of it.

Armour is the soft counter of choice in a survivors game: it slows the kill
without ever stopping it. Resistances by family already do this
(`Enemies.Undead`: frost 25%, shadow 35%, holy −50%, fire −15%).

- **Simple:** a slower kill, nothing worse.
- **Sweaty:** brings the answer the map names: crits under the oath of iron,
  holy against the dead, fire against beasts, Mark Prey and Hunter's Mark
  on the heaviest thing in sight.
- **Design rules:** no resistance above 50% on any rank-and-file creature;
  no immunities, ever, except bosses to fear and charm (Diablo II's
  immunities are the genre's standing example of a hard counter that
  invalidated builds: `RESEARCH.md`).

## Thief / fleer

**It asks:** will you give chase? **Today:** none, though `Behavior.Flee`
and `EnemyState.Fleeing` exist and do nothing.

The loot goblin. It is pure opt-in risk: ignoring it costs nothing, chasing
it pulls the survivor out of position for a purse. See the Cutpurse in
`ROSTER.md`.

- **Simple:** ignores it and loses nothing they had.
- **Sweaty:** chases it through the horde, the survivors-game version of
  Diablo III's treasure goblin.
- **Design rules:** it steals nothing the survivor already owns (ember on
  the ground at most), it is visible from across the arena, and it escapes
  after 20 s, taking only what it took.

## Champion and herald

**It asks:** can you do two things at once? **Today:** any creature can be a
champion (the arena's champion flag: three times the health, a level higher,
a third of the knockback, frozen half as long, a 40% chance of a draught).
Champions come with an escort every fourth event and carry a chest; a
**herald** of the people comes at ten and twenty minutes with (4 + tier)×
health and a chest. **They have no Signs** (affixes): a champion is a bigger
version of what it was.

This is the biggest gap in the horde and the biggest opportunity. Diablo's
champion and elite affixes are what make its ordinary fights memorable
(`RESEARCH.md`), and they are where a sweaty player reads, prepares and
profits. `COUNTERS.md` §4 proposes twelve Signs with readable tells and a
counter each, and `RISK_REWARD.md` what they should pay.

- **Simple:** kites the champion while the build works. Champions are slow
  fights, not sudden deaths.
- **Sweaty:** reads the Sign as it walks in and answers it: kills the
  banner-bearer's escort-leader first, drags the burning one away from the
  crowd, freezes the mender's cast.
- **Design rules:** at most one champion's Sign on screen per kind of
  effect (one aura, one trail, one death effect at a time); Signs scale in
  number by tier, never in strength by tier.

---

## What the roster covers today

| Role | the Pack | the Risen | the Lamplings | the Kerchiefs |
|---|---|---|---|---|
| Fodder | (wolves are swarmers) | risen | tunneler | footpad |
| Swarmer | wolf | – | – | – |
| Charger | tusker; Greymuzzle | barrow knight | – | enforcer |
| Ranged | – | bowman | – | – |
| Lobber | – | – | sapper | pillager |
| Guard | – | shieldman | – | bruiser |
| Raiser | – | grave-caller | – | – |
| Exploder | blight-sick wolf | – | sapper | – |
| Burrower | – | – | tunneler | – |
| Splitter, aura, healer, orbiter, thief | – | – | – | – |

Each people asks three or four questions; together they ask nine of the
sixteen. The Lamplings ask the fewest (two kinds), the Risen the most. Five
roles are unbuilt, and three of those (splitter, orbiter, thief) have their
verbs already written. `ROSTER.md` fills the gaps people by people, and
`IMPLEMENTATION.md` orders the work.
