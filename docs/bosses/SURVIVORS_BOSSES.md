# Arena bosses: designs for the night

Eight bosses for the ember arenas, a midpoint for the fifteenth minute, and
two shapes for the endless hour after the win. Each is fitted to the story
bible's people, to the code's units and to what the research says works
(`MECHANICS.md` for the why; `IMPLEMENTATION.md` for the how). Every
number here is a proposal for the balance lab, sized against the probe
(`AUDIT.md` §4); none of it is in the game.

## 0. The rules every arena boss keeps

These come first because they fix the current boss's biggest problems
whichever designs are built.

**0.1 The boss is a boss, and not the herald.** It is flagged as one
(`Enemy.Boss`; today the arena boss is only an elite, `AUDIT.md` §2), so its
script runs and no lock or execute can end it. Heralds stay the people's
champion. The boss is its own creature, with its own view, verbs, bar and
music, and its lieutenant at the fifteenth minute (§9) is the one preview
the player gets.

**0.2 The run-up (28:00 to 30:00).** Build on `docs/feel` S-11, which already
specifies the valley before the peak. Add, per boss, a sign in the world
before the bar: the Pack-Mother's howl from one edge of the map, the Barrow
Lord's drum, Grimtunnel's blasting thump and a rattle of picks, the Red
Hand's whistle. Each is a sound first, then a light on the arena's edge at
the bearing it will come from. The player turns to face it before it
arrives. (Knocking is kept for the Morrow alone: it is Tam's clue.)

**0.3 The arrival.** The boss enters from where the sign was, onto the
picture (12–14 m from the survivor, not 18), with its own entrance (per
boss) and a name card. Its escort is its own kind, not a random draw.

**0.4 The horde during the fight.** Not held at half by a blind spawner:
each boss says what the horde does (the Pack-Mother commands it, the Barrow
Lord raises it, Grimtunnel's lamplings flock to light). The default, for a
boss that does not say, is the S-12 breather: 40% of the target, so the
boss is the thing on screen.

**0.5 Phases are gates, not just thresholds.** Each phase ends at a health
mark **or** at its time ceiling, whichever comes first (Brotato's rule:
`RESEARCH.md` §3.1), and cannot end before its time floor:
- **The mark.** Damage past a phase's mark is not taken off the next phase;
  it fills the **Break**. When the phase ends the boss staggers for 2.5 s,
  plus up to 2.5 s more by the overflow, and the overflow lands as one
  big number ("BREAK 48,210"). The stagger is the transition: the boss
  cannot be hurt in it.
- **The floor** (10–20 s a phase). Before it, health stops at the mark and
  everything more goes to the Break. A strong build never skips a phase,
  and its surplus is shown, not silently thrown away (Gungeon's hidden cap
  is the warning: `MECHANICS.md` §7).
- **The ceiling** (60 s a phase). Past it, the next phase begins anyway at
  the health the boss has. The last phase has none: there the enrages of
  §0.10 take over. A weak build sees every move the boss has before it
  meets them.
- **What overkill buys.** The fight's summed Break is its score: past a
  par amount the boss's chest gains an item, and a fight won with no
  telegraphed blow taken (§0.8's middle band) gains another ("Unscathed",
  the Master Round's lesson). Surplus power and clean play both turn into
  something, rather than being cancelled.
- The word "Break" means only this overflow. A damage check inside a phase
  is written as "damage of N% of its health in T s"; crowd control fills
  the stagger bar (§0.15).

**0.6 The budget.** Fight length at par (the probe's bot at ×2, roughly an
ordinary player at that tier): **90–120 s**, of which 60–75 s is damage time
and the rest transitions, moves that ask for movement and time at reduced
damage. A strong build (×4 to ×10) should still take **45–60 s**, held up
by the time floors. A weak build (×0.5) should take 4–5 minutes and meet
the soft enrage. Today it is 13–44 s at par and about 2 to 4½ minutes at
×0.5, with no enrage (`AUDIT.md` §4).

**0.7 Health.** The def's `Health` (level 1) × `ScaleFor(level)` × a boss
multiplier, as now, but with the multiplier raised and flattened across
tiers: **× (12 + 2 × tier)** instead of × (6 + 2 × tier) (× 14 at tier 1,
× 20 at tier 4). At the half hour the level is 14 at tier 1 (`ScaleFor`
× 11.9), 16 at tier 2 (× 14.6) and 20 at tier 4 (× 20.9). The bosses' own
level-1 `Health` (2–3 times the champions' they replace) is a starting
point, not a result: against each people's measured ×2 damage at tier 1
the figures below give anything from about 60 s (the Red Hand) to about
200 s (the Barrow Lord, measured with a weak stalker), because par damage
differs by people and calling. **The target, 70–90 s of par damage, is set
per boss by re-running the probe** once the boss exists.

**0.8 Damage.** The survivor carries roughly 400–700 health at the half hour
(call it 550 at par). The bosses' blows today were 13–40% of it in the
probe (`AUDIT.md` §4). Three bands, as a share of a par survivor, with the
multipliers on the def's `Damage` (× `ScaleFor` × 1.3, as now) that give
them for a def `Damage` of 24 at tier 1 (× 1 ≈ 88):
- **contact and small shots**: × 0.4–0.6, 6–10%;
- **telegraphed blows**: × 1.5–2, 24–32%: two mistakes hurt, three kill;
- **arena mechanics** with a 2 s or longer telegraph: × 3.5–4.5, 56–72%,
  never a certain kill from full health, so a mistake costs the fight's
  margin, not the run.
Each design gives its multipliers in these bands; for a different
`Damage` the lab keeps the shares and moves the multipliers.

**0.9 Telegraphs.** The language in `MECHANICS.md` §2, four rules, each with
its own edge pattern as well as its colour: **amber** "a blow is coming
here" (circle, line, cone, ring; filled); **violet** "this ground stays
bad" (hatched); **pale blue** "stand here" (safe zones, the boss's open
moment; dashed); **grey** "this will be solid" (cages, pits, walls; solid
edge). Wind-ups no shorter than 0.8 s for a single blow, 1.2–1.5 s for a
heavy one, 2–3 s for anything that covers the arena. Every telegraph has a
sound, and every boss attack that can be perfect-dodged says so by being
`telegraphed` in `HurtPlayer`.

**0.10 Soft and hard enrage.** At 3 minutes the boss's cadence quickens by
a quarter and the horde's share returns to 100% (the soft enrage: the fight
gets harder, not impossible). At 5 minutes the boss performs its final move
on a loop (the hard enrage, named for each boss) that a weak build can
survive for perhaps a minute. Both are announced. Neither is reached by an
ordinary build.

**0.11 The kill.** `docs/feel` S-11 (the camera turned to the boss, slow
motion, silence, a chord, the horde dying in rings). Add: **the boss drops
the run's best chest** (3 items at least, 5 at tier 3 and up, evolutions
first; `docs/items/ACQUISITION.md` §2.1 gives the boss 2 + tier/2 items,
and should be raised to match), its Named roll and its people's signature
items (ACQUISITION §4), and a per-boss death that says who it was (below).
The way out opens where it fell, as now. The victory card shows the
fight's time and its Break: strong builds' "deletion" clips are a genre of
their own on Reddit (`RESEARCH.md` §6).

**0.12 What the oaths do to a boss.** Each oath changes the boss in the
same direction it changes the horde, and says so on the name card:

| Oath | On the boss |
|---|---|
| Swarm | Its add waves are half again as large. |
| Champions | Its lieutenant (§9) returns at 30:00 beside it (a second, smaller bar). |
| Deep Dark | Two levels, as for the horde; nothing else. |
| Long Vigil | Its phases' time floors are a third shorter, its cadence a fifth faster. |
| Long Winter | Its heavy blows chill. |
| Blight | It leaves blighted ground where it walks (violet, 2 s). |
| Embers | Its telegraphed blows leave burning ground (3 s). |
| Hunt | A fifth faster, and its wind-ups a tenth shorter (never under 0.7 s). |
| Iron | Its stagger bar fills a third slower from anything but criticals. |
| Moonless | The boss keeps to the dark at the edge of your light; its telegraphs still draw everywhere (hiding them is the one remix players reject, `RESEARCH.md` §5.2), and its sound cues are louder. |
| Ruin | Its adds burst; it bursts once, at each phase change (amber ring, 1.5 s). |

**0.13 Banes: the day's knowledge against the night's boss.** Halls of
Torment hides a "Lord Hex" in every hall, an optional secret that weakens
its Lord (halves its health, disarms its adds, removes its invulnerability,
simplifies its patterns); it gives weak builds a route to victory through
knowledge, and players love finding them (`RESEARCH.md` §1.3). Each of our
bosses has a **bane**, and the day half is where it is learned: a line of
lore, a person's advice, an item carried in. A bane is never needed and
never a secret the game hides for ever: the bestiary records it once seen.

**0.14 Rules from the research.** Every boss keeps these:
- **Thresholds crossed together queue.** A survivors build will cross two
  phase marks in one hit; Diablo IV once left Uber Lilith stuck
  invulnerable that way (`RESEARCH.md` §4.1). Each phase still plays.
- **Nothing it summons soaks auto-aim.** Its adds and hazards are either
  ordinary targets the survivor wants to hit, or not targets at all.
- **Every weapon family can win.** Check each boss against melee rings,
  thrown blades, spells, zones, beams and summons; no boss may be out of
  reach of one of them (Polyphemus against melee, Vampire Hunters'
  statue the flamethrower could not reach, `RESEARCH.md` §5.2, §6).
- **Attacking is never punished.** The weapons fire on their own, so no
  move may hurt the survivor for hitting, or for killing what stands near
  the boss (Polyphemus's counter stance, Grim Dawn's death blasts,
  `RESEARCH.md` §5.2, §4.3).
- **Never out of reach for long.** No phase in which the boss cannot be
  hurt lasts more than 3 s outside the transitions of §0.5; where a boss
  hides, it takes reduced damage instead (Uber Lilith's "an Action-RPG
  without the action", `RESEARCH.md` §4.1).
- **Arena changes end with the fight.** Every pit, cage, flood, bad air
  and grave a boss makes fills, lifts or fades within 3 s of the kill, on
  every theme, before the endless hour; every lingering hazard has a
  lifetime (Soulstone's littered arenas, `RESEARCH.md` §3.4).
- **No soft-lock.** Every heal or shield weakens with time and stops at the
  soft enrage (Rogue: Genesia's unkillable Vampire Queen, `RESEARCH.md` §6).
- **The stage is cleared for it.** The horde's share drops when the boss
  arrives and the field near its entrance is cleared; the boss arrives
  "encased" for 2–3 s (a statue, an ember gate, rising from the ground) so
  the player has a moment to see it, as Soulstone's Lords now do
  (`RESEARCH.md` §3.4).

**0.15 Stagger.** As a boss (§0.1) it ignores fear, freeze, pull, execute and
knockback and shortens stuns (`AUDIT.md` §2), but every crowd-control effect
that lands also fills a **stagger bar** under the health bar (Diablo IV's,
`RESEARCH.md` §4.1). Full, the boss is held for 3 s and takes 25% more, then
resists stagger for 15 s. Frost, storm and control builds, which would
otherwise lose their verbs against a boss, earn the fight's damage windows
instead. A stagger also breaks whatever the boss is channelling (the
moon-howl, the call of the drowned, the Toll), as an interrupt does today.

**0.16 What the boss teaches.** A skill seen burning in an arena is
discovered and can be learned by day. HoloCure gives each boss's attack to
the player as a weapon (Fubuzilla's beam becomes Fan Beam, `RESEARCH.md`
§3.3). Each boss's kill discovers one skill in its image (the Pack-Mother's
Spirit Herd, the Barrow Lord's Grave Tether, Grimtunnel's Cinderfall, the
Red Hand's Knifestorm, the Kiln Warden's Rimeshard, the Penitent's Moonbrand,
the Barn Thing's Blightfield, the Centurion's Judgement Disc), so the night's
fight leaves the day something to learn.

**0.17 Named at the start, with its weakness.** Elden Ring Nightreign names
each run's boss and its weakness before the run, and makes the weakness a
scripted interrupt rather than a multiplier (lightning breaks Maris's sleep
channel), so the whole run becomes preparation (`RESEARCH.md` §4.5). The
arena's opening card says who rules it ("Held by the Pack. At the half
hour: the Pack-Mother") and its weakness, the bestiary keeps it, and one
card in the fifteenth minute's great blessing draft always answers it. Each
boss has one channel or move that a single hit of its school breaks at
once:

| Boss | Weakness | What one hit of it does |
|---|---|---|
| The Pack-Mother | Fire | Breaks the moon-howl |
| The Barrow Lord | Holy | Breaks "Rise": the dead stay down |
| Grimtunnel | Frost | Surfaces him from an Under, dazed |
| The Red Hand | Storm | The thief drops the stolen weapon |
| The Kiln Warden | Fire | Breaks the call of the drowned |
| The Silver Penitent | Holy | Stops his pull on the ember for 5 s |
| The Thing in the Barn | Fire | A surfaced segment recoils and stays up |
| The Centurion | Storm | Stops the drum: no line forms |

The interrupt is an auto-firing game's version of the counter: the build
the player drafted toward the boss answers it without the player aiming.

## 1. The Pack-Mother, Alpha of the Deep Wood

*The Pack. Table tiers I–IV. In the story, **Greymuzzle, the Old Alpha**
(The Hollow by Night).*

**Who she is.** The Pack is sick, not bold: the Dig's slurry is in the
stream (`STORY_BIBLE.md` §6). The Pack-Mother is what leads it where
Greymuzzle does not: a great grey she-wolf, older than the wolves around
her, blind in one eye, the slurry's green in her breath. She is not hunting
the survivor; she is herding them, away from the den. The fight is a hunt
run backwards: the survivor is the deer.

**The question it asks.** *Can you see the drive coming and refuse to be
herded?* A movement fight, with a damage check in the middle.

**Body.** `wolf_matriarch`: Health 1,100, Speed 6.2, Damage 24, Radius 1.1,
Mass 12, AttackEvery 0.8, Scale 1.9. Resists as the Pack. At tier 1: about
183,000 health (today's boss: 49,000); about 83 s of the Pack's measured par
damage, about 105 s with her time at half damage in the dark.

**The run-up.** At 28:00, a howl from one edge of the map; the wolves on the
field lift their heads and break off toward it for a moment. At 29:30 two
green eyes at the edge of the survivor's light, on that bearing; she comes
out of the trees with twelve wolves.

**Phase 1, the Drive (100%–65%; floor 15 s).** She will not close. She runs
the edge of the survivor's light (light radius + 2 m), and the wolves do the
work:
- **The Drive** (every 14 s): she howls (a rising two-note call), and the
  Pack forms a crescent on one side of the survivor, 10 m out, and walks
  forward. The open side is the trap: she waits beyond it, and a **lunge
  lane** (amber line, 1.0 s, × 1.8) is drawn across the gap as the crescent
  closes. Counter: go *through* the crescent's thinnest point (the wolves
  are ordinary; a dash or an area skill breaks them), never into the gap.
- **The miss.** When a Drive fails (the survivor breaks out), she pauses
  for 2 s at the crescent's broken end, inside the light, panting (a
  pale-blue ring: her open moment). This is the melee window, and it comes
  from playing the Drive right.
- **Hamstring** (when within 6 m): a single bite, 0.8 s wind-up, × 1.5 and a
  2 s slow. Perfect-dodgeable.
- In the dark beyond the survivor's light she takes half damage (her
  outline drawn faintly, never hidden); in the light she takes full and
  flees it after 3 s. Long untargetable spells are one of the most-cited
  failures in ARPG bosses (`RESEARCH.md` §4.1, §4.4), so she is never out
  of reach, only harder to hurt.

**Phase 2, the Moon (65%–30%; floor 20 s, ceiling 60 s).** The sky clears;
the arena brightens (`AtmosphereFor`, a moon key light) and her shadow is
long. She stops hiding and circles at 12 m:
- **Moon-howl** (at the start, then every 25 s): the light dims to the
  survivor's own radius for 8 s, and **three spectral wolves** (her dead,
  `wolf_spirit_hostile`: not creatures but moving hazards, never a target
  for auto-aim or seekers) run straight lanes across the survivor's light,
  each lane an amber line 1.2 s ahead, × 1.5 on contact. The damage check:
  while they run she sits howling at the edge (`BossBar.Channel`, "The
  moon-howl: break it!"); damage of 6% of her health in those 8 s, a stagger,
  or one hit of fire cuts the howl short and holds her 3 s.
- **The Pack's turn**: the nearest wolves gather at her flanks; each wolf
  beside her (within 4 m) gives her 5% less damage taken, at most 25%.
  Killing the Pack near her is the answer, never a mistake.

**Phase 3, the Den (30%–0).** She stands. No more drives; she fights at the
survivor's side with everything left:
- **Shake** (every 6 s): a 120° cone in front, 1.0 s, × 1.8.
- **Lunge** chains of three, each lane telegraphed 0.8 s, × 1.6, the second
  and third aimed where the survivor *will* be (their velocity × 0.6 s).
- At 15% the last of the Pack comes (a ring of 12 wolves at 14 m, closing).

**The horde.** Wolves only, all fight long; boars stop coming. The arena's
trees matter: a lunge of hers that ends in a trunk stuns her for 1.8 s. Only
a boar's charge does that today (`Ai.cs:139-147`); a lunge that meets a tree
just ends, so this is a new rule for her.

**Soft and hard enrage.** At 3 minutes the drives come every 9 s. At 5
minutes, **The Long Hunt**: the light shrinks to half and does not recover;
she lunges from the dark every 3 s.

**With the survivor's tools.** Hunter's Mark finds her even in the dark
(the mark draws her outline for its 5 s) and its 30% applies there too: the
blessing that answers her. Spirit Companion's wolves will not fight her;
they whine and stay at heel (a line of bark, and a good moment), but they
fight the Pack. Her stagger fills fastest from slows and stuns; frost builds
hold her in the light. Momentum suits the Drive. The Moonless oath doubles
her darkness; the Hunt oath makes her lunges faster.

**Scaling.** Tier raises health and damage only. The floors (15 s, 20 s, 15
s) and transitions hold a ×10 build to about 55 s; a ×0.5 build sees Phase 3
by its ceilings and meets the Long Hunt.

**Bane.** The six fires at the arena's edge (the standing stones' fires the
map already lays, `MapGen.cs:543-553`). Stand by one for 3 s to feed it and
for 20 s she will not cross its light, and no Drive can close across it.
Learned by day from Maeca: "They won't come near a fire that's fed."

