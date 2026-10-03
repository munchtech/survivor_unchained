# A catalogue of boss mechanics for a survivors-like

What a boss can do in a game where the player mostly moves and the build
does the killing, drawn from the teardown in `RESEARCH.md` (section
numbers in brackets point there; the full notes with every source are in
`notes/`). Each entry says how the mechanic works and why it is fun, how
it fails, what it needs to stay readable and accessible, and how it copes
with builds from weak to absurd. Where a design in `SURVIVORS_BOSSES.md`
uses it, the design is named.

The genre's starting point, in the players' own ranking (`RESEARCH.md` §6):
the most common complaint about survivors-like bosses is the **HP sponge**
(a big health bar on two to four moves); the second is **not being able to
see the attack** under the horde and the player's own effects; the third is
**a build that cannot answer the boss**. The most common praise is for a
boss that **switches the game into a learnable dodging dance** for a
while, then **pays out big at the kill**, on **a stage cleared for it**.

## 1. Movement checks and damage checks

**How it works.** Every boss attack asks one of two questions. A movement
check asks the player to be somewhere else in time (a lane, a ring, a
safe spot). A damage check asks the build to deal a sum in a window (break
a channel, kill the adds before they heal the boss, a shield before it
blows). A good fight alternates them, so both halves of a survivors build
(the draft and the hands) matter.

**Why it is fun.** In an auto-attacking game movement is the player's only
verb, so the movement check is where the skill lives; the damage check is
where the build is felt. Players praise fights that "feel very
bullet-hell" (Halls of Torment's Lord of Pain, [§1.2]) and Death Must Die's
Lady "because you can dance with her" [§3.6].

**Failure modes.**
- *The pure damage check*: a hard death timer the build must beat. Halls of
  Torment's 40-second curse on the Lord of Pain was its most hated
  mechanic in early access and was removed within weeks for a Lord that
  "gets stronger over time" [§1.2].