**The death.** She does not fall where she stands: she runs, hurt, to the
arena's edge, and lies down at the foot of a standing stone. The camera
follows her there (S-11's turn) in half-speed for 1.2 s. The Pack stops.
Every wolf on the field turns and goes past the survivor to her, and lies
down round her (`Behavior.Flee` toward a point, then `Stationary`), and the
howl that started the fight is answered once from the far wood. Silence,
then the chord. No wolf attacks again in this arena; the endless hour is
fought against what comes from the dark instead (§11).

**Drops.** The run's chest, Pack-Mother's Collar (Named, her home), wolf
pelts, the Pack's Own set pieces; discovers Spirit Herd.

**Greymuzzle, the story's version.** The same fight, with three changes.
Greymuzzle does not herd; he shields. In Phase 2 he stands over the den
mouth and will not leave it (a fixed point in the arena), and the wolves
stand guard before him and shove the survivor back (knockback on touch),
never catching the survivor's shots. This fight runs only on the branch
where the survivor hunts the Pack, so Maeca, whom the Pack saved, is not in
it; the name card says so: "Maeca would not come." And if the stream
already runs clean (`stream.clear`), his eyes are clear too: at 30% he
stops and looks at the survivor, and a prompt offers *Let him go*. The
fight ends there, won, and the Pack is spared (a new outcome for the owner
to name; `beasts.outcome` today has `cured`, `allied`, `exploited`,
`ignored` and `slaughtered`).

## 2. The Barrow Lord, Who Would Not Lie Down

*The Risen. Table tiers I–IV. In the story, **the Barrow Lord, of the
Seventh Legion** (Behind the Sealed Door).*

**Who he is.** The standard-bearer of a century of the Seventh Legion,
buried with it "under what it could not burn". He carried the eagle's pole
in life and carries it still, and the risen of the valley fall in behind it
as his century did. He speaks, in a dead man's Latin-flattened Common, only
orders: "Close up." "Hold." "Rise." (The Legion's rank and its parting are
the Act 3 Centurion's, §8.)

**The question it asks.** *Can you read a formation and break it?* An
arena-shaping fight: his walls are men.

**Body.** `barrow_lord`: Health 1,250, Speed 2.6, Damage 30, Radius 1.3, Mass
40, AttackEvery 1.3, Scale 2.4. Resists as the Undead (holy hurts him
half again). At tier 1: about 207,000 health; at par about 120 s once tuned
(§0.7).

**The run-up.** A drum, slow, under the music from 28:00; the risen on the
field stop and turn to face it, then go on. At 29:40, the ground at the
bearing splits along a line, and he rises with his standard.

**Phase 1, the Drill (100%–70%; floor 15 s).** He walks behind his century:
- **Close Up** (every 16 s, a drum roll then "Close up!"): eight
  `risen_warrior` rise in a line 14 m long, shields locked (`Guard`, arc
  180°), and march across the arena toward the survivor at 2 m/s. The line
  is a moving wall the survivor must go round or through (the line is 14 m;
  a dash or Vault clears its end; breaking one shield breaks the line there
  and the halves wheel inward). **It never wastes the survivor's fire**:
  while locked, the line's men are not auto-aim targets (seekers go for him
  behind them), and a projectile that strikes a locked shield passes
  through at half damage to what is behind.
- **Pilum** (every 7 s): from behind the line he throws a spear: an amber
  line 20 m long, 1.0 s, × 1.6; it stays stuck in the ground 6 s as a small
  collider (an obstacle you can hide behind).

**Phase 2, the Testudo (70%–40%; floor 20 s, ceiling 60 s).** He joins the
line:
- **Testudo**: twelve shields form a ring round him (radius 4 m) that turns
  slowly to face the survivor. The shields are **not targets**, and the
  survivor's fire is not wasted on them: projectiles aimed at the standard
  inside arc over the rim (a lobbed hit, at full damage), and melee and
  zones reach through the ring's gaps at half. A lit **standard** stands in
  the ring's centre (a breakable part, 6% of his health, holy and fire half
  again); breaking it drops the ring and holds him 3 s. Otherwise he opens
  the ring after 8 s and charges.
- **Charge of the Century** (when the testudo opens): three columns of four
  risen run straight lanes from the ring outward, one toward the survivor
  and two either side of it (three amber lines, 1.3 s, × 1.5 on contact).
  The gaps are the safety; they close by one column at 55%.
- **Rise** (when a man of his falls): the dead get up as they do now
  (`RaiseSpec`), but only his men, and only once each; a hit of holy on the
  grave keeps it down.

**Phase 3, Who Would Not Lie Down (40%–0, then again).** He fights alone:
- **Gladius** (every 4 s): a two-strike combo, a 90° cone then a short
  lunge, 0.9 s and 0.7 s, × 1.5 each.
- **Hold!** (every 12 s): an amber ring round the survivor at 6 m, 1.5 s:
  every grave inside it sends up a hand (a root, 1.2 s). Stand outside the
  ring, or dash as it closes.
- **"Rise, and to me"** (once, at 20%): any raised ally of the survivor's
  within 10 m (Grave Call's servants, Risen Servants) stands still for 3 s,
  torn between two masters, then fights on for the survivor.
- **At 0 health he falls, and does not die.** He lies in the ground,
  glowing, for 8 s; the bar reads "He will not lie down" and a pale-blue
  circle is drawn round him, 3 m. **Stand in it** for 3 s (a channel the
  survivor holds, shown on the bar) and he is laid down for good. If the
  survivor does not, he rises with 25% and Phase 3 begins again, a fifth
  faster. Holy damage while he lies there counts the 3 s twice as fast. The
  horde's risen try to drag the survivor out of the circle (they come at it
  from every side).