- *The single-stat check*: a boss only movement speed can answer (Lord of
  Pain's triple dash, Brotato's elites, DRG: Survivor's "keep +10% movement
  speed") reads as "the draft lied to me" [§6].
- *The movement check nobody can see*: under the horde or the build's own
  light (§2).

**Readability.** A damage check must show its sum and its clock: the Ford-
Warden's channel bar ("Calling the drowned: break it!") is exactly right.

**Scaling.** Damage checks scale themselves (a strong build passes them
early); movement checks do not. So a boss that must stay hard for a strong
build should lean on movement checks, and one that must stay passable for
a weak build should give every damage check a fallback (the channel fails
into a heal and a relit lamp, not a death).

*Used by:* every design; the Pack-Mother is the movement-heaviest, the
Barn Thing's Drag the purest damage check.

## 2. Telegraph language

**How it works.** A telegraph is the boss asking its question in advance:
a wind-up in the body, a shape on the ground, a sound, sometimes a word.
The genre's best practice is all of them at once.

- **Ground decals with a fixed delay.** The camera looks at the floor;
  shapes read where sprites overlap. Diablo III built the vocabulary (rings
  before a slam, a lit line before a charge, tiles that light before they
  burn), with 1–2 s delays [§4.1]. Vampire Survivors' Shooting Stars land
  on their markers after 2 s [§2]; Soulstone's red zones are harmless until
  filled [§3.4].
- **Wind-up first, decal second.** The DRG: Survivor Dreadnought "stops and
  wiggles" before it jumps, learned in one sentence ("when he stops do a 90
  degree turn") [§3.5]; Hollow Knight: Silksong's bosses move into
  position before acting, so repositioning is itself a tell [§5].
- **Sound and voice.** Sound is the one channel the player's build cannot
  drown out. Halls of Torment added sound cues to lances after complaints
  [§1.4]; Path of Exile's lethal moves are shouted ("DIE!", "STAND
  STILL!") [§4.2]; Azmodan announces his adds [§4.1]; HoloCure pairs a
  "!!" icon with an audio cue [§3.3].
- **One colour per rule, not per attack.** Returnal's purple means "cannot
  be dashed through"; Path of Exile 2's red flash means "cannot be blocked"
  [§4.2, §5]. Proposed for us: **amber** a blow is coming here, **violet**
  this ground stays bad, **pale blue** stand here (a safe spot or the
  boss's open moment), **grey** this will be solid.
- **The safe shape.** Once the floor is busy, showing where to stand reads
  better than showing where not to: Zana's bubble, the Elder's inner ring,
  the Arbiter of Ash's safe-inside seed, Malthael's sector behind him
  [§4.1, §4.2].
- **Named attacks.** Touhou's spell cards give each pattern a name, a timer
  and a capture bonus [§5]; a name on screen makes a move learnable and
  quotable. Keegan's duel in `ARPG_BOSSES.md` makes the name the telegraph.

**Teaching (2.6).** Teach one attack at a time, then combine (Cuphead's
Root Pack, Bullet King) [§5]; preview the boss in the run before it comes
(Vampire Survivors' Cappella Magna parades the Ender's five parts in turn
before it [§2]; Halls of Torment's mid-run bosses [§1.1]). Our Kindling at
15:00 is that preview.

**Failure modes.** A decal that lies about the hitbox (Belial, launch Uber
Lilith) [§4.1]; a body tell that must be read before the decal appears
(Death Must Die's Frog King) [§3.6]; attacks triggered from off-screen
(Halls of Torment's Frozen Depths, fixed by shorter trigger ranges)
[§1.4]; un-expiring clutter (Soulstone, Rogue: Genesia) [§3.4, §6]; a
remix boss that changes form mid-tell (Isaac's Delirium) [§5].

**Readability in a horde.** Draw enemy telegraphs *above* the player's own
effects: Halls of Torment moved its Frost Avalanche under enemy projectiles
and added an opacity slider; Soulstone exempted boss attacks from its
slider; Picayune Dreams dims the player's weapons during every boss [§1.4,
§3.4, §6]. A slider is a patch; the draw order is the fix.

**Accessibility.** Never colour alone, never sound alone (the Game
Accessibility Guidelines; red/green deficiency affects 8–10% of men) [§5].
Each of our four colours carries an edge pattern (filled, hatched, dashed,
solid) and each lethal telegraph a sound and, for the boss's signature
moves, a word. An option to lengthen wind-ups by a quarter.

**Scaling.** Telegraph time must not scale down with difficulty past a
floor: Soulstone's endless bosses whose "attack speed almost becomes
instant" were capped at +70% [§3.4]. Our floor: 0.7 s.

*Used by:* every design; the Barn Thing is built on sound (with a ring shown
for every knock).

## 3. Phase changes

**How it works.** The boss changes at thresholds: new moves, a new arena, a
new partner, faster tempo. The bar shows where the thresholds are.

**Why it is fun.** A phase is a second fight inside the first, and the
transition is a beat of drama (Lich dragging the player into a smaller
room; Mithrix leaving and the horde becoming the fight) [§5].

**What triggers a phase.**
- *Health*: the classic. Fails against a strong build, which skips phases.
- *Health or time, whichever comes first* (Brotato's Predator at 50% or 45
  s) [§3.1]: a weak build still sees every phase. The single most
  transferable rule in the research.
- *Time and level together* (Vampire Survivors' Directer opens each phase
  at a timer **and** a player level of 7, 14, 19, 22) [§2]: the strong
  build waits for the show; the weak build is fed experience by the fight.
- *A damage bank* (the Ender's 90 s shield stores all damage and releases
  it at once) [§2]: the strong build's power is shown, not wasted.
- *Health gates with invulnerable intermissions* (Path of Exile's Sirus at
  75/50/25%, the Shaper's corridor runs) [§4.2]; *breakable shields at
  thresholds* (Diablo IV Season 10 replaced immunity with shields at a third
  and two thirds that a build can break in 5 s) [§4.1]; *ward at
  breakpoints that decays* (Last Epoch 1.1) [§4.2].

**Failure modes.** A transition that breaks when a build crosses two
thresholds in one hit: a 2025 bug left Uber Lilith stuck invulnerable when
her health fell "too quickly" [§4.1]. A survivors build will do this every
time; transitions must queue. Long untargetable intermissions ("an
Action-RPG without the action", Uber Lilith) [§4.1]. Phases that are the
same moves with more health (Voidling's "cardinal sin of being boring")
[§5].

**Readability.** Marks on the bar (Furi's pips, Returnal's three bars) and
the arena as the bar (Hush's room darkening, Typhon's wounds, Tisiphone's
walls closing at 50% and 25%) [§5]. Music too: Scylla's band loses an
instrument as each Siren falls [§5].

**Scaling.** Our contract (`SURVIVORS_BOSSES.md` §0.5): each phase ends at
its mark or its time ceiling, never before its floor; overkill fills the
Break. Thresholds crossed together queue in order.

*Used by:* every arena design; the Penitent's "death" at 60% and the
Barrow Lord's lay-down are phase changes dressed as story.

## 4. Arena shaping

**How it works.** The fight changes the ground: rings that shrink, walls
that rise, water that floods, light that fails, pits that open, hazards
the boss leaves behind.

**Why it is fun.** In a game about movement, changing the space changes
the game. A shrinking arena is also a soft enrage the player can see.

**Kinds, with their best examples** [§3–§5]:
- *A temporary wall that forces the duel*: 20 Minutes Till Dawn's 60 s
  electric barrier on open maps; Death Must Die's barrier that dissolves
  after a set time even if the boss lives. Stops the boss being kited
  forever, which our probe found Grimtunnel can be.
- *A shrinking safe space*: Azmodan's pools; Andariel's added hazard per
  intermission; Lilith's breaking platform; Risk of Rain 2's Eclipse
  halving the teleporter ring; False Son's arena losing rings.
- *Hazards the boss lays down*: Mithrix's 45 s fire pillars; the Shaper's
  vortices; Halls of Torment's Lord of Regret's mines.
- *The arena as part of the boss*: the Ford-Warden's lamps; Nuclear
  Throne's generators (destroy all four and the Throne loses half its
  health); Halls of Torment's hidden "Lord Hexes" [§1.3].
- *Light and dark*: 20 Minutes Till Dawn's dark around a small light;
  Ravenswatch flipping every chapter boss to night at half health [§3.7].

**Failure modes.** Hazards that never expire and litter the arena
(Soulstone, Vampire Hunters' permanent slime, Shaper phase 3) [§3.4, §6,
§4.2]; walls that one-shot (Spirit Hunters' shrinking spike cage, made a
fixed cage of "Boss Hurty Spikes") [§3.10]; walls whose collision lies
(Grind Survivors' barrier gaps) [§6]; arena changes that last beyond the
fight [§6]; knockback into walls [§3.10].

**Readability.** Show the future shape before it is solid (grey, "this will
be solid"), give every lingering hazard a lifetime, and keep at most one
kind of persistent hazard at once [§4.2].

**Scaling.** Space does not scale with damage, which is the point: a
shrinking ring threatens an absurd build as much as a weak one. Hurt, do
not kill: walls and floods should cost health and position, not the run.

*Used by:* Grimtunnel (pits), the Kiln Warden (the flood), the Red Hand and
the Keeper (cages and sliding rows), the Pack-Mother (dark), the Barn Thing
(the ground going), the Dawn.

## 5. Adds and the horde

**How it works.** The survivors boss arrives on top of a horde; what the two
do together is the genre's own design space.

**Kinds** [§1–§6]:
- *The horde clears for the duel*: HoloCure wipes the field and sends a
  themed escort; Bounty of One's hunters "retreat"; Diablo III's Greater
  Rift kills everything within 100 yards when the guardian spawns; 20
  Minutes Till Dawn's developer announced, for its beta, that spawns would
  stop during bosses "to prevent too much clutter". The most-praised readability fix.
- *The boss on top of the horde*: Risk of Rain 2's teleporter boss ignores
  the monster cap and fights inside a charging circle; spawns stop at 99%.
- *The horde as a resource the boss uses*: Sketamari absorbs enemies and
  grows; Avatar of Gaea's health is the run's kill count; Atziri's adds
  walk to her and heal her; the Trickster turns XP gems into bombs [§2,
  §4.2].
- *The horde as a resource the player uses*: Nova Drift's Dweller **loses
  health whenever a minion dies**, so area builds still count against a
  single target [§3.9]; Hyper Light Drifter's Emperor is stunned by its own
  exploding adds [§5]; the Shaper's add waves refill flasks [§4.2].
- *Adds as an armour gate*: Ravenswatch bosses take 50–75% less while their
  adds live, and are stunned when they die [§3.7]; Diablo IV's Varshan
  gains a buff unless the add he channels is killed [§4.1].
- *Adds with a job*: our Slurry Engine's menders; Halls of Torment's
  Marching Ghosts, two armies converging as a visible countdown [§1.2].

**Failure modes.** Adds that soak the player's auto-aim and projectiles
were Halls of Torment's angriest feedback (the Lord of Regret's orbs, made
untargetable) [§1.2] and Army of Ruin's deadliest fight (a saw that blocked
shots while the minion ramp peaked) [§3.11]. Filler adds that only feed an
area build (Diablo IV) [§4.1]. Late, a bigger horde helps an evolved build
rather than threatening it [§3.11].

**Readability.** Adds a boss uses should be its own kind, look different
from the field, and say what they do (a mender's channel bar; a tether to
the boss).

**Scaling.** "Health from kills" and "armour while adds live" make the
horde-clearing half of a build count against the boss; prefer them to
single-target damage checks, which punish the area builds the genre
rewards all run [§1.5's "single-target damage versus horde-clear builds"].

*Used by:* the Pack-Mother (commands), the Barrow Lord (formations, raising),
Grimtunnel (moths to light), the Barn Thing (feeds), the Penitent (the
horde parts for him), the Keeper (hostages).

## 6. Shields, weak points and breakable parts

**How it works.** The boss is protected until something is broken: lamps,
valves, a standard, hands, heads, pylons. Or it has weak points that take
more.

**Why it is fun.** It gives the player a target to choose, a sequence to
plan, and a visible win in the middle of the fight. It also gives crowd
control and area damage a job when the boss itself shrugs them off.

**Examples.** The Ford-Warden's three lamps (ours); Mega Satan's hands;
the Directer's masks breakable after a time and a level; Orochimario's
eight heads; the Giant Enemy Crab's pincers that regrow; the Lord of
Greed's four pylons; Diablo IV's breakable shields; Rogue: Genesia's Sand
Worm shield broken by killing elites from the horde [§2, §1, §4, §6].

**Failure modes.** A shield the build cannot answer (Rogue: Genesia's Void
Primordial, damageable only with enough penetration: one player finished
it after 30 hours at one frame a second) [§6]; parts that regrow forever;
parts hidden behind the boss from a high camera.

**Readability.** Parts glow in the boss's colour, sit on the side the
camera sees, and show on the bar as pips. A broken part should fall off.

**Accessibility.** Parts are targets for auto-aim and every weapon, never
special-cased (`IMPLEMENTATION.md` N3).

**Scaling.** Parts have their own health, so a strong build breaks them in
seconds; the reward should be something the player can see (a verb gone, a
stagger), not a number.

**Stagger.** Diablo IV gives every boss a stagger bar under its health,
filled by every kind of crowd control (chill, slow, stun, knock-back, fear,
freeze); when full the boss is held for a few seconds, then resists for a
while, so control builds earn a damage window without locking the boss
for ever [§4.1]. It turns the exemptions a boss needs into a currency the
build spends. Ravenswatch's bosses and elites have stagger bars too, and
their resistance rises by chapter because players' ability to stagger
grows [§3.7].

*Used by:* Grimtunnel's lamps, the Barrow Lord's standard, the Kiln Warden's
irons, the Barn Thing's segments, the Kindling's heart, the Slurry Engine's
valves; stagger on every boss (`SURVIVORS_BOSSES.md` §0.15).

## 7. Soft and hard enrages, and the floor under fight length

**How it works.** A soft enrage makes the fight harder the longer it lasts;
a hard enrage ends it. A floor stops a strong build ending it too soon.

**The floor: caps, gates and banks** [§5, §4, §2]:
- *Damage caps*: Enter the Gungeon caps boss DPS over a 3 s window (about
  25–35 s per phase); Isaac's armour is health ÷ soft-cap DPS, so the
  armour number is the intended minimum length (Hush: 140 s), with a 9%
  floor so broken builds still win; Slay the Spire's Heart takes at most
  300 a turn; Risk of Rain 2's adaptive armour taxes burst.
- *Gates and banks*: §3 above. Path of Exile 2's emergence damage reduction
  fades over time; Nova Drift's final boss takes *more* damage from 35 s in,
  so weak builds are carried to the end.
- **The cost of a hidden cap**: Gungeon *raised* its caps in its final
  update so synergies "feel appropriately powerful", and removed them in
  Boss Rush; players treat breaking the cap as content [§5]. A cap the
  player cannot see feels like the game cheating. Our Break makes the
  surplus loud instead of hiding it.

**The soft enrage.** Halls of Torment's Lords "get stronger over time"
(instead of a death timer) [§1.2]; DRG: Survivor raises its threat level
every 60 s of a boss fight and grades the loot crate by time to kill
[§3.5]; Ravenswatch's overtime adds up to +100% boss health and damage over
three minutes [§3.7]; Diablo III's Torment enrages turn a known mechanic all
the way up (all the Butcher's grates ignite) [§4.1]. The best enrage is a
mechanic the player already knows, at full strength.

**The hard enrage.** Vampire Survivors' Reaper (655,350 × level health,
65,535 damage) is a curtain, not a fight; the White Hand ends even a run
that killed it [§2]. Brotato's boss wave ends after 90 s and counts as a
win [§3.1]; Death Must Die's barrier dissolves [§3.6].

**Failure modes.** The binary death timer (Halls of Torment, above). A soft-
lock: a boss that heals faster than a legal build hurts it (Rogue:
Genesia's Vampire Queen) [§6]; the developer considered healing that
weakens the longer the fight runs, which is the right shape for any heal.

**Scaling.** Our contract: floors and ceilings per phase, the Break, a soft
enrage at 3:00 (the known moves faster, the horde back to full) and a hard
enrage at 5:00 (the boss's signature move on a loop). Neither should be met
by an ordinary build; both should be survivable for a while by a weak one.

## 8. Bosses that steal or turn the player's own tools

**How it works.** The boss takes, disables or copies what the player
built: weapons, items, summons, pickups, the dash.

**Why it is fun.** The genre's fantasy is the build; a boss that touches it
makes the player feel what each piece was doing, and getting it back is a
victory inside the victory.

**Examples** [§2, §3, §5]:
- Mithrix steals every item in phase 4 and returns them as he is damaged.
  Hated until Hopoo made it deterministic ("if you have him at 50% health,
  you will have 50% of your items back"): "We want this to be a fun phase,
  not a frustrating conclusion."
- Megabonk's final boss strips the weapons and returns one per phase.
- Death and Je-Ne-Viv in Vampire Survivors remove the player's weapons for
  part of the fight (which also clears the screen of the player's effects).
- Hades II's short inversions: Hecate's sheep curse, Eris firing the first
  game's Rail, Chronos turning Melinoë into a child for one dodge-only
  phase.
- The Trickster turns XP gems into bombs; the Cosmic Egg casts the player's
  own Infinite Corridor.

**Failure modes.** A counter that makes players **avoid power**: players
scrapped items before Mithrix so he could not use them, and called the
phase one that "punishes you for doing well" [§5]. Denying a build's core
verb outright (Death Must Die's Frog King could not be dashed through,
breaking dash builds; the Lady's charm on summons was hotfixed from 20% to
7%) [§3.6]. A boss that invalidates a weapon family (Polyphemus against
melee; Vampire Hunters' statue the flamethrower could not reach) [§5.2, §6].
A move that punishes the player for attacking (Polyphemus's "Where Are
You?" counter, triggered even by familiars and boon effects) [§5.2]: our
weapons fire on their own, so no boss may ever punish being hit.

**The rules.** Proportional, visible, time-limited, and always returned,
ideally with a bonus. Never take the dash. Never let the counter scale
with how good the build is (the Penitent grows from stones *left on the
ground*, not from the survivor's power).

*Used by:* the Red Hand (the Toll), the Silver Penitent (a rival from the
survivor's own build), the Barrow Lord (raised allies called back), the
Centurion (ember as the toll).

## 9. Pacing around the 30-minute mark and the endless phase

**How it works.** Where bosses sit in the run, and what the half hour and
the time after it feel like.

**What the research shows** [§1, §2, §3]:
- **Mid-run bosses carry the pacing.** Halls of Torment puts a boss every
  eight minutes (6, 14, 22) with an elite between, and unlocks the next
  hall from a mid-run boss, never the Lord. Vampire Survivors' Arcana
  bosses at 11:00 and 21:00 carry the run's biggest choices. HoloCure has a
  mini-boss every two minutes and bosses at 10 and 20.
- **Clear the stage for the climax.** Vampire Survivors clears the screen
  before the Reaper and before the Ender (fade to black, a 30 s countdown,
  a cutscene of its five parts merging); Soulstone's Lords arrive "encased
  in statues" for a few seconds of preparation [§3.4].
- **The 30-minute tax.** A loss or a slog at the end of half an hour feels
  like the half hour was wasted (Halls of Torment's most persistent
  complaint) [§1.5]. Keep the final fight short at par (our 90–120 s), and
  never let it soft-lock.
- **Power can shorten the night.** Halls of Torment's Boglands summons its
  Lord after 20,000 kills; the Vault's Lord is unsealed by the player;
  Ravenswatch's Hourglass rewards summoning the boss early [§1.3, §3.7].
- **Endless.** Vampire Survivors re-runs the whole boss schedule with +100%
  health a cycle; Halls of Torment's Vault scales until its run "starts
  breaking" at about 95 minutes; Megabonk's endless swarm produced
  five-hour runs at 1.5 frames a second until ghosts sped up after 20
  minutes. Players say endless needs new mechanics, not more health
  ("fighting the same bosses ... just with more health now isn't all that
  enticing", Picayune Dreams' developer) [§6]. Opt-in boss density is the
  favourite: Risk of Rain 2's Shrine of the Mountain doubles the boss and
  the drops; Vampire Hunters' constellations; Boss Rash's red skull plate
  [§5, §6, §2].

*Used by:* the run-up and arrival (§0.2–0.3), the Kindling (§9), Echoes and
the Dawn (§10–11) in `SURVIVORS_BOSSES.md`.

## 10. Rewards and the moment of victory

**How it works.** What the kill gives, and how the game says "won".

**The chest.** Vampire Survivors' chest pauses the game, spins reels, plays
a jingle per tier (1, 3 or 5 items), fires fireworks, never gives an
unwanted item ("Treasure Chests are supposed to be a purely positive
thing", Galante), scripts the first six chests as 1-1-3-1-1-5 so a new
player sees the jackpot early, and withholds the skip button until the
player has seen hundreds [§2]. Players across the genre name the boss's
exclusive reward as the best part of a boss [§6]. `docs/feel` S-09 already
specifies our chest as a sequence; the boss should drop the biggest one.

**The physical win.** Halls of Torment's Lord drops a crystal; picking it up
ends the run, and the well teleports to the player so the victory lap is
not a walk through a live horde [§1.3]. HoloCure blacks out to a "stage
cleared" card [§3.3]. Hades shows "Boss Vanquished" and opens a safe room;
Mithrix's death starts a three-minute escape with the player's whole build
returned [§5].

**Speed and skill rewards.** DRG: Survivor's crate graded by time to kill;
Nuclear Throne's Big Bandit opens a secret area if killed in under 10 s;
Gungeon's Master Round for a boss taken without a hit [§3.5, §5]. These
turn surplus power and clean play into something, rather than cancelling
them.

**Failure modes.** A reward that can be lost to the horde (Halls of
Torment's orbs covering the Lord's drop) [§1.2]; a win that is only a
banner; loot dropped as sacks in a field still full of enemies (our boss
today, `AUDIT.md` §2).

*Used by:* §0.11 of `SURVIVORS_BOSSES.md` and each boss's death.

## 11. A one-page checklist for any boss we add

1. It asks at least one movement question and one damage question, and
   neither is a single-stat check.
2. Every attack has a body tell, a ground shape and a sound; the lethal ones
   a word; the shape draws above the survivor's effects; the shape tells
   the truth about the hitbox.
3. Phases end at a mark or a time ceiling, never before a floor; overkill is
   shown (the Break); thresholds crossed together queue.
4. It has a soft enrage that is a known move turned up, and a hard enrage
   the ordinary build never sees.
5. It does something with the horde, and nothing it summons soaks the
   survivor's auto-aim.
6. It changes the arena, and the change ends with the fight.
7. Anything it takes from the survivor is proportional, visible, time-limited
   and given back.
8. It can be beaten by every weapon family in the draft (check against each).
9. It never soft-locks: every gate has a fallback that grows with time.
10. Its kill is a moment (`docs/feel` S-11) and pays the run's best chest.