**Why this works.** Phase 3's last beat turns the damage race into a
movement choice at the moment of victory: the horde's whole job is to keep
you out of a circle. Builds that overkill him still have to stand in the
middle of the dead. Players remember the fights they *finished*.

**Soft and hard enrage.** At 3 minutes, a new line forms every 10 s. At 5
minutes, **The Last Watch**: the whole century rises at once round the
arena's edge and walks inward, shields locked, a closing ring of walls;
it reaches the middle in 40 s.

**With the survivor's tools.** Holy builds (Dawnpulse, Hallowed Ground) are
his answer: they burn the standard, keep graves down and count the lay-down
twice. Shield Bash breaks a shield in the line, and interrupts his Gladius.
Summon builds fight for the survivor throughout; "Rise, and to me" only
gives them pause. Stagger fills fastest from stuns and knock-backs into his
men. The Oath of Embers turns his pilum into a line of fire.

**Scaling.** Tier raises health and damage; the line's length grows by two
men a tier (14 m to 20 m). The floors and the lay-down hold a ×10 build to
about 55 s; a ×0.5 build sees the Testudo by its ceiling and meets the Last
Watch.

**Bane.** His standard. When it breaks in Phase 2 it falls; pick it up
(a prompt) and carry it, and for the rest of the fight his century does not
form lines: they follow the standard, not him. Learned from Chid, who has
seen the Legion before: "They never followed a man. They followed the
pole."

**The death.** He sinks into the ground standing, the camera low and close
for 1 s, a hand raised in a salute that is not to the survivor but to
something below. Every risen on the field kneels, then falls, as one, and
the drum stops on the off-beat; silence, then the chord. Every grave on the
field closes, on every theme.

**Drops.** The run's chest, the Barrow Lord's Helm (Named, Act 2 and on),
barrow dust, Legion fragments at tier IV; discovers Grave Tether.

**The story's version (Behind the Sealed Door).** The fight is inside the
door, on the stair's first landing: a narrower arena (radius 40), a wall at
the north where the stair goes down into the dark. When he is laid down the
stair stays dark and closed; nothing of what lies below is shown in Act 1,
and the bootprints remain the clue they already are outside the door.

## 3. Grimtunnel, Roused, Come Up Out of the Dark

*The Lamplings. Table tiers I–IV. In the story, **The Dig Boils Over**.*

**Who he is.** The Boss of the Dig: three lamps and a grudge, a believer
carrying a god its heart. He cannot die before Act 3 (`STORY_BIBLE.md` §3),
and the story's outcome already says "drove Grimtunnel back down". So this
fight is won when he goes back down the hole, not when he dies. It is the
one comic boss: Snib comments.

**The question it asks.** *Can you keep your feet when the ground itself
is the enemy?* An arena-shaping fight with breakable parts.

**Body.** `grimtunnel_boss`: Health 950, Speed 3.6, Damage 22, Radius 1.0,
Mass 10, AttackEvery 1.1, Scale 2.3. Fire resistant (50%), frost
vulnerable. At tier 1: about 158,000 health; about 65 s of the Lamplings'
measured par damage, about 100 s with his time underground at half damage.

**The run-up.** A blasting thump from one edge, the ground shivering, and a
rattle of picks; at 29:30 a mound runs in from that bearing and he bursts
up out of it with a dozen lamplings.

**His three lamps.** Each is a breakable part on his harness (red, blue,
green; 8% of his health each), and each lamp lit gives him a verb:
- **Red, the blasting ember**: lobbed charges (amber circles, 1.4 s, × 1.6,
  leaving burning ground 3 s), three at a time.
- **Blue, the deep lamp**: the lamplings see by it; while it burns, any
  lampling that surfaces does so *under the survivor* (a 1.0 s circle at
  their feet).
- **Green, the slurry**: a sprayed cone of slurry (60°, 1.2 s, × 1.2) that
  leaves violet ground that slows (4 s).
Break a lamp and that verb is gone for the fight; a broken lamp's shards
spray away from the survivor (the colour's school), hurting his own crew.
The bar shows three lamp icons.

**Phase 1, the Dig (100%–60%; floor 15 s).** He tunnels:
- **Under** (every 12 s): he dives and a mound travels toward the survivor
  for at most 3 s (visible, with a sound like rocks in a barrel). **The
  mound is him**: it takes half damage and every weapon can hit it. He
  **bursts up** where it stops: an amber circle 3.5 m, 1.2 s from when the
  mound stops moving, × 2. Above, for 4 s after, he is dazed and takes half
  again. One hit of frost on the mound surfaces him at once, dazed for
  twice as long.
- **Lamp-moths**: the lamplings flock to light. Every 20 s, ten lamplings
  surface round the *brightest thing* in the arena: a lamp of his, a
  burning patch, the survivor's own light. A survivor who has broken his
  lamps is the brightest thing.

**Phase 2, the Collapse (60%–25%; floor 20 s, ceiling 60 s).** The ground
goes:
- **Sinkholes**: each Under now leaves a pit (radius 3 m: unwalkable,
  `InBounds` false, collision added; grey edge 1.5 s before it opens) where
  he burst. Up to six pits; the oldest fills in when a seventh opens. The
  arena fills with holes the player must route round, and the horde routes
  round them too (the flow field re-bakes).
- **Snib's charge** (once, at 50%): Snib shouts from the edge ("Boss! BOSS!
  Not the good stuff! It IS the good stuff.") and a crate of blasting ember
  lands in the middle (a barrel prop). Hit it when Grimtunnel is within 5 m
  and it blows (a tenth of his health, and his armour off for the rest of
  the phase). Miss, and he hits it himself in 20 s and the blast is round
  the survivor (amber ring, 2 s).

**Phase 3, the Boil (25%–0).** He is out of his hole and in a temper:
- He runs at the survivor's light, faster (Speed 4.8), swinging a pick (a
  90° cone, 0.9 s, × 1.5).
- Every 15 s the Dig **boils**: slurry wells up in a ring that expands from
  the arena's centre at 4 m/s (the ring's leading edge amber, × 1; the
  slurry it leaves violet, slowing, 4 s). Dash through it, Vault over it,
  or stand on a pit's rim where it breaks.

**Soft and hard enrage.** At 3 minutes, the pits stop filling in. At 5
minutes, **The Fall**: the arena's floor caves from the edge inward, a ring
of pits closing at 2 m every 10 s (Ashford's Fall, small).

**With the survivor's tools.** Frost builds stop his Under (the weakness,
§0.17). Cinderwake is risky: burning ground is bright, and the lamplings
come for it. Vault and Grapple Chain cross the pits; Shield Bash or
Crashing Leap beside a pit knocks him into it (a lamp breaks). Moonless
arenas are kind to the survivor here: less light, fewer moths. Area builds
clear the moths; single-target builds take the lamps.

**Scaling.** Tier raises health and damage, and adds a pit to the cap per
tier (six to nine). A ×10 build meets every phase by its floors (about 55
s); a ×0.5 build meets the Boil by the ceilings and must route round the
pits.

**Bane.** Grimtunnel's Spare Lamp, the one he dropped in the prologue
(`grimtunnels_lamp`). Carried in, it can be set down (a prompt), and his
next two Unders surface under it instead of under the survivor, dazed for
twice as long: he cannot resist his own light.

**Victory: back down the hole.** At 0 he does not die. He grabs the nearest
pit's edge ("Not done! Not DONE!"), the camera dropping to him as he slips,
is pulled in by the lamplings below, and the pit collapses on top of him
with a deep crump and a column of dust. Every other pit fills in behind it
in a rolling wave over 3 s; the run's chest is thrown up out of the dust a
second later. Every lampling on the field dives underground and is gone.
Snib's last line from the edge: "Snib will tell Boss you said hello. Snib
will NOT tell Boss."

**Drops.** The run's chest, Grimtunnel's Spare Lamp (Named), Snib's Hard Hat
(rare), ember shards and slurry; discovers Cinderfall.

## 4. The Red Hand, Warlord of the Ravine

*The Kerchiefs. Table tiers I–IV. In the story, **Redcowl** (Raid on the
Roost).*

**Who he is.** The Kerchiefs are what is left of Ashford's levy: red was
Ashford's colour. The Red Hand is their war-captain, a big man in a red
brigandine with a tollman's bell on his belt, who takes a toll from
everything that passes, the survivor included. He is the boss who steals.

**The question it asks.** *What is your build without its best piece?* A
fight about the survivor's own tools.

**Body.** `red_hand`: Health 1,050, Speed 3.8, Damage 26, Radius 0.95, Mass
8, AttackEvery 1.0, Scale 1.6. At tier 1: about 174,000 health; about 62 s of
the Kerchiefs' measured par damage, about 100 s with the chases.

**The run-up.** A whistle, three notes, from one edge, and an answering
whistle from another; at 29:30 the toll bell, then he walks in with a
crossbow on his shoulder and two bruisers carrying a cage on poles.

**Phase 1, the Toll (100%–65%; floor 15 s).**
- **The Toll** (every 30 s, first at 10 s): he rings the bell ("Toll's
  due."), and a red ring closes round the survivor (1.0 s): a footpad
  dashes in, touches the survivor and runs. Dash out of the ring and he
  misses, and is stunned. Touched, the survivor's **highest-ranked weapon
  stops firing**, its icon greyed in the HUD with a red kerchief over it,
  and the thief (`toll_thief`, twice a footpad's health, fast, `Flee`) runs
  for the arena's edge with a light on him. **While he holds it he is
  auto-aim's first target.** The weapon comes back on its own after 8 s;
  kill him first and it comes back at once with a surge (it fires three
  times together).
- **Volley** (every 9 s): he and four pillagers fire crossbows: five amber
  lines in a fan from him, 1.1 s, × 1.2.
- **Firepots** from the pillagers, as now, capped.

**Phase 2, the Cages (65%–30%; floor 20 s, ceiling 60 s).**
- **Cage** (every 20 s): the bruisers drop a cage over the survivor's
  position: a ring of eight posts (radius 5 m) drawn grey 1.5 s ahead, then
  solid colliders for 8 s. Inside, footpads; outside, he waits with the
  crossbow. Dash out before it closes, or break a post (a breakable part, a
  moderate hit), or fight through. Walls you can see and break.
- **The Levy** (once, at 50%): eight bruisers in a shield line (Guard) with
  red colours, marching in step: the Ashford levy's drill. Unlike the
  Barrow Lord's line it does not raise the dead; it pushes (knockback on
  touch). Its men are not auto-aim targets while locked, as the Barrow
  Lord's are not. The levy breaks if he is hurt hard (damage of 5% of his
  health in 6 s, or a stagger): they look to him and waver.

**Phase 3, the Hand (30%–0).**
- He drops the crossbow and fights with a maul: a two-handed overhead (an
  amber circle at the end of a 4 m line, 1.2 s, × 2.0) and a sweep (a 160°
  cone, 1.0 s, × 1.4).
- **Takes everything** (once, at 15%): the toll bell rings three times, and
  **all** the survivor's weapons stop for 6 s while the survivor's arts and
  dash still work: the moment the survivor's hands are their own. A red
  ring telegraphs it 2 s; a perfect dodge through it cancels it.

**Why this works.** The genre's strongest fantasy is the build; the Toll
makes the player notice what each piece of it is doing, and the chase to
get it back is a short, sharp objective inside the boss fight. It never
removes more than one piece for more than 8 s, and always gives it back.

**Soft and hard enrage.** At 3 minutes, the toll every 15 s. At 5 minutes,
**Everything Owed**: the thief takes a weapon every 10 s, two at a time;
each still comes back after 8 s, or at once when he is caught, so the
survivor is never left with nothing.

**With the survivor's tools.** Mark Prey on the thief marks him, and below
a fifth of his health he dies outright (`Arts.cs:796`): a good answer.
Smoke Bomb makes the toll miss. Time Slip slows the thief to a third. Iron
Vow's barrier takes the touch. Storm builds make the thief drop it (the
weakness). The Oath of Champions brings his lieutenant, the toll-taker
(§9), back beside him.

**Scaling.** Tier raises health and damage, and the cage's posts gain
health. The floors hold a ×10 build to about 55 s; the Toll's 8 s return
means a weak build is never stripped for long.

**Bane.** The Kerchiefs' whistle. A survivor who has worked out how word
reaches the Roost (`redcowl.birds`) hears the toll-taker's signal early:
the red ring comes half a second sooner, and the thief's route to the edge
is drawn on the ground.

**The death.** He goes down on one knee and takes off the brigandine's red
hood, and under it is a face, middle-aged, Ashford's; the camera holds on
him at half speed for 1 s. The bell drops and rolls, ringing, and every
Kerchief on the field stops, takes off their red cloth, and walks away
(`Flee`). Every stolen weapon comes back in one surge, all firing at once.

**Drops.** The run's chest, the Red Kerchief, red cloth, the Red Hand set
pieces; discovers Knifestorm. (Ashford Levy Colours stays the branch-only
item ACQUISITION makes it.)

**Redcowl, the story's version.** Redcowl fights as the Red Hand, with
three changes: he never says "Ashford" (his lines in his `VOICES.md` voice:
a big chest voice that laughs before it threatens, hard Scots, "my lot");
the cage holds the caravan's prisoners if they are still held
(`caravan.survivors`), and breaking it frees them (they run; they do not
fight); and **the six crates** are in the arena if `be.crates` is unset:
stacked at the Roost's centre. Hit them with fire and they blow (an amber
ring 3 s ahead, then a crater, the arena's middle gone, and everything in
it hurt, Redcowl too): the story's B.E. go up here, and `be.crates` is set
to `burned`.

## 5. The Warden of the Kiln Ford

*The Drowned (a new people: the Low Ford's dead and the Kiln Ford's, risen
mindless in the ditches). Act 2, only if the Kiln Ford is lit (`nell.told`
is `lie` or `evaded`, `STORY_BIBLE.md` §7.8). At the table thereafter as
**a Warden's echo** of either crossing.*

**Who it is.** The second of the seven Wardens woken: made by the Order of
the Morning Light to keep a crossing and kill what comes near. The Kiln Ford
Warden is a woman in the Order's mail, drowned and huge, with a lamp in each
hand: Brannoc's last two irons, lit. It sings in the water, as the dead
watchman wrote of the first.

**The question it asks.** *Will you remember the first Warden?* The
prologue's language, at the scale of a horde: lamps that ward her, a charge
you steer into them, a channel you break. The players who learned the Ford-
Warden are rewarded for it.

**Body.** `kiln_warden`: Health 1,300, Speed 2.6, Damage 30, Radius 1.5, Mass
40, AttackEvery 1.4, Scale 2.8. At tier 2 (where Act 2 starts): about
303,000 health; par about 120 s once tuned, much of it behind the ward.

**The arena.** A ford: the arena's middle is a river (a band 14 m wide
across the map), with **stepping stones** (circles 2.5 m) across it. Water is
walkable but slow (× 0.7) and the drowned rise from it. Two banks of solid
ground. Six lamps along the banks: the **two irons** in her hands become
the first two lamps when the fight starts (she sets them in the river
mouth), and **four old lamps of the Order**, rusted and relit, stand on the
banks (different art; 1% of her health each, against the irons' 2%).

**The run-up.** At 28:00 singing from the river, under the music; at
29:30 the irons are lit, one then the other, and she stands up out of the
water.

**Phase 1, the Lamps (100%–60%; floor 15 s).** As the Ford-Warden, at
scale:
- **The ward**: damage taken × (1 − 0.12 × lamps lit): × 0.28 with all six.
  The bar is grey while any burn.
- **Charge** (every 8 s): an amber line 24 m, 1.3 s, "It lowers its
  head...", × 1.8; a lamp in the lane is snuffed and she is stunned 4 s,
  taking × 1.5. Lamps also break to blows.
- **Cleave** (when within 5 m): an amber circle 3.4 m, 1.05 s, × 1.5.
- **Sing**: while she sings (a held note, every 20 s for 5 s), the drowned
  rise from the water in the river's band only, never within 3 m of a stone
  the survivor stands on.

**Phase 2, the Flood (60%–25%; floor 20 s, ceiling 60 s).** She calls the
river up:
- **The flood**: the water's band widens by 4 m every 20 s (a shrinking
  arena: the banks are what is left), to a limit (§ Phase 3).
- **The call of the drowned** (at 60% and 40%): "RISE, YOU WHO DROWNED
  HERE." The Ford-Warden's channel, 6 s, broken by damage of 9% of her
  health, an interrupt, a stagger or one hit of fire; finished, it heals 4%
  and relights a lamp (each finished call heals half as much as the last,
  and none after the soft enrage).
- **The lamps go under**: lamps in the water cannot be lured into; only
  bank lamps can. The puzzle tightens as the river grows.

**Phase 3, the Drowning (25%–0).** The water is everywhere but the stones
and **two bank strips, 6 m wide**, that the flood never takes:
- She walks the river at full speed (water does not slow her).
- **Undertow** (every 10 s): an amber ring round her, 6 m, 1.4 s: anything
  in water inside it is pulled 3 m toward her.

**Soft and hard enrage.** At 3 minutes, the flood reaches its limit at once
and her charge comes every 5 s. At 5 minutes, **High Water**: the strips
narrow to 3 m and she charges along them.

**With the survivor's tools.** Every Ford-Warden trick works: lure the
charge into a lamp. Fire breaks her call (the weakness). Frost builds
freeze the water's edge into footing (a frozen patch is ground for 4 s).
Vault and Blink cross the river; Grapple Chain pulls the survivor to a
stone. Projectile and zone builds break the far lamps; melee lures the
charge. Summons stand in water and slow, so they guard the banks.

**Scaling.** Tier raises health and damage; the river's limit stays the
same, so space never shrinks with tier. A ×10 build still has to snuff or
break the lamps (the ward caps its damage until it does), which is the
point: about 60 s.

**Brannoc's choice, in the fight.** If Brannoc knows about Nell and broke
the last irons, this fight does not exist; if he forged them and learned
later, the two irons are his work. At the table, the Warden's echo uses the
Ford-Warden (three lamps, the Low Ford's river, a man) with the Kiln
Ford's flood.

**Bane.** Brannoc's mark. A survivor who has seen his mark on the iron
(`brannoc.saw_iron`) knows where he leaves the weld soft: the two irons
break at half their health. For the echo of the Low Ford, the dead
watchman's line for the devout ("It shatters its own lamps when it
charges. Make it charge.") is the bane, as it was in the prologue.

**The death.** The water goes down all at once, back into its band, with a
long drawn breath of sound; she sits in it, the camera pulled back to the
whole ford, and the two irons go out one after another, then the Order's
lamps. Silence, then the chord, and a single note of her song.

**Drops.** The run's chest, the Kiln Ford Rod (Named, its home, ACQUISITION
§6), drowned silver; for the table's echo, the Warden's Lamp (Named, the
echo's only home, ACQUISITION §4); discovers Rimeshard. What the story does
with this Warden's heart is the story's to decide.

## 6. The Silver Penitent

*The Vigil. Act 2 (Silverstair and the war at the gate) and the table. The
items plan's "Sallow's champion".*

**Who he is.** One of the Unchained in Sallow's silver cages, bought and
armoured in argent plate for the war in the south: a soldier who rises
every night. His helm has no face but a silver ledger-plate with his entry
on it: a name scratched out, "From the Ashford road. Risen the winter of
the Fall. Comes back." He is the survivor as the Vigil would make them, and
he burns as they do: he has an ember of his own.

**The question it asks.** *Who can burn brighter?* A rival who grows by the
same rule the survivor does, and who comes back.

**Body.** `silver_penitent`: Health 900, Speed 4.2, Damage 24, Radius 0.8,
Mass 6, AttackEvery 0.9, Scale 1.3 (man-sized: the one boss who is not big,
and reads by his light and a silver outline, not his bulk). Shadow-
resistant, holy-vulnerable (he is Unchained). At tier 2: about 210,000
health, spent twice (he comes back).

**The run-up.** A bell from the north edge, the Vigil's; at 29:30 two
knights carry in a silver cage and open it, and he walks out.

**His ember.** He collects ember. **Ember stones left on the ground within
20 m of him drift to him** (a visible stream of motes), at most 20 stones
in any 10 s. Every 40 he takes a level: one of the survivor's own weapons,
copied at **rank 2** and never deeper, fired at two thirds of its speed,
drawn with a hostile silver outline and an amber trace on the ground so it
can never be mistaken for the survivor's own fire. A survivor who collects
cleanly keeps him poor; one who lets the field fill with stones meets
copies of their build, never its full strength.

**Phase 1, the Rival (100%–60%; floor 15 s).** He fights like the
survivor: he moves, dashes (a short line, telegraphed 0.4 s: his dash is
not an attack), and his copied weapons fire at a third of their rate. The
horde is the Vigil's caged risen (Silverstair's people); they part for him
and fight the survivor.
- **Silver Ink** (every 15 s): he writes in the air, a line drawn across the
  survivor's position (an amber line 1.4 s, then violet ground 3 s):
  crossed while it burns, it spills an ember level's worth of stones from
  the survivor's bar (cards stay, `README.md` decision 3), and they drift
  to him. Everything he takes comes back when he is laid down.

**Phase 2, the Return (60%–30%; floor 20 s, ceiling 60 s).** "Return to the
dark", the Vigil's old order, in Sallow's book:
- **At 60% he dies.** He falls, the light goes out of him, and the bar
  empties. Then, 4 s later, at the arena's edge, he **rises** with the
  phase's health ("He comes back more often than most."), and every stone on
  the field drifts to him. The fight's twist, and the first time the player
  sees someone else come back.
- **Censers**: two Vigil knights swing censers (a mobile violet zone each,
  radius 4 m): inside, the survivor's ember pickup is halved. The knights
  are ordinary targets.

**Phase 3, the Ledger (30%–0).**
- He uses the survivor's art (their ability, at its cooldown × 2).
- **Cage** (every 18 s): the silver cage drops over the survivor (grey 1.5
  s ahead, as the Red Hand's; solid 8 s); while it is closed the survivor's
  ember bar does not fill.

**How to keep him down.** At 0 he falls again, and rises again in 8 s
unless the survivor **takes his ember**: stand over him (a pale-blue circle,
2.5 m) and the motes come out of him to the survivor (3 s). Taken, he is
laid down; everything he took comes back, and the survivor gains three
ember levels at once (the reward is literally his power). Left, he rises
with 20%, and Phase 3 begins again. Mirror of the Barrow Lord's lay-down,
and the story's: an Unchained can be put down only by taking what keeps
them up.

**Why this works.** It is the boss that steals the player's tools in the
truest way: it is built from them, at a fixed low strength, and it grows
only from what the survivor leaves lying. It rewards a habit (clean
collection) the genre already teaches. Its two returns are a story beat
played as mechanics.

**Soft and hard enrage.** At 3 minutes, his rate goes to two thirds. At 5
minutes, **Paid in Full**: every stone in the arena drifts to him, wherever
it lies, and his copies go to rank 4.

**With the survivor's tools.** Ember Tithe's doubled pickup radius starves
him. Holy builds stop his pull (the weakness). Area builds kill the
censer-knights; single-target builds keep him from levelling. Arts that
interrupt stop his dash. Summons are ordinary allies here.

**Scaling.** Tier raises health and damage; his copies stay at rank 2
whatever the tier. A ×10 build meets both returns (about 55 s); a ×0.5
build that collects cleanly fights a poor rival.

**Bane.** His name. Ysolde's notes (Act 2) have the entry before it was
scratched out. A survivor who has read it can say it over him when he
falls (a prompt in place of the 3 s channel), and he lies down at once,
and stays down.

**The death.** He kneels and takes off the helm, the camera close for 1.5 s
at half speed. Under it, a young man, grey; he says one plain line ("Was I
in the book long?") and is gone, and the silver plate rings on the stones.
The survivor's journal: his scratched-out name, if Ysolde's notes are found
later. On the field the caged risen stop, and stand there, waiting for
orders that do not come.

**Drops.** The run's chest, Sallow's Silver Pen (Named), silver ink, argent
scraps, the Argent Vigil set; discovers Moonbrand.

## 7. The Thing in the Barn

*The Fevered (Act 2, the breakthrough; the items plan's people). Act 2
story and the table.*

**Who it is.** Not a creature: a part of one. When the Dig breaks into the
Morrow's outer workings, something pale and segmented comes up: a feeler of
the Morrow, or a thing that lives on it. Tam heard it knocking in Act 1. The
Fevered are the farmhands and the neighbours with the fever year's sickness
in them again.

**Where.** The breakthrough is where the story put it (`STORY_BIBLE.md`
§7.1). Under the Penhale farm (one or two things fed the Dig), the arena is
the farmyard with **the barn** in its middle. At the old sinkhole in the
Verge (the pump blown in Act 1), it is a ring of broken ground round the
sinkhole's mouth, with rubble and a fallen pump-frame where the barn would
be (the same cover beat). With nothing fed and a slow sinking, there is no
fight: the family walks out with two days' warning.

**The question it asks.** *Can you listen?* A boss under the ground,
telegraphed by sound first: the fight for players who play with the sound
on, with every cue also shown.

**Body.** `barn_thing` (the head; the segments are parts): Health 1,400,
Speed (underground) 5, Damage 28, Radius 2.0, Scale 3.2. At tier 2: about
326,000 health.

**The run-up.** At 28:00 the knocking starts under the music, far off; at
29:30 it is under the survivor, and the ground in the arena's middle heaves.

**The knocking.** Tam's knock is the fight's language: **one knock** = it is
moving; **two** = it will surface within 2 s; **three** = it will surface
under the survivor. Each knock also pulses a dust ring on the ground where
the sound comes from (shown as well as heard: an accessibility rule, not an
option), and the HUD's compass edge shows the bearing.

**Phase 1, the Knocking (100%–65%; floor 15 s).**
- **Surface** (every 10 s): three knocks, then an amber circle under the
  survivor (3 m, 1.2 s, × 2): segments burst up in an arc, the head among
  them. The segments stay up 6 s (breakable parts, each 3% of the whole;
  break all three and the head is held up for 6 s more). **One segment
  always stays up between Surfaces** (the tail, at half damage), so it is
  never out of reach.
- **Drag**: it pulls the Fevered under. Every 15 s, a cluster of the horde
  sinks into a dust ring (1.0 s) and it heals 1% per creature dragged, at
  most 5% in a phase, each drag healing half as much as the last, none after
  the soft enrage. Kill the horde before it does; or let it, and it
  surfaces where it fed. The boss that feeds on the horde.

**Phase 2, the Bad Air (65%–30%; floor 20 s, ceiling 60 s).**
- The fever: violet bad air seeps from every hole it has made (a zone per
  surfacing, 5 m, lasting 20 s), poisoning; the healing cut of the Blight
  oath applies in it. Wenna's blightward mask (if worn by day, it carries)
  halves it: the day's gear answering the night.
- **The barn falls** (once, at 50%): the barn (or the pump-frame) collapses
  (grey 2 s ahead); its beams become cover (colliders) and the knocking
  echoes off them (two bearings for each knock for 10 s).

**Phase 3, the Mouth (30%–0).** It comes up and stays up: a ring of segments
round a pale opening at the arena's centre, the ground round it opening by
a metre every 20 s (grey edge 2 s ahead). It sweeps (an amber 180° cone, 1.5
s, × 2) and breathes (an amber line 16 m, 1.2 s, × 1.6, leaving violet
poison ground 4 s).

**Soft and hard enrage.** At 3 minutes, it surfaces every 7 s. At 5
minutes, **Ashford Again**: the ground goes, from the middle outward.

**With the survivor's tools.** Fire makes a surfaced segment recoil and
stay up (the weakness). Area builds stop the Drag; single-target builds
break segments. Zones placed where the dust rings pulse are waiting when
it comes up. Summons are not dragged. Sure-footed gear and Tenacity shrug
off the bad air's slow.

**Scaling.** Tier raises health and damage; the drag's cap does not grow.
A ×10 build meets every phase by its floors (about 55 s); a ×0.5 build
fights a capped heal and meets the Mouth by the ceilings.

**Bane.** Tam. A survivor who listened to him in Act 1 (`tam.tock`) knows
the knocking's count: the third knock's ring appears a second sooner.
Wenna's blightward mask, worn in, halves the bad air.

**The death.** The segments go slack and slide back down, and the ground
closes over them, too fast, like something being pulled; every hole and all
the bad air go with them. The camera looks down at the closing ground for 1
s. The knocking stops; then, very far below, it knocks **once**. (The
Morrow is not dead. It prays.) Silence, and no chord: the one fight that
does not end in triumph. The farm is spared or lost as the story set.

**Drops.** The run's chest, the Penhale Lantern, bitterroot, moonpetal;
discovers Blightfield.

## 8. The Centurion of the Stair

*The Legion (Act 3, the stair down to the Morrow). The last arena boss; at
the table thereafter as an echo.*

**Who he is.** The Seventh Legion's dead keep the inner door "from inside",
and part for the Morrow's own light. The Centurion keeps the door. He is
not hostile to the Morrow's light, which the survivor carries; he is
hostile to anyone who comes down without paying, and the toll is owed at
the inner door (`STORY_BIBLE.md` §8). The fight is a ritual as much as a
battle.

**The question it asks.** *How much of your light will you spend?* The boss
that turns the survivor's ember into the price of the fight.

**Body.** `centurion`: Health 1,500, Speed 3.0, Damage 34, Radius 1.4, Mass
50, AttackEvery 1.2, Scale 2.6. At tier 4: about 626,000 health; par about
120 s once tuned.

**The arena.** The stair's last landing: a long hall, 60 m by 30 m, the
inner door at its north end, ranks of the Legion's dead along both walls,
the survivor's light the brightest thing in it.

**The run-up.** No horde comes in the last two minutes: the dead stand
still, and a drum begins, slow. At 29:30 the ranks along the walls turn
their heads to the survivor, together, and he steps out of the door.

**The parting.** The dead **part for the light when the survivor shows it**:
standing still for 1 s raises the survivor's light as a pale-blue ring (6
m), and the ranks within it step aside and stay aside for 4 s. Moving, the
survivor is one more traveller, and the ranks close and push. The trigger
is the survivor's choice and is drawn on the ground; it never depends on
the ember bar's fill.

**Phase 1, the Ranks (100%–60%; floor 15 s).** He stands at the door
behind his ranks:
- **Close Up** (every 14 s, a drum roll): a line of ten shields rises
  across the hall and marches on the survivor (as the Barrow Lord's, §2:
  not auto-aim targets while locked; projectiles pass at half). Showing
  the light parts it.
- **Pila** (every 6 s): three spears from the door, three amber lines 22 m,
  1.0 s, × 1.6.
- **Hold!** (every 12 s): an amber ring round the survivor at 6 m, 1.5 s;
  inside it the ranks' hands root the survivor 1.2 s.

**Phase 2, the Toll (60%–25%; floor 20 s, ceiling 60 s).** "The toll." He
opens his hand:
- **Pay** (a prompt at the door, offered every 30 s): spend three ember
  levels (the bar and the level step back; cards stay, decision 3) and the
  Legion lays down its shields for 30 s: he fights alone and takes × 2.
- **Refuse**: the ranks close entirely and must be broken by force: two
  lines at once, and the parting lasts only 2 s.
- Either way he fights: **Gladius** (a cone and a lunge, 0.9 s and 0.7 s,
  × 1.5 each) and **Testudo** (as the Barrow Lord's, 8 s, the standard
  replaced by the door's lamp).
- The toll is the only place in the game where ember is spent.

**Phase 3, the Door (25%–0).** He fights at the door with the whole drill:
- **The Charge of the Legion**: four columns run the hall's length (four
  amber lanes, 1.5 s, × 1.8), the gaps between them the safety.
- **Gladius** faster (every 3 s); **Pila** in fours.
- At 10% the ranks along the walls kneel: the fight is his alone.

**Soft and hard enrage.** At 3 minutes, a line every 9 s and the toll
offered no more. At 5 minutes, **The Inner Door**: the whole Legion marches
from both walls inward, shields locked, the parting the only way through.

**With the survivor's tools.** Storm stops the drum (the weakness): no line
forms for 8 s. Holy builds burn the door's lamp. Stillness builds (Iron
Vow, Bulwark) suit the parting; Momentum fights it. Summons hold the ranks.
Area builds shred the lines; single-target builds take him at the door.

**Scaling.** Act 3 runs at tier 4 and above; tier raises health and damage
and the lines' length. A ×10 build meets every phase by its floors (about
55 s); a ×0.5 build that pays the toll halves the fight.

**Bane.** Vonnra's coin, carried. He sees it, and does not take it:
"Paid. Later." For the rest of the fight the Legion lays down its shields
without the ember being spent. The coin stays the survivor's, for the inner
door and the ending, which are the bible's (`STORY_BIBLE.md` §8).

**The death.** He does not die. At 0 he lowers the gladius and steps aside,
and the door's lamp goes out; every rank along the walls turns away from
the survivor to face the door, the camera rising to show the whole hall,
and the drum stops. "Paid." The door opens a hand's width; what is beyond
it is the story's.

**Drops.** The run's chest, the Standard of the Seventh (Named,
ACQUISITION §4), Legion seals; discovers Judgement Disc. (What It Could Not
Burn stays at the Vault door, as ACQUISITION places it.)

## 9. The fifteenth minute: the Kindling

The great blessing at 15:00 is today an announcement. Make it a moment, and
make it the boss's first verse.

**What happens.** At 14:30 the horde draws back 15 m and thins to 40% (the
S-12 breather). In the middle of the arena an **ember-core** surfaces: the
burning heart of the ember scar the arena was opened from (`Verge.cs`'s
scars), a lump of raw ember the size of a cart wheel, pulsing. Round it,
the **lieutenant**: the boss's own creature, with one of the boss's verbs
and a fifth of a boss's health:

| People | Lieutenant | The verb it previews |
|---|---|---|
| The Pack | the Pack-Mother's yearling | the Drive (a crescent, a lunge across the gap) |
| The Risen | the Barrow Lord's horn-blower | Close Up (a line of four shields) |
| The Lamplings | a sapper-foreman with one lamp | Under (the mound and the burst) |
| The Kerchiefs | the Red Hand's toll-taker | the Toll (a thief, a chase) |
| The Drowned | a drowned lamp-bearer | the charge into a lamp |
| The Vigil | a censer-knight | Silver Ink |
| The Fevered | a feeler | the knock and the Surface |
| The Legion | an optio with a drum | Close Up, and the parting |

**The core.** The great blessing is owed whatever happens (it is never
lost). Break the core within 60 s (it has the lieutenant's health, and
breaking it stuns the lieutenant 4 s) and the great blessing is offered
from **four** instead of three, one of them answering the boss's weakness
(§0.17); fail, and it is three, one still answering. Kill the lieutenant as
well and it drops the run's mid chest.

**Why.** Every survivors-like that players praise for bosses teaches their
language before the exam (VS's Arcana bosses at 11 and 21; Halls of Torment's
stage bosses before the Lord; Nightreign's raids; `RESEARCH.md` §1–2, §4.5).
The Kindling puts a fight where the run's pacing already wants a peak, and
its reward is the run's most important choice made better, not a bigger
number.

## 10. The endless hour: Echoes

After the win, the herald every five minutes becomes **an echo**: one of the
*other* peoples' bosses, from the table's tier, cast in pale ember
(`view:echo` tinting the boss's view), at 60% of its health and the first
two of its phases only. Bosses whose fight needs their own ground come as
echo variants: the Kiln Warden's flood is a moving band across the arena;
the Barn Thing surfaces anywhere, without the barn; the Centurion brings
his ranks only. Each echo killed drops a chest and cuts a **notch** on the
HUD (seven notches, like the sealed door's sigil, which the player has
already seen in Act 1). At seven notches the next echo is the Ford-Warden
itself, with three lamp-irons set round it, and its death is the arena's
highest score.

**Let it ride.** An echo's chest may be left unopened (walk past it and it
goes dark): the next echo comes harder (a third phase, its health × 1.3)
and its chest carries both, with the Named chance doubled. Titan Quest's
Tartarus does exactly this with his orb (`RESEARCH.md` §4.3); it turns the
endless hour into a wager the player sets, the opt-in density players like
best (§6 there).

Scaling after the win already hardens the horde; echoes harden with it (×
(1 + 0.1 × minutes past) health). They give the endless hour a goal (the
notches) and a gallery (every boss the survivor has met), and they make each
people's boss worth having learned.

## 11. The endless hour: the Dawn

The bible's own hard enrage: the Unchained burn at night, and **at dawn the
light drains back into the ground and leaves them ordinary**
(`STORY_BIBLE.md` §1). Make it the end of every arena.

- **At 50:00** the arena's sky begins to grey at the east edge (a slow change
  of the atmosphere preset); the music thins.
- **At 55:00 the dawn line**: a band of daylight enters from the east edge
  and crosses the arena at 1 m every 4 s. In daylight the survivor's ember
  drains (one ember level each 5 s: the bar and the level step back, the
  cards stay, decision 3), and nothing of the night can stand in it
  (creatures that touch it go still and grey, and fall). The night side is
  the arena, and it shrinks.
- **At 60:00 or when the last of the night is gone**: "Dawn." The fight is
  over; the survivor leaves with everything earned, the run ends as a win,
  and the journal says "Saw the night out".

Why: it is a hard cap like the Reaper, but it is the world's rule, not a
monster's, and it is beautiful where the Reaper is a joke the genre has
learned to wink at. The last minutes are a choice between staying lit and
running toward the dark: the run's best image. It also gives the engine a
ceiling (the horde's numbers at 60 minutes are knowable).

(For the story's later acts the owner may prefer a hunter instead: the
Vigil's knights coming at 45:00 for an Unchained who stays too long. Dawn
is recommended; see `README.md`, decision 4.)
